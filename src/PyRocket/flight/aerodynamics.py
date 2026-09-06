"""MAE-540 empirical axial drag, expressed as an SI vector force.

The coefficient is the piecewise C_D(Mach) in Project/PR13/Nozzle_Funcs.py.
Its break-point jumps are retained. No lift, wind, or aerodynamic torque.
"""
import math
from ..legacy.common import C_D


def drag(vx_m_s, vy_m_s, density_kg_m3, speed_of_sound_m_s, reference_area_m2):
    """Drag opposes velocity in stationary air. Return force and diagnostics."""
    values = locals().copy()
    if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) for v in values.values()):
        raise ValueError('drag inputs must be finite numbers')
    if density_kg_m3 < 0 or speed_of_sound_m_s <= 0 or reference_area_m2 <= 0:
        raise ValueError('density must be nonnegative; sound speed and reference area must be positive')
    speed = math.hypot(vx_m_s, vy_m_s)
    mach = speed / speed_of_sound_m_s
    coefficient = C_D(mach)
    dynamic_pressure = 0.5 * density_kg_m3 * speed**2
    force = coefficient * dynamic_pressure * reference_area_m2
    scale = -force/speed if speed else 0.0
    return dict(drag_x_n=scale*vx_m_s, drag_y_n=scale*vy_m_s,
                drag_n=force, mach_number=mach, drag_coefficient=coefficient,
                dynamic_pressure_pa=dynamic_pressure)
