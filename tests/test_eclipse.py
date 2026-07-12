"""
Validation tests for eclipse physics against published references.

Key benchmarks:
  - At beta=0, LEO min sunlit fraction is ~59-63% (Wikipedia "Beta angle";
    arXiv 2406.08342 gives ~63% at 550 km).
  - Max LEO eclipse duration ~35 min (ERAU IJAAA 2019).
  - Above the critical beta angle, eclipse fraction is exactly 0.
  - ISS-like orbit (~408 km, 51.6 deg) period ~92-93 min.
"""

import math

import pytest

from orbital_compute_budget import (
    Orbit,
    beta_angle_deg,
    beta_critical_deg,
    eclipse_fraction,
    sunlit_fraction,
    eclipse_minutes,
)


def test_period_iss_like():
    orbit = Orbit(altitude_km=408, inclination_deg=51.6)
    # ISS period is ~92.7 min.
    assert 90.0 < orbit.period_minutes() < 95.0


def test_period_550km():
    orbit = Orbit(altitude_km=550, inclination_deg=53)
    # Starlink-shell period is ~95.6 min.
    assert 94.0 < orbit.period_minutes() < 97.0


def test_sunlit_fraction_beta_zero_550km():
    # At beta=0 and 550 km, sunlit fraction should be ~0.62-0.63.
    f = sunlit_fraction(altitude_km=550, beta_deg=0.0)
    assert 0.59 <= f <= 0.65


def test_sunlit_min_at_beta_zero_bounded_below():
    # Wikipedia: a LEO satellite spends at least ~59% of its orbit in sun.
    for alt in (300, 400, 550, 800):
        f = sunlit_fraction(altitude_km=alt, beta_deg=0.0)
        assert f >= 0.55  # generous lower bound across low altitudes


def test_no_eclipse_above_critical_beta():
    alt = 550
    b_star = beta_critical_deg(alt)
    # Just above critical: no eclipse.
    assert eclipse_fraction(alt, b_star + 0.5) == 0.0
    # Just below critical: some eclipse.
    assert eclipse_fraction(alt, b_star - 5.0) > 0.0


def test_eclipse_fraction_decreases_with_beta():
    alt = 550
    f0 = eclipse_fraction(alt, 0.0)
    f30 = eclipse_fraction(alt, 30.0)
    f50 = eclipse_fraction(alt, 50.0)
    assert f0 > f30 > f50


def test_max_leo_eclipse_duration():
    # Max eclipse (beta=0) at low LEO should be ~30-38 min.
    orbit = Orbit(altitude_km=400, inclination_deg=51.6)
    ecl = eclipse_minutes(orbit, beta_deg=0.0)
    assert 28.0 < ecl < 38.0


def test_beta_angle_range():
    # Beta angle magnitude never exceeds ~ (inclination + obliquity).
    for sol_lon in range(0, 360, 15):
        b = beta_angle_deg(53.0, 0.0, float(sol_lon))
        assert -90.0 <= b <= 90.0


def test_beta_critical_monotonic_in_altitude():
    # Higher altitude -> smaller critical beta (easier to avoid eclipse).
    assert beta_critical_deg(300) > beta_critical_deg(550) > beta_critical_deg(1200)


def test_eclipse_fraction_bounds():
    for alt in (300, 550, 1200):
        for beta in (0, 10, 30, 60, 80):
            f = eclipse_fraction(alt, float(beta))
            assert 0.0 <= f <= 0.5  # eclipse never exceeds half an orbit
