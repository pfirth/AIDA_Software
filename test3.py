<<<<<<< HEAD
import datetime

D = str(datetime.datetime.now())
D = D.split(' ')[0]
Y,M,D = D.split('-')
ID = 'PF' + Y[2:] + M + D+'-'

print(ID)
=======
from __future__ import division
import serial
import time
from ArduinoMegaPLC import ArduinoMegaPLC
import queue
import serial
import threading
import time
from power_supply import PowerSupply
import struct
import binascii


class RFGenerator():
    def __init__(self, min_power, max_power, port, baud=19200,
                 parity=serial.PARITY_NONE,
                 timeout=0.2, slot=0):

        self.min = min
        self.max = max
        self.slot = slot

        self.currentSet = '0'
        self.currentFoward = '0'
        self.currentFormatted = ''
        self.currentReflected = ''

        self.on = False

        self.TXQ = queue.SimpleQueue()

        self.ser = serial.Serial(port, baud, timeout=timeout, parity=parity)
        self.com_thread = threading.Thread(target=self.comloop)
        self.com_thread.start()

    def comloop(self):
        GETSTATE = bytearray(b'\x97\x04\xAA\x01\x18\xEF')
        FORREV = bytearray(b'\x97\x04\xAA\x01\x10\x2D')
        Power100 = bytearray(b'\x97\x06\xAA\x01\x11\xE8\03\x6C')
        RFOff = bytearray(b'\x97\x05\xAA\x01\x19\x01\xFF')

        self.ser.write(RFOff)
        while self.ser.inWaiting() == 0:
            pass
        while self.ser.inWaiting() > 0:
            self.ser.read()
        self.ser.write(Power100)
        while self.ser.inWaiting() == 0:
            pass
        while self.ser.inWaiting() > 0:
            self.ser.read()

        while True:
            r = bytearray()
            #if there are no commands to write
            if self.TXQ.empty():
                self.ser.write(FORREV)

                while self.ser.inWaiting() == 0:
                    pass
                while self.ser.inWaiting() >0:
                    r.extend(self.ser.read())

                    self.currentFoward = str(int.from_bytes(r[5:7], byteorder='little') / 10)
                    self.currentReflected = str(int.from_bytes(r[7:10], byteorder='little') / 10)

                    print('fwd:')
                    print(self.currentFoward)
                    print('rev:')
                    print(self.currentReflected)

            #if there is a command
            else:
                print('in here')
                COMMAND = self.TXQ.get()
                print(COMMAND)
                self.ser.write(COMMAND)

    def crc8(self,msg):
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

    def turnOn(self):
        RFOn = bytearray(b'\x97\x05\xAA\x01\x19\x03\x43')
        self.TXQ.put(RFOn)
        self.on = True

    def turnOff(self):
        RFOff = bytearray(b'\x97\x05\xAA\x01\x19\x01\xFF')
        self.TXQ.put(RFOff)
        self.on = False

    def setFowardPower(self,powerSP):
        SETPOWER_HEAD = bytearray(b'\x97\x06')
        SETPOWER_BASE = bytearray(b'\xAA\x01\x11')

        powerSP = int(float(powerSP)) * 10

        binSP = struct.pack('<h', powerSP)

        SETPOWER_HEAD.extend(SETPOWER_BASE)
        SETPOWER_HEAD.extend(binSP)

        CS = self.crc8(SETPOWER_HEAD)
        SETPOWER_HEAD.append(CS)

        self.TXQ.put(SETPOWER_HEAD)

    def readFowardPower(self):
        pass

    def readReflectedPower(self):
        pass

    def read(self):
        return self.currentFoward + '/' + self.currentReflected



if __name__ == '__main__':
    AG = RFGenerator(min_power=0, max_power=600,port = 'COM12')

    time.sleep(3)

    AG.turnOn()
    time.sleep(5)
    AG.turnOff()
    time.sleep(5)
    AG.setFowardPower(154)
    AG.turnOn()
    time.sleep(3)
    AG.turnOff()
>>>>>>> origin/SC500-Recipe
