"""SI quasi-steady cylindrical-grain motor simulation.

The driver couples grain regression, mass balance and ideal nozzle expansion.
It does not model ignition, chamber filling, or a post-burn pressure tail.
"""
import math

from ..validation import positive


def mach_from_area(area_ratio, gamma, subsonic=False):
    positive('area_ratio', area_ratio)
    if area_ratio < 1 or not math.isfinite(gamma) or gamma <= 1:
        raise ValueError('area_ratio must be >= 1 and gamma must be > 1')
    if area_ratio == 1:
        return 1.0

    def area(m):
        return ((2 + (gamma - 1) * m*m) / (gamma + 1)) ** ((gamma + 1) / (2 * (gamma - 1))) / m

    low, high = (1e-14, 1.0) if subsonic else (1.0, 2.0)
    if subsonic and area(low) < area_ratio:
        raise ValueError('area ratio exceeds solver range')
    if not subsonic:
        for _ in range(100):
            if area(high) >= area_ratio:
                break
            high *= 2
        else:
            raise ValueError('could not bracket Mach number')
    for _ in range(160):
        middle = (low + high) / 2
        if (area(middle) > area_ratio) == subsonic:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def simulate(outer_radius_m, inner_radius_m, length_m, density_kg_m3,
             burn_coefficient, burn_exponent, characteristic_velocity_m_s,
             throat_radius_m, exit_area_m2, gamma, grain_count=1,
             ends_inhibited=True, ambient_pressure_pa=101325.0,
             temperature_k=293.15, reference_temperature_k=293.15,
             temperature_sensitivity_per_k=0.0, erosion_m_s_pa=0.0,
             time_step_s=0.01, max_time_s=120.0, max_steps=100000):
    """Burn rate = coefficient * exp(sensitivity * delta T) * pressure**exponent.

    Coefficient units are m/s/Pa**exponent. Erosion is radial m/s/Pa.
    Time stepping uses the current regression rate with an exact last web step.
    """
    values = locals().copy()
    for name, value in values.items():
        if name in {'ends_inhibited', 'grain_count', 'max_steps'}:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            raise ValueError(f'{name} must be a finite number')
    for name in ['outer_radius_m', 'inner_radius_m', 'length_m', 'density_kg_m3',
                 'burn_coefficient', 'characteristic_velocity_m_s', 'throat_radius_m',
                 'exit_area_m2', 'temperature_k', 'reference_temperature_k', 'time_step_s', 'max_time_s']:
        positive(name, values[name])
    if type(grain_count) is not int or grain_count < 1:
        raise ValueError('grain_count must be a positive integer')
    if type(max_steps) is not int or not 1 <= max_steps <= 1000000:
        raise ValueError('max_steps must be an integer between 1 and 1000000')
    if type(ends_inhibited) is not bool:
        raise ValueError('ends_inhibited must be a boolean')
    if outer_radius_m <= inner_radius_m:
        raise ValueError('outer_radius_m must exceed inner_radius_m')
    if not 0 <= burn_exponent < 1 or gamma <= 1:
        raise ValueError('burn_exponent must be in [0, 1); gamma must exceed one')
    if ambient_pressure_pa < 0 or erosion_m_s_pa < 0:
        raise ValueError('ambient pressure and erosion coefficient must be nonnegative')
    if exit_area_m2 < math.pi * throat_radius_m**2:
        raise ValueError('exit area must be at least the throat area')
    effective_a = burn_coefficient * math.exp(temperature_sensitivity_per_k * (temperature_k - reference_temperature_k))
    positive('temperature-adjusted burn coefficient', effective_a)
    web_limit = min(outer_radius_m - inner_radius_m,
                    math.inf if ends_inhibited else length_m / 2)
    initial_mass = density_kg_m3 * grain_count * math.pi * length_m * (outer_radius_m**2 - inner_radius_m**2)
    time = web = impulse = 0.0
    throat = throat_radius_m
    rows = []
    reason = 'max_steps'
    for step in range(max_steps + 1):
        radius = inner_radius_m + web
        length = length_m if ends_inhibited else max(0.0, length_m - 2 * web)
        remaining_mass = density_kg_m3 * grain_count * math.pi * length * max(0.0, outer_radius_m**2 - radius**2)
        burned_out = web >= web_limit
        area = 0.0 if burned_out else grain_count * (2 * math.pi * radius * length +
                    (0 if ends_inhibited else 2 * math.pi * (outer_radius_m**2 - radius**2)))
        throat_area = math.pi * throat**2
        if throat_area > exit_area_m2:
            raise ValueError('eroded throat exceeds exit area; reduce duration or erosion')
        pressure = (effective_a * density_kg_m3 * characteristic_velocity_m_s * area / throat_area) ** (1 / (1 - burn_exponent)) if area else 0.0
        rate = effective_a * pressure**burn_exponent if area else 0.0
        mach = mach_from_area(exit_area_m2 / throat_area, gamma)
        pressure_ratio = (1 + (gamma - 1) / 2 * mach**2) ** (-gamma / (gamma - 1))
        cf = math.sqrt(2 * gamma**2 / (gamma - 1) * (2 / (gamma + 1)) ** ((gamma + 1) / (gamma - 1)) * (1 - pressure_ratio ** ((gamma - 1) / gamma)))
        thrust = pressure * throat_area * cf + (pressure * pressure_ratio - ambient_pressure_pa) * exit_area_m2 if area else 0.0
        if area and pressure * (2 / (gamma + 1)) ** (gamma / (gamma - 1)) <= ambient_pressure_pa:
            raise ValueError('simulation leaves the choked-flow regime')
        row = dict(time_s=time, web_m=web, propellant_mass_kg=remaining_mass,
                   ambient_pressure_pa=ambient_pressure_pa, exit_area_m2=exit_area_m2,
                   throat_pressure_pa=pressure * (2 / (gamma + 1)) ** (gamma / (gamma - 1)),
                   burn_area_m2=area, chamber_pressure_pa=pressure, burn_rate_m_s=rate,
                   mass_flow_kg_s=area * rate * density_kg_m3, throat_area_m2=throat_area,
                   exit_pressure_pa=pressure * pressure_ratio, thrust_n=thrust,
                   total_impulse_n_s=impulse)
        if not all(math.isfinite(v) for v in row.values()):
            raise ValueError('simulation produced a non-finite state')
        rows.append(row)
        if burned_out:
            reason = 'burnout'
            break
        if time >= max_time_s:
            reason = 'max_time'
            break
        if step == max_steps:
            break
        positive('burn rate', rate)
        dt = min(time_step_s, max_time_s - time, (web_limit - web) / rate)
        if time + dt <= time:
            raise ValueError('time step too small to advance simulation')
        # Left-rectangle integration matches the explicit state advancement.
        impulse += thrust * dt
        throat += erosion_m_s_pa * pressure * dt
        web = min(web_limit, web + rate * dt)
        time += dt
    consumed = initial_mass - rows[-1]['propellant_mass_kg']
    return dict(summary=dict(termination=reason, completed=reason == 'burnout',
                             duration_s=time, initial_propellant_mass_kg=initial_mass,
                             consumed_propellant_mass_kg=consumed, total_impulse_n_s=impulse,
                             specific_impulse_s=impulse / (consumed * 9.80665) if consumed else 0.0),
                history=rows)
