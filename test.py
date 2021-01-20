import numpy as np
import math
import pandas as pd
'''for i in range(21,30,1):
    print(str(i)+'.0')'''

'''for i in np.arange(21.0, 23.0, 0.1):
    command = 'P' + "{:.1f}".format(i) + '\r'
    command = str.encode(command)

    print(command)'''

motorParamDictionary = {'Gear diameter': 50, 'Steps per revolution':5000}

def distanceToSteps(distance):
    '''takes a float argment for distance with units
    of mm. Returns the numer of steps the motor should take
    based on the gear diameter and steps per revolution.'''

    GD = motorParamDictionary['Gear diameter']  # float, mm
    SPR = motorParamDictionary['Steps per revolution']  # float, steps

    gearCircumference = math.pi * GD  # mm traveled in one revolution
    mmPerStep = gearCircumference / SPR  # number of mm traveled each step

    steps = distance / mmPerStep
    roundedSteps = round(steps,0)
    formatedSteps = '{:.0f}'.format(roundedSteps)
    return formatedSteps


def speedToStepDelay(speed):
    '''takes a float argument for speed with units of
    mm/s. Returns a delay time in useconds. Used to convert
    user-entered params into motor control params'''
    speed = float(speed)
    GD = motorParamDictionary['Gear diameter']  # float, mm
    SPR = motorParamDictionary['Steps per revolution']  # float, steps

    gearCircumference = math.pi * GD  # mm traveled in one revolution
    mmPerStep = gearCircumference / SPR  # number of mm traveled each step

    delay_s = mmPerStep / speed
    delay_us = delay_s * 1e6

    roundedDelay = round(delay_us, 0)  # round because motor can't take half a step
    formatedDelay = '{:.0f}'.format(roundedDelay)  # formatting for communication


    return formatedDelay



Motorsettings = pd.read_csv('MotorSettings.CSV')
print(Motorsettings.head())

GD = float(Motorsettings['Gear Diameter (mm)'].values)
SPR = float(Motorsettings['Steps per revolution(steps)']. values)
print(GD, SPR)
print(type(GD))