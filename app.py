from __future__ import annotations

import numpy as np
import streamlit as st


def _evaluate_shot(base_inputs, club, swing, direction):
    test_inputs = SimulationInputs(
        club_name=base_inputs.club_name,
        swing_pct=swing,
        hole_distance_yards=base_inputs.hole_distance_yards,
        hole_direction_deg=base_inputs.hole_direction_deg,
        shot_direction_deg=direction,
        wind_speed_mph=base_inputs.wind_speed_mph,
        wind_direction_deg=base_inputs.wind_direction_deg,
        dt=base_inputs.dt,
        cup_tolerance_m=base_inputs.cup_tolerance_m,
    )
    derived = compute_derived(test_inputs, club)
    result = run_simulation(test_inputs, derived)
    return test_inputs, result


def _search_grid(base_inputs, club, swing_values, direction_values, best_error, best_inputs, best_result):
    for swing in swing_values:
        for direction in direction_values:
            candidate_inputs, candidate_result = _evaluate_shot(base_inputs, club, swing, direction)
            error = candidate_result.miss_distance_m
            if error < best_error:
                best_error = error
                best_inputs = candidate_inputs
                best_result = candidate_result
                if best_result.hole_in_one:
                    return best_error, best_inputs, best_result
    return best_error, best_inputs, best_result


def find_best_shot(base_inputs, club):
    best_error = float("inf")
    best_inputs = None
    best_result = None

    direction_center = base_inputs.hole_direction_deg

    # Coarse pass over a broad area.
    best_error, best_inputs, best_result = _search_grid(
        base_inputs,
        club,
        swing_values=np.arange(0.10, 1.0001, 0.01),
        direction_values=np.arange(direction_center - 30.0, direction_center + 30.0001, 0.5),
        best_error=best_error,
        best_inputs=best_inputs,
        best_result=best_result,
    )
    if best_result is not None and best_result.hole_in_one:
        return best_inputs, best_result

    # Refinement passes around the current best point.
    if best_inputs is None:
        return None, None

    refinement_passes = [
        (0.08, 0.0025, 4.0, 0.10),
        (0.02, 0.0005, 1.0, 0.02),
    ]
    for swing_window, swing_step, dir_window, dir_step in refinement_passes:
        s0 = max(0.01, best_inputs.swing_pct - swing_window)
        s1 = min(1.00, best_inputs.swing_pct + swing_window)
        d0 = max(-45.0, best_inputs.shot_direction_deg - dir_window)
        d1 = min(45.0, best_inputs.shot_direction_deg + dir_window)
        best_error, best_inputs, best_result = _search_grid(
            base_inputs,
            club,
            swing_values=np.arange(s0, s1 + swing_step * 0.5, swing_step),
            direction_values=np.arange(d0, d1 + dir_step * 0.5, dir_step),
            best_error=best_error,
            best_inputs=best_inputs,
            best_result=best_result,
        )
        if best_result is not None and best_result.hole_in_one:
            return best_inputs, best_result

    return best_inputs, best_result

from golf_sim.clubs import clubs_by_name
from golf_sim.models import SimulationInputs
from golf_sim.physics import compute_derived
from golf_sim.simulation import run_simulation
from golf_sim.plotting import make_3d_figure, make_topdown_figure, make_golf_animation_html
import streamlit.components.v1 as components


st.set_page_config(page_title="Golf Hole-in-One Simulator", layout="wide")
st.title("Golf Hole-in-One Simulator")
st.caption("3D Euler-method golf ball flight simulation with club, swing, wind, and target direction.")

if "best_shot_locked" not in st.session_state:
    st.session_state.best_shot_locked = False
if "best_shot_summary" not in st.session_state:
    st.session_state.best_shot_summary = None
if "pending_best_shot" not in st.session_state:
    st.session_state.pending_best_shot = None

# Apply optimized values before widget creation to avoid Streamlit state mutation errors.
if st.session_state.pending_best_shot is not None:
    p = st.session_state.pending_best_shot
    st.session_state.swing_pct_input = p["swing_pct"]
    st.session_state.aim_at_hole_input = False
    st.session_state.shot_direction_input = p["shot_direction_deg"]
    st.session_state.best_shot_locked = True
    st.session_state.best_shot_summary = {
        "swing_pct": p["swing_pct"],
        "shot_direction_deg": p["shot_direction_deg"],
        "miss_distance_m": p["miss_distance_m"],
        "hole_in_one": p["hole_in_one"],
    }
    st.session_state.pending_best_shot = None

clubs = clubs_by_name()
club_names = list(clubs.keys())

# Apply shot controls coming from the in-visual control panel.
qp = st.query_params
qp_changed = False
if "club" in qp:
    q_club = qp.get("club")
    if q_club in club_names:
        st.session_state.club_name_input = q_club
    qp_changed = True
if "swing" in qp:
    try:
        q_swing = float(qp.get("swing"))
        st.session_state.swing_pct_input = max(1.0, min(100.0, q_swing))
    except (TypeError, ValueError):
        pass
    qp_changed = True
if "dir" in qp:
    try:
        q_dir = float(qp.get("dir"))
        st.session_state.aim_at_hole_input = False
        st.session_state.shot_direction_input = max(-45.0, min(45.0, q_dir))
    except (TypeError, ValueError):
        pass
    qp_changed = True
if qp_changed:
    for key in ("club", "swing", "dir"):
        if key in qp:
            del qp[key]

with st.sidebar:
    st.header("Inputs")
    club_name = st.selectbox(
        "Club",
        club_names,
        index=club_names.index("7 Iron") if "7 Iron" in club_names else 0,
        key="club_name_input",
    )
    swing_pct = st.number_input(
        "Swing percentage (%)",
        min_value=1.00,
        max_value=100.00,
        value=96.00,
        step=0.01,
        format="%.2f",
        key="swing_pct_input",
    ) / 100.0
    hole_distance_m = st.number_input(
        "Hole distance (meters)",
        min_value=45.72,
        max_value=320.04,
        value=150.0,
        step=1.0,
        key="hole_distance_m_input",
    )
    wind_speed_mph = st.number_input("Wind speed (mph)", min_value=0.0, max_value=50.0, value=0.0, step=1.0, key="wind_speed_input")
    wind_direction_deg = st.slider("Wind direction (deg)", -180, 180, 0, key="wind_direction_input")
    hole_direction_deg = st.slider("Hole direction (deg)", -45, 45, 0, key="hole_direction_input")
    aim_at_hole = st.checkbox("Aim at hole", value=True, key="aim_at_hole_input")
    shot_direction_deg = hole_direction_deg if aim_at_hole else st.slider("Shot direction (deg)", -45, 45, 0, key="shot_direction_input")
    cup_tolerance_m = st.number_input("Hole-in-one tolerance (m)", min_value=0.01, max_value=0.20, value=0.10, step=0.01, key="cup_tolerance_input")
    dt = st.number_input("Time step dt (s)", min_value=0.005, max_value=0.1, value=0.02, step=0.005, format="%.3f", key="dt_input")
    optimize = st.button("Find Hole-in-One Shot 🎯")

    if st.session_state.best_shot_locked and st.session_state.best_shot_summary is not None:
        s = st.session_state.best_shot_summary
        st.markdown(
            f"""
            <div style="background:#e8f5e9;border:1px solid #66bb6a;border-radius:8px;padding:10px;margin-top:8px;">
              <div style="color:#1b5e20;font-weight:700;">Best Shot Locked</div>
              <div style="color:#2e7d32;font-size:0.92rem;">Swing: {s['swing_pct']:.2f}%</div>
              <div style="color:#2e7d32;font-size:0.92rem;">Direction: {s['shot_direction_deg']:.2f}°</div>
              <div style="color:#2e7d32;font-size:0.92rem;">Miss: {s['miss_distance_m']:.3f} m</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Unlock Best Shot"):
            st.session_state.best_shot_locked = False
            st.session_state.best_shot_summary = None
            st.rerun()

inputs = SimulationInputs(
    club_name=club_name,
    swing_pct=swing_pct,
    hole_distance_yards=hole_distance_m / 0.9144,
    hole_direction_deg=hole_direction_deg,
    shot_direction_deg=shot_direction_deg,
    wind_speed_mph=wind_speed_mph,
    wind_direction_deg=wind_direction_deg,
    dt=dt,
    cup_tolerance_m=cup_tolerance_m,
    
)

club = clubs[club_name]
derived = compute_derived(inputs, club)
result = run_simulation(inputs, derived)

if optimize:
    best_inputs, best_result = find_best_shot(inputs, club)
    if best_inputs is not None and best_result is not None:
        st.session_state.pending_best_shot = {
            "swing_pct": round(best_inputs.swing_pct * 100.0, 2),
            "shot_direction_deg": round(best_inputs.shot_direction_deg, 2),
            "miss_distance_m": round(best_result.miss_distance_m, 3),
            "hole_in_one": bool(best_result.hole_in_one),
        }
        st.rerun()

if st.session_state.best_shot_locked and st.session_state.best_shot_summary is not None:
    inputs = SimulationInputs(
        club_name=st.session_state.club_name_input,
        swing_pct=st.session_state.swing_pct_input / 100.0,
        hole_distance_yards=st.session_state.hole_distance_m_input / 0.9144,
        hole_direction_deg=st.session_state.hole_direction_input,
        shot_direction_deg=st.session_state.shot_direction_input,
        wind_speed_mph=st.session_state.wind_speed_input,
        wind_direction_deg=st.session_state.wind_direction_input,
        dt=st.session_state.dt_input,
        cup_tolerance_m=st.session_state.cup_tolerance_input,
    )
    club = clubs[inputs.club_name]
    derived = compute_derived(inputs, club)
    result = run_simulation(inputs, derived)

    if result.hole_in_one:
        st.success("Hole-in-one shot found 🎯")
    else:
        st.warning("Closest shot found (outside hole-in-one tolerance).")
    st.write(f"Swing %: {inputs.swing_pct*100:.2f}%")
    st.write(f"Shot Direction: {inputs.shot_direction_deg:.2f}°")
    st.write(f"Miss Distance: {result.miss_distance_m:.3f} m")

derived = compute_derived(inputs, club)
result = run_simulation(inputs, derived)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ball speed", f"{derived.ball_speed_mph:.2f} mph")
c2.metric("Launch angle", f"{derived.launch_angle_deg:.2f}°")
c3.metric("Carry", f"{result.carry_m:.2f} m", f"{result.carry_yards:.2f} yd")
c4.metric("Outcome", "HOLE IN ONE" if result.hole_in_one else "MISSED")

st.subheader("Shot results")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Landing X", f"{result.landing_x_m:.2f} m")
r2.metric("Landing Y", f"{result.landing_y_m:.2f} m")
r3.metric("Long / Short", f"{abs(result.long_short_m):.2f} m", "On distance" if abs(result.long_short_m) <= cup_tolerance_m else ("Long" if result.long_short_m > 0 else "Short"))
r4.metric("Left / Right", f"{abs(result.left_right_m):.2f} m", "On line" if abs(result.left_right_m) <= cup_tolerance_m else ("Right" if result.left_right_m > 0 else "Left"))

st.write(
    {
        "full_club_speed_mph": round(derived.full_club_speed_mph, 3),
        "actual_club_speed_mph": round(derived.actual_club_speed_mph, 3),
        "smash_factor": round(derived.smash_factor, 3),
        "spin_rate_rpm": round(derived.spin_rate_rpm, 1),
        "lift_coefficient": round(derived.lift_coefficient, 5),
        "wind_x_mps": round(derived.wind_x_mps, 5),
        "wind_y_mps": round(derived.wind_y_mps, 5),
        "hole_x_m": round(derived.hole_x_m, 5),
        "hole_y_m": round(derived.hole_y_m, 5),
        "miss_distance_m": round(result.miss_distance_m, 5),
        "flight_time_s": round(result.flight_time_s, 3),
        "apex_m": round(result.apex_m, 3),
    }
)

st.subheader("Shot animation")
components.html(make_golf_animation_html(result), height=760)

col_plot1, col_plot2 = st.columns(2)
with col_plot1:
    st.pyplot(make_3d_figure(result), clear_figure=True)
with col_plot2:
    st.pyplot(make_topdown_figure(result), clear_figure=True)

with st.expander("Trajectory table"):
    st.dataframe([
        {
            "t": p.t,
            "x": p.x,
            "y": p.y,
            "z": p.z,
            "vx": p.vx,
            "vy": p.vy,
            "vz": p.vz,
            "u": p.u,
            "ax": p.ax,
            "ay": p.ay,
            "az": p.az,
        }
        for p in result.points
    ])
