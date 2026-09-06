"""Shared scalar validation."""
import math

def positive(name, value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")
