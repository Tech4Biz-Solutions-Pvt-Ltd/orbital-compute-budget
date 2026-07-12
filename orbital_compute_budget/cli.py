"""
Command-line interface for orbital-compute-budget.

Example
-------
    ocb --altitude 550 --inclination 53 \\
        --compute-power 1000 --array-power 3000 --battery-wh 1500
"""

from __future__ import annotations

import argparse
import sys

from .eclipse import Orbit
from .budget import PowerSystem, evaluate_orbit


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ocb",
        description="Effective compute budget for a data center in low Earth orbit.",
    )
    p.add_argument("--altitude", type=float, required=True,
                   help="Orbit altitude in km.")
    p.add_argument("--inclination", type=float, required=True,
                   help="Orbit inclination in degrees.")
    p.add_argument("--raan", type=float, default=0.0,
                   help="Right ascension of ascending node, degrees (default 0).")
    p.add_argument("--solar-longitude", type=float, default=0.0,
                   help="Solar ecliptic longitude, degrees (sets season/beta).")

    p.add_argument("--compute-power", type=float, required=True,
                   help="Steady compute (GPU) load in watts.")
    p.add_argument("--array-power", type=float, required=True,
                   help="Solar array output in full sun, watts.")
    p.add_argument("--battery-wh", type=float, required=True,
                   help="Battery capacity in watt-hours.")
    p.add_argument("--max-dod", type=float, default=0.8,
                   help="Max battery depth-of-discharge, 0..1 (default 0.8).")
    p.add_argument("--housekeeping-power", type=float, default=0.0,
                   help="Non-compute base load, watts (default 0).")
    p.add_argument("--eclipse-compute-fraction", type=float, default=1.0,
                   help="Fraction of compute kept on during eclipse (default 1.0).")
    p.add_argument("--sweep-year", action="store_true",
                   help="Report best/worst case over a full year of beta angles.")
    return p


def _print_result(orbit: Orbit, res) -> None:
    print(f"Orbit: {orbit.altitude_km:.0f} km, {orbit.inclination_deg:.1f} deg incl")
    print(f"  Period:            {res.period_minutes:6.2f} min")
    print(f"  Beta angle:        {res.beta_deg:6.2f} deg")
    print(f"  Eclipse fraction:  {res.eclipse_fraction:6.3f}")
    print(f"  Sunlit / eclipse:  {res.sunlit_minutes:5.1f} / "
          f"{res.eclipse_minutes:5.1f} min")
    print(f"  Effective compute: {res.effective_compute_hours_per_day:6.2f} "
          f"compute-hours/day")
    feas = "OK" if res.battery_feasible else "INFEASIBLE"
    print(f"  Battery:           {feas} "
          f"(need {res.battery_energy_needed_wh:.0f} Wh, "
          f"margin {res.battery_margin_wh:+.0f} Wh)")
    for note in res.notes:
        print(f"  ! {note}")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    orbit = Orbit(
        altitude_km=args.altitude,
        inclination_deg=args.inclination,
        raan_deg=args.raan,
    )
    power = PowerSystem(
        compute_power_w=args.compute_power,
        solar_array_power_w=args.array_power,
        battery_capacity_wh=args.battery_wh,
        battery_max_dod=args.max_dod,
        housekeeping_power_w=args.housekeeping_power,
        eclipse_compute_fraction=args.eclipse_compute_fraction,
    )

    if args.sweep_year:
        results = [
            evaluate_orbit(orbit, power, solar_longitude_deg=float(s))
            for s in range(0, 360, 5)
        ]
        best = max(results, key=lambda r: r.effective_compute_hours_per_day)
        worst = min(results, key=lambda r: r.effective_compute_hours_per_day)
        print("=== Best case over the year ===")
        _print_result(orbit, best)
        print("\n=== Worst case over the year ===")
        _print_result(orbit, worst)
    else:
        res = evaluate_orbit(
            orbit, power, solar_longitude_deg=args.solar_longitude
        )
        _print_result(orbit, res)

    return 0


if __name__ == "__main__":
    sys.exit(main())
