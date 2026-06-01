"""Data Justification section — methodology, sources, and rationale."""
from __future__ import annotations

import streamlit as st

from mm_setpieces_1.utils import hero_block, section_header


def render_data_justification() -> None:
    hero_block("Methodology", "Data Justification", "Sources, definitions, and analytical rationale behind every metric")

    tab_sources, tab_metrics, tab_models, tab_caveats = st.tabs([
        "📂 Data sources", "📐 Metric definitions", "🧮 Models & methods", "⚠️ Caveats"
    ])

    with tab_sources:
        section_header("Event data", "What we collect and where it comes from")
        st.markdown("""
<div class="mm-insight-card">
Event data is sourced from <strong>Opta / StatsBomb</strong> feeds ingested via the club's data pipeline.
Each row represents a single set-piece restart event — a corner, direct or indirect free kick, or throw-in.
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="mm-command-panel" style="margin-top:.8rem">
  <div class="mm-command-title">Coverage</div>
  <div class="mm-command-row"><div class="mm-command-label">Competitions</div><div class="mm-command-value">All loaded leagues in the Data/ folder — filenames determine league tagging.</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Seasons</div><div class="mm-command-value">Dependent on uploaded files. Each SP workbook covers one season/competition.</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Granularity</div><div class="mm-command-value">Sequence-level: from the restart event through to the sequence end (shot, clearance, out of play, etc.).</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Coordinate system</div><div class="mm-command-value">Opta: 0–100 × 0–100 pitch. Pitches normalised to attack left-to-right.</div></div>
</div>
""", unsafe_allow_html=True)

        section_header("HOPS data", "Heading and aerial duel profiles")
        st.markdown("""
<div class="mm-command-panel" style="margin-top:.8rem">
  <div class="mm-command-title">Source</div>
  <div class="mm-command-row"><div class="mm-command-label">Origin</div><div class="mm-command-value">Player-level heading metrics derived from aerial duel outcomes across all tracked matches for each player.</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Rating</div><div class="mm-command-value">Composite score combining aerial duel win rate, volume, and positional context. Normalised to 0–1 scale.</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Tiers</div><div class="mm-command-value">Elite (&gt;0.75) / Strong (0.55–0.75) / Average (0.35–0.55) / Below average (&lt;0.35).</div></div>
</div>
""", unsafe_allow_html=True)

        section_header("Delay data", "Corner-taking timing")
        st.markdown("""
<div class="mm-command-panel" style="margin-top:.8rem">
  <div class="mm-command-title">Source</div>
  <div class="mm-command-row"><div class="mm-command-label">Method</div><div class="mm-command-value">Extracted from video timestamps. Delay = time between referee whistle / ball-in-play signal and the corner kick event timestamp.</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Bands</div><div class="mm-command-value">Quick (&lt;5 s) / Standard (5–15 s) / Slow (15–30 s) / Very slow (&gt;30 s).</div></div>
</div>
""", unsafe_allow_html=True)

    with tab_metrics:
        section_header("Core set-piece metrics")

        metrics = [
            ("Set pieces / Restarts", "Count of all qualifying restart events in the filtered dataset. A 'restart' is the moment of the set piece itself — not subsequent play."),
            ("Shots", "Any shot attempt (on target, off target, blocked) occurring within the set-piece sequence, up to the sequence end event."),
            ("Goals", "Goals scored within the set-piece sequence, including second-phase goals if still within the same possession sequence."),
            ("xG (expected goals)", "Sum of Opta/StatsBomb xG values for all shots in the sequence. Represents the probability-weighted goal expectation."),
            ("Shot rate %", "Shots ÷ Set pieces × 100. The proportion of restarts that produced at least one shot attempt."),
            ("xG / 100", "Total xG ÷ Set pieces × 100. Allows fair comparison across teams with different restart volumes."),
            ("Goals / 100", "Goals ÷ Set pieces × 100. Raw goal conversion per 100 restarts."),
        ]

        for name, defn in metrics:
            st.markdown(f"""
<div class="mm-command-panel" style="margin:.45rem 0">
  <div class="mm-command-row" style="border-top:none;padding-top:0">
    <div class="mm-command-label" style="min-width:9rem">{name}</div>
    <div class="mm-command-value">{defn}</div>
  </div>
</div>
""", unsafe_allow_html=True)

        section_header("HOPS metrics")
        st.markdown("""
<div class="mm-command-panel" style="margin-top:.5rem">
  <div class="mm-command-row" style="border-top:none;padding-top:0"><div class="mm-command-label">Rating</div><div class="mm-command-value">Composite 0–1 aerial ability score. Higher = better heading threat or defensive aerial ability.</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Percentile</div><div class="mm-command-value">Player's position in the rating distribution across all players in the dataset.</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Tier</div><div class="mm-command-value">Band label derived from rating thresholds (see Data sources tab).</div></div>
</div>
""", unsafe_allow_html=True)

    with tab_models:
        section_header("xG model")
        st.markdown("""
<div class="mm-insight-card">
Expected goals values are supplied directly by the event data provider (Opta or StatsBomb).
We do <strong>not</strong> recalculate xG — we aggregate and report provider values as-is.
This ensures consistency with club-level reporting and avoids double-modelling.
</div>
""", unsafe_allow_html=True)

        section_header("Sequence definition", "How a set-piece sequence is bounded")
        st.markdown("""
<div class="mm-command-panel" style="margin-top:.5rem">
  <div class="mm-command-row" style="border-top:none;padding-top:0"><div class="mm-command-label">Start</div><div class="mm-command-value">The restart event itself (corner kick, free kick, throw-in).</div></div>
  <div class="mm-command-row"><div class="mm-command-label">End</div><div class="mm-command-value">First of: shot, goal, ball out of play, opposing team possession, or 10 events elapsed — whichever comes first.</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Second phase</div><div class="mm-command-value">Shots from second-phase play (e.g. a clearance won back) are included if still within the same possession sequence.</div></div>
</div>
""", unsafe_allow_html=True)

        section_header("Zone definitions")
        st.markdown("""
<div class="mm-command-panel" style="margin-top:.5rem">
  <div class="mm-command-row" style="border-top:none;padding-top:0"><div class="mm-command-label">Corners</div><div class="mm-command-value">Near post / Far post / Centre / Short — based on delivery landing zone relative to goal.</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Free kicks</div><div class="mm-command-value">Zone 1 (central, &lt;25m) / Zone 2 (wide, &lt;30m) / Zone 3 (&gt;30m or indirect). Based on origin coordinates.</div></div>
  <div class="mm-command-row"><div class="mm-command-label">Throw-ins</div><div class="mm-command-value">Defensive third / Middle third / Attacking third — based on throw origin x-coordinate.</div></div>
</div>
""", unsafe_allow_html=True)

    with tab_caveats:
        section_header("Known limitations")

        caveats = [
            ("Sample size", "Teams with fewer than ~30 set pieces in a filter should be treated with caution. Small samples inflate xG / 100 and shot rate figures."),
            ("Data completeness", "Coverage depends on uploaded workbooks. Missing leagues or seasons produce gaps that are not flagged automatically — check the Data/ folder."),
            ("xG provider variance", "Opta and StatsBomb use different xG models. Cross-provider comparisons (e.g. across leagues sourced from different providers) may not be directly comparable."),
            ("Second-phase attribution", "Second-phase shots are included in the set-piece sequence totals. This inflates xG slightly compared to definitions that only count direct delivery shots."),
            ("Delay measurement", "Corner delay timings are derived from video timestamps and carry ±1–2 s measurement error depending on the footage frame rate."),
            ("HOPS generalisability", "HOPS ratings are calculated from the players in the loaded dataset only. Ratings for players with very few aerial duels (&lt;10) should be treated as indicative."),
        ]

        for title, body in caveats:
            st.markdown(f"""
<div class="mm-insight-card" style="margin:.4rem 0">
  <strong>{title}</strong><br><span style="font-size:.84rem">{body}</span>
</div>
""", unsafe_allow_html=True)
