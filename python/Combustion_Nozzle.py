# -*- coding: utf-8 -*-
"""
Created on Wed Feb 13 23:24:40 2019

F = q*Ve + (Pe - Pa)*Ae

p = m*v

F = dp/dt

F = m*a

C = Ve + (Pe - Pa)*Ae/q

F = q*C

Isp = C/go guess specific impulse and get a flow rate

C = Isp*go

Cstar = Pc*At/q  

At = (q/Pt)*(R*Tt/(M*k))**(0.5)  changing mass flow rate changes pressure

Pt = Pc*(1 + (k - 1)/2)**(-k/(k -1))

Tt = Tc/(1 + (k - 1)/2)

Ve = ((2*k/(k - 1))*(R*Tc/M)*(1 - (Pe/Pc)**((k - 1)/k)))**(0.5)

@author: jfowl
"""

import numpy as np
import matplotlib.pyplotb

go = 32.2  # gravity at sea level, ft/s^2
Pa = 14.7*144  # atmospheric pressure, psi
Pe = 14.7*144  # exit pressure, psi
Pc = 300*144  # chamber pressure, psi
Tc = 1200 + 459.67  # chamber temp, R
alpha = 15  # angle of nozzle, degrees
k = 1.4  # specific heat ratio oxygen
R = 1545.35  # Univeral Gas Constant, in lb/ lbmol R
q = 0.001  # rate of mass flow, lb/s
Mox = 31.9988  # molecular weight of Oxygen
MHTPB = 1.3  # molecular weight of HTPB

Ve = ((2*k/(k - 1))*(R*Tc/Mox)*(1 - (Pe/Pc)**((k - 1)/k)))**(0.5)
Tt = Tc/(1 + (k - 1)/2)
Pt = Pc*(1 + (k - 1)/2)**(-k/(k - 1))
At = (q/Pt)*(R*Tt/(Mox*k))**(0.5)
MN = ((2/(k - 1))*((Pc/Pa) - 1))**(0.5)
Ae = (At/MN)*(((1 + (k - 1)/2)*MN**2)/((k + 1)/2))**((k + 1)/(2*(k - 1)))
C = Ve + (Pe - Pa)*Ae/q
F = q*C
Cstar = Pc*At/q
F = q*Ve + (Pe - Pa)*Ae
