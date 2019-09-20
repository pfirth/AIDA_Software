from kivy.uix.button import Button
from kivy.uix.label import Label
from inputButton import inputButton
from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from functools import partial
from threading import Thread
import time
from inputButton import inputButton



class InputField(GridLayout):
    def __init__(self,**kwargs):
        super(InputField,self).__init__()
        self.rows = 1
        self.cols = 3

        self.titleLabel = Label(text = 'test')
        if 'labeltext' in kwargs:
            self.titleLabel.text = kwargs['labeltext']
        else:
            self.titleLabel.text = 'Unused'

        #setting the maximum and minimum valuse that can be entered
        if 'max' in kwargs:
            self.max = kwargs['max']
        else:
            self.max = 1000000000
        if min in kwargs:
            self.min = kwargs['min']
        else:
            self.min = 0

        self.fieldButton = inputButton(min = self.min,max = self.max)
        self.readLabel = Label(text = '-',font_size = '25sp',halign = 'left')

        self.add_widget(self.titleLabel)
        self.add_widget(self.fieldButton)
        self.add_widget(self.readLabel)

    def addLabel(self):
        self.cols = 4
        self.add_widget(Label())

    def setMinMax(self,**kwargs):

        if 'max' in kwargs:
            self.max = kwargs['max']
        if 'min' in kwargs:
            self.min = kwargs['min']

        self.fieldButton.setMinMax(min = self.min,max = self.max)

    def getMax(self):
        return self.max

    def setReadLabel(self,text):
        self.readLabel.text = text

    def getReadLabel(self):
        return self.readLabel.text

    def getSetValue(self):
        return self.fieldButton.text

    def setSetValue(self,strVal):
        self.fieldButton.text = strVal

    def wasUpdated(self):
        '''main loop checks to see if the parameter was updated.'''
        return self.fieldButton.wasUpdated

    def updateAcknowledged(self):
        '''main loop will call this function once it sees an update
        has occurred and acts on it.'''
        self.fieldButton.wasUpdated = False

    def setTitle(self,tit):
        self.titleLabel.text = tit

class InputFieldVertical(GridLayout):
    def __init__(self,**kwargs):
        super(InputFieldVertical,self).__init__()
        self.rows = 2
        self.cols = 1

        self.titleLabel = Label(text = 'test')
        if 'labeltext' in kwargs:
            self.titleLabel.text = kwargs['labeltext']
        else:
            self.titleLabel.text = 'Unused'

        self.fieldButton = inputButton()

        self.add_widget(self.titleLabel)
        self.add_widget(self.fieldButton)

    def getTitle(self):
        return self.titleLabel.text

    def getSetValue(self):
        return self.fieldButton.text

    def wasUpdated(self):
        '''main loop checks to see if the parameter was updated.'''
        return self.fieldButton.wasUpdated

    def updateAcknowledged(self):
        '''main loop will call this function once it sees an update
        has occurred and acts on it.'''
        self.fieldButton.wasUpdated = False

def testFunc(**kwargs):
    if 'name' in kwargs:
        name = kwargs['name']
    else:
        name = 'Peter'
    print(name)

if __name__ == '__main__':
    pass
