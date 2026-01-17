"""Exponential Moving Average (EMA) filter for temperature smoothing."""


def apply_ema(
    current: float,
    previous: float | None,
    tau: int,
    dt: float,
) -> float:
    """
    Apply Exponential Moving Average filter to temperature reading.

    EMA formula: filtered = alpha * current + (1 - alpha) * previous
    Where alpha = dt / (tau + dt), and tau is the time constant.

    The time constant tau determines how quickly the filter responds to changes:
    - Larger tau = slower response, more smoothing
    - Smaller tau = faster response, less smoothing
    - tau = 0 disables filtering entirely

    Args:
        current: Current raw temperature reading from sensor.
        previous: Previous EMA value (None on first reading).
        tau: Time constant in seconds (0 disables filtering).
        dt: Time delta since last update in seconds.

    Returns:
        Filtered temperature value.

    """
    # No filtering if time constant is 0 or no previous value
    if tau <= 0 or previous is None:
        return current

    # Calculate smoothing factor alpha
    alpha = dt / (tau + dt)

    # Apply EMA filter
    return alpha * current + (1 - alpha) * previous
