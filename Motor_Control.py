import serial
import time
import pandas as pd

#<1,1,1,1000,300,3,0>

class ArduinoMotor():
    def __init__(self,comport):

        self.connection = serial.Serial('COM' + str(comport),115200) #create the connection
        self.connected = False
        self.handshake(self.connection) #start the connection

        self.sendSum= 0
        self.currentRecipe = b''
        self.currentRecipeLoaded = False

        self.DataDic = {}

        self.waitingForResponse = False
        self.currentLoopCount = "0"

        self.busy = False

        self.moving = False
        self.homed = False

        self.communicationDic = {'#':self.updateLoopCount}

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

    def __receivedata(self,confirmcommand):
        while True:
            if self.connection.in_waiting >0:
                rec =  self.connection.readline().strip()
                if rec == confirmcommand:
                    break

    def checkForData(self):
        if self.connection.in_waiting >0:
            rec =  str(self.connection.readline().strip(),"utf-8")
            command = rec.split(',')
            try:
                self.communicationDic[command[0]](command[1])
            except KeyError:
                print('received a value I did not expect... Motor_Control line 63')
            return rec

    def updateLoopCount(self,count):
        self.currentLoopCount = count

    def updateSingleStepRecipe(self):
        a = '<1,2,1,'+self.DataDic['start']+',50,1,0,'
        b = '1,'+ str(int(self.DataDic['stop'])-int(self.DataDic['start']))+ ','+self.DataDic['speed']+','+ self.DataDic['swipes'] +',0>'

        #a = '<1,2,'+str(self.DataDic['start'])+',' + self.DataDic['stop'] +',' + self.DataDic['speed']+','+ self.DataDic['swipes'] +',0>'
        a = a+b
        self.DataDic['changed'] = False
        print(a)
        recipe = str.encode(a,"utf-8")
        self.uploadRecipe(recipe)

    def testRecipe(self):
        a = '<1,1,0,10000,120,1,0>'
        recipe = str.encode(a,"utf-8")
        self.uploadRecipe(recipe)

    def home(self): #need to redo this
        self.connection.write(b'<3>')
        self.__receivedata(b'Home Complete')
        self.homed = True

    def move(self):
        self.homed = False
        if self.currentRecipeLoaded:
            self.connection.write(b'<2>')
            self.moving = True
        #self.__receivedata(b'Move Complete')

    def stopMove(self):
        self.connection.write(b'<4>')

    def resetLoopCount(self):
        self.connection.write(b'<6>')

    def uploadRecipe(self,recipe):
        self.connection.write(recipe)
        t = time.time()
        checksumfromarduino = b''
        while True:
            if self.connection.in_waiting >0:
                checksumfromarduino = self.connection.readline().strip()
                try:
                    if int(checksumfromarduino) == self.sendSum:
                        break
                except ValueError:
                    break
                else:
                    break
            else:
                #print("Missed")
                time.sleep(0.2)

        self.currentRecipeLoaded = True
        print("Check: Data uploaded successfully!")

    def CreateRecipeFromFile(self,csvFileLocation):
        csvDataFrame = pd.read_csv(csvFileLocation)
        numberofrows = csvDataFrame.shape[0]

        self.sendSum = 0
        self.sendSum+=numberofrows

        recipestring = '<1,' + str(numberofrows)

        for index,row in csvDataFrame.iterrows():
            for parameter in row:
                self.sendSum+=parameter
                recipestring+=',' + str(parameter)
        recipestring+='>'
        print(recipestring)
        self.currentRecipe = bytes(recipestring,'utf-8')
        self.uploadRecipe(self.currentRecipe)

    def moveLoadLockIn(self):
        self.connection.write(b'<8>')

    def moveLoadLockOut(self):
        self.connection.write(b'<9>')

if __name__ == '__main__':
    motor = ArduinoMotor(15)
    motor.home()
    motor.uploadRecipe(b'<1,2,1,0,500,1,0,0,2400,240,4,0>')

    motor.move()
    while True:
        motor.checkForData()


    #motor.CreateRecipeFromFile('C:\\Users\peter\Swift Coat Dropbox\Engineering\Software\Deppy_Automation\Test_Recipe.csv')
    #motor.CreateRecipeFromFile('C:\\Users\peter\Swift Coat Dropbox\Engineering\Software\Deppy_Automation\Test_Recipe.csv')
    #motor.move()
    #motor.home()
    #motor.CreateRecipeFromFile('C:\\Users\peter\Swift Coat Dropbox\Engineering\Software\Deppy_Automation\Test_Recipe2.csv')
    #motor.move()
    #motor.home()
    #motor.testRecipe()
    #time.sleep(1)
    #motor.move()
    #motor.home()




