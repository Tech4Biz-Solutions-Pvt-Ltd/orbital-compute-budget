# orbital-compute-budget

**By [Tech4Biz Solutions](https://tech4biz.io)**

Estimate the effective compute you actually get from a data center in low Earth orbit, after eclipse periods and battery limits.

Space data centers are moving from concept to funded engineering. The single number that governs their economics is rarely stated cleanly: given an orbit and a compute power draw, how much usable compute do you actually get per day once you account for eclipse, battery depth-of-discharge, and recharge headroom? This tool answers that question with transparent, citable physics.

## What it does

You give it an orbit (altitude, inclination) and a power system (compute load, solar array, battery). It computes:

- Orbital period, beta angle, and eclipse fraction over the year.
- Sunlit and eclipse minutes per orbit.
- Effective compute-hours per day.
- Whether the battery can carry the eclipse load, with an explicit margin.
- Warnings when the array is undersized or cannot recharge in time.

## Install

```bash
git clone https://github.com/Tech4Biz-Solutions-Pvt-Ltd/orbital-compute-budget.git
cd orbital-compute-budget
pip install -e .
```

## Use

```bash
ocb --altitude 550 --inclination 53 \
    --compute-power 1000 --array-power 3000 --battery-wh 1500
```

Sweep a full year of beta angles to see best and worst case:

```bash
ocb --altitude 550 --inclination 97.6 --raan 90 \
    --compute-power 1000 --array-power 3000 --battery-wh 1500 --sweep-year
```

Or from Python:

```python
from orbital_compute_budget import Orbit, PowerSystem, evaluate_orbit

orbit = Orbit(altitude_km=550, inclination_deg=53)
power = PowerSystem(
    compute_power_w=1000,
    solar_array_power_w=3000,
    battery_capacity_wh=1500,
)
result = evaluate_orbit(orbit, power)
print(result.effective_compute_hours_per_day)
```

## The key insight

If your battery is sized to carry the full compute load through eclipse, you get close to 24 compute-hours per day. Eclipse does not cost you compute time in that case. It costs you battery mass and an oversized solar array. If you choose to throttle compute during eclipse to save battery, effective compute drops accordingly. This tool makes that tradeoff explicit rather than hidden.

## The physics is exact and citable

The eclipse and beta-angle model uses standard, published spacecraft-power equations:

- **Beta angle** (angle between the orbit plane and the Sun vector), the standard formulation from RAAN, inclination, solar longitude, and Earth's obliquity.
- **Critical beta angle** `arcsin(R_earth / (R_earth + h))`, above which the orbit has no eclipse.
- **Eclipse fraction** via the cylindrical-shadow approximation.

These reproduce known benchmarks: at beta=0 and 550 km, the sunlit fraction is ~62%; maximum LEO eclipse is ~35 minutes; a 550 km orbit period is ~95.6 minutes. All are covered by the test suite.

## The power-system parameters are honest assumptions

Solar array size, battery capacity, depth-of-discharge, and eclipse compute fraction are **your inputs**, not claimed truths. The tool computes the consequence of your assumptions and flags infeasible configurations. This separation, exact physics versus tunable engineering assumptions, is deliberate and is what makes the results defensible.

## References

- Beta angle and LEO sunlit fraction: Wikipedia, "Beta angle."
- Eclipse-time computation for LEO small satellites: R. M. S., *International Journal of Aviation, Aeronautics, and Aerospace*, 6(5), 2019.
- Power-generation fraction and cylindrical shadow geometry: arXiv:2406.08342.
- Orbital mechanics fundamentals: Vallado, *Fundamentals of Astrodynamics and Applications*.
- Small-satellite thermal / eclipse parameterization: NASA SSRI, "Preliminary Thermal Analysis of Small Satellites."

## Tests

```bash
pip install pytest
pytest
```

16 tests validate the physics against the published benchmarks above.

## License

MIT. Copyright (c) 2026 Tech4Biz Solutions.

## About

Built and maintained by [Tech4Biz Solutions](https://tech4biz.io), a hardware-to-cloud engineering firm. This tool is part of our open-source work on space and orbital compute infrastructure.

Web: [tech4biz.io](https://tech4biz.io) / [tech4bizsolutions.com](https://tech4bizsolutions.com) · Contact: contact@tech4biz.io
