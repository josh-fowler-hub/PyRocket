#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 23:44:48 2019

@author: josh
"""
import numpy as np
from .common import (T2_T0)

def func(area_rat, k, m2):
    c1 = 2*(k-1)/(k+1)
    first = 1 + (k-1)/2
    second = area_rat**c1
    third = m2**c1
    fourth = (k-1)/2
    fifth = m2**2
    y = first*second*third - fourth*fifth - 1
    return y


def func_prime(area_rat, k, m2):
    c1 = 2*(k-1)/(k+1)
    first = 1 + (k-1)/2
    second = area_rat**c1
    third = m2**(c1-1)
    fourth = (k-1)
    fifth = m2
    y = c1*first*second*third - fourth*fifth
    return y


def M2(area_rat, k, x_0=2):
    error = 1
    x_n = x_0
    while error>0.000001:
        x_new = x_n - (func(area_rat, k, x_n)/func_prime(area_rat, k, x_n))
        error = abs(x_new - x_n)
        x_n = x_new
    return x_n


def press_rat(k, area_rat):
    m2 = M2(area_rat, k)
    exponent = k/(k-1)
    p2_p1 = np.power((1 + 0.5*(k - 1)*(m2**2)), -exponent)
    return p2_p1


def C_F_min(area_rat):
    cfm = -0.0445*(np.log(area_rat))**2 + 0.5324*np.log(area_rat) + 0.1843
    return cfm


def C_F(k, area_rats, p1_p3):
    CFS = []
    flow_sep_ars = []
    for area_rat in area_rats:
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
            flow_sep_ars.append(area_rat)
            cf_min = C_F_min(area_rat)
            CFS.append(cf_min)
        else:
            CFS.append(cf)
    print('Flow Seperation Area Ratio @ k={}, p1/p3={}: '.format(k, p1_p3),
          min(flow_sep_ars))
    return CFS

def area_rat(Mach2s, k):
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
    prs = []
    for m2 in Mach2s:
        first = 0.5*(k-1)*(m2**2)
        exp = k/(k-1)
        pr = (1 + first)**exp
        prs.append(pr)
    return prs
