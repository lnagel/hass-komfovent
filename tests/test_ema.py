"""Test EMA (Exponential Moving Average) formula calculation."""

import pytest

from custom_components.komfovent.core.ema import apply_ema


class TestApplyEma:
    """Test cases for the apply_ema function."""

    def test_no_filtering_when_tau_zero(self) -> None:
        """Test that tau=0 disables filtering and returns raw value."""
        raw_temp = 22.5
        previous_ema = 20.0
        tau = 0
        dt = 60.0

        result = apply_ema(raw_temp, previous_ema, tau, dt)
        assert result == raw_temp

    def test_no_filtering_when_tau_negative(self) -> None:
        """Test that negative tau disables filtering and returns raw value."""
        raw_temp = 22.5
        previous_ema = 20.0
        tau = -100
        dt = 60.0

        result = apply_ema(raw_temp, previous_ema, tau, dt)
        assert result == raw_temp

    def test_no_filtering_when_no_previous_value(self) -> None:
        """Test that first reading returns raw value."""
        raw_temp = 21.0
        previous_ema = None
        tau = 600
        dt = 60.0

        result = apply_ema(raw_temp, previous_ema, tau, dt)
        assert result == raw_temp

    def test_alpha_calculation_standard(self) -> None:
        """Test alpha calculation with standard values."""
        # tau=600s, dt=60s -> alpha = 60/(600+60) = 0.0909...
        tau = 600
        dt = 60.0
        expected_alpha = dt / (tau + dt)
        assert expected_alpha == pytest.approx(0.0909, rel=0.01)

    def test_ema_smoothing_effect(self) -> None:
        """Test that EMA smooths out sudden changes."""
        previous_ema = 20.0
        raw_temp = 25.0  # Sudden 5 degree spike
        tau = 600
        dt = 60.0

        result = apply_ema(raw_temp, previous_ema, tau, dt)

        # alpha = 60/660 = 0.0909
        # result = 0.0909 * 25 + 0.9091 * 20 = 2.27 + 18.18 = 20.45
        assert result == pytest.approx(20.45, rel=0.01)

        # The filtered value should be much closer to previous than raw
        assert abs(result - previous_ema) < abs(raw_temp - previous_ema) * 0.2

    def test_ema_convergence_over_time(self) -> None:
        """Test that EMA converges to the raw value over multiple iterations."""
        tau = 600
        dt = 60.0
        raw_temp = 25.0  # Constant raw temperature
        ema = 20.0  # Starting point

        # Apply EMA multiple times - should converge toward raw_temp
        for _ in range(100):
            ema = apply_ema(raw_temp, ema, tau, dt)

        # After many iterations, should be very close to raw value
        assert ema == pytest.approx(raw_temp, rel=0.01)

    def test_ema_with_short_time_constant(self) -> None:
        """Test EMA with shorter time constant (faster response)."""
        previous_ema = 20.0
        raw_temp = 22.0
        tau = 120  # 2 minutes - faster response
        dt = 60.0

        result = apply_ema(raw_temp, previous_ema, tau, dt)

        # alpha = 60/180 = 0.333
        # result = 0.333 * 22 + 0.667 * 20 = 7.33 + 13.33 = 20.67
        assert result == pytest.approx(20.67, rel=0.01)

    def test_ema_with_long_time_constant(self) -> None:
        """Test EMA with longer time constant (slower response)."""
        previous_ema = 20.0
        raw_temp = 22.0
        tau = 1800  # 30 minutes - slower response
        dt = 60.0

        result = apply_ema(raw_temp, previous_ema, tau, dt)

        # alpha = 60/1860 = 0.0323, result ≈ 20.06 (barely moves)
        assert result == pytest.approx(20.06, rel=0.01)

    def test_ema_step_response(self) -> None:
        """Test EMA step response characteristics."""
        tau = 600
        dt = 60.0
        raw_temp = 25.0  # Step change target
        ema = 20.0  # Starting point

        # Calculate how many iterations to reach ~63% of the step
        # Time constant tau means 63% reached after tau seconds
        iterations_for_tau = tau / dt  # 10 iterations

        # Apply EMA for tau seconds worth of iterations
        for _ in range(int(iterations_for_tau)):
            ema = apply_ema(raw_temp, ema, tau, dt)

        # After one time constant, should be ~63% of the way there
        step_size = raw_temp - 20.0  # 5 degrees
        expected_progress = step_size * 0.63  # ~3.15 degrees
        actual_progress = ema - 20.0

        # Allow some tolerance due to discrete sampling
        assert actual_progress == pytest.approx(expected_progress, rel=0.1)

    def test_ema_negative_temperature(self) -> None:
        """Test EMA works with negative temperatures."""
        previous_ema = -5.0
        raw_temp = -10.0
        tau = 600
        dt = 60.0

        result = apply_ema(raw_temp, previous_ema, tau, dt)

        # Should be between previous and raw
        assert result < previous_ema
        assert result > raw_temp

    def test_ema_with_varying_dt(self) -> None:
        """Test EMA adjusts correctly with different time intervals."""
        previous_ema = 20.0
        raw_temp = 22.0
        tau = 600

        # With longer dt, alpha increases, more weight to raw
        result_short_dt = apply_ema(raw_temp, previous_ema, tau, dt=30.0)
        result_standard_dt = apply_ema(raw_temp, previous_ema, tau, dt=60.0)
        result_long_dt = apply_ema(raw_temp, previous_ema, tau, dt=120.0)

        # Longer dt should move result closer to raw_temp
        assert result_short_dt < result_standard_dt < result_long_dt
        assert result_long_dt < raw_temp  # But not all the way there

    def test_ema_preserves_steady_state(self) -> None:
        """Test EMA preserves value when raw equals previous."""
        previous_ema = 21.5
        raw_temp = 21.5  # Same as previous
        tau = 600
        dt = 60.0

        result = apply_ema(raw_temp, previous_ema, tau, dt)

        # Should stay approximately the same (allowing for float precision)
        assert result == pytest.approx(previous_ema)

    @pytest.mark.parametrize(
        ("precision", "expected"), [(0, 20.0), (1, 20.5), (2, 20.45)]
    )
    def test_ema_precision(self, precision: int, expected: float) -> None:
        """Test precision parameter controls decimal rounding."""
        result = apply_ema(25.0, 20.0, tau=600, dt=60.0, precision=precision)
        assert result == expected
