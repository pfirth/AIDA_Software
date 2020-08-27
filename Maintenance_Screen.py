from kivy.uix.button import Button
from kivy.uix.label import Label
from inputButton import inputButton
from kivy.uix.gridlayout import GridLayout
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

#self.PLC.relayCurrent[self.ParameterDictionary['Vent Channel']] = '1'


#APLC = ArduinoMegaPLC(6)
#APLC.allOff()

class TB(ToggleButton):
    def __init__(self):
        super(TB,self).__init__()

        self.position = 0

class Maintenance_Screen(Screen):

    def __init__(self,screenname):
        super(Maintenance_Screen,self).__init__(name = screenname)
        self.APLC = ''#APLC
        rows = 13
        cols = 2
        self.positionDic = {0:'Blank',1:'RF Gen',2:'Open',3:'LL Lid',4:'Tio2 N2',5:'Tio2 He',6:'H2o vap',
                            7:'USD',8:'Dry Air',9:'Silane',10:'Sio2 Helium',11:'Man Lid - 11',12:'Main Lid - 12',13:'Wet Air',14:'Pins down',15:'pins up',16:'gate open',
                            17:'gate closed',18:'LL Lid Open',19:'ISO - 19',20:'Main Vent',21:'Main Lid Open',22:"22"}


        self.box = BoxLayout(orientation = 'vertical')

        self.main = GridLayout(rows = rows, cols = cols, size_hint = (1,0.75))

        #populating the rows with buttons to control the transistors
        for i in range((rows-2)*cols):
            B = TB()
            B.text = self.positionDic[i]
            B.position = i

            B.bind(on_press = self.cyclePneumatic)
            self.main.add_widget(B)

        self.RF1_Button = Button(text = 'RF1')
        self.RF1_Button.bind(on_press = self.updateVoltage)
        self.RF2_Button = Button(text = 'RF2')
        self.RF2_Button.bind(on_press = self.updateVoltage)

        self.RF1_Text = TextInput(text = '0')
        self.RF2_Text = TextInput()

        self.main.add_widget(self.RF1_Button)
        self.main.add_widget(self.RF1_Text)
        self.main.add_widget(self.RF2_Button)
        self.main.add_widget(self.RF2_Text)

        self.screenButton = Button(size_hint = (1,0.25), text = 'Main Screen')
        self.screenButton.bind(on_press = partial(self.changeScreen))

        self.box.add_widget(self.main)
        self.box.add_widget(self.screenButton)

        self.add_widget(self.box)

    def addPLC(self,PLC):
        self.APLC = PLC

    def changeScreen(self,arg):
        if self.manager.current == 'maintenance':
            self.manager.current = 'main'

    def cyclePneumatic(self,button):
        if button.state == 'down':
            self.APLC.relayCurrent[int(button.position)] = 1
        else:
            self.APLC.relayCurrent[int(button.position)] = 0
        self.APLC.updateRelayBank()

        print(button.position)

    def updateVoltage(self,button):
        if button.text == 'RF1':
            try:
                voltage = float(self.RF1_Text.text)
                if voltage > 5:
                    voltage = '5.0'
                print('RF1 ' + str(voltage))
                self.APLC.changeVoltage('5',voltage)
            except ValueError:
                print('not a number')

        if button.text == 'RF2':
            try:
                voltage = float(self.RF2_Text.text)
                if voltage >5:
                    voltage = '5.0'
                print('RF2 ' + str(voltage))
                self.APLC.changeVoltage('6',voltage)
            except ValueError:
                print('not a number')

if __name__ == '__main__':


    sm = ScreenManager()
    MainScreen = Maintenance_Screen('main')
    sm.add_widget(MainScreen)
    sm.current = 'main'

    class TestApp(App):
        def on_start(self):
            print("App Starting")

        def on_stop(self):
            print("App Stopping")

        def build(self):
            return sm

    TestApp().run()
