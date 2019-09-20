from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.switch import Switch
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
from inputButton import inputButton
from SettingsField import SettingsField

class SettingsScreen(Screen):
    def __init__(self,screenname,parameterDictionary):
        super(SettingsScreen,self).__init__(name = screenname)
        self.screenname = screenname
        self.parameterDictionary = parameterDictionary
        self.screenButton = Button(text = 'switch screens')
        self.screenButton.bind(on_press = partial(self.changeScreen))

        self.G = GridLayout(rows = 10, cols = 1)

        self.titleGrid = GridLayout(rows = 1, cols = 4)
        self.titleGrid.add_widget(Label(text = 'Field Name'))
        self.titleGrid.add_widget(Label(text = 'Pneumatic on/off'))
        self.titleGrid.add_widget(Label(text = 'Low Value'))
        self.titleGrid.add_widget(Label(text = 'High Value'))
        self.G.add_widget(self.titleGrid)

        self.settingsFieldList = []
        for i in range(8):
            a = SettingsField()
            self.settingsFieldList.append(a)
            self.G.add_widget(a)

        self.G.add_widget(self.screenButton)
        self.add_widget(self.G)

    def on_pre_leave(self, *args):
        pass
        #self.parameterDictionary['title list'] = [i.titleInput.text for i in self.settingsFieldList]


    def changeScreen(self,arg):
        if self.manager.current == 'settings':
            self.manager.current = 'main'
