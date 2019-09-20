import serial
import time
import pandas as pd


class keithly2440():
    def __init__(self,comport):
        self.connection = serial.Serial('COM' + str(comport),115200) #create the connection

    def inc(self):
        pass
