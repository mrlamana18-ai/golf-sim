from __future__ import annotations

from golf_sim.clubs import clubs_by_name
from golf_sim.models import SimulationInputs
from golf_sim.physics import compute_derived
from golf_sim.simulation import run_simulation
from golf_sim.plotting import make_3d_figure

import matplotlib.pyplot as plt


def main() -> None:
    clubs = clubs_by_name()
    inputs = SimulationInputs(
        club_name="7 Iron",
        swing_pct=0.9583,
        hole_distance_yards=164.0415,
        hole_direction_deg=0.0,
        shot_direction_deg=0.0,
        wind_speed_mph=10.0,
        wind_direction_deg=90.0,
    )
    derived = compute_derived(inputs, clubs[inputs.club_name])
    result = run_simulation(inputs, derived)

    print("Golf simulation result")
    print(f"Club: {inputs.club_name}")
    print(f"Swing %: {inputs.swing_pct * 100:.2f}%")
    print(f"Ball speed: {derived.ball_speed_mph:.2f} mph")
    print(f"Launch angle: {derived.launch_angle_deg:.2f} deg")
    print(f"Carry: {result.carry_m:.2f} m ({result.carry_yards:.2f} yd)")
    print(f"Landing X: {result.landing_x_m:.2f} m")
    print(f"Landing Y: {result.landing_y_m:.2f} m")
    print(f"Long/Short: {result.long_short_m:.2f} m")
    print(f"Left/Right: {result.left_right_m:.2f} m")
    print(f"Miss distance: {result.miss_distance_m:.2f} m")
    print("Outcome:", "HOLE IN ONE" if result.hole_in_one else "MISSED")

    fig = make_3d_figure(result)
    plt.show()


if __name__ == "__main__":
    main()
