#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 19:06:25 2019

@author: josh
"""
import numpy as np


def max_web(rf, ri):
    wmax = rf - ri
    return wmax


def calc_dw(w, wold, ro, r0):
    wmax = max_web(ro, r0)
    dw = w - wold
    wnext = w + r0
    dw = abs(wmax - wnext)
    return dw


def Propellant_Mass(rho_b, ro, r0, w, L0, ngrain, grain_end):
    """Calculates the Mass of the Propellant:
            rho_b = Density of the Propellant
            ro = Outside radius of the Propellant Grain
            ri = Inside radius of the Propellant Grain
            length = length of the Propellant Grain
            ngrain = Number of Grains in the Motor"""
    if grain_end is True:
        L = L0
    else:
        L = L0 - 2*w
    wmax = max_web(ro, r0)
    if w > wmax:
        # if the Motor has burned out the Volume is zero
        V = 0
    else:
        # Calculate the Volume of the propellant
        V = np.pi*L*(ro**2 - (r0 + w)**2)
    Mass = ngrain*rho_b*V
    # Return the number of propellant grains times the density times the volume
    return Mass


def Burn_Area_in(L0, rf, r0, w, ngrain):
    """Calculate the Burn Surface Area of the Propellant Grain:
            radius = inside radius of the Grain
            length = the length of the Grain
            rf = Outside Radius of the Grain
            ngrain = Number of Grains in the Motor"""
    # Calculates the Burn Area with the ends inhibited
        # Calculate the Burn Surface Area of a single Grain
    sa = 2*np.pi*(r0 + w)*L0
    # Return the Surface Area Times the number of Grains
    return ngrain*sa


# Calculate the Burn Area with the ends uninhibited
def Burn_Area(radius, L0, length, rf, r0, w, ngrain):
    """Calculate the Burn Area with the ends uninhibited:
            radius = Inside Radius of the Grain
            L0 = Initial Length of the Grain
            length = Current Length of the Grain
            rf = Outside radius of the Grain
            r0 = Initial radius of the Grain
            w = Web distance of the burned grain
            ngrain = Number of Grains in the motor"""
    if length == 0 or radius > rf:  # If the ends or the radius has burned out
        # do not calculate the surface area
        sa = 0
    else:
        sa = 2*np.pi*(rf**2 - (r0 + w)**2 + (L0 - 2*w)*(r0 + w))
    return ngrain*sa


def new_length(L0, w):
    """
    Calculate the New Length of the Grain after one Burn Step distance:
            length = old length of the Grain
            dr = The step distance"""
    nl = L0 - 2*w
    if nl <= 0:
        # If the ends have burned together do not calculate a negetive
        # length
        nl = 0
    else:
        nl = nl
    return nl


# Calculate the web thickness from the current radius
def web_thickness(r, ri):
    """
    Calculate the web thickness from the Current radius of the Grain:
            r = Current Radius
            ri = Initial Radius
    """
    w = r - ri
    return w


# Calculate the radius from the web thickness
# the web_thickness and radius functions are mostly for book keeping,
# We use w for the plot and put w into the burn area function
def radius(w, ri):
    """
    Calculate the Current Radius of the Grain from the web thickness:
            w = Web Distance
            ri = initial radius of the Grain
    """
    r = w + ri
    return r


def func(area_rat, k, m2):
    """
    Error function for the Mach Number:
            area_rat = Area Ratio of the Nozzle
            k = Ratio of Specific Heats
            m2 = The Exit Mach Number
            """
    c1 = 2*(k-1)/(k+1)
    first = 1 + (k-1)/2
    second = area_rat**c1
    third = m2**c1
    fourth = (k-1)/2
    fifth = m2**2
    y = first*second*third - fourth*fifth - 1
    return y


def func_prime(area_rat, k, m2):
    """
    Derivative of the Error Function for the Mach Number:
            area_rat = Area Ratio of the Nozzle
            k = ratio of specific heats
            m2 = The exit Mach Number
            """
    c1 = 2*(k-1)/(k+1)
    first = 1 + (k-1)/2
    second = area_rat**c1
    third = m2**(c1-1)
    fourth = (k-1)
    fifth = m2
    y = c1*first*second*third - fourth*fifth
    return y


def M2(area_rat, k, p1_b=True, x_0=2):
    """
    Newton raphson root-finding scheme for the Exit Mach Number:
            area_rat = Area Ratio of the Nozzle
            k = ratio of specific heats
            x_0 = Initial guess for the Mach Number
    
    NOTE: x_0 defaults to 2 which should be sufficient for finding the
          exit Mach Number, however if you have a good idea (such as a
          previous Mach Number one time step ago, you can force a faster
          convergence.
      """
    if x_0 == 0 or p1_b is not True:
        x_n = 0
    else:
        error = 1
        x_n = x_0
        while error > 1e-6:
            x_new = x_n - (func(area_rat, k, x_n)/func_prime(area_rat, k, x_n))
            error = abs((x_new - x_n)/x_n)*100
            x_n = x_new
    return round(x_n, 15)


def press_rat(k, area_rat, p1_b=True, x_0=2):
    """
    Calculates the pressure ratio p2/p1:
            k = ratio of specific heats
            area_rat = Area Ratio of the nozzle
            x_0 = Initial guess for the Mach Number
    
    NOTE: x_0 defaults to 2 which should be sufficient for finding the
          exit Mach Number, however if you have a good idea (such as a
          previous Mach Number one time step ago, you can force a faster
          convergence.
      """
    m2 = M2(area_rat, k, p1_b, x_0)
    exponent = k/(k-1)
    p2_p1 = np.power((1 + 0.5*(k - 1)*(m2**2)), -exponent)
    return p2_p1


def C_F_min(area_rat):
    """
    Calculates the minimum Thrust coefficient, at which flow seperation will
    occur
    """
    cfm = -0.0445*(np.log(area_rat))**2 + 0.5324*np.log(area_rat) + 0.1843
    return cfm


def C_F(k, area_rat, p1_p3, p1_b=True):
    """
    Calculates the Thrust Coefficient:
        area_rat = Area Ratio of the Nozzle
        p1_p3 = The value of the chamber pressure divided by the ambient
                pressure
    """
    if p1_p3 == 0 or p1_b is not True:
        cf = 0
    else:
        p2_p1 = round(press_rat(k, area_rat, p1_b=p1_b), 15)
        p3_p1 = round(1/p1_p3, 15)
        first = round((2*k**2)/(k-1), 15)
        second = round(2/(k+1), 15)
        secondexp = round((k+1)/(k-1), 15)
        third = round(np.power(second, secondexp), 15)
        fourth = 1
        fifth = round(p2_p1, 15)
        fifthexp = round((k-1)/k, 15)
        sixth = round(np.power(fifth, fifthexp), 15)
        seventh = round(fourth - sixth, 15)
        FIRST = round(first*third*seventh, 15)
        SECOND = round(p2_p1, 15)
        THIRD = round(p3_p1, 15)
        FOURTH = round(area_rat, 15)
        cf = round(np.sqrt(FIRST), 15) + round((SECOND - THIRD)*FOURTH, 15)
    if cf < C_F_min(area_rat):
        if cf > 0:
            print('Flow Seperation Detected...')
        else:
            pass
    else:
        pass
    return round(cf, 15)


# def C_F(k, area_rat, p1_p3):
#     if p1_p3 == 0:
#         cf = 0
#     else:
#         p3_p1 = 1/p1_p3
#         m2 = M2(k, area_rat)
#         p2_p1 = (1 + 0.5*(k - 1)*(m2**2))
#         p2_p1 = np.power(p2_p1, -k/(k-1))
#         first = (2*(k**2))/(k-1)
#         second = 2/(k+1)
#         second = np.power(second, (k+1)/(k-1))
#         third = 1 - np.power(p2_p1, (k-1)/k)
#         cf = np.sqrt(first*second*third) + (p2_p1 - p3_p1)*area_rat
#         print(m2, '\t', cf)
#     return cf


def area_rat(Mach2s, k):
    """
    Calculate the Area ratio for the rocket motor:
        Mach2s = a list of Mach Numbers
        k = the specific heat ratio
    """
    area_rats = []
    for m2 in Mach2s:
        first = 1/m2
        num = 1 + ((k-1)/2)*(m2**2)
        denom = (k+1)/2
        second = num/denom
        secondexp = (k+1)/(2*(k-1))
        ar = first*np.power(second, secondexp)
        area_rats.append(ar)
    return area_rats


def p2_p0(Mach2s, k):
    """
    Calculate the pressure ratio p2/p0:
        Mach2s = list of Mach Numbers
        k = ratio of specific heats
    """
    prs = []
    for m2 in Mach2s:
        first = 0.5*(k-1)*(m2**2)
        exp = k/(k-1)
        pr = (1 + first)**exp
        prs.append(pr)
    return prs


def T2_T0(Mach2s, k):
    trs = []
    for m2 in Mach2s:
        first = 0.5*(k-1)*(m2**2)
        tr = 1 + first
        trs.append(tr)
    return trs


def burn_rate(a, p1, sigma_p, Tb, Tb0, n):
    sens = np.exp(sigma_p*(Tb - Tb0))
    r = a*sens*np.power(p1, n)
    if r <= 0:
        r = 0
    else:
        r = r
    return r


def temp_coeff(r, p1, n):
    if r == 0:
        a = 0
    else:
        a = np.exp(np.log(r) - n*np.log(p1))
        if a <= 0:
            a = 0
        else:
            a = a
    return a


def propellant_mass_flow(Ab, r, rho_b):
    mdot = Ab*r*rho_b
    return mdot


def Ab_At(Ab, At):
    if At == 0:
        K = 0
    else:
        K = Ab/At
    return K


def K(rho_b, a, cstar, p1, n):
    K = np.power(p1, 1 - n)/(rho_b*a*cstar)
    return K


def P1(a, rho_b, sigma_p, Tb, Tb0, Cstar, Ab, At, n, g0):
    sens = np.exp(sigma_p*(Tb - Tb0))
    p = a*rho_b*sens*Cstar*(Ab/At)
    p1 = np.power(p/g0, 1/(1-n))
    return p1


def P2(a, rho_b, r, Cstar, k, Ab, At, Ae, n, sigma_p, Tb, Tb0, g0):
    p1 = P1(a, rho_b, sigma_p, Tb, Tb0, Cstar, Ab, At, n, g0)
    p2 = p1*press_rat(k, Ae/At)
    return p2


def web_size(w0, t, r, wmax):
    w = w0 + t*r
    if w >= wmax:
        w = wmax
    else:
        w = w
    return w


def rho_f(alt):
    if alt < 82000:
        rho3 = (0.00000000001255)*alt**2 - (0.0000019453)*alt + 0.07579
    else:
        rho3 = 0
    return rho3


def P3(alt):
    if alt < 83000:
        pres3 = (-4.272981E-14*alt**3 + 0.000000008060081*alt**2 -
                 0.0005482655*alt + 14.69241)
    else:
        pres3 = 0
    return pres3


def T3(alt):
    if alt < 32809:
        Temp3 = -0.0036*alt + 518
    else:
        Temp3 = 399
    return Temp3


def C_D(Mach):
    if Mach < 0.6:
        Cd = 0.15
    elif Mach < 1.2:
        Cd = -0.12 + 0.45*Mach
    elif Mach < 1.8:
        Cd = 0.76 - 0.283*Mach
    elif Mach < 4:
        Cd = 0.311 - 0.034*Mach
    else:
        Cd = 0.175
    return Cd


def rthroat(rold, t, told, p1):
    Dnew = (2*rold) + 0.000087*(t - told)*p1
    return Dnew/2


def Throat_Area(rt):
    At = np.pi*(rt**2)
    return At


def Circle(xs, a, b, r):
    """(x+a)^2 + (y+b)^2 = r^2"""
    pys = []
    nys = []

    for x in xs:
        ny = np.sqrt(r**2 - (x + a)**2) - b
        py = -np.sqrt(r**2 - (x + a)**2) - b
        pys.append(py)
        nys.append(ny)

    return pys, nys


def next_time(ti, dw, a0, p1, sigma_p, Tb, Tb0, n):
    if p1 == 0:
        tip1 = ti + 0.1
    else:
        tip1 = ti + dw/(burn_rate(a0, p1, sigma_p, Tb, Tb0, n))
    return tip1


def Total_Impulse(Itold, F, Fold, t, told):
    if F == 0:
        It = 0
    else:
        It = Itold + 0.5*(F + Fold)*(t - told)
    return It


def Specific_Impulse(It, mp0):
    Is = It/(mp0)
    return Is


def Speed_of_Sound_Air(alt):
    rprime = 1545.3465119999998*32.1740
    k = 1.4
    Mw = 28.97
    R = rprime/Mw
    a = np.sqrt(k*R*T3(alt))
    return a
    

def Speed_of_Sound(k, Mw, T):
    rprime = 1545.3465119999998*32.1740
    R = rprime/Mw
    T = T + 460.67
    a = np.sqrt(k*R*T)
    return a


def Air_Density(alt): 
   if alt < 82000:
       rho3 = 0.00000000001255*(alt**2) - 0.0000019453*alt + 0.07579
   else:
       rho3 = 0
   return rho3


def Drag_Force(A, v, alt, g0):
    Mach = abs(v/Speed_of_Sound_Air(alt))
    CD = C_D(Mach)
    rho3 = Air_Density(alt)
    D = 0.5*CD*A*rho3*v*(abs(v))
    return D/g0


def Altitude(altold, v, vold, t, told):
    alt = altold + ((v + vold)/2)*(t - told)
    if alt <= 0:
        Alt = 0
    else:
        Alt = alt
    return Alt


def Velocity(vold, acc, t, told, alt):
    v = vold + acc*(t - told)
    if v < 0 and alt == 0:
        v = 0
    return v


def Acceleration(F, D, mp, mf, mb, mc, g0, alt):
    Fm = F*g0
    Dm = D*g0
    TM = mp + mf + mb + mc
    # Gm = 6.6743015e-11
    # G = Gm*(35.3146667)/(2.20462262)
    # r = (3958.7613)*5280 + alt
    # EM = 1.3166e25
    # g = (G*(EM*TM))/(r**2)
    Acc = Fm/TM - Dm/TM - g0
    return Acc
