from __future__ import division
import serial
import time
from ArduinoMegaPLC import ArduinoMegaPLC
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
        #setpoint = min(max(setpoint, self.min_power), self.max_power)
        return self.send_cmd(0x5341, int(setpoint))

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

if __name__ == '__main__':
    '''PLC = ArduinoMegaPLC(3)
    RFX = RFX600(PLC,3,1,2,8,0,600,1)

    RFX.setFowardPower(72)
    RFX.turnOn()
    time.sleep(1.5)
    PLC.getAnalogData()

    print(RFX.read())

    RFX.turnOff()'''

    gen = TCPowerRFGenrator(0, 600, 'COM18', debug=False)
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

