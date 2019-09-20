from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.filechooser import FileChooserListView
from functools import partial
from threading import Thread
import time
import pandas as pd
from inputField import InputFieldVertical
from Motor_Control import ArduinoMotor

def Create_Thread(function, *args):
    new_thread = Thread(target = function, args = (args))
    new_thread.start()

class motorScreen(FloatLayout):

    def __init__(self):
        super(motorScreen,self).__init__()
        self.setParameterDictionary = {'motorOn':False,'motorStateChange':False,'homing':False,'homeStateChange':False}

        self.mainGrid = GridLayout(rows = 2, cols = 1)
        self.buttonGrid = GridLayout(rows = 1, cols = 5)

        self.staticFieldList = [InputFieldVertical(labeltext =['speed','swipes','start','stop'][i]) for i in range(4)]
        for field in self.staticFieldList:
            self.buttonGrid.add_widget(field)

        self.homeButton = ToggleButton(text = 'Home')
        self.buttonGrid.add_widget(self.homeButton)

        self.startButton = ToggleButton(text = 'Start')

        self.mainGrid.add_widget(self.buttonGrid)
        self.mainGrid.add_widget(self.startButton)


        self.startButton.bind(on_press = lambda x: self.parameterChange('motorOn',self.startButton.state,'motorStateChange'))
        self.homeButton.bind(on_press = lambda x: self.parameterChange('homing',self.homeButton.state,'homeStateChange'))

        self.add_widget(self.mainGrid)


    def parameterChange(self,currentKey,current,changeKey):
        if current == 'down':
            self.setParameterDictionary[currentKey] = True
        else:
            self.setParameterDictionary[currentKey] = False

        self.setParameterDictionary[changeKey] = True

MP = motorScreen()
StepperController = ArduinoMotor(9)

class GB():
    def __init__(self,mainscreen,AM):
        self.stepperMotor = AM
        self.mainscreen = mainscreen
        self.programrunning = True

        self.paramDic = self.mainscreen.setParameterDictionary

        for i in self.mainscreen.staticFieldList:
            self.stepperMotor.DataDic[i.getTitle()] = ''

        self.run()

    def run(self):
        Create_Thread(self.updating,)

    def updating(self):
        while self.programrunning:
            self.updateMotorRecipe()

            if self.paramDic['motorStateChange']:
                self.paramDic['motorStateChange'] = False
                if self.paramDic['motorOn']:
                    self.stepperMotor.move()
                else:
                    self.stepperMotor.stopMove()

            if self.paramDic['homeStateChange']:
                self.paramDic['homeStateChange'] = False
                if self.paramDic['homing']:
                    self.stepperMotor.home()
                else:
                    pass

            time.sleep(0.1)


    def updateMotorRecipe(self):
        #update the motor control recipe
        for i in self.mainscreen.staticFieldList:
            if self.stepperMotor.DataDic[i.getTitle()] != i.getSetValue():
                self.stepperMotor.DataDic[i.getTitle()] = i.getSetValue()
                self.stepperMotor.DataDic['changed'] = True
            else:
                pass

        if self.stepperMotor.DataDic['changed']:
            self.stepperMotor.updateSingleStepRecipe()


gob = GB(MP,StepperController)

if __name__ == '__main__':

    class TP(App):

        def on_stop(self):
            gob.programrunning = False

        def build(self):
            return MP

    tst = TP().run()

