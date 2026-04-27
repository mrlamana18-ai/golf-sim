from __future__ import annotations

from functools import lru_cache
import math

from .models import Club, DerivedValues, SimulationInputs


def mph_to_mps(value: float) -> float:
    return value * 0.44704


def yards_to_meters(value: float) -> float:
    return value * 0.9144


def meters_to_yards(value: float) -> float:
    return value / 0.9144


def _simulate_carry_meters(
    ball_speed_mps: float,
    launch_angle_rad: float,
    *,
    dt: float,
    max_time_s: float,
    gravity: float,
    air_density: float,
    drag_coefficient: float,
    ball_diameter_m: float,
    ball_mass_kg: float,
    lift_coefficient: float,
) -> float:
    area_m2 = math.pi * (ball_diameter_m / 2.0) ** 2
    k_over_m = 0.5 * air_density * drag_coefficient * area_m2 / ball_mass_kg
    lift_constant = 0.5 * air_density * lift_coefficient * area_m2 / ball_mass_kg

    x = 0.0
    z = 0.0
    vx = ball_speed_mps * math.cos(launch_angle_rad)
    vz = ball_speed_mps * math.sin(launch_angle_rad)

    prev_x = 0.0
    prev_z = 0.0
    max_steps = max(2, int(max_time_s / dt))

    for _ in range(max_steps + 1):
        u = math.sqrt(vx * vx + vz * vz)
        ax = -k_over_m * u * vx
        az = -gravity - k_over_m * u * vz + lift_constant * (u * u)

        prev_x = x
        prev_z = z
        x = x + vx * dt
        z = z + vz * dt
        vx = vx + ax * dt
        vz = vz + az * dt

        if z <= 0.0 and prev_z > 0.0:
            denom = prev_z - z
            alpha = 0.0 if abs(denom) < 1e-12 else prev_z / denom
            return prev_x + alpha * (x - prev_x)

    return max(0.0, x)


@lru_cache(maxsize=512)
def _calibrated_full_ball_speed_mph(
    full_ball_speed_mph: float,
    base_launch_angle_deg: float,
    base_carry_yards: float,
    base_lift_coefficient: float,
    dt: float,
    max_time_s: float,
    gravity: float,
    air_density: float,
    drag_coefficient: float,
    ball_diameter_m: float,
    ball_mass_kg: float,
) -> float:
    target_carry_m = yards_to_meters(base_carry_yards)
    launch_angle_rad = math.radians(base_launch_angle_deg)
    baseline_speed_mps = mph_to_mps(full_ball_speed_mph)

    baseline_carry_m = _simulate_carry_meters(
        baseline_speed_mps,
        launch_angle_rad,
        dt=dt,
        max_time_s=max_time_s,
        gravity=gravity,
        air_density=air_density,
        drag_coefficient=drag_coefficient,
        ball_diameter_m=ball_diameter_m,
        ball_mass_kg=ball_mass_kg,
        lift_coefficient=base_lift_coefficient,
    )
    if baseline_carry_m <= 1e-9:
        return full_ball_speed_mph

    # Use a ratio-informed guess, then tighten with binary search.
    guess_scale = math.sqrt(max(1e-6, target_carry_m / baseline_carry_m))
    lo = max(0.35, guess_scale * 0.6)
    hi = min(2.25, guess_scale * 1.6)

    for _ in range(36):
        mid = 0.5 * (lo + hi)
        carry_m = _simulate_carry_meters(
            baseline_speed_mps * mid,
            launch_angle_rad,
            dt=dt,
            max_time_s=max_time_s,
            gravity=gravity,
            air_density=air_density,
            drag_coefficient=drag_coefficient,
            ball_diameter_m=ball_diameter_m,
            ball_mass_kg=ball_mass_kg,
            lift_coefficient=base_lift_coefficient,
        )
        if carry_m < target_carry_m:
            lo = mid
        else:
            hi = mid

    calibrated_speed_mps = baseline_speed_mps * (0.5 * (lo + hi))
    return calibrated_speed_mps / 0.44704


def compute_derived(inputs: SimulationInputs, club: Club) -> DerivedValues:
    swing_pct = max(0.0, min(1.0, inputs.swing_pct))
    actual_club_speed_mph = club.full_club_speed_mph * swing_pct
    calibrated_full_ball_speed_mph = _calibrated_full_ball_speed_mph(
        club.full_ball_speed_mph,
        club.base_launch_angle_deg,
        club.base_carry_yards,
        club.base_lift_coefficient,
        inputs.dt,
        inputs.max_time_s,
        inputs.gravity,
        inputs.air_density,
        inputs.drag_coefficient,
        inputs.ball_diameter_m,
        inputs.ball_mass_kg,
    )
    ball_speed_mph = calibrated_full_ball_speed_mph * swing_pct
    ball_speed_mps = mph_to_mps(ball_speed_mph)

    launch_angle_deg = club.base_launch_angle_deg
    launch_angle_rad = math.radians(launch_angle_deg)
    shot_direction_rad = math.radians(inputs.shot_direction_deg)
    hole_direction_rad = math.radians(inputs.hole_direction_deg)

    hole_distance_m = yards_to_meters(inputs.hole_distance_yards)
    wind_speed_mps = mph_to_mps(inputs.wind_speed_mph)

    wind_x_mps = wind_speed_mps * math.cos(math.radians(inputs.wind_direction_deg))
    wind_y_mps = wind_speed_mps * math.sin(math.radians(inputs.wind_direction_deg))

    hole_x_m = hole_distance_m * math.cos(hole_direction_rad)
    hole_y_m = hole_distance_m * math.sin(hole_direction_rad)

    area_m2 = math.pi * (inputs.ball_diameter_m / 2.0) ** 2
    drag_constant = 0.5 * inputs.air_density * inputs.drag_coefficient * area_m2
    lift_constant = 0.5 * inputs.air_density * club.base_lift_coefficient * area_m2 / inputs.ball_mass_kg

    return DerivedValues(
        hole_distance_m=hole_distance_m,
        wind_speed_mps=wind_speed_mps,
        ball_speed_mps=ball_speed_mps,
        ball_speed_mph=ball_speed_mph,
        launch_angle_deg=launch_angle_deg,
        launch_angle_rad=launch_angle_rad,
        shot_direction_rad=shot_direction_rad,
        hole_direction_rad=hole_direction_rad,
        wind_x_mps=wind_x_mps,
        wind_y_mps=wind_y_mps,
        hole_x_m=hole_x_m,
        hole_y_m=hole_y_m,
        area_m2=area_m2,
        drag_constant=drag_constant,
        lift_constant=lift_constant,
        full_club_speed_mph=club.full_club_speed_mph,
        actual_club_speed_mph=actual_club_speed_mph,
        smash_factor=club.smash_factor,
        spin_rate_rpm=club.base_spin_rate_rpm,
        lift_coefficient=club.base_lift_coefficient,
        club=club,
    )
