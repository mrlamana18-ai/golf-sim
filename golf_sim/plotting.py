from __future__ import annotations

import json
import math
import os
from typing import Optional

# Avoid matplotlib cache permission issues in restricted environments.
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from .models import SimulationResult


def make_3d_figure(result: SimulationResult) -> Figure:
    xs = [p.x for p in result.points]
    ys = [p.y for p in result.points]
    zs = [p.z for p in result.points]

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(xs, ys, zs, label="Ball flight")
    ax.scatter([0], [0], [0], s=50, marker="o", label="Tee")
    ax.scatter([result.derived.hole_x_m], [result.derived.hole_y_m], [0], s=70, marker="^", label="Hole")
    ax.scatter([result.landing_x_m], [result.landing_y_m], [0], s=60, marker="x", label="Landing")

    # simple wind arrow on ground plane
    wx = result.derived.wind_x_mps
    wy = result.derived.wind_y_mps
    if abs(wx) > 1e-9 or abs(wy) > 1e-9:
        scale = 5.0
        ax.quiver(0, 0, 0, wx * scale, wy * scale, 0, length=1.0, normalize=False)

    ax.set_xlabel("X (forward, m)")
    ax.set_ylabel("Y (sideways, m)")
    ax.set_zlabel("Z (height, m)")
    ax.set_title("3D Golf Ball Trajectory")
    ax.legend(loc="best")

    max_x = max(xs + [result.derived.hole_x_m, result.landing_x_m, 1.0])
    max_y = max(abs(v) for v in ys + [result.derived.hole_y_m, result.landing_y_m, 1.0])
    max_z = max(zs + [1.0])
    ax.set_xlim(0, max_x * 1.05)
    ax.set_ylim(-max_y * 1.1, max_y * 1.1)
    ax.set_zlim(0, max_z * 1.1)
    return fig


def make_golf_animation_html(result: SimulationResult) -> str:
    """Return an HTML string with a 3D Trackman-style canvas animation."""
    pts = result.points
    if not pts:
        return "<div>No trajectory points available for animation.</div>"

    n_sample = min(220, len(pts))
    indices = [int(i * (len(pts) - 1) / max(n_sample - 1, 1)) for i in range(n_sample)]
    traj = [[round(pts[i].x, 3), round(pts[i].y, 3), round(pts[i].z, 3)] for i in indices]

    hole_x = round(result.derived.hole_x_m, 3)
    hole_y = round(result.derived.hole_y_m, 3)
    landing_x = round(result.landing_x_m, 3)
    landing_y = round(result.landing_y_m, 3)
    long_short = round(result.long_short_m, 3)
    left_right = round(result.left_right_m, 3)
    miss = round(result.miss_distance_m, 3)
    carry_yds = round(result.carry_yards, 1)
    apex_m = round(result.apex_m, 2)
    apex_ft = round(result.apex_m * 3.28084, 1)
    club_name = result.derived.club.name
    swing_pct = (
        0.0
        if abs(result.derived.full_club_speed_mph) < 1e-9
        else round((result.derived.actual_club_speed_mph / result.derived.full_club_speed_mph) * 100.0, 2)
    )
    shot_direction_deg = round(math.degrees(result.derived.shot_direction_rad), 2)
    ball_speed_mph = round(result.derived.ball_speed_mph, 1)
    wind_speed_mph = round(result.derived.wind_speed_mps * 2.2369362921, 1)
    wind_direction_deg = round(math.degrees(math.atan2(result.derived.wind_y_mps, result.derived.wind_x_mps)), 2)
    club_options_json = json.dumps(
        ["Driver", "3 Wood", "5 Wood", "3 Iron", "4 Iron", "5 Iron", "6 Iron", "7 Iron", "8 Iron", "9 Iron", "PW"]
    )
    hole_in_one_js = "true" if result.hole_in_one else "false"
    traj_json = json.dumps(traj)
    club_name_json = json.dumps(club_name)

    return f"""
<div style="position:relative;background:#0a1422;padding:16px;border-radius:14px;font-family:sans-serif;">
  <canvas id="golfCanvas3d" width="1100" height="620"
    style="display:block;margin:auto;border-radius:12px;background:#0b1f34;"></canvas>
  <div id="shotControlBox3d" style="position:absolute;right:28px;bottom:92px;width:250px;
      background:rgba(12,18,28,0.92);border:2px solid rgba(87,120,180,0.85);border-radius:8px;
      color:#e7eef6;padding:10px 12px;font-size:12px;">
    <div style="font-weight:700;margin-bottom:8px;">Shot Controls</div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
      <span>Club</span><span id="clubValue3d" style="font-weight:700;"></span>
    </div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
      <span>Swing %</span><span id="swingValue3d" style="font-weight:700;"></span>
    </div>
    <div style="display:flex;align-items:center;justify-content:space-between;">
      <span>Shot Dir (deg)</span><span id="dirValue3d" style="font-weight:700;"></span>
    </div>
  </div>
  <div id="windCompassWrap3d" style="position:absolute;left:26px;top:24px;width:210px;height:210px;
      background:rgba(12,18,28,0.90);border:2px solid rgba(120,140,170,0.75);border-radius:10px;padding:8px;">
    <canvas id="windCompass3d" width="194" height="170" style="display:block;margin:0 auto;"></canvas>
    <div style="text-align:center;color:#dce6f2;font-size:12px;">
      Wind: <span id="windSpeedText3d" style="font-weight:700;"></span> mph
      <span style="margin-left:8px;">Dir: <span id="windDirText3d" style="font-weight:700;"></span>°</span>
    </div>
  </div>
  <div style="text-align:center;margin-top:10px;">
    <button id="hitBallBtn3d"
      style="background:#2e7d32;color:#fff;border:none;padding:10px 28px;
             border-radius:22px;font-size:15px;cursor:pointer;font-weight:700;">
      Hit Ball
    </button>
  </div>
</div>
<script>
(function() {{
  const canvas = document.getElementById('golfCanvas3d');
  const ctx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;
  const btn = document.getElementById('hitBallBtn3d');
  const clubValue = document.getElementById('clubValue3d');
  const swingValue = document.getElementById('swingValue3d');
  const dirValue = document.getElementById('dirValue3d');
  const windCompass = document.getElementById('windCompass3d');
  const wctx = windCompass.getContext('2d');
  const windSpeedText = document.getElementById('windSpeedText3d');
  const windDirText = document.getElementById('windDirText3d');

  const traj = {traj_json};
  const hole = {{ x: {hole_x}, y: {hole_y}, z: 0 }};
  const landing = {{ x: {landing_x}, y: {landing_y}, z: 0 }};
  const holeInOne = {hole_in_one_js};
  const carryYds = {carry_yds};
  const apexM = {apex_m};
  const apexFt = {apex_ft};
  const missLongShort = {long_short};
  const missLeftRight = {left_right};
  const missDistance = {miss};
  const clubOptions = {club_options_json};
  const uiClubName = {club_name_json};
  const uiSwingPct = {swing_pct};
  const uiShotDir = {shot_direction_deg};
  const windSpeedMph = {wind_speed_mph};
  const windDirDeg = {wind_direction_deg};
  const ballSpeedMph = {ball_speed_mph};

  const SWING_FRAMES = 42;
  const IMPACT_FRAME = 28;
  const FLIGHT_FRAMES = Math.max(2, traj.length);
  const FLIGHT_STEP = 2;
  const HOLD_FRAMES = 40;
  const focal = 760;

  let phase = 'ready'; // ready -> swing -> flight -> hold
  let swingFrame = 0;
  let flightFrame = 0;
  let holdFrame = 0;
  let animId = null;
  const camX = -20;
  const camY = 0;
  const camZ = 3.2;

  function clamp(v, lo, hi) {{ return Math.max(lo, Math.min(hi, v)); }}

  function project(x, y, z) {{
    const xc = y - camY;
    const yc = z - camZ;
    const zc = x - camX;
    if (zc <= 1.5) return null;
    const sx = W * 0.5 + (xc * focal) / zc;
    const sy = H * 0.74 - (yc * focal) / zc;
    return {{ x: sx, y: sy, zc }};
  }}

  function getSwingAngles(f) {{
    const KF = [
      [0,   1.35,  2.10],
      [20, -1.70, -2.60],
      [28,  1.35,  2.20],
      [42, -0.40, -1.20],
    ];
    for (let i = 0; i < KF.length - 1; i++) {{
      const [f0, a0, c0] = KF[i];
      const [f1, a1, c1] = KF[i + 1];
      if (f <= f1) {{
        const raw = (f - f0) / (f1 - f0);
        const t = clamp(raw, 0, 1);
        return [a0 + (a1 - a0) * t, c0 + (c1 - c0) * t];
      }}
    }}
    return [KF[KF.length - 1][1], KF[KF.length - 1][2]];
  }}

  function drawBackground() {{
    const sky = ctx.createLinearGradient(0, 0, 0, H * 0.7);
    sky.addColorStop(0, '#8b95ad');
    sky.addColorStop(1, '#6d7893');
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, H);

    const ground = ctx.createLinearGradient(0, H * 0.44, 0, H);
    ground.addColorStop(0, '#9e9967');
    ground.addColorStop(1, '#6f7a47');
    ctx.fillStyle = ground;
    // Organic ground silhouette instead of a hard rectangle.
    ctx.beginPath();
    ctx.moveTo(0, H * 0.46);
    ctx.quadraticCurveTo(W * 0.30, H * 0.42, W * 0.52, H * 0.45);
    ctx.quadraticCurveTo(W * 0.75, H * 0.48, W, H * 0.43);
    ctx.lineTo(W, H);
    ctx.lineTo(0, H);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = 'rgba(36,63,38,0.8)';
    for (let i = 0; i < 18; i++) {{
      const x = 30 + i * 50 + ((i % 3) * 8);
      const y = H * 0.43 + (i % 2 ? 3 : -2);
      const r = 14 + (i % 4) * 3;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }}

    // Removed the bright fairway ribbon to keep hole/green/bunker unobstructed.
  }}

  function drawGroundGrid() {{
    ctx.strokeStyle = 'rgba(226, 233, 196, 0.16)';
    ctx.lineWidth = 1;

    for (let gx = 0; gx <= 420; gx += 12) {{
      const p0 = project(gx, -55, 0);
      const p1 = project(gx, 55, 0);
      if (!p0 || !p1) continue;
      ctx.beginPath();
      ctx.moveTo(p0.x, p0.y);
      ctx.lineTo(p1.x, p1.y);
      ctx.stroke();
    }}

    for (let gy = -55; gy <= 55; gy += 6) {{
      const p0 = project(0, gy, 0);
      const p1 = project(420, gy, 0);
      if (!p0 || !p1) continue;
      ctx.beginPath();
      ctx.moveTo(p0.x, p0.y);
      ctx.lineTo(p1.x, p1.y);
      ctx.stroke();
    }}
  }}

  function drawFlagAndCup() {{
    const cup = project(hole.x, hole.y, 0);
    const flagTop = project(hole.x, hole.y, 3.2);
    if (!cup || !flagTop) return;

    // Green complex around cup (layered turf + fringe).
    ctx.fillStyle = 'rgba(92, 142, 72, 0.80)';
    ctx.beginPath();
    ctx.ellipse(cup.x, cup.y + 10, 86, 34, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = 'rgba(116, 167, 87, 0.92)';
    ctx.beginPath();
    ctx.ellipse(cup.x, cup.y + 8, 64, 24, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = 'rgba(150, 194, 118, 0.55)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 4; i++) {{
      ctx.beginPath();
      ctx.ellipse(cup.x, cup.y + 8, 58 - i * 8, 21 - i * 3, 0, 0, Math.PI * 2);
      ctx.stroke();
    }}

    // Bunker near green.
    ctx.fillStyle = 'rgba(210, 194, 151, 0.96)';
    ctx.beginPath();
    ctx.ellipse(cup.x - 70, cup.y + 18, 48, 17, -0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = 'rgba(150, 130, 96, 0.8)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    ctx.strokeStyle = '#d9e1e8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(cup.x, cup.y);
    ctx.lineTo(flagTop.x, flagTop.y);
    ctx.stroke();

    ctx.fillStyle = '#f44336';
    ctx.beginPath();
    ctx.moveTo(flagTop.x, flagTop.y);
    ctx.lineTo(flagTop.x + 18, flagTop.y + 6);
    ctx.lineTo(flagTop.x, flagTop.y + 12);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = '#111';
    ctx.beginPath();
    ctx.arc(cup.x, cup.y, 4, 0, Math.PI * 2);
    ctx.fill();
  }}

  function drawTeeMarker() {{
    const tee = project(0, 0, 0);
    if (!tee) return;
    ctx.fillStyle = '#f8f8f8';
    ctx.beginPath();
    ctx.arc(tee.x, tee.y, 5, 0, Math.PI * 2);
    ctx.fill();
  }}

  function drawGolfer(swingF) {{
    const tee = project(0, 0, 0);
    if (!tee) return;
    const [armA, clubA] = getSwingAngles(swingF);

    const gx = tee.x - 42;
    const gy = tee.y + 2;
    const bodyTop = gy - 76;
    const bodyBot = gy - 20;
    const shoulderY = bodyTop + 7;

    ctx.strokeStyle = '#90caf9';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(gx, bodyTop);
    ctx.lineTo(gx, bodyBot);
    ctx.stroke();

    ctx.strokeStyle = '#4f5b62';
    ctx.beginPath();
    ctx.moveTo(gx, bodyBot);
    ctx.lineTo(gx - 10, gy);
    ctx.moveTo(gx, bodyBot);
    ctx.lineTo(gx + 10, gy);
    ctx.stroke();

    ctx.fillStyle = '#ffcc80';
    ctx.beginPath();
    ctx.arc(gx, bodyTop - 9, 9, 0, Math.PI * 2);
    ctx.fill();

    const armLen = 28;
    const handX = gx + Math.cos(armA) * armLen;
    const handY = shoulderY + Math.sin(armA) * armLen;
    ctx.strokeStyle = '#90caf9';
    ctx.beginPath();
    ctx.moveTo(gx, shoulderY);
    ctx.lineTo(handX, handY);
    ctx.stroke();

    const clubLen = 38;
    const tipX = handX + Math.cos(clubA) * clubLen;
    const tipY = handY + Math.sin(clubA) * clubLen;
    ctx.strokeStyle = '#cfd8dc';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(handX, handY);
    ctx.lineTo(tipX, tipY);
    ctx.stroke();
  }}

  function drawGolferDance(danceFrame) {{
    const tee = project(0, 0, 0);
    if (!tee) return;

    const gx = tee.x - 38;
    const gy = tee.y + 2;
    const bounce = Math.sin(danceFrame * 0.35) * 6;
    const bodyTop = gy - 74 + bounce;
    const bodyBot = gy - 18 + bounce;
    const shoulderY = bodyTop + 8;
    const step = Math.floor((danceFrame % 48) / 12);

    // Macarena-inspired four-step arm positions.
    let armA = 0.0;
    let armB = 0.0;
    if (step === 0) {{
      armA = -0.05;  // left arm forward
      armB = -2.5;   // right arm down
    }} else if (step === 1) {{
      armA = -0.05;  // both arms forward
      armB = -3.10;
    }} else if (step === 2) {{
      armA = -0.8;   // left hand to shoulder
      armB = -3.10;
    }} else {{
      armA = -0.8;   // both hands to shoulders
      armB = 2.35;
    }}

    ctx.strokeStyle = '#9fe6ff';
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.moveTo(gx, bodyTop);
    ctx.lineTo(gx, bodyBot);
    ctx.stroke();

    ctx.strokeStyle = '#4f5b62';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(gx, bodyBot);
    ctx.lineTo(gx - 11, gy + 1 + Math.sin(danceFrame * 0.2) * 3);
    ctx.moveTo(gx, bodyBot);
    ctx.lineTo(gx + 11, gy + 1 - Math.sin(danceFrame * 0.2) * 3);
    ctx.stroke();

    ctx.fillStyle = '#ffcc80';
    ctx.beginPath();
    ctx.arc(gx, bodyTop - 10, 9, 0, Math.PI * 2);
    ctx.fill();

    const armLen = 26;
    const handAX = gx + Math.cos(armA) * armLen;
    const handAY = shoulderY + Math.sin(armA) * armLen;
    const handBX = gx + Math.cos(armB) * armLen;
    const handBY = shoulderY + Math.sin(armB) * armLen;
    ctx.strokeStyle = '#9fe6ff';
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.moveTo(gx, shoulderY);
    ctx.lineTo(handAX, handAY);
    ctx.moveTo(gx, shoulderY);
    ctx.lineTo(handBX, handBY);
    ctx.stroke();
  }}

  function drawTrajectory(fi) {{
    if (fi < 1) return;
    ctx.strokeStyle = '#00c853';
    ctx.lineWidth = 4;
    ctx.beginPath();
    let started = false;
    for (let i = 0; i <= fi; i++) {{
      const p = project(traj[i][0], traj[i][1], traj[i][2]);
      if (!p) continue;
      if (!started) {{
        ctx.moveTo(p.x, p.y);
        started = true;
      }} else {{
        ctx.lineTo(p.x, p.y);
      }}
    }}
    if (started) ctx.stroke();
  }}

  function drawBallAt(x, y, z) {{
    const p = project(x, y, z);
    if (!p) return;
    const ground = project(x, y, 0);
    if (ground) {{
      ctx.fillStyle = 'rgba(0,0,0,0.22)';
      ctx.beginPath();
      ctx.ellipse(ground.x, ground.y + 2, 7, 3, 0, 0, Math.PI * 2);
      ctx.fill();
    }}
    const r = clamp(8 - p.zc * 0.015, 3, 8);
    ctx.fillStyle = '#ffffff';
    ctx.strokeStyle = '#d6dee5';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }}

  function drawLandingMarker() {{
    const p = project(landing.x, landing.y, 0);
    if (!p) return;
    ctx.strokeStyle = '#ff8a80';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(p.x - 6, p.y - 6);
    ctx.lineTo(p.x + 6, p.y + 6);
    ctx.moveTo(p.x + 6, p.y - 6);
    ctx.lineTo(p.x - 6, p.y + 6);
    ctx.stroke();
  }}

  function drawLandingComparison() {{
    const lp = project(landing.x, landing.y, 0);
    const hp = project(hole.x, hole.y, 0);
    if (!lp || !hp) return;

    // Visual link from hole to landing point.
    ctx.setLineDash([6, 6]);
    ctx.strokeStyle = 'rgba(255,255,255,0.9)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(hp.x, hp.y);
    ctx.lineTo(lp.x, lp.y);
    ctx.stroke();
    ctx.setLineDash([]);

    // Directional arrow at landing side.
    const dx = lp.x - hp.x;
    const dy = lp.y - hp.y;
    const ang = Math.atan2(dy, dx);
    const ah = 10;
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.moveTo(lp.x, lp.y);
    ctx.lineTo(lp.x - ah * Math.cos(ang - 0.4), lp.y - ah * Math.sin(ang - 0.4));
    ctx.lineTo(lp.x - ah * Math.cos(ang + 0.4), lp.y - ah * Math.sin(ang + 0.4));
    ctx.closePath();
    ctx.fill();

    // Comparison box near landing point.
    const bx = lp.x + 16;
    const by = lp.y - 64;
    ctx.fillStyle = 'rgba(255,255,255,0.94)';
    ctx.fillRect(bx, by, 190, 64);
    ctx.strokeStyle = '#7b8a96';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(bx, by, 190, 64);
    ctx.fillStyle = '#20303d';
    ctx.font = 'bold 12px sans-serif';
    ctx.fillText('Ball vs Hole', bx + 10, by + 18);
    ctx.font = '12px sans-serif';
    ctx.fillText(`Long/Short: ${{missLongShort.toFixed(2)}} m`, bx + 10, by + 36);
    ctx.fillText(`Left/Right: ${{missLeftRight.toFixed(2)}} m`, bx + 10, by + 52);
  }}

  function drawHoleInOneCelebration(danceFrame) {{
    const bw = 450;
    const bh = 92;
    const bx = (W - bw) / 2;
    const by = 24;

    ctx.fillStyle = 'rgba(15, 25, 35, 0.86)';
    ctx.fillRect(bx, by, bw, bh);
    ctx.strokeStyle = '#ffd54f';
    ctx.lineWidth = 3;
    ctx.strokeRect(bx, by, bw, bh);

    const glow = 0.65 + 0.35 * Math.sin(danceFrame * 0.3);
    ctx.fillStyle = `rgba(255, 230, 120, ${{glow.toFixed(3)}})`;
    ctx.font = 'bold 36px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('HOLE IN ONE!', W / 2, by + 44);
    ctx.font = 'bold 18px sans-serif';
    ctx.fillText('Celebration Mode', W / 2, by + 74);
    ctx.textAlign = 'start';
  }}

  function drawHud(fi) {{
    // Intentionally blank: user requested to remove shot details from the simulation canvas.
  }}

  function drawShotBox() {{
    // Intentionally blank: controls live in top-right HTML panel.
  }}

  function drawApexLabel(fi) {{
    if (fi < 3) return;
    let idx = 0;
    for (let i = 1; i <= fi; i++) {{
      if (traj[i][2] > traj[idx][2]) idx = i;
    }}
    const p = project(traj[idx][0], traj[idx][1], traj[idx][2]);
    if (!p) return;
    const bw = 112;
    const bh = 44;
    const bx = p.x + 14;
    const by = p.y - 56;
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
    ctx.fillRect(bx, by, bw, bh);
    ctx.strokeStyle = '#8d6e1c';
    ctx.lineWidth = 2;
    ctx.strokeRect(bx, by, bw, bh);
    ctx.fillStyle = '#1e2935';
    ctx.font = 'bold 13px sans-serif';
    ctx.fillText('Apex', bx + 35, by + 17);
    ctx.font = '14px sans-serif';
    ctx.fillText(`${{apexM.toFixed(2)}} m`, bx + 30, by + 35);
  }}

  function render() {{
    drawBackground();
    drawGroundGrid();
    drawFlagAndCup();
    drawTeeMarker();
    drawLandingMarker();
    drawShotBox();

    if (phase === 'ready') {{
      drawGolfer(0);
      drawBallAt(0, 0, 0);
      drawHud(0);
      return;
    }}

    if (phase === 'swing') {{
      drawGolfer(swingFrame);
      if (swingFrame < IMPACT_FRAME) {{
        drawBallAt(0, 0, 0);
      }} else {{
        drawBallAt(traj[0][0], traj[0][1], traj[0][2]);
      }}
      drawHud(0);
      return;
    }}

    // flight / hold
    const fi = Math.min(flightFrame, FLIGHT_FRAMES - 1);
    drawTrajectory(fi);
    drawApexLabel(fi);
    drawGolfer(SWING_FRAMES);
    drawBallAt(traj[fi][0], traj[fi][1], traj[fi][2]);
    drawHud(fi);
    if (phase === 'hold') {{
      drawLandingComparison();
      if (holeInOne) {{
        drawGolferDance(holdFrame);
        drawHoleInOneCelebration(holdFrame);
      }}
    }}
  }}

  function tick() {{
    ctx.clearRect(0, 0, W, H);
    render();

    if (phase === 'swing') {{
      swingFrame += 1;
      if (swingFrame >= SWING_FRAMES) {{
        phase = 'flight';
        flightFrame = 0;
      }}
      animId = requestAnimationFrame(tick);
      return;
    }}

    if (phase === 'flight') {{
      flightFrame += FLIGHT_STEP;
      if (flightFrame >= FLIGHT_FRAMES) {{
        phase = 'hold';
        holdFrame = 0;
      }}
      animId = requestAnimationFrame(tick);
      return;
    }}

    if (phase === 'hold') {{
      holdFrame += 1;
      if (holdFrame >= HOLD_FRAMES) {{
        phase = 'ready';
        btn.disabled = false;
        btn.textContent = 'Replay Shot';
        return;
      }}
      animId = requestAnimationFrame(tick);
    }}
  }}

  function startShot() {{
    if (animId) cancelAnimationFrame(animId);
    phase = 'swing';
    swingFrame = 0;
    flightFrame = 0;
    holdFrame = 0;
    btn.disabled = true;
    btn.textContent = 'Ball In Flight...';
    tick();
  }}

  function drawWindCompass() {{
    const CW = windCompass.width;
    const CH = windCompass.height;
    const cx = CW * 0.5;
    const cy = CH * 0.5 + 8;
    const r = 62;
    wctx.clearRect(0, 0, CW, CH);

    wctx.fillStyle = '#f3f7fb';
    wctx.beginPath();
    wctx.arc(cx, cy, r + 14, 0, Math.PI * 2);
    wctx.fill();
    wctx.strokeStyle = '#b8c4d1';
    wctx.lineWidth = 2;
    wctx.stroke();

    wctx.strokeStyle = '#6c7a88';
    wctx.lineWidth = 1.5;
    for (let d = 0; d < 360; d += 10) {{
      const a = (d - 90) * Math.PI / 180;
      const inner = d % 30 === 0 ? r - 10 : r - 5;
      wctx.beginPath();
      wctx.moveTo(cx + Math.cos(a) * inner, cy + Math.sin(a) * inner);
      wctx.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
      wctx.stroke();
    }}

    wctx.fillStyle = '#0b1724';
    wctx.strokeStyle = '#f0f5fb';
    wctx.lineWidth = 2.5;
    wctx.font = 'bold 22px sans-serif';
    wctx.textAlign = 'center';
    wctx.textBaseline = 'middle';
    wctx.strokeText('N', cx, cy - r + 10);
    wctx.fillText('N', cx, cy - r + 10);
    wctx.strokeText('E', cx + r - 10, cy);
    wctx.fillText('E', cx + r - 10, cy);
    wctx.strokeText('S', cx, cy + r - 8);
    wctx.fillText('S', cx, cy + r - 8);
    wctx.strokeText('W', cx - r + 10, cy);
    wctx.fillText('W', cx - r + 10, cy);
    wctx.textAlign = 'start';
    wctx.textBaseline = 'alphabetic';

    const a = (windDirDeg - 90) * Math.PI / 180;
    const tipX = cx + Math.cos(a) * (r - 2);
    const tipY = cy + Math.sin(a) * (r - 2);
    const baseX = cx - Math.cos(a) * 12;
    const baseY = cy - Math.sin(a) * 12;
    const perpX = Math.cos(a + Math.PI / 2) * 7;
    const perpY = Math.sin(a + Math.PI / 2) * 7;

    wctx.fillStyle = '#ef5350';
    wctx.beginPath();
    wctx.moveTo(tipX, tipY);
    wctx.lineTo(baseX + perpX, baseY + perpY);
    wctx.lineTo(baseX - perpX, baseY - perpY);
    wctx.closePath();
    wctx.fill();

    wctx.fillStyle = '#cfd8dc';
    wctx.beginPath();
    wctx.arc(cx, cy, 11, 0, Math.PI * 2);
    wctx.fill();
    wctx.strokeStyle = '#8d9aa7';
    wctx.lineWidth = 1;
    wctx.stroke();

    windSpeedText.textContent = windSpeedMph.toFixed(1);
    windDirText.textContent = windDirDeg.toFixed(1);
  }}

  function bindShotControls() {{
    clubValue.textContent = uiClubName;
    swingValue.textContent = `${{uiSwingPct.toFixed(2)}}%`;
    dirValue.textContent = `${{uiShotDir.toFixed(2)}}`;
    drawWindCompass();
  }}

  btn.addEventListener('click', startShot);
  window._golfAnim3d = {{ start: startShot }};
  bindShotControls();
  render();
}})();
</script>
"""


def make_topdown_figure(result: SimulationResult) -> Figure:
    xs = [p.x for p in result.points]
    ys = [p.y for p in result.points]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(xs, ys, label="Ball path")
    ax.scatter([0], [0], s=50, marker="o", label="Tee")
    ax.scatter([result.derived.hole_x_m], [result.derived.hole_y_m], s=70, marker="^", label="Hole")
    ax.scatter([result.landing_x_m], [result.landing_y_m], s=60, marker="x", label="Landing")
    cup = plt.Circle((result.derived.hole_x_m, result.derived.hole_y_m), result.derived.club.base_lift_coefficient * 0 + result.derived.club.base_lift_coefficient*0 + 0.10, fill=False)
    ax.add_artist(cup)
    ax.set_xlabel("X (forward, m)")
    ax.set_ylabel("Y (sideways, m)")
    ax.set_title("Top-Down View")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(loc="best")
    return fig
