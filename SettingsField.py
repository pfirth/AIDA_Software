from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.filechooser import FileChooserListView
from functools import partial
from threading import Thread
import time
from inputButton import inputButton


class SettingsField(GridLayout):
    def __init__(self,**kwargs):
        super(SettingsField,self).__init__()
        self.cols = 4
        self.rows = 1
        self.titleInput = TextInput()
        self.pneumatic = Switch()
        self.highValue = TextInput()
        self.lowValue = TextInput()

        self.add_widget(self.titleInput)
        self.add_widget(self.pneumatic)
        self.add_widget(self.highValue)
        self.add_widget(self.lowValue)
