from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from threading import Thread
import time
import pandas as pd
import serial
from inputButton import inputButton
from ProcessScreen import ProcessScreen
from SettingsScreen import SettingsScreen
#Equipment
from Valve import Valve,gateValveOnly,MKS153D
from ArduinoMegaPLC import ArduinoMegaPLC

from Motor_Control import ArduinoMotor
from startStopSpeedMotor import startStopArduinoMotor

from RFGenerator import RFX600
from Baratron import valveBaratron,analogBaratron
from MassFlowController import HoribaZ500,HoribaLF_F

#Config.set('graphics','fullscreen','auto')

def Create_Thread(function, *args):
    new_thread = Thread(target = function, args = (args))
    new_thread.start()

def Return_Thread(function, *args):
    new_thread = Thread(target = function, args = (args))
    return new_thread

ParameterDictionary = {'title list':['a','a','a','a','a','a','a','a'],
                       'valveOpen':False,'valveStateChange':False, 'valveBusy':False,
                       'motorOn':False,'motorStateChange':False,'loopNumber':'0','RFOn':False,'RFStateChange':False,
                       'pressureSetCurrent': '0', 'bottomChamberPressure':'0',
                       'silaneOn': False,'silaneStateChange':False,
                       'ventOn':False,'ventStateChange':False, 'lidOpen':False,'lidStateChange':False,
                       'stageHomed':False,'homeStateChange':True,
                       '1ReactorPressure':'0','ADC1read':'0','ADC2read':'0','ADC3read':'0',
                       'gasOn':False, 'gasStateChange':False,
                       '1MFCOn':False, '1MFCSetCurrent':'0', '1MFCRead':'0', '1Pneumatic':'1',
                       '2MFCOn':False, '2MFCSetCurrent':'0', '2MFCRead':'0', '2Pneumatic':'1',
                       '3MFCOn':False, '3MFCSetCurrent':'0', '3MFCRead':'0', '3Pneumatic':'1',
                       '4MFCOn':False, '4MFCSetCurrent':'0', '4MFCRead':'0', '4Pneumatic':'1',
                       '5Pneumatic':'1','6Pneumatic':'1','7Pneumatic':'1',
                       '8Pneumatic':'1','9Pneumatic':'1','10Pneumatic':'1',
                       '11Pneumatic':'1','12Pneumatic':'1','13Pneumatic':'1',
                       '14Pneumatic':'1','15Pneumatic':'1','16Pneumatic':'1',
                       'pneumaticStateChange':False, 'pneumaticSetCurret':'<2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1>',
                       'RF1On':False, 'RF1SetCurrent':'0', 'RF1StateChange':False,
                       'RF2On':False, 'RF2SetCurrent':'0', 'RF2StateChange':False,
                       'encoderPostion':'0','Vent Channel':''}




class goBetween():
    def __init__(self,processScreen, gateValve,PLC,MFCList,BaratronList,RFGeneratorList,StageController,ParameterDictionary):
        self.processScreen = processScreen
        self.inputFieldList = self.processScreen.inputFieldList

        self.gateValve = gateValve
        self.PLC = PLC
        self.MFCList = MFCList
        self.BaratronList = BaratronList
        self.RFGeneratorList = RFGeneratorList
        self.StageController = StageController
        self.ParameterDictionary = ParameterDictionary
        self.programRunning = False

        self.stateDictionary = {0:self.state0,1:self.state1,2:self.state2,3:self.state3,-1:self.stateA}
        self.currentState = 0
    def run(self):
        self.programRunning = True
        Create_Thread(self.updating)

    def updating(self):
        self.processScreen.addStateButton('home')
        self.processScreen.addStateButton('vacuum')
        self.processScreen.addStateButton('start')
        while self.programRunning:
            self.stateDictionary[self.currentState]()

    def stateA(self):
        print('state A')
        while self.programRunning and self.currentState == -1:
            self.getReadAndUpdateLabels()
            self.motorProcesses()
            self.updateGrinder()

            #stationary conditions
            if self.ParameterDictionary['lidStateChange']:
                self.ParameterDictionary['lidStateChange'] = False
                self.openCloseLid()

                '''if not self.ParameterDictionary['lidOpen']:
                    self.processScreen.addStateButton('vacuum')
                    self.currentState=0'''

            #foward moving conditions
            if self.ParameterDictionary['ventStateChange']:
                self.ParameterDictionary['ventStateChange'] = False #acknowledge the click
                self.ventStateChange()
                self.processScreen.addStateButton('vacuum')
                self.processScreen.removeStateButton('lid')
                self.currentState = 0

            #foward moving condition

    def state0(self):
        '''in this state, the vacuum valve is closed. Can move to eithe the vented state or the under
        vacuum state'''

        print('state 0')
        self.processScreen.addStateButton('vent')

        while self.programRunning and self.currentState == 0:
            self.getReadAndUpdateLabels()
            self.motorProcesses()
            self.updateGrinder()

            #reverse condition - send to lid lift IF that is a thing
            if self.ParameterDictionary['ventStateChange']:
                self.ParameterDictionary['ventStateChange'] = False #acknowledge the click
                self.ventStateChange()

                if self.ParameterDictionary['ventOn']:
                    self.processScreen.removeStateButton('vacuum')
                    self.processScreen.addStateButton('lid')
                    self.currentState = -1

            #foward moving condition
            if self.ParameterDictionary['valveStateChange']: #was the valve button clicked?
                self.ParameterDictionary['valveStateChange'] = False #acknowledge the click
                self.readyForVacuum()
                self.valveStateChange() #lauch the function associated with the click
                if self.ParameterDictionary['valveOpen']:
                    self.processScreen.removeStateButton('vent')
                    self.currentState = 1

    def state1(self):
        print("state 1")

        self.processScreen.addStateButton('gas')

        while self.programRunning and self.currentState == 1:
            self.getReadAndUpdateLabels()
            self.motorProcesses()
            self.updateGrinder()

            #reverse condition
            if self.ParameterDictionary['valveStateChange']: #was the valve button clicked?
                self.ParameterDictionary['valveStateChange'] = False #acknowledge the click
                self.valveStateChange() #lauch the function associated with the click
                if not self.ParameterDictionary['valveOpen']:
                    self.processScreen.removeStateButton('gas')
                    self.currentState = 0
            #foward condition
            if self.ParameterDictionary['gasStateChange']:
                self.ParameterDictionary['gasStateChange'] = False #acknowledge the click
                if self.ParameterDictionary['gasOn']:
                    self.updateMFCSetpoints()#update MFC values
                    self.turnOnMFCs()#turn the MFCs on
                    #head to the next state
                    self.processScreen.removeStateButton('vacuum')
                    self.currentState = 2
                    pass

    def state2(self):
        print('state 2')
        self.processScreen.addStateButton('RF')
        while self.programRunning and self.currentState == 2:
            self.getReadAndUpdateLabels()
            self.updateMFCSetpoints()
            self.motorProcesses()
            self.updateGrinder()

            #reverse condition
            if self.ParameterDictionary['gasStateChange']:
                self.ParameterDictionary['gasStateChange'] = False #acknowledge the click
                if not self.ParameterDictionary['gasOn']:
                    self.turnOffMFCs()
                    self.processScreen.addStateButton('vacuum')
                    self.processScreen.removeStateButton('RF')
                    self.currentState = 1

            #foward condition
            if self.ParameterDictionary['RFStateChange']:
                self.ParameterDictionary['RFStateChange'] = False #acknowledge the click
                if self.ParameterDictionary['RFOn']:
                    self.processScreen.removeStateButton('gas')
                    self.updateRFGenSetpoints()
                    self.turnOnRFGen()
                    self.currentState = 3

    def state3(self):
        print('state 3')

        while self.programRunning and self.currentState == 3:
            self.getReadAndUpdateLabels()
            self.updateMFCSetpoints()
            self.updateRFGenSetpoints()
            self.motorProcesses()
            self.updateGrinder()

            #reverse condition
            if self.ParameterDictionary['RFStateChange']:
                self.ParameterDictionary['RFStateChange'] = False #acknowledge the click
                if not self.ParameterDictionary['RFOn']:
                    self.processScreen.addStateButton('gas')
                    self.turnOffRFGen()
                    self.currentState = 2

    def getReadAndUpdateLabels(self):
        def MFCcurrentRead():
            for m in self.MFCList:
                m.read()
        def PLCcurrentRead():
            PLC.getAnalogData()

        def GateValveRead():
            #check to see if the valve is going through the soft pump routine.
            if self.ParameterDictionary['valveBusy']:
                pass
            else:
                for b in self.BaratronList:
                    b.read()

        t1 = Return_Thread(MFCcurrentRead)
        t2 = Return_Thread(PLCcurrentRead)
        t3 = Return_Thread(GateValveRead)

        t1.start()
        t2.start()
        t3.start()

        t1.join()
        t2.join()
        t3.join()

        for b in self.BaratronList:
            field = self.inputFieldList[b.slot]
            field.setReadLabel(b.currentRead)
        for m in self.MFCList:
            field = self.inputFieldList[m.slot]
            field.setReadLabel(m.currentRead)
        for r in self.RFGeneratorList:
            field = self.inputFieldList[r.slot]
            field.setReadLabel(r.read())

    def updateMFCSetpoints(self):
        for m in MFCList:
            #if the setpoint has changed
            currentSet = self.inputFieldList[m.slot].getSetValue()
            if float(m.currentSet) != float(currentSet):
                m.set(currentSet)

                if not m.on and float(m.currentSet)> 0:
                    m.turnOn()

                if float(m.currentSet)<= 0:
                    m.turnOff()

            #if it has not, don't do anything
            else:
                pass

    def turnOnMFCs(self):
        for m in self.MFCList:
            if float(m.currentSet) > 0:
                m.turnOn()
            else:
                m.turnOff()

    def turnOffMFCs(self):
        for m in self.MFCList:
            m.turnOff()

    def updateRFGenSetpoints(self):
        for r in self.RFGeneratorList:
            currentSet = self.inputFieldList[r.slot].getSetValue()
            if float(r.currentSet) != float(currentSet):
                r.setFowardPower(currentSet)

                if not r.on and float(r.currentSet) > 0:
                    r.turnOn()

                if float(r.currentSet) <=0:
                    r.turnOff()
            else:
                pass

    def turnOnRFGen(self):
        for R in self.RFGeneratorList:
            R.turnOn()

    def turnOffRFGen(self):
        for R in self.RFGeneratorList:
            R.turnOff()

    def readyForVacuum(self):
        #turn off the vent
        self.PLC.relayCurrent[self.ParameterDictionary['Vent Channel']] = '0'
        self.PLC.updateRelayBank()
        self.ParameterDictionary['ventOn'] = False
        self.processScreen.ventButton.b.state = 'normal'

    def valveStateChange(self):
        def softOpen():
            #this stops the computer from asking the valve for pressure readings during soft open
            self.ParameterDictionary['valveBusy'] = True
            self.gateValve.softOpen()
            self.ParameterDictionary['valveBusy'] = False

        def Open():
            #this stops the computer from asking the valve for pressure readings during soft open
            self.ParameterDictionary['valveBusy'] = True
            self.gateValve.Open()
            self.ParameterDictionary['valveBusy'] = False

        if self.ParameterDictionary['valveOpen']: #If the button press activates the valve
            #need a way of identifying which baratron to use...
            if float(self.BaratronList[0].currentRead) > float(self.BaratronList[0].max): #soft open condition
                Create_Thread(softOpen,)
                #Open() #this is a thread for certain types of gate valves
            else: #regular open condition
                #Create_Thread(Open,)
                Open() #thi


        else: #if the button click is intented to close the valve.
            self.gateValve.interrupt = True #stops the soft pump routine if it's in
            self.gateValve.Close()

    def ventStateChange(self):
        if self.ParameterDictionary['ventOn']:
            self.PLC.relayCurrent[self.ParameterDictionary['Vent Channel']] = '1'
            self.PLC.updateRelayBank()

        else:
            self.PLC.relayCurrent[self.ParameterDictionary['Vent Channel']] = '0'
            self.PLC.updateRelayBank()

    def motorProcesses(self):
        if self.ParameterDictionary['homeStateChange']:
            self.ParameterDictionary['homeStateChange'] = False
            Create_Thread(self.StageController.home,)

        if self.StageController.homed:
            self.processScreen.homeButton.b.state = 'normal'

        if self.ParameterDictionary['motorStateChange']:
            self.ParameterDictionary['motorStateChange'] = False

            if self.ParameterDictionary['motorOn']:
                self.StageController.move()
            else:
                self.StageController.stopMove()

        if self.ParameterDictionary['motorOn']:
            self.StageController.checkForData()
            self.processScreen.loopCount.text = "Loop # " + self.StageController.currentLoopCount + " of " + self.processScreen.staticFieldList[1].getSetValue()

        else:
            for i in self.processScreen.staticFieldList:
                if self.StageController.DataDic[i.getTitle()] != i.getSetValue():
                    self.StageController.DataDic[i.getTitle()] = i.getSetValue()
                    self.StageController.updateSingleStepRecipe()

        if int(self.StageController.currentLoopCount) == int(self.processScreen.staticFieldList[1].getSetValue()):
            self.ParameterDictionary['motorOn'] = False
            self.processScreen.startbutton.b.state = 'normal'
            self.StageController.currentLoopCount = '0'

    def openCloseLid(self):
        #if we are opening the lid
        if self.ParameterDictionary['lidOpen']:
            self.PLC.relayCurrent[self.ParameterDictionary['Open Channel']] = '1'
            try:
                self.PLC.relayCurrent[self.ParameterDictionary['Close Channel']] = '0'
            except KeyError: #if no close channel
                pass
            self.PLC.updateRelayBank()
        #if we are closing the lid
        else:
            self.PLC.relayCurrent[self.ParameterDictionary['Open Channel']] = '0'
            try:
                self.PLC.relayCurrent[self.ParameterDictionary['Close Channel']] = '1'
            except KeyError: #if no close channel
                pass

            self.PLC.updateRelayBank()
            #put the lid button to normal
            self.processScreen.lidLiftButton.state = 'normal'

    def updateGrinder(self):
        if self.ParameterDictionary['grindMotor']: #is there a grinder attached?
            gmObject = self.ParameterDictionary['grindMotorObject']

            if int(gmObject.currentSpeed) != int(self.processScreen.grindSpeedButton.getText()): #if the set point has changed
                newSpeed = self.processScreen.grindSpeedButton.getText()
                gmObject.currentSpeed = newSpeed
                gmObject.changeSpeed(newSpeed)

            if self.ParameterDictionary['silaneStateChange']: # if the buttonr was pressed
                self.ParameterDictionary['silaneStateChange'] = False #acknowledge the press
                if self.ParameterDictionary['silaneOn']:#if it is on, turn on the motor
                    gmObject.start()
                else: #if it is not on, turn off the motor
                    gmObject.stop()

        else: #don't do anything
            pass

sm = ScreenManager()
SettingsScreen = SettingsScreen('settings',ParameterDictionary)
MainScreen = ProcessScreen('main',ParameterDictionary)

sm.add_widget(MainScreen)
sm.add_widget(SettingsScreen)

sm.current = 'main'

#read from the CSV file
df = pd.read_csv('SettingsFile.csv')

comDic = {} #holds the comport number and the corresponding serial port object
MFCList = [] #holds the MFC objects
RFGenList = [] #holds RF generator objects
BaratronList = [] #holds baratron objects

for row in df.iterrows(): #iterate through each row of the excel file and adds in the right comonent.
    r = row[1]
    print(r['type'])

    if r['type'] == 'ArduinoPLC':
        PLC = ArduinoMegaPLC(int(r['Com']))

    if r['type'] == 'ArduinoMotor':
        StepperController = ArduinoMotor(int(r['Com']))

    if r['type'] == 'HoribaZ500':
        try: #check if the desired comport has been opened
            MFCconnection = comDic[r['Com']]
        except KeyError: #if it has not, create it and add it to the com dictionary
            MFCconnection = serial.Serial(port= 'COM'+str(r['Com']),baudrate=38400,
                                    bytesize=serial.SEVENBITS,stopbits = serial.STOPBITS_ONE,
                                    parity=serial.PARITY_ODD)
            comDic[r['Com']] = MFCconnection

        #create the MFC object
        m = HoribaZ500(PLC,r['relay address'],MFCconnection,str(r['write address']), str(['read address']),
                r['max'],r['min'],r['slot'])

        MFCList.append(m)
        MainScreen.inputFieldList[r['slot']].setTitle(r['title'])
        MainScreen.inputFieldList[r['slot']].setMinMax(min = float(r['min']),max = float(r['max']))

    if r['type'] == 'HoribaLF':
        try:
            MFCconnection = comDic[r['Com']]
        except KeyError:
            MFCconnection = serial.Serial(port= 'COM'+str(r['Com']),baudrate=38400,
                                    bytesize=serial.SEVENBITS,stopbits = serial.STOPBITS_ONE,
                                    parity=serial.PARITY_ODD)
            comDic[r['Com']] = MFCconnection
        #create the MFC object
        m = HoribaLF_F(PLC,r['relay address'],MFCconnection,str(r['write address']), str(['read address']),
                       r['max'],r['min'],r['slot'])
        MFCList.append(m)
        MainScreen.inputFieldList[r['slot']].setTitle(r['title'])
        MainScreen.inputFieldList[r['slot']].setMinMax(min = float(r['min']),max = float(r['max']))

    if r['type'] == 'RFX600':
        instrument = RFX600(PLC,r['write address'],int(r['read address'].split(',')[0]),
                            int(r['read address'].split(',')[1]),
                            r['relay address'],r['min'],r['max'],r['slot'])
        RFGenList.append(instrument)
        MainScreen.inputFieldList[r['slot']].setTitle(r['title'])
        MainScreen.inputFieldList[r['slot']].setMinMax(min = float(r['min']),max = float(r['max']))

    if r['type'] == 'Pneumatic':
        ParameterDictionary[r['title']] = int(r['relay address'])

    if r['type'] == 'GateValve':
        print(r['read address'])
        gateValve = gateValveOnly(PLC,int(r['read address'].split(',')[0]),
                            int(r['read address'].split(',')[1]))

    if r['type'] == 'ButterflyValve':

        if r['title'] == 'MKS153D':

            gateValve = MKS153D(r['Com'],r['max'])

        if r['title'] == 'whatever the VAT model numebr is':
            pass

    if r['type'] == 'AnalogBaratron':
        instrument = analogBaratron(PLC,int(r['read address']),r['min'],r['max'],r['slot'])
        BaratronList.append(instrument)
        MainScreen.inputFieldList[r['slot']].setTitle(r['title'])
        MainScreen.inputFieldList[r['slot']].setMinMax(min = float(r['min']),max = float(r['max']))

    if r['type'] == 'ValveBaratron':
        instrument = valveBaratron(gateValve,r['min'],r['max'],r['slot'])
        BaratronList.append(instrument)
        MainScreen.inputFieldList[r['slot']].setTitle(r['title'])
        MainScreen.inputFieldList[r['slot']].setMinMax(min = float(r['min']),max = float(r['max']))

    if r['type'] == 'Grinder':
        grindMotor = startStopArduinoMotor(r['Com'])
        ParameterDictionary['grindMotor'] = True
        ParameterDictionary['grindMotorObject'] = grindMotor
    else:
        ParameterDictionary['grindMotor'] = False


    if r['type'] == 'Blank':
        print(r['title'])
        MainScreen.inputFieldList[r['slot']].setTitle(r['title'])

#need a catch in case one of the pieces of equipment is missing.
GB2 = goBetween(MainScreen,gateValve,PLC,MFCList,BaratronList,RFGenList,StepperController,ParameterDictionary)


class TestApp(App):
    def on_start(self):
        print("App Starting")
        self.loadSettings()
        GB2.run()
        #Create_Thread(checkPLC,PLC,ParameterDictionary,GB)


    def on_stop(self):
        GB2.programRunning = False
        '''GB.programrunning = False
        time.sleep(0.25)
        GB.beforeExit()'''

    def build(self):
        return sm

    def loadSettings(self):
        staticList = MainScreen.staticFieldList
        for b in staticList:
            StepperController.DataDic[b.getTitle()] = b.getSetValue()





if __name__ == '__main__':
        TestApp().run()





