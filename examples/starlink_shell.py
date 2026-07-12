"""
Worked example: compare a 53-degree Starlink-shell orbit against a
sun-synchronous dusk-dawn orbit for a 10 kW compute node.

Run:
    python examples/starlink_shell.py
"""

from orbital_compute_budget import Orbit, PowerSystem, evaluate_orbit


def run():
    power = PowerSystem(
        compute_power_w=10_000,
        solar_array_power_w=30_000,
        battery_capacity_wh=15_000,
        battery_max_dod=0.8,
        housekeeping_power_w=1_000,
    )

    orbits = {
        "Starlink shell (53 deg, 550 km)": Orbit(550, 53),
        "Sun-sync dusk-dawn (97.6 deg, 550 km)": Orbit(550, 97.6, raan_deg=90),
    }

    for name, orbit in orbits.items():
        # Worst-case over the year.
        worst = min(
            (evaluate_orbit(orbit, power, solar_longitude_deg=float(s))
             for s in range(0, 360, 5)),
            key=lambda r: r.effective_compute_hours_per_day,
        )
        print(f"\n{name}")
        print(f"  Worst-case eclipse fraction: {worst.eclipse_fraction:.3f}")
        print(f"  Worst-case eclipse minutes:  {worst.eclipse_minutes:.1f}")
        print(f"  Battery need / margin:       "
              f"{worst.battery_energy_needed_wh:.0f} / "
              f"{worst.battery_margin_wh:+.0f} Wh")
        print(f"  Effective compute:           "
              f"{worst.effective_compute_hours_per_day:.2f} h/day")
        for n in worst.notes:
            print(f"  ! {n}")


if __name__ == "__main__":
    run()
