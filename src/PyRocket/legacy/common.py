"""Identical, self-contained formulas shared by historical versions."""
import numpy as np


def max_web(rf, ri):
    wmax = rf -ri
    return wmax


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


def web_thickness(r, ri):
    """
    Calculate the web thickness from the Current radius of the Grain:
            r = Current Radius
            ri = Initial Radius
    """
    w = r - ri
    return w


def radius(w, ri):
    """
    Calculate the Current Radius of the Grain from the web thickness:
            w = Web Distance
            ri = initial radius of the Grain
    """
    r = w + ri
    return r


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


def P1(a, rho_b, sigma_p, Tb, Tb0, Cstar, Ab, At, n, g0):
    sens = np.exp(sigma_p*(Tb - Tb0))
    p = a*rho_b*sens*Cstar*(Ab/At)
    p1 = np.power(p/g0, 1/(1-n))
    return p1


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


def Specific_Impulse(It, mp0):
    Is = It/(mp0)
    return Is


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
