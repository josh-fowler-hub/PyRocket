#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 19:06:25 2019

@author: josh
"""
import numpy as np
from .common import (max_web, new_length, web_thickness, radius, area_rat, p2_p0, T2_T0, burn_rate, temp_coeff, propellant_mass_flow, P1, web_size, rho_f, P3, T3, C_D, rthroat, Throat_Area, Circle, Specific_Impulse, Speed_of_Sound, Air_Density, Altitude, Velocity, Acceleration)


def calc_dw(w, wold, ro, r0):
    wmax = max_web(ro, r0)
    dw = w - wold
    wnext = w + r0
    dw = abs(wmax - wnext)
    return dw


def Propellant_Mass(rho_b, ro, r0, w, L0, ngrain):
    """Calculates the Mass of the Propellant:
            rho_b = Density of the Propellant
            ro = Outside radius of the Propellant Grain
            ri = Inside radius of the Propellant Grain
            length = length of the Propellant Grain
            ngrain = Number of Grains in the Motor"""
    L = L0 - 2*w
    wmax = max_web(ro, r0)
    if w >= wmax or L <= 0:
        # if the Motor has burned out the Volume is zero
        V = 0
    else:
        # Calculate the Volume of the propellant
        V = np.pi*L*(ro**2 - (r0 + w)**2)
    Mass = ngrain*rho_b*V
    # Return the number of propellant grains times the density times the volume
    return Mass


def Burn_Area_in(radius, length, rf, ngrain):
    """Calculate the Burn Surface Area of the Propellant Grain:
            radius = inside radius of the Grain
            length = the length of the Grain
            rf = Outside Radius of the Grain
            ngrain = Number of Grains in the Motor"""
    # Calculates the Burn Area with the ends inhibited
    if length == 0 or radius >= rf:
        # If the ends have burned together or the motor has burn to the outside
        # radius do not calculate the surface area
        sa = 0
    else:
        # Calculate the Burn Surface Area of a single Grain
        sa = 2*np.pi*radius*length
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
    if length == 0 or radius >= rf:
        # If the ends have burned together do not calculate the surface area
        sa = 0
    else:
        sa = 2*np.pi*(rf**2 - (r0 + w)**2 + (L0 - 2*w)*(r0 + w))
    return ngrain*sa


# Calculate the web thickness from the current radius


# Calculate the radius from the web thickness
# the web_thickness and radius functions are mostly for book keeping,
# We use w for the plot and put w into the burn area function


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


def M2(area_rat, k, x_0=2):
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
    error = 1
    x_n = x_0
    while error > 1e-10:
        x_new = x_n - (func(area_rat, k, x_n)/func_prime(area_rat, k, x_n))
        error = abs(x_new - x_n)
        x_n = x_new
    return x_n


def press_rat(k, area_rat, x_0=2):
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
    m2 = M2(area_rat, k, x_0)
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


def C_F(k, area_rat, p1_p3):
    """
    Calculates the Thrust Coefficient:
        area_rat = Area Ratio of the Nozzle
        p1_p3 = The value of the chamber pressure divided by the ambient
                pressure
    """
    if p1_p3 == 0:
        cf = 0
    else:
        p2_p1 = press_rat(k, area_rat)
        p3_p1 = 1/p1_p3
        first = (2*k**2)/(k-1)
        second = 2/(k+1)
        secondexp = (k+1)/(k-1)
        third = np.power(second, secondexp)
        fourth = 1
        fifth = p2_p1
        fifthexp = (k-1)/k
        sixth = np.power(fifth, fifthexp)
        seventh = fourth - sixth
        FIRST = first*third*seventh
        SECOND = p2_p1
        THIRD = p3_p1
        FOURTH = area_rat
        cf = np.sqrt(FIRST) + (SECOND - THIRD)*FOURTH
    if cf < C_F_min(area_rat):
        if cf > 0:
            print('Flow Seperation Detected...')
        else:
            pass
    else:
        pass
    return cf


def Ab_At(Ab, At):
    if At == 0:
        K = 0
    else:
        K = Ab/At
    return K


def K(rho_b, a, cstar, p1, n):
    K = np.power(p1, 1 - n)/(rho_b*a*cstar)
    return K


def P2(a, rho_b, r, Cstar, k, Ab, At, Ae, n, sigma_p, Tb, Tb0, g0):
    p1 = P1(a, rho_b, sigma_p, Tb, Tb0, Cstar, Ab, At, n, g0)
    p2 = p1*press_rat(k, Ae/At)
    return p2


def next_time(ti, dw, a0, p1, sigma_p, Tb, Tb0, n):
    if p1 == 0:
        tip1 = ti + 0.001
    else:
        tip1 = ti + dw/(burn_rate(a0, p1, sigma_p, Tb, Tb0, n))
    return tip1


def Total_Impulse(Itold, F, Fold, t, told):
    It = Itold + 0.5*(F + Fold)*(t - told)
    return It


def Speed_of_Sound_Air(alt):
    rprime = 1545.3465119999998*32.1740
    k = 1.4
    Mw = 28.97
    R = rprime/Mw
    a = np.sqrt(k*R*T3(alt))
    return a


def Drag_Force(A, v, alt, g0):
    Mach = abs(v/Speed_of_Sound_Air(alt))
    CD = C_D(Mach)
    rho3 = Air_Density(alt)
    D = 0.5*CD*A*rho3*v*(abs(v))
    return D/g0
