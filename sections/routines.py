"""Routines Playbook — save, tag and review set piece routines."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import streamlit as st
import pandas as pd

from mm_setpieces_1.utils import (
    hero_block,
    section_header,
    DATA_VERSION,
    load_prepared_sp_data,
    load_prepared_freekick_brief_data,
)
from sections._shared import _safe_sorted, _with_match_names

ROUTINES_FILE = Path(__file__).resolve().parent.parent / "routines.json"

SP_TYPES  = ["Corner", "Free Kick", "Throw-in", "General"]
PHASES    = ["Attack", "Defend", "Both"]
OUTCOMES  = ["Goal", "Shot", "Chance", "Possession Win", "Transition", "Other"]


# ── Persistence ────────────────────────────────────────────────────────────

def _load_routines() -> list[dict]:
    if not ROUTINES_FILE.exists():
        return []
    try:
        return json.loads(ROUTINES_FILE.read_text())
    except Exception:
        return []


def _save_routines(routines: list[dict]) -> None:
    ROUTINES_FILE.write_text(json.dumps(routines, indent=2))


# ── Team name helpers ───────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading data…")
def _all_teams(_dv: str = DATA_VERSION) -> list[str]:
    teams: set[str] = set()
    for df in [
        _with_match_names(load_prepared_sp_data("Corners",   _dv)),
        _with_match_names(load_prepared_freekick_brief_data( _dv)),
        _with_match_names(load_prepared_sp_data("Throw ins", _dv)),
    ]:
        if not df.empty and "Team" in df.columns:
            teams.update(df["Team"].dropna().astype(str).unique())
    teams.discard("Unknown")
    return sorted(teams)


# ── Render helpers ──────────────────────────────────────────────────────────

_TYPE_ICONS = {"Corner": "⚽", "Free Kick": "🎯", "Throw-in": "↗", "General": "📋"}
_PHASE_COLOURS = {"Attack": "#22c55e", "Defend": "#3b82f6", "Both": "#f59e0b"}


def _routine_card(r: dict, idx: int) -> None:
    icon    = _TYPE_ICONS.get(r.get("sp_type", "General"), "📋")
    colour  = _PHASE_COLOURS.get(r.get("phase", "Attack"), "#22c55e")
    tags_html = "".join(
        f'<span style="background:rgba(255,255,255,.08);border-radius:4px;'
        f'padding:1px 7px;font-size:.72rem;margin-right:4px">{t}</span>'
        for t in r.get("tags", [])
    )
    match_ref = r.get("match_ref", "")
    match_line = (
        f'<div style="font-size:.72rem;color:#64748b;margin-top:.3rem">📎 {match_ref}</div>'
        if match_ref else ""
    )
    st.markdown(
        f"""<div style="background:#161922;border:1px solid rgba(255,255,255,.08);
            border-left:3px solid {colour};border-radius:6px;
            padding:.8rem 1rem .7rem;margin-bottom:.6rem">
            <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.3rem">
                <span style="font-size:1.1rem">{icon}</span>
                <span style="font-weight:700;font-size:.95rem">{r.get("name","Unnamed")}</span>
                <span style="font-size:.72rem;color:#94a3b8;margin-left:auto">{r.get("team","")}</span>
            </div>
            <div style="font-size:.8rem;color:#94a3b8;margin-bottom:.4rem">
                {r.get("sp_type","—")} · {r.get("phase","—")} · {r.get("outcome","")}
            </div>
            <div style="font-size:.85rem;color:#cbd5e1;white-space:pre-wrap">{r.get("description","")}</div>
            {tags_html}
            {match_line}
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("🗑 Delete", key=f"del_routine_{idx}_{r['id']}", help="Delete this routine"):
        routines = _load_routines()
        routines = [x for x in routines if x["id"] != r["id"]]
        _save_routines(routines)
        st.rerun()


# ── Main render ─────────────────────────────────────────────────────────────

def render_routines() -> None:
    routines = _load_routines()
    hero_block("📖", "Routines Playbook", f"{len(routines):,} saved routines")
    st.session_state["ctx_row_count"] = f"Routines · {len(routines):,}"

    # ── Add routine ─────────────────────────────────────────────────────
    with st.expander("➕ Add new routine", expanded=(len(routines) == 0)):
        teams = [""] + _all_teams(DATA_VERSION)

        af1, af2, af3 = st.columns(3)
        with af1:
            r_name = st.text_input("Routine name *", key="r_name",
                                   placeholder="e.g. Near-post flick-on")
        with af2:
            r_team = st.selectbox("Team", teams, key="r_team")
        with af3:
            r_sp_type = st.selectbox("Type", SP_TYPES, key="r_sp_type")

        af4, af5, af6 = st.columns(3)
        with af4:
            r_phase = st.selectbox("Phase", PHASES, key="r_phase")
        with af5:
            r_outcome = st.selectbox("Typical outcome", OUTCOMES, key="r_outcome")
        with af6:
            r_match_ref = st.text_input("Match reference", key="r_match_ref",
                                        placeholder="e.g. Arsenal vs Chelsea 2-1 (45')")

        r_description = st.text_area(
            "Description / setup notes *",
            key="r_description",
            height=110,
            placeholder=(
                "Describe the routine: which players, movement patterns, "
                "trigger cues, delivery zone, blocking assignments…"
            ),
        )
        r_tags_raw = st.text_input(
            "Tags (comma-separated)",
            key="r_tags",
            placeholder="e.g. near-post, flick-on, 2-man-block",
        )

        if st.button("Save routine", key="r_save", type="primary"):
            if not r_name.strip() or not r_description.strip():
                st.error("Name and description are required.")
            else:
                tags = [t.strip() for t in r_tags_raw.split(",") if t.strip()]
                new = {
                    "id":          str(uuid.uuid4()),
                    "created_at":  int(time.time()),
                    "name":        r_name.strip(),
                    "team":        r_team,
                    "sp_type":     r_sp_type,
                    "phase":       r_phase,
                    "outcome":     r_outcome,
                    "match_ref":   r_match_ref.strip(),
                    "description": r_description.strip(),
                    "tags":        tags,
                }
                routines.append(new)
                _save_routines(routines)
                st.success("Routine saved!")
                st.rerun()

    # ── Export / Import ─────────────────────────────────────────────────
    with st.expander("📤 Export / Import routines", expanded=False):
        ei1, ei2 = st.columns(2)
        with ei1:
            st.caption("**Export** — download all routines as JSON")
            if routines:
                st.download_button(
                    "⬇ Download routines.json",
                    data=json.dumps(routines, indent=2),
                    file_name="routines_export.json",
                    mime="application/json",
                    use_container_width=True,
                    key="r_export",
                )
            else:
                st.info("No routines to export yet.")
        with ei2:
            st.caption("**Import** — upload a previously exported JSON file")
            uploaded = st.file_uploader("Upload routines JSON", type=["json"], key="r_import",
                                        label_visibility="collapsed")
            if uploaded is not None:
                try:
                    imported = json.loads(uploaded.read())
                    if not isinstance(imported, list):
                        st.error("Invalid format — expected a JSON array.")
                    else:
                        existing_ids = {r.get("id") for r in routines}
                        new_items = [r for r in imported if r.get("id") not in existing_ids]
                        if new_items:
                            routines = routines + new_items
                            _save_routines(routines)
                            st.success(f"Imported {len(new_items)} new routine{'s' if len(new_items) != 1 else ''}.")
                            st.rerun()
                        else:
                            st.info("All routines in that file already exist.")
                except Exception as exc:
                    st.error(f"Could not parse file: {exc}")

    if not routines:
        st.info("No routines yet. Add your first one above.")
        return

    # ── Filters ─────────────────────────────────────────────────────────
    with st.container():
        st.markdown('<div class="mm-filter-panel"><div class="mm-filter-panel-label">Filters</div>', unsafe_allow_html=True)
        rf1, rf2, rf3, rf4 = st.columns(4)
        with rf1:
            f_type  = st.selectbox("Type",  ["All"] + SP_TYPES,  key="r_f_type")
        with rf2:
            f_phase = st.selectbox("Phase", ["All"] + PHASES,    key="r_f_phase")
        with rf3:
            all_teams_in_data = sorted({r.get("team","") for r in routines if r.get("team")})
            f_team  = st.selectbox("Team",  ["All"] + all_teams_in_data, key="r_f_team")
        with rf4:
            all_tags = sorted({t for r in routines for t in r.get("tags", [])})
            f_tag   = st.selectbox("Tag",   ["All"] + all_tags,  key="r_f_tag")

    displayed = routines
    if f_type  != "All": displayed = [r for r in displayed if r.get("sp_type") == f_type]
    if f_phase != "All": displayed = [r for r in displayed if r.get("phase")   == f_phase]
    if f_team  != "All": displayed = [r for r in displayed if r.get("team")    == f_team]
    if f_tag   != "All": displayed = [r for r in displayed if f_tag in r.get("tags", [])]

    # Sort newest first
    displayed = sorted(displayed, key=lambda r: r.get("created_at", 0), reverse=True)

    section_header(f"{len(displayed)} routine{'s' if len(displayed) != 1 else ''}")

    # Summary table
    tab_cards, tab_table = st.tabs(["Cards", "Table"])

    with tab_cards:
        if not displayed:
            st.info("No routines match the current filters.")
        else:
            for i, r in enumerate(displayed):
                _routine_card(r, i)

    with tab_table:
        if not displayed:
            st.info("No routines match the current filters.")
        else:
            rows = []
            for r in displayed:
                rows.append({
                    "Name":        r.get("name", ""),
                    "Team":        r.get("team", ""),
                    "Type":        r.get("sp_type", ""),
                    "Phase":       r.get("phase", ""),
                    "Outcome":     r.get("outcome", ""),
                    "Tags":        ", ".join(r.get("tags", [])),
                    "Match ref":   r.get("match_ref", ""),
                    "Description": r.get("description", "")[:80] + ("…" if len(r.get("description","")) > 80 else ""),
                })
            from mm_setpieces_1.utils import render_analyst_table
            render_analyst_table(pd.DataFrame(rows), height=400)
