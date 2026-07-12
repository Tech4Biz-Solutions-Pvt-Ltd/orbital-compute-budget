"""Tests for the energy-balance / compute-budget logic."""

from orbital_compute_budget import Orbit, PowerSystem, evaluate_orbit


def _healthy_system():
    # Array comfortably exceeds load; battery sized for a full eclipse.
    return PowerSystem(
        compute_power_w=1000,
        solar_array_power_w=3000,
        battery_capacity_wh=1500,
        battery_max_dod=0.8,
        housekeeping_power_w=100,
    )


def test_full_compute_when_battery_carries_eclipse():
    # When the battery is sized to carry the full eclipse load, compute
    # runs 100% of the time -> ~24 h/day. The cost of eclipse then shows
    # up as battery mass/margin, NOT as lost compute. This is the key
    # tradeoff the tool is meant to expose.
    orbit = Orbit(altitude_km=550, inclination_deg=53)
    res = evaluate_orbit(orbit, _healthy_system(), solar_longitude_deg=0.0)
    assert res.effective_compute_hours_per_day > 23.9
    assert res.battery_feasible


def test_compute_lost_when_eclipse_compute_reduced():
    # If we choose NOT to run full compute in eclipse (e.g. to save
    # battery), effective compute drops below wall-clock.
    orbit = Orbit(altitude_km=550, inclination_deg=53)
    sys = _healthy_system()
    sys.eclipse_compute_fraction = 0.0  # compute only in sunlight
    res = evaluate_orbit(orbit, sys, solar_longitude_deg=0.0)
    assert res.effective_compute_hours_per_day < 20.0
    assert res.effective_compute_hours_per_day > 0.0


def test_battery_feasible_when_well_sized():
    orbit = Orbit(altitude_km=550, inclination_deg=53)
    res = evaluate_orbit(orbit, _healthy_system(), solar_longitude_deg=0.0)
    assert res.battery_feasible
    assert res.battery_margin_wh >= 0.0


def test_battery_infeasible_when_undersized():
    orbit = Orbit(altitude_km=400, inclination_deg=51.6)
    weak = PowerSystem(
        compute_power_w=2000,
        solar_array_power_w=5000,
        battery_capacity_wh=100,   # far too small for a 35-min eclipse
        battery_max_dod=0.8,
    )
    res = evaluate_orbit(orbit, weak, solar_longitude_deg=0.0)
    assert not res.battery_feasible
    assert res.battery_margin_wh < 0.0
    assert any("Battery cannot carry" in n for n in res.notes)


def test_no_eclipse_orbit_gives_full_compute():
    # High-beta (near-terminator) orbit: pick solar longitude that yields
    # a large beta so there is no eclipse.
    orbit = Orbit(altitude_km=550, inclination_deg=97.6, raan_deg=90)
    # Sweep to find a no-eclipse point.
    best = max(
        (evaluate_orbit(orbit, _healthy_system(), solar_longitude_deg=s)
         for s in range(0, 360, 5)),
        key=lambda r: r.effective_compute_hours_per_day,
    )
    # At its best (sun-synchronous dusk-dawn), compute approaches 24h/day.
    assert best.effective_compute_hours_per_day > 20.0


def test_undersized_array_flagged():
    orbit = Orbit(altitude_km=550, inclination_deg=53)
    bad = PowerSystem(
        compute_power_w=4000,
        solar_array_power_w=1000,   # cannot even meet load in sun
        battery_capacity_wh=2000,
    )
    res = evaluate_orbit(orbit, bad, solar_longitude_deg=0.0)
    assert any("array undersized" in n.lower() for n in res.notes)
