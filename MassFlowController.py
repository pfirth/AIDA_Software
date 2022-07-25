import serial
from serial import SerialException
import time
import binascii
import codecs
from ArduinoMegaPLC import ArduinoMegaPLC

class MassFlowController():
    def __init__(self):
        self.port = 'str number'
        self.connection = 'Serial Object'
        self.readChannel = ''
        self.writeChannel = ''
        self.max = 'float'
        self.min = 'float'
    def turnOn(self):
        pass
    def turnOFf(self):
        pass
    def set(self):
        pass
    def read(self):
        pass


class HoribaLF_F():
    groupOn = False #global class variable to determine if any other MFCs are on.
    '''This item requires a RS-232 to 485 converter'''
    def __init__(self,pneumaticController,pneumaticAddress,connection,writeChannel,readChannel,max,min,slot,units):
        '''Initialization requires that the port number of the 4-port USB to serial
        adapter be input (A,B,C,D) to start. This will be changed to work with different
        computers'''

        #Makes sure that the program doesn't crash if the serial is not connected
        try:
            self.connection = connection
            self.connected = True
        except SerialException:
            self.connected = False


        self.pneumaticController = pneumaticController #arduino controller
        self.pneumaticAddress = pneumaticAddress
        self.writeChannel = writeChannel #4 digit string (3031)
        self.readChannel = readChannel   #will be the same as the write channel
        self.units = units
        self.max = max                   #float
        self.min = min                   #float #5% of maximum
        self.slot = slot
        #add in arduino with the relay addresses for pneumatics.

        self.DataDic = {}

        self.currentRead = '0'
        self.currentSet = '0'
        self.on = False


    def checksum(self,command):
        stringCommand = command
        sumOfBits = 0
        for i in stringCommand:
            '''converts each character in string command to hex, then that hex value into
             the an integer and sums them all together'''
            i =  ' '.join(format(ord(x), 'b') for x in i)
            i = int(i,2)
            sumOfBits+= i

        sumOfBits +=3 #adding the EXT bit
        #need to add feature to catch if CS is a special character.
        return format(sumOfBits%128, '#04x')[2:]

    def parsereturn(self,ret):
        response = ''
        catch = 0
        s = ''
        r = ''
        flag = 0

        for a in str(ret):
            s = s+a

            if flag:
                if a == '\'':
                    break
                r = r+a

            if '\\x02' in s:
                flag = 1

        return r

    def set(self,flowrate):
        '''flowrate should be in sccm and come in the form of a string, eg '20000'
        address should be sring in the form of '3031' '''

        if not self.connected:
            return '-1'

        self.currentSet = flowrate

        command = 'AFC' + str(flowrate) + ','+ self.units #command for setting the flowrate 'B' represents SCCM, a:ccm, b:g/min
        print('P:' + command)
        checkSum = self.checksum(command)
        #forming the whole command in format @ + address + STX + commad + ETC + BCC
        command =  '40' + self.writeChannel  + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum

        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        ret = self.sendCommand(command)

        return ret

    def readFullScaleFlowRate(self):

        if not self.connected:
            return '-1'

        '''RFS. Returns a string of the maximum flowrate that can be set'''
        # 52 46 53
        command = 'RFS' #RFS
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        return self.sendCommand(command)

    def reconnect(self):
        command = '15'
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum

        a = codecs.decode(str.encode(command,"utf-8"),"hex")
        ret = self.sendCommand(a)

    def reconnect2(self):
        command = '06'
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum

        a = codecs.decode(str.encode(command,"utf-8"),"hex")
        ret = self.sendCommand(a)

    def read(self):

        if not self.connected:
            return '-1'

        command = 'RFV' #RFV
        checkSum = self.checksum(command)

        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        a = codecs.decode(str.encode(command,"utf-8"),"hex")
        ret = self.sendCommand(a)
        ret = "{0:.2f}".format(float(ret))

        self.currentRead = ret
        return ret

    def sendCommand(self,command):

        if not self.connected:
            return '-1'

        ret = b''
        flag = 1
        self.connection.write(command)
        time.sleep(0.09)

        start = time.time()

        badCount = 0

        while flag:
            elapsed = time.time() - start
            if elapsed > 1.5:
                print("Digital MFCs not Responding")
                badCount +=1

                #print(ret)
                return '-1'
            #print('MFC Digital send command',command)
            #print(command)

            if self.connection.in_waiting >0:
                a = self.connection.read()

                if a == b'\x03':
                    while self.connection.in_waiting >0:
                        b = self.connection.read()

                    flag = 0

                else:
                    ret = ret+a

        ret = self.parsereturn(ret)

        return ret

    def readSetFlowRate(self):
        if not self.connected:
            return '-1'
        command = 'RFC' #RFC
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        return self.sendCommand(command)

    def turnOn(self):
        if not self.connected:
            return '-1'

        command = 'IAC' #RFC
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")
        self.connection.write(command)
        self.turnOnPneumatic()
        self.on = True
        #update the pneumatic

        return self.sendCommand(command)

    def turnOff(self):
        if not self.connected:
            return '-1'
        command = 'MVC' #RFC
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        self.turnOffPneumatic()
        self.connection.write(command)
        self.on = False
        #turn the pneumatic off

        return self.sendCommand(command)

    def readValveControlMode(self):
        if not self.connected:
            return '-1'
        command = 'RVM' #RFC
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + command.encode('hex') + '03' + checkSum
        command = command.decode('hex')
        ret = self.__Receive_Data(command)

        return self.parsereturn(ret)

    def __Receive_Data(self,command):
        '''This sends a command to the baratron and returns a value if good, or -1 if
        a time out situation'''

        while True:

            self.connection.write(command)
            time.sleep(0.1)

            out = ''
            while self.connection.inWaiting() >0:
                incoming  = self.connection.read()
                out+=incoming

            return out

    def turnOnPneumatic(self):
        if self.pneumaticAddress == -1:  # if there is no pneumatic associated with the mfc
            pass
        else:
            self.pneumaticController.relayCurrent[self.pneumaticAddress] = '1'
            self.pneumaticController.updateRelayBank()

    def turnOffPneumatic(self):

        if self.pneumaticAddress == -1:  # if there is no pneumatic associated with the mfc
            pass
        else:
            self.pneumaticController.relayCurrent[self.pneumaticAddress] = '0'
            self.pneumaticController.updateRelayBank()


class HoribaZ500():

    groupOn = False #global class variable to determine if any other MFCs are on.
    '''This item requires a RS-232 to 485 converter'''
    def __init__(self,pneumaticController,pneumaticAddress,connection,writeChannel,readChannel,max,min,slot):
        '''Initialization requires that the port number of the 4-port USB to serial
        adapter be input (A,B,C,D) to start. This will be changed to work with different
        computers'''

        #Makes sure that the program doesn't crash if the serial is not connected
        try:
            self.connection = connection
            self.connected = True
        except SerialException:
            self.connected = False


        self.pneumaticController = pneumaticController #arduino controller
        self.pneumaticAddress = pneumaticAddress
        self.writeChannel = writeChannel #4 digit string (3031)
        self.readChannel = readChannel   #will be the same as the write channel
        self.max = max                   #float
        self.min = min                   #float #5% of maximum
        self.slot = slot
        #add in arduino with the relay addresses for pneumatics.

        self.DataDic = {}

        self.currentRead = '0'
        self.currentSet = '0'
        self.on = False


    def checksum(self,command):
        stringCommand = command
        sumOfBits = 0
        for i in stringCommand:
            '''converts each character in string command to hex, then that hex value into
             the an integer and sums them all together'''
            i =  ' '.join(format(ord(x), 'b') for x in i)
            i = int(i,2)
            sumOfBits+= i

        sumOfBits +=3 #adding the EXT bit
        #need to add feature to catch if CS is a special character.
        return format(sumOfBits%128, '#04x')[2:]

    def parsereturn(self,ret):
        response = ''
        catch = 0
        s = ''
        r = ''
        flag = 0

        for a in str(ret):
            s = s+a

            if flag:
                if a == '\'':
                    break
                r = r+a

            if '\\x02' in s:
                flag = 1

        return r

    def set(self,flowrate):
        '''flowrate should be in sccm and come in the form of a string, eg '20000'
        address should be sring in the form of '3031' '''

        if not self.connected:
            return '-1'

        self.currentSet = flowrate

        command = 'AFC' + str(flowrate) + ',B' #command for setting the flowrate 'B' represents SCCM

        checkSum = self.checksum(command)
        #forming the whole command in format @ + address + STX + commad + ETC + BCC
        command =  '40' + self.writeChannel  + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum

        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        ret = self.sendCommand(command)

        return ret

    def readFullScaleFlowRate(self):

        if not self.connected:
            return '-1'

        '''RFS. Returns a string of the maximum flowrate that can be set'''
        # 52 46 53
        command = 'RFS' #RFS
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        return self.sendCommand(command)

    def reconnect(self):
        command = '15'
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum

        a = codecs.decode(str.encode(command,"utf-8"),"hex")
        ret = self.sendCommand(a)

    def reconnect2(self):
        command = '06'
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum

        a = codecs.decode(str.encode(command,"utf-8"),"hex")
        ret = self.sendCommand(a)

    def read(self):

        if not self.connected:
            return '-1'

        command = 'RFV' #RFV
        checkSum = self.checksum(command)

        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        a = codecs.decode(str.encode(command,"utf-8"),"hex")
        ret = self.sendCommand(a)
        ret = "{0:.2f}".format(float(ret))

        self.currentRead = ret
        return ret

    def sendCommand(self,command):

        if not self.connected:
            return '-1'

        ret = b''
        flag = 1
        self.connection.write(command)
        time.sleep(0.09)

        start = time.time()

        badCount = 0

        while flag:
            elapsed = time.time() - start
            if elapsed > 1.5:
                print("Z500 Digital MFCs not Responding: " + str(self.slot))
                badCount +=1

                #print(ret)
                return '-1'
            #print('MFC Digital send command',command)
            #print(command)

            if self.connection.in_waiting >0:
                a = self.connection.read()

                if a == b'\x03':
                    while self.connection.in_waiting >0:
                        b = self.connection.read()

                    flag = 0

                else:
                    ret = ret+a

        ret = self.parsereturn(ret)

        return ret

    def readSetFlowRate(self):
        if not self.connected:
            return '-1'
        command = 'RFC' #RFC
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        return self.sendCommand(command)

    def turnOn(self):
        if not self.connected:
            return '-1'

        command = 'IAC' #RFC
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")
        self.connection.write(command)
        self.turnOnPneumatic()
        self.on = True
        #update the pneumatic

        return self.sendCommand(command)

    def turnOff(self):
        if not self.connected:
            return '-1'
        command = 'MVC' #RFC
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        self.turnOffPneumatic()
        self.connection.write(command)
        self.on = False
        #turn the pneumatic off

        return self.sendCommand(command)

    def readValveControlMode(self):
        if not self.connected:
            return '-1'
        command = 'RVM' #RFC
        checkSum = self.checksum(command)
        command  = '40' + self.writeChannel + '02' + command.encode('hex') + '03' + checkSum
        command = command.decode('hex')
        ret = self.__Receive_Data(command)

        return self.parsereturn(ret)

    def __Receive_Data(self,command):
        '''This sends a command to the baratron and returns a value if good, or -1 if
        a time out situation'''

        while True:

            self.connection.write(command)
            time.sleep(0.1)

            out = ''
            while self.connection.inWaiting() >0:
                incoming  = self.connection.read()
                out+=incoming

            return out

    def turnOnPneumatic(self):
        if self.pneumaticAddress == -1: #if there is no pneumatic associated with the mfc
            pass
        else:
            self.pneumaticController.relayCurrent[self.pneumaticAddress] = '1'
            self.pneumaticController.updateRelayBank()

    def turnOffPneumatic(self):
        if self.pneumaticAddress == -1: #if there is no pneumatic associated with the mfc
            pass
        else:
            self.pneumaticController.relayCurrent[self.pneumaticAddress] = '0'
            self.pneumaticController.updateRelayBank()


class AnalogMFC():
    def __init__(self,pneumaticController,pneumaticAddress,writeChannel,readChannel,max,min,slot):
        '''Initialization requires that the port number of the 4-port USB to serial
        adapter be input (A,B,C,D) to start. This will be changed to work with different
        computers'''

        self.pneumaticController = pneumaticController  # arduino controller
        self.pneumaticAddress = pneumaticAddress
        self.writeChannel = writeChannel  #4
        self.readChannel = readChannel  # will be the same as the write channel
        self.max = max  # float
        self.min = min  # float #5% of maximum
        self.slot = slot
        # add in arduino with the relay addresses for pneumatics.

        self.DataDic = {}

        self.currentRead = '0'
        self.currentSet = '0'
        self.on = False

    def set(self,flowrate):
        '''flowrate should be in sccm and come in the form of a string, eg '20000'
        address should be sring in the form of '3031' '''

        self.currentSet = float(flowrate)

        if self.on:
            voltage = 5 * (float(self.currentSet) / self.max)
            self.pneumaticController.changeVoltage(self.writeChannel, voltage)
        else:
            pass

    def read(self):
        anr = self.pneumaticController.analogPercents
        ret_int = anr[int(self.readChannel)]*self.max
        ret = str("{0:.2f}".format(ret_int))

        self.currentRead = ret
        return ret

    def turnOn(self):
        voltage = 5 * (float(self.currentSet) / self.max)
        print(self.writeChannel,voltage)
        self.pneumaticController.changeVoltage(self.writeChannel,voltage)

        self.turnOnPneumatic()
        self.on = True

    def turnOff(self):
        voltage = 0
        self.currentSet = 0
        self.pneumaticController.changeVoltage(self.writeChannel, voltage)
        self.turnOffPneumatic()
        self.on = False

    def turnOnPneumatic(self):
        if self.pneumaticAddress == -1: #if there is no pneumatic associated with the mfc
            pass
        else:
            self.pneumaticController.relayCurrent[self.pneumaticAddress] = '1'
            self.pneumaticController.updateRelayBank()

    def turnOffPneumatic(self):
        if self.pneumaticAddress == -1: #if there is no pneumatic associated with the mfc
            pass
        else:
            self.pneumaticController.relayCurrent[self.pneumaticAddress] = '0'
            self.pneumaticController.updateRelayBank()

if __name__ == '__main__':

    #'@01\x02RFV\x03q'
    print(0x61)
    PLC = ArduinoMegaPLC(3)

    M = AnalogMFC(PLC,11, 0, 4, 5, 0, 8)
    M.set(3.3)
    M.turnOn()
    time.sleep(5)
    M.set(1.5)
    time.sleep(5)
    M.turnOff()





