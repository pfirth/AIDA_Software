from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from Viewer_Pop_up import Viewer
from functools import partial

class inputButton(Button):
    '''This Button class just sets the background to the desired images'''
    def __init__(self,**kwargs):
        super(inputButton,self).__init__()

        if 'max' in kwargs:
            self.max = kwargs['max']
        else:
            self.max = 1000000000
        if min in kwargs:
            self.min = kwargs['min']
        else:
            self.min = 0

        self.text = '0'
        self.popUpGrid = GridLayout(cols = 0, rows = 2)
        self.popUpTextInput = TextInput(font_size = 35,multiline=False)
        self.popUpButton = Button(text = 'Press to Confirm')
        self.popUpGrid.add_widget(self.popUpTextInput)
        self.popUpGrid.add_widget(self.popUpButton)


        self.popupField = Popup(title='Test popup',
        content=self.popUpGrid,size_hint=(None, None), size=(400, 200),
                                auto_dismiss = False)

        self.popupField.bind(on_open = self.focusText)
        self.popupField.bind(on_dismiss = self.changeText)
        self.popUpButton.bind(on_press = self.popupField.dismiss)

        self.bind(on_press = partial(self.openPopup))

        self.wasUpdated = False

    def getText(self):
        return self.text

    def focusText(self,arg):
        self.popUpTextInput.focus = True

    def openPopup(self,arg):
        self.popUpTextInput.text = self.text
        self.popupField.open()

    def getMax(self):
        return self.max

    def setMinMax(self,**kwargs):

        if 'max' in kwargs:
            self.max = kwargs['max']
        if 'min' in kwargs:
            self.min = kwargs['min']

    def changeText(self,arg):

        #sets a flag so that the main loop can see something was changed and it needs to act
        self.wasUpdated = True

        #make sure that the user is inputting a number
        try:
            a = float(self.popUpTextInput.text)
            if a > self.max:
                self.text = str(self.max)
            elif a < self.min:
                self.text = '0'
            else:
                self.text = self.popUpTextInput.text

        except ValueError:
            self.wasUpdated = False
            pass



