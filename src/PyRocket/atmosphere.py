"""U.S. Standard Atmosphere 1976 lower-atmosphere pressure (0–86 km).

Source: NOAA-S/T 76-1562, lower-atmosphere hydrostatic layer equations.
Input is geometric altitude in metres above mean sea level, not geopotential
height. Upper-atmosphere diffusion above 86 km is deliberately not extrapolated.
"""
import math

EARTH_GEOPOTENTIAL_RADIUS_M = 6356766.0
G0 = 9.80665
R_SPECIFIC = 8314.32 / 28.9644
BASE_HEIGHTS = (0.0, 11000.0, 20000.0, 32000.0, 47000.0, 51000.0, 71000.0)
LAPSE_RATES = (-0.0065, 0.0, 0.001, 0.0028, 0.0, -0.0028, -0.002)


def _layer(temperature, pressure, lapse, distance):
    next_temperature = temperature + lapse * distance
    if lapse == 0:
        next_pressure = pressure * math.exp(-G0 * distance / (R_SPECIFIC * temperature))
    else:
        next_pressure = pressure * (temperature / next_temperature)**(G0 / (R_SPECIFIC * lapse))
    return next_temperature, next_pressure


def properties(altitude_m):
    """Return pressure, temperature, density and sound speed in SI units."""
    if isinstance(altitude_m, bool) or not math.isfinite(altitude_m) or not 0 <= altitude_m <= 86000:
        raise ValueError('US1976 pressure supports geometric altitude 0–86000 m; no upper-atmosphere extrapolation')
    height = EARTH_GEOPOTENTIAL_RADIUS_M * altitude_m / (EARTH_GEOPOTENTIAL_RADIUS_M + altitude_m)
    temperature, value = 288.15, 101325.0
    for index, (base, lapse) in enumerate(zip(BASE_HEIGHTS, LAPSE_RATES)):
        upper = BASE_HEIGHTS[index+1] if index+1 < len(BASE_HEIGHTS) else height
        temperature, value = _layer(temperature, value, lapse, min(height, upper)-base)
        if height <= upper:
            break
    return dict(pressure_pa=value, temperature_k=temperature,
                density_kg_m3=value / (R_SPECIFIC * temperature),
                speed_of_sound_m_s=math.sqrt(1.4 * R_SPECIFIC * temperature))


def pressure(altitude_m):
    """Return USSA1976 pressure in Pa for geometric altitudes 0–86000 m."""
    return properties(altitude_m)['pressure_pa']
