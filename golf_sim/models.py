from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Club:
    name: str
    loft_deg: float
    full_ball_speed_mph: float
    full_club_speed_mph: float
    smash_factor: float
    base_launch_angle_deg: float
    base_spin_rate_rpm: float
    base_carry_yards: float
    base_lift_coefficient: float


@dataclass(frozen=True)
class SimulationInputs:
    club_name: str
    swing_pct: float  # 0 to 1
    hole_distance_yards: float
    hole_direction_deg: float
    shot_direction_deg: float
    wind_speed_mph: float
    wind_direction_deg: float
    dt: float = 0.02
    cup_tolerance_m: float = 0.10
    gravity: float = 9.81
    ball_mass_kg: float = 0.04593
    air_density: float = 1.225
    drag_coefficient: float = 0.25
    ball_diameter_m: float = 0.04267
    max_time_s: float = 12.0


@dataclass(frozen=True)
class DerivedValues:
    hole_distance_m: float
    wind_speed_mps: float
    ball_speed_mps: float
    ball_speed_mph: float
    launch_angle_deg: float
    launch_angle_rad: float
    shot_direction_rad: float
    hole_direction_rad: float
    wind_x_mps: float
    wind_y_mps: float
    hole_x_m: float
    hole_y_m: float
    area_m2: float
    drag_constant: float
    lift_constant: float
    full_club_speed_mph: float
    actual_club_speed_mph: float
    smash_factor: float
    spin_rate_rpm: float
    lift_coefficient: float
    club: Club


@dataclass(frozen=True)
class TrajectoryPoint:
    t: float
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    ux: float
    uy: float
    uz: float
    u: float
    ax: float
    ay: float
    az: float


@dataclass(frozen=True)
class SimulationResult:
    points: List[TrajectoryPoint]
    landing_x_m: float
    landing_y_m: float
    carry_m: float
    carry_yards: float
    long_short_m: float
    left_right_m: float
    miss_distance_m: float
    hole_in_one: bool
    flight_time_s: float
    apex_m: float
    derived: DerivedValues
