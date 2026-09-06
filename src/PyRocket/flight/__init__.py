"""Planar flight dynamics, pitch control and time integration."""
from .simulation import simulate
from .dynamics import inertia, derivatives
from .control import gimbal_angle
from .aerodynamics import drag
