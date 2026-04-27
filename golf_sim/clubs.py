from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from .models import Club


DATA_PATH = Path(__file__).resolve().parent / "data" / "clubs.csv"


def load_clubs() -> List[Club]:
    clubs: List[Club] = []
    with DATA_PATH.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clubs.append(
                Club(
                    name=row["club"],
                    loft_deg=float(row["loft_deg"]),
                    full_ball_speed_mph=float(row["full_ball_speed_mph"]),
                    full_club_speed_mph=float(row["full_club_speed_mph"]),
                    smash_factor=float(row["smash_factor"]),
                    base_launch_angle_deg=float(row["base_launch_angle_deg"]),
                    base_spin_rate_rpm=float(row["base_spin_rate_rpm"]),
                    base_carry_yards=float(row["base_carry_yards"]),
                    base_lift_coefficient=float(row["base_lift_coefficient"]),
                )
            )
    return clubs


def clubs_by_name() -> Dict[str, Club]:
    return {club.name: club for club in load_clubs()}
