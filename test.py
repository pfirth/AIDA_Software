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

def setpower(powerSP):
    SETPOWER_HEAD = bytearray(b'\x97\x06')
    SETPOWER_BASE = bytearray(b'\xAA\x01\x11')

    powerSP = int(float(powerSP))*10

    binSP = struct.pack('<h', powerSP)

    SETPOWER_HEAD.extend(SETPOWER_BASE)
    SETPOWER_HEAD.extend(binSP)

    CS = crc8(SETPOWER_HEAD)
    SETPOWER_HEAD.append(CS)

    return SETPOWER_HEAD

def getfwdrev(ser):

    r = bytearray()
    COMMAND = bytearray(b'\x97\x04\xAA\x01\x10\x2D')

    ser.write(COMMAND)
    time.sleep(1)

    while ser.inWaiting() > 0:
        r.extend(ser.read())

    a = binascii.hexlify(r)
    print('asdf')
    print(a)


    print('fwd:')
    print(int.from_bytes(r[5:7], byteorder='little') / 10)
    print('rev:')
    print(int.from_bytes(r[7:10], byteorder='little') / 10)


class AG0163_old():
    def __init__(self):
        pass

min_power=0
max_power=600
port=None
baud=19200
parity=serial.PARITY_NONE
timeout=0.2
line_term=''
verbose=False

ser = serial.Serial('COM12', baud, timeout=timeout)

getState = bytearray(b'\x97\x04\xAA\x01\x18\xEF')

RFOff = bytearray(b'\x97\x05\xAA\x01\x19\x01\xFF')
RFOn = bytearray(b'\x97\x05\xAA\x01\x19\x03\x43')

Power30 = bytearray(b'\x97\x06\xAA\x01\x11\x2C\01\x5F')
Power100 = bytearray(b'\x97\x06\xAA\x01\x11\xE8\03\x6C')


TXQ = queue.SimpleQueue()

if __name__ == '__main__':
    COMMAND = bytearray(b'\x97\x04\xAA\x01\x10\x2D')
    ser.write(Power100)
    ser.write(RFOn)
    time.sleep(0.1)
    while ser.inWaiting() > 0:
        r = ser.read()
        print(r)
    time.sleep(3)

    getfwdrev(ser)


'''time.sleep(1)
ser.write(COMMAND)
time.sleep(0.5)
r =bytearray()

while ser.inWaiting() > 0:
    r.extend(ser.read())
a = binascii.hexlify(r)
print('asdf')
print(a)
print(binascii.hexlify(r[5:7]))
print(int.from_bytes(r[5:7], byteorder='little')/10)
print(int.from_bytes(r[7:10], byteorder='little') / 10)
#print(binascii.hexlify(a[0]))'''

'''ser.write(RFOff)
count = 0
ison = False
is30 = False

while True:
    if TXQ.empty():
        ser.write(getState)

        while ser.inWaiting()>0:
            r = ser.read()


    count+=1
    print(count)
    if count >30:
        count = 0
        if ison:
            ser.write(RFOff)
            ison = False

        else:
            if is30:
                ser.write(Power30)
                is30 = False
            else:
                ser.write(setpower('312'))
                is30 = True

            while ser.inWaiting() > 0:
                r = ser.read()

            ser.write(RFOn)
            ison = True

            while ser.inWaiting() > 0:
                r = ser.read()

    time.sleep(0.1)'''