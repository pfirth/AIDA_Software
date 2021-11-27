# T&C Power Conversion AG 0613 600W RF Generator, "old style" communication
# Dave Matthews, Swift Coat Inc, Nov 2021

from power_supply import PowerSupply
import queue
import serial
import threading
import time


class AG0613_old(PowerSupply):
    ''' "Old" style communication for AG0613 '''

    BYTEORDER = "little"

    CMD_HEAD = b'\x97'
    CMD_ADDR = b'\x01'
    CMD_CTRL = b'\xAA'

    KEYS_INIT = 0b101

    @staticmethod
    def crc8(msg):
        ''' Generate checksum through arcane method given in manual '''
        crc = 0
        for b in msg:
            for i in range(0, 8):
                if (crc ^ b) & 0x01:
                    crc = crc ^ 0x18
                    crc = crc >> 1
                    crc = crc | 0x80
                else:
                    crc = crc >> 1
                    crc = crc & 0x7f
                b = b >> 1
        return crc

    def __init__(self,slot=0,
                 min_power=0,
                 max_power=600,
                 port=None,
                 baud=19200,
                 parity=serial.PARITY_NONE,
                 timeout=0.2,
                 line_term='',
                 verbose=False):

        # Params
        self.max_power = max_power
        self.min_power = min_power

        # Serial communication
        self.line_term = line_term

        # Com thread
        self.tx_queue = queue.SimpleQueue()
        self.rx_queue = queue.SimpleQueue()
        self.running = False
        self.com_thread = threading.Thread(target=self.__com_loop)

        #Software integration
        self.slot = slot
        self.currentSet = '0'
        self.currentFoward = '0'
        self.currentFormatted = ''
        self.currentReflected = ''
        self.on = False

        # State caching
        self.state = {
            'forward': None,
            'reflected': None,
            'requested': None,
            'temperature': None,
            'load_power': None,
            'vswr': None,
            'pmode': None,
            'work_mode': None,
            'pwr_on': None,
            'over_heat': None,
            'rev_limit': None,
            'forward_limit': None,
            'rf_on': None,
            'burst_enable': None,
            'burst_select': None,
            'blank_loc_en': None,
            'source': None,
            'ilock': None,
            'power_mode': None
        }
        self.keys = self.KEYS_INIT     # Stores key states as a binary value

        # Finish initialization and connect
        super().__init__(port, baud, parity, timeout, verbose)

    def __com_loop(self):
        ''' Serial communication loop
        - Sends commands from self.tx_queue or get_status() if no command shows
        up in tx_queue for over one second.
        - Places responces in self.rx_queue.
        - tx_queue messages are just bytestrings to send
        - rx_queue messages are tuples:
            (command id, received data or b'' if none)
        - Continues until self.running == False. '''

        # Connect
        try:
            ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        except serial.SerialException as e:
            print("RF: Failed to connect")
            raise e

        # Run send/receive loop until disconnect
        while self.running:
            # Wait one second for a real message, otherwise get status
            try:
                msg = self.tx_queue.get(timeout=1.0)
            except queue.Empty:
                self.get_status()
                continue

            ser.write(msg)
            self.debug("> " + str(msg))
            cmd_id = msg[4]   # Save command id for response queue

            # Read until finding a head byte
            # TODO: exit if too many retries
            msg = ser.read()
            n = 0
            while msg != self.CMD_HEAD:
                if n > 10:
                    self.running = False
                    break
                self.debug(f"< {msg} discarded, waiting for {self.CMD_HEAD}")
                msg = ser.read()
                n += 1

            # Get length
            msg += ser.read()
            # Read rest of message
            length = msg[-1]
            msg += ser.read(length)
            self.debug("< ", msg)

            # Verify address byte
            if msg[3] != 0:
                print(f"Received bad address byte: {msg[3]}")
                continue

            # Verify command id
            cmd_in = msg[4]
            if cmd_in != cmd_id:
                print(f"Received response to wrong command: {cmd_in}, "
                      + f"expected {cmd_id}")
                continue

            # Verify checksum
            crc_in = msg[-1]
            crc = self.crc8(msg[:-1])
            if crc_in != crc:
                print(f"Received bad checksum: {crc_in}, expected {crc}")
                continue

            # Put response in queue
            data = msg[5:-1]    # will be b'' if no data received
            self.rx_queue.put((cmd_in, data))
            self.debug(f"put {data}")
            time.sleep(0.02)

        # Cleanup
        ser.close()

    def connect(self):
        if self.running:
            return

        # Start communication loop
        self.running = True
        self.com_thread.start()

        # Init keys and self.state
        self.set_key_state(self.KEYS_INIT)
        self.get_power_measurement()
        self.get_status()

    def disconnect(self):
        ''' Release control, then set flag to close com loop. '''
        if not self.running:
            return

        # Release control end end communication loop
        self.control = False
        time.sleep(1.)
        self.running = False
        self.com_thread.join(2.)

    def assemble_cmd(self, cmd_id, data=b''):
        ''' Internal function to format commands for sending. '''

        # Sub-frame
        frame = self.CMD_ADDR
        frame += cmd_id
        frame += data

        # Tx frame
        tx = self.CMD_HEAD                         # Head
        tx += self.to_bytes(len(frame) + 2, 1)     # Length (min 4)
        tx += self.CMD_CTRL                        # Ctrl
        tx += frame                                # Sub-frame
        tx += self.to_bytes(self.crc8(tx))
        return tx

    def send_cmd(self, cmd_id, data=b''):
        ''' Format and send a command, then wait for and return response.
        Returns data, if expected; otherwise returns bool representing
        whether command was acknowledged successfully.'''

        if not self.running:
            return

        # Assemble and send command
        msg = self.assemble_cmd(cmd_id, data)
        self.tx_queue.put(msg)
        cmd_id = self.from_bytes(cmd_id)

        # Read receive queue until a response matches the correct id
        while True:
            try:
                cmd_in, data = self.rx_queue.get(timeout=0.4)
            except queue.Empty:
                if self.running:
                    print("ERROR -- RF: Failed to get response, command:")
                    print("\t", msg)
                return False

            if cmd_in != cmd_id:
                self.rx_queue.put((cmd_in, data))
                self.debug("Put msg back in queue, expected"
                           + f" cmd {cmd_id} but received cmd {cmd_in}")
                time.sleep(0.05)
            else:
                break

        # Return data, or just True if no data received
        return True if data == b'' else data

    # Command helpers --------------------------------------------------------
    def get_str(self, cmd):
        str = self.send_cmd(cmd)
        if str:
            str = str.decode()
        return str

    def get_int(self, cmd):
        val = self.send_cmd(cmd)
        if val:
            val = self.from_bytes(val)
        return val

    # Status updates ---------------------------------------------------------
    def get_power_measurement(self):
        ''' Updates power state '''
        data = self.send_cmd(b'\x10')
        if not data:
            return False

        state = {
            'forward': self.from_bytes(data[0:2]) / 10,
            'reflected': self.from_bytes(data[2:4]) / 10,
            'requested': self.from_bytes(data[4:6]) / 10,
            'temperature': self.from_bytes(data[6:8]) / 10,
            'load_power': self.from_bytes(data[8:10]) / 10,
            'vswr': data[10:13],
            'pmode': data[13]
        }
        for k, v in state.items():
            self.state[k] = v
        return True

    def get_status(self):
        data = self.send_cmd(b'\x18')
        if not data or isinstance(data, bool):
            return False

        work_mode = data[0]
        if work_mode & 2:
            work_mode = "local"
        elif work_mode & 1:
            work_mode = "gui"
        else:
            work_mode = "remote"

        flags = self.from_bytes(data[1:3])

        state = {
            'work_mode': work_mode,
            'pwr_on': bool(flags & 0b1),
            'over_heat': bool(flags & 0b10),
            'rev_limit': bool(flags & 0b100),
            'forward_limit': bool(flags & 0b1000),
            'rf_on': bool(flags & 0b10000),
            'burst_enable': bool(flags & 0b10000),
            'burst_select': bool(flags & 0b100000),
            'blank_loc_en': bool(flags & 0b1000000),
            'source': bool(flags & 0b10000000),
            'ilock': bool(flags & 0b100000000),
            'power_mode': bool(flags & 0b1000000000000),
        }
        for k, v in state.items():
            self.state[k] = v

        keys = 0
        keys += state['work_mode'] == "gui"
        keys += state['rf_on'] << 1
        keys += state['source'] << 2
        keys += state['blank_loc_en'] << 3
        keys += state['burst_enable'] << 4
        keys += state['burst_select'] << 5
        keys += state['power_mode'] << 6
        self.keys = keys

        return True

    # Commands from manual ---------------------------------------------------
    @property
    def version(self):
        versions = self.send_cmd(b'\x01')
        self.debug(f"Versions: \n\tfamily: {self.from_bytes(versions[0])}"
                   + f"\n\thardware: {self.from_bytes(versions[1])}"
                   + f"\n\tfirmware: {self.from_bytes(versions[2:])}")
        return versions

    @property
    def serial(self):
        return self.get_str(b'\x02')

    @property
    def device_name(self):
        return self.get_str(b'\x03')

    @property
    def scales(self):
        scales = self.send_cmd(b'\x0A')
        scales = scales.split(b'\x00')
        ret = []
        for scale in scales:
            ret.append(scale.decode())
        return ret

    @property
    def setpoint(self):
        return self.get_int(b'\x13') / 10

    @setpoint.setter
    def setpoint(self, pwr):
        ''' Set requested power in Watts'''
        # round(pwr*10) converts to 100 mW units as used by power supply
        return self.send_cmd(b'\x11', self.to_bytes(round(pwr*10), 2))

    # def set_percentage_power_level(self, pwr):
    #     # Cap between 0-100
    #     pwr = max(min(pwr, 100), 0)
    #     # Handle fractional power levels
    #     if pwr < 1:
    #         pwr *= 100
    #     # Convert to mW units
    #     pwr = round(pwr * 10)
    #     return self.send_cmd(b'\x14', self.to_bytes(pwr))

    # Keystate settings ------------------------------------------------------
    def set_key_state(self, keys):
        ''' Set new states for all keys at once
            (no way to do these individually) '''
        # Set key state
        success = self.send_cmd(b'\x19', self.to_bytes(keys))
        if not success:
            return False
        # Update state
        self.get_status()
        return True

    def set_key_bit(self, bit, on=True):
        if on:
            keys = self.keys | bit
        else:
            keys = ~self.keys
            keys = keys | bit
            keys = ~keys
        return self.set_key_state(keys)

    @property
    def control(self):
        return self.state['work_mode']

    @control.setter
    def control(self, control):
        self.set_key_bit(0b1, bool(control))

    @property
    def output(self):
        return self.state['rf_on']

    @output.setter
    def output(self, output):
        self.set_key_bit(0b10, bool(output))

    @property
    def source(self):
        return self.state['source']

    @source.setter
    def source(self, source):
        if source not in ("internal", "external"):
            raise ValueError('Source value must be "internal" or "external"')
        self.set_key_bit(0b100, source == "external")

    @property
    def blanking(self):
        return self.state['blank_loc_en']

    @blanking.setter
    def blanking(self, blanking):
        self.set_key_bit(0b1000, bool(blanking))

    @property
    def burst_enable(self):
        return self.state['burst_enable']

    @burst_enable.setter
    def burst_enable(self, burst):
        self.set_key_bit(0b10000, bool(burst))

    @property
    def burst_select(self):
        return self.state['burst_select']

    @burst_select.setter
    def burst_select(self, burst):
        self.set_key_bit(0b100000, bool(burst))

    @property
    def power_mode(self):
        return self.state['power_mode']

    @power_mode.setter
    def power_mode(self, mode):
        if mode not in ("load", "forward"):
            raise ValueError('Power mode must be "load" or "forward"')
        self.set_key_bit(0b1000000, mode == "load")

    # Specced methods --------------------------------------------------------
    def turnOn(self):
        self.on = True
        self.output = True

    def turnOff(self):
        self.on = False
        self.output = False

    def setFowardPower(self, pwr):
        self.setpoint = float(pwr)

    def readFowardPower(self):
        self.get_power_measurement()
        return self.state['forward']

    def readReflectedPower(self):
        self.get_power_measurement()
        return self.state['reflected']

    def read(self):
        self.currentFoward = self.readFowardPower()
        self.currentReflected = self.readReflectedPower()
        self.currentFormatted = self.currentFoward + '/' + self.currentReflected
        return self.currentFormatted


class TCPowerRFGenerator(AG0613_old):
    ''' Compatibility '''
    pass


class TCPowerRFGenrator(AG0613_old):
    ''' Typo compatibility '''
    pass


if __name__ =='__main__':
    Gen = AG0613_old(port = 'COM17')
    a = Gen.readReflectedPower()
    Gen.setForwardPower(35)
    Gen.turnOn()
    time.sleep(5)
    Gen.turnOff()
    time.sleep(5)
    Gen.setForwardPower(25)
    Gen.turnOn()
    time.sleep(5)
    Gen.turnOff()
    print(a)