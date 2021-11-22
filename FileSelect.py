from kivy.uix.button import Button
from kivy.uix.label import Label
from inputButton import inputButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
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
from kivy.uix.filechooser import FileChooserListView

class FileSelectScreen(Screen):
    def __init__(self,screenname,parameterdictionary):

        super(FileSelectScreen,self).__init__(name = screenname)
        self.parameterdictionary = parameterdictionary
        self.main = BoxLayout(orientation = 'vertical')

        self.add_widget(self.main)

        self.fileselect = FileChooserListView(size_hint = (1,1))
        self.fileselect.path ='C:\\Users\\peter\\PycharmProjects\\AIDA_Software-3\\Recipes'
        self.fileselect.filters = ['*.csv']


        self.selectbutton = Button(text = 'Confirm Selection',size_hint = (1,0.5))
        self.selectbutton.bind(on_press = lambda x: self.selectfile())

        self.main.add_widget(self.fileselect)
        self.main.add_widget(self.selectbutton)

        self.selectedrecipe = ''

    def selectfile(self):
        print(self.fileselect.selection)
        try:
            self.parameterdictionary['recipe'] = self.fileselect.selection[0]
            self.parameterdictionary['new recipe'] = True
            self.selectedrecipe = self.fileselect.selection
            self.manager.current = 'main'
        except IndexError:
            self.manager.current = 'main'

    def on_pre_enter(self, *args):
        self.fileselect._update_files()


sm = ScreenManager()

PD = {}
MainScreen = FileSelectScreen('Load Recipe',PD)

sm.add_widget(MainScreen)


if __name__ == '__main__':

    class TestApp(App):
        def on_start(self):
            #self.loadSettings()
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
