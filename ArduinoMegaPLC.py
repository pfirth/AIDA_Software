import serial
import time
from Device import SerialDevice
import pandas as pd

class ArduinoMegaPLC(SerialDevice):
    def __init__(self,comport):
        super(ArduinoMegaPLC,self).__init__()

        self.connection = serial.Serial('COM' + str(comport),115200) #create the connection
        self.connected = False
        self.handshake(self.connection)

        self.DataDic = {}

        self.relayCurrent = ['0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0',
                             '0','0','0','0','0','0']

        self.analogPercents = [0,0,0,0,0,0,0]

    #def writeCommand(self,command):
    #    self.connection.write(command)

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

    def getData(self):
        '''returns a list of the different data types in human readable form'''
        self.writeCommand(self.connection,b'<3>')

        rawData = str(self.receiveData(self.connection),"utf-8")

        dataList = rawData.split(',')

        for key in self.DataDic.keys():

            slot = self.DataDic[key]
            if int(slot['readAddress']) >-1:
                _15BitValue = float(dataList[slot['readAddress']])
                _15BitFraction = _15BitValue/(29790-29790*0.1) #just a conversion factor that makes the flows match
                humanValue = str(self.convertToHumanValue(_15BitFraction,slot['max']))
                slot['currentRead'] = humanValue

        return dataList

    def getAnalogData(self):
        self.writeCommand(self.connection,b'<3>')
        rawData = str(self.receiveData(self.connection),"utf-8")
        dataList = rawData.split(',')

        dataList = [float(_15bitValue)/(29790-29790*0.1) for _15bitValue in dataList]

        self.analogPercents = dataList

        return float(dataList[3])*30000

    def convertToHumanValue(self,fraction,max):
        return str(float("{0:.2f}".format(fraction*max)))

    def convertData(self,data):
        ADCData = data[0].split('@')[1].split(',')
        encoderPosition = data[1].split('@')[1]

        pressureValueList = []
        for ndx,value in enumerate(ADCData):
            if int(value) >0:
                pressureFraction = (float(value)/(29790-29790*0.1))
                pressureValueList.append(pressureFraction)
            else:
                pressureValueList.append('0')

        pressureValueList.append(encoderPosition)

        return pressureValueList,encoderPosition

    def updateVoltage(self,slotNumber,newVoltage):
        self.DataDic[slotNumber]['currentSet'] = str(newVoltage)
        newVoltage = 5*(int(newVoltage)/self.DataDic[slotNumber]['max'])
        command = '<1,'+str(self.DataDic[slotNumber]['writeAddress'])+','+str(newVoltage)+'>'
        command = str.encode(command)

        self.writeCommand(self.connection,command)


        if newVoltage >0:
            self.DataDic[slotNumber]['on'] = True
        else:
            self.DataDic[slotNumber]['on'] = False


        return self.connection.readline()

     #maybe delete

    def changeVoltage(self,writeChannel,newVoltage):
        command = '<1,'+str(writeChannel)+','+str(newVoltage)+'>'
        command = str.encode(command)
        self.writeCommand(self.connection,command)

    def receivedata(self,confirmcommand):
        print("updateBank")
        while True:
            if self.connection.in_waiting >0:
                rec =  self.connection.readline().strip()
                return rec

    def updateBank(self,bankarray):

        self.connection.write(str.encode(bankarray,"utf-8"))
        #self.writeCommand(self.connection,str.encode(bankarray,"utf-8"))
        #self.receivedata(b'Bank Updated')

    def updateRelayBank(self):
        a = '<2'
        for i in self.relayCurrent:
            a = a + ',' + str(i)

        a = a + '>'
        self.updateBank(a)

    def silaneOn(self):
        self.relayCurrent[7] = '0'
        self.updateRelayBank()

    def silaneOff(self):
        self.relayCurrent[7] = '1'
        self.updateRelayBank()

    def allOff(self):
        self.updateBank('<2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0>')


if __name__ == '__main__':
    A = ArduinoMegaPLC(8)

    def openGateValve():
        A.relayCurrent = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        A.updateRelayBank()
        time.sleep(3)

        A.relayCurrent = [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        A.updateRelayBank()
        time.sleep(1)

        A.relayCurrent = [1,1,1,1,1 ,1,1,1,1,1,1,1,1,1,1,1,1]
        A.updateRelayBank()

        time.sleep(1)

        A.relayCurrent = [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        A.updateRelayBank()
        time.sleep(1)

        A.relayCurrent = [1,1,1,1,1 ,1,1,1,1,1,1,1,1,1,1,1,1]
        A.updateRelayBank()


        '''A.relayCurrent = [1,1,1,1,1 ,1,1,1,1,1,1,1,1,1,1,1,1]
        A.updateRelayBank()
        A.relayCurrent = [0,1,1,1,1 ,1,1,1,1,1,1,1,1,1,1,1,1]
        A.updateRelayBank()'''

    def closeGateValve():
        A.relayCurrent = [1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1]
        A.updateRelayBank()


    closeGateValve()
    #time.sleep(3)
    #openGateValve()

    #A.relayCurrent = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    #A.updateRelayBank()

    srt = A.getAnalogData()
    Starttime = time.time()
    while True:
        current = A.getAnalogData()
        currentTime = time.time()
        RORO = (current-srt)/(((currentTime-Starttime)/1000)*60)

        print(srt,current,RORO)
        time.sleep(0.1)

    #while True:
     #   print(A.getData())
      #  time.sleep(0.1)'''





