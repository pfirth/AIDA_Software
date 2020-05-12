from kivy.uix.button import Button
from kivy.uix.label import Label
from inputButton import inputButton
from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from functools import partial
from threading import Thread
import time
from inputButton import inputButton
from kivy.uix.togglebutton import ToggleButton
from inputField import InputField,InputFieldVertical
from inputButton import inputButton
from SettingsScreen import SettingsScreen
import pandas as pd
from swappableToggle import swapToggle

class controllerSensor():
    def __init__(self,slot, type, address, title, min, max):

        self.slot = slot
        self.type = type
        self.address = address
        self.title = title
        self.min = min
        self.max = max

class ProcessScreen(Screen):

    def __init__(self,sceenname,parameterDictionary):

        super(ProcessScreen,self).__init__(name = sceenname)
        self.setParameterDictionary = parameterDictionary

        self.main = GridLayout(rows = 3)

        self.topgrid = GridLayout(cols = 3, size_hint_y = 0.25)
        self.staticparametergrid = GridLayout(cols = 4,rows = 1)

        #Static parameter Grid

        self.staticFieldList = [InputFieldVertical(labeltext =['speed','swipes','start','stop'][i]) for i in range(4)]
        for field in self.staticFieldList:
            self.staticparametergrid.add_widget(field)

        self.topgrid.add_widget(self.staticparametergrid)
        #self.topgrid.add_widget(FileChooserListView())

        self.screenButton = Button(text = 'switch screens')
        self.screenButton.bind(on_press = partial(self.changeScreen))


        self.loopCount = Label(text = "0",font_size = 25)
        self.topgrid.add_widget(self.loopCount)

        self.centergrid = GridLayout(size_hint_y = 1,rows = 1,cols = 3)

        self.mfcgridrows = 15
        self.mfcgrid = GridLayout(rows = self.mfcgridrows, cols = 1)

        #Set and read Labels
        self.titleGrid = GridLayout(rows = 1, cols = 3)
        self.titleGrid.add_widget(Label()) #space holder
        self.titleGrid.add_widget(Label(text = 'Set'))
        self.titleGrid.add_widget(Label(text = 'Read'))
        self.mfcgrid.add_widget(self.titleGrid)

        #####################################################
        #####################################################
        #####################################################
        self.inputFieldList = [InputField() for i in range(self.mfcgridrows-1)]

        for field in self.inputFieldList:
            self.mfcgrid.add_widget(field)
        #####################################################
        #####################################################
        #####################################################


        #####################################################
        #############Transfer Menu###########################
        #####################################################
        self.transferGrid = GridLayout(cols = 1, rows = 3)
        self.homeButton = swapToggle('Home Stage')
        self.ventButton = swapToggle('Vent Chamber')
        self.lidLiftButton = swapToggle('Open/Close Lid')

        self.ventButton.b.bind(on_press = lambda x: self.parameterChange('ventOn',self.ventButton.b.state,'ventStateChange'))
        self.lidLiftButton.b.bind(on_press = lambda x: self.parameterChange('lidOpen',self.lidLiftButton.b.state,'lidStateChange'))
        self.homeButton.b.bind(on_press = lambda x: self.parameterChange('stageHomed',self.lidLiftButton.b.state,'homeStateChange'))

        self.transferGrid.add_widget(self.homeButton)
        self.transferGrid.add_widget(self.ventButton)
        self.transferGrid.add_widget(self.lidLiftButton)


        #adding larger widgets
        self.centergrid.add_widget(self.mfcgrid)
        #self.centergrid.add_widget(Button(size_hint_x = 2/3))

        self.grindGrid = GridLayout(rows = 2, cols = 1)

        self.loadSampleButton = Button(text = 'Load Sample')

        self.grindSpeedButton = Button(text = 'Another Screen')
        self.grindSpeedButton.bind(on_press = partial(self.changeScreen))

        self.grindGrid.add_widget(self.loadSampleButton)
        self.grindGrid.add_widget(self.grindSpeedButton)

        self.centergrid.add_widget(self.grindGrid)

        self.centergrid.add_widget(self.transferGrid)


        self.bottomgrid = GridLayout(cols = 5,size_hint_y = 0.25)

        self.vacuumbutton = swapToggle('Vacuum')
        self.isobutton = swapToggle('PressureISO')
        self.gasbutton = swapToggle('Gas')
        self.RFbutton = swapToggle('RF')
        self.startbutton = swapToggle('Start')

        self.testFunc = partial(self.parameterChange)

        self.vacuumbutton.b.bind(on_press = lambda x: self.parameterChange('valveOpen',self.vacuumbutton.b.state,'valveStateChange'))
        self.isobutton.b.bind(on_press = lambda x: self.parameterChange('isoOpen',self.isobutton.b.state,'isoStateChange'))
        self.gasbutton.b.bind(on_press = lambda x: self.parameterChange('gasOn',self.gasbutton.b.state,'gasStateChange'))
        self.startbutton.b.bind(on_press = lambda x: self.parameterChange('motorOn',self.startbutton.b.state,'motorStateChange'))
        self.RFbutton.b.bind(on_press = lambda x: self.parameterChange('RFOn',self.RFbutton.b.state,'RFStateChange'))

        self.stateButtonDictionary = {'vacuum':self.vacuumbutton,'gas':self.gasbutton,'start':self.startbutton,
                                      'RF':self.RFbutton,'vent':self.ventButton, 'lid':self.lidLiftButton,'home':self.homeButton,
                                      'pressureISO':self.isobutton}
        self.stateFloats = []

        self.bottomgrid.add_widget(self.vacuumbutton)
        self.bottomgrid.add_widget(self.isobutton)
        self.bottomgrid.add_widget(self.gasbutton)
        self.bottomgrid.add_widget(self.RFbutton)
        self.bottomgrid.add_widget(self.startbutton)

        self.main.add_widget(self.topgrid)
        self.main.add_widget(self.centergrid)
        self.main.add_widget(self.bottomgrid)

        self.add_widget(self.main)

    def addStateButton(self,k):
        self.stateButtonDictionary[k].add()

    def removeStateButton(self,k):
        self.stateButtonDictionary[k].remove()

    def parameterChange(self,currentKey,current,changeKey):
        if current == 'down':
            self.setParameterDictionary[currentKey] = True
        else:
            self.setParameterDictionary[currentKey] = False

        self.setParameterDictionary[changeKey] = True

    def changeScreen(self,arg):
        if self.manager.current == 'main':
            self.manager.current = 'maintenance'

    def on_enter(self, *args):
        print('entering main screen')
        #for num,field in enumerate(self.inputFieldList):
        #    field.setTitle(self.setParameterDictionary['title list'][num])

        #set high and low values

    def on_leave(self):
        print('leaving main screen')

ParameteDictionary = {'title list':[],
                      'min list':[],
                      'max list':[]}

sm = ScreenManager()
SettingsScreen = SettingsScreen('settings',ParameteDictionary)
MainScreen = ProcessScreen('main',ParameteDictionary)

sm.add_widget(MainScreen)
sm.add_widget(SettingsScreen)

sm.current = 'main'

if __name__ == '__main__':

    paramDic = {}
    BB = ProcessScreen('start',paramDic)

    class TestApp(App):
        def on_start(self):
            self.loadSettings()
            print("App Starting")

        def on_stop(self):
            print("App Stopping")

        def build(self):
            return sm

        def loadSettings(self):
            df = pd.read_csv('C:\\Users\peter\Swift Coat Dropbox\Engineering\Software\Interface Work File\Settings.csv')
            df.set_index('slot', inplace=True)

            for i in range(df.shape[0]): #iterate through the number of rows
                print(df.shape[0])
                MainScreen.inputFieldList[i].setTitle(df['title'][i])
                MainScreen.inputFieldList[i].setMinMax(min = df['min'][i],max = df['max'][i])




    TestApp().run()
