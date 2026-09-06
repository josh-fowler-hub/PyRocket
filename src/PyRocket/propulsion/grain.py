"""Illustrative historical grain curves."""
def grain_curves(samples=10):
    """Reproduce the legacy illustrative curves, including their signed values.

    These polynomials have no established force units or physical burn model.
    The plateau depends on the sampling, as in the original script.
    """
    if samples < 2:
        raise ValueError("samples must be at least two")
    rows = []
    neutral = regressive = 0.0
    for i in range(samples):
        t = 10 * i / (samples - 1)
        polynomial = 500 * t**2 + 5000 * t - 500
        progressive = -polynomial / 20 - 25
        if t < 2:
            neutral = -polynomial / 2 - 25
        if t < 1.5:
            regressive = -polynomial - 25
            value = regressive
        else:
            value = regressive + polynomial / 50 - 25
        rows.append((t, progressive, neutral, value))
    return rows + [(11, -500, -500, -500), (12, 0, 0, 0)]
