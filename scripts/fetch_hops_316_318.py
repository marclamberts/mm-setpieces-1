"""
Fetch HOPS data for all competitions in season_id 316 and 318.
Run this on your local machine (StatsBomb API is IP-restricted).

Usage:
    python scripts/fetch_hops_316_318.py

Outputs one parquet per competition to Data/HOPS/, e.g.:
    "Premier League 318 HOPS.parquet"
    "Bundesliga 316 HOPS.parquet"
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd
from statsbombpy import sb

# ── Config ────────────────────────────────────────────────────────────────────
ACCOUNTS = [
    {"user": "m.pulley@az.nl",         "passwd": "SwHrVcks"},
    {"user": "JACK71299@HOTMAIL.CO.UK", "passwd": "J7rB7aP2"},
]

TARGET_SEASON_IDS = [316, 318]
MAX_WORKERS       = 8

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "Data" / "HOPS"

KEEP_COLS = ["player", "player_name", "team", "team_name", "duel_hops_rating", "match_id"]

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg: str) -> None:
    print(msg, flush=True)


def try_accounts(func: Callable[..., Any], *args, **kwargs) -> Any:
    for idx, creds in enumerate(ACCOUNTS, 1):
        try:
            result = func(*args, creds=creds, **kwargs)
            if isinstance(result, pd.DataFrame) and not result.empty:
                return result
            if isinstance(result, list) and result:
                return result
            if result is not None:
                return result
        except Exception as e:
            log(f"  Account {idx} failed ({func.__name__}): {e}")
    return None


def slim_events(match_id: int) -> Optional[pd.DataFrame]:
    raw = try_accounts(sb.events, match_id=int(match_id))
    if raw is None or (isinstance(raw, pd.DataFrame) and raw.empty):
        return None
    if not isinstance(raw, pd.DataFrame):
        try:
            raw = pd.DataFrame(raw)
        except Exception:
            return None
    keep = [c for c in KEEP_COLS if c in raw.columns]
    slim = raw[keep].copy()
    if "match_id" not in slim.columns:
        slim["match_id"] = match_id
    return slim


def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\t]', '', name).strip()


def process_competition(comp_id: int, season_id: int, comp_name: str) -> tuple[str, int | str]:
    """Fetch, aggregate, and save one competition's HOPS data. Returns (status, count)."""
    out_path = OUTPUT_DIR / f"{safe_filename(comp_name)} {season_id} HOPS.parquet"
    if out_path.exists():
        log(f"  [skip] {out_path.name} already exists")
        return "skipped", 0

    # 1) matches
    matches = try_accounts(sb.matches, competition_id=comp_id, season_id=season_id)
    if matches is None or (isinstance(matches, pd.DataFrame) and matches.empty):
        return "no_matches", 0

    match_ids = matches["match_id"].dropna().astype(int).unique().tolist()
    if not match_ids:
        return "no_matches", 0

    # 2) slim events (parallel)
    frames = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(slim_events, mid): mid for mid in match_ids}
        for fut in as_completed(futures):
            try:
                df = fut.result()
                if df is not None and not df.empty:
                    frames.append(df)
            except Exception:
                pass

    if not frames:
        return "no_events", 0

    events = pd.concat(frames, ignore_index=True)

    # 3) aggregate
    player_col = next((c for c in ["player", "player_name"] if c in events.columns), None)
    team_col   = next((c for c in ["team",   "team_name"]   if c in events.columns), None)
    if player_col is None or team_col is None or "duel_hops_rating" not in events.columns:
        return "no_hops_col", 0

    df = events[[player_col, team_col, "duel_hops_rating"]].copy()
    df["duel_hops_rating"] = pd.to_numeric(df["duel_hops_rating"], errors="coerce")
    df = df.dropna(subset=[player_col, team_col, "duel_hops_rating"])
    df = df[df[player_col].astype(str).str.strip().ne("") & df[team_col].astype(str).str.strip().ne("")]
    if df.empty:
        return "no_hops_data", 0

    agg = (
        df.groupby([player_col, team_col], as_index=False)
        .agg(Rating=("duel_hops_rating", "mean"))
        .rename(columns={player_col: "Player", team_col: "Team"})
        .sort_values("Rating", ascending=False)
        .reset_index(drop=True)
    )[["Player", "Team", "Rating"]]

    # 4) save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        agg.to_parquet(out_path, engine="fastparquet", index=False, compression="zstd")
    except Exception:
        agg.to_parquet(out_path, engine="pyarrow", index=False)

    return "ok", len(agg)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    if not ACCOUNTS:
        raise SystemExit("No credentials configured.")

    # Load competitions list
    comps_path = Path(__file__).resolve().parent.parent / "Data" / "competitions.csv"
    if comps_path.exists():
        all_comps = pd.read_csv(comps_path)
    else:
        # fallback: fetch from StatsBomb
        log("Fetching competitions from StatsBomb...")
        all_comps = try_accounts(sb.competitions)
        if all_comps is None:
            raise SystemExit("Could not load competitions — check credentials / connectivity.")

    targets = all_comps[all_comps["season_id"].isin(TARGET_SEASON_IDS)].copy()
    targets = targets.drop_duplicates(subset=["competition_id", "season_id"])
    log(f"Competitions to process: {len(targets)} (seasons {TARGET_SEASON_IDS})\n")

    ok_count = skipped = failed = 0

    for _, row in targets.iterrows():
        comp_id   = int(row["competition_id"])
        season_id = int(row["season_id"])
        comp_name = str(row.get("competition_name", f"Competition_{comp_id}"))
        log(f"→ [{season_id}] {comp_name} (comp={comp_id})")
        status, n = process_competition(comp_id, season_id, comp_name)
        if status == "ok":
            log(f"  ✓ saved {n} players")
            ok_count += 1
        elif status == "skipped":
            skipped += 1
        else:
            log(f"  ✗ {status}")
            failed += 1

    log(f"\n{'='*50}")
    log(f"Done — saved: {ok_count}  |  skipped: {skipped}  |  failed/empty: {failed}")
    log(f"Files in {OUTPUT_DIR}:")
    for f in sorted(OUTPUT_DIR.glob("*.parquet")):
        log(f"  {f.name}")


if __name__ == "__main__":
    main()
