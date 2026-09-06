"""Thrust data reduction in SI units."""
import math
from .validation import positive

def analyze(time, thrust, propellant_mass=None):
    """Integrate thrust in N over time in s; optional propellant mass in kg."""
    if len(time) != len(thrust) or len(time) < 2:
        raise ValueError("at least two matching time/thrust samples are required")
    if not all(math.isfinite(v) for v in [*time, *thrust]):
        raise ValueError("time and thrust samples must be finite")
    if any(b <= a for a, b in zip(time, time[1:])):
        raise ValueError("time samples must be strictly increasing")
    impulse = sum((b - a) * (x + y) / 2 for a, b, x, y in zip(time, time[1:], thrust, thrust[1:]))
    duration = time[-1] - time[0]
    result = dict(samples=len(time), duration_s=duration, total_impulse_n_s=impulse,
                  average_thrust_n=impulse / duration, peak_thrust_n=max(thrust))
    if propellant_mass is not None:
        positive("propellant mass", propellant_mass)
        result["specific_impulse_s"] = impulse / (propellant_mass * 9.80665)
    return result


from pathlib import Path
from types import SimpleNamespace

def analyze_csv(input, time_column='Time', thrust_column='Thrust', thrust_unit='N',
                propellant_mass=None, limit=None):
    from .data import read_curve
    if thrust_unit not in {'N', 'lbf'}:
        raise ValueError('thrust_unit must be N or lbf')
    if limit is not None and type(limit) is not int:
        raise ValueError('limit must be an integer')
    args = SimpleNamespace(input=Path(input), time_column=time_column,
                           thrust_column=thrust_column, thrust_unit=thrust_unit, limit=limit)
    time, thrust = read_curve(args)
    result = analyze(time, thrust, propellant_mass)
    result['history'] = [dict(time_s=t, thrust_n=f) for t, f in zip(time, thrust)]
    return result
