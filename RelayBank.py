import serial
import time
import pandas as pd

class ArduinoRelayBank():

    def __init__(self,comport,numberofrelays):
        self.connection = serial.Serial('COM' + str(comport),115200) #create the connection
        self.connected = False
        self.handshake(self.connection)

    def handshake(self,device):
        time.sleep(1) #give everything a chance to conenct

        while not self.connected:
            if device.in_waiting >0: #check if there is anything in the serial buffer
                read = device.readline() #if there is, read it
                print(b'Arduino: '+ read.strip())
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
    def updatebank(self,bankarray):
        self.connection.write(bankarray)
        self.__receivedata(b'Bank Updated')

    def alloff(self):
        self.updatebank(b'<2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1>')

    def __receivedata(self,confirmcommand):
        while True:
            if self.connection.in_waiting >0:
                rec =  self.connection.readline().strip()
                if rec == confirmcommand:
                    break

if __name__ == "__main__":
    relay = ArduinoRelayBank(3,16)
    relay.updatebank(b'<2,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0>')
    #relay.alloff()
    #time.sleep(2)
    #relay.alloff()
