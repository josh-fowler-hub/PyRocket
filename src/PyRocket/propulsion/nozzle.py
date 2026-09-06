"""Ideal nozzle performance in SI units."""
import math
from ..validation import positive

def nozzle(chamber_pressure, exit_pressure, ambient_pressure,
           temperature, mass_flow, molecular_weight, gamma):
    """Ideal, isentropic nozzle with sonic throat and supersonic exit.

    Pressures: Pa; temperature: K; mass flow: kg/s; molecular weight: kg/kmol.
    """
    for name, value in locals().copy().items():
        if name != "ambient_pressure":
            positive(name, value)
    if not math.isfinite(ambient_pressure) or ambient_pressure < 0:
        raise ValueError("ambient_pressure must be finite and nonnegative")
    if gamma <= 1:
        raise ValueError("gamma must be greater than one")
    gas_constant = 8314.46261815324 / molecular_weight
    throat_temperature = temperature * 2 / (gamma + 1)
    throat_pressure = chamber_pressure * (2 / (gamma + 1)) ** (gamma / (gamma - 1))
    if exit_pressure > throat_pressure:
        raise ValueError("exit pressure must not exceed sonic throat pressure")
    throat_area = mass_flow / throat_pressure * math.sqrt(gas_constant * throat_temperature / gamma)
    mach = math.sqrt(2 / (gamma - 1) * ((chamber_pressure / exit_pressure) ** ((gamma - 1) / gamma) - 1))
    area_ratio = ((1 + (gamma - 1) / 2 * mach**2) / ((gamma + 1) / 2)) ** ((gamma + 1) / (2 * (gamma - 1))) / mach
    exit_area = throat_area * area_ratio
    velocity = math.sqrt(2 * gamma / (gamma - 1) * gas_constant * temperature * (1 - (exit_pressure / chamber_pressure) ** ((gamma - 1) / gamma)))
    thrust = mass_flow * velocity + (exit_pressure - ambient_pressure) * exit_area
    return dict(throat_pressure_pa=throat_pressure, throat_temperature_k=throat_temperature,
                throat_area_m2=throat_area, exit_mach=mach, area_ratio=area_ratio,
                exit_area_m2=exit_area, exhaust_velocity_m_s=velocity, thrust_n=thrust,
                characteristic_velocity_m_s=chamber_pressure * throat_area / mass_flow,
                specific_impulse_s=thrust / (mass_flow * 9.80665))
