"""Planar rigid-body equations adapted from the ME-426 final project.

Inertial x points radially outward at launch. Pitch is measured from +x.
The historical inertia convention is retained: m*r²/4 + m*length²/3.
"""
import math
import numpy as np


def inertia(mass, radius, length):
    return mass * (radius**2 / 4 + length**2 / 3)


def derivatives(state, mass, thrust, beta, gravitational_parameter, length, diameter, target):
    x, vx, y, vy, theta, omega, integral = state
    radius = math.hypot(x, y)
    gravity = gravitational_parameter / radius**3
    angle = theta - beta
    angular_acceleration = thrust * math.sin(beta) * length / (2 * inertia(mass, diameter / 2, length))
    return np.array([vx, thrust * math.cos(angle) / mass - gravity*x,
                     vy, thrust * math.sin(angle) / mass - gravity*y,
                     omega, angular_acceleration, target - theta])
