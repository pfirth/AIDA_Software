from __future__ import division
import serial
import time
from ArduinoMegaPLC import ArduinoMegaPLC

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

if __name__ == '__main__':
    PLC = ArduinoMegaPLC(3)
    RFX = RFX600(PLC,3,1,2,8,0,600,1)

    RFX.setFowardPower(72)
    RFX.turnOn()
    time.sleep(1.5)
    PLC.getAnalogData()

    print(RFX.read())

    RFX.turnOff()

