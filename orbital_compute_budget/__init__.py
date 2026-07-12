"""
orbital-compute-budget
=======================

Estimate the effective compute you actually get from a data center in
low Earth orbit, after eclipse periods and battery limits.

Core eclipse/beta-angle physics is exact and citable. Power-system
parameters (solar array, battery, depth-of-discharge) are transparent,
tunable inputs.

Copyright (c) 2026 Tech4Biz Solutions. Licensed under the MIT License.
Maintained by Tech4Biz Solutions.
"""

from .eclipse import (
    Orbit,
    beta_angle_deg,
    beta_critical_deg,
    eclipse_fraction,
    sunlit_fraction,
    eclipse_minutes,
)
from .budget import PowerSystem, OrbitComputeResult, evaluate_orbit

__version__ = "0.1.0"
__author__ = "Tech4Biz Solutions"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2026 Tech4Biz Solutions"

__all__ = [
    "Orbit",
    "beta_angle_deg",
    "beta_critical_deg",
    "eclipse_fraction",
    "sunlit_fraction",
    "eclipse_minutes",
    "PowerSystem",
    "OrbitComputeResult",
    "evaluate_orbit",
]
