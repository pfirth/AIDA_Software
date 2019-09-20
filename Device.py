import serial
import time
import pandas as pd

from serial import SerialException



class SerialDevice():
    def __init__(self):
        pass

    def writeCommand(self,device,command):
        try:
            device.write(command)

        except SerialException:
            print('Arduino Mega Disconnected')

    def receiveData(self,device):
        incoming = b''
        try:
            while True:
                if device.in_waiting >0: #while there are characters in the buffer
                    incoming = device.readline().strip() #read the line and remove the end characters
                    return incoming

        except SerialException:
            print('Arduino Mega Disconnected: Close software, plug it in, and restart!')
            reconnect = 0




    def handshake(self,device):
        time.sleep(1) #give everything a chance to conenct

        while not self.connected:
            print('plc')
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
                    time.sleep(0.5)
            else:
                time.sleep(0.1)
                pass

        return 1
