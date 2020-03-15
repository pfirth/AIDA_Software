from kivy.uix.button import Button
from kivy.uix.label import Label
from inputButton import inputButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
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
from kivy.uix.textinput import TextInput
from ArduinoMegaPLC import ArduinoMegaPLC
from Motor_Control import ArduinoMotor
import pandas as pd

class LoadSamplePopUpInterface(Screen):

    def __init__(self,**kwargs):
        super(LoadSamplePopUpInterface, self).__init__(name = 'Load')
        #self.title = 'Load Sample Menu'

        #creating the content of the popup
        self.base = BoxLayout(orientation = 'vertical')

        ##############Functional Buttons#######################
        self.buttonGrid = GridLayout(rows = 2, cols = 3, size_hint = (1,0.8))

        #load lock buttons
        self.loadLockVentButton = ToggleButton(text = 'Load Lock Vent')
        self.loadLockVacuumButton = ToggleButton(text = 'Load Lock Vacuum')
        self.loadLockLidButton = ToggleButton(text = 'Lift/Close Load Lock')

        #main chamber buttons
        self.mainChamberVacuumButton = ToggleButton(text = 'Main Chamber Vacuum')
        self.mainChamberVentButton = ToggleButton(text = 'Main Chamber Vent')

        #Load Sample Button
        self.loadSampleButton = ToggleButton(text = 'Load Sample')

        self.buttonGrid.add_widget(self.loadLockVacuumButton)
        self.buttonGrid.add_widget(self.loadLockVentButton)
        self.buttonGrid.add_widget(self.loadLockLidButton)

        self.buttonGrid.add_widget(self.mainChamberVacuumButton)
        self.buttonGrid.add_widget(self.mainChamberVentButton)
        self.buttonGrid.add_widget(self.loadSampleButton)

        #exit button
        self.exitButton = Button(text = 'Exit', size_hint = (1,0.2))

        #adding the main components
        self.base.add_widget(self.buttonGrid)
        self.base.add_widget(self.exitButton)

        self.add_widget(self.base)


class LoadSamplePopUpLogic(LoadSamplePopUpInterface):
    def __init__(self,parameterDictionary,PLC,motor,**kwargs):
        super(LoadSamplePopUpLogic,self).__init__(**kwargs)
        self.ParameterDictionary = parameterDictionary
        self.PLC = PLC
        self.motor = motor
        print(self.ParameterDictionary)

        #adding functionality to the buttons
        self.exitButton.bind(on_press = lambda  x: self.changeScreen())
        self.loadLockLidButton.bind(on_press = self.loadLockLid)
        self.loadLockVentButton.bind(on_press = self.loadLockVent)
        self.loadLockVacuumButton.bind(on_press = self.loadLockVacuum)

        self.mainChamberVentButton.bind(on_press = self.mainChamberVent)

        self.loadSampleButton.bind(on_press = self.loadSample)

    def loadLockLid(self,button):
        if button.state == 'down':
            self.PLC.relayCurrent[self.ParameterDictionary['LL Lid']] = '1'
        else:
            self.PLC.relayCurrent[self.ParameterDictionary['LL Lid']] = '0'
        self.PLC.updateRelayBank()

    def loadLockVent(self,button):
        if button.state == 'down':
            self.PLC.relayCurrent[self.ParameterDictionary['LL Vent']] = '1'
        else:
            self.PLC.relayCurrent[self.ParameterDictionary['LL Vent']] = '0'
        self.PLC.updateRelayBank()

    def loadLockVacuum(self,button):
        if button.state == 'down':
            self.PLC.relayCurrent[self.ParameterDictionary['Lock Vac Open']] = '1'
        else:
            self.PLC.relayCurrent[self.ParameterDictionary['Lock Vac Open']] = '0'
        self.PLC.updateRelayBank()

    def mainChamberVent(self,button):
        if button.state == 'down':
            self.PLC.relayCurrent[self.ParameterDictionary['Vent Channel']] = '1'
        else:
            self.PLC.relayCurrent[self.ParameterDictionary['Vent Channel']] = '0'
        self.PLC.updateRelayBank()

    def loadSample(self,button):
        #load procedure
        if button.state == 'down':
            self.motor.home()
            self.__openGate()
            self.__lowerPins()
            time.sleep(2)
            self.motor.moveLoadLockIn()
            time.sleep(13)
            self.__raisePins()
            time.sleep(3)
            self.motor.moveLoadLockOut()
            time.sleep(13)
            self.__lowerPins()
            self.__closeGate()

        #unload procedure
        else:
            self.motor.home()
            self.__openGate()
            self.__raisePins()
            time.sleep(2)
            self.motor.moveLoadLockIn()
            time.sleep(13)
            self.__lowerPins()
            time.sleep(3)
            self.motor.moveLoadLockOut()
            time.sleep(13)
            self.__closeGate()

    def changeScreen(self):
        self.manager.current = 'main'

    def __openGate(self):
        self.PLC.relayCurrent[self.ParameterDictionary['Gate Close']] = '1'
        self.PLC.relayCurrent[self.ParameterDictionary['Gate Open']] = '0'
        self.PLC.updateRelayBank()
        time.sleep(2.5)

        self.PLC.relayCurrent[self.ParameterDictionary['Gate Open']] = '1'
        self.PLC.updateRelayBank()
        time.sleep(0.1)

        self.PLC.relayCurrent[self.ParameterDictionary['Gate Close']] = '0'
        self.PLC.updateRelayBank()

    def __closeGate(self):
        self.PLC.relayCurrent[self.ParameterDictionary['Gate Close']] = '1'
        self.PLC.relayCurrent[self.ParameterDictionary['Gate Open']] = '0'
        self.PLC.updateRelayBank()

    def __lowerPins(self):
        self.PLC.relayCurrent[self.ParameterDictionary['Pins Down']] = '1'
        self.PLC.relayCurrent[self.ParameterDictionary['Pins Up']] = '0'
        self.PLC.updateRelayBank()

    def __raisePins(self):
        self.PLC.relayCurrent[self.ParameterDictionary['Pins Down']] = '0'
        self.PLC.relayCurrent[self.ParameterDictionary['Pins Up']] = '1'
        self.PLC.updateRelayBank()

class MS(Screen):
    def __init__(self,**kwargs):
        super(MS,self).__init__(name = 'main',**kwargs)

        self.main = FloatLayout()
        self.B = Button(text = 'Press Here')
        self.B.bind(on_press = lambda  x: self.changeScreens())
        self.main.add_widget(self.B)

        self.add_widget(self.main)



    def changeScreens(self):
        self.manager.current = 'Load'

if __name__ == '__main__':

    parameterDictionary = {}
    df = pd.read_csv('SettingsFile.csv')
    for row in df.iterrows():
        r = row[1]
        if r['type'] == 'ArduinoPLC':
            PLC = ArduinoMegaPLC(int(r['Com']))
        if r['type'] == 'ArduinoMotor':
            ArduinoMotor = ArduinoMotor(int(r['Com']))
        if r['type'] == 'Pneumatic':
            parameterDictionary[r['title']] = int(r['relay address'])

    sm = ScreenManager()
    MS = MS()
    LSI = LoadSamplePopUpLogic(parameterDictionary,PLC,ArduinoMotor)

    sm.add_widget(MS)
    sm.add_widget(LSI)

    sm.current = 'main'




    class TestApp(App):
        def on_start(self):
            print("App Starting")

        def on_stop(self):
            print("App Stopping")

        def build(self):
            return sm

    TestApp().run()
