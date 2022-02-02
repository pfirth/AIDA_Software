from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from Viewer_Pop_up import Viewer
from functools import partial
import datetime

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

        if 'label' in kwargs:
            self.field_label = kwargs['label']
        else:
            self.field_label = ''

        self.text = '0'
        self.popUpBoxLayout = BoxLayout(orientation = 'vertical')

        self.popUpGrid = GridLayout(cols = 0, rows = 2)

        self.popUpTextBox = BoxLayout(size_hint = (1,0.2))
        self.popUpTextInput = TextInput(font_size = 35,multiline=False)
        self.popUpTextBox.add_widget(self.popUpTextInput)

        self.popUpButtonBox = BoxLayout(size_hint = (1,0.6))
        self.popUpConfirmBox = BoxLayout(size_hint = (1,0.2))

        #Number Grid
        self.numberGrid = GridLayout(rows = 4, cols = 3)
        for i in [1,2,3,4,5,6,7,8,9]:
            numberButton = Button(text = str(i))
            numberButton.bind(on_press = self.updateText)
            self.numberGrid.add_widget(numberButton)

        self.clear_button = Button(text ='Clear')
        self.clear_button.bind(on_press = self.updateText)
        self.numberGrid.add_widget(self.clear_button)

        #adding in 0 to the bottom row
        numberButton = Button(text = '0')
        numberButton.bind(on_press = self.updateText)
        self.numberGrid.add_widget(numberButton)

        #adding in the decimal Character
        self.decimalButton = Button(text ='.')
        self.decimalButton.bind(on_press = self.updateText)
        self.numberGrid.add_widget(self.decimalButton)

        #Adding the confirm button
        self.popUpButton = Button(text = 'Confirm')
        self.popUpConfirmBox.add_widget(self.popUpButton)


        self.popUpButtonBox.add_widget(self.numberGrid)

        #self.popUpGrid.add_widget(self.popUpTextInput)
        #self.popUpGrid.add_widget(self.popUpButton)

        self.popUpBoxLayout.add_widget(self.popUpTextBox)
        self.popUpBoxLayout.add_widget(self.popUpButtonBox)
        self.popUpBoxLayout.add_widget(self.popUpConfirmBox)


        self.popupField = Popup(title=self.field_label,
        content=self.popUpBoxLayout,size_hint=(None, None), size=(400, 600),
                                auto_dismiss = False)

        self.popupField.bind(on_open = self.focusText)
        self.popupField.bind(on_dismiss = self.changeText)
        self.popUpButton.bind(on_press = self.popupField.dismiss)

        self.bind(on_press = partial(self.openPopup))

        self.wasUpdated = False
        self.popUpOpened = False


    def updateText(self,button):
        if button.text == 'Clear':
            self.popUpTextInput.text = ''
        else:
            self.popUpTextInput.text = self.popUpTextInput.text + button.text


    def getText(self):
        return self.text

    def focusText(self,arg):
        self.popUpTextInput.focus = True

    def openPopup(self,arg):
        self.popUpTextInput.text = self.text
        self.popUpOpened = True
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

class TextInputButton(Button):
    '''This Button class just sets the background to the desired images'''

    def __init__(self, **kwargs):
        super(TextInputButton, self).__init__()

        if 'max' in kwargs:
            self.max = kwargs['max']
        else:
            self.max = 1000000000
        if min in kwargs:
            self.min = kwargs['min']
        else:
            self.min = 0

        if 'popup_label' in kwargs:
            self.popup_label = kwargs['popup_label']
        else:
            self.popup_label = ''

        if 'button_label' in kwargs:
            self.button_label = kwargs['button_label']
        else:
            self.button_label = ''

        if 'sampleID' in kwargs:
            D = str(datetime.datetime.now())
            D = D.split(' ')[0]
            Y, M, D = D.split('-')
            ID = 'PF' + Y[2:] + M + D + '-'
            self.sampleIDText = ID
        else:
            self.popUpTextInput = TextInput(font_size=35, multiline=False)
            self.sampleIDText = ''

        self.text = self.button_label
        self.popUpBoxLayout = BoxLayout(orientation='vertical')

        self.popUpGrid = GridLayout(cols=0, rows=2)

        self.popUpTextBox = BoxLayout(size_hint=(1, 0.05))
        self.popUpTextInput = TextInput(font_size=35, multiline=False)
        self.popUpTextBox.add_widget(self.popUpTextInput)

        self.popUpButtonBox = BoxLayout(size_hint=(1, 0.6))
        self.popUpConfirmBox = BoxLayout(size_hint=(1, 0.2))


        self.clear_button = Button(text='Clear', background_color = (1,0,0,1))
        self.clear_button.bind(on_press=self.updateText)
        self.popUpConfirmBox.add_widget(self.clear_button)

        # Adding the confirm button
        self.popUpButton = Button(text='Confirm', background_color = (0,1,0,1))
        self.popUpConfirmBox.add_widget(self.popUpButton)

        self.popUpBoxLayout.add_widget(self.popUpTextBox)
        #self.popUpBoxLayout.add_widget(self.popUpButtonBox)
        self.popUpBoxLayout.add_widget(self.popUpConfirmBox)

        self.popupField = Popup(title=self.popup_label,
                                content=self.popUpBoxLayout, size_hint=(None, None), size=(400, 300),
                                auto_dismiss=False)

        self.popupField.bind(on_open=self.focusText)
        self.popupField.bind(on_dismiss=self.changeText)
        self.popUpButton.bind(on_press=self.popupField.dismiss)

        self.bind(on_press=partial(self.openPopup))

        self.wasUpdated = False
        self.popUpOpened = False

    def updateText(self, button):
        if button.text == 'Clear':
            self.popUpTextInput.text = ''
        else:
            self.popUpTextInput.text = self.popUpTextInput.text + button.text

    def getText(self):
        return self.text

    def focusText(self, arg):
        self.popUpTextInput.focus = True

    def openPopup(self, arg):
        self.popUpTextInput.text = self.sampleIDText
        self.popUpOpened = True
        self.popupField.open()

    def getMax(self):
        return self.max

    def setMinMax(self, **kwargs):

        if 'max' in kwargs:
            self.max = kwargs['max']
        if 'min' in kwargs:
            self.min = kwargs['min']

    def changeText(self, arg):
        print('text changed')
        # sets a flag so that the main loop can see something was changed and it needs to act
        self.wasUpdated = True

        self.text = self.button_label + '\n' + self.popUpTextInput.text


