import serial
import time
import pandas as pd
from serial.serialutil import SerialException


class startStopArduinoMotor():
    def __init__(self,comport):
        try:
            self.connection = serial.Serial('COM' + str(comport),115200) #create the connection
            self.connected = False
            self.handshake(self.connection) #start the connection

            self.currentSpeed = '1000'
            self.changeSpeed(self.currentSpeed)

        except SerialException:
            self.connected = False



    def start(self):
        if self.connected:
            self.connection.write(b'<1>')

    def stop(self):
        if self.connected:
            self.connection.write(b'<2>')

    def changeSpeed(self,delayTime):
        if self.connected:
            startChain = '<3,'
            command = startChain + str(delayTime) + '>'

            recipe = str.encode(command,"utf-8")

            self.connection.write(recipe)

    def handshake(self,device):
        time.sleep(1) #give everything a chance to conenct

        while not self.connected:

            if device.in_waiting >0: #check if there is anything in the serial buffer
                read = device.readline() #if there is, read it
                print(b'Grinder Arduino: '+ read.strip())
                if read == b'Are you there?\r\n': #if it is 'connected,' the mesage from the arduino
                    self.connected = True #confirm that the device is connected
                    print("Peter: Yes I am")
                    device.write(b'-connected-') #write back to start everything.
                    time.sleep(0.1)
                    print(b'Arduino :'+ device.readline().strip())
                    print('Together: We are now one')
                    time.sleep(1.5)
            else:
                time.sleep(0.1)
                pass



if __name__ == '__main__':

    m = startStopArduinoMotor(3)

