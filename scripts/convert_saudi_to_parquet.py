"""
Convert Saudi Pro League Opta JSON events + CSV match metadata into parquet files
matching the repo's Corners, Freekicks and Throwins schemas.

Opta event conventions used:
  typeId=1 (Pass) + qualifier 6   → Corner kick
  typeId=1 (Pass) + qualifier 5   → Free kick
  typeId=1 (Pass) + qualifier 107 → Throw-in
  typeId=13/14/15/16              → Shots (on target / miss / attempt saved / blocked)
  qualifier 140 / 141             → pass end_x / end_y
  qualifier 103                   → xG (percentage string, divided by 100)
  qualifier 22                    → headed (presence = header)
  outcome field                   → 1 success, 0 failure

Usage (run on your local machine):
    python scripts/convert_saudi_to_parquet.py \\
        --done   "/Users/user/XG/Saudi/DONE" \\
        --xgcsv  "/xgCSV" \\
        --matches "/Users/user/XG/Saudi Matches.csv" \\
        --out    "/path/to/mm-setpieces-1/Data"

Outputs:
    Data/Corners/Saudi Pro League - Corners 2025-2026.parquet
    Data/SP/Saudi Pro League - Freekicks.parquet
    Data/SP/Saudi Pro League - Throwins.parquet
"""

import argparse
import json
import os
import glob
import re
from collections import defaultdict

import pandas as pd


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--done",    required=True, help="Dir with Opta JSON event files")
    p.add_argument("--xgcsv",  required=True, help="Dir with per-match metadata CSVs")
    p.add_argument("--matches", required=True, help="Saudi Matches.csv (match metadata)")
    p.add_argument("--out",     required=True, help="Root Data/ directory of the repo")
    p.add_argument("--shot-window", type=int, default=30,
                   help="Seconds after set piece to look for a linked shot (default 30)")
    return p.parse_args()


# ── Qualifier helpers ─────────────────────────────────────────────────────────

def get_q(event, qualifier_id, default=None):
    """Get value for a qualifier by ID."""
    for q in event.get("qualifier", []):
        if q["qualifierId"] == qualifier_id:
            return q.get("value", True)  # some qualifiers are flags with no value
    return default


def has_q(event, qualifier_id):
    return any(q["qualifierId"] == qualifier_id for q in event.get("qualifier", []))


# Opta qualifier IDs
Q_FREEKICK   = 5
Q_CORNER     = 6
Q_THROWIN    = 107
Q_END_X      = 140
Q_END_Y      = 141
Q_XG         = 103    # xG as percentage string (e.g. "6.9" → 0.069)
Q_ZONE       = 56     # pass direction zone: Back/Left/Right/Center
Q_HEADED     = 22     # flag: header
Q_CROSS      = 2      # flag: cross
Q_OUTSWING   = 224    # flag: outswinging corner
Q_INSWING    = 72     # flag: inswinging corner

# Shot typeIds
SHOT_TYPE_IDS = {13, 14, 15, 16}
SHOT_OUTCOME = {
    13: "Saved",
    14: "Off T",
    15: "Saved",
    16: "Blocked",
}


def _xg_from_event(ev):
    """Return xG float (0–1) from qualifier 103, or None."""
    raw = get_q(ev, Q_XG)
    if raw is None:
        return None
    try:
        return float(raw) / 100.0
    except (ValueError, TypeError):
        return None


def _timestamp_seconds(ev):
    """Return total seconds from period start using timeMin/timeSec."""
    return ev.get("timeMin", 0) * 60 + ev.get("timeSec", 0)


def _opta_x_to_sb(x):
    """Convert Opta 0-100 x to StatsBomb 0-120."""
    return round(float(x) * 1.2, 1) if x is not None else None


def _opta_y_to_sb(y):
    """Convert Opta 0-100 y to StatsBomb 0-80."""
    return round(float(y) * 0.8, 1) if y is not None else None


# ── Match metadata ────────────────────────────────────────────────────────────

def load_matches(path):
    """
    Load Saudi Matches.csv. Returns dict keyed by match_id with
    home_team_name, away_team_name, and any other columns.
    Tries common column name variants.
    """
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    rename = {}
    for c in df.columns:
        cl = c.lower().replace(" ", "_")
        if cl in ("match_id", "id", "matchid"):
            rename[c] = "match_id"
        elif "home" in cl and "team" in cl:
            rename[c] = "home_team_name"
        elif "away" in cl and "team" in cl:
            rename[c] = "away_team_name"
        elif "home_contestant" in cl or "home_id" in cl:
            rename[c] = "home_contestant_id"
        elif "away_contestant" in cl or "away_id" in cl:
            rename[c] = "away_contestant_id"
    df = df.rename(columns=rename)
    df["match_id"] = df["match_id"].astype(int)
    return df.set_index("match_id")


def load_xg_csvs(xgcsv_dir):
    """
    Load per-match CSVs from xgCSV directory.
    Returns dict {match_id: DataFrame}.
    """
    out = {}
    for fp in glob.glob(os.path.join(xgcsv_dir, "*.csv")):
        try:
            df = pd.read_csv(fp)
            df.columns = [c.strip() for c in df.columns]
            if "match_id" in df.columns:
                mid = int(df["match_id"].iloc[0])
            else:
                m = re.search(r"(\d{5,})", os.path.basename(fp))
                if not m:
                    print(f"  Warning: cannot determine match_id for {fp}")
                    continue
                mid = int(m.group(1))
            out[mid] = df
        except Exception as e:
            print(f"  Warning: could not read {fp}: {e}")
    return out


def _team_map_from_matches(match_id, matches_df):
    """
    Return dict {contestant_id: team_name} if matches_df has contestant IDs.
    Falls back to None if not available.
    """
    if match_id not in matches_df.index:
        return None
    row = matches_df.loc[match_id]
    mapping = {}
    if "home_contestant_id" in row.index and pd.notna(row.get("home_contestant_id")):
        mapping[str(row["home_contestant_id"])] = str(row["home_team_name"])
    if "away_contestant_id" in row.index and pd.notna(row.get("away_contestant_id")):
        mapping[str(row["away_contestant_id"])] = str(row["away_team_name"])
    return mapping or None


def _match_label(match_id, matches_df):
    if match_id not in matches_df.index:
        return str(match_id)
    row = matches_df.loc[match_id]
    home = row.get("home_team_name", "?")
    away = row.get("away_team_name", "?")
    return f"{home} - {away}"


# ── Possession builder ────────────────────────────────────────────────────────

def build_possessions(events):
    """
    Assign a possession number to each event by tracking team transitions.
    Returns list of possession ints, same length as events.
    """
    BREAK_TYPES = {30, 32, 34, 37, 40, 42, 68, 70}  # kickoff/period start/end etc.
    poss = []
    poss_num = 0
    last_team = None
    for ev in events:
        tid = ev.get("typeId")
        team = ev.get("contestantId")
        if tid in BREAK_TYPES or team is None:
            poss_num += 1
            last_team = None
        elif team != last_team and last_team is not None:
            poss_num += 1
            last_team = team
        else:
            last_team = team
        poss.append(poss_num)
    return poss


# ── Find linked shot ──────────────────────────────────────────────────────────

def find_linked_shot(events, sp_index, sp_poss, possessions, shot_window_secs):
    """
    Find the first shot event that occurs within shot_window_secs of the set piece
    AND belongs to the same possession (or the very next one within the window).
    Returns the shot event dict or None.
    """
    sp_ev = events[sp_index]
    sp_secs = _timestamp_seconds(sp_ev)
    sp_period = sp_ev.get("periodId")

    for i in range(sp_index + 1, len(events)):
        ev = events[i]
        if ev.get("periodId") != sp_period:
            break
        if _timestamp_seconds(ev) - sp_secs > shot_window_secs:
            break
        if ev["typeId"] in SHOT_TYPE_IDS:
            # Must be same possession or one after (immediate transition)
            if possessions[i] <= sp_poss + 1:
                return ev
    return None


# ── Opta → pass height ────────────────────────────────────────────────────────

def _pass_height(ev):
    """Derive rough pass height from qualifiers (Opta has no direct equivalent)."""
    if has_q(ev, Q_CROSS):
        return "High Pass"
    if has_q(ev, Q_HEADED):
        return "Low Pass"
    return None


def _technique(ev):
    """Derive corner technique from inswing/outswing qualifiers."""
    if has_q(ev, Q_INSWING):
        return "Inswinging"
    if has_q(ev, Q_OUTSWING):
        return "Outswinging"
    return None


def _body_part(ev):
    if has_q(ev, Q_HEADED):
        return "Head"
    return "Right Foot"  # Opta doesn't flag foot side on passes unless qualifier present


def _outcome_name(ev):
    return None if ev.get("outcome", 1) == 1 else "Incomplete"


def _team_name(ev, team_map):
    if team_map:
        return team_map.get(ev.get("contestantId"), ev.get("contestantId"))
    return ev.get("contestantId")


# ── Load JSON events ──────────────────────────────────────────────────────────

def load_json_events(done_dir, matches_df):
    """
    Load all Opta JSON files. Returns list of (match_id, team_map, events).
    match_id resolved from matches CSV (by team name) or filename.
    """
    result = []
    for fp in sorted(glob.glob(os.path.join(done_dir, "*.json"))):
        fname = os.path.basename(fp)
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  Warning: could not parse {fp}: {e}")
            continue

        events = data.get("event", data) if isinstance(data, dict) else data

        # Try to get match_id from filename
        mid_match = re.search(r"(\d{5,})", fname)
        if mid_match:
            match_id = int(mid_match.group(1))
        else:
            # Try to match by team names from filename
            # e.g. "20260506_Al_Ahli_FC__Al_Fateh_SC.json"
            match_id = _match_id_from_filename(fname, matches_df)

        if match_id is None:
            print(f"  Warning: cannot determine match_id for {fname}, skipping")
            continue

        # Build team map: contestantId → team name
        team_map = _team_map_from_matches(match_id, matches_df)
        if team_map is None:
            # Fall back: parse team names from filename
            team_map = _team_map_from_filename(fname, events, matches_df, match_id)

        result.append((match_id, team_map or {}, events))
        print(f"  Loaded {fname} → match_id={match_id}, {len(events)} events")
    return result


def _clean_team_name(s):
    return s.replace("_", " ").replace("  ", " ").strip()


def _match_id_from_filename(fname, matches_df):
    """
    Try to match filename team names against matches_df home/away columns.
    Filename format: YYYYMMDD_Home_Team__Away_Team.json
    """
    m = re.match(r"\d{8}_(.+?)__(.+?)\.json", fname)
    if not m:
        return None
    home_raw = _clean_team_name(m.group(1))
    away_raw = _clean_team_name(m.group(2))

    for mid, row in matches_df.iterrows():
        h = str(row.get("home_team_name", "")).strip()
        a = str(row.get("away_team_name", "")).strip()
        # Fuzzy: normalise by removing FC/SC/etc and lowercasing
        def norm(s): return re.sub(r'\b(fc|sc|afc|cf|united|city)\b', '', s.lower()).strip()
        if norm(home_raw) in norm(h) or norm(h) in norm(home_raw):
            if norm(away_raw) in norm(a) or norm(a) in norm(away_raw):
                return mid
    return None


def _team_map_from_filename(fname, events, matches_df, match_id):
    """
    Build {contestantId: team_name} from filename and the two unique contestantIds in events.
    """
    m = re.match(r"\d{8}_(.+?)__(.+?)\.json", fname)
    if not m:
        return {}
    home_name = _clean_team_name(m.group(1))
    away_name = _clean_team_name(m.group(2))

    # Find the two unique contestant IDs (excluding None)
    ids = [ev.get("contestantId") for ev in events if ev.get("contestantId")]
    from collections import Counter
    counts = Counter(ids)
    if len(counts) < 2:
        return {}
    top2 = [cid for cid, _ in counts.most_common(2)]

    # The home team typically kicks off - first real pass belongs to them
    # or just map in order (home=top2[0], away=top2[1])
    # Best effort: check matches_df if we have contestant IDs there
    if match_id in matches_df.index:
        row = matches_df.loc[match_id]
        hcid = str(row.get("home_contestant_id", ""))
        acid = str(row.get("away_contestant_id", ""))
        mapping = {}
        for cid in top2:
            if cid == hcid:
                mapping[cid] = str(row.get("home_team_name", home_name))
            elif cid == acid:
                mapping[cid] = str(row.get("away_team_name", away_name))
        if mapping:
            return mapping

    # Fallback: assign by order
    return {top2[0]: home_name, top2[1]: away_name}


# ── Build CORNERS ─────────────────────────────────────────────────────────────

def build_corners(all_match_events, matches_df, shot_window):
    rows = []
    for match_id, team_map, events in all_match_events:
        possessions = build_possessions(events)
        match_label = _match_label(match_id, matches_df)

        for i, ev in enumerate(events):
            if ev.get("typeId") != 1:
                continue
            if not has_q(ev, Q_CORNER):
                continue

            poss = possessions[i]
            x = ev.get("x")
            y = ev.get("y")
            end_x = get_q(ev, Q_END_X)
            end_y = get_q(ev, Q_END_Y)

            shot_ev = find_linked_shot(events, i, poss, possessions, shot_window)
            shot_xg = _xg_from_event(shot_ev) if shot_ev else None
            shot_outcome = SHOT_OUTCOME.get(shot_ev["typeId"]) if shot_ev else None

            rows.append({
                "match_id":            match_id,
                "Match":               match_label,
                "possession":          poss,
                "pass_timestamp":      f"{ev.get('timeMin', 0):02d}:{ev.get('timeSec', 0):02d}",
                "pass_team_name":      _team_name(ev, team_map),
                "Taker":               ev.get("playerName"),
                "pass_position":       get_q(ev, Q_ZONE),
                "pass.height.name":    _pass_height(ev),
                "pass.body_part.name": _body_part(ev),
                "pass.outcome.name":   _outcome_name(ev),
                "pass.technique.name": _technique(ev),
                "pass_location_x":     _opta_x_to_sb(x),
                "pass_location_y":     _opta_y_to_sb(y),
                "pass_end_location_x": _opta_x_to_sb(end_x),
                "pass_end_location_y": _opta_y_to_sb(end_y),
                "shot_timestamp":      (f"{shot_ev.get('timeMin',0):02d}:{shot_ev.get('timeSec',0):02d}"
                                        if shot_ev else None),
                "shot_team_name":      (_team_name(shot_ev, team_map) if shot_ev else None),
                "Shooter":             (shot_ev.get("playerName") if shot_ev else None),
                "shot_position":       (get_q(shot_ev, Q_ZONE) if shot_ev else None),
                "shot.body_part.name": ("Head" if shot_ev and has_q(shot_ev, Q_HEADED) else
                                        "Right Foot" if shot_ev else None),
                "shot.outcome.name":   shot_outcome,
                "shot.statsbomb_xg":   shot_xg,
                "shot_location_x":     (_opta_x_to_sb(shot_ev.get("x")) if shot_ev else None),
                "shot_location_y":     (_opta_y_to_sb(shot_ev.get("y")) if shot_ev else None),
                "shot_location_z":     None,
                "Defensive_setup":     "",
                "Minute":              ev.get("timeMin"),
                "Second":              ev.get("timeSec"),
                "SP_outcome":          ("" if ev.get("outcome", 1) == 1 else "Incomplete"),
            })

    if not rows:
        print("  WARNING: No corner rows found — check qualifier IDs in your data")
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["match_id"]   = df["match_id"].astype("int64")
    df["possession"] = df["possession"].astype("int64")
    df["Minute"]     = pd.array(df["Minute"].values, dtype=pd.Int64Dtype())
    df["Second"]     = pd.array(df["Second"].values, dtype=pd.Int64Dtype())
    for col in ("pass_location_x", "pass_location_y", "pass_end_location_x",
                "pass_end_location_y", "shot_location_x", "shot_location_y",
                "shot_location_z", "shot.statsbomb_xg"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ── Build SP (Freekicks / Throwins) ──────────────────────────────────────────

def build_sp(all_match_events, matches_df, shot_window):
    rows = []
    for match_id, team_map, events in all_match_events:
        possessions = build_possessions(events)

        for i, ev in enumerate(events):
            if ev.get("typeId") != 1:
                continue
            if has_q(ev, Q_FREEKICK):
                sp_type = "From Free Kick"
            elif has_q(ev, Q_THROWIN):
                sp_type = "From Throw In"
            else:
                continue

            poss = possessions[i]
            x = ev.get("x")
            y = ev.get("y")
            end_x_raw = get_q(ev, Q_END_X)
            end_y_raw = get_q(ev, Q_END_Y)

            sbx = _opta_x_to_sb(x)
            sby = _opta_y_to_sb(y)
            end_x = _opta_x_to_sb(end_x_raw)
            end_y = _opta_y_to_sb(end_y_raw)

            shot_ev = find_linked_shot(events, i, poss, possessions, shot_window)
            shot_xg = _xg_from_event(shot_ev) if shot_ev else None
            shot_outcome = SHOT_OUTCOME.get(shot_ev["typeId"]) if shot_ev else None
            shot_x = _opta_x_to_sb(shot_ev.get("x")) if shot_ev else None
            shot_y = _opta_y_to_sb(shot_ev.get("y")) if shot_ev else None

            rows.append({
                "match_id":                    match_id,
                "possession":                  poss,
                "team.name":                   _team_name(ev, team_map),
                "type.name":                   "Pass",
                "SP_Type":                     sp_type,
                "location.pass":               (f"{sbx}, {sby}" if sbx is not None else None),
                "pass.height.name":            _pass_height(ev),
                "timestamp":                   f"{ev.get('timeMin', 0):02d}:{ev.get('timeSec', 0):02d}",
                "Taker":                       ev.get("playerName"),
                "Shooter":                     (shot_ev.get("playerName") if shot_ev else None),
                "location.shot":               (f"{shot_x}, {shot_y}" if shot_x is not None else None),
                "shot.statsbomb_xg":           shot_xg,
                "shot.freeze_frame":           None,
                "shot.outcome.name":           shot_outcome,
                "shot_x":                      shot_x,
                "shot_y":                      shot_y,
                "Metrics":                     None,
                "Occupation_Rating":           0,
                "Proximity_Rating":            None,
                "Duel_Win_Prob":               0,
                "OPS_Opponent_Rating":         0,
                "Restart_Profile":             None,
                "Start_Third":                 _start_third(sbx),
                "Next_3_Box_Entry":            False,
                "Next_3_Retain_Possession":    False,
                "restart_x":                   sbx,
                "restart_y":                   sby,
                "actions_checked":             0,
                "delivery_end_x":              end_x,
                "delivery_end_y":              end_y,
            })

    if not rows:
        print("  WARNING: No freekick/throwin rows found — check qualifier IDs")
        return pd.DataFrame(), pd.DataFrame()

    df = pd.DataFrame(rows)
    df["match_id"]           = df["match_id"].astype("int64")
    df["possession"]         = df["possession"].astype("int64")
    df["Occupation_Rating"]  = df["Occupation_Rating"].astype("int64")
    df["Duel_Win_Prob"]      = df["Duel_Win_Prob"].astype("int64")
    df["OPS_Opponent_Rating"]= df["OPS_Opponent_Rating"].astype("int64")
    df["actions_checked"]    = df["actions_checked"].astype("int64")
    for col in ("shot.statsbomb_xg", "shot_x", "shot_y",
                "restart_x", "restart_y", "delivery_end_x", "delivery_end_y"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    freekicks = df[df["SP_Type"] == "From Free Kick"].reset_index(drop=True)
    throwins  = df[df["SP_Type"] == "From Throw In"].reset_index(drop=True)
    return freekicks, throwins


def _start_third(x):
    """Classify start third from StatsBomb x coordinate (0–120)."""
    if x is None:
        return None
    if x < 40:
        return "Defensive third"
    if x < 80:
        return "Middle third"
    return "Attacking third"


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    print("Loading matches CSV …")
    matches_df = load_matches(args.matches)
    print(f"  {len(matches_df)} matches")

    print("Loading xG/metadata CSVs …")
    xg_data = load_xg_csvs(args.xgcsv)
    print(f"  {len(xg_data)} CSV files")

    print("Loading JSON event files …")
    all_match_events = load_json_events(args.done, matches_df)
    print(f"  {len(all_match_events)} matches loaded")

    if not all_match_events:
        print("ERROR: No event files could be loaded. Check --done path and match IDs.")
        return

    print(f"\nBuilding corners (shot window={args.shot_window}s) …")
    corners_df = build_corners(all_match_events, matches_df, args.shot_window)
    print(f"  {len(corners_df)} corner rows")

    print("Building freekicks and throwins …")
    fk_df, ti_df = build_sp(all_match_events, matches_df, args.shot_window)
    print(f"  {len(fk_df)} freekick rows, {len(ti_df)} throwin rows")

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
