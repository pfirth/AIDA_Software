from __future__ import division
import serial
import time
import binascii
import codecs


#40 30 31 02 52 46 43 03 5E --> check current flowrate

class HoribaDigitalMFC():
    '''This item requires a RS-232 to 485 converter'''
    def __init__(self,port):
        '''Initialization requires that the port number of the 4-port USB to serial
        adapter be input (A,B,C,D) to start. This will be changed to work with different
        computers'''
        self.connection = serial.Serial(port= 'COM'+str(port),baudrate=38400,
                                        bytesize=serial.SEVENBITS,stopbits = serial.STOPBITS_ONE,
                                        parity=serial.PARITY_ODD)

        self.DataDic = {}
        self.port = port
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

    def setFlowRate(self,slot,flowrate):
        '''flowrate should be in sccm and come in the form of a string, eg '20000'
        address should be sring in the form of '3031' '''
        command = 'AFC' + flowrate + ',B' #command for setting the flowrate 'B' represents SCCM

        self.DataDic[slot]['currentSet'] = flowrate

        checkSum = self.checksum(command)
        #forming the whole command in format @ + address + STX + commad + ETC + BCC
        command =  '40' + '303'+ str(self.DataDic[slot]['writeAddress'])  + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum

        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        ret = self.sendCommand(command)

        if int(flowrate) > 0:
            self.DataDic[slot]['on'] = True
        else:
            self.DataDic[slot]['on'] = False

        return ret

    def readFullScaleFlowRate(self,address):
        '''RFS. Returns a string of the maximum flowrate that can be set'''
        # 52 46 53
        command = 'RFS' #RFS
        checkSum = self.checksum(command)
        command  = '40' + address + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        return self.sendCommand(command)

    def readDetectedFlowrate2(self,address):

        command = 'RFV' #RFV
        checkSum = self.checksum(command)
        command  = '40' + address + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        #print(command)
        a = codecs.decode(str.encode(command,"utf-8"),"hex")
        ret = self.sendCommand(a)

        for key in self.DataDic.keys():
            dic = self.DataDic[key]
            if dic['readAddress'] == 2:
                try:
                    dic['currentRead'] = "{0:.2f}".format(float(ret))
                except ValueError:
                    pass
        return ret

    def readDetectedFlowrate(self,address):
        command = 'RFV' #RFV
        checkSum = self.checksum(command)

        command  = '40' + '303'+ address+ '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        a = codecs.decode(str.encode(command,"utf-8"),"hex")
        ret = self.sendCommand(a)

        for key in self.DataDic.keys():
            dic = self.DataDic[key]
            if dic['readAddress'] == int(address):
                try:
                    dic['currentRead'] = "{0:.2f}".format(float(ret))
                except ValueError:
                    pass
        return ret

    def readDetectedFlowtateAll(self):
        for key in self.DataDic.keys():
            self.readDetectedFlowrate(str(self.DataDic[key]['readAddress']))

    def sendCommand(self,command):
        ret = b''
        flag = 1
        self.connection.write(command)
        time.sleep(0.07)

        start = time.time()

        badCount = 0

        while flag:
            elapsed = time.time() - start
            if elapsed > 1.5:
                print("Digital MFCs not Responding")
                badCount +=1

                if badCount >3:
                    self.connection.close()
                    self.connection = serial.Serial(port= 'COM'+str(self.port),baudrate=38400,
                                    bytesize=serial.SEVENBITS,stopbits = serial.STOPBITS_ONE,
                                    parity=serial.PARITY_ODD)

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

    def readSetFlowRate2(self,address):
        '''returns a string with the set flowrate in sccm'''

        command = 'RFC' #RFC
        checkSum = self.checksum(command)
        command  = '40' + address + '02' + command.encode('hex') + '03' + checkSum
        command = command.decode('hex')
        ret = self.__Receive_Data(command)

        return self.parsereturn(ret)

    def readSetFlowRate(self,slot):

        if self.DataDic[slot]['writeAddress']<0:
            print('NA')
            return "N/a"
        command = 'RFC' #RFC
        checkSum = self.checksum(command)
        command  = '40' + '303'+ str(self.DataDic[slot]['writeAddress']) + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")

        return self.sendCommand(command)

    def initiateAutomaticControl(self,slot):

        command = 'IAC' #RFC
        checkSum = self.checksum(command)
        command  = '40' + '303'+ str(self.DataDic[slot]['writeAddress']) + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")
        self.connection.write(command)

        if int(self.DataDic[slot]['currentSet']) >0:
            self.DataDic[slot]['on'] = True
        else:
            self.DataDic[slot]['on'] = False

        return self.sendCommand(command)

    def readValveControlMode(self,address):

        command = 'RVM' #RFC
        checkSum = self.checksum(command)
        command  = '40' + address + '02' + command.encode('hex') + '03' + checkSum
        command = command.decode('hex')
        ret = self.__Receive_Data(command)

        return self.parsereturn(ret)

    def forceValveClosed(self,slot):

        command = 'MVC' #RFC
        checkSum = self.checksum(command)
        command  = '40' + '303'+ str(self.DataDic[slot]['writeAddress']) + '02' + str(binascii.hexlify(str.encode(command,"utf-8")),"utf-8") + '03' + checkSum
        command = codecs.decode(str.encode(command,"utf-8"),"hex")
        self.connection.write(command)

        self.DataDic[slot]['on'] = False

        return self.sendCommand(command)

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





if __name__ == '__main__':
    t = time.time()
    DeppyNozzle = HoribaDigitalMFC(16)
    #print(DeppyNozzle.readFullScaleFlowRate('3032'))
    #print(DeppyNozzle.readDetectedFlowrate2('3032'))
    #time.sleep(1)
    while 1:
        print(DeppyNozzle.readDetectedFlowrate2('3031'))
        print(DeppyNozzle.readDetectedFlowrate2('3032'))
        print(DeppyNozzle.readDetectedFlowrate2('3033'))

    #    time.sleep(0.1)
    #DeppyNozzle.Home()
