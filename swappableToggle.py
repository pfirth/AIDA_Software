from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import WidgetException


class swapToggle(GridLayout):
    '''This Button class just sets the background to the desired images'''
    def __init__(self,buttonText):
        super(swapToggle,self).__init__()

        self.cols = 1
        self.rows = 1

        self.b = ToggleButton(text = buttonText)

    def add(self):
        try:
            self.add_widget(self.b)
        except WidgetException:
            pass

    def remove(self):
        try:
            self.remove_widget(self.b)
        except WidgetException:
            pass


