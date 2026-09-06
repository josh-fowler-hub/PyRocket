"""The coursework pitch PID and symmetric gimbal saturation."""


def gimbal_angle(theta, omega, integral, target, kp, kd, ki, limit):
    return max(-limit, min(limit, kp * (target - theta) - kd * omega + ki * integral))
