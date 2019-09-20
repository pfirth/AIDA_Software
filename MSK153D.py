from __future__ import division
import serial
import time

class Valve():

    def __init__(self,port):
        '''Initialization requires that the port number of the 4-port USB to serial
        adapter be input (A,B,C,D) to start. This will be changed to work with different
        computers.

        Interacting with a Vat Valve via the service port.
        '''
        self.connection = serial.Serial('COM' + str(port),baudrate=9600,
                                        bytesize=serial.EIGHTBITS,stopbits = serial.STOPBITS_ONE,
                                        parity=serial.PARITY_NONE)
        self.interrupt = False
        self.DataDic = {}

    def __receivedata(self,confirm,confirmcommand):
        if confirm:
            while True:
                if self.connection.in_waiting >0:
                    rec =  str(self.connection.readline(),"utf-8").strip()
                    if rec == confirmcommand:
                        print(rec)
                        break
        else:

            a = ''
            time.sleep(0.15)
            while self.connection.in_waiting>0:
                a+=str(self.connection.read(),"utf-8")
            return a

    def getSensorConfiguration(self):
        self.connection.write(b'i:01\r\n')

        return self.__receivedata(False,'')

    def setSensorScale(self,maxSensorReadTorr):
        start = 's:01'
        a = '1'
        b = '0'
        c = maxSensorReadTorr

        #adding leading zeros to fit the 6 figure format on manual pg 63
        zeroAdd = 6 -len(c)
        for x in range(zeroAdd):
            c = '0'+c
        command = str.encode(start+a+b+c+'\r\n',"utf-8")
        self.connection.write(command)
        return self.__receivedata(False,'')

    def getSensorScale(self):
        self.connection.write(b'i:01\r\n')
        return self.__receivedata(False,'')

    def setSensorRange(self,range):
        start = 's:21'
        a = '2'
        b = range
        zeroAdd = 7 -len(b)
        b = '0'*zeroAdd + b

        command = str.encode(start+a + b + '\r\n',"utf-8")

        self.connection.write(command)

        return self.__receivedata(False,' ')

    def __Pressure_Conversion(self,P):
        '''converts a pressure in Torr to the appropriate ASII
        command'''''
        command = str(int(P*500000))
        #print command,P
        for x in range(7-len(command)):
            command = '0'+command
        #print command
        return 'S:0'+ command

    def getPressureSetpoint(self):
        self.connection.write(b'i:38\r\n')
        return self.__receivedata(False,'')

    def setPressure(self,slot,Pressure):
        '''Sends the pressure setpoint to the valve
        Pressure should be supplied in mTorr'''
        self.DataDic[slot]['currentSet'] = Pressure

        start = 'S:0'
        a = Pressure

        zeroAdd = 7 - len(a)

        a = '0'*zeroAdd + a
        print(start+a)
        command = str.encode(start+a+'\r\n',"utf-8")

        self.connection.write(command)

        return self.__receivedata(False,'')

    def pressureControlStatus(self):

        self.connection.write(b'i:36\r\n')
        return self.__receivedata(False,'')

    def getPosition(self):
        self.connection.write(b'A:\r\n')
        return self.__receivedata(False,'')

    def getPressure(self):
        self.connection.write(b'R5\r')
        ret = self.__receivedata(False,'')
        ret = ret[1:]
        return float(ret)/100

    def Open(self):
        '''This function sets the valve to it's fully open position'''
        self.connection.write(b'O\r')
        self.__receivedata(False,"F")

    def Close(self):
        '''This function closes the valve'''
        self.connection.write(b'C\r') #\r\n?
        #self.__receivedata(True,'C')

    def softOpen(self):
        '''This function slowly opens the gate valve as to not cause
        any damage to critical parts of of the system'''
        self.connection.write(b'O\r')
        '''x = -400
        step = 425 #Valve step size
        self.connection.write(b'R:000050\r\n') #setting the initial position
        time.sleep(5)
        self.interrupt = False #in case it was previously interrupted.
        while x <= 12000 and not self.interrupt:
            if self.interrupt:
                print("interuppted")
                return 0
            else: #If a command with higher priority is entered, this loop quits
                y = '0'
                x +=int(step)
                command = str.encode('R:'+ (6 - len(str(x)))*y + str(x) +'\r\n')
                self.connection.write(command) #Stepping the valve open
                time.sleep(0.4) #break between command sets

        if self.interrupt:
            pass
        else:
            self.Open()#once the valve has been opened to position 12000, the valve fully opens'''

    def Learn(self):
        self.connection.write(b'L: 00030000\r\n')
        return self.__receivedata(False,'')

'''def ROR(X,startPressure):
    pNow = X.getPressure()
    print("Pressure: " + pNow)

    timeNow = time.time()
    timeEllapsed = (timeNow - start)/60
    ROR = (int(pNow) - startPressure)/timeEllapsed

    print("ROR: " + str(ROR) + " Time: " + str(timeEllapsed))
    time.sleep(0.25)'''

if __name__ == '__main__':
    X = Valve(26)
    #time.sleep(2)
    #X.Close()
    #time.sleep(5)
    #X.Close()
    print(X.getPressure())
    #time.sleep(5)
    #X.Close()
