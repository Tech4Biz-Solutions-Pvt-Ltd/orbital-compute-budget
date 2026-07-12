# orbital-compute-budget
# Copyright (c) 2026 Tech4Biz Solutions. Licensed under the MIT License.
# Project: https://github.com/Tech4Biz-Solutions-Pvt-Ltd/orbital-compute-budget
# Maintained by Tech4Biz Solutions (https://tech4biz.io)
"""
Energy balance and effective-compute budget for an orbital compute node.

The physics of *when* the satellite is in sunlight (eclipse.py) is exact
and citable. The step from there to "usable compute" depends on hardware
choices: solar array size, battery capacity, depth-of-discharge limits,
and how much of the load must stay on during eclipse.

Those hardware parameters are TUNABLE INPUTS, not claimed truths. The
model is transparent: given your assumptions, it computes the answer,
and it flags when the battery cannot carry the load through eclipse.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .eclipse import Orbit, beta_angle_deg, eclipse_fraction


@dataclass
class PowerSystem:
    """
    Hardware power configuration. All values are user-supplied
    assumptions; defaults are illustrative, not authoritative.
    """
    compute_power_w: float                 # steady GPU/compute load, watts
    solar_array_power_w: float             # array output in full sun, watts
    battery_capacity_wh: float             # usable battery energy, watt-hours
    battery_max_dod: float = 0.8           # max depth-of-discharge (0..1)
    housekeeping_power_w: float = 0.0      # non-compute base load, watts
    charge_efficiency: float = 0.90        # round-trip charge efficiency
    eclipse_compute_fraction: float = 1.0  # fraction of compute kept on in eclipse

    @property
    def usable_battery_wh(self) -> float:
        return self.battery_capacity_wh * self.battery_max_dod


@dataclass
class OrbitComputeResult:
    beta_deg: float
    eclipse_fraction: float
    period_minutes: float
    sunlit_minutes: float
    eclipse_minutes: float
    sun_compute_hours: float          # compute-hours accrued in sunlight
    eclipse_compute_hours: float      # compute-hours accrued in eclipse
    effective_compute_hours_per_orbit: float
    effective_compute_hours_per_day: float
    battery_feasible: bool            # can the battery carry eclipse load?
    battery_energy_needed_wh: float
    battery_margin_wh: float          # usable - needed (negative = infeasible)
    notes: list[str] = field(default_factory=list)


SECONDS_PER_DAY = 86400.0


def evaluate_orbit(
    orbit: Orbit,
    power: PowerSystem,
    solar_longitude_deg: float = 0.0,
) -> OrbitComputeResult:
    """
    Compute the effective compute budget for one orbit at a given
    point in the year (via solar longitude, which sets beta angle).
    """
    beta = beta_angle_deg(
        orbit.inclination_deg, orbit.raan_deg, solar_longitude_deg
    )
    f_ecl = eclipse_fraction(orbit.altitude_km, beta)
    period_min = orbit.period_minutes()

    sunlit_min = (1.0 - f_ecl) * period_min
    eclipse_min = f_ecl * period_min

    notes: list[str] = []

    # --- Sunlight phase: compute runs, surplus charges battery ---
    sun_compute_hours = (sunlit_min / 60.0)  # compute assumed fully on in sun

    # --- Eclipse phase: battery carries whatever compute stays on ---
    eclipse_load_w = (
        power.compute_power_w * power.eclipse_compute_fraction
        + power.housekeeping_power_w
    )
    eclipse_hours = eclipse_min / 60.0
    battery_needed_wh = eclipse_load_w * eclipse_hours

    usable_wh = power.usable_battery_wh
    battery_feasible = battery_needed_wh <= usable_wh
    battery_margin = usable_wh - battery_needed_wh

    if not battery_feasible:
        notes.append(
            "Battery cannot carry the eclipse load: compute must throttle "
            "or the array/battery must be resized."
        )

    # Effective compute during eclipse = what the battery can actually sustain.
    if battery_feasible:
        eclipse_compute_hours = eclipse_hours * power.eclipse_compute_fraction
    else:
        # Battery-limited: scale eclipse compute down to what energy allows.
        sustainable_fraction = 0.0
        if eclipse_load_w > 0:
            sustainable_fraction = min(
                1.0, usable_wh / battery_needed_wh
            )
        eclipse_compute_hours = (
            eclipse_hours * power.eclipse_compute_fraction * sustainable_fraction
        )

    # --- Check the sunlight phase can both run compute AND recharge ---
    surplus_sun_w = power.solar_array_power_w - (
        power.compute_power_w + power.housekeeping_power_w
    )
    recharge_capacity_wh = (
        max(0.0, surplus_sun_w) * (sunlit_min / 60.0) * power.charge_efficiency
    )
    if battery_feasible and recharge_capacity_wh < battery_needed_wh:
        notes.append(
            "Solar surplus in sunlight is insufficient to fully recharge the "
            "battery before the next eclipse; sustained operation not possible "
            "with these parameters."
        )

    if surplus_sun_w < 0:
        notes.append(
            "Solar array cannot even meet the sunlight load: array undersized."
        )

    effective_per_orbit = sun_compute_hours + eclipse_compute_hours
    orbits_per_day = SECONDS_PER_DAY / orbit.period_seconds()
    effective_per_day = effective_per_orbit * orbits_per_day

    return OrbitComputeResult(
        beta_deg=beta,
        eclipse_fraction=f_ecl,
        period_minutes=period_min,
        sunlit_minutes=sunlit_min,
        eclipse_minutes=eclipse_min,
        sun_compute_hours=sun_compute_hours,
        eclipse_compute_hours=eclipse_compute_hours,
        effective_compute_hours_per_orbit=effective_per_orbit,
        effective_compute_hours_per_day=effective_per_day,
        battery_feasible=battery_feasible,
        battery_energy_needed_wh=battery_needed_wh,
        battery_margin_wh=battery_margin,
        notes=notes,
    )
