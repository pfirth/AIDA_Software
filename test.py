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

import math
import serial
from bidict import bidict


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

    def __init__(self,min, max, slot, port=None, baud=9600, address=1, timeout=1, debug=False):
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
        self.currentFoward = self.readFowardPower()
        self.currentReflected = self.readReflectedPower()
        self.currentFormatted = self.currentFoward + '/' + self.currentReflected
        return self.currentFormatted

if __name__ == "__main__":
     import time
#
     pwr = AEPinnaclePlus(port='COM12', min = 0,max = 5000,slot = 1)
     print(pwr.supply_type)
     #pwr.setpoint = 123
#     print(pwr.control_mode)
#     print(pwr.regulation_method)
#     print(pwr.setpoint)
#     print(pwr.program_source)
#
#     # pwr.setpoint = 100
#     # print(pwr.setpoint)
#     # print(pwr.output)
#     # print(pwr.forward_power)
#     # print(pwr.readReflectedPower())

     time.sleep(1)
#     print(pwr.debug_output)
#     print(pwr.debug_status)
#     print(pwr.debug_config)
#     print(pwr.debug_faults)
#     # print(pwr.setpoint)
#     # print(pwr.output)
#     # print(pwr.forward_power)
#     # print(pwr.readReflectedPower())

#     pwr.disconnect()