from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget


class Viewer(Widget):
    '''A button that results in a popup window when pressed. Changing the test within
    the popup menu changes the text on the button'''
    def __init__(self,title,but,Set_Label):

        super(Viewer,self).__init__()

        self.Set_Label = Set_Label
        self.but = but
        self.title = title
        self.Pops = Popup(title = self.title, size_hint = (None,None), size = (300,150),auto_dismiss = False,
                    pos_hint = {'x':.425,'y':.6},separator_color = [0.3,0.2,0,1],title_color = [0.3,0.2,0,1],
                    title_size = '20sp')
        #self.Pops.background = 'images/Pop_Background.png'

        self.Pops.bind(on_open = lambda widget: self.FocTxt())
        self.Tex = TextInput(font_size = 35,multiline=False)


        self.B = Button(text = 'Press To Confirm')
        self.B.bind(on_press = lambda widget: self.SubChangeDismiss(self.Tex,self.Set_Label,self.Pops))
        self.FL = BoxLayout(orientation = 'vertical',size_hint_x= 1,size_hint_y= 1,rows = 1)
        self.box1 = BoxLayout(orientation = 'vertical',size_hint_x= 1,size_hint_y= .6,rows = 1)
        self.box2 = BoxLayout(orientation = 'vertical',size_hint_x= 1,size_hint_y= .4,rows = 1)

        self.Pops.add_widget(self.FL)
        self.FL.add_widget(self.box1)
        self.FL.add_widget(self.box2)
        self.box1.add_widget(self.Tex)
        self.box2.add_widget(self.B)

        self.add_widget(self.Pops)

        self.wasUpdated = 'Hello Peter'

    def SubChangeDismiss(self,Tx,Bt,PP):
        '''When activated, this function changes the text
        of a button to the text of the text input, defocuses
        on the text input box and closes the popup'''
        if Tx.text.strip() == '':
            Bt.text = '0'
        else:
            Bt.text =  Tx.text
        Tx.focus = False
        self.wasUpdated = 'hello Chad'
        PP.dismiss()

    def FocTxt(self):
        '''When the popup is opened up, it immediately focuses on the text box.
        This will automatically call keyboards in apple/android devices, plus is
        just convienient'''
        self.Tex.focus = True
        return self.Pops

    '''def build(self):

        self.Pops.add_widget(self.FL)
        self.FL.add_widget(self.box1)
        self.FL.add_widget(self.box2)
        self.box1.add_widget(self.Tex)
        self.box2.add_widget(self.B)
        return self.Pops'''
