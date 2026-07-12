"""
Generate the graphs used in the README, directly from the library's
own physics. These are not illustrative sketches: every curve is
produced by orbital_compute_budget itself, so the README plots and the
code always agree.

Run:  python docs/make_figures.py
"""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from orbital_compute_budget import (
    Orbit,
    PowerSystem,
    eclipse_fraction,
    sunlit_fraction,
    beta_angle_deg,
    beta_critical_deg,
    evaluate_orbit,
)

# Tech4Biz brand: dark navy background, blue accent, calm, structured.
NAVY = "#0B1F3A"
PANEL = "#0F2647"
BLUE = "#3B82F6"
CYAN = "#38BDF8"
AMBER = "#F59E0B"
RED = "#EF4444"
GREEN = "#22C55E"
GRID = "#1E3A5F"
TEXT = "#E5EDF7"

plt.rcParams.update({
    "figure.facecolor": NAVY,
    "axes.facecolor": PANEL,
    "savefig.facecolor": NAVY,
    "text.color": TEXT,
    "axes.labelcolor": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "axes.edgecolor": GRID,
    "grid.color": GRID,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "figure.dpi": 130,
})


def _style(ax):
    ax.grid(True, alpha=0.4, linewidth=0.6)
    for s in ax.spines.values():
        s.set_color(GRID)


# ---------------------------------------------------------------------------
# Figure 1: Sunlit fraction vs beta angle, for several altitudes.
# ---------------------------------------------------------------------------
def fig_sunlit_vs_beta():
    betas = np.linspace(0, 90, 400)
    alts = [400, 550, 1200]
    colors = [CYAN, BLUE, AMBER]

    fig, ax = plt.subplots(figsize=(8, 4.6))
    for alt, c in zip(alts, colors):
        f = [sunlit_fraction(alt, b) * 100 for b in betas]
        ax.plot(betas, f, color=c, lw=2.4, label=f"{alt} km")
        b_star = beta_critical_deg(alt)
        ax.axvline(b_star, color=c, ls=":", lw=1.2, alpha=0.7)

    ax.axhline(100, color=GREEN, ls="--", lw=1.0, alpha=0.6)
    ax.text(2, 101.2, "100% sunlit (no eclipse)", color=GREEN, fontsize=9)
    ax.set_xlabel("Solar beta angle |\u03b2|  (degrees)")
    ax.set_ylabel("Sunlit fraction of orbit  (%)")
    ax.set_title("Sunlit fraction rises with beta angle until eclipse vanishes")
    ax.set_xlim(0, 90)
    ax.set_ylim(55, 104)
    ax.legend(title="Altitude", facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT,
              title_fontsize=10)
    _style(ax)
    ax.annotate("dotted line = critical beta\n(eclipse disappears)",
                xy=(72, 88), color=TEXT, fontsize=8.5, ha="left",
                bbox=dict(boxstyle="round,pad=0.4", fc=NAVY, ec=GRID))
    fig.tight_layout()
    fig.savefig("docs/assets/sunlit_vs_beta.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: Eclipse minutes vs altitude at beta = 0 (worst case).
# ---------------------------------------------------------------------------
def fig_eclipse_vs_altitude():
    alts = np.linspace(300, 2000, 400)
    ecl_min = []
    period_min = []
    for a in alts:
        orbit = Orbit(altitude_km=a, inclination_deg=51.6)
        f = eclipse_fraction(a, 0.0)
        ecl_min.append(f * orbit.period_minutes())
        period_min.append(orbit.period_minutes())

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(alts, ecl_min, color=RED, lw=2.4, label="Eclipse duration (\u03b2=0)")
    ax.plot(alts, period_min, color=BLUE, lw=2.0, ls="--", label="Orbital period")
    ax.axhline(35, color=AMBER, ls=":", lw=1.2)
    ax.text(320, 36, "~35 min: published LEO max eclipse", color=AMBER, fontsize=9)
    ax.set_xlabel("Orbit altitude  (km)")
    ax.set_ylabel("Minutes")
    ax.set_title("Worst-case eclipse duration vs altitude")
    ax.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)
    _style(ax)
    fig.tight_layout()
    fig.savefig("docs/assets/eclipse_vs_altitude.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3: Beta angle over a year, and resulting eclipse fraction.
# ---------------------------------------------------------------------------
def fig_beta_over_year():
    sol_lon = np.linspace(0, 360, 400)
    # Two orbits: a mid-inclination shell and a sun-synchronous dusk-dawn.
    orbit_a = Orbit(550, 53, raan_deg=0)
    orbit_b = Orbit(550, 97.6, raan_deg=90)

    beta_a = [beta_angle_deg(53, 0, s) for s in sol_lon]
    beta_b = [beta_angle_deg(97.6, 90, s) for s in sol_lon]
    ecl_a = [eclipse_fraction(550, b) * 100 for b in beta_a]
    ecl_b = [eclipse_fraction(550, b) * 100 for b in beta_b]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True)

    ax1.plot(sol_lon, beta_a, color=BLUE, lw=2.2, label="53\u00b0 shell")
    ax1.plot(sol_lon, beta_b, color=AMBER, lw=2.2, label="97.6\u00b0 sun-sync")
    ax1.set_ylabel("Beta angle (deg)")
    ax1.set_title("Beta angle drives eclipse over the year")
    ax1.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)
    _style(ax1)

    ax2.plot(sol_lon, ecl_a, color=BLUE, lw=2.2)
    ax2.plot(sol_lon, ecl_b, color=AMBER, lw=2.2)
    ax2.set_ylabel("Eclipse fraction (%)")
    ax2.set_xlabel("Solar ecliptic longitude  (degrees over one year)")
    ax2.set_xlim(0, 360)
    _style(ax2)

    fig.tight_layout()
    fig.savefig("docs/assets/beta_over_year.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4: The core tradeoff. Battery size vs effective compute.
# ---------------------------------------------------------------------------
def fig_battery_tradeoff():
    orbit = Orbit(550, 53)
    compute_w = 1000
    array_w = 3000
    battery_range = np.linspace(0, 1400, 400)  # Wh

    eff = []
    for wh in battery_range:
        power = PowerSystem(
            compute_power_w=compute_w,
            solar_array_power_w=array_w,
            battery_capacity_wh=wh,
            battery_max_dod=0.8,
        )
        res = evaluate_orbit(orbit, power, solar_longitude_deg=0.0)
        eff.append(res.effective_compute_hours_per_day)

    # Battery needed to fully carry the eclipse.
    res_full = evaluate_orbit(
        orbit,
        PowerSystem(compute_w, array_w, 10_000, battery_max_dod=0.8),
        solar_longitude_deg=0.0,
    )
    need_wh = res_full.battery_energy_needed_wh / 0.8  # capacity incl DoD

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(battery_range, eff, color=CYAN, lw=2.6)
    ax.axvline(need_wh, color=GREEN, ls="--", lw=1.4)
    ax.text(need_wh + 15, 12, "battery sized to\ncarry full eclipse",
            color=GREEN, fontsize=9)
    ax.fill_between(battery_range, eff, 0,
                    where=(battery_range < need_wh),
                    color=RED, alpha=0.12)
    ax.set_xlabel("Battery capacity  (Wh)")
    ax.set_ylabel("Effective compute  (hours/day)")
    ax.set_title("The real cost of eclipse is battery mass, not lost compute")
    ax.set_xlim(0, 1400)
    ax.set_ylim(0, 25)
    _style(ax)
    fig.tight_layout()
    fig.savefig("docs/assets/battery_tradeoff.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_sunlit_vs_beta()
    fig_eclipse_vs_altitude()
    fig_beta_over_year()
    fig_battery_tradeoff()
    print("Figures written to docs/assets/")
