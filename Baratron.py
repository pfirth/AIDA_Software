import serial
from serial import SerialException
import time
import binascii
import codecs
from ArduinoMegaPLC import ArduinoMegaPLC
from Valve import Valve

class Baratron():

    def __init__(self):
        self.min = ''
        self.max = ''
        self.currentPressure = ''

    def read(self):
        pass

class analogBaratron():
    def __init__(self,PLC,readAddress,min,max,slot):
        self.PLC = PLC
        self.readAddress = readAddress
        self.min = min
        self.max = max
        self.slot = slot
        self.currentRead = '0.00'

    def read(self):
        ret = str("{0:.2f}".format(self.PLC.analogPercents[self.readAddress]*self.max))
        self.currentRead = ret
        return ret


class valveBaratron:
    def __init__(self,valve,min,max,slot):

        self.valve = valve
        self.min = min
        self.max = max
        self.slot = slot
        self.currentRead = '0.00'

    def read(self):
        ret = "{0:.2f}".format(float(self.valve.getPressure()))
        self.currentRead = ret
        return ret

if __name__ == '__main__':
    v = Valve(15)
    B = valveBaratron(v,0,10000)


    print(B.read())
