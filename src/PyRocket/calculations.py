"""Explicit calculation catalog. Configuration never imports or evaluates code."""
import contextlib
import inspect
import io
import math

import numpy as np

from .validation import positive
from .propulsion import nozzle, grain_curves
from .legacy import v0, v1, v2
from .propulsion.motor import mach_from_area, simulate
from .flight import simulate as simulate_flight
from .atmosphere import pressure as atmosphere_pressure
from .atmosphere import properties as atmosphere_properties


def _mach_old(area_rat, k, x_0=2):
    return mach_from_area(area_rat, k, subsonic=x_0 < 1)


def _mach_new(area_rat, k, p1_b=True, x_0=2):
    return 0.0 if not p1_b or x_0 == 0 else _mach_old(area_rat, k, x_0)


# Replace unbounded Newton iterations, including calls inside legacy functions.
# Preserve the original signatures and branch-selection convention.
v0.M2 = _mach_old
v1.M2 = _mach_old
v2.M2 = _mach_new


def _cf_v0(k, area_rats, p1_p3):
    # Original v0 clamps to the empirical minimum but min([]) raised when
    # no point separated. Keep its clamp and report separation as metadata.
    positive('p1_p3', p1_p3)
    result, separated = [], []
    for area in area_rats:
        ratio = v0.press_rat(k, area)
        cf = math.sqrt(2*k*k/(k-1) * (2/(k+1))**((k+1)/(k-1)) *
                       (1-ratio**((k-1)/k))) + (ratio-1/p1_p3)*area
        minimum = v0.C_F_min(area)
        if cf < minimum:
            separated.append(area)
        result.append(max(cf, minimum))
    if separated:
        print(f'Flow separation minimum area ratio: {min(separated)}')
    return result


v0.C_F = _cf_v0


from .analysis import analyze_csv


CATALOG = {
    'atmosphere_properties': atmosphere_properties,
    'atmosphere_pressure': atmosphere_pressure,
    'nozzle': nozzle,
    'analyze': analyze_csv,
    'grain': grain_curves,
    'mach': mach_from_area,
    'simulation': simulate,
    'flight': simulate_flight,
}
for version, module in [('v0', v0), ('v1', v1), ('v2', v2)]:
    for name, function in vars(module).items():
        if not name.startswith('_') and inspect.isfunction(function):
            CATALOG[f'legacy.{version}.{name}'] = function


def normalize(value):
    if isinstance(value, np.ndarray):
        return normalize(value.tolist())
    if isinstance(value, np.generic):
        return normalize(value.item())
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('calculation produced a non-finite result')
    if isinstance(value, complex):
        raise ValueError('calculation produced a complex result')
    return value


def validate(name, parameters):
    if name not in CATALOG:
        raise ValueError(f'unknown calculation {name!r}; use catalog to list available functions')
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a TOML table')
    try:
        inspect.signature(CATALOG[name]).bind(**parameters)
    except TypeError as exc:
        raise ValueError(f'{name}: {exc}') from exc
    def check(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('parameters must be finite')
        if isinstance(value, list):
            for item in value:
                check(item)
        elif not isinstance(value, (float, int, str, bool)):
            raise ValueError('parameters must be numbers, booleans, strings, or arrays')
    for value in parameters.values():
        check(value)


def calculate(name, parameters):
    validate(name, parameters)
    messages = io.StringIO()
    try:
        with contextlib.redirect_stdout(messages), np.errstate(all='raise'):
            result = normalize(CATALOG[name](**parameters))
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f'{name}: {exc}') from exc
    response = {'calculation': name, 'result': result}
    if messages.getvalue().strip():
        response['messages'] = messages.getvalue().strip().splitlines()
    return response


def describe(name):
    if name not in CATALOG:
        raise ValueError(f'unknown calculation: {name}')
    function = CATALOG[name]
    return f'{name}{inspect.signature(function)}\n{inspect.getdoc(function) or "Historical formula; original parameter names and units apply."}'
