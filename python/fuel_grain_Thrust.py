# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 14:46:26 2019

@author: jfowl
"""

import matplotlib.pyplot as plt
import numpy as np

file = open('cylindrical_fuel_grain_thrust.csv', 'w')

tvec = list(np.linspace(0, 10, 10))


def progressive_fuel_grain(tvec, thrust):
    T = []
    for t in tvec:
        T.append(-(500*t**2 + 5000*t - 500)/20 - 25)
    return T


def neutral_fuel_grain(tvec, thrust):
    T = []
    for t in tvec:
        if t < 2:
            T.append(-(500*t**2 + 5000*t - 500)/2 - 25)
            old_t = t
        else:
            T.append(-(500*old_t**2 + 5000*old_t - 500)/2 - 25)
    return T


def regressive_fuel_grain(tvec, thrust):
    T = []
    for t in tvec:
        if t < 1.5:
            Thrust = -(500*t**2 + 5000*t - 500) - 25
            T.append(Thrust)
            newT = Thrust
        else:
            T.append(newT + (500*t**2 + 5000*t - 500)/50 - 25)
    return T


proT = progressive_fuel_grain(tvec, 5000)
neuT = neutral_fuel_grain(tvec, 5000)
regT = regressive_fuel_grain(tvec, 5000)

tvec.append(11)
tvec.append(12)

proT.append(-500)
neuT.append(-500)
regT.append(-500)
proT.append(0)
neuT.append(0)
regT.append(0)

plt.figure(1)
plt.plot(tvec, proT)
plt.plot(tvec, neuT)
plt.plot(tvec, regT)
plt.show()

for i in range(len(tvec)):
    line = str(tvec[i]) + ',' + str(proT[i]) + ',' + str(neuT[i]) + ',' + str(regT[i]) + '\n'
    file.writelines(line)

file.close()