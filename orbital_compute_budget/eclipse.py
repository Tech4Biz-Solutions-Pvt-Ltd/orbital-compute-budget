"""
Eclipse fraction and beta-angle physics for circular LEO orbits.

All equations are standard, published spacecraft-power results:

  - Beta angle:        angle between the orbit plane and the Sun vector.
  - Eclipse fraction:  fraction of one orbit spent in Earth's shadow,
                       using the cylindrical-shadow approximation.

References
----------
Vallado, D. A., "Fundamentals of Astrodynamics and Applications".
Wikipedia, "Beta angle" (LEO min sunlit fraction ~59% at beta=0).
NASA SSRI, "Preliminary Thermal Analysis of Small Satellites".
The cylindrical-shadow eclipse formula matches these to within
the approximation's known bounds (umbra/penumbra cones ignored).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Physical constants
R_EARTH_KM = 6378.137          # Earth equatorial radius (WGS-84), km
MU_EARTH = 398600.4418         # Earth gravitational parameter, km^3/s^2
OBLIQUITY_DEG = 23.45          # Earth's axial tilt (ecliptic obliquity)


@dataclass(frozen=True)
class Orbit:
    """A circular Earth orbit."""
    altitude_km: float
    inclination_deg: float
    raan_deg: float = 0.0        # right ascension of ascending node

    @property
    def semi_major_axis_km(self) -> float:
        return R_EARTH_KM + self.altitude_km

    def period_seconds(self) -> float:
        """Orbital period from Kepler's third law (circular orbit)."""
        a = self.semi_major_axis_km
        return 2.0 * math.pi * math.sqrt(a ** 3 / MU_EARTH)

    def period_minutes(self) -> float:
        return self.period_seconds() / 60.0


def beta_angle_deg(
    inclination_deg: float,
    raan_deg: float,
    solar_longitude_deg: float,
    obliquity_deg: float = OBLIQUITY_DEG,
) -> float:
    """
    Solar beta angle (degrees).

    beta = arcsin[ cos(Gamma) sin(Omega) sin(i)
                 - sin(Gamma) cos(eps) cos(Omega) sin(i)
                 + sin(Gamma) sin(eps) cos(i) ]

    where Gamma = solar ecliptic longitude, Omega = RAAN,
    i = inclination, eps = obliquity of the ecliptic.

    This is the standard formulation used in spacecraft power/thermal
    analysis. beta ranges over +/-90 deg; its magnitude sets how much
    of the orbit can be shadowed.
    """
    i = math.radians(inclination_deg)
    omega = math.radians(raan_deg)
    gamma = math.radians(solar_longitude_deg)
    eps = math.radians(obliquity_deg)

    sin_beta = (
        math.cos(gamma) * math.sin(omega) * math.sin(i)
        - math.sin(gamma) * math.cos(eps) * math.cos(omega) * math.sin(i)
        + math.sin(gamma) * math.sin(eps) * math.cos(i)
    )
    # Clamp for numerical safety before arcsin.
    sin_beta = max(-1.0, min(1.0, sin_beta))
    return math.degrees(math.asin(sin_beta))


def beta_critical_deg(altitude_km: float) -> float:
    """
    Critical beta angle above which the orbit has NO eclipse.

    beta* = arcsin( R_earth / (R_earth + h) )

    For |beta| >= beta*, the Sun never passes behind the Earth as seen
    from the satellite, so the orbit is fully sunlit.
    """
    ratio = R_EARTH_KM / (R_EARTH_KM + altitude_km)
    return math.degrees(math.asin(ratio))


def eclipse_fraction(altitude_km: float, beta_deg: float) -> float:
    """
    Fraction of one circular orbit spent in eclipse (0..1),
    cylindrical-shadow approximation.

    f_E = (1 / 180) * arccos( sqrt(h^2 + 2 R h) / ((R + h) cos beta) )   [deg form]

    Returns 0.0 when |beta| >= beta_critical (no eclipse).

    The term under the square root is the projected shadow half-chord;
    dividing by (R+h)cos(beta) and taking arccos gives the shadow
    half-angle as a fraction of a half-orbit.
    """
    beta = math.radians(beta_deg)
    R = R_EARTH_KM
    h = altitude_km

    beta_star = beta_critical_deg(altitude_km)
    if abs(beta_deg) >= beta_star:
        return 0.0

    numerator = math.sqrt(h ** 2 + 2.0 * R * h)
    denominator = (R + h) * math.cos(beta)
    arg = numerator / denominator
    arg = max(-1.0, min(1.0, arg))  # numerical safety

    # arccos(arg) is the shadow half-angle in radians; divide by pi to
    # express as a fraction of the full orbit (2*half-angle / 2*pi).
    return math.acos(arg) / math.pi


def sunlit_fraction(altitude_km: float, beta_deg: float) -> float:
    """Fraction of one orbit in sunlight (1 - eclipse fraction)."""
    return 1.0 - eclipse_fraction(altitude_km, beta_deg)


def eclipse_minutes(orbit: Orbit, beta_deg: float) -> float:
    """Eclipse duration per orbit, in minutes, for a given beta angle."""
    return eclipse_fraction(orbit.altitude_km, beta_deg) * orbit.period_minutes()
