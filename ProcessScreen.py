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
from inputButton import inputButton,TextInputButton
from SettingsScreen import SettingsScreen
import pandas as pd
from swappableToggle import swapToggle
from kivy.core.window import Window
from Maintenance_Screen import Maintenance_Screen
from FileSelect import FileSelectScreen
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import csv

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


        Window.bind(on_key_down=self._on_keyboard_down)


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

        self.mfcgridrows = 17
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

        self.grindGrid = GridLayout(rows = 5, cols = 1)

        self.loadSampleButton = Button(text = 'Select Recipe')
        self.saveRecipeButton = TextInputButton(popup_label='Recipe Filename', button_label='Save Recipe:')
        self.sampleIDButton = TextInputButton(popup_label='Sample ID', button_label='Sample ID:',sampleID = True)
        self.uploadParametersButton = Button(text='Save to Sheets')

        self.grindSpeedButton = Button(text = 'Maintenance Menu')
        #self.grindSpeedButton.bind(on_press = partial(self.changeScreen))


        self.grindGrid.add_widget(self.loadSampleButton)
        self.grindGrid.add_widget(self.saveRecipeButton)
        self.grindGrid.add_widget(self.sampleIDButton)
        self.grindGrid.add_widget(self.uploadParametersButton)
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

        #screen button binding
        self.grindSpeedButton.bind(on_press=lambda x: self.changeScreen('maintenance'))
        self.loadSampleButton.bind(on_press=lambda x: self.changeScreen('file selection'))
        self.uploadParametersButton.bind(on_press = lambda  x: self.updateSheet())
        #self.self.uploadParametersButton.bind(on_press=lambda x: self.updateSheet())

        #self.processScreen.loadSampleButton.bind(on_press=lambda x: self.loadSample())

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
        #if self.manager.current == 'main':
        #    self.manager.current = 'maintenance'
        self.manager.current = arg

    def on_enter(self, *args):
        print('entering main screen')

        if self.setParameterDictionary['new recipe']:
            self.loadRecipe()
            self.setParameterDictionary['new recipe'] = False

        if self.setParameterDictionary['save recipe']:
            pass

        self.connectToSheet(self.setParameterDictionary['sheet_ID'])

    def on_leave(self):
        pass
        #print('leaving main screen')

    def _on_keyboard_down(self, instance, keyboard, keycode, text, modifiers):

        try:
            if keycode == 22 and modifiers[0] == 'ctrl':
                #get the recipe name
                recipename = self.saveRecipeButton.text.split(':')[1].strip()
                if len(recipename)>0:
                    recipename = 'Recipes/'+ recipename +'.csv'



                    with open(recipename, mode = 'w') as csv_file:
                        csv_reader = csv.writer(csv_file, delimiter=',')
                        csv_reader.writerow(['Type', 'Slot', 'Des', 'Val'])
                        for slot,i in enumerate(self.inputFieldList):
                            Type = 'P'
                            S = slot
                            Des = i.getTitle()
                            Val = i.getSetValue()
                            csv_reader.writerow([Type,S,Des,Val])
                        for slot,i in enumerate(self.staticFieldList):
                            Type = 'M'
                            S = slot
                            Des = i.getTitle()
                            Val = i.getSetValue()
                            csv_reader.writerow([Type,S,Des,Val])

                    print('recipe saved')


        except IndexError:
            pass

    def loadRecipe(self):
        DF = pd.read_csv(self.setParameterDictionary['recipe'])

        for row in DF.iterrows():
            slot = row[1]['Slot']
            desc = row[1]['Des']
            val = row[1]['Val']
            type = row[1]['Type']
            if val == val:
                if type == 'P':
                    self.inputFieldList[slot].setSetValue(str(val))
                    print(slot, val, desc)
                if type == 'M':
                    val = '{:.0f}'.format(float(val))

                    self.staticFieldList[slot].setSetValue(str(val))

    def updateSheet(self):

        sheet = self.setParameterDictionary['sheet']
        dataholderdictionary = {}

        if sheet == -1:
            pass

        else:
            try:
                L = sheet.row_values(1)
            except IndexError:#no values currently in the sheet
                L = []

            #getting the titles and values from the inputs
            for i in self.inputFieldList:
                fieldtitle = i.getTitle()

                if 'Pressure' in fieldtitle:
                    fieldvalue = i.getReadLabel()
                else:
                    fieldvalue = i.getSetValue()

                if fieldtitle in L:
                    pass
                else:
                    L.append(fieldtitle)
                dataholderdictionary[fieldtitle] = fieldvalue
            for i in self.staticFieldList:
                fieldtitle = i.getTitle()
                fieldvalue = i.getSetValue()
                if fieldtitle in L:
                    pass
                else:
                    L.append(fieldtitle)
                dataholderdictionary[fieldtitle] = fieldvalue

            ######get other info about the sample#######
            #sample ID
            sampleID = self.sampleIDButton.text.split(':')[1].strip()
            dataholderdictionary['Sample ID'] = sampleID
            if 'Sample ID' in L:
                pass
            else:
                L.insert(0,'Sample ID')
            #Date
            date = str(datetime.now())
            dataholderdictionary['Date'] = date
            if 'Date' in L:
                pass
            else:
                L.insert(0,'Date')

            # update columns
            num_cols = len(L)

            if num_cols <=26:
                cells_to_update = 'A1:' + chr(ord('@') + num_cols) + '1'
            else:
                cells_to_update = 'A1:' + 'A'+ chr(ord('@') + num_cols-26) + '1'
            sheet.update(cells_to_update, [L])

            # building a list to update
            toupdate = []
            for coltitle in L:
                try:
                    toupdate.append(dataholderdictionary[coltitle])
                except KeyError:  # if there isn't a value in the sheet
                    toupdate.append('')

            # updating the values
            sheet.append_row(toupdate)

    def connectToSheet(self,sheetID):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        cred = ServiceAccountCredentials.from_json_keyfile_name('aida-update-e3da1e0863cf.json', scope)

        client = gspread.authorize(cred)

        try:
            sheet = client.open_by_key(sheetID)
            sheet = sheet.worksheet('VA_SIO2_SC501')
            print('successfully connected to sheet')
            self.uploadParametersButton.text = 'Save to Sheets\n(Successful Connection)'
            self.setParameterDictionary['sheet'] = sheet
            return sheet

        except Exception as e:
            if 'Max retries exceeded with url' in str(e):
                print('no internet!')
                self.uploadParametersButton.text = 'Save to Sheets\n(Not Connected: No Internet)'
                return -1

            elif 'Requested entity was not found' in str(e):
                self.uploadParametersButton.text = 'Save to Sheets\n(Not Connected: Bad Sheet ID)'
                print('bad sheet name')
                return -1

            elif 'The caller does not have permission' in str(e):
                self.uploadParametersButton.text = 'Save to Sheets\n(Not Connected: Sheet not shared)'
                print('need to share sheet')
                return -1

            else:
                print(str(e))
                return -1

ParameterDictionary = {'title list':[],
                      'min list':[],
                      'max list':[],
                      'new recipe':False,
                       'recipe':'',
                       'save recipe':False,
                       'sheet_ID':'1KfwftgVLMEHyujG-p6m1Kvqw07hqFSUgQVP4ldVyrN8',
                       'sheet':-1}

sm = ScreenManager()
#SettingsScreen = SettingsScreen('maintenance',ParameteDictionary)
MainScreen = ProcessScreen('main',ParameterDictionary)
Maintenance_Screen = Maintenance_Screen('maintenance')
SelectFileScreen = FileSelectScreen('file selection',ParameterDictionary)

sm.add_widget(MainScreen)
sm.add_widget(Maintenance_Screen)
sm.add_widget(SelectFileScreen)

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
