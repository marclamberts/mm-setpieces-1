"""
Convert Saudi Pro League JSON events + CSV match metadata into parquet files
matching the repo's Corners, Freekicks and Throwins schemas.

Usage:
    python scripts/convert_saudi_to_parquet.py \
        --done   /Users/user/XG/Saudi/DONE \
        --xgcsv  /xgCSV \
        --matches "/Users/user/XG/Saudi Matches.csv" \
        --out    /path/to/mm-setpieces-1/Data

Outputs (placed in --out directory):
    Corners/Saudi Pro League - Corners 2025-2026.parquet
    SP/Saudi Pro League - Freekicks.parquet
    SP/Saudi Pro League - Throwins.parquet
"""

import argparse
import json
import math
import os
import glob
import re

import numpy as np
import pandas as pd


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--done",    required=True, help="Dir with StatsBomb JSON event files")
    p.add_argument("--xgcsv",  required=True, help="Dir with per-match xG CSV files")
    p.add_argument("--matches", required=True, help="Saudi Matches.csv (match metadata)")
    p.add_argument("--out",     required=True, help="Root Data/ directory of the repo")
    return p.parse_args()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _xy(loc):
    """Return (x, y) floats from a StatsBomb location list/None."""
    if loc is None or (isinstance(loc, float) and math.isnan(loc)):
        return None, None
    if isinstance(loc, str):
        loc = json.loads(loc)
    return float(loc[0]), float(loc[1])


def _loc_str(loc):
    """'x, y' string used in SP location columns."""
    x, y = _xy(loc)
    if x is None:
        return None
    return f"{x}, {y}"


def _ts(s):
    """Normalise timestamp string, return as-is (already HH:MM:SS.mmm)."""
    return s if isinstance(s, str) else None


def _match_label(row):
    """'{Home} - {Away}' from match metadata row."""
    return f"{row['home_team_name']} - {row['away_team_name']}"


def _minute_second(timestamp):
    """Return (minute, second) ints from 'HH:MM:SS.mmm'."""
    if not isinstance(timestamp, str):
        return None, None
    parts = timestamp.split(":")
    try:
        h, m, s = int(parts[0]), int(parts[1]), int(float(parts[2]))
        return h * 60 + m, s
    except Exception:
        return None, None


# ── Load matches metadata ────────────────────────────────────────────────────

def load_matches(path):
    df = pd.read_csv(path)
    # Normalise common column name variants
    df.columns = [c.strip() for c in df.columns]
    rename = {}
    for c in df.columns:
        cl = c.lower()
        if cl in ("match_id", "id"):
            rename[c] = "match_id"
        elif "home" in cl and "team" in cl and "name" in cl:
            rename[c] = "home_team_name"
        elif "away" in cl and "team" in cl and "name" in cl:
            rename[c] = "away_team_name"
    df = df.rename(columns=rename)
    df["match_id"] = df["match_id"].astype(int)
    return df.set_index("match_id")


# ── Load xG CSVs ─────────────────────────────────────────────────────────────

def load_xg_csvs(xgcsv_dir):
    """Return dict {match_id: DataFrame} from per-match xG CSVs."""
    out = {}
    for fp in glob.glob(os.path.join(xgcsv_dir, "*.csv")):
        try:
            df = pd.read_csv(fp)
            df.columns = [c.strip() for c in df.columns]
            # Try to infer match_id from filename or column
            if "match_id" in df.columns:
                mid = int(df["match_id"].iloc[0])
            else:
                m = re.search(r"(\d{6,})", os.path.basename(fp))
                if not m:
                    continue
                mid = int(m.group(1))
            out[mid] = df
        except Exception as e:
            print(f"  Warning: could not read {fp}: {e}")
    return out


# ── Process JSON events ──────────────────────────────────────────────────────

def load_json_events(done_dir):
    """Load all JSON event files, return list of (match_id, events_list)."""
    pairs = []
    for fp in sorted(glob.glob(os.path.join(done_dir, "*.json"))):
        m = re.search(r"(\d{5,})", os.path.basename(fp))
        if not m:
            # Try loading to find match_id inside
            with open(fp) as f:
                events = json.load(f)
            if not events:
                continue
            mid = events[0].get("match_id")
            if mid is None:
                print(f"  Warning: cannot determine match_id for {fp}, skipping")
                continue
        else:
            mid = int(m.group(1))
            with open(fp) as f:
                events = json.load(f)
        pairs.append((int(mid), events))
    return pairs


# ── Build CORNERS ────────────────────────────────────────────────────────────

CORNER_TYPES = {"corner kick", "corner"}

def build_corners(match_events_list, matches_df):
    rows = []
    for match_id, events in match_events_list:
        if match_id not in matches_df.index:
            print(f"  Warning: match_id {match_id} not in matches CSV, skipping corners")
            continue
        meta = matches_df.loc[match_id]
        match_label = _match_label(meta)

        # Index shot events by possession for quick lookup
        shots_by_poss = {}
        for ev in events:
            if ev.get("type", {}).get("name", "").lower() == "shot":
                poss = ev.get("index_possession") or ev.get("possession")
                shots_by_poss.setdefault(poss, []).append(ev)

        for ev in events:
            etype = ev.get("type", {}).get("name", "")
            if etype.lower() != "pass":
                continue
            pass_data = ev.get("pass", {})
            # Detect corner
            technique = (pass_data.get("technique") or {}).get("name", "")
            play_pattern = ev.get("play_pattern", {}).get("name", "")
            sp_type = pass_data.get("type", {}).get("name", "") if pass_data.get("type") else ""

            is_corner = (
                "corner" in technique.lower()
                or "corner" in play_pattern.lower()
                or "corner" in sp_type.lower()
                or any("corner" in str(v).lower() for v in [
                    pass_data.get("goal_assist"), pass_data.get("switch")
                ] if v)
            )
            # StatsBomb corner detection: play_pattern = "From Corner"
            if not is_corner:
                pp = ev.get("play_pattern", {}).get("name", "")
                is_corner = "corner" in pp.lower()

            if not is_corner:
                continue

            possession = ev.get("index_possession") or ev.get("possession")
            timestamp = ev.get("timestamp", "")
            minute, second = _minute_second(timestamp)
            loc = ev.get("location", [None, None])
            px, py = (loc[0], loc[1]) if loc and len(loc) >= 2 else (None, None)
            end_loc = pass_data.get("end_location", [None, None])
            ex, ey = (end_loc[0], end_loc[1]) if end_loc and len(end_loc) >= 2 else (None, None)

            # Find associated shot in same possession
            shot_ev = None
            for s in shots_by_poss.get(possession, []):
                shot_ev = s
                break

            shot_data = shot_ev.get("shot", {}) if shot_ev else {}
            shot_loc = shot_ev.get("location", []) if shot_ev else []
            sx = shot_loc[0] if shot_loc and len(shot_loc) > 0 else None
            sy = shot_loc[1] if shot_loc and len(shot_loc) > 1 else None
            sz = shot_loc[2] if shot_loc and len(shot_loc) > 2 else None

            rows.append({
                "match_id": match_id,
                "Match": match_label,
                "possession": possession,
                "pass_timestamp": timestamp,
                "pass_team_name": ev.get("team", {}).get("name"),
                "Taker": ev.get("player", {}).get("name"),
                "pass_position": ev.get("position", {}).get("name"),
                "pass.height.name": pass_data.get("height", {}).get("name") if pass_data.get("height") else None,
                "pass.body_part.name": pass_data.get("body_part", {}).get("name") if pass_data.get("body_part") else None,
                "pass.outcome.name": pass_data.get("outcome", {}).get("name") if pass_data.get("outcome") else None,
                "pass.technique.name": technique or None,
                "pass_location_x": float(px) if px is not None else None,
                "pass_location_y": float(py) if py is not None else None,
                "pass_end_location_x": float(ex) if ex is not None else None,
                "pass_end_location_y": float(ey) if ey is not None else None,
                "shot_timestamp": shot_ev.get("timestamp") if shot_ev else None,
                "shot_team_name": shot_ev.get("team", {}).get("name") if shot_ev else None,
                "Shooter": shot_ev.get("player", {}).get("name") if shot_ev else None,
                "shot_position": shot_ev.get("position", {}).get("name") if shot_ev else None,
                "shot.body_part.name": shot_data.get("body_part", {}).get("name") if shot_data.get("body_part") else None,
                "shot.outcome.name": shot_data.get("outcome", {}).get("name") if shot_data.get("outcome") else None,
                "shot.statsbomb_xg": shot_data.get("statsbomb_xg"),
                "shot_location_x": float(sx) if sx is not None else None,
                "shot_location_y": float(sy) if sy is not None else None,
                "shot_location_z": float(sz) if sz is not None else None,
                "Defensive_setup": "",
                "Minute": minute,
                "Second": second,
                "SP_outcome": pass_data.get("outcome", {}).get("name") if pass_data.get("outcome") else "",
            })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["match_id"] = df["match_id"].astype("int64")
    df["possession"] = df["possession"].astype("int64")
    for col in ("Minute", "Second"):
        df[col] = pd.array(df[col].values, dtype=pd.Int64Dtype())
    for col in ("shot.statsbomb_xg", "pass_location_x", "pass_location_y",
                "pass_end_location_x", "pass_end_location_y",
                "shot_location_x", "shot_location_y", "shot_location_z"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ── Build SP (Freekicks / Throwins) ─────────────────────────────────────────

def _sp_type_from_event(ev):
    """Return 'From Free Kick' or 'From Throw In' or None."""
    pass_data = ev.get("pass", {})
    pp = ev.get("play_pattern", {}).get("name", "")
    sp_t = pass_data.get("type", {}).get("name", "") if pass_data.get("type") else ""

    if "free kick" in pp.lower() or "free kick" in sp_t.lower():
        return "From Free Kick"
    if "throw" in pp.lower() or "throw" in sp_t.lower():
        return "From Throw In"
    return None


def build_sp(match_events_list, matches_df):
    rows = []
    for match_id, events in match_events_list:
        if match_id not in matches_df.index:
            print(f"  Warning: match_id {match_id} not in matches CSV, skipping SP")
            continue

        shots_by_poss = {}
        for ev in events:
            if ev.get("type", {}).get("name", "").lower() == "shot":
                poss = ev.get("index_possession") or ev.get("possession")
                shots_by_poss.setdefault(poss, []).append(ev)

        for ev in events:
            if ev.get("type", {}).get("name", "").lower() != "pass":
                continue
            sp_type = _sp_type_from_event(ev)
            if sp_type is None:
                continue

            pass_data = ev.get("pass", {})
            possession = ev.get("index_possession") or ev.get("possession")
            loc = ev.get("location", [None, None])
            px = loc[0] if loc and len(loc) > 0 else None
            py = loc[1] if loc and len(loc) > 1 else None
            end_loc = pass_data.get("end_location", [None, None])
            ex = end_loc[0] if end_loc and len(end_loc) > 0 else None
            ey = end_loc[1] if end_loc and len(end_loc) > 1 else None

            shot_ev = (shots_by_poss.get(possession) or [None])[0]
            shot_data = shot_ev.get("shot", {}) if shot_ev else {}
            shot_loc = shot_ev.get("location", []) if shot_ev else []
            sx = shot_loc[0] if shot_loc and len(shot_loc) > 0 else None
            sy = shot_loc[1] if shot_loc and len(shot_loc) > 1 else None

            rows.append({
                "match_id": match_id,
                "possession": possession,
                "team.name": ev.get("team", {}).get("name"),
                "type.name": "Pass",
                "SP_Type": sp_type,
                "location.pass": _loc_str(loc),
                "pass.height.name": pass_data.get("height", {}).get("name") if pass_data.get("height") else None,
                "timestamp": ev.get("timestamp"),
                "Taker": ev.get("player", {}).get("name"),
                "Shooter": shot_ev.get("player", {}).get("name") if shot_ev else None,
                "location.shot": _loc_str(shot_ev.get("location")) if shot_ev else None,
                "shot.statsbomb_xg": shot_data.get("statsbomb_xg"),
                "shot.freeze_frame": None,
                "shot.outcome.name": shot_data.get("outcome", {}).get("name") if shot_data.get("outcome") else None,
                "shot_x": float(sx) if sx is not None else None,
                "shot_y": float(sy) if sy is not None else None,
                "Metrics": None,
                "Occupation_Rating": 0,
                "Proximity_Rating": None,
                "Duel_Win_Prob": 0,
                "OPS_Opponent_Rating": 0,
                "Restart_Profile": None,
                "Start_Third": None,
                "Next_3_Box_Entry": False,
                "Next_3_Retain_Possession": False,
                "restart_x": float(px) if px is not None else None,
                "restart_y": float(py) if py is not None else None,
                "actions_checked": 0,
                "delivery_end_x": float(ex) if ex is not None else None,
                "delivery_end_y": float(ey) if ey is not None else None,
            })

    if not rows:
        return pd.DataFrame(), pd.DataFrame()

    df = pd.DataFrame(rows)
    df["match_id"] = df["match_id"].astype("int64")
    df["possession"] = df["possession"].astype("int64")
    df["Occupation_Rating"] = df["Occupation_Rating"].astype("int64")
    df["Duel_Win_Prob"] = df["Duel_Win_Prob"].astype("int64")
    df["OPS_Opponent_Rating"] = df["OPS_Opponent_Rating"].astype("int64")
    df["actions_checked"] = df["actions_checked"].astype("int64")
    for col in ("shot.statsbomb_xg", "shot_x", "shot_y",
                "restart_x", "restart_y", "delivery_end_x", "delivery_end_y"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    freekicks = df[df["SP_Type"] == "From Free Kick"].reset_index(drop=True)
    throwins  = df[df["SP_Type"] == "From Throw In"].reset_index(drop=True)
    return freekicks, throwins


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    print("Loading matches CSV …")
    matches_df = load_matches(args.matches)
    print(f"  {len(matches_df)} matches loaded")

    print("Loading JSON event files …")
    match_events = load_json_events(args.done)
    print(f"  {len(match_events)} match files loaded")

    print("Loading xG CSVs …")
    xg_data = load_xg_csvs(args.xgcsv)
    print(f"  {len(xg_data)} xG files loaded")

    # Corners
    print("Building corners …")
    corners_df = build_corners(match_events, matches_df)
    print(f"  {len(corners_df)} corner rows")

    # Freekicks + Throwins
    print("Building freekicks and throwins …")
    fk_df, ti_df = build_sp(match_events, matches_df)
    print(f"  {len(fk_df)} freekick rows, {len(ti_df)} throwin rows")

    # Save
    corners_dir = os.path.join(args.out, "Corners")
    sp_dir      = os.path.join(args.out, "SP")
    os.makedirs(corners_dir, exist_ok=True)
    os.makedirs(sp_dir,      exist_ok=True)

    corners_path = os.path.join(corners_dir, "Saudi Pro League - Corners 2025-2026.parquet")
    fk_path      = os.path.join(sp_dir,      "Saudi Pro League - Freekicks.parquet")
    ti_path      = os.path.join(sp_dir,      "Saudi Pro League - Throwins.parquet")

    corners_df.to_parquet(corners_path, engine="pyarrow", compression="zstd", index=False)
    fk_df.to_parquet(fk_path,           engine="pyarrow", compression="zstd", index=False)
    ti_df.to_parquet(ti_path,           engine="pyarrow", compression="zstd", index=False)

    print("\nDone! Files written:")
    for p in (corners_path, fk_path, ti_path):
        size = os.path.getsize(p) / 1024
        print(f"  {p}  ({size:.1f} KB)")


if __name__ == "__main__":
    main()
