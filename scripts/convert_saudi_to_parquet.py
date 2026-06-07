"""
Convert Saudi Pro League Opta JSON events + Saudi Matches.csv into parquet files
matching the repo's Corners, Freekicks and Throwins schemas.

Saudi Matches.csv columns used:
  matchInfo/id                    → Opta match ID (alphanumeric)
  matchInfo/contestant/0/id       → home contestant ID
  matchInfo/contestant/0/name     → home team name
  matchInfo/contestant/0/position → "home"
  matchInfo/contestant/1/id       → away contestant ID
  matchInfo/contestant/1/name     → away team name

Opta event conventions:
  typeId=1 + qualifier 6   → Corner kick
  typeId=1 + qualifier 5   → Free kick
  typeId=1 + qualifier 107 → Throw-in
  typeId=13/14/15          → Shot (on target / miss / attempt saved)
  qualifier 140 / 141      → pass end_x / end_y
  qualifier 103            → xG (percentage string, divide by 100)
  qualifier 22             → headed (flag)
  qualifier 72 / 224       → inswinging / outswinging corner

Usage (run on your local machine):
    python scripts/convert_saudi_to_parquet.py

Outputs:
    Data/Corners/Saudi Pro League - Corners 2025-2026.parquet
    Data/SP/Saudi Pro League - Freekicks.parquet
    Data/SP/Saudi Pro League - Throwins.parquet
"""

import json
import os
import glob
import re
import zlib
from collections import Counter
from pathlib import Path

import pandas as pd


BASE       = Path("/Users/user/XG/Saudi")
DONE_DIR   = BASE / "DONE"
XGCSV_DIR  = BASE / "xgCSV"
MATCHES_CSV = BASE / "Saudi Matches.csv"
OUT_DIR    = Path("/Users/user/Documents/GitHub/mm-setpieces-1/Data")
SHOT_WINDOW = 30  # seconds after set piece to look for a linked shot


# ── Qualifier helpers ─────────────────────────────────────────────────────────

def get_q(event, qualifier_id, default=None):
    for q in event.get("qualifier", []):
        if q["qualifierId"] == qualifier_id:
            return q.get("value", True)
    return default


def has_q(event, qualifier_id):
    return any(q["qualifierId"] == qualifier_id for q in event.get("qualifier", []))


Q_FREEKICK = 5
Q_CORNER   = 6
Q_THROWIN  = 107
Q_END_X    = 140
Q_END_Y    = 141
Q_XG       = 103
Q_ZONE     = 56
Q_HEADED   = 22
Q_INSWING  = 72
Q_OUTSWING = 224

SHOT_TYPE_IDS = {13, 14, 15, 16}
SHOT_OUTCOME_MAP = {13: "Saved", 14: "Off T", 15: "Saved", 16: "Blocked"}


def _opta_id_to_int(opta_id: str) -> int:
    """Convert Opta alphanumeric match ID to a stable integer using CRC32."""
    return zlib.crc32(opta_id.encode()) & 0x7FFFFFFF


def _xg(ev):
    raw = get_q(ev, Q_XG)
    if raw is None:
        return None
    try:
        return round(float(raw) / 100.0, 4)
    except (ValueError, TypeError):
        return None


def _secs(ev):
    return ev.get("timeMin", 0) * 60 + ev.get("timeSec", 0)


def _to_sb_x(v):
    """Opta 0–100 → StatsBomb 0–120."""
    return round(float(v) * 1.2, 1) if v is not None else None


def _to_sb_y(v):
    """Opta 0–100 → StatsBomb 0–80."""
    return round(float(v) * 0.8, 1) if v is not None else None


def _norm(name: str) -> str:
    """Normalise team name for fuzzy matching."""
    return re.sub(r'\b(fc|sc|afc|cf|club|united|city|al)\b', '',
                  name.lower()).strip()


# ── Load Saudi Matches.csv ────────────────────────────────────────────────────

def load_matches(path):
    """
    Returns a dict keyed by Opta match ID string:
    {
      opta_id:  str,
      match_id: int (CRC32),
      home_name: str,
      away_name: str,
      home_cid:  str,
      away_cid:  str,
    }
    Also a lookup: {contestant_id → team_name} across all matches.
    """
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]

    matches = {}
    contestant_to_team = {}

    for _, row in df.iterrows():
        opta_id   = str(row.get("matchInfo/id", "")).strip()
        home_name = str(row.get("matchInfo/contestant/0/name", "")).strip()
        away_name = str(row.get("matchInfo/contestant/1/name", "")).strip()
        home_cid  = str(row.get("matchInfo/contestant/0/id", "")).strip()
        away_cid  = str(row.get("matchInfo/contestant/1/id", "")).strip()
        home_pos  = str(row.get("matchInfo/contestant/0/position", "home")).strip()

        # If contestant/0 is actually "away", swap
        if home_pos == "away":
            home_name, away_name = away_name, home_name
            home_cid,  away_cid  = away_cid,  home_cid

        if not opta_id:
            continue

        matches[opta_id] = {
            "opta_id":   opta_id,
            "match_id":  _opta_id_to_int(opta_id),
            "home_name": home_name,
            "away_name": away_name,
            "home_cid":  home_cid,
            "away_cid":  away_cid,
            "label":     f"{home_name} - {away_name}",
        }
        contestant_to_team[home_cid] = home_name
        contestant_to_team[away_cid] = away_name

    print(f"  {len(matches)} matches, {len(contestant_to_team)} contestant IDs")
    return matches, contestant_to_team


def _match_by_teams(fname, matches_by_id):
    """
    Match filename like '20260506_Al_Ahli_FC__Al_Fateh_SC.json'
    against match records by normalised team name comparison.
    """
    m = re.search(r"\d{8}_(.+?)__(.+?)\.json", fname)
    if not m:
        return None
    raw_home = _norm(m.group(1).replace("_", " "))
    raw_away = _norm(m.group(2).replace("_", " "))

    best = None
    for mid, rec in matches_by_id.items():
        nh = _norm(rec["home_name"])
        na = _norm(rec["away_name"])
        if (raw_home in nh or nh in raw_home) and (raw_away in na or na in raw_away):
            best = rec
            break
    return best


# ── Load JSON events ──────────────────────────────────────────────────────────

def load_json_events(done_dir, matches_by_id, contestant_to_team):
    """
    Returns list of dicts:
      { match_rec, team_map, events }
    """
    result = []
    for fp in sorted(glob.glob(os.path.join(str(done_dir), "*.json"))):
        fname = os.path.basename(fp)
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  Warning: cannot parse {fp}: {e}")
            continue

        events = data.get("event", data) if isinstance(data, dict) else data
        if not events:
            continue

        # Resolve match record
        match_rec = _match_by_teams(fname, matches_by_id)
        if match_rec is None:
            print(f"  Warning: no match found for {fname} — skipping")
            continue

        # Build local team map from match record contestant IDs
        team_map = {
            match_rec["home_cid"]: match_rec["home_name"],
            match_rec["away_cid"]: match_rec["away_name"],
        }
        # Supplement with global contestant lookup for safety
        team_map = {**contestant_to_team, **team_map}

        print(f"  {fname} → {match_rec['label']} (match_id={match_rec['match_id']})")
        result.append({"match_rec": match_rec, "team_map": team_map, "events": events})

    return result


# ── Possession tracker ────────────────────────────────────────────────────────

BREAK_TYPES = {30, 32, 34, 37, 40, 42, 68, 70}

def build_possessions(events):
    poss_num = 0
    last_team = None
    out = []
    for ev in events:
        team = ev.get("contestantId")
        if ev.get("typeId") in BREAK_TYPES or team is None:
            poss_num += 1
            last_team = None
        elif team != last_team and last_team is not None:
            poss_num += 1
            last_team = team
        else:
            last_team = team
        out.append(poss_num)
    return out


# ── Find linked shot ──────────────────────────────────────────────────────────

def find_linked_shot(events, sp_index, sp_poss, possessions, window_secs):
    sp_ev     = events[sp_index]
    sp_secs   = _secs(sp_ev)
    sp_period = sp_ev.get("periodId")

    for i in range(sp_index + 1, len(events)):
        ev = events[i]
        if ev.get("periodId") != sp_period:
            break
        if _secs(ev) - sp_secs > window_secs:
            break
        if ev["typeId"] in SHOT_TYPE_IDS and possessions[i] <= sp_poss + 1:
            return ev
    return None


# ── Derived fields ────────────────────────────────────────────────────────────

def _team_name(ev, team_map):
    return team_map.get(ev.get("contestantId"), ev.get("contestantId", ""))


def _pass_height(ev):
    if has_q(ev, Q_CORNER) or has_q(ev, 2):   # 2 = cross
        return "High Pass"
    return None


def _technique(ev):
    if has_q(ev, Q_INSWING):
        return "Inswinging"
    if has_q(ev, Q_OUTSWING):
        return "Outswinging"
    return None


def _body_part(ev):
    return "Head" if has_q(ev, Q_HEADED) else "Right Foot"


def _outcome_name(ev):
    return None if ev.get("outcome", 1) == 1 else "Incomplete"


def _start_third(sb_x):
    if sb_x is None:
        return None
    if sb_x < 40:
        return "Defensive third"
    if sb_x < 80:
        return "Middle third"
    return "Attacking third"


# ── Build CORNERS ─────────────────────────────────────────────────────────────

def build_corners(all_matches, shot_window):
    rows = []
    for m in all_matches:
        rec     = m["match_rec"]
        team_map = m["team_map"]
        events  = m["events"]
        poss    = build_possessions(events)

        for i, ev in enumerate(events):
            if ev.get("typeId") != 1 or not has_q(ev, Q_CORNER):
                continue

            sbx = _to_sb_x(ev.get("x"))
            sby = _to_sb_y(ev.get("y"))
            ex  = _to_sb_x(get_q(ev, Q_END_X))
            ey  = _to_sb_y(get_q(ev, Q_END_Y))

            shot = find_linked_shot(events, i, poss[i], poss, shot_window)
            rows.append({
                "match_id":            rec["match_id"],
                "Match":               rec["label"],
                "possession":          poss[i],
                "pass_timestamp":      f"{ev.get('timeMin',0):02d}:{ev.get('timeSec',0):02d}",
                "pass_team_name":      _team_name(ev, team_map),
                "Taker":               ev.get("playerName"),
                "pass_position":       get_q(ev, Q_ZONE),
                "pass.height.name":    _pass_height(ev),
                "pass.body_part.name": _body_part(ev),
                "pass.outcome.name":   _outcome_name(ev),
                "pass.technique.name": _technique(ev),
                "pass_location_x":     sbx,
                "pass_location_y":     sby,
                "pass_end_location_x": ex,
                "pass_end_location_y": ey,
                "shot_timestamp":      (f"{shot.get('timeMin',0):02d}:{shot.get('timeSec',0):02d}" if shot else None),
                "shot_team_name":      (_team_name(shot, team_map) if shot else None),
                "Shooter":             (shot.get("playerName") if shot else None),
                "shot_position":       (get_q(shot, Q_ZONE) if shot else None),
                "shot.body_part.name": ("Head" if shot and has_q(shot, Q_HEADED) else "Right Foot" if shot else None),
                "shot.outcome.name":   (SHOT_OUTCOME_MAP.get(shot["typeId"]) if shot else None),
                "shot.statsbomb_xg":   (_xg(shot) if shot else None),
                "shot_location_x":     (_to_sb_x(shot.get("x")) if shot else None),
                "shot_location_y":     (_to_sb_y(shot.get("y")) if shot else None),
                "shot_location_z":     None,
                "Defensive_setup":     "",
                "Minute":              ev.get("timeMin"),
                "Second":              ev.get("timeSec"),
                "SP_outcome":          ("" if ev.get("outcome", 1) == 1 else "Incomplete"),
            })

    if not rows:
        print("  WARNING: 0 corner rows — check qualifier IDs match your Opta feed")
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["match_id"]   = df["match_id"].astype("int64")
    df["possession"] = df["possession"].astype("int64")
    df["Minute"]     = pd.array(df["Minute"].values, dtype=pd.Int64Dtype())
    df["Second"]     = pd.array(df["Second"].values, dtype=pd.Int64Dtype())
    for col in ("pass_location_x","pass_location_y","pass_end_location_x","pass_end_location_y",
                "shot_location_x","shot_location_y","shot_location_z","shot.statsbomb_xg"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ── Build SP (Freekicks / Throwins) ──────────────────────────────────────────

def build_sp(all_matches, shot_window):
    rows = []
    for m in all_matches:
        rec      = m["match_rec"]
        team_map = m["team_map"]
        events   = m["events"]
        poss     = build_possessions(events)

        for i, ev in enumerate(events):
            if ev.get("typeId") != 1:
                continue
            if has_q(ev, Q_FREEKICK):
                sp_type = "From Free Kick"
            elif has_q(ev, Q_THROWIN):
                sp_type = "From Throw In"
            else:
                continue

            sbx = _to_sb_x(ev.get("x"))
            sby = _to_sb_y(ev.get("y"))
            ex  = _to_sb_x(get_q(ev, Q_END_X))
            ey  = _to_sb_y(get_q(ev, Q_END_Y))

            shot = find_linked_shot(events, i, poss[i], poss, shot_window)
            sx = _to_sb_x(shot.get("x")) if shot else None
            sy = _to_sb_y(shot.get("y")) if shot else None

            rows.append({
                "match_id":                 rec["match_id"],
                "possession":               poss[i],
                "team.name":                _team_name(ev, team_map),
                "type.name":                "Pass",
                "SP_Type":                  sp_type,
                "location.pass":            (f"{sbx}, {sby}" if sbx is not None else None),
                "pass.height.name":         _pass_height(ev),
                "timestamp":                f"{ev.get('timeMin',0):02d}:{ev.get('timeSec',0):02d}",
                "Taker":                    ev.get("playerName"),
                "Shooter":                  (shot.get("playerName") if shot else None),
                "location.shot":            (f"{sx}, {sy}" if sx is not None else None),
                "shot.statsbomb_xg":        (_xg(shot) if shot else None),
                "shot.freeze_frame":        None,
                "shot.outcome.name":        (SHOT_OUTCOME_MAP.get(shot["typeId"]) if shot else None),
                "shot_x":                   sx,
                "shot_y":                   sy,
                "Metrics":                  None,
                "Occupation_Rating":        0,
                "Proximity_Rating":         None,
                "Duel_Win_Prob":            0,
                "OPS_Opponent_Rating":      0,
                "Restart_Profile":          None,
                "Start_Third":              _start_third(sbx),
                "Next_3_Box_Entry":         False,
                "Next_3_Retain_Possession": False,
                "restart_x":                sbx,
                "restart_y":                sby,
                "actions_checked":          0,
                "delivery_end_x":           ex,
                "delivery_end_y":           ey,
            })

    if not rows:
        print("  WARNING: 0 SP rows — check qualifier IDs match your Opta feed")
        return pd.DataFrame(), pd.DataFrame()

    df = pd.DataFrame(rows)
    df["match_id"]            = df["match_id"].astype("int64")
    df["possession"]          = df["possession"].astype("int64")
    df["Occupation_Rating"]   = df["Occupation_Rating"].astype("int64")
    df["Duel_Win_Prob"]       = df["Duel_Win_Prob"].astype("int64")
    df["OPS_Opponent_Rating"] = df["OPS_Opponent_Rating"].astype("int64")
    df["actions_checked"]     = df["actions_checked"].astype("int64")
    for col in ("shot.statsbomb_xg","shot_x","shot_y","restart_x","restart_y",
                "delivery_end_x","delivery_end_y"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    fk = df[df["SP_Type"] == "From Free Kick"].reset_index(drop=True)
    ti = df[df["SP_Type"] == "From Throw In"].reset_index(drop=True)
    return fk, ti


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Loading Saudi Matches.csv …")
    matches_by_id, contestant_to_team = load_matches(MATCHES_CSV)

    print("Loading JSON event files …")
    all_matches = load_json_events(DONE_DIR, matches_by_id, contestant_to_team)
    print(f"  {len(all_matches)} matches loaded\n")

    if not all_matches:
        print("ERROR: No event files matched. Check team names in filenames vs CSV.")
        return

    print(f"Building corners (shot window={SHOT_WINDOW}s) …")
    corners_df = build_corners(all_matches, SHOT_WINDOW)
    print(f"  {len(corners_df)} rows")

    print("Building freekicks and throwins …")
    fk_df, ti_df = build_sp(all_matches, SHOT_WINDOW)
    print(f"  {len(fk_df)} freekick rows, {len(ti_df)} throwin rows\n")

    corners_dir = OUT_DIR / "Corners"
    sp_dir      = OUT_DIR / "SP"
    corners_dir.mkdir(parents=True, exist_ok=True)
    sp_dir.mkdir(parents=True, exist_ok=True)

    corners_path = corners_dir / "Saudi Pro League - Corners 2025-2026.parquet"
    fk_path      = sp_dir      / "Saudi Pro League - Freekicks.parquet"
    ti_path      = sp_dir      / "Saudi Pro League - Throwins.parquet"

    corners_df.to_parquet(corners_path, engine="pyarrow", compression="zstd", index=False)
    fk_df.to_parquet(fk_path,           engine="pyarrow", compression="zstd", index=False)
    ti_df.to_parquet(ti_path,           engine="pyarrow", compression="zstd", index=False)

    print("Files written:")
    for p in (corners_path, fk_path, ti_path):
        print(f"  {p}  ({os.path.getsize(p)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
