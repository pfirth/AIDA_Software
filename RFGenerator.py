from __future__ import division
import serial
import time
from ArduinoMegaPLC import ArduinoMegaPLC
import queue
import serial
import threading
import time
import math
import serial
from bidict import bidict
from power_supply import PowerSupply
import queue
import serial
import threading
import time

class RFGenerator():
    def __init__(self):
        pass
    def turnOn(self):
        pass
    def turnOFf(self):
        pass
    def setFowardPower(self):
        pass
    def readFowardPower(self):
        pass
    def readReflectedPower(self):
        pass

class RFX600():
    def __init__(self,arduinoPLC,forward_set_channel,forward_read_channel,reflected_read_channel,on_off_channel,
                 min,max,slot):

        self.arduinoPLC = arduinoPLC

        self.forward_set_channel = forward_set_channel
        self.forward_read_channel = forward_read_channel
        self.reflected_read_channel = reflected_read_channel
        self.on_off_channel = on_off_channel
        self.min = min
        self.max = max
        self.slot = slot

        self.currentSet = '0'
        self.currentFoward = '0'
        self.currentFormatted = ''
        self.currentReflected = ''

        self.on = False

    def turnOn(self):
        self.arduinoPLC.relayCurrent[self.on_off_channel] = '1'
        self.arduinoPLC.updateRelayBank()
        self.on = True

    def turnOff(self):
        self.arduinoPLC.relayCurrent[self.on_off_channel] = '0'
        self.arduinoPLC.updateRelayBank()
        self.on = False

    def setFowardPower(self,setPoint):
        voltage = 5*(float(setPoint)/self.max)
        self.currentSet = setPoint
        self.arduinoPLC.changeVoltage(self.forward_set_channel,voltage)

    def readFowardPower(self):
        return str("{0:.0f}".format(self.arduinoPLC.analogPercents[self.forward_read_channel]*self.max))

    def readReflectedPower(self):
        return str("{0:.0f}".format(self.arduinoPLC.analogPercents[self.reflected_read_channel]*self.max))

    def read(self):
        self.currentFoward = self.readFowardPower()
        self.currentReflected = self.readReflectedPower()
        self.currentFormatted = self.currentFoward + '/' + self.currentReflected
        return self.currentFormatted

class TCPowerRFGenrator(object):
    BYTEORDER   = 'big'

    ACK         = 0x2A.to_bytes(1, BYTEORDER)
    NACK        = 0x3F.to_bytes(1, BYTEORDER)

    CMD_HEAD    = 0x43.to_bytes(1, BYTEORDER)
    CMD_ADDR    = 0x01.to_bytes(1, BYTEORDER)
    RSP_HEAD    = 0x52.to_bytes(1, BYTEORDER)

    MAX_CAP_COUNTS = 1005.  # Max digital readout for both caps
    MAX_CAP_VDC = 5.  # Max VDC for both caps (actual is higher)
    MIN_LOAD_VDC = 0.065  # Minimum actual VDC for load cap
    MIN_TUNE_VDC = 0.095  # Minimum actual VDC for tune cap
    CAP_F = MAX_CAP_VDC / MAX_CAP_COUNTS  # Digital -> VDC

    FMT_FLOAT = '{0:.0f}'

    def __init__(self, min_power, max_power, port, baud=38400, timeout=0.2,
                 line_term='', readonly=False, debug=False,slot = 0):
        # Params
        self.debug = debug
        self.max_power = max_power
        self.min_power = min_power
        self.readonly = readonly

        # Serial communication
        self.baud = baud
        self.line_term = line_term
        self.port = port
        self.timeout = timeout

        # Com thread
        self.tx_queue = queue.SimpleQueue()
        self.rx_queue = queue.SimpleQueue()
        self.running = True
        self.com_thread = threading.Thread(target=self.__com_loop)
        self.com_thread.start()

        self.slot = slot
        self.currentSet = '0'
        self.currentFoward = '0'
        self.currentFormatted = ''
        self.currentReflected = ''
        self.on = False

        # Initialize
        if not readonly:
            # Request control
            success = self.requestControl()
            # Set power limit on hardware (also enforced in setForwardPower)
            if success:
                success = self.setForwardPowerLimit(self.max_power)
            if not success:
                print("WARNING -- RF: Generator initialization failed")
                self.stop()

    def __com_loop(self):
        ''' Serial communication loop
        - Sends commands from self.tx_queue or a heartbeat message if no
        command shows up in tx_queue for over one second.
        - Places responces in self.rx_queue. Response includes data, if
        expected, or just an acknowledgement message if no data expected.
        - tx_queue messages are tuples:
            (bytestring to send, bool whether data is expected)
        - rx_queue messages are tuples:
            (command id, response content)
        - Continues until self.running == False. '''

        # Connect
        try:
            ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        except serial.SerialException as e:
            print("RF: Failed to connect")
            raise e

        # Run send/receive loop until disconnect
        while self.running:
            # Wait one second for a real message, otherwise send heartbeat
            try:
                msg, read = self.tx_queue.get(timeout=1.0)
                heartbeat = False
                if self.debug:
                    print("> " + str(msg))
            except queue.Empty:
                msg, read = self.assemble_cmd(0x4250), False
                heartbeat = True
            ser.write(msg)
            cmd_id = msg[2:4]   # Save command id for response queue

            # Read until finding an acknowledgement
            msg = ser.read(1)
            while msg not in (self.ACK, self.NACK):
                if self.debug:
                    print("< " + str(msg) + " (discarded, waiting for ACK)")
                msg = ser.read(1)

            # Don't pollute the queue if this is just a heartbeat
            if heartbeat:
                continue

            # If no response expected, put ack in queue and continue
            if self.debug:
                print("< " + 'OK' if msg == self.ACK else 'NOT OK')
            if not read or msg != self.ACK:
                self.rx_queue.put((cmd_id, msg))
                continue

            # Read until finding a response byte
            msg = ser.read(1)
            while msg != self.RSP_HEAD:
                if self.debug:
                    print("< " + str(head) + " (discarded, waiting for resp)")
                msg = ser.read(1)
            # Address byte
            msg += ser.read(1)
            # Data length (2 bytes)
            len = ser.read(2)
            msg += len
            # Data (variable length)
            data = ser.read(self.from_bytes(len))
            msg += data
            # Checksum (2 bytes)
            chksum = ser.read(2)
            if sum(msg) != self.from_bytes(chksum):
                print("WARNING -- RF: Bad checksum received, check for errors")

            # Put data in queue
            self.rx_queue.put((cmd_id, data))
            if self.debug:
                print("< ", msg + chksum)

        # Cleanup
        ser.close()

    # Internal methods -----------------------------------------------------
    def from_bytes(self, v):
        ''' Helper function. Returns an int from bytes. '''
        return int.from_bytes(v, self.BYTEORDER)

    def to_bytes(self, v, l):
        ''' Helper function. Returns bytestring from int and length. '''
        return v.to_bytes(l, self.BYTEORDER)

    def assemble_cmd(self, cmd_id, parm1=0, parm2=0):
        ''' Internal function to format commands for sending. '''
        msg = self.CMD_HEAD + self.CMD_ADDR     # Header + address
        msg += self.to_bytes(cmd_id, 2)         # Command ID
        msg += self.to_bytes(parm1, 2)          # Param 1
        msg += self.to_bytes(parm2, 2)          # Param 2
        msg += self.to_bytes(sum(msg), 2)       # Checksum
        return msg

    def send_cmd(self, cmd_id, parm1=0x00, parm2=0x00, read=False):
        ''' Format and send a command, then wait for and return response.
        Returns data, if expected; otherwise returns bool representing
        whether command was acknowledged successfully.'''

        # Assemble and send command
        msg = self.assemble_cmd(cmd_id, parm1, parm2)
        self.tx_queue.put((msg, read))

        # Read receive queue until a response matches the correct id
        id = b'\x00'
        while self.from_bytes(id) != cmd_id:
            try:
                id, val = self.rx_queue.get(timeout=2)
            except queue.Empty:
                print("ERROR -- RF: Failed to get response, command below.")
                print("\t", msg)
                return False

        # Return data if requested, or whether ACK signal was okay otherwise
        if read:
            ret = val
        else:
            ret = val == self.ACK
        return ret

    # Misc control ---------------------------------------------------------
    def stop(self):
        ''' Release control, then set flag to close com loop. '''
        self.releaseControl()
        time.sleep(2)
        self.running = False

    def ping(self):
        ''' Returns true if unit will acknowledge commands. '''
        return self.send_cmd(0x4250)

    def requestControl(self):
        ''' Returns True if control was granted, False otherwise. '''
        status = self.send_cmd(0x4243, 0x5555, read=True)
        return self.from_bytes(status) == 1

    def releaseControl(self):
        ''' Returns True on success. Even if this fails, unit will
        automatically return control if heartbeat stops for 2 seconds. '''
        status = self.send_cmd(0x4243, read=True)
        return self.from_bytes(status) == 0

    def getStatus(self):
        ''' Returns [STATUS] [TEMP] [OPMODE] [TUNER], 2 bytes each '''
        return self.send_cmd(0x4753, read=True)

    def getTunerStatus(self):
        ''' Returns [STATUS] [LC POS] [TC POS] [VDC] [PRESET], 2 bytes each '''
        return self.send_cmd(0x4754, read=True)

    # On/Off ---------------------------------------------------------------
    def rf(self, on=False):
        ''' Turns rf power on/off, returns success either way. '''
        return self.send_cmd(0x4252, 0x5555 if on else 0x0000)

    def turnOn(self):
        ''' Alias for rf '''
        self.on = True
        print('Gen: ' + str(self.port))
        return self.rf(True)

    def turnOff(self):
        ''' Alias for rf '''
        self.on = False
        return self.rf(False)

    # Power ----------------------------------------------------------------
    def readPower(self):
        ''' Returns tuple of current (forward, refected, load) power. '''
        ret = self.send_cmd(0x4750, read=True)
        fwd = self.from_bytes(ret[0:2]) / 10
        rev = self.from_bytes(ret[2:4]) / 10
        load = self.from_bytes(ret[4:6]) / 10
        return fwd, rev, load

    def readFowardPower(self):
        ''' Alias of readPower that only returns forward power as a string. '''
        return self.FMT_FLOAT.format(self.readPower()[0])

    def readForwardPowerSetpoint(self):
        ''' Returns current forward power setpoint, not actual power. '''
        setpt = self.from_bytes(self.send_cmd(0x474C, read=True)) / 10
        return self.FMT_FLOAT.format(setpt)

    def readReflectedPower(self):
        ''' Alias of readPower that only returns refl power as a string. '''
        return self.FMT_FLOAT.format(self.readPower()[1])

    def setFowardPower(self, setpoint):
        ''' Set forward power setpoint.
        Enforces min/max power limits from init. '''
        self.currentSet = setpoint
        sp = '{:.0f}'.format(float(setpoint))
        #setpoint = min(max(setpoint, self.min_power), self.max_power)
        return self.send_cmd(0x5341, int(sp))

    def setForwardPowerLimit(self, limit):
        ''' Set forward power limit in hardware. '''
        limit = min(max(limit, self.min_power), self.max_power)
        return self.send_cmd(0x5355, 1, limit)

    def setReflectedPowerLimit(self, limit):
        ''' Set reflected power limit in hardware. '''
        return self.send_cmd(0x5355, 2, limit)

    def read(self):
        self.currentFoward = self.readFowardPower()
        self.currentReflected = self.readReflectedPower()
        self.currentFormatted = self.currentFoward + '/' + self.currentReflected
        return self.currentFormatted

    def getTunerStatus(self):
        ''' Returns [STATUS] [LC POS] [TC POS] [VDC] [PRESET], 2 bytes each '''
        # Get tuner status
        response = self.send_cmd(0x4754, read=True)
        # Convert from bytes to int
        ret = []
        for i in range(0, len(response), 2):
            ret.append(self.from_bytes(response[i:i + 2]))
        # Convert load/tune positions from counts to VDC
        ret[1] = ret[1] * CAP_F + MIN_LOAD_VDC
        ret[2] = ret[2] * CAP_F + MIN_TUNE_VDC
        return ret

    def getLoad(self):
        ''' Return load cap position in VDC via getTunerStatus() '''
        return self.getTunerStatus()[1]

    def getTune(self):
        ''' Return load cap position in VDC via getTunerStatus() '''
        return self.getTunerStatus()[2]

    def getTuneLoad(self):
        ''' Return [tune, load] cap positions in VDC via getTunerStatus() '''
        return self.getTunerStatus()[1:3]

# T&C Power Conversion AG 0613 600W RF Generator, "old style" communication
# Dave Matthews, Swift Coat Inc, Nov 2021

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

    def __init__(self, slot=0,
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

        # Software integration
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
        self.keys = self.KEYS_INIT  # Stores key states as a binary value

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
            cmd_id = msg[4]  # Save command id for response queue

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
            data = msg[5:-1]  # will be b'' if no data received
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
        tx = self.CMD_HEAD  # Head
        tx += self.to_bytes(len(frame) + 2, 1)  # Length (min 4)
        tx += self.CMD_CTRL  # Ctrl
        tx += frame  # Sub-frame
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
        return self.send_cmd(b'\x11', self.to_bytes(round(pwr * 10), 2))

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
        print('ononon')
        self.on = True
        self.output = True

    def turnOff(self):
        self.on = False
        self.output = False

    def setFowardPower(self, pwr):
        self.currentSet = str(pwr)
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
        self.currentFormatted = str(self.currentFoward) + '/' + str(self.currentReflected)
        return self.currentFormatted


class TCPowerRFGenerator(AG0613_old):
    ''' Compatibility '''
    pass


class TCPowerRFGenrator(AG0613_old):
    ''' Typo compatibility '''
    pass


class Seren301(RFGenerator):
    ''' Seren301 RF Generator
        Connection: RS232 via DB9 on rear of unit
        This software will take control of the unit whether it is in serial
        mode or not, and will return it to panel control on proper shutdown.
    '''

    ACK     = b'\r'     # Manual says this should be '>' but it seems wrong
    NACK    = b'N'

    def __init__(self,
                 min_power,
                 max_power,
                 port,
                 baud=19200,
                 timeout=0.2,
                 line_term='\r',
                 max_reflected=300,
                 readonly=False,
                 debug=False):

        # Serial settings
        self.baud = baud
        self.line_term = line_term
        self.port = port
        self.timeout = timeout

        # Params
        self.max_power = max_power
        self.min_power = min_power
        self.max_reflected = min(max_power, max_reflected)
        self.readonly = readonly
        self.debug = debug

        # Com thread
        self.tx_queue = queue.SimpleQueue()
        self.rx_queue = queue.SimpleQueue()
        self.running = True
        self.com_thread = threading.Thread(target=self.__com_loop)
        self.com_thread.start()

        # Initialize TODO
        self.status = {}    # Refreshed on every self.getStatus() call
        if not readonly:
            # Try to get control
            success = self.requestControl()
            if not success:
                print("WARNING -- RF: Generator initialization failed")
                self.stop()
                return
            # Init status
            self.getStatus()
            # TODO: Init control mode and other stuff
            # TODO: Check for error conditions


    def __com_loop(self):
        ''' Serial communication loop
        - Sends commands from self.tx_queue or a heartbeat message if no
        command shows up in tx_queue for over one second.
        - Places responces in self.rx_queue. Response includes data, if
        expected, or just an acknowledgement message if no data expected.
        - tx_queue messages are tuples:
            (command name, data to send, bool whether data should be received)
        - rx_queue messages are tuples:
            (command name, response)
        - Continues until self.running == False. '''

        # Connect
        try:
            ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        except serial.SerialException as e:
            print("ERROR -- RF: Failed to connect")
            raise e

        # Run send/receive loop until disconnect
        while self.running:
            # Wait one second for a message, otherwise verify still running
            try:
                # Save command and param separately in case of echo mode
                # TODO: Implement echo mode for extra verification
                cmd, param, read = self.tx_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            # Send a message if one was found
            msg = self.assemble_cmd(cmd, param)
            if self.debug:
                print("> " + msg.decode())
            ser.write(msg)

            # Read response
            msg = ser.readline()

            # If command failed, put False in rx queue
            if msg == self.NACK:
                val = False
                if self.debug:
                    print("< NOT OK")

            # If command succeeded and no further data expected, put True
            elif not read:
                val = True
                if self.debug:
                    print("< OK")

            # If command successful and data expected, put data on rx queue
            else:
                val = msg.decode()
                if self.debug:
                    print("< ", val)
            self.rx_queue.put((cmd, val))

        # Cleanup
        ser.close()

    # Internal methods -----------------------------------------------------
    def assemble_cmd(self, cmd, param=None):
        ''' Internal function to format commands for sending. '''
        msg = param + ' ' if param else ''
        msg += cmd
        msg += self.line_term
        return msg.encode('ascii')

    def send_cmd(self, cmd, param=None, read=False):
        ''' Format and send a command, then wait for and return response.
        Returns data, if expected; otherwise returns bool representing
        whether command was acknowledged successfully.'''

        def check_queue():
            try:
                msg = self.rx_queue.get(timeout=2.0)
            except queue.Empty as e:
                print("ERROR -- RF: Failed to get response")
                print("\t", msg)
                self.running = False
                raise e
            return msg

        # Put command in tx queue as tuple
        self.tx_queue.put((cmd, param, read))

        # Read receive queue, verify response is from correct command
        ret_cmd, val = check_queue()
        attempts = 1
        while ret_cmd != cmd:
            print("Warning -- RF: Received unexpected message, discarding")
            print("\tmsg: " + ret_cmd + ' ' + val)
            if attempts > 5:
                print("ERROR -- RF: Could not get expected response, quitting")
                print("\t", msg)
                self.running = False
                raise Exception()
            ret_cmd, val = check_queue()
            attempts += 1

        return val

    # Misc control ---------------------------------------------------------
    def stop(self):
        ''' Release control, then set flag to close com loop. '''
        self.releaseControl()
        time.sleep(2)
        self.running = False

    def ping(self):
        ''' Returns true if unit will acknowledge commands. '''
        return self.send_cmd('Q')

    def requestControl(self):
        ''' Returns True if control was granted, False otherwise. '''
        return self.send_cmd('***')

    def releaseControl(self):
        ''' Returns True on success. Even if this fails, unit will
        automatically return control if heartbeat stops for 2 seconds. '''
        return self.send_cmd('PANEL')

    def getStatus(self):
        ''' Returns status string: 'ABCDEFG_aaaa_bbbb_ccc_dddd'
            A: Control, 0=front, 1=analog, 2=serial
            B: Feedback, 0=external, 3=internal
            C: Setpoint, 0=front, 1=analog, 2=serial
            D: Status flags
                Bit 3: RF, 0=off, 1=on
                Bit 2: Reflected limit, 0=inactive, 1=active
                Bit 1: Max power limit, 0=inactive, 1=active
                Bit 0: Pulse mode, 0=inactive, 1=active
            E: Status flags
                Bit 3: RF power alarm, 0=alarm, 1=RF on and ok
                Bit 2: Dissipation limit, 0=inactive, 1=active
                Bit 1: CEX, 0=master, 1=agent
                Bit 0: Pulse mode, 0=inactive, 1=active
            F: Status flags
                Bit 3: Unused
                Bit 2: Unused
                Bit 1: External interlock, 0=open, 1=ok
                Bit 0: Temperature alarm, 0=inactive, 1=active
            G: Unused
            aaaa: Setpoint, 1-4 characters, W
            bbbb: Forward power, 1-4 characters, W
            ccc: Reflected power, 1-3 characters, W
            dddd: Maximum power, 1-4 characters, W
        '''

        msg = self.send_cmd('Q', read=True)
        if not msg or not isinstance(msg, str):
            print("ERROR -- RF: No status response received")
            return False

        status = msg.split(' ')
        if len(status) != 5:
            print("ERROR -- RF: Can't parse status string:")
            print("\t" + msg)
            return False

        # A: Control, 0=front, 1=analog, 2=serial
        flags = status[0]
        info = int(flags[0])
        if info == 0:
            value = 'front'
        elif info == 1:
            value = 'analog'
        elif info == 2:
            value = 'serial'
        else:
            value = 'unknown'
            print("Warning -- RF: Control source unknown")
        self.status['control_source'] = value

        # B: Feedback, 0=external, 3=internal
        info = int(flags[1])
        if info == 0:
            value = 'external'
        elif info == 3:
            value = 'internal'
        else:
            value = 'unknown'
            print("Warning -- RF: Feedback source unknown")
        self.status['feedback_source'] = value

        # C: Setpoint, 0=front, 1=analog, 2=serial
        info = int(flags[2])
        if info == 0:
            value = 'front'
        elif info == 1:
            value = 'analog'
        elif info == 2:
            value = 'serial'
        else:
            value = 'unknown'
            print("Warning -- RF: Setpoint source unknown")
        self.status['setpoint_source'] = value

        # D: Status flags
        # TODO
        # info = int(flags[3])
        #     Bit 3: RF, 0=off, 1=on
        #     Bit 2: Reflected limit, 0=inactive, 1=active
        #     Bit 1: Max power limit, 0=inactive, 1=active
        #     Bit 0: Pulse mode, 0=inactive, 1=active

        # E: Status flags
        # TODO
        # info = int(flags[4])
        #     Bit 3: RF power alarm, 0=alarm, 1=RF on and ok
        #     Bit 2: Dissipation limit, 0=inactive, 1=active
        #     Bit 1: CEX, 0=master, 1=agent
        #     Bit 0: Pulse mode, 0=inactive, 1=active

        # F: Status flagsinfo = int(msg[3]) TODO
        # TODO
        # info = int(flags[5])
        #     Bit 3: Unused
        #     Bit 2: Unused
        #     Bit 1: External interlock, 0=open, 1=ok
        #     Bit 0: Temperature alarm, 0=inactive, 1=active

        set = int(status[1])
        fwd = int(status[2])
        ref = int(status[3])
        max = int(status[4])

        if set > self.max_power:
            print("Warning -- RF: Forward power setpoint above software maximum.")
            print("\tCurrent: {}, Maximum: {}".format(set, self.max_power))
            print("Attempting to reset to software maximum.")
            self.setForwardPower(self, self.max_power)

        if fwd > self.max_power:
            print("Warning -- RF: Forward power above software maximum.")
            print("\tCurrent: {}, Maximum: {}".format(set, self.max_power))
            print("Attempting to reset to software maximum.")
            self.setForwardPower(self, self.max_power)

        if ref > self.max_reflected:
            print("ERROR -- RF: Reflected power above software maximum.")
            print("\tCurrent: {}, Maximum: {}".format(set, self.max_reflected))
            print("Disabling RF power.")
            self.rf(False)

        if max > self.max_power:
            print("Info -- RF: Firmware max power is below software max.")
            print("\tFirmware: {}, Software: {}".format(max, self.max_reflected))

        self.status['setpoint'] = set
        self.status['forward'] = fwd
        self.status['reflected'] = ref
        self.status['maximum'] = max

        return True


    # On/Off ---------------------------------------------------------------
    def rf(self, on=False):
        ''' Turns rf power on/off, returns success either way. '''
        return self.send_cmd('G' if on else 'S')

    def turnOn(self):
        ''' Alias for rf '''
        return self.rf(True)

    def turnOff(self):
        ''' Alias for rf '''
        return self.rf(False)

    # Control --------------------------------------------------------------
    def readControlSource(self, source):
        self.getStatus()
        return self.status['control_source']

    def readFeedbackSource(self, source):
        self.getStatus()
        return self.status['feedback_source']

    def readSetpointSource(self, source):
        self.getStatus()
        return self.status['setpoint_source']


    # Power ----------------------------------------------------------------
    def readForwardPower(self):
        ''' Alias of readPower that only returns forward power as a string. '''
        self.getStatus()
        return self.status['forward']

    def readForwardPowerSetpoint(self):
        ''' Returns current forward power setpoint, not actual power. '''
        self.getStatus()
        return self.status['setpoint']

    def readReflectedPower(self):
        ''' Alias of readPower that only returns refl power as a string. '''
        self.getStatus()
        return self.status['reflected']

    def setForwardPower(self, setpoint):
        ''' Set forward power setpoint.
            Enforces min/max power limits from init. '''
        if setpoint > self.max_power:
            print("Warning -- RF: Attempted power setpoint above maximum. Using maximum instead.")
            print("\tAttempted: {}, Maximum: {}".format(setpoint, self.max_power))
            setpoint = max_power
        if setpoint < self.min_power:
            print("Warning -- RF: Attempted power setpoint below minimum. Using minimum instead.")
            print("\tAttempted: {}, Minimum: {}".format(setpoint, self.min_power))
            setpoint = max_power
        return self.send_cmd('W', str(setpoint).zfill(4))

    def setForwardPowerLimit(self, limit):
        ''' Set forward power limit in SOFTWARE ONLY
            This function is not supported by the hardware. '''
        limit = min(max(limit, self.min_power), self.max_power)
        self.max_power = limit
        return True

    def setReflectedPowerLimit(self, limit):
        ''' Set forward power limit in SOFTWARE ONLY
            This function is not supported by the hardware. '''
        limit = min(max(limit, self.min_power), self.max_power)
        self.max_reflected = limit
        return True

    def readBias(self):
        ''' Read DC bias voltage
            0? and V? are the same command '''
        return int(self.send_cmd('V?', read=True))

class AEPinnaclePlus(object):
    '''
    Pinnacle Plus+ DC Power Supply
    Serial communication
    Dave Matthews, Swift Coat Inc, Oct 2021
    Setup
    -- Port
    9 pin serial port labeled "AE Host". Located on AE Bus card, top rear of unit.
    If AE Bus card not present, can use 4-pin RJ14 jack.
    RJ14 cannot be used for communication if AE Bus card is present.
    -- DIP switch positions
    11110011 where 1=up, 0=down
    Switches 0-4: unit address 1
    5-6: baud 9600
    7: RS-232
    -- Communication, assuming DIP switch positions above
    Standard: RS-232
    Baud: 9600
    Parity: odd
    Start, data, stop bits: 1, 8, 1
    Byte order: Low-high
    Communication protocol
    Host (PC)                   Client (Power supply)
    ----                        ----
    Send packet
                                Receive packet, send ACK
    Receive ACK                 Send packet
    Receive packet, send ACK
                                Receive ACK, retransmit if NAK
    '''


    ack = b'\x06'
    nak = b'\x15'
    byteorder = "little"
    control_modes = bidict({
        "serial": b'\x02',      # Serial (Host) port
        "user": b'\x04',        # User port
        "panel": b'\x06'})      # Active control panel
    regulation_methods = bidict({
        "power": b'\x06',
        "voltage": b'\x07',
        "current": b'\x08'})
    regulation_decimals = {
        "power": 0,             # Watts (manual uses kilowatts)
        "voltage": 0,           # Volts
        "current": 2}           # Amps

    def __init__(self,min, max, slot, port=None, baud=19200, address=1, timeout=1, debug=False):
        self.debug = debug
        self.address = address  # Also sets _header via @property
        self.baud = baud
        self.port = port
        self.timeout = timeout
        self.ser = None
        if port:
            self.connect()


        self.slot = slot
        self.min = min
        self.max = max
        self.currentSet = 0
        self.on = False

    # Helper functions
    def print(self, msg):
        if self.debug:
            print(msg)

    def from_bytes(self, v):
        ''' Takes bytes, returns int '''
        return int.from_bytes(v, self.byteorder)

    # I/O
    def connect(self):
        ser = serial.Serial(
            self.port,
            self.baud,
            parity=serial.PARITY_ODD,
            timeout=self.timeout)
        if not ser:
            raise(Exception(f"Connection failed on port {self.port}"))
        self.ser = ser
        self.control_mode = "serial"
        self.regulation_method = "power"
        self.program_source = "internal"

    def disconnect(self):
        self.control_mode = "panel"
        if self.ser:
            self.ser.close()

    def write(self, cmd, data=None):
        ''' Packet structure
        -- Header, 1 byte
        5 bits: address of unit this packet is for / comes from
        3 bits: data byte count, 0-7 w/o checksum; use Length byte if > 7
        -- Command, 1 byte
        Command being given / replied to
        -- Length, 1 byte, optional; only used when header length bits == 111
        Data byte count, 0-255 w/o checksum
        -- Data, 0 to 255 bytes as specified above
        If no data requested, this will be a 1-byte CSR (response) code.
        CSR 0 = accepted
        -- Checksum, 1 byte
        Accumulated XOR value of all bytes up to, but not including, checksum
        Including checksum should force accumulated XOR == 0
        '''

        if not self.ser:
            return False

        n = 0
        while True:
            # Retries
            n += 1
            if n > 5:
                return False

            # Header and command bytes
            msg = bytearray([self._header, cmd])

            # Data and length bytes
            if data:
                # Convert to bytes
                if isinstance(data, bytes):
                    pass
                elif isinstance(data, int):
                    # Pack into minimum amount of bytes necessary
                    data = data.to_bytes(
                        math.floor(data/256) + 1, self.byteorder)
                elif isinstance(data, str):
                    data = data.encode()

                # Add data to msg with appropriate length
                length = len(data)
                if length < 7:
                    # Length fits in last 3 bits of header byte
                    msg[0] += length
                else:
                    # Length gets its own byte
                    msg[0] += 7
                    msg.append(length)
                msg += data

            # Checksum byte
            checksum = False
            for b in msg:
                checksum ^= b
            msg.append(checksum)

            self.print(f"> {msg}")
            self.ser.write(msg)

            # Verify receipt
            ack = self.ser.read()
            self.print(f"< {ack}, ack")
            if ack == self.ack:
                return True
            elif ack != self.nak:
                return False

    def readgen(self, cmd_chk=None):
        if not self.ser:
            return False

        def nak():
            self.ser.write(self.nak)  # NAK

        data = None
        n = 0
        while True:
            msg = bytearray()

            # Retries
            n += 1
            if n > 6:
                break

            # Header
            header = self.ser.read()
            self.print(f"> {header}, header")
            if not header or header[0] >> 3 != self._address:
                nak()
                continue
            msg += header

            # Command code
            cmd = self.ser.read()
            self.print(f"> {cmd}, command code")
            if not cmd or (cmd_chk and cmd[0] != cmd_chk):
                nak()
                continue
            msg += cmd

            # Data
            length = header[0] & 7
            if length > 0:
                # Get length from length byte if needed
                if length == 7:
                    length = self.ser.read()
                    msg += length
                    self.print(f"> {length}, length byte")
                # Get data
                data = self.ser.read(length)
                self.print(f"> {data}")
                msg += data

            # Checksum
            chk = self.ser.read()
            self.print(f"> {chk}, checksum")
            msg += chk
            checksum = 0
            for b in msg:
                checksum ^= b
            if checksum == 0:
                break
            nak()

        # ACK
        self.ser.write(self.ack)
        return data

    def command(self, cmd, data=None):
        ''' Write/read cycle. All commands generate an ACK and response packet.
        '''
        self.write(cmd, data)
        return self.readgen(cmd)

    # Test command
    def null(self):
        self.command(0)

    # Properties -------------------------------------------------------------

    # Test property
    @property
    def supply_type(self):
        return self.command(128).decode()

    # Unit to address
    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, address):
        ''' Set _address and prepare _header for read/write '''
        self._address = address
        self._header = address << 3     # First 5 bits of header byte

    # Control mode
    @property
    def control_mode(self):
        return self.control_modes.inverse[self.command(155)]

    @control_mode.setter
    def control_mode(self, mode):
        mode = mode.lower()
        if mode not in self.control_modes:
            raise(ValueError(f"Cannot set unknown control mode: {mode}"))
        self.command(14, self.control_modes[mode])

    @property
    def program_source(self):
        config = self.debug_config
        source = "internal" if config[0] & 128 == 0 else "external"
        return source

    @program_source.setter
    def program_source(self, source):
        ''' Source is set separately per control mode; this just sets all 3 '''
        err = ValueError(f"Can't set unknown program source: {source}")
        if not isinstance(source, str):
            raise err
        elif source == "internal":
            b = b'\x00'
        elif source == "external":
            b = b'\x01'
        else:
            raise err
        self.command(17, b + b'\x00\x01')

    # Output power state
    @property
    def debug_output(self):
        return self.command(161)

    @property
    def debug_status(self):
        return self.command(162)

    @property
    def debug_config(self):
        return self.command(163)

    @property
    def debug_faults(self):
        return self.command(208, b'\x00')

    @property
    def output(self):
        # command returns full process status; output is byte 1, bit 4
        return self.command(162)[0] & 8

    @output.setter
    def output(self, output):
        ''' Setting output to False will work even when in local control '''
        self.command(2 if output else 1)

    # Output regulation method
    @property
    def regulation_method(self):
        return self.regulation_methods.inverse[self.command(154)]

    @regulation_method.setter
    def regulation_method(self, method):
        method = method.lower()
        if method not in self.regulation_methods:
            raise(ValueError(f"Cannot set unknown regulation method: {method}"))
        self.command(3, self.regulation_methods[method])

    # Output setpoint
    @property
    def setpoint(self):
        # command returns setpoint (bytes 1-2) and regulation mode (byte 3)
        status = self.command(164)
        # Divide by appropriate number of decimal places for regulation method
        regulation_method = self.regulation_methods.inverse[bytes([status[2]])]
        setpoint = self.from_bytes(status[:2])
        setpoint /= 10 ** self.regulation_decimals[regulation_method]
        return setpoint

    @setpoint.setter
    def setpoint(self, setpoint):
        ''' Changing setpoint while power is on will obey any set ramp rate '''
        # Use appropriate number of decimal places for regulation method
        decimals = self.regulation_decimals[self.regulation_method]
        setpoint = setpoint/10
        setpoint = round(setpoint * 10**decimals)

        # Setpoint must be a two-byte value
        self.command(6, setpoint.to_bytes(2, self.byteorder))

    # Read-only power delivery
    # Can also request all 3 at once with cmd 168
    @property
    def forward_power(self):
        return self.from_bytes(self.command(165))         # Watts

    @property
    def forward_voltage(self):
        return self.from_bytes(self.command(166))         # Volts

    @property
    def forward_current(self):
        decimals = self.regulation_decimals["current"]
        return self.from_bytes(self.command(167)) / 10**decimals

    @property
    def arc_density(self):
        ''' Return total density of arcs per second (micro and hard arcs) '''
        resp = self.command(188)
        micro = self.from_bytes(resp[:2])
        hard = self.from_bytes(resp[2:])
        return micro + hard

    # Specced functions ------------------------------------------------------
    def turnOn(self):
        self.on = True
        self.output = True

    def turnOff(self):
        self.on = False
        self.output = False

    def setFowardPower(self, power):
        self.currentSet = power
        self.setpoint = float(power)

    def readFowardPower(self):
        return str(self.forward_power)

    def readReflectedPower(self):
        ''' Actually returns arc density per second '''
        return str(self.arc_density)

    def read(self):
        try:
            self.currentFoward = self.readFowardPower()
            self.currentReflected = self.readReflectedPower()
            self.currentFormatted = self.currentFoward + '/' + self.currentReflected
            return self.currentFormatted
        except TypeError:
            return('0/0')


if __name__ == '__main__':
    '''PLC = ArduinoMegaPLC(3)
    RFX = RFX600(PLC,3,1,2,8,0,600,1)

    RFX.setFowardPower(72)
    RFX.turnOn()
    time.sleep(1.5)
    PLC.getAnalogData()

    print(RFX.read())

    RFX.turnOff()'''

    gen = TCPowerRFGenrator(min_power=0, max_power = 600, port='COM18', slot = 0)
    #gen = Seren301(0, 300, 'COM18', debug=True)
    print("\tPing")
    print(gen.ping())
    print("\tSet forward power to 50")
    print(gen.setFowardPower(50))
    print("\tRead forward power")
    print(gen.readFowardPower())
    print("\tRead forward power setpoint")
    print(gen.readForwardPowerSetpoint())
    print("\tSleeping...")
    time.sleep(4)
    print("\tRF ON!")
    print(gen.turnOn())
    print("\tRead forward power")
    print(gen.readFowardPower())
    print("\tRead forward power setpoint")
    print(gen.readForwardPowerSetpoint())
    time.sleep(4)
    print("\tRead forward power")
    print(gen.readFowardPower())
    print("\tRF off")
    print(gen.turnOff())
    print("\tSet forward power to 10")
    print(gen.setFowardPower(10))
    print("\tRead forward power")
    print(gen.readFowardPower())
    print("\tRead forward power setpoint")
    print(gen.readForwardPowerSetpoint())
    time.sleep(4)
    gen.stop()

