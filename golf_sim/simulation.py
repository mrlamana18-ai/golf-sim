from __future__ import annotations

import math
from typing import List

from .models import DerivedValues, SimulationInputs, SimulationResult, TrajectoryPoint
from .physics import meters_to_yards


def run_simulation(inputs: SimulationInputs, derived: DerivedValues) -> SimulationResult:
    dt = inputs.dt
    max_steps = max(2, int(inputs.max_time_s / dt))
    k_over_m = derived.drag_constant / inputs.ball_mass_kg

    x = 0.0
    y = 0.0
    z = 0.0

    vx = (
        derived.ball_speed_mps
        * math.cos(derived.launch_angle_rad)
        * math.cos(derived.shot_direction_rad)
    )
    vy = (
        derived.ball_speed_mps
        * math.cos(derived.launch_angle_rad)
        * math.sin(derived.shot_direction_rad)
    )
    vz = derived.ball_speed_mps * math.sin(derived.launch_angle_rad)

    points: List[TrajectoryPoint] = []
    prev_x = prev_y = prev_z = 0.0
    prev_t = 0.0

    landing_x = 0.0
    landing_y = 0.0
    flight_time = 0.0
    apex = 0.0
    crossed = False

    for step in range(max_steps + 1):
        t = step * dt

        ux = vx - derived.wind_x_mps
        uy = vy - derived.wind_y_mps
        uz = vz
        u = math.sqrt(ux * ux + uy * uy + uz * uz)

        ax = -k_over_m * u * ux
        ay = -k_over_m * u * uy
        az = -inputs.gravity - k_over_m * u * uz + derived.lift_constant * (u * u)

        apex = max(apex, z)

        if step > 0 and z <= 0.0:
            denom = prev_z - z
            alpha = 0.0 if abs(denom) < 1e-12 else prev_z / denom

            landing_x = prev_x + alpha * (x - prev_x)
            landing_y = prev_y + alpha * (y - prev_y)
            flight_time = prev_t + alpha * (t - prev_t)

            points.append(
                TrajectoryPoint(
                    t=flight_time,
                    x=landing_x,
                    y=landing_y,
                    z=0.0,
                    vx=vx,
                    vy=vy,
                    vz=vz,
                    ux=ux,
                    uy=uy,
                    uz=uz,
                    u=u,
                    ax=ax,
                    ay=ay,
                    az=az,
                )
            )

            crossed = True
            break

        points.append(
            TrajectoryPoint(
                t=t,
                x=x,
                y=y,
                z=z,
                vx=vx,
                vy=vy,
                vz=vz,
                ux=ux,
                uy=uy,
                uz=uz,
                u=u,
                ax=ax,
                ay=ay,
                az=az,
            )
        )

        prev_x, prev_y, prev_z, prev_t = x, y, z, t

        x = x + vx * dt
        y = y + vy * dt
        z = z + vz * dt

        vx = vx + ax * dt
        vy = vy + ay * dt
        vz = vz + az * dt

    if not crossed:
        landing_x = x
        landing_y = y
        flight_time = max_steps * dt

    carry_m = math.sqrt(landing_x**2 + landing_y**2)
    carry_yards = meters_to_yards(carry_m)

    dx = landing_x - derived.hole_x_m
    dy = landing_y - derived.hole_y_m

    theta = derived.hole_direction_rad
    long_short = dx * math.cos(theta) + dy * math.sin(theta)
    left_right = -dx * math.sin(theta) + dy * math.cos(theta)
    miss_distance = math.sqrt(long_short**2 + left_right**2)

    return SimulationResult(
        points=points,
        landing_x_m=landing_x,
        landing_y_m=landing_y,
        carry_m=carry_m,
        carry_yards=carry_yards,
        long_short_m=long_short,
        left_right_m=left_right,
        miss_distance_m=miss_distance,
        hole_in_one=miss_distance <= inputs.cup_tolerance_m,
        flight_time_s=flight_time,
        apex_m=apex,
        derived=derived,
    )