from __future__ import division
import serial
import time
from ArduinoMegaPLC import ArduinoMegaPLC
import queue
import serial
import threading
import time
from power_supply import PowerSupply
import binascii
import struct

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

POWER30 = bytearray(b'\x97\x06\xAA\x01\x11\x2C\01\x5F')
POWER100 = bytearray(b'\x97\x06\xAA\x01\x11\xE8\03\x6C')
print(binascii.hexlify(POWER30))

setpower('50.0')

'''Power30 = bytearray(b'\x97\x06\xAA\x01\x11\x2C\01\x5F')
POWER30_NCS = bytearray(b'\x97\x06\xAA\x01\x11\x2C\01')

POWER100 = bytearray(b'\x97\x06\xAA\x01\x11\xE8\03\x6C')
POWER100_NCS = bytearray(b'\x97\x06\xAA\x01\x11\xE8\03')

SETPOWER_HEAD = bytearray(b'\x97\x06')
SETPOWER_BASE = bytearray(b'\xAA\x01\x11')

CS = crc8(POWER30_NCS)
POWER30_NCS.append(CS)

CS = crc8(POWER100_NCS)
POWER100_NCS.append(CS)

#print(binascii.hexlify(POWER100_NCS))
print(binascii.hexlify(POWER100))


a = struct.pack('<h',1000)
print(binascii.hexlify(a))

POWER100 = bytearray(b'\x97\x06\xAA\x01\x11')
POWER100.extend(a)
print(binascii.hexlify(POWER100))

CS = crc8(POWER100)
POWER100.append(CS)
print(binascii.hexlify(POWER100))'''