# Power supply communication template
# Dave Matthews, Swift Coat Inc, Nov 2021

# TODO: support Python context manager

import serial


class Device(object):
    def __init__(self, verbose=False):
        super().__init__()
        self.verbose = verbose

    def debug(self, *msgs):
        if self.verbose:
            print(*msgs)


class SerialDevice(Device):
    BYTEORDER = "big"

    ACK = None
    NAK = None

    def __init__(self,
                 port=None,
                 baud=9600,
                 parity=serial.PARITY_NONE,
                 timeout=1,
                 verbose=False):

        super().__init__(verbose=verbose)
        self.port = port
        self.baud = baud
        self.parity = parity
        self.timeout = timeout

        if port:
            self.connect()

    def from_bytes(self, value):
        ''' Takes bytes, returns int '''
        return int.from_bytes(value, self.BYTEORDER)

    def to_bytes(self, value, length=1):
        ''' Takes int and length, returns bytestring '''
        return value.to_bytes(length, self.BYTEORDER)

    def connect(self):
        ''' Establish a normal, non-threaded serial connection '''
        ser = serial.Serial(
            self.port,
            self.baud,
            parity=self.parity,
            timeout=self.timeout)
        assert ser is not None, f"Connection failed on port {self.port}"
        self.ser = ser

    def disconnect(self):
        if self.ser:
            self.ser.close()


class PowerSupply(SerialDevice):
    pass

    @property
    def ReadForwardPower(self):
        raise NotImplementedError()