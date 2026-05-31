"""
Football tracking data insights
Generates 4 visualisations from a match tracking JSONL file.
"""

import json
import math
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import numpy as np

# ── Config ──────────────────────────────────────────────────────────────────
TRACKING_FILE = "/Users/user/Downloads/2068343_tracking_extrapolated.jsonl"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "Data", "tracking_insights")
os.makedirs(OUTPUT_DIR, exist_ok=True)

PITCH_LENGTH = 105.0   # metres (x: -52.5 → +52.5)
PITCH_WIDTH  = 68.0    # metres (y: -34  → +34)
FPS = 10               # frames per second

HOME_COLOR = "#1a78cf"
AWAY_COLOR = "#e63946"


# ── Pitch drawing ────────────────────────────────────────────────────────────
def draw_pitch(ax, color="white", linecolor="#cccccc", zorder=0):
    ax.set_facecolor(color)
    lw = 1.2
    kw = dict(color=linecolor, lw=lw, zorder=zorder)

    # Outer rectangle
    ax.plot([-52.5, 52.5, 52.5, -52.5, -52.5],
            [-34, -34, 34, 34, -34], **kw)
    # Halfway line + centre circle
    ax.plot([0, 0], [-34, 34], **kw)
    centre = plt.Circle((0, 0), 9.15, fill=False, **kw)
    ax.add_patch(centre)
    ax.plot(0, 0, "o", color=linecolor, ms=2, zorder=zorder)

    for sign in (-1, 1):
        # Penalty area (40.32m wide, 16.5m deep)
        ax.plot([sign * 52.5, sign * 36.0, sign * 36.0, sign * 52.5],
                [-20.16, -20.16, 20.16, 20.16], **kw)
        # Goal area (18.32m wide, 5.5m deep)
        ax.plot([sign * 52.5, sign * 47.0, sign * 47.0, sign * 52.5],
                [-9.16, -9.16, 9.16, 9.16], **kw)
        # Penalty spot
        ax.plot(sign * 40.39, 0, "o", color=linecolor, ms=2, zorder=zorder)
        # Penalty arc
        arc = mpatches.Arc((sign * 40.39, 0), 18.3, 18.3,
                            angle=0,
                            theta1=130 if sign == 1 else 310,
                            theta2=230 if sign == 1 else 50,
                            **kw)
        ax.add_patch(arc)
        # Goals
        ax.plot([sign * 52.5, sign * 54.0, sign * 54.0, sign * 52.5],
                [-3.66, -3.66, 3.66, 3.66],
                color=linecolor, lw=lw * 0.8, zorder=zorder)

    ax.set_xlim(-56, 56)
    ax.set_ylim(-37, 37)
    ax.set_aspect("equal")
    ax.axis("off")


# ── Load data ────────────────────────────────────────────────────────────────
print("Loading tracking data…")
frames = []
with open(TRACKING_FILE) as f:
    for line in f:
        frames.append(json.loads(line))

# Identify team membership from possession events
player_team = {}
for fr in frames:
    pid = fr["possession"]["player_id"]
    grp = fr["possession"]["group"]
    if pid and grp:
        player_team[pid] = grp

# Fallback: players with avg_x < 0 in period 1 are home, > 0 away
player_sum_x = defaultdict(list)
for fr in frames:
    if fr["period"] == 1:
        for p in fr["player_data"]:
            if p["is_detected"]:
                player_sum_x[p["player_id"]].append(p["x"])
for pid, xs in player_sum_x.items():
    if pid not in player_team:
        player_team[pid] = "home team" if (sum(xs) / len(xs)) < 0 else "away team"

home_ids = {pid for pid, t in player_team.items() if t == "home team"}
away_ids = {pid for pid, t in player_team.items() if t == "away team"}


# ── 1. Distance covered per player ──────────────────────────────────────────
print("Computing distances…")

prev_pos = {}
distance = defaultdict(float)

for fr in frames:
    for p in fr["player_data"]:
        pid = p["player_id"]
        if not p["is_detected"]:
            prev_pos.pop(pid, None)
            continue
        cur = (p["x"], p["y"])
        if pid in prev_pos:
            dx = cur[0] - prev_pos[pid][0]
            dy = cur[1] - prev_pos[pid][1]
            d = math.sqrt(dx * dx + dy * dy)
            if d < 8:          # ignore teleports / large gaps
                distance[pid] += d
        prev_pos[pid] = cur

# Convert to km and sort
dist_km = {pid: d / 1000 for pid, d in distance.items()}
home_dist = sorted([(pid, dist_km[pid]) for pid in home_ids if pid in dist_km],
                   key=lambda x: x[1], reverse=True)
away_dist = sorted([(pid, dist_km[pid]) for pid in away_ids if pid in dist_km],
                   key=lambda x: x[1], reverse=True)
all_sorted = home_dist + away_dist
all_sorted.sort(key=lambda x: x[1], reverse=True)

labels = [str(pid) for pid, _ in all_sorted]
values = [v for _, v in all_sorted]
colors = [HOME_COLOR if pid in home_ids else AWAY_COLOR for pid, _ in all_sorted]

fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#0d1117")
bars = ax.barh(labels, values, color=colors, edgecolor="none", height=0.7)
ax.set_xlabel("Distance (km)", color="white", fontsize=11)
ax.set_title("Distance Covered by Player", color="white", fontsize=14, pad=12)
ax.tick_params(colors="white")
ax.spines[:].set_visible(False)
ax.xaxis.label.set_color("white")
for val, bar in zip(values, bars):
    ax.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}", va="center", ha="left", color="white", fontsize=8)
home_patch = mpatches.Patch(color=HOME_COLOR, label="Home")
away_patch = mpatches.Patch(color=AWAY_COLOR, label="Away")
ax.legend(handles=[home_patch, away_patch], facecolor="#1c2128",
          labelcolor="white", framealpha=0.8)
plt.tight_layout()
path1 = os.path.join(OUTPUT_DIR, "1_distance_covered.png")
plt.savefig(path1, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"  Saved → {path1}")


# ── 2. Ball heatmap ──────────────────────────────────────────────────────────
print("Computing ball heatmap…")

ball_x, ball_y = [], []
for fr in frames:
    bd = fr["ball_data"]
    if bd["is_detected"] and bd["x"] is not None:
        ball_x.append(bd["x"])
        ball_y.append(bd["y"])

fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor("#0d1117")
draw_pitch(ax, color="#0d1117", linecolor="#555555")

hb = ax.hexbin(ball_x, ball_y, gridsize=40, cmap="inferno",
               extent=[-52.5, 52.5, -34, 34], mincnt=1, alpha=0.85)
cbar = fig.colorbar(hb, ax=ax, pad=0.01, fraction=0.025)
cbar.set_label("Frame count", color="white")
cbar.ax.yaxis.set_tick_params(color="white")
plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")
ax.set_title("Ball Position Heatmap", color="white", fontsize=14, pad=8)
# Label home/away halves
ax.text(-40, 36, "HOME half", color=HOME_COLOR, ha="center", fontsize=10, fontweight="bold")
ax.text( 40, 36, "AWAY half", color=AWAY_COLOR, ha="center", fontsize=10, fontweight="bold")

path2 = os.path.join(OUTPUT_DIR, "2_ball_heatmap.png")
plt.savefig(path2, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"  Saved → {path2}")


# ── 3. Average player positions (formation) ──────────────────────────────────
print("Computing average positions…")

# Normalise: flip period 2 so home always attacks right→left
# Home defends left (negative x) in period 1; in period 2 they swap sides.
# We normalise so home always attacks toward positive x.
player_positions = defaultdict(lambda: {"x": [], "y": []})

for fr in frames:
    if fr["period"] is None:
        continue
    flip = (fr["period"] == 2)
    for p in fr["player_data"]:
        if not p["is_detected"]:
            continue
        x = -p["x"] if flip else p["x"]
        y = -p["y"] if flip else p["y"]
        player_positions[p["player_id"]]["x"].append(x)
        player_positions[p["player_id"]]["y"].append(y)

avg_pos = {pid: (np.median(v["x"]), np.median(v["y"]))
           for pid, v in player_positions.items()
           if len(v["x"]) > 500}

fig, ax = plt.subplots(figsize=(13, 8))
fig.patch.set_facecolor("#0d1117")
draw_pitch(ax, color="#0d1117", linecolor="#555555")

for pid, (ax_x, ax_y) in avg_pos.items():
    team = player_team.get(pid, "")
    color = HOME_COLOR if team == "home team" else AWAY_COLOR
    ax.scatter(ax_x, ax_y, s=300, color=color, edgecolors="white",
               linewidths=1.5, zorder=5)
    ax.text(ax_x, ax_y - 3.5, str(pid), ha="center", va="top",
            color="white", fontsize=6, zorder=6)

ax.set_title("Average Player Positions (normalised: home attacks →)",
             color="white", fontsize=13, pad=8)
home_patch = mpatches.Patch(color=HOME_COLOR, label="Home")
away_patch = mpatches.Patch(color=AWAY_COLOR, label="Away")
ax.legend(handles=[home_patch, away_patch], facecolor="#1c2128",
          labelcolor="white", loc="lower right")

path3 = os.path.join(OUTPUT_DIR, "3_average_positions.png")
plt.savefig(path3, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"  Saved → {path3}")


# ── 4. Team compactness & centroid over time ──────────────────────────────────
print("Computing team compactness…")

WINDOW = FPS * 30   # 30-second rolling window for smoothing

home_cx, home_spread, away_cx, away_spread, minutes = [], [], [], [], []

for fr in frames:
    if fr["period"] is None or fr["timestamp"] is None:
        continue

    home_xs, away_xs = [], []
    for p in fr["player_data"]:
        if not p["is_detected"]:
            continue
        pid = p["player_id"]
        if pid in home_ids and pid != 529803:   # exclude GK for outfield compactness
            home_xs.append(p["x"])
        elif pid in away_ids and pid != 32682:
            away_xs.append(p["x"])

    if len(home_xs) >= 5 and len(away_xs) >= 5:
        home_cx.append(np.mean(home_xs))
        home_spread.append(np.std(home_xs))
        away_cx.append(np.mean(away_xs))
        away_spread.append(np.std(away_xs))

        # Parse timestamp "HH:MM:SS.ff" → minutes
        ts = fr["timestamp"]
        h, m, rest = ts.split(":")
        s = float(rest)
        minutes.append(int(h) * 60 + int(m) + s / 60)

minutes = np.array(minutes)
home_cx = np.array(home_cx)
away_cx = np.array(away_cx)
home_spread = np.array(home_spread)
away_spread = np.array(away_spread)


def rolling_mean(arr, w):
    kernel = np.ones(w) / w
    return np.convolve(arr, kernel, mode="same")


w = WINDOW
hcx = rolling_mean(home_cx, w)
acx = rolling_mean(away_cx, w)
hsp = rolling_mean(home_spread, w)
asp = rolling_mean(away_spread, w)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
fig.patch.set_facecolor("#0d1117")
for ax in (ax1, ax2):
    ax.set_facecolor("#0d1117")
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")
    ax.yaxis.label.set_color("white")

# Draw half-time divider
ht = minutes[minutes <= 45].max() if any(minutes <= 45) else 45
for ax in (ax1, ax2):
    ax.axvline(ht, color="#888888", lw=1, ls="--", alpha=0.6, label="Half time")

ax1.plot(minutes, hcx, color=HOME_COLOR, lw=1.5, alpha=0.9, label="Home centroid x")
ax1.plot(minutes, acx, color=AWAY_COLOR, lw=1.5, alpha=0.9, label="Away centroid x")
ax1.axhline(0, color="#888888", lw=0.8, ls=":")
ax1.set_ylabel("Centroid x (m)")
ax1.set_title("Team Centroid & Compactness Over Time (30s rolling avg)",
              color="white", fontsize=13)
ax1.legend(facecolor="#1c2128", labelcolor="white", fontsize=9)

ax2.plot(minutes, hsp, color=HOME_COLOR, lw=1.5, alpha=0.9, label="Home spread (σ x)")
ax2.plot(minutes, asp, color=AWAY_COLOR, lw=1.5, alpha=0.9, label="Away spread (σ x)")
ax2.set_ylabel("Spread σ (m)")
ax2.set_xlabel("Match minute", color="white")
ax2.legend(facecolor="#1c2128", labelcolor="white", fontsize=9)
ax2.xaxis.label.set_color("white")

plt.tight_layout()
path4 = os.path.join(OUTPUT_DIR, "4_team_compactness.png")
plt.savefig(path4, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"  Saved → {path4}")


# ── Summary stats ────────────────────────────────────────────────────────────
total_home = sum(v for pid, v in dist_km.items() if pid in home_ids)
total_away = sum(v for pid, v in dist_km.items() if pid in away_ids)
poss_frames = [fr for fr in frames if fr["possession"]["group"]]
home_poss = sum(1 for fr in poss_frames if fr["possession"]["group"] == "home team")
away_poss = sum(1 for fr in poss_frames if fr["possession"]["group"] == "away team")
total_poss = home_poss + away_poss

print("\n── Match Summary ─────────────────────────────────────────────────")
print(f"  Total distance  →  Home {total_home:.1f} km  |  Away {total_away:.1f} km")
print(f"  Ball possession →  Home {home_poss/total_poss*100:.1f}%  |  Away {away_poss/total_poss*100:.1f}%")
print(f"  Ball detected   →  {len(ball_x):,} frames  ({len(ball_x)/len(frames)*100:.0f}% of match)")
print("──────────────────────────────────────────────────────────────────")
print(f"\nAll images saved to: {OUTPUT_DIR}")
