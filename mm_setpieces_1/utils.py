
from __future__ import annotations

from pathlib import Path
from io import BytesIO
from html import escape
import os
import tempfile
import textwrap
import numpy as np
import pandas as pd
import streamlit as st

# Colour tokens and CSS injection now live in styles.py
from mm_setpieces_1.styles import (
    BLACK, RED, RED_DARK, INK, MUTED, BORDER,
    inject_app_style,
    inject_sidebar_css,
)

PLOTLY_AVAILABLE = True
try:
    import plotly.graph_objects as go
except Exception:
    PLOTLY_AVAILABLE = False

    class _PlotlyLayout(dict):
        def __getattr__(self, name):
            value = self.get(name)
            if isinstance(value, dict):
                return _PlotlyLayout(value)
            return value

    class _FallbackFigure:
        def __init__(self, other=None, *_, **__):
            if hasattr(other, "to_dict"):
                payload = other.to_dict()
                self.data = list(payload.get("data", []))
                self.layout = _PlotlyLayout(payload.get("layout", {}))
            else:
                self.data = []
                self.layout = _PlotlyLayout()

        def add_trace(self, trace):
            self.data.append(dict(trace))
            return self

        def add_bar(self, **kwargs):
            return self.add_trace({"type": "bar", **kwargs})

        def add_histogram(self, **kwargs):
            return self.add_trace({"type": "histogram", **kwargs})

        def add_box(self, **kwargs):
            return self.add_trace({"type": "box", **kwargs})

        def add_annotation(self, **kwargs):
            self.layout.setdefault("annotations", []).append(kwargs)
            return self

        def update_layout(self, **kwargs):
            for key, value in kwargs.items():
                if isinstance(value, dict) and isinstance(self.layout.get(key), dict):
                    self.layout[key].update(value)
                else:
                    self.layout[key] = value
            return self

        def update_xaxes(self, **kwargs):
            self.layout.setdefault("xaxis", {}).update(kwargs)
            return self

        def update_yaxes(self, **kwargs):
            self.layout.setdefault("yaxis", {}).update(kwargs)
            return self

        def to_dict(self):
            return {"data": self.data, "layout": dict(self.layout)}

    class _FallbackGraphObjects:
        Figure = _FallbackFigure

        @staticmethod
        def Bar(**kwargs):
            return {"type": "bar", **kwargs}

        @staticmethod
        def Scatter(**kwargs):
            return {"type": "scatter", **kwargs}

        @staticmethod
        def Histogram(**kwargs):
            return {"type": "histogram", **kwargs}

        @staticmethod
        def Box(**kwargs):
            return {"type": "box", **kwargs}

    go = _FallbackGraphObjects()

PITCH_LENGTH = 120
PITCH_WIDTH = 80
HALF_START = 60
OPTA_PITCH_LENGTH = 100
OPTA_PITCH_WIDTH = 68
OPTA_HALF_START = 50
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Data"
LOGO_PATH = BASE_DIR.parent / "assets" / "setplaypro-logo.jpg"

# ── DATA_VERSION: derived from data dir modification time so cache auto-busts
# when files are added. Falls back to a static string if Data/ doesn't exist.
def _compute_data_version() -> str:
    data_dir = BASE_DIR.parent / "Data"
    if not data_dir.exists():
        return "foldered_sources_v14_a_league"
    try:
        mtime = max(p.stat().st_mtime for p in data_dir.rglob("*") if p.is_file())
        return f"data_{int(mtime)}"
    except Exception:
        return "foldered_sources_v14_a_league"

DATA_VERSION = _compute_data_version()

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mm-setpieces-mpl"))



def render_sidebar_menu(active: str = "Home", filters: list[tuple[str, str]] | None = None) -> None:
    st.sidebar.markdown("### Desk")
    st.sidebar.caption("Use the single app selector in app.py to switch views.")
    st.sidebar.markdown(f"### {active} filters")
    if filters:
        for label, value in filters:
            st.sidebar.markdown(
                f"""
                <div class="mm-filter-card">
                    <div class="mm-filter-label">{escape(str(label))}</div>
                    <div class="mm-filter-value">{escape(str(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _format_filter_value(value: object) -> str:
    if value is None:
        return "All"
    if isinstance(value, (list, tuple, set)):
        cleaned = [str(v) for v in value if str(v).strip()]
        if not cleaned:
            return "All"
        if len(cleaned) <= 2:
            return ", ".join(cleaned)
        return f"{', '.join(cleaned[:2])} +{len(cleaned) - 2}"
    text = str(value).strip()
    return text or "All"


def render_filter_summary(
    label: str,
    source_rows: int,
    filtered_rows: int,
    filters: list[tuple[str, object]],
) -> None:
    active = [
        (name, _format_filter_value(value))
        for name, value in filters
        if _format_filter_value(value) not in {"All", "Total", "0-95"}
    ]
    chips = "".join(
        f"<span class='mm-chip'><strong>{escape(str(name))}:</strong>{escape(str(value))}</span>"
        for name, value in active[:8]
    )
    if len(active) > 8:
        chips += f"<span class='mm-chip'><strong>More</strong>{len(active) - 8} filters</span>"
    if not chips:
        chips = "<span class='mm-chip'><strong>Filters</strong>Full sample</span>"

    st.markdown(
        f"""
        <div class="mm-filter-summary">
            <div class="mm-filter-count">{escape(label)} · {filtered_rows:,} of {source_rows:,} rows</div>
            <div class="mm-filter-chips">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_filter_state() -> None:
    st.markdown(
        """
        <div class="mm-empty-state">
            <div class="mm-empty-title">No rows match the current filters.</div>
            <div class="mm-empty-copy">Widen the team, league, minute range, or player filters above to bring events back into view.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_rail() -> None:
    return None


def hero_block(eyebrow: str, title: str, copy: str) -> None:
    """Compact page header — replaces the old hero banner."""
    st.markdown(
        f"""
        <div class="mm-page-header">
            <div class="mm-page-title">{title}</div>
            <div class="mm-page-scope">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, scope: str = "") -> None:
    """Lightweight section page header with optional scope line."""
    scope_html = f'<div class="mm-page-scope">{scope}</div>' if scope else ""
    st.markdown(
        f"""
        <div class="mm-page-header">
            <div class="mm-page-title">{title}</div>
            {scope_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, note: str = "") -> None:
    note_html = f'<div class="mm-section-note">{note}</div>' if note else ""
    st.markdown(
        f"""
        <div class="mm-section">
            <div class="mm-section-title">{title}</div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def polish_plotly_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        font=dict(color="#d1d5db", family="Inter, Arial, sans-serif", size=12),
        title_font=dict(color="#f1f5f9", size=13, family="Inter, Arial, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#161922",
        colorway=["#22c55e", "#3b82f6", "#f59e0b", "#8b5cf6", "#06b6d4", "#f43f5e", "#94a3b8"],
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(255,255,255,0.08)",
            borderwidth=1,
            font=dict(size=11, color="#9ca3af"),
        ),
        margin=dict(l=8, r=8, t=32, b=8),
    )
    fig.update_xaxes(
        showgrid=True, gridcolor="rgba(255,255,255,0.05)",
        zeroline=False, color="#6b7280",
        tickfont=dict(size=11), title_font=dict(size=11),
        linecolor="rgba(255,255,255,0.08)",
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="rgba(255,255,255,0.05)",
        zeroline=False, color="#6b7280",
        tickfont=dict(size=11), title_font=dict(size=11),
        linecolor="rgba(255,255,255,0.08)",
    )
    return fig


def _safe_file_stem(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value.strip().lower())
    return "_".join(part for part in cleaned.split("_") if part) or "setplaypro"


def add_logo_to_png_bytes(png_bytes: bytes) -> bytes:
    from PIL import Image

    if not LOGO_PATH.exists():
        return png_bytes

    image = Image.open(BytesIO(png_bytes)).convert("RGBA")
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo_width = max(84, min(180, int(image.width * 0.13)))
    logo.thumbnail((logo_width, logo_width), Image.LANCZOS)
    margin = max(18, int(image.width * 0.018))
    image.alpha_composite(logo, (image.width - logo.width - margin, margin))

    output = BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()


def _coerce_plot_values(values) -> list:
    if values is None:
        return []
    if hasattr(values, "tolist"):
        values = values.tolist()
    return list(values)


def _matplotlib_color(value: object, default: str = "#94a3b8"):
    text = str(value or "").strip()
    if text.startswith("rgba(") and text.endswith(")"):
        parts = [part.strip() for part in text[5:-1].split(",")]
        if len(parts) == 4:
            try:
                return (float(parts[0]) / 255, float(parts[1]) / 255, float(parts[2]) / 255, float(parts[3]))
            except ValueError:
                return default
    if text.startswith("rgb(") and text.endswith(")"):
        parts = [part.strip() for part in text[4:-1].split(",")]
        if len(parts) == 3:
            try:
                return (float(parts[0]) / 255, float(parts[1]) / 255, float(parts[2]) / 255)
            except ValueError:
                return default
    if text in {"", "none", "None"}:
        return "none"
    return text


def _plotly_matplotlib_fallback_png_bytes(fig: go.Figure, width: int, height: int) -> bytes:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig_dict = fig.to_dict()
    data = fig_dict.get("data", [])
    layout = fig_dict.get("layout", {})
    title = layout.get("title", {}).get("text") if isinstance(layout.get("title"), dict) else layout.get("title", "")
    title = title or "SetPlayPro visual"

    mpl_fig, ax = plt.subplots(figsize=(width / 180, height / 180), dpi=180)
    mpl_fig.patch.set_facecolor("#1e2230")
    ax.set_facecolor("#1e2230")

    for shape in layout.get("shapes", []) or []:
        shape_type = shape.get("type", "")
        line = shape.get("line", {}) or {}
        fillcolor = _matplotlib_color(shape.get("fillcolor", "none"), "none")
        edgecolor = _matplotlib_color(line.get("color", "#94a3b8"))
        linewidth = float(line.get("width", 1) or 1)
        alpha = 1.0
        if fillcolor == "rgba(255,255,255,0)":
            fillcolor = "none"

        if shape_type == "rect":
            rect = patches.Rectangle(
                (float(shape.get("x0", 0)), float(shape.get("y0", 0))),
                float(shape.get("x1", 0)) - float(shape.get("x0", 0)),
                float(shape.get("y1", 0)) - float(shape.get("y0", 0)),
                linewidth=linewidth,
                edgecolor=edgecolor,
                facecolor=fillcolor,
                alpha=alpha,
                zorder=0,
            )
            ax.add_patch(rect)
        elif shape_type == "line":
            ax.plot(
                [float(shape.get("x0", 0)), float(shape.get("x1", 0))],
                [float(shape.get("y0", 0)), float(shape.get("y1", 0))],
                color=edgecolor,
                linewidth=linewidth,
                zorder=0,
            )
        elif shape_type == "circle":
            x0, x1 = float(shape.get("x0", 0)), float(shape.get("x1", 0))
            y0, y1 = float(shape.get("y0", 0)), float(shape.get("y1", 0))
            circle = patches.Ellipse(
                ((x0 + x1) / 2, (y0 + y1) / 2),
                abs(x1 - x0),
                abs(y1 - y0),
                linewidth=linewidth,
                edgecolor=edgecolor,
                facecolor=fillcolor,
                zorder=0,
            )
            ax.add_patch(circle)

    drew_trace = False
    box_values = []
    box_labels = []
    for idx, trace in enumerate(data):
        trace_type = trace.get("type", "scatter")
        name = str(trace.get("name") or trace_type.title())
        x = _coerce_plot_values(trace.get("x"))
        y = _coerce_plot_values(trace.get("y"))
        marker = trace.get("marker", {}) or {}
        color = marker.get("color") if isinstance(marker.get("color"), str) else None
        color = color or [RED, BLACK, "#2563eb", "#16a34a", "#f59e0b", "#7c3aed", "#64748b"][idx % 7]

        if trace_type == "bar" and x and y:
            if trace.get("orientation") == "h":
                ax.barh(y, x, label=name, color=color, alpha=0.88)
            else:
                ax.bar(x, y, label=name, color=color, alpha=0.88)
            drew_trace = True
        elif trace_type in {"scatter", "scattergl"} and x and y:
            mode = trace.get("mode", "markers")
            if "lines" in mode:
                ax.plot(x, y, label=name, color=color, linewidth=1.8, alpha=0.86)
            if "markers" in mode or mode == "markers":
                raw_size = marker.get("size", 42)
                if hasattr(raw_size, "tolist"):
                    raw_size = raw_size.tolist()
                if isinstance(raw_size, list):
                    sizes = [max(18, min(180, float(v or 18))) for v in raw_size]
                else:
                    sizes = max(24, min(120, float(raw_size or 42)))
                ax.scatter(x, y, s=sizes, label=name, color=color, alpha=0.78, edgecolors="white", linewidths=0.5)
            drew_trace = True
        elif trace_type == "histogram" and x:
            ax.hist(x, bins=min(30, max(8, int(len(x) ** 0.5) if x else 8)), label=name, color=color, alpha=0.86)
            drew_trace = True
        elif trace_type == "box" and y:
            box_values.append(y)
            box_labels.append(name)
            drew_trace = True

    if box_values:
        ax.boxplot(box_values, labels=box_labels, patch_artist=True)

    if not drew_trace:
        ax.text(0.5, 0.5, "No visual data available", ha="center", va="center", transform=ax.transAxes, color=MUTED)

    x_title = layout.get("xaxis", {}).get("title", {}).get("text", "") if isinstance(layout.get("xaxis"), dict) else ""
    y_title = layout.get("yaxis", {}).get("title", {}).get("text", "") if isinstance(layout.get("yaxis"), dict) else ""
    ax.set_title(title, color="#f1f5f9", fontweight="bold", pad=14)
    ax.set_xlabel(x_title)
    ax.set_ylabel(y_title)
    xaxis = layout.get("xaxis", {}) if isinstance(layout.get("xaxis"), dict) else {}
    yaxis = layout.get("yaxis", {}) if isinstance(layout.get("yaxis"), dict) else {}
    if xaxis.get("range"):
        ax.set_xlim(xaxis["range"])
    if yaxis.get("range"):
        ax.set_ylim(yaxis["range"])
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, color="#e5e7eb", linewidth=0.7)
    if len(data) > 1:
        legend = layout.get("legend", {}) if isinstance(layout.get("legend"), dict) else {}
        if legend.get("orientation") == "h":
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=min(4, len(data)), fontsize=7)
            mpl_fig.tight_layout(rect=[0, 0.08, 1, 0.96])
        else:
            ax.legend(loc="best", fontsize=7)
            mpl_fig.tight_layout(rect=[0, 0, 0.9, 0.96])
    else:
        mpl_fig.tight_layout(rect=[0, 0, 1, 0.96])

    output = BytesIO()
    mpl_fig.savefig(output, format="png", dpi=180, facecolor="#1e2230")
    plt.close(mpl_fig)
    return add_logo_to_png_bytes(output.getvalue())


def plotly_figure_png_bytes(fig: go.Figure, width: int = 1400, height: int | None = None) -> bytes:
    export_height = height or int(fig.layout.height or 820)
    export_fig = go.Figure(fig)
    margin = fig.layout.margin
    export_fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(
            l=int(margin.l or 40) if margin else 40,
            r=int(margin.r or 40) if margin else 40,
            t=max(int(margin.t or 50) if margin else 50, 70),
            b=int(margin.b or 40) if margin else 40,
        ),
    )
    try:
        return add_logo_to_png_bytes(export_fig.to_image(format="png", width=width, height=export_height, scale=2))
    except Exception:
        pass
    return _plotly_matplotlib_fallback_png_bytes(export_fig, width, export_height)


def matplotlib_figure_png_bytes(fig) -> bytes:
    output = BytesIO()
    fig.savefig(output, format="png", dpi=180, bbox_inches="tight", facecolor="#1e2230")
    return add_logo_to_png_bytes(output.getvalue())


def add_logo_to_matplotlib_figure(fig) -> None:
    if not LOGO_PATH.exists():
        return

    import matplotlib.image as mpimg

    logo = mpimg.imread(LOGO_PATH)
    ax = fig.add_axes([0.82, 0.91, 0.12, 0.055], anchor="NE", zorder=20)
    ax.imshow(logo)
    ax.axis("off")


def render_plotly_png_download(fig: go.Figure, label: str, key: str) -> None:
    if st.checkbox(f"Prepare {label} PNG", key=f"{key}_prepare_png"):
        try:
            st.download_button(
                "Download PNG with logo",
                data=plotly_figure_png_bytes(fig),
                file_name=f"{_safe_file_stem(label)}.png",
                mime="image/png",
                key=f"{key}_download_png",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"PNG export failed. Streamlit Cloud may still be installing the export dependency. Details: {exc}")


def render_matplotlib_png_download(fig, label: str, key: str) -> None:
    if st.checkbox(f"Prepare {label} PNG", key=f"{key}_prepare_png"):
        st.download_button(
            "Download PNG with logo",
            data=matplotlib_figure_png_bytes(fig),
            file_name=f"{_safe_file_stem(label)}.png",
            mime="image/png",
            key=f"{key}_download_png",
            use_container_width=True,
        )


@st.cache_data(show_spinner="Loading data…")
def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()


def render_export_controls(df: pd.DataFrame, slug: str, sheet_name: str = "Data") -> None:
    st.markdown('<div class="mm-table-note">Exports are prepared only when needed to keep page reruns fast.</div>', unsafe_allow_html=True)
    if not st.checkbox("Prepare export files", key=f"{slug}_prepare_exports"):
        return

    csv_col, excel_col = st.columns(2)
    safe_slug = slug.lower().replace(" ", "_").replace("/", "-")
    with csv_col:
        st.download_button(
            "Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"{safe_slug}_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with excel_col:
        st.download_button(
            "Download Excel",
            data=dataframe_to_excel_bytes(df, sheet_name=sheet_name[:31] or "Data"),
            file_name=f"{safe_slug}_filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def categorical_breakdown_figure(
    df: pd.DataFrame,
    column: str,
    title: str,
    *,
    top_n: int = 8,
    color: str = RED,
    exclude_unknown: bool = True,
) -> go.Figure:
    fig = go.Figure()
    if df.empty or column not in df.columns:
        fig.add_annotation(text="No data available", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return polish_plotly_figure(fig)

    raw = df[column].fillna("Unknown").astype(str)
    if exclude_unknown:
        raw = raw[~raw.str.strip().str.lower().isin(["unknown", "nan", "none", ""])]

    if raw.empty:
        fig.add_annotation(text="No data available", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return polish_plotly_figure(fig)

    counts = raw.value_counts().head(top_n).sort_values(ascending=True)

    fig.add_trace(
        go.Bar(
            x=counts.values,
            y=counts.index.tolist(),
            orientation="h",
            marker=dict(color=color),
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    fig.update_layout(title=title, height=340, margin=dict(l=10, r=10, t=45, b=10), showlegend=False)
    return polish_plotly_figure(fig)


def minute_distribution_figure(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    if df.empty or "minute" not in df.columns:
        fig.add_annotation(text="No minute data available", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return polish_plotly_figure(fig)

    minutes = pd.to_numeric(df["minute"], errors="coerce").dropna()
    if minutes.empty:
        fig.add_annotation(text="No minute data available", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return polish_plotly_figure(fig)

    # Always show all 5-min bands from 0 to at least 95; extend if data has extra time.
    # Avoid pd.cut: map each minute directly to its band start (54→50, 90→90, 95→95).
    max_minute = max(95, int(minutes.max()))
    max_bin_start = (max_minute // 5) * 5
    all_labels = [f"{b}-{b + 4}" for b in range(0, max_bin_start + 1, 5)]
    bin_starts = (minutes.astype(int) // 5) * 5
    mapped = bin_starts.map(lambda b: f"{b}-{b + 4}")
    counts = mapped.value_counts().reindex(all_labels, fill_value=0)
    fig.add_trace(
        go.Bar(
            x=counts.index.tolist(),
            y=counts.values,
            marker=dict(color="#60a5fa"),
            hovertemplate="Minute window %{x}: %{y}<extra></extra>",
        )
    )
    fig.update_layout(title=title, height=340, margin=dict(l=10, r=10, t=45, b=10), showlegend=False)
    return polish_plotly_figure(fig)

DATA_SUBFOLDERS = {
    "Corners": DATA_DIR / "Corners",
    "SP": DATA_DIR / "SP",
    "HOPS": DATA_DIR / "HOPS",
}

SP_SOURCE_COLUMNS = {
    "match_id",
    "possession",
    "team.name",
    "type.name",
    "SP_Type",
    "location.pass",
    "pass.height.name",
    "timestamp",
    "Taker",
    "Shooter",
    "location.shot",
    "shot.statsbomb_xg",
    "shot.outcome.name",
    "shot_x",
    "shot_y",
    "Restart_Profile",
    "Start_Third",
    "Next_3_Box_Entry",
    "Next_3_Retain_Possession",
    "restart_x",
    "restart_y",
    "actions_checked",
}
SP_PREPARED_COLUMNS = {"Team", "Match", "minute", "pass_x", "pass_y", "xg", "is_shot", "match_rank"}


def _folder_from_filename(path: Path) -> str:
    text = " ".join([path.name, *path.parent.parts]).lower().replace("_", " ").replace("-", " ")
    name = path.name.lower()
    if "delay" in name:
        return ""
    if "hops" in text:
        return "HOPS"
    if ("sp" in text or "set piece" in text) and "corner" not in name:
        return "SP"
    if "corner" in text:
        return "Corners"
    return ""


def _columns_from_data_file(path: Path) -> set[str]:
    try:
        suffix = path.suffix.lower()
        if suffix == ".parquet":
            cols = pd.read_parquet(path, engine="pyarrow", columns=[]).columns
        elif suffix == ".csv":
            cols = pd.read_csv(path, nrows=0).columns
        else:
            cols = pd.read_excel(path, nrows=0, engine="openpyxl").columns
    except Exception:
        return set()
    return {str(col).strip().lower() for col in cols if str(col).strip()}


def _folder_from_file(path: Path) -> str:
    folder = _folder_from_filename(path)
    if folder:
        return folder

    cols = _columns_from_data_file(path)
    if {"player", "rating"}.issubset(cols):
        return "HOPS"
    if "sp_type" in cols or "play_pattern.name" in cols or "location.pass" in cols:
        return "SP"
    if {"pass_team_name", "taker"}.issubset(cols) or "sp_outcome" in cols:
        return "Corners"
    return ""

def _title_from_token(text: str) -> str:
    upper_tokens = {"ii", "iii", "iv", "u21", "u23", "uae", "usa", "uk", "hnl", "snl", "mls", "nbl", "nfl", "nba", "usl", "az"}
    words = []
    for word in text.replace("_", " ").replace("-", " ").split():
        clean = word.strip()
        if not clean:
            continue
        words.append(clean.upper() if clean.lower() in upper_tokens else clean.capitalize())
    return " ".join(words)


def _league_from_generic_filename(path: Path) -> str:
    import re as _re
    stem = path.stem.strip()
    parts = stem.replace("_", " ").split(" - ", 1)
    candidate = parts[0].strip()
    for suffix in [" Corners", " SP", " HOPS"]:
        if candidate.lower().endswith(suffix.lower()):
            candidate = candidate[: -len(suffix)].strip()
    # Strip trailing season IDs like 316, 318 (3–4 digit numbers)
    candidate = _re.sub(r"\s+\d{3,4}$", "", candidate).strip()
    candidate = " ".join(candidate.split())
    if not candidate or candidate.lower() in {"all", "data", "corners", "sp", "hops"}:
        return "Unknown"
    if candidate.lower().replace("-", " ") in {"a league", "aleague"}:
        return "A-League"
    return _title_from_token(candidate)


def _candidate_paths(filename: str) -> list[Path]:
    return [
        DATA_DIR / filename,
        *(folder / filename for folder in DATA_SUBFOLDERS.values()),
        BASE_DIR.parent / filename,
        BASE_DIR / filename,
        Path(filename),
    ]


def _is_data_file(path: Path, suffixes: tuple[str, ...]) -> bool:
    return (
        path.is_file()
        and not path.name.startswith(("~$", "."))
        and path.suffix.lower() in suffixes
    )


def _data_files(folder: str, suffixes: tuple[str, ...]) -> list[Path]:
    paths: list[Path] = []
    search_root = DATA_SUBFOLDERS.get(folder, DATA_DIR)
    if search_root.exists():
        paths.extend(
            path
            for path in search_root.rglob("*")
            if _is_data_file(path, suffixes)
            and _folder_from_file(path) == folder
        )
    return sorted(set(paths), key=lambda path: tuple(part.lower() for part in path.parts))


def _sp_phase_terms(label: str) -> tuple[str, ...]:
    if label == "Freekicks":
        return ("freekicks", "free kicks", "free-kicks")
    if label == "Throw ins":
        return ("throwins", "throw ins", "throw-ins")
    return ()


def _sp_files_for_label(label: str) -> list[Path]:
    paths = _data_files("SP", (".parquet",))
    terms = _sp_phase_terms(label)
    if not terms:
        return paths

    preferred = [
        path
        for path in paths
        if any(term in path.stem.lower().replace("_", " ") for term in terms)
    ]
    if preferred:
        return preferred

    return [
        path
        for path in paths
        if not any(term in path.stem.lower().replace("_", " ") for term in ("freekicks", "free kicks", "free-kicks", "throwins", "throw ins", "throw-ins"))
    ]


def _prepared_sp_files_for_label(label: str) -> list[Path]:
    return [
        path
        for path in _sp_files_for_label(label)
        if SP_PREPARED_COLUMNS.issubset(_columns_from_data_file(path))
    ]


def _read_prepared_sp_data(label: str) -> pd.DataFrame:
    sources = []
    for path in _prepared_sp_files_for_label(label):
        league = _league_from_filename(path)
        source = _normalise_sp_source(_with_league(_read_sp_source_path(path), league))
        if not source.empty:
            sources.append(source)
    return pd.concat(sources, ignore_index=True, sort=False) if sources else pd.DataFrame()


def _league_from_filename(path: Path) -> str:
    text = " ".join([path.stem, *path.parent.parts]).lower().replace("_", " ").replace("-", " ")
    tokens = set(text.split())
    if "serie a" in text or "italy" in text or "italia" in text or "ita" in tokens:
        return "Serie A"
    if "bundesliga ii" in text or "bundesliga 2" in text or "bundesliga second" in text:
        return "Bundesliga II"
    if "bundesliga" in text or "germany" in text or "ger" in tokens or "deu" in tokens:
        return "Bundesliga"
    if "allsvenskan" in text or "sweden" in text or "swe" in tokens:
        return "Allsvenskan"
    if "czech" in text or "czechia" in text or "cz" in tokens or "cze" in tokens:
        return "Czech First League"
    if "denmark ii" in text or "denmark 2" in text or "denmark second" in text or "danish 2" in text or "dnk ii" in text:
        return "Denmark II"
    if "1. division" in text or "1 division" in text or "danish 1" in text:
        return "1. Division"
    if "superliga" in text:
        return "Superliga"
    if "denmark" in text or "danish" in text or "dnk" in tokens or "den" in tokens:
        return "Denmark"
    if "challenger pro" in text or "challenge league" in text:
        return "Challenger Pro League"
    if "saudi" in text or "ksa" in tokens:
        return "Saudi Pro League"
    if "greece" in text or "greek" in text:
        return "Greece Super League"
    if "switzerland" in text or "swiss" in text:
        if "challenge" in text:
            return "Switzerland Challenge League"
        return "Switzerland Super League"
    if "jupiler" in text or "pro league" in text:
        return "Jupiler Pro League"
    if "belgium" in text or "belgian" in text or "bel" in tokens:
        return "Jupiler Pro League"
    if "uae" in tokens or "emirates" in text:
        return "UAE Pro League"
    if "hnl" in text or "croatia" in text or "croat" in text:
        return "1. HNL"
    if "snl" in text or "slovenia" in text or "slovenian" in text:
        return "1. SNL"
    if ("austria" in text or "austrian" in text) and ("2. liga" in text or "2 liga" in text or "zweite" in text):
        return "2. Liga"
    return _league_from_generic_filename(path)


def _read_excel_path(path: Path, sheet_name=0):
    try:
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    except ImportError:
        return {} if sheet_name is None else pd.DataFrame()
    except Exception:
        return {} if sheet_name is None else pd.DataFrame()


def _read_sp_source_path(path: Path, columns: list[str] | set[str] | None = None) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        try:
            if columns is None:
                return pd.read_parquet(path, engine="pyarrow")
            return pd.read_parquet(path, engine="pyarrow", columns=list(columns))
        except Exception:
            try:
                source = pd.read_parquet(path, engine="pyarrow")
                return source[[col for col in source.columns if str(col) in columns]].copy()
            except Exception:
                return pd.DataFrame()

    try:
        if columns is None:
            return pd.read_excel(path, engine="openpyxl")
        return pd.read_excel(path, engine="openpyxl", usecols=lambda col: str(col) in columns)
    except ImportError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(show_spinner="Loading data…")
def _read_excel_if_exists(filename: str, sheet_name=0):
    for path in _candidate_paths(filename):
        if path.exists():
            return _read_excel_path(path, sheet_name=sheet_name)
    return {} if sheet_name is None else pd.DataFrame()

@st.cache_data(show_spinner="Loading data…")
def _read_csv_if_exists(filename: str) -> pd.DataFrame:
    for path in _candidate_paths(filename):
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame()

def _with_league(df: pd.DataFrame, league: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if league and league != "Unknown":
        df["League"] = league
        return df
    if "League" not in df.columns:
        df["League"] = league
    else:
        league_text = df["League"].astype("object")
        missing = league_text.isna() | league_text.astype(str).str.strip().str.lower().isin(["", "unknown", "nan", "none"])
        df.loc[missing, "League"] = league
    return df

def _canonical_sp_type(value: object) -> str:
    text = str(value).strip()
    lowered = text.lower()
    if "free kick" in lowered or "freekick" in lowered:
        return "From Free Kick"
    if "throw in" in lowered or "throw-in" in lowered or "throwin" in lowered:
        return "From Throw In"
    if "corner" in lowered:
        return "From Corner"
    return text

def _canonical_sp_type_series(series: pd.Series) -> pd.Series:
    return series.map(_canonical_sp_type)

@st.cache_data(show_spinner="Loading data…")
def _load_czech_sp_data() -> pd.DataFrame:
    cz = _read_excel_if_exists("Czech SP.xlsx")
    if cz.empty:
        return cz
    cz = cz.copy()
    if "SP_Type" not in cz.columns and "play_pattern.name" in cz.columns:
        cz["SP_Type"] = cz["play_pattern.name"]
    if "SP_Type" in cz.columns:
        cz["SP_Type"] = _canonical_sp_type_series(cz["SP_Type"])
    return cz

@st.cache_data(show_spinner="Loading data…")
def _load_bundesliga_sp_data(_data_version: str = DATA_VERSION) -> pd.DataFrame:
    bundesliga = _read_excel_if_exists("Bundesliga SP.xlsx")
    if bundesliga.empty:
        return bundesliga
    bundesliga = bundesliga.copy()
    if "SP_Type" not in bundesliga.columns and "play_pattern.name" in bundesliga.columns:
        bundesliga["SP_Type"] = bundesliga["play_pattern.name"]
    if "SP_Type" in bundesliga.columns:
        bundesliga["SP_Type"] = _canonical_sp_type_series(bundesliga["SP_Type"])
    return bundesliga

@st.cache_data(show_spinner="Loading data…")
def _load_uae_sp_data(_data_version: str = DATA_VERSION) -> pd.DataFrame:
    uae = _read_excel_if_exists("UAE SP.xlsx")
    if uae.empty:
        return uae
    uae = uae.copy()
    if "SP_Type" in uae.columns:
        uae["SP_Type"] = _canonical_sp_type_series(uae["SP_Type"])
    return uae


def _normalise_sp_source(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if "SP_Type" not in df.columns and "play_pattern.name" in df.columns:
        df["SP_Type"] = df["play_pattern.name"]
    if "SP_Type" in df.columns:
        df["SP_Type"] = _canonical_sp_type_series(df["SP_Type"])
    return df

def _fill_from_candidates(df: pd.DataFrame, target: str, candidates: list[str], default=np.nan) -> None:
    if target not in df.columns:
        df[target] = pd.Series(np.nan, index=df.index, dtype="object")
    else:
        df[target] = df[target].astype("object")
    for cand in candidates:
        if cand == target or cand not in df.columns:
            continue
        missing = df[target].isna()
        if missing.any():
            df.loc[missing, target] = df.loc[missing, cand]
    df[target] = df[target].fillna(default)

@st.cache_data(show_spinner="Loading data…")
def _cz_taker_team_map(_data_version: str = DATA_VERSION) -> dict[str, str]:
    cz_sp = _load_czech_sp_data()
    if cz_sp.empty or "team.name" not in cz_sp.columns:
        return {}
    player_col = "player.name" if "player.name" in cz_sp.columns else "Taker" if "Taker" in cz_sp.columns else None
    if player_col is None:
        return {}
    taker_team = (
        cz_sp[[player_col, "team.name"]]
        .dropna()
        .astype(str)
        .groupby(player_col)["team.name"]
        .agg(lambda s: s.value_counts().idxmax())
    )
    return taker_team.to_dict()

@st.cache_data(show_spinner="Loading data…")
def _bundesliga_taker_team_map(_data_version: str = DATA_VERSION) -> dict[str, str]:
    bundesliga = _load_bundesliga_sp_data()
    if bundesliga.empty or "team.name" not in bundesliga.columns:
        return {}
    player_col = "Taker" if "Taker" in bundesliga.columns else "player.name" if "player.name" in bundesliga.columns else None
    if player_col is None:
        return {}
    taker_team = (
        bundesliga[[player_col, "team.name"]]
        .dropna()
        .astype(str)
        .groupby(player_col)["team.name"]
        .agg(lambda s: s.value_counts().idxmax())
    )
    return taker_team.to_dict()


@st.cache_data(show_spinner="Loading data…")
def _sp_taker_team_map(league: str, _data_version: str = DATA_VERSION) -> dict[str, str]:
    sources = []
    for path in _data_files("SP", (".parquet",)):
        if _league_from_filename(path) != league:
            continue
        source = _normalise_sp_source(_with_league(_read_sp_source_path(path), league))
        if not _sp_source_matches_filename_league(source, league):
            continue
        if not source.empty:
            sources.append(source)
    if not sources:
        return {}
    sp = pd.concat(sources, ignore_index=True, sort=False)
    player_col = "Taker" if "Taker" in sp.columns else "player.name" if "player.name" in sp.columns else None
    team_col = "Team" if "Team" in sp.columns else "team.name" if "team.name" in sp.columns else None
    if player_col is None or team_col is None:
        return {}
    taker_team = (
        sp[[player_col, team_col]]
        .dropna()
        .astype(str)
        .groupby(player_col)[team_col]
        .agg(lambda s: s.value_counts().idxmax())
    )
    return taker_team.to_dict()


def _normalise_league_name(value: object) -> str:
    text = str(value).strip().lower()
    replacements = {
        "a league": "a-league",
        "a-league men": "a-league",
        "australia - a-league": "a-league",
        "australia - a-league men": "a-league",
        "australia - a league": "a-league",
        "australia - a league men": "a-league",
        "italy - serie a": "serie a",
        "germany - bundesliga": "bundesliga",
        "germany - 2. bundesliga": "bundesliga ii",
        "sweden - allsvenskan": "allsvenskan",
        "czech republic - 1. liga": "czech",
        "croatia - 1. hnl": "croatia",
        "uae - uae pro league": "uae",
        "saudi arabian league": "saudi pro league",
        "saudi league": "saudi pro league",
    }
    text = replacements.get(text, text)
    for prefix in ["australia - ", "italy - ", "germany - ", "sweden - ", "czech republic - ", "croatia - ", "uae - "]:
        if text.startswith(prefix):
            text = text[len(prefix):]
    return (
        text.replace("a league men", "a-league")
        .replace("a-league men", "a-league")
        .replace("a league", "a-league")
        .replace("2. bundesliga", "bundesliga ii")
        .replace("uae pro league", "uae")
        .strip()
    )


@st.cache_data(show_spinner="Loading data…")
def _match_competition_lookup(_data_version: str = DATA_VERSION) -> dict[str, str]:
    path = DATA_DIR / "all_matches.csv"
    if not path.exists():
        return {}
    try:
        matches = pd.read_csv(path, usecols=["match_id", "competition_name"])
    except ValueError:
        return {}
    matches = matches.dropna(subset=["match_id", "competition_name"]).copy()
    matches["match_id"] = matches["match_id"].astype(str).str.replace(r"\.0$", "", regex=True)
    return dict(zip(matches["match_id"], matches["competition_name"].astype(str)))


def _sp_source_matches_filename_league(df: pd.DataFrame, league: str) -> bool:
    if df.empty or "match_id" not in df.columns:
        return True
    lookup = _match_competition_lookup()
    if not lookup:
        return True

    match_ids = df["match_id"].dropna().astype(str).str.replace(r"\.0$", "", regex=True).drop_duplicates()
    competitions = match_ids.map(lookup).dropna()
    if competitions.empty:
        return True

    dominant_competition = competitions.value_counts().index[0]
    return _normalise_league_name(dominant_competition) == _normalise_league_name(league)


@st.cache_data(show_spinner="Loading data…")
def _sp_match_taker_team_map(league: str, _data_version: str = DATA_VERSION) -> dict[tuple[str, str], str]:
    sources = []
    for path in _data_files("SP", (".parquet",)):
        if _league_from_filename(path) != league:
            continue
        source = _normalise_sp_source(_with_league(_read_sp_source_path(path), league))
        if not _sp_source_matches_filename_league(source, league):
            continue
        if not source.empty:
            sources.append(source)
    if not sources:
        return {}

    sp = pd.concat(sources, ignore_index=True, sort=False)
    player_col = "Taker" if "Taker" in sp.columns else "player.name" if "player.name" in sp.columns else None
    team_col = "Team" if "Team" in sp.columns else "team.name" if "team.name" in sp.columns else None
    if player_col is None or team_col is None or "match_id" not in sp.columns:
        return {}

    source = sp[["match_id", player_col, team_col]].dropna().astype(str).copy()
    source["match_id"] = source["match_id"].str.replace(r"\.0$", "", regex=True)
    taker_team = (
        source.groupby(["match_id", player_col])[team_col]
        .agg(lambda s: s.value_counts().idxmax())
    )
    return {(match_id, taker): team for (match_id, taker), team in taker_team.items()}


def _assign_corner_team_from_sp(corners: pd.DataFrame, league: str) -> pd.DataFrame:
    if corners.empty or "Team" in corners.columns or "pass_team_name" in corners.columns or "Taker" not in corners.columns:
        return corners

    corners = corners.copy()
    corners["Team"] = pd.Series(np.nan, index=corners.index, dtype="object")
    if "match_id" in corners.columns:
        match_map = _sp_match_taker_team_map(league)
        if match_map:
            match_ids = corners["match_id"].astype(str).str.replace(r"\.0$", "", regex=True)
            takers = corners["Taker"].astype(str)
            corners["Team"] = [match_map.get((match_id, taker), np.nan) for match_id, taker in zip(match_ids, takers)]

    missing = corners["Team"].isna()
    if missing.any():
        corners.loc[missing, "Team"] = corners.loc[missing, "Taker"].astype(str).map(_sp_taker_team_map(league))
    return corners

@st.cache_data(show_spinner="Loading data…")
def load_corner_data(_data_version: str = DATA_VERSION) -> pd.DataFrame:
    sources = []
    for path in _data_files("Corners", (".parquet",)):
        league = _league_from_filename(path)
        try:
            corners = _with_league(pd.read_parquet(path, engine="pyarrow"), league)
        except Exception:
            corners = pd.DataFrame()
        corners = _assign_corner_team_from_sp(corners, league)
        sources.append(corners)

    sources = [df for df in sources if not df.empty]
    return pd.concat(sources, ignore_index=True, sort=False) if sources else pd.DataFrame()

@st.cache_data(show_spinner="Loading data…")
def load_swe_sp_data(_data_version: str = DATA_VERSION) -> pd.DataFrame:
    sources = []
    for path in _data_files("SP", (".parquet",)):
        league = _league_from_filename(path)
        source = _normalise_sp_source(_with_league(_read_sp_source_path(path, columns=SP_SOURCE_COLUMNS), league))
        if not _sp_source_matches_filename_league(source, league):
            continue
        sources.append(source)
    sources = [df for df in sources if not df.empty]
    return pd.concat(sources, ignore_index=True, sort=False) if sources else pd.DataFrame()

@st.cache_data(show_spinner="Loading data…")
def load_sp_data(label: str, _data_version: str = DATA_VERSION) -> pd.DataFrame:
    if label == "Corners":
        return load_corner_data(_data_version).copy()

    sources = []
    for path in _sp_files_for_label(label):
        league = _league_from_filename(path)
        source = _normalise_sp_source(_with_league(_read_sp_source_path(path, columns=SP_SOURCE_COLUMNS), league))
        if not _sp_source_matches_filename_league(source, league):
            continue
        if not source.empty:
            sources.append(source)

    raw = pd.concat(sources, ignore_index=True, sort=False) if sources else pd.DataFrame()
    if raw.empty or "SP_Type" not in raw.columns:
        return pd.DataFrame()

    mapping = {
        "Freekicks": "From Free Kick",
        "Throw ins": "From Throw In",
    }
    sp_type = mapping.get(label)
    if sp_type:
        sp = _canonical_sp_type_series(raw["SP_Type"])
        return raw[sp.eq(sp_type)].copy()
    return pd.DataFrame()


def filter_by_sp_type(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty or "SP_Type" not in df.columns:
        return df
    mapping = {
        "Freekicks": "From Free Kick",
        "Throw ins": "From Throw In",
    }
    wanted = mapping.get(label)
    if not wanted:
        return df
    sp = _canonical_sp_type_series(df["SP_Type"])
    return df[sp.eq(wanted)].copy()

def _has_values(df: pd.DataFrame, column: str) -> bool:
    return column in df.columns and df[column].notna().any()

def _match_count(df: pd.DataFrame) -> int:
    if _has_values(df, "match_id"):
        return int(df["match_id"].nunique())
    if _has_values(df, "Match"):
        return int(df["Match"].nunique())
    return 0

def _ensure_column(df: pd.DataFrame, target: str, candidates: list[str], default=np.nan):
    _fill_from_candidates(df, target, candidates, default)

def prepare_sp_dataframe(df: pd.DataFrame, label: str = "") -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return df

    if label == "Corners":
        if "pass_team_name" in df.columns:
            pass_team = df["pass_team_name"].astype("object")
            valid_pass_team = pass_team.notna() & pass_team.astype(str).str.strip().ne("")
            if "Team" not in df.columns:
                df["Team"] = pd.Series(np.nan, index=df.index, dtype="object")
            else:
                df["Team"] = df["Team"].astype("object")
            df.loc[valid_pass_team, "Team"] = pass_team.loc[valid_pass_team]
        _ensure_column(df, "Team", ["Team", "pass_team_name", "shot_team_name"], "Unknown")
        _ensure_column(df, "Match", ["Match"], "Unknown")
        _ensure_column(df, "minute", ["minute", "Minute"], 0)
        _ensure_column(df, "second", ["second", "Second"], 0)
        _ensure_column(df, "Technique", ["Technique", "pass.technique.name", "pass_technique"], "Unknown")
        _ensure_column(df, "Delivery height", ["Delivery height", "pass.height.name", "pass_height"], "Unknown")
        _ensure_column(df, "Delivery outcome", ["SP_outcome", "Delivery outcome", "pass.outcome.name", "pass_outcome"], "Unknown")
        _ensure_column(df, "Shot outcome", ["Shot outcome", "shot.outcome.name", "shot_outcome"], "No shot")
        _ensure_column(df, "Shooter", ["Shooter"], "Unknown")
        _ensure_column(df, "Taker", ["Taker"], "Unknown")
        _ensure_column(df, "League", ["League"], "Allsvenskan")
        _ensure_column(df, "timestamp", ["timestamp", "pass_timestamp"], "")
        _ensure_column(df, "pass_x", ["pass_x", "pass_location_x"], np.nan)
        _ensure_column(df, "pass_y", ["pass_y", "pass_location_y"], np.nan)
        _ensure_column(df, "shot_x", ["shot_x", "shot_location_x"], np.nan)
        _ensure_column(df, "shot_y", ["shot_y", "shot_location_y"], np.nan)
        _ensure_column(df, "delivery_end_x", ["delivery_end_x", "pass_end_location_x", "end_x"], np.nan)
        _ensure_column(df, "delivery_end_y", ["delivery_end_y", "pass_end_location_y", "end_y"], np.nan)
        _ensure_column(df, "xg", ["xg", "shot.statsbomb_xg", "shot_statsbomb_xg"], 0.0)

        for col in ["Team", "Match", "Technique", "Delivery height", "Delivery outcome", "Shot outcome", "Shooter", "Taker", "League"]:
            fill = "Allsvenskan" if col == "League" else ("No shot" if col == "Shot outcome" else "Unknown")
            df[col] = df[col].fillna(fill)

        for col in ["minute", "second", "pass_x", "pass_y", "shot_x", "shot_y", "delivery_end_x", "delivery_end_y", "xg"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "side" not in df.columns:
            if "pass_y" in df.columns:
                py = pd.to_numeric(df["pass_y"], errors="coerce")
                league_series = df["League"] if "League" in df.columns else pd.Series("", index=df.index)
                threshold = np.where(league_series.astype(str).eq("UAE Pro League"), OPTA_PITCH_WIDTH / 2, PITCH_WIDTH / 2)
                df["side"] = np.where(py <= threshold, "Left", "Right")
            else:
                df["side"] = "Unknown"

        if "is_shot" not in df.columns:
            df["is_shot"] = df[["shot_x", "shot_y"]].notna().all(axis=1)
        if "is_goal" not in df.columns:
            df["is_goal"] = df["Shot outcome"].astype(str).str.lower().eq("goal")

        if "game_period" not in df.columns:
            minute = pd.to_numeric(df["minute"], errors="coerce").fillna(0)
            bins = [-1, 15, 30, 45, 60, 75, 200]
            labels = ["0-15", "16-30", "31-45", "46-60", "61-75", "76+"]
            df["game_period"] = pd.cut(minute, bins=bins, labels=labels).astype(str)

        if "match_rank" not in df.columns:
            if "match_id" in df.columns:
                match_order = (
                    df[["match_id"]]
                    .dropna()
                    .drop_duplicates()
                    .assign(_match_id_sort=lambda x: x["match_id"].astype(str))
                    .sort_values("_match_id_sort", ascending=False)
                    .reset_index(drop=True)
                )
                match_order["match_rank"] = range(1, len(match_order) + 1)
                match_order = match_order.drop(columns=["_match_id_sort"])
                df = df.merge(match_order, on="match_id", how="left")
            else:
                df["match_rank"] = 999
        return df

    _ensure_column(df, "Team", ["Team", "team.name"], "Unknown")
    _ensure_column(df, "Match", ["Match"], "Unknown")
    _ensure_column(df, "Technique", ["Technique", "type.name", "pass.technique.name"], "Unknown")
    _ensure_column(df, "Delivery height", ["Delivery height", "pass.height.name"], "Unknown")
    _ensure_column(df, "Delivery outcome", ["SP_outcome", "Delivery outcome", "Metrics", "pass.outcome.name"], "Unknown")
    _ensure_column(df, "Shot outcome", ["Shot outcome", "shot.outcome.name"], "No shot")
    _ensure_column(df, "Taker", ["Taker"], "Unknown")
    _ensure_column(df, "Shooter", ["Shooter"], "Unknown")
    _ensure_column(df, "League", ["League"], "Allsvenskan")
    _ensure_column(df, "xg", ["xg", "shot.statsbomb_xg"], 0.0)

    if "Match" in df.columns and (df["Match"].isna().all() or df["Match"].astype(str).eq("Unknown").all()) and "match_id" in df.columns:
        df["Match"] = "Match " + df["match_id"].astype(str)

    for col in ["Team", "Match", "Technique", "Delivery height", "Delivery outcome", "Shot outcome", "Taker", "Shooter", "League"]:
        fill = "Allsvenskan" if col == "League" else ("No shot" if col == "Shot outcome" else "Unknown")
        df[col] = df[col].fillna(fill)

    if "location.pass" in df.columns:
        pass_xy = df["location.pass"].astype(str).str.replace(r"[\[\]]", "", regex=True).str.split(",", expand=True)
        if pass_xy.shape[1] >= 2:
            df["pass_x"] = pd.to_numeric(pass_xy[0].str.strip(), errors="coerce")
            df["pass_y"] = pd.to_numeric(pass_xy[1].str.strip(), errors="coerce")

    if "side" not in df.columns:
        if "pass_y" in df.columns:
            league_series = df["League"] if "League" in df.columns else pd.Series("", index=df.index)
            threshold = np.where(league_series.astype(str).eq("UAE Pro League"), OPTA_PITCH_WIDTH / 2, PITCH_WIDTH / 2)
            df["side"] = np.where(df["pass_y"] <= threshold, "Left", "Right")
        else:
            df["side"] = "Unknown"

    if "location.shot" in df.columns:
        shot_xy = df["location.shot"].astype(str).str.replace(r"[\[\]]", "", regex=True).str.split(",", expand=True)
        if shot_xy.shape[1] >= 2:
            df["shot_x"] = pd.to_numeric(shot_xy[0].str.strip(), errors="coerce")
            df["shot_y"] = pd.to_numeric(shot_xy[1].str.strip(), errors="coerce")

    _ensure_column(df, "shot_x", ["shot_x"], np.nan)
    _ensure_column(df, "shot_y", ["shot_y"], np.nan)
    _ensure_column(df, "delivery_end_x", ["delivery_end_x", "shot_x"], np.nan)
    _ensure_column(df, "delivery_end_y", ["delivery_end_y", "shot_y"], np.nan)

    if "minute" not in df.columns:
        if "timestamp" in df.columns:
            parts = df["timestamp"].astype(str).str.split(":", expand=True)
            if parts.shape[1] >= 2:
                hours = pd.to_numeric(parts[0], errors="coerce").fillna(0)
                minutes = pd.to_numeric(parts[1], errors="coerce").fillna(0)
                df["minute"] = hours * 60 + minutes
            else:
                df["minute"] = pd.to_numeric(parts[0], errors="coerce").fillna(0) if parts.shape[1] >= 1 else 0
        else:
            df["minute"] = 0

    if "second" not in df.columns:
        if "timestamp" in df.columns:
            parts = df["timestamp"].astype(str).str.split(":", expand=True)
            df["second"] = pd.to_numeric(parts[2], errors="coerce").fillna(0) if parts.shape[1] >= 3 else 0
        else:
            df["second"] = 0

    for col in ["minute", "second", "shot_x", "shot_y", "delivery_end_x", "delivery_end_y", "xg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "is_shot" not in df.columns:
        df["is_shot"] = df["shot_x"].notna() & df["shot_y"].notna()
    if "is_goal" not in df.columns:
        df["is_goal"] = df["Shot outcome"].astype(str).str.lower().eq("goal")

    if "game_period" not in df.columns:
        minute = pd.to_numeric(df["minute"], errors="coerce").fillna(0)
        bins = [-1, 15, 30, 45, 60, 75, 200]
        labels = ["0-15", "16-30", "31-45", "46-60", "61-75", "76+"]
        df["game_period"] = pd.cut(minute, bins=bins, labels=labels).astype(str)

    if "match_rank" not in df.columns:
        if "match_id" in df.columns:
            order = (
                df[["match_id"]]
                .dropna()
                .drop_duplicates()
                .assign(_match_id_sort=lambda x: x["match_id"].astype(str))
                .sort_values("_match_id_sort", ascending=False)
                .reset_index(drop=True)
            )
            order["match_rank"] = range(1, len(order) + 1)
            order = order.drop(columns=["_match_id_sort"])
            df = df.merge(order, on="match_id", how="left")
        else:
            df["match_rank"] = 999
    return df


@st.cache_data(show_spinner="Loading data…")
def load_prepared_sp_data(label: str, _data_version: str = DATA_VERSION) -> pd.DataFrame:
    if label != "Corners":
        prepared = _read_prepared_sp_data(label)
        if not prepared.empty:
            return filter_by_sp_type(prepared, label)

    raw = load_sp_data(label, _data_version)
    return filter_by_sp_type(prepare_sp_dataframe(raw, label=label), label)


@st.cache_data(show_spinner="Loading data…")
def load_prepared_freekick_brief_data(_data_version: str = DATA_VERSION) -> pd.DataFrame:
    prepared_source = _read_prepared_sp_data("Freekicks")
    if not prepared_source.empty:
        prepared_source = filter_by_sp_type(prepared_source, "Freekicks")
        vital_columns = [
            "match_id",
            "possession",
            "Team",
            "Match",
            "League",
            "minute",
            "second",
            "game_period",
            "match_rank",
            "pass_x",
            "pass_y",
            "Taker",
            "Delivery height",
            "Shooter",
            "shot_x",
            "shot_y",
            "xg",
            "Shot outcome",
            "is_shot",
            "is_goal",
        ]
        return prepared_source[[c for c in vital_columns if c in prepared_source.columns]].copy()

    sources = []
    for path in _sp_files_for_label("Freekicks"):
        league = _league_from_filename(path)
        source = _read_sp_source_path(path, columns=SP_SOURCE_COLUMNS)
        source = _normalise_sp_source(_with_league(source, league))
        if not _sp_source_matches_filename_league(source, league):
            continue
        if not source.empty:
            sources.append(source)

    if not sources:
        return pd.DataFrame()

    raw = pd.concat(sources, ignore_index=True, sort=False)
    raw = filter_by_sp_type(raw, "Freekicks")
    prepared = filter_by_sp_type(prepare_sp_dataframe(raw, label="Freekicks"), "Freekicks")
    vital_columns = [
        "match_id",
        "possession",
        "Team",
        "Match",
        "League",
        "minute",
        "second",
        "game_period",
        "match_rank",
        "pass_x",
        "pass_y",
        "Taker",
        "Delivery height",
        "Shooter",
        "shot_x",
        "shot_y",
        "xg",
        "Shot outcome",
        "is_shot",
        "is_goal",
    ]
    return prepared[[c for c in vital_columns if c in prepared.columns]].copy()


def _is_swe_sp_df(df: pd.DataFrame) -> bool:
    return "SP_Type" in df.columns

def unique_shot_events(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "shot_x" not in df.columns or "shot_y" not in df.columns:
        return df.iloc[0:0].copy()
    shots = df[df["shot_x"].notna() & df["shot_y"].notna()].copy()
    if shots.empty:
        return shots
    if _is_swe_sp_df(shots):
        keys = [c for c in ["match_id", "possession", "Team", "shot_x", "shot_y", "Shot outcome", "xg"] if c in shots.columns]
        if keys:
            shots = shots.drop_duplicates(subset=keys)
    return shots

def unique_start_events(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if _is_swe_sp_df(df) and _has_values(df, "possession"):
        keys = [c for c in ["match_id", "possession", "Team", "pass_x", "pass_y", "Taker", "timestamp"] if c in df.columns]
        if keys:
            return df.drop_duplicates(subset=keys)
    return df

def uses_opta_pitch(df: pd.DataFrame) -> bool:
    if df.empty or "League" not in df.columns:
        return False
    leagues = set(df["League"].dropna().astype(str).str.strip())
    return bool(leagues) and leagues.issubset({"UAE Pro League"})

def pitch_dimensions(df: pd.DataFrame | None = None) -> dict[str, object]:
    return {
        "name": "statsbomb",
        "length": PITCH_LENGTH,
        "width": PITCH_WIDTH,
        "half_start": HALF_START,
    }

def coords_to_statsbomb(df: pd.DataFrame, x_col: str, y_col: str) -> tuple[pd.Series, pd.Series]:
    x = pd.to_numeric(df[x_col], errors="coerce")
    y = pd.to_numeric(df[y_col], errors="coerce")
    if "League" not in df.columns:
        return x, y
    is_uae = df["League"].astype(str).str.strip().eq("UAE Pro League")
    return x.where(~is_uae, x * (PITCH_LENGTH / OPTA_PITCH_LENGTH)), y.where(~is_uae, y * (PITCH_WIDTH / OPTA_PITCH_WIDTH))

def vertical_coords_from_statsbomb(x: pd.Series, y: pd.Series) -> tuple[pd.Series, pd.Series]:
    return pd.to_numeric(y, errors="coerce"), pd.to_numeric(x, errors="coerce")

def vertical_coords_from_pitch(x: pd.Series, y: pd.Series, _pitch: dict[str, object]) -> tuple[pd.Series, pd.Series]:
    return pd.to_numeric(y, errors="coerce"), pd.to_numeric(x, errors="coerce")

def restart_origin_xy(side: str, pitch: dict[str, object] | None = None) -> tuple[float, float]:
    pitch = pitch or pitch_dimensions()
    return (0.0, float(pitch["length"])) if str(side).lower() == "left" else (float(pitch["width"]), float(pitch["length"]))

def add_half_vertical_pitch_layout(
    fig: go.Figure,
    title: str,
    pitch_color: str = "white",
    height: int = 620,
    source_df: pd.DataFrame | None = None,
) -> go.Figure:
    pitch = pitch_dimensions(source_df)
    pitch_width = float(pitch["width"])
    pitch_length = float(pitch["length"])
    half_start = float(pitch["half_start"])
    sx = pitch_width / PITCH_WIDTH
    sy = pitch_length / PITCH_LENGTH

    fig.update_xaxes(range=[0, pitch_width], visible=False)
    fig.update_yaxes(range=[half_start, pitch_length], visible=False, scaleanchor="x", scaleratio=1)

    penalty_left = (pitch_width / 2) - (22 * sx)
    penalty_right = (pitch_width / 2) + (22 * sx)
    six_left = (pitch_width / 2) - (10 * sx)
    six_right = (pitch_width / 2) + (10 * sx)
    goal_left = (pitch_width / 2) - (4 * sx)
    goal_right = (pitch_width / 2) + (4 * sx)

    def xs(v: float) -> float:
        return v * sx

    def ys(v: float) -> float:
        return v * sy

    zone_shapes = [
        dict(type="rect", x0=xs(30), y0=ys(114), x1=xs(36.67), y1=pitch_length, line=dict(width=0.8, color="rgba(37,99,235,0.55)"), fillcolor="rgba(37,99,235,0.10)", layer="below"),
        dict(type="rect", x0=xs(36.67), y0=ys(114), x1=xs(43.33), y1=pitch_length, line=dict(width=0.8, color="rgba(22,163,74,0.55)"), fillcolor="rgba(22,163,74,0.10)", layer="below"),
        dict(type="rect", x0=xs(43.33), y0=ys(114), x1=xs(50), y1=pitch_length, line=dict(width=0.8, color="rgba(245,158,11,0.55)"), fillcolor="rgba(245,158,11,0.10)", layer="below"),
        dict(type="rect", x0=xs(28), y0=ys(108), x1=xs(52), y1=ys(114), line=dict(width=0.8, color="rgba(124,58,237,0.55)"), fillcolor="rgba(124,58,237,0.08)", layer="below"),
        dict(type="rect", x0=xs(18), y0=ys(102), x1=xs(62), y1=ys(108), line=dict(width=0.8, color="rgba(100,116,139,0.45)"), fillcolor="rgba(100,116,139,0.06)", layer="below"),
    ]

    pitch_shapes = [
        dict(type="rect", x0=0, y0=half_start, x1=pitch_width, y1=pitch_length, line=dict(width=2, color="#1e293b")),
        dict(type="line", x0=0, y0=half_start, x1=pitch_width, y1=half_start, line=dict(width=2, color="#94a3b8")),
        dict(type="rect", x0=penalty_left, y0=ys(102), x1=penalty_right, y1=pitch_length, line=dict(width=1.6, color="#1e293b")),
        dict(type="rect", x0=six_left, y0=ys(114), x1=six_right, y1=pitch_length, line=dict(width=1.6, color="#1e293b")),
        dict(type="line", x0=goal_left, y0=pitch_length, x1=goal_right, y1=pitch_length, line=dict(width=3, color="#1e293b")),
    ]

    annotations = [
        dict(x=xs(33.3), y=ys(116.5), text="Near post", showarrow=False, font=dict(size=10, color="#1e3a8a")),
        dict(x=xs(40.0), y=ys(116.5), text="Central 6", showarrow=False, font=dict(size=10, color="#166534")),
        dict(x=xs(46.7), y=ys(116.5), text="Far post", showarrow=False, font=dict(size=10, color="#b45309")),
        dict(x=xs(40.0), y=ys(111.0), text="Penalty spot", showarrow=False, font=dict(size=10, color="#6d28d9")),
        dict(x=xs(40.0), y=ys(105.0), text="Edge box", showarrow=False, font=dict(size=10, color="#475569")),
    ]

    fig.update_layout(
        title=title,
        shapes=zone_shapes + pitch_shapes,
        annotations=annotations,
        margin=dict(l=10, r=10, t=50, b=10),
        height=height,
        plot_bgcolor=pitch_color,
        paper_bgcolor=pitch_color,
        legend_title_text="",
    )
    return fig

def add_full_pitch_layout(fig: go.Figure, title: str, source_df: pd.DataFrame | None = None, height: int = 560) -> go.Figure:
    pitch = pitch_dimensions(source_df)
    pitch_length = float(pitch["length"])
    pitch_width = float(pitch["width"])
    sx = pitch_length / PITCH_LENGTH
    sy = pitch_width / PITCH_WIDTH

    def xs(v: float) -> float:
        return v * sx

    def ys(v: float) -> float:
        return v * sy

    fig.update_xaxes(range=[0, pitch_length], visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(range=[0, pitch_width], visible=False)
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        shapes=[
            dict(type="rect", x0=0, y0=0, x1=pitch_length, y1=pitch_width, line=dict(color=BLACK, width=1.4)),
            dict(type="line", x0=pitch_length / 2, y0=0, x1=pitch_length / 2, y1=pitch_width, line=dict(color="#94a3b8", width=1)),
            dict(type="rect", x0=xs(102), y0=ys(18), x1=pitch_length, y1=ys(62), line=dict(color=BLACK, width=1.2)),
            dict(type="rect", x0=xs(114), y0=ys(30), x1=pitch_length, y1=ys(50), line=dict(color=BLACK, width=1.2)),
            dict(type="circle", x0=xs(108), y0=ys(34), x1=xs(112), y1=ys(46), line=dict(color="#94a3b8", width=1)),
        ],
    )
    return fig

def shotmap_figure(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    pitch = pitch_dimensions(df)
    half_start = float(pitch["half_start"])
    pitch_width = float(pitch["width"])
    pitch_length = float(pitch["length"])
    if df.empty:
        fig.add_annotation(text="No data available", x=pitch_width / 2, y=(half_start + pitch_length) / 2, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title, source_df=df)

    shots = unique_shot_events(df).copy()
    if not shots.empty:
        shots["plot_x"], shots["plot_y"] = coords_to_statsbomb(shots, "shot_x", "shot_y")
    shots = shots[shots["plot_x"] >= half_start] if not shots.empty else shots

    if shots.empty:
        fig.add_annotation(text="No shots for current filter", x=pitch_width / 2, y=(half_start + pitch_length) / 2, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title, source_df=df)

    shots["vx"], shots["vy"] = vertical_coords_from_pitch(shots["plot_x"], shots["plot_y"], pitch)
    shots["Result"] = np.where(shots["is_goal"], "Goal", "Shot")
    color_map = {"Shot": "#2563eb", "Goal": "#16a34a"}

    for result in ["Shot", "Goal"]:
        part = shots[shots["Result"] == result]
        if part.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=part["vx"],
                y=part["vy"],
                mode="markers",
                name=result,
                marker=dict(
                    size=12 if result == "Shot" else 16,
                    color=color_map[result],
                    opacity=0.78,
                    line=dict(width=1, color="white"),
                ),
                customdata=np.stack(
                    [
                        part["Shooter"].fillna("Unknown"),
                        part["Shot outcome"].fillna("Unknown"),
                        part["xg"].fillna(0).round(3),
                        part["Match"].fillna("Unknown"),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>xG: %{customdata[2]}<br>%{customdata[3]}<extra></extra>",
            )
        )

    return add_half_vertical_pitch_layout(fig, title, source_df=df)

def delivery_map_figure(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    pitch = pitch_dimensions(df)
    half_start = float(pitch["half_start"])
    pitch_width = float(pitch["width"])
    pitch_length = float(pitch["length"])
    if df.empty:
        fig.add_annotation(text="No data available", x=pitch_width / 2, y=(half_start + pitch_length) / 2, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title, source_df=df)

    deliveries = df.copy()

    # Explicit SP_Type filtering for SWE SP pages.
    if "SP_Type" in deliveries.columns:
        sp_values = deliveries["SP_Type"].astype(str).str.strip()
        if sp_values.eq("From Free Kick").any() and not sp_values.eq("From Throw In").any():
            deliveries = deliveries[sp_values.eq("From Free Kick")]
        elif sp_values.eq("From Throw In").any() and not sp_values.eq("From Free Kick").any():
            deliveries = deliveries[sp_values.eq("From Throw In")]

    deliveries = deliveries[deliveries["delivery_end_x"].notna() & deliveries["delivery_end_y"].notna()].copy()
    if not deliveries.empty:
        deliveries["plot_end_x"], deliveries["plot_end_y"] = coords_to_statsbomb(deliveries, "delivery_end_x", "delivery_end_y")

    # Corners use the dedicated half-pitch cutoff; SWE SP freekicks/throw-ins should show all deliveries.
    if "SP_Type" not in deliveries.columns:
        deliveries = deliveries[deliveries["plot_end_x"] >= half_start]

    if deliveries.empty:
        fig.add_annotation(text="No deliveries with end locations for current filter", x=pitch_width / 2, y=(half_start + pitch_length) / 2, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title, source_df=df)

    sample = deliveries.copy()
    if len(sample) > 250:
        st.info(f"Delivery map: showing a random sample of 250 of {len(sample):,} deliveries. Adjust filters to see a specific subset.")
        sample = sample.sample(250, random_state=7)

    sample["vx_end"], sample["vy_end"] = vertical_coords_from_pitch(sample["plot_end_x"], sample["plot_end_y"], pitch)

    color_map = {
        "Goal": "#15803d",
        "Shot after 3 seconds": "#2563eb",
        "Shot after 5 seconds": "#1d4ed8",
        "Shot after 10 seconds": "#7c3aed",
        "Shot": "#2563eb",
        "No shot": "#64748b",
        "Ball astray": "#b45309",
        "First contact won": "#0f766e",
        "First contact lost": "#dc2626",
        "Cleared": "#475569",
        "Retained": "#16a34a",
        "Unknown": "#94a3b8",
    }
    fallback_colors = ["#c1121f", "#0891b2", "#9333ea", "#ea580c", "#334155", "#be123c", "#4f46e5"]
    outcomes = sorted(sample["Delivery outcome"].fillna("Unknown").astype(str).unique())
    for idx, outcome in enumerate(outcomes):
        color_map.setdefault(outcome, fallback_colors[idx % len(fallback_colors)])

    for outcome, part in sample.groupby("Delivery outcome", dropna=False):
        outcome_label = str(outcome) if str(outcome).strip() else "Unknown"
        color = color_map.get(outcome_label, "#64748b")
        for _, row in part.iterrows():
            start_x, start_y = restart_origin_xy(row.get("side", "Left"), pitch)
            fig.add_trace(
                go.Scatter(
                    x=[start_x, row["vx_end"]],
                    y=[start_y, row["vy_end"]],
                    mode="lines",
                    line=dict(color=color, width=1.3),
                    opacity=0.28,
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        fig.add_trace(
            go.Scatter(
                x=part["vx_end"],
                y=part["vy_end"],
                mode="markers",
                name=outcome_label,
                marker=dict(size=10, color=color, opacity=0.84, line=dict(width=0.8, color="white")),
                customdata=np.stack(
                    [
                        part["Taker"].fillna("Unknown"),
                        part["Technique"].fillna("Unknown") if "Technique" in part.columns else pd.Series("Unknown", index=part.index),
                        part["Delivery height"].fillna("Unknown"),
                        part["Delivery outcome"].fillna("Unknown"),
                        part["Match"].fillna("Unknown"),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>Technique: %{customdata[1]}<br>Height: %{customdata[2]}<br>SP outcome: %{customdata[3]}<br>%{customdata[4]}<extra></extra>",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[0, pitch_width],
            y=[pitch_length, pitch_length],
            mode="markers",
            name="Restart spot",
            marker=dict(size=11, color="#0f172a", symbol="circle-open", line=dict(width=2, color="#0f172a")),
            hoverinfo="skip",
        )
    )

    fig = add_half_vertical_pitch_layout(fig, title, source_df=df)
    fig.update_layout(legend_title_text="SP outcome")
    return fig


def starting_location_map_figure(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    pitch = pitch_dimensions(df)
    pitch_width = float(pitch["width"])
    half_start = float(pitch["half_start"])
    pitch_length = float(pitch["length"])
    if df.empty:
        fig.add_annotation(text="No data available", x=pitch_width / 2, y=(half_start + pitch_length) / 2, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title, source_df=df)

    starts = df.copy()

    # Use pass start locations from SWE SP
    if "pass_x" not in starts.columns or "pass_y" not in starts.columns:
        if "location.pass" in starts.columns:
            pass_xy = starts["location.pass"].astype(str).str.replace(r"[\[\]]", "", regex=True).str.split(",", expand=True)
            if pass_xy.shape[1] >= 2:
                starts["pass_x"] = pd.to_numeric(pass_xy[0].str.strip(), errors="coerce")
                starts["pass_y"] = pd.to_numeric(pass_xy[1].str.strip(), errors="coerce")
        if "pass_x" not in starts.columns or "pass_y" not in starts.columns:
            fig.add_annotation(text="No start locations for current filter", x=pitch_width / 2, y=(half_start + pitch_length) / 2, showarrow=False, font=dict(size=18, color="#64748b"))
            return add_half_vertical_pitch_layout(fig, title, source_df=df)

    starts = starts[starts["pass_x"].notna() & starts["pass_y"].notna()].copy()
    starts = unique_start_events(starts)

    if starts.empty:
        fig.add_annotation(text="No start locations for current filter", x=pitch_width / 2, y=(half_start + pitch_length) / 2, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title, source_df=df)

    starts["plot_x"], starts["plot_y"] = coords_to_statsbomb(starts, "pass_x", "pass_y")
    starts["vx"], starts["vy"] = vertical_coords_from_pitch(starts["plot_x"], starts["plot_y"], pitch)

    color_map = {
        "From Free Kick": "#2563eb",
        "From Throw In": "#f59e0b",
    }

    if "SP_Type" in starts.columns:
        groups = starts.groupby("SP_Type", dropna=False)
    else:
        starts["SP_Type"] = "Start location"
        groups = starts.groupby("SP_Type", dropna=False)

    for sp_type, part in groups:
        color = color_map.get(str(sp_type), "#7c3aed")
        fig.add_trace(
            go.Scatter(
                x=part["vx"],
                y=part["vy"],
                mode="markers",
                name=str(sp_type),
                marker=dict(
                    size=10,
                    color=color,
                    opacity=0.82,
                    line=dict(width=0.8, color="white"),
                ),
                customdata=np.stack(
                    [
                        part["Team"].fillna("Unknown") if "Team" in part.columns else pd.Series(["Unknown"] * len(part)),
                        part["Taker"].fillna("Unknown") if "Taker" in part.columns else pd.Series(["Unknown"] * len(part)),
                        part["Match"].fillna("Unknown") if "Match" in part.columns else pd.Series(["Unknown"] * len(part)),
                        part["minute"].fillna(0) if "minute" in part.columns else pd.Series([0] * len(part)),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>Taker: %{customdata[1]}<br>%{customdata[2]}<br>Minute: %{customdata[3]}<extra></extra>",
            )
        )

    return add_half_vertical_pitch_layout(fig, title, source_df=df)


FK_PITCH_ZONES = ["Left Wide", "Left Half Space", "Central", "Right Half Space", "Right Wide"]

def classify_fk_pitch_zone(pass_y: pd.Series, pitch_width: float = 80.0) -> pd.Series:
    """Classify FK start location y-coordinate into 5 horizontal zones."""
    w = pitch_width
    return pd.cut(
        pass_y,
        bins=[-0.001, w * 0.2, w * 0.38, w * 0.52, w * 0.70, w + 1],
        labels=["Left Wide", "Left Half Space", "Central", "Right Half Space", "Right Wide"],
    ).astype(str)


def freekick_start_end_arrow_figure(df: pd.DataFrame, title: str) -> go.Figure:
    """Show FK start locations as circles with arrows pointing to delivery end locations."""
    fig = go.Figure()
    pitch = pitch_dimensions(df)
    pitch_width = float(pitch["width"])
    half_start = float(pitch["half_start"])
    pitch_length = float(pitch["length"])

    if df.empty:
        fig.add_annotation(text="No data available", x=pitch_width / 2, y=(half_start + pitch_length) / 2, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title, source_df=df)

    has_start = "pass_x" in df.columns and "pass_y" in df.columns
    has_end = "delivery_end_x" in df.columns and "delivery_end_y" in df.columns

    if not has_start:
        fig.add_annotation(text="No start location data available", x=pitch_width / 2, y=(half_start + pitch_length) / 2, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title, source_df=df)

    starts = df[df["pass_x"].notna() & df["pass_y"].notna()].copy()
    starts = unique_start_events(starts)

    if starts.empty:
        fig.add_annotation(text="No start locations for current filter", x=pitch_width / 2, y=(half_start + pitch_length) / 2, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title, source_df=df)

    starts["plot_x"], starts["plot_y"] = coords_to_statsbomb(starts, "pass_x", "pass_y")
    starts["vx"], starts["vy"] = vertical_coords_from_pitch(starts["plot_x"], starts["plot_y"], pitch)

    # Draw start location circles
    fig.add_trace(
        go.Scatter(
            x=starts["vx"], y=starts["vy"],
            mode="markers",
            name="Start",
            marker=dict(size=10, color="#f59e0b", opacity=0.9, line=dict(width=1.5, color="white")),
            hovertemplate="Taker: %{customdata[0]}<br>Minute: %{customdata[1]}<extra></extra>",
            customdata=np.stack([
                starts["Taker"].fillna("Unknown") if "Taker" in starts.columns else pd.Series(["Unknown"] * len(starts)),
                starts["minute"].fillna(0) if "minute" in starts.columns else pd.Series([0] * len(starts)),
            ], axis=1),
        )
    )

    # Draw arrows to end locations if available
    if has_end:
        ends = starts[starts["delivery_end_x"].notna() & starts["delivery_end_y"].notna()].copy()
        if not ends.empty:
            ends["end_plot_x"], ends["end_plot_y"] = coords_to_statsbomb(ends, "delivery_end_x", "delivery_end_y")
            ends["end_vx"], ends["end_vy"] = vertical_coords_from_pitch(ends["end_plot_x"], ends["end_plot_y"], pitch)

            # Build line segments with None separators for efficiency
            xs: list = []
            ys: list = []
            for _, row in ends.head(150).iterrows():
                xs.extend([row["vx"], row["end_vx"], None])
                ys.extend([row["vy"], row["end_vy"], None])

            fig.add_trace(
                go.Scatter(
                    x=xs, y=ys,
                    mode="lines",
                    name="Delivery",
                    line=dict(color="#60a5fa", width=1.5),
                    opacity=0.65,
                    hoverinfo="skip",
                )
            )
            # End location markers
            fig.add_trace(
                go.Scatter(
                    x=ends.head(150)["end_vx"], y=ends.head(150)["end_vy"],
                    mode="markers",
                    name="End",
                    marker=dict(size=8, color="#60a5fa", symbol="triangle-right", opacity=0.85),
                    hoverinfo="skip",
                )
            )

    return add_half_vertical_pitch_layout(fig, title, source_df=df)


@st.cache_data(show_spinner="Loading data…")
def build_summary_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if df.empty or "Team" not in df.columns:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Sequence-based summaries for SP pages; corner files may carry empty possession columns after concat.
    if _has_values(df, "possession"):
        rows = []
        for team, part in df.groupby("Team", dropna=False):
            sequences = int(part["possession"].nunique())
            matches = _match_count(part)

            shot_part = part[part["is_shot"]] if "is_shot" in part.columns else part.iloc[0:0]
            goal_part = part[part["is_goal"]] if "is_goal" in part.columns else part.iloc[0:0]

            shots = int(shot_part["possession"].nunique()) if not shot_part.empty else 0
            goals = int(goal_part["possession"].nunique()) if not goal_part.empty else 0

            if set(["possession", "shot_x", "shot_y", "xg"]).issubset(part.columns):
                xg_df = part[part["shot_x"].notna()][["possession", "shot_x", "shot_y", "xg"]].drop_duplicates()
                total_xg = float(xg_df["xg"].sum()) if not xg_df.empty else 0.0
                avg_xg = float(xg_df["xg"].mean()) if not xg_df.empty else 0.0
            else:
                total_xg = 0.0
                avg_xg = 0.0

            rows.append({
                "Team": team,
                "Matches": matches,
                "Set_Pieces": sequences,
                "Shots": shots,
                "Goals": goals,
                "Total_xG": total_xg,
                "Avg_xG": avg_xg,
            })

        summary = pd.DataFrame(rows).sort_values(["Total_xG", "Goals", "Shots"], ascending=False)
    else:
        summary = (
            df.groupby("Team", dropna=False)
            .agg(
                Matches=("match_id", "nunique") if _has_values(df, "match_id") else ("Match", "nunique") if _has_values(df, "Match") else ("Team", "size"),
                Set_Pieces=("Team", "size"),
                Shots=("is_shot", "sum"),
                Goals=("is_goal", "sum"),
                Total_xG=("xg", "sum"),
                Avg_xG=("xg", "mean"),
            )
            .reset_index()
            .sort_values(["Total_xG", "Goals", "Shots"], ascending=False)
        )

    summary["Shot conversion %"] = np.where(summary["Shots"] > 0, (summary["Goals"] / summary["Shots"] * 100).round(1), 0)
    summary["Avg_xG"] = summary["Avg_xG"].fillna(0).round(3)
    summary["Total_xG"] = summary["Total_xG"].fillna(0).round(2)

    technique_mix = (
        df.groupby(["Technique", "Delivery height"], dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    ) if set(["Technique", "Delivery height"]).issubset(df.columns) else pd.DataFrame()

    outcome_mix = (
        df.groupby(["Delivery outcome", "Shot outcome"], dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    ) if set(["Delivery outcome", "Shot outcome"]).issubset(df.columns) else pd.DataFrame()

    return summary, technique_mix, outcome_mix


def _rate(numerator: float, denominator: float) -> float:
    return round((numerator / denominator * 100), 1) if denominator else 0.0


def set_piece_kpi_values(df: pd.DataFrame) -> dict[str, object]:
    if df.empty:
        return {
            "matches": 0,
            "restarts": 0,
            "shots": 0,
            "goals": 0,
            "total_xg": 0.0,
            "shot_rate": 0.0,
            "goal_conversion": 0.0,
            "xg_per_restart": 0.0,
            "xg_per_100": 0.0,
            "xg_per_shot": 0.0,
            "top_taker": "Unknown",
            "top_shooter": "Unknown",
            "top_delivery": "Unknown",
            "top_outcome": "Unknown",
        }

    starts = unique_start_events(df)
    shots_df = unique_shot_events(df)
    restarts = int(len(starts)) if not starts.empty else int(len(df))
    shots = int(len(shots_df))
    goals = int(shots_df["is_goal"].sum()) if "is_goal" in shots_df.columns and not shots_df.empty else 0
    total_xg = float(shots_df["xg"].fillna(0).sum()) if "xg" in shots_df.columns and not shots_df.empty else 0.0
    matches = _match_count(df)

    def top_value(source: pd.DataFrame, column: str) -> str:
        if column not in source.columns or source.empty:
            return "Unknown"
        values = source[column].dropna().astype(str)
        values = values[values.str.strip().ne("") & values.str.lower().ne("unknown")]
        return values.value_counts().index[0] if not values.empty else "Unknown"

    return {
        "matches": matches,
        "restarts": restarts,
        "shots": shots,
        "goals": goals,
        "total_xg": total_xg,
        "shot_rate": _rate(shots, restarts),
        "goal_conversion": _rate(goals, shots),
        "xg_per_restart": round(total_xg / restarts, 3) if restarts else 0.0,
        "xg_per_100": round(total_xg / restarts * 100, 2) if restarts else 0.0,
        "xg_per_shot": round(total_xg / shots, 3) if shots else 0.0,
        "top_taker": top_value(starts, "Taker"),
        "top_shooter": top_value(shots_df, "Shooter"),
        "top_delivery": top_value(starts, "Delivery height"),
        "top_outcome": top_value(starts, "Delivery outcome"),
    }


def render_set_piece_kpi_deck(df: pd.DataFrame, label: str = "Set pieces") -> None:
    kpi = set_piece_kpi_values(df)
    cards = [
        ("Restarts", f"{kpi['restarts']:,}", f"{kpi['matches']:,} matches", False),
        ("Shot creation", f"{kpi['shot_rate']:.1f}%", f"{kpi['shots']:,} shots", True),
        ("xG / 100", f"{kpi['xg_per_100']:.2f}", "Threat per 100 restarts", False),
        ("xG / shot", f"{kpi['xg_per_shot']:.3f}", "Shot quality", True),
        ("Goals", f"{kpi['goals']:,}", f"{kpi['goal_conversion']:.1f}% conversion", False),
        ("Total xG", f"{kpi['total_xg']:.2f}", label, True),
    ]
    html = "<div class='mm-kpi-deck'>"
    for title, value, note, is_red in cards:
        cls = "mm-kpi-card is-red" if is_red else "mm-kpi-card"
        html += (
            f"<div class='{cls}'>"
            f"<div class='mm-kpi-label'>{escape(str(title))}</div>"
            f"<div class='mm-kpi-value'>{escape(str(value))}</div>"
            f"<div class='mm-kpi-help'>{escape(str(note))}</div>"
            "</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    reads = [
        ("Primary taker", kpi["top_taker"]),
        ("Main delivery", kpi["top_delivery"]),
        ("Best shooter", kpi["top_shooter"]),
    ]
    read_html = "<div class='mm-read-strip'>"
    for title, value in reads:
        read_html += (
            "<div class='mm-read-card'>"
            f"<div class='mm-read-title'>{escape(str(title))}</div>"
            f"<div class='mm-read-value'>{escape(str(value))}</div>"
            "</div>"
        )
    read_html += "</div>"
    st.markdown(read_html, unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading data…")
def build_team_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Team" not in df.columns:
        return pd.DataFrame()

    base = add_delivery_zones(unique_start_events(df))
    rows = []
    for team, part in base.groupby("Team", dropna=False):
        events = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        matches = _match_count(part)
        takers = int(part["Taker"].nunique()) if "Taker" in part.columns else 0
        rows.append(
            {
                "Team": team,
                "Matches": matches,
                "Events": events,
                "Takers": takers,
                "Shots": shots,
                "Goals": goals,
                "Shot rate %": _rate(shots, events),
                "Goals / shot %": _rate(goals, shots),
                "Total xG": round(total_xg, 2),
                "xG / event": round(total_xg / events, 3) if events else 0,
                "xG / 100": round(total_xg / events * 100, 2) if events else 0,
                "xG / shot": round(total_xg / shots, 3) if shots else 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["xG / 100", "Shot rate %", "Events"], ascending=False)


def build_taker_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    roles = build_role_archetypes(df)
    if roles.empty:
        return roles
    cols = [
        "Taker", "Team", "Role", "Archetype", "Events", "Shots", "Goals",
        "Shot rate", "xG / event", "xG / 100", "Top technique", "Top zone",
    ]
    return roles[[c for c in cols if c in roles.columns]]


def build_shooter_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    shots = unique_shot_events(df)
    if shots.empty or "Shooter" not in shots.columns:
        return pd.DataFrame()

    rows = []
    for shooter, part in shots.groupby("Shooter", dropna=False):
        attempts = int(len(part))
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        team = part["Team"].fillna("Unknown").mode().iloc[0] if "Team" in part.columns and not part["Team"].dropna().empty else "Unknown"
        rows.append(
            {
                "Shooter": shooter,
                "Team": team,
                "Shots": attempts,
                "Goals": goals,
                "Total xG": round(total_xg, 2),
                "xG / shot": round(total_xg / attempts, 3) if attempts else 0,
                "Conversion %": _rate(goals, attempts),
            }
        )
    return pd.DataFrame(rows).sort_values(["Total xG", "Shots", "Goals"], ascending=False)


def build_pattern_library(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = add_delivery_zones(unique_start_events(df))
    group_cols = [c for c in ["Team", "side", "Technique", "Delivery height", "Delivery zone", "Delivery outcome"] if c in base.columns]
    if not group_cols:
        return pd.DataFrame()

    rows = []
    for keys, part in base.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group_cols, keys))
        events = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        record.update(
            {
                "Events": events,
                "Shots": shots,
                "Goals": goals,
                "Shot rate %": _rate(shots, events),
                "Total xG": round(xg, 2),
                "xG / event": round(xg / events, 3) if events else 0,
                "xG / 100": round(xg / events * 100, 2) if events else 0,
                "xG / shot": round(xg / shots, 3) if shots else 0,
            }
        )
        rows.append(record)

    return (
        pd.DataFrame(rows)
        .sort_values(["Events", "xG / event", "Shot rate %"], ascending=False)
        .head(40)
    )


@st.cache_data(show_spinner="Loading data…")
def build_match_log(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = add_delivery_zones(unique_start_events(df))
    group_cols = [c for c in ["Match", "Team"] if c in base.columns]
    if not group_cols:
        return pd.DataFrame()

    rows = []
    for keys, part in base.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group_cols, keys))
        events = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        record.update(
            {
                "Events": events,
                "Shots": shots,
                "Goals": goals,
                "Shot rate %": _rate(shots, events),
                "Total xG": round(xg, 2),
            }
        )
        rows.append(record)

    return pd.DataFrame(rows).sort_values(["Match", "Total xG"], ascending=[True, False])


def render_analyst_table(
    df: pd.DataFrame,
    *,
    height: int = 360,
    max_rows: int = 500,
    color_cols: list[str] | None = None,
    invert_cols: list[str] | None = None,
) -> None:
    """Render a styled analyst table.

    color_cols:  columns to apply a heatmap to (default: all numeric)
    invert_cols: numeric columns where low = good (reversed colour scale)
    """
    if df.empty:
        st.info("No rows available for this view.")
        return

    display_df = df.head(max_rows)
    if len(df) > max_rows:
        st.caption(f"Showing {max_rows:,} of {len(df):,} rows. Use exports for the full table.")

    # Identify numeric columns eligible for colouring (booleans excluded — they break gradient math)
    all_numeric = [
        c for c in display_df.columns
        if pd.api.types.is_numeric_dtype(display_df[c]) and not pd.api.types.is_bool_dtype(display_df[c])
    ]
    target_cols = color_cols if color_cols is not None else all_numeric
    target_cols = [
        c for c in target_cols
        if c in display_df.columns
        and pd.api.types.is_numeric_dtype(display_df[c])
        and not pd.api.types.is_bool_dtype(display_df[c])
    ]
    inverted = set(invert_cols or [])

    # Base colour palette: white → steel-blue; inverted: white → rose-red
    BLUE_MAP = ["#222428", "#1e3a5f", "#1e4d8c", "#2563eb", "#1d4ed8"]
    RED_MAP  = ["#222428", "#3d1a1a", "#7f1d1d", "#dc2626", "#b91c1c"]

    def _col_gradient(s: pd.Series, cmap: list[str]) -> list[str]:
        """Return CSS background-color strings for a numeric series."""
        vals = pd.to_numeric(s, errors="coerce").astype(float)
        lo, hi = float(vals.min()), float(vals.max())
        if pd.isna(lo) or pd.isna(hi) or lo == hi:
            return [""] * len(s)
        n = len(cmap) - 1
        styles = []
        for v in vals:
            if pd.isna(v):
                styles.append("")
            else:
                v = float(v)
                t = (v - lo) / (hi - lo)
                idx = min(int(t * n), n - 1)
                lo_c, hi_c = cmap[idx], cmap[idx + 1]
                # linear interpolation within the swatch
                frac = t * n - idx
                def _blend(a: str, b: str, f: float) -> str:
                    def _hex2rgb(h: str) -> tuple[int, int, int]:
                        h = h.lstrip("#")
                        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                    ra, ga, ba = _hex2rgb(a)
                    rb, gb, bb = _hex2rgb(b)
                    r = int(ra + (rb - ra) * f)
                    g = int(ga + (gb - ga) * f)
                    b_ = int(ba + (bb - ba) * f)
                    lum = 0.299 * r + 0.587 * g + 0.114 * b_
                    txt = "#0b0f14" if lum > 140 else "#ffffff"
                    return f"background-color:#{r:02x}{g:02x}{b_:02x};color:{txt}"
                styles.append(_blend(lo_c, hi_c, frac))
        return styles

    styler = display_df.style.hide(axis="index")

    def _compact(v):
        """Compact number formatter: 1 500 000 → 1.5M, 100 000 → 100K, else 2dp."""
        if pd.isna(v):
            return ""
        if isinstance(v, float) and v == int(v) and abs(v) >= 1000:
            v = int(v)
        if isinstance(v, (int, np.integer)):
            if abs(v) >= 1_000_000:
                return f"{v/1_000_000:.1f}M"
            if abs(v) >= 1_000:
                return f"{v/1_000:.0f}K"
            return f"{v:,}"
        return f"{v:,.2f}"

    # Format numeric columns
    for col in all_numeric:
        sample = display_df[col].dropna()
        if len(sample) == 0:
            continue
        if pd.api.types.is_integer_dtype(display_df[col]):
            styler = styler.format({col: _compact})
        else:
            styler = styler.format({col: _compact})

    # Column alignment: numbers right, text left
    text_cols = [c for c in display_df.columns if c not in all_numeric]
    for col in all_numeric:
        styler = styler.set_properties(subset=[col], **{
            "text-align": "right",
            "font-variant-numeric": "tabular-nums",
        })
    for col in text_cols:
        styler = styler.set_properties(subset=[col], **{"text-align": "left"})

    # Per-column header alignment to match
    col_header_styles: dict[str, list[dict]] = {}
    for col in display_df.columns:
        align = "right" if col in all_numeric else "left"
        col_header_styles[col] = [{"selector": "th", "props": [("text-align", align)]}]
    if col_header_styles:
        styler = styler.set_table_styles(col_header_styles, overwrite=False, axis=0)

    # Apply per-column gradients
    for col in target_cols:
        cmap = RED_MAP if col in inverted else BLUE_MAP
        styler = styler.apply(lambda s, c=col, cm=cmap: _col_gradient(s, cm), subset=[col])

    # Table chrome — dark theme (rendered as plain HTML, not st.dataframe iframe)
    styler = styler.set_table_styles([
        {"selector": "thead th", "props": [
            ("background-color", "#1e2026"), ("color", "#9ca3af"),
            ("font-size", ".68rem"), ("font-weight", "700"),
            ("letter-spacing", ".06em"), ("text-transform", "uppercase"),
            ("padding", ".45rem .65rem"),
            ("border-bottom", "1px solid rgba(255,255,255,0.08)"),
            ("border-right", "none"), ("white-space", "nowrap"),
            ("position", "sticky"), ("top", "0"), ("z-index", "1"),
        ]},
        {"selector": "tbody td", "props": [
            ("background-color", "#222428"),
            ("font-size", ".82rem"), ("font-weight", "500"),
            ("padding", ".38rem .65rem"),
            ("border-bottom", "1px solid rgba(255,255,255,0.05)"),
            ("border-right", "none"), ("white-space", "nowrap"),
            ("color", "#ffffff"),
        ]},
        {"selector": "tbody tr:hover td", "props": [
            ("background-color", "#2a2d35"),
        ]},
        {"selector": "table", "props": [
            ("border-collapse", "collapse"), ("width", "100%"),
            ("background-color", "#222428"),
        ]},
    ])

    html = styler.to_html(uuid_len=0, escape=False)
    st.markdown(
        f'<div style="overflow:auto;max-height:{height}px;'
        f'background:#222428;border-radius:5px;'
        f'border:1px solid rgba(255,255,255,0.08)">'
        f'{html}</div>',
        unsafe_allow_html=True,
    )


def _to_statsbomb_xy(x: object, y: object, pitch_name: str = "statsbomb") -> tuple[float, float]:
    px = pd.to_numeric(pd.Series([x]), errors="coerce").iloc[0]
    py = pd.to_numeric(pd.Series([y]), errors="coerce").iloc[0]
    if pitch_name == "opta":
        px = px * (PITCH_LENGTH / OPTA_PITCH_LENGTH)
        py = py * (PITCH_WIDTH / OPTA_PITCH_WIDTH)
    return px, py

def freekick_zone(x: object, y: object, pitch_name: str = "statsbomb") -> str:
    px, py = _to_statsbomb_xy(x, y, pitch_name)
    if pd.isna(px) or pd.isna(py):
        return "Unknown"
    if px >= 96 and 24 <= py <= 56:
        return "Direct threat"
    if px >= 82 and (py < 24 or py > 56):
        return "Wide delivery"
    if px >= 82:
        return "Advanced central"
    if px >= 60:
        return "Middle third"
    return "Deep restart"


def freekick_channel(y: object, pitch_name: str = "statsbomb") -> str:
    _, py = _to_statsbomb_xy(0, y, pitch_name)
    if pd.isna(py):
        return "Unknown"
    if py < 18:
        return "Left wide"
    if py < 32:
        return "Left half-space"
    if py <= 48:
        return "Central"
    if py <= 62:
        return "Right half-space"
    return "Right wide"


def freekick_sequence_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df.copy()
    if "pass_x" not in base.columns and "restart_x" in base.columns:
        base["pass_x"] = base["restart_x"]
        base["pass_y"] = base["restart_y"]
    if "pass_x" not in base.columns or "pass_y" not in base.columns:
        return pd.DataFrame()

    group_cols = [c for c in ["match_id", "possession", "Team"] if c in base.columns]
    if len(group_cols) < 2:
        return pd.DataFrame()

    rows = []
    for keys, part in base.sort_values(["minute", "second"] if {"minute", "second"}.issubset(base.columns) else group_cols).groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group_cols, keys))
        first = part.iloc[0]
        pitch_name = "opta" if str(first.get("League", "")) == "UAE Pro League" else "statsbomb"
        shots = unique_shot_events(part)
        total_xg = float(shots["xg"].fillna(0).sum()) if "xg" in shots.columns and not shots.empty else 0.0
        goals = int(shots["is_goal"].sum()) if "is_goal" in shots.columns and not shots.empty else 0
        record.update(
            {
                "Match": first.get("Match", record.get("match_id", "Unknown")),
                "League": first.get("League", ""),
                "Minute": int(first.get("minute", 0)) if pd.notna(first.get("minute", np.nan)) else 0,
                "Origin x": round(float(first.get("pass_x", np.nan)), 1) if pd.notna(first.get("pass_x", np.nan)) else np.nan,
                "Origin y": round(float(first.get("pass_y", np.nan)), 1) if pd.notna(first.get("pass_y", np.nan)) else np.nan,
                "Zone": freekick_zone(first.get("pass_x", np.nan), first.get("pass_y", np.nan), pitch_name),
                "Channel": freekick_channel(first.get("pass_y", np.nan), pitch_name),
                "Initial taker": first.get("Taker", "Unknown"),
                "Initial height": first.get("Delivery height", "Unknown"),
                "Actions": int(len(part)),
                "Shots": int(len(shots)),
                "Goals": goals,
                "Total xG": round(total_xg, 3),
                "Best shooter": shots.sort_values("xg", ascending=False).iloc[0].get("Shooter", "Unknown") if not shots.empty and "xg" in shots.columns else "Unknown",
                "Best shot xG": round(float(shots["xg"].max()), 3) if not shots.empty and "xg" in shots.columns else 0.0,
                "Shot outcome": shots.iloc[0].get("Shot outcome", "No shot") if not shots.empty else "No shot",
            }
        )
        rows.append(record)

    return pd.DataFrame(rows).sort_values(["Total xG", "Shots", "Minute"], ascending=[False, False, True])


def freekick_zone_summary(df: pd.DataFrame) -> pd.DataFrame:
    seq = freekick_sequence_summary(df)
    if seq.empty:
        return pd.DataFrame()
    summary = (
        seq.groupby(["Zone", "Channel"], dropna=False)
        .agg(
            Sequences=("Zone", "size"),
            Shots=("Shots", "sum"),
            Shot_Sequences=("Shots", lambda s: int((s > 0).sum())),
            Goals=("Goals", "sum"),
            Total_xG=("Total xG", "sum"),
            Avg_xG=("Total xG", "mean"),
            Avg_Actions=("Actions", "mean"),
        )
        .reset_index()
    )
    summary["Shot sequence %"] = summary.apply(lambda r: _rate(r["Shot_Sequences"], r["Sequences"]), axis=1)
    summary["Shots / seq"] = (summary["Shots"] / summary["Sequences"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    summary["Total_xG"] = summary["Total_xG"].round(2)
    summary["Avg_xG"] = summary["Avg_xG"].round(3)
    summary["Avg_Actions"] = summary["Avg_Actions"].round(1)
    summary = summary.sort_values(["Total_xG", "Shots / seq", "Sequences"], ascending=False)
    return summary.drop(columns=[c for c in ["Shot_Sequences", "Shot sequence %"] if c in summary.columns])


def freekick_taker_summary(df: pd.DataFrame) -> pd.DataFrame:
    seq = freekick_sequence_summary(df)
    if seq.empty:
        return pd.DataFrame()
    summary = (
        seq.groupby("Initial taker", dropna=False)
        .agg(
            Team=("Team", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Sequences=("Initial taker", "size"),
            Shots=("Shots", "sum"),
            Shot_Sequences=("Shots", lambda s: int((s > 0).sum())),
            Goals=("Goals", "sum"),
            Total_xG=("Total xG", "sum"),
            Avg_xG=("Total xG", "mean"),
            Main_zone=("Zone", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Main_channel=("Channel", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Main_height=("Initial height", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
        )
        .reset_index()
        .rename(columns={"Initial taker": "Taker"})
    )
    summary["Shot sequence %"] = summary.apply(lambda r: _rate(r["Shot_Sequences"], r["Sequences"]), axis=1)
    summary["Shots / seq"] = (summary["Shots"] / summary["Sequences"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    summary["Total_xG"] = summary["Total_xG"].round(2)
    summary["Avg_xG"] = summary["Avg_xG"].round(3)
    summary = summary.sort_values(["Total_xG", "Sequences", "Avg_xG"], ascending=False)
    return summary.drop(columns=[c for c in ["Shot_Sequences", "Shot sequence %"] if c in summary.columns])


def freekick_shooter_summary(df: pd.DataFrame) -> pd.DataFrame:
    shots = unique_shot_events(df)
    if shots.empty or "Shooter" not in shots.columns:
        return pd.DataFrame()
    summary = (
        shots.groupby("Shooter", dropna=False)
        .agg(
            Team=("Team", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Shots=("Shooter", "size"),
            Goals=("is_goal", "sum") if "is_goal" in shots.columns else ("Shooter", "size"),
            Total_xG=("xg", "sum") if "xg" in shots.columns else ("Shooter", "size"),
            Avg_xG=("xg", "mean") if "xg" in shots.columns else ("Shooter", "size"),
            Best_xG=("xg", "max") if "xg" in shots.columns else ("Shooter", "size"),
        )
        .reset_index()
    )
    summary["Conversion %"] = summary.apply(lambda r: _rate(r["Goals"], r["Shots"]), axis=1)
    for col in ["Total_xG", "Avg_xG", "Best_xG"]:
        summary[col] = pd.to_numeric(summary[col], errors="coerce").fillna(0).round(3)
    return summary.sort_values(["Total_xG", "Shots", "Goals"], ascending=False)


def freekick_origin_map_figure(df: pd.DataFrame, title: str = "Freekick origins"):
    import matplotlib.pyplot as plt
    from mplsoccer import VerticalPitch

    # Lane definitions: (boundary_start, boundary_end, label, bg_color, dot_color)
    LANES = [
        (0,  18, "Left\nwide",        "#dbeafe", "#1d4ed8"),
        (18, 30, "Left half\nspace",  "#fef9c3", "#b45309"),
        (30, 50, "Central\narea",     "#dcfce7", "#15803d"),
        (50, 62, "Right half\nspace", "#fef9c3", "#b45309"),
        (62, 80, "Right\nwide",       "#dbeafe", "#1d4ed8"),
    ]

    fig, ax = plt.subplots(figsize=(6, 9), dpi=130)
    fig.patch.set_facecolor("#161922")
    pitch_plot = VerticalPitch(
        pitch_type="statsbomb",
        pitch_color="#1a2438",
        line_color="#4b5563",
        linewidth=1.2,
        line_zorder=3,
    )
    pitch_plot.draw(ax=ax)

    ax.set_ylim([-14, ax.get_ylim()[1]])

    # Lane background tints and dashed dividers
    for i, (x0, x1, label, bg, _) in enumerate(LANES):
        ax.axvspan(x0, x1, alpha=0.15, color=bg, zorder=1)
        if i > 0:
            ax.axvline(x=x0, color="#94a3b8", linestyle="--", linewidth=0.9, alpha=0.65, zorder=2)
        ax.text((x0 + x1) / 2, -7, label, ha="center", va="center",
                fontsize=6.5, color="#9ca3af", fontweight="bold")

    ax.set_title(title, fontsize=12, fontweight="bold", color="#f1f5f9", pad=8)

    seq = freekick_sequence_summary(df)
    if seq.empty or "Origin x" not in seq.columns:
        ax.text(40, 60, "No freekick origins available", ha="center", va="center", color="#94a3b8", fontsize=11)
        fig.tight_layout()
        return fig

    seq = seq.copy()
    seq["Plot x"], seq["Plot y"] = coords_to_statsbomb(seq, "Origin x", "Origin y")
    plot_df = seq.dropna(subset=["Plot x", "Plot y"]).copy()

    # Assign each point its lane based on StatsBomb y (= VerticalPitch x)
    def _lane_for_y(y: float) -> int:
        for i, (x0, x1, *_) in enumerate(LANES):
            if x0 <= y < x1:
                return i
        return len(LANES) - 1

    plot_df["Lane"] = plot_df["Plot y"].apply(_lane_for_y)

    for i, (x0, x1, label, _, dot_color) in enumerate(LANES):
        part = plot_df[plot_df["Lane"] == i]
        if part.empty:
            continue
        sizes = np.clip(part["Total xG"].fillna(0).to_numpy() * 180 + 28, 28, 130)
        pitch_plot.scatter(
            part["Plot x"],  # StatsBomb x (length) — VerticalPitch rotates this to vertical axis
            part["Plot y"],  # StatsBomb y (width)  — VerticalPitch rotates this to horizontal axis
            s=sizes,
            color=dot_color,
            edgecolors="white",
            linewidth=0.8,
            alpha=0.82,
            label=label.replace("\n", " "),
            ax=ax,
            zorder=4,
        )

    ax.legend(
        loc="lower left",
        fontsize=7,
        frameon=True,
        framealpha=0.85,
        facecolor="#1a2438",
        edgecolor="#4b5563",
        labelcolor="#cbd5e1",
        title="Lane",
        title_fontsize=7,
    )
    fig.tight_layout()
    return fig


def throwin_zone(x: object, pitch_name: str = "statsbomb") -> str:
    px, _ = _to_statsbomb_xy(x, 0, pitch_name)
    if pd.isna(px):
        return "Unknown"
    if px >= 102:
        return "Final-third pressure"
    if px >= 84:
        return "Attacking channel"
    if px >= 60:
        return "Middle-third platform"
    if px >= 36:
        return "Build-up restart"
    return "Defensive throw"


def throwin_side(y: object, pitch_name: str = "statsbomb") -> str:
    _, py = _to_statsbomb_xy(0, y, pitch_name)
    if pd.isna(py):
        return "Unknown"
    return "Left touchline" if py <= 40 else "Right touchline"


def throwin_sequence_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Vectorised: one row in the prepared data == one sequence."""
    if df.empty:
        return pd.DataFrame()

    seq = df.copy()

    # Side from pre-computed column or pass_y
    if "side" in seq.columns:
        seq["Side"] = seq["side"].map({"Left": "Left touchline", "Right": "Right touchline"}).fillna("Unknown")
    elif "pass_y" in seq.columns:
        seq["Side"] = np.where(pd.to_numeric(seq["pass_y"], errors="coerce").fillna(40) <= 40, "Left touchline", "Right touchline")
    else:
        seq["Side"] = "Unknown"

    # Zone from Start_Third where available, else pass_x thresholds
    if "Start_Third" in seq.columns:
        zone_map = {"Attacking third": "Attacking channel", "Middle third": "Middle-third platform", "Defensive third": "Defensive throw"}
        seq["Zone"] = seq["Start_Third"].map(zone_map).fillna("Unknown")
    elif "pass_x" in seq.columns:
        px = pd.to_numeric(seq["pass_x"], errors="coerce")
        seq["Zone"] = pd.cut(
            px,
            bins=[-np.inf, 36, 60, 84, 102, np.inf],
            labels=["Defensive throw", "Build-up restart", "Middle-third platform", "Attacking channel", "Final-third pressure"],
        ).astype(str)
    else:
        seq["Zone"] = "Unknown"

    # Box entry flag
    seq["Box entry"] = seq["Next_3_Box_Entry"].astype(bool) if "Next_3_Box_Entry" in seq.columns else False

    # Shot/goal/xG — already one row per event in prepared data
    seq["Shots"] = seq["is_shot"].astype(int) if "is_shot" in seq.columns else 0
    seq["Goals"] = seq["is_goal"].astype(int) if "is_goal" in seq.columns else 0
    xg_col = "xg" if "xg" in seq.columns else ("shot.statsbomb_xg" if "shot.statsbomb_xg" in seq.columns else None)
    seq["Total xG"] = pd.to_numeric(seq[xg_col], errors="coerce").fillna(0).round(3) if xg_col else 0.0
    seq["Best shot xG"] = seq["Total xG"]
    seq["Best shooter"] = seq.get("Shooter", pd.Series("Unknown", index=seq.index)).fillna("Unknown")
    seq["Shot outcome"] = seq.get("Shot outcome", pd.Series("No shot", index=seq.index)).fillna("No shot")

    seq["Actions"] = 1
    seq["Initial taker"] = seq.get("Taker", pd.Series("Unknown", index=seq.index)).fillna("Unknown")
    seq["Initial height"] = seq.get("Delivery height", pd.Series("Unknown", index=seq.index)).fillna("Unknown")
    seq["Minute"] = pd.to_numeric(seq.get("minute", pd.Series(0, index=seq.index)), errors="coerce").fillna(0).astype(int)

    if "pass_x" in seq.columns:
        seq["Origin x"] = pd.to_numeric(seq["pass_x"], errors="coerce").round(1)
        seq["Origin y"] = pd.to_numeric(seq["pass_y"], errors="coerce").round(1)
    elif "restart_x" in seq.columns:
        seq["Origin x"] = pd.to_numeric(seq["restart_x"], errors="coerce").round(1)
        seq["Origin y"] = pd.to_numeric(seq["restart_y"], errors="coerce").round(1)
    else:
        seq["Origin x"] = np.nan
        seq["Origin y"] = np.nan

    # Carry through shot coords as delivery end when no dedicated end column exists
    if "delivery_end_x" not in seq.columns:
        seq["delivery_end_x"] = pd.to_numeric(seq["shot_x"], errors="coerce") if "shot_x" in seq.columns else np.nan
        seq["delivery_end_y"] = pd.to_numeric(seq["shot_y"], errors="coerce") if "shot_y" in seq.columns else np.nan

    return seq.sort_values(["Box entry", "Total xG", "Shots", "Minute"], ascending=[False, False, False, True])


def throwin_zone_summary(df: pd.DataFrame) -> pd.DataFrame:
    seq = throwin_sequence_summary(df)
    if seq.empty:
        return pd.DataFrame()
    summary = (
        seq.groupby(["Zone", "Side"], dropna=False)
        .agg(
            Sequences=("Zone", "size"),
            Shots=("Shots", "sum"),
            Goals=("Goals", "sum"),
            Total_xG=("Total xG", "sum"),
            Avg_xG=("Total xG", "mean"),
            Box_entries=("Box entry", "sum"),
        )
        .reset_index()
    )
    summary["Shots / seq"] = (summary["Shots"] / summary["Sequences"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    summary["Box entry %"] = (summary["Box_entries"] / summary["Sequences"] * 100).round(1)
    summary["Total_xG"] = summary["Total_xG"].round(2)
    summary["Avg_xG"] = summary["Avg_xG"].round(3)
    summary = summary.drop(columns=["Box_entries"])
    return summary.sort_values(["Box entry %", "Shots / seq", "Sequences"], ascending=False)


def throwin_taker_summary(df: pd.DataFrame) -> pd.DataFrame:
    seq = throwin_sequence_summary(df)
    if seq.empty:
        return pd.DataFrame()

    grp = seq.groupby("Initial taker", dropna=False)
    summary = grp.agg(
        Sequences=("Initial taker", "size"),
        Shots=("Shots", "sum"),
        Goals=("Goals", "sum"),
        Total_xG=("Total xG", "sum"),
        Avg_xG=("Total xG", "mean"),
        Box_entries=("Box entry", "sum"),
    ).reset_index().rename(columns={"Initial taker": "Taker"})

    # Fastest-mode columns via value_counts on the first element of each group
    for col, target in [("Team", "Team"), ("Zone", "Main_zone"), ("Side", "Main_side"), ("Initial height", "Main_height")]:
        if col in seq.columns:
            first_vals = seq.groupby("Initial taker", dropna=False)[col].agg(lambda s: s.value_counts().index[0] if len(s) else "Unknown")
            summary = summary.merge(first_vals.rename(target).reset_index().rename(columns={"Initial taker": "Taker"}), on="Taker", how="left")
        else:
            summary[target] = "Unknown"

    summary["Shots / seq"] = (summary["Shots"] / summary["Sequences"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    summary["Box entry %"] = (summary["Box_entries"] / summary["Sequences"] * 100).round(1)
    summary["Total_xG"] = summary["Total_xG"].round(2)
    summary["Avg_xG"] = summary["Avg_xG"].round(3)
    summary = summary.drop(columns=["Box_entries"])
    return summary.sort_values(["Box entry %", "Sequences", "Shots / seq"], ascending=False)


def throwin_shooter_summary(df: pd.DataFrame) -> pd.DataFrame:
    shots = unique_shot_events(df)
    if shots.empty or "Shooter" not in shots.columns:
        return pd.DataFrame()
    summary = (
        shots.groupby("Shooter", dropna=False)
        .agg(
            Team=("Team", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Shots=("Shooter", "size"),
            Goals=("is_goal", "sum") if "is_goal" in shots.columns else ("Shooter", "size"),
            Total_xG=("xg", "sum") if "xg" in shots.columns else ("Shooter", "size"),
            Avg_xG=("xg", "mean") if "xg" in shots.columns else ("Shooter", "size"),
            Best_xG=("xg", "max") if "xg" in shots.columns else ("Shooter", "size"),
        )
        .reset_index()
    )
    summary["Conversion %"] = summary.apply(lambda r: _rate(r["Goals"], r["Shots"]), axis=1)
    for col in ["Total_xG", "Avg_xG", "Best_xG"]:
        summary[col] = pd.to_numeric(summary[col], errors="coerce").fillna(0).round(3)
    return summary.sort_values(["Total_xG", "Shots", "Goals"], ascending=False)


def throwin_delivery_map_figure(df: pd.DataFrame, title: str = "Throw-in deliveries") -> object:
    import matplotlib.pyplot as plt
    from mplsoccer import Pitch

    SIDE_COLORS = {"Left touchline": "#2563eb", "Right touchline": "#dc2626", "Unknown": "#94a3b8"}

    fig, ax = plt.subplots(figsize=(10, 7), dpi=120)
    fig.patch.set_facecolor("#161922")
    pitch_plot = Pitch(
        pitch_type="statsbomb",
        pitch_color="#1a2438",
        line_color="#4b5563",
        linewidth=1.2,
        line_zorder=3,
    )
    pitch_plot.draw(ax=ax)
    ax.set_title(title, fontsize=12, fontweight="bold", color="#f1f5f9", pad=8)

    seq = throwin_sequence_summary(df)
    if seq.empty or "Origin x" not in seq.columns:
        ax.text(60, 40, "No throw-in data available", ha="center", va="center", color="#94a3b8", fontsize=11)
        fig.tight_layout()
        return fig

    has_end = {"delivery_end_x", "delivery_end_y"}.issubset(seq.columns)
    plot_df = seq.dropna(subset=["Origin x", "Origin y"]).copy()
    plot_df["ox"], plot_df["oy"] = coords_to_statsbomb(plot_df, "Origin x", "Origin y")

    if has_end:
        end_df = plot_df.dropna(subset=["delivery_end_x", "delivery_end_y"]).copy()
        end_df["ex"], end_df["ey"] = coords_to_statsbomb(end_df, "delivery_end_x", "delivery_end_y")
    else:
        end_df = pd.DataFrame()

    for side, part in plot_df.groupby("Side", dropna=False):
        color = SIDE_COLORS.get(str(side), "#94a3b8")
        if not end_df.empty:
            arrows = end_df[end_df["Side"] == side]
            if not arrows.empty:
                pitch_plot.arrows(
                    arrows["ox"], arrows["oy"],
                    arrows["ex"], arrows["ey"],
                    color=color, alpha=0.3, width=1.0, headwidth=3, headlength=3,
                    ax=ax, zorder=4,
                )
        pitch_plot.scatter(
            part["ox"], part["oy"],
            s=np.clip(part["Total xG"].fillna(0) * 200 + 18, 18, 90),
            color=color,
            edgecolors="white",
            linewidth=0.6,
            alpha=0.75,
            label=str(side),
            ax=ax,
            zorder=5,
        )

    ax.legend(loc="lower right", fontsize=8, frameon=True, framealpha=0.9, title="Side", title_fontsize=8)
    fig.tight_layout()
    return fig


def throwin_outcome_zone_figure(df: pd.DataFrame, title: str = "Throw-in outcomes by zone") -> object:
    """Pitch map: throw-in origins coloured by tiered outcome within 3 actions.
    Attacking third  → goal > shot > box entry
    Middle third     → goal > shot > box entry > retain
    Defensive third  → moved into middle third (delivery_end_x ≥ 40)
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from mplsoccer import Pitch

    ZONES = [
        (80, 120, "Attacking\nthird",   "→ Into box",             "#dcfce7"),
        (40,  80, "Middle\nthird",      "→ Retain possession",    "#fef9c3"),
        ( 0,  40, "Defensive\nthird",   "→ Into middle third",    "#dbeafe"),
    ]

    # Tiered outcome colours (best → worst)
    C_GOAL    = "#15803d"  # dark green
    C_SHOT    = "#86efac"  # light green
    C_BOX     = "#f59e0b"  # amber — box entry, no shot
    C_RETAIN  = "#93c5fd"  # light blue — retained, no box entry
    C_ADVANCE = "#6366f1"  # indigo — defensive: advanced to middle third
    C_NONE    = "#e5e7eb"  # gray — nothing notable

    fig, ax = plt.subplots(figsize=(13, 7.5), dpi=120)
    fig.patch.set_facecolor("#161922")
    pitch_plot = Pitch(
        pitch_type="statsbomb",
        pitch_color="#1a2438",
        line_color="#4b5563",
        linewidth=1.2,
        line_zorder=4,
    )
    pitch_plot.draw(ax=ax)
    ax.set_ylim([-14, 80])

    # Zone bands + labels above pitch
    for x0, x1, zone_label, target_label, bg in ZONES:
        ax.axvspan(x0, x1, alpha=0.10, color=bg, zorder=1)
        cx = (x0 + x1) / 2
        ax.text(cx, -4, zone_label, ha="center", va="center",
                fontsize=8, fontweight="bold", color="#9ca3af")
        ax.text(cx, -10, target_label, ha="center", va="center",
                fontsize=6.5, color="#6b7280", style="italic")

    for xb in [40, 80]:
        ax.axvline(x=xb, color="#94a3b8", linestyle="--", linewidth=0.9, alpha=0.7, zorder=3)

    seq = throwin_sequence_summary(df)
    if seq.empty or "Origin x" not in seq.columns:
        ax.text(60, 40, "No throw-in data available", ha="center", va="center", color="#94a3b8", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold", color="#f1f5f9", pad=8)
        fig.tight_layout()
        return fig

    plot_df = seq.dropna(subset=["Origin x", "Origin y"]).copy()
    plot_df["ox"], plot_df["oy"] = coords_to_statsbomb(plot_df, "Origin x", "Origin y")

    # Real delivery ends only — no estimation
    if {"delivery_end_x", "delivery_end_y"}.issubset(plot_df.columns):
        plot_df["ex"], plot_df["ey"] = coords_to_statsbomb(plot_df, "delivery_end_x", "delivery_end_y")
    else:
        plot_df["ex"] = np.nan
        plot_df["ey"] = np.nan

    # _advanced: defensive throw that reached middle third (real end only)
    plot_df["_advanced"] = pd.to_numeric(plot_df["ex"], errors="coerce").fillna(0) >= 40

    def _outcome_color(row) -> str:
        ox = row.get("ox", 60)
        if row.get("Goals", 0):
            return C_GOAL
        if row.get("Shots", 0):
            return C_SHOT
        if ox >= 80:
            return C_BOX
        if ox >= 40:
            return C_BOX if row.get("Box entry", False) else C_RETAIN
        return C_ADVANCE if row.get("_advanced", False) else C_NONE

    plot_df["_color"] = plot_df.apply(_outcome_color, axis=1)

    # Draw in reverse priority order (best outcomes on top)
    for color, label, zorder in [
        (C_NONE,   "No advance",  5),
        (C_ADVANCE,"Into middle", 6),
        (C_RETAIN, "Retain",      7),
        (C_BOX,    "Box entry",   8),
        (C_SHOT,   "Shot",        9),
        (C_GOAL,   "Goal",       10),
    ]:
        pts = plot_df[plot_df["_color"] == color]
        if pts.empty:
            continue
        end_pts = pts.dropna(subset=["ex", "ey"])
        if not end_pts.empty:
            pitch_plot.arrows(
                end_pts["ox"], end_pts["oy"],
                end_pts["ex"], end_pts["ey"],
                color=color, alpha=0.25, width=0.8,
                headwidth=3, headlength=3,
                ax=ax, zorder=zorder,
            )
        pitch_plot.scatter(
            pts["ox"], pts["oy"],
            s=22, color=color, edgecolors="white", linewidth=0.5,
            alpha=0.82, ax=ax, zorder=zorder + 10,
        )

    ax.set_title(title, fontsize=12, fontweight="bold", color="#f1f5f9", pad=8)
    legend_patches = [
        mpatches.Patch(color=C_GOAL,    label="Goal"),
        mpatches.Patch(color=C_SHOT,    label="Shot (no goal)"),
        mpatches.Patch(color=C_BOX,     label="Box entry (no shot)"),
        mpatches.Patch(color=C_RETAIN,  label="Retain (no box entry)"),
        mpatches.Patch(color=C_ADVANCE, label="Into middle third"),
        mpatches.Patch(color=C_NONE,    label="No advance"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", fontsize=7.5,
              frameon=True, framealpha=0.9, ncol=1)
    fig.tight_layout()
    return fig


def kpi_row(df: pd.DataFrame) -> None:
    render_set_piece_kpi_deck(df)

def info_panel(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No rows match the current filters.")
        return
    notes = []
    base = unique_start_events(df)
    if "Technique" in base.columns:
        vc = base["Technique"].fillna("Unknown").value_counts().head(1)
        if not vc.empty:
            notes.append(f"Top technique: {vc.index[0]} ({int(vc.iloc[0])})")
    if "Taker" in base.columns:
        vc = base["Taker"].fillna("Unknown").value_counts().head(1)
        if not vc.empty:
            notes.append(f"Top taker: {vc.index[0]} ({int(vc.iloc[0])})")
    if notes:
        st.caption(" · ".join(notes))


def delivery_zone_label(x: object, y: object, pitch_name: str = "statsbomb") -> str:
    end_x = pd.to_numeric(pd.Series([x]), errors="coerce").iloc[0]
    end_y = pd.to_numeric(pd.Series([y]), errors="coerce").iloc[0]
    if pd.isna(end_x) or pd.isna(end_y):
        return "Unknown"
    if pitch_name == "opta":
        end_x = end_x * (PITCH_LENGTH / OPTA_PITCH_LENGTH)
        end_y = end_y * (PITCH_WIDTH / OPTA_PITCH_WIDTH)
    if end_x >= 114 and 30 <= end_y <= 50:
        return "Six-yard corridor"
    if end_x >= 114:
        return "Near/far post lane"
    if end_x >= 108 and 28 <= end_y <= 52:
        return "Penalty spot"
    if end_x >= 102 and 18 <= end_y <= 62:
        return "Edge of box"
    if end_x < 90:
        return "Short / recycle"
    return "Second ball zone"


def add_delivery_zones(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    if {"delivery_end_x", "delivery_end_y"}.issubset(enriched.columns):
        enriched["Delivery zone"] = [
            delivery_zone_label(x, y, "opta" if str(league) == "UAE Pro League" else "statsbomb")
            for x, y, league in zip(
                enriched["delivery_end_x"],
                enriched["delivery_end_y"],
                enriched["League"] if "League" in enriched.columns else pd.Series("", index=enriched.index),
            )
        ]
    elif "Delivery zone" not in enriched.columns:
        enriched["Delivery zone"] = "Unknown"
    return enriched

def mplsoccer_pitch_xy(df: pd.DataFrame, x_col: str, y_col: str, pitch: dict[str, object]) -> tuple[pd.Series, pd.Series]:
    length_coord, width_coord = coords_to_statsbomb(df, x_col, y_col)
    margin = 0.7
    length_coord = length_coord.clip(lower=float(pitch["half_start"]) + margin, upper=float(pitch["length"]) - margin)
    width_coord = width_coord.clip(lower=margin, upper=float(pitch["width"]) - margin)
    return length_coord, width_coord

def mplsoccer_center_xy(pitch: dict[str, object], x_share: float = 0.75) -> tuple[float, float]:
    return float(pitch["width"]) / 2, float(pitch["length"]) * x_share


@st.cache_data(show_spinner="Loading data…")
def build_role_archetypes(df: pd.DataFrame, label: str = "") -> pd.DataFrame:
    if df.empty or "Taker" not in df.columns:
        return pd.DataFrame()

    base = add_delivery_zones(unique_start_events(df))
    rows = []
    for taker, part in base.groupby("Taker", dropna=False):
        taker_name = str(taker) if str(taker).strip() else "Unknown"
        events = int(len(part))
        if events == 0:
            continue
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        shot_rate = shots / events if events else 0.0
        xg_per_event = total_xg / events if events else 0.0

        top_technique = part["Technique"].fillna("Unknown").mode().iloc[0] if "Technique" in part.columns and not part["Technique"].dropna().empty else "Unknown"
        top_height = part["Delivery height"].fillna("Unknown").mode().iloc[0] if "Delivery height" in part.columns and not part["Delivery height"].dropna().empty else "Unknown"
        top_zone = part["Delivery zone"].fillna("Unknown").mode().iloc[0] if "Delivery zone" in part.columns and not part["Delivery zone"].dropna().empty else "Unknown"
        team = part["Team"].fillna("Unknown").mode().iloc[0] if "Team" in part.columns and not part["Team"].dropna().empty else "Unknown"

        if events >= max(8, base.groupby("Taker").size().quantile(0.75)):
            role = "Primary taker"
        elif shot_rate >= 0.35 or xg_per_event >= 0.04:
            role = "Chance creator"
        elif top_zone == "Short / recycle":
            role = "Short option"
        else:
            role = "Rotation taker"

        technique_l = str(top_technique).lower()
        if "inswing" in technique_l:
            archetype = f"Inswing {top_zone.lower()}"
        elif "outswing" in technique_l:
            archetype = f"Outswing {top_zone.lower()}"
        elif top_zone == "Short / recycle":
            archetype = "Short-play connector"
        elif label == "Freekicks":
            archetype = f"Dead-ball {top_height.lower()}"
        else:
            archetype = f"Mixed {top_zone.lower()}"

        rows.append(
            {
                "Taker": taker_name,
                "Team": team,
                "Role": role,
                "Archetype": archetype,
                "Events": events,
                "Shots": shots,
                "Goals": goals,
                "Shot rate": round(shot_rate * 100, 1),
                "xG / event": round(xg_per_event, 3),
                "xG / 100": round(xg_per_event * 100, 2),
                "Top technique": top_technique,
                "Top zone": top_zone,
            }
        )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["xG / 100", "Shot rate", "Events"], ascending=False)


@st.cache_data(show_spinner="Loading data…")
def build_team_archetypes(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Team" not in df.columns:
        return pd.DataFrame()

    base = add_delivery_zones(unique_start_events(df))
    rows = []
    for team, part in base.groupby("Team", dropna=False):
        events = int(len(part))
        if events == 0:
            continue
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        zone = part["Delivery zone"].fillna("Unknown").mode().iloc[0] if "Delivery zone" in part.columns and not part["Delivery zone"].dropna().empty else "Unknown"
        height = part["Delivery height"].fillna("Unknown").mode().iloc[0] if "Delivery height" in part.columns and not part["Delivery height"].dropna().empty else "Unknown"
        technique = part["Technique"].fillna("Unknown").mode().iloc[0] if "Technique" in part.columns and not part["Technique"].dropna().empty else "Unknown"

        if shots / events >= 0.35:
            profile = "Direct shot hunters"
        elif zone == "Short / recycle":
            profile = "Short and second-phase"
        elif "High" in str(height):
            profile = "Aerial box load"
        else:
            profile = "Mixed delivery side"

        rows.append(
            {
                "Team": team,
                "Archetype": profile,
                "Events": events,
                "Shots": shots,
                "Goals": goals,
                "Shot rate": round(shots / events * 100, 1),
                "xG / event": round(total_xg / events, 3),
                "Primary delivery": f"{technique} · {zone}",
            }
        )
    return pd.DataFrame(rows).sort_values(["xG / event", "Shot rate", "Events"], ascending=False)


def generate_set_piece_insights(df: pd.DataFrame, label: str = "") -> list[str]:
    if df.empty:
        return ["No rows match the current filter, so the report cannot generate a reliable read."]

    base = add_delivery_zones(unique_start_events(df))
    insights: list[str] = []
    events = len(base)
    shots = int(base["is_shot"].sum()) if "is_shot" in base.columns else 0
    goals = int(base["is_goal"].sum()) if "is_goal" in base.columns else 0
    total_xg = float(base["xg"].fillna(0).sum()) if "xg" in base.columns else 0.0
    shot_rate = shots / events * 100 if events else 0
    insights.append(f"{label or 'Set pieces'} produced {shots} shots from {events} events ({shot_rate:.1f}% shot rate), worth {total_xg:.2f} xG and {goals} goals.")

    roles = build_role_archetypes(base, label)
    if not roles.empty:
        lead = roles.iloc[0]
        insights.append(f"Main taker profile: {lead['Taker']} is a {str(lead['Role']).lower()} for {lead['Team']}, most often showing as {lead['Archetype']}.")
        creator = roles.sort_values(["xG / event", "Shot rate", "Events"], ascending=False).iloc[0]
        insights.append(f"Best creation signal: {creator['Taker']} leads the filtered takers on xG/event ({creator['xG / event']:.3f}) with a {creator['Shot rate']:.1f}% shot rate.")

    teams = build_team_archetypes(base)
    if not teams.empty:
        top_team = teams.iloc[0]
        insights.append(f"Team archetype to prepare for: {top_team['Team']} profile as {str(top_team['Archetype']).lower()}, built around {top_team['Primary delivery']}.")

    if "Delivery zone" in base.columns:
        zone_counts = base["Delivery zone"].value_counts()
        if not zone_counts.empty:
            zone = zone_counts.index[0]
            share = zone_counts.iloc[0] / len(base) * 100
            insights.append(f"Dominant target area is {zone.lower()} ({share:.1f}% of deliveries with a classified end zone).")

    if "side" in base.columns:
        side_counts = base["side"].value_counts()
        if len(side_counts) > 0:
            insights.append(f"Restart side bias: {side_counts.index[0]} side accounts for {side_counts.iloc[0] / len(base) * 100:.1f}% of the sample.")

    return insights[:6]


def corner_landing_heatmap_figure(df: pd.DataFrame, colour_by: str = "density"):
    """KDE heatmap of corner delivery end locations (where the ball arrives in the box)."""
    import matplotlib.pyplot as plt
    from mplsoccer import VerticalPitch

    fig, ax = plt.subplots(figsize=(5, 7))
    fig.patch.set_facecolor("#161922")
    pitch = VerticalPitch(pitch_type="statsbomb", half=True,
                          pitch_color="#1a2438", line_color="#4b5563", linewidth=1.2)
    pitch.draw(ax=ax)
    ax.set_title("Delivery landing zones", fontsize=13, fontweight="bold",
                 color="#f1f5f9", pad=8)

    if df.empty or not {"delivery_end_x", "delivery_end_y"}.issubset(df.columns):
        ax.text(40, 85, "No landing location data", ha="center", va="center",
                color="#94a3b8", fontsize=11)
        return fig

    plot_df = df.dropna(subset=["delivery_end_x", "delivery_end_y"]).copy()
    plot_df = plot_df[pd.to_numeric(plot_df["delivery_end_x"], errors="coerce") >= 60].copy()
    if plot_df.empty:
        ax.text(40, 85, "No in-box landing data", ha="center", va="center",
                color="#94a3b8", fontsize=11)
        return fig

    xs = pd.to_numeric(plot_df["delivery_end_x"], errors="coerce")
    ys = pd.to_numeric(plot_df["delivery_end_y"], errors="coerce")

    pitch.kdeplot(xs, ys, ax=ax, cmap="YlOrRd", fill=True, levels=100,
                  thresh=0.05, alpha=0.85)
    pitch.scatter(xs, ys, ax=ax, s=8, color="white", alpha=0.25, zorder=4)
    fig.tight_layout(pad=0.5)
    return fig


def mplsoccer_delivery_figure(df: pd.DataFrame, label: str = ""):
    import matplotlib.pyplot as plt
    from mplsoccer import VerticalPitch

    base = add_delivery_zones(unique_start_events(df))
    pitch = pitch_dimensions(df)
    fig, ax = plt.subplots(figsize=(5.8, 8), dpi=140)
    fig.patch.set_facecolor("#161922")
    pitch_plot = VerticalPitch(pitch_type="statsbomb", half=True, pitch_color="#1a2438", line_color="#4b5563", linewidth=1.2)
    pitch_plot.draw(ax=ax)
    ax.set_title(f"{label} delivery map", fontsize=14, fontweight="bold", color="#f1f5f9", pad=10)

    if base.empty or not {"delivery_end_x", "delivery_end_y"}.issubset(base.columns):
        ax.text(*mplsoccer_center_xy(pitch), "No delivery end locations", ha="center", va="center", color=MUTED, fontsize=12)
        return fig

    plot_df = base.dropna(subset=["delivery_end_x", "delivery_end_y"]).copy()
    if plot_df.empty:
        ax.text(*mplsoccer_center_xy(pitch), "No delivery end locations", ha="center", va="center", color=MUTED, fontsize=12)
        return fig

    if len(plot_df) > 320:
        st.info(f"Delivery map: showing a random sample of 320 of {len(plot_df):,} deliveries.")
        plot_df = plot_df.sample(320, random_state=11)

    colors = {
        "Six-yard corridor": RED,
        "Near/far post lane": "#2563eb",
        "Penalty spot": "#16a34a",
        "Edge of box": "#f59e0b",
        "Short / recycle": "#7c3aed",
        "Second ball zone": "#64748b",
        "Unknown": "#94a3b8",
    }

    for zone, part in plot_df.groupby("Delivery zone", dropna=False):
        color = colors.get(str(zone), "#64748b")
        plot_x, plot_y = mplsoccer_pitch_xy(part, "delivery_end_x", "delivery_end_y", pitch)
        pitch_plot.scatter(
            plot_x,
            plot_y,
            s=np.clip(part["xg"].fillna(0).to_numpy() * 550 + 28 if "xg" in part.columns else 36, 28, 120),
            color=color,
            edgecolors="white",
            linewidth=0.7,
            alpha=0.82,
            label=str(zone),
            ax=ax,
        )

    ax.legend(loc="lower left", bbox_to_anchor=(0.01, 0.01), fontsize=7, frameon=True)
    fig.tight_layout()
    return fig


def mplsoccer_delivery_sp_outcome_figure(df: pd.DataFrame, label: str = ""):
    import matplotlib.pyplot as plt
    from mplsoccer import VerticalPitch

    base = unique_start_events(df).copy()
    pitch = pitch_dimensions(df)
    fig, ax = plt.subplots(figsize=(5.8, 8), dpi=140)
    fig.patch.set_facecolor("#161922")
    pitch_plot = VerticalPitch(pitch_type="statsbomb", half=True, pitch_color="#1a2438", line_color="#4b5563", linewidth=1.2)
    pitch_plot.draw(ax=ax)
    ax.set_title(f"{label} delivery map SP outcomes", fontsize=14, fontweight="bold", color="#f1f5f9", pad=10)

    if base.empty or not {"delivery_end_x", "delivery_end_y"}.issubset(base.columns):
        ax.text(*mplsoccer_center_xy(pitch), "No delivery end locations", ha="center", va="center", color=MUTED, fontsize=12)
        return fig

    plot_df = base.dropna(subset=["delivery_end_x", "delivery_end_y"]).copy()
    if plot_df.empty:
        ax.text(*mplsoccer_center_xy(pitch), "No delivery end locations", ha="center", va="center", color=MUTED, fontsize=12)
        return fig

    if len(plot_df) > 320:
        st.info(f"Delivery SP-outcome map: showing a random sample of 320 of {len(plot_df):,} deliveries.")
        plot_df = plot_df.sample(320, random_state=13)

    outcome_col = next((col for col in ["SP_outcome", "SP outcome", "Delivery outcome", "Shot outcome", "Outcome"] if col in plot_df.columns), None)
    if outcome_col is None:
        plot_df["SP outcome"] = "Unknown"
        outcome_col = "SP outcome"

    plot_df[outcome_col] = (
        plot_df[outcome_col]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace({"": "Unknown", "nan": "Unknown", "None": "Unknown", "undefined": "Unknown"})
    )

    colors = {
        "Goal": "#16a34a",
        "Shot after 3 seconds": "#2563eb",
        "Shot after 5 seconds": "#1d4ed8",
        "Shot after 10 seconds": "#7c3aed",
        "Shot": "#2563eb",
        "No shot": "#64748b",
        "Ball astray": "#b45309",
        "First contact won": "#0f766e",
        "First contact lost": "#dc2626",
        "Cleared": "#475569",
        "Retained": "#16a34a",
        "Unknown": "#94a3b8",
    }
    fallback_colors = [RED, "#0891b2", "#9333ea", "#ea580c", "#334155", "#be123c", "#4f46e5"]

    for idx, (outcome, part) in enumerate(plot_df.groupby(outcome_col, dropna=False)):
        outcome_label = str(outcome) if str(outcome).strip() else "Unknown"
        color = colors.get(outcome_label, fallback_colors[idx % len(fallback_colors)])
        plot_x, plot_y = mplsoccer_pitch_xy(part, "delivery_end_x", "delivery_end_y", pitch)
        pitch_plot.scatter(
            plot_x,
            plot_y,
            s=44,
            color=color,
            edgecolors="white",
            linewidth=0.7,
            alpha=0.82,
            label=outcome_label,
            ax=ax,
        )

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2, fontsize=7, frameon=True)
    fig.tight_layout()
    return fig


def mplsoccer_shot_figure(df: pd.DataFrame, label: str = ""):
    import matplotlib.pyplot as plt
    from mplsoccer import VerticalPitch

    shots = unique_shot_events(df)
    pitch = pitch_dimensions(df)
    half_start = float(pitch["half_start"])
    fig, ax = plt.subplots(figsize=(5.8, 8), dpi=140)
    fig.patch.set_facecolor("#161922")
    pitch_plot = VerticalPitch(pitch_type="statsbomb", half=True, pitch_color="#1a2438", line_color="#4b5563", linewidth=1.2)
    pitch_plot.draw(ax=ax)
    ax.set_title(f"{label} shot quality", fontsize=14, fontweight="bold", color="#f1f5f9", pad=10)

    if shots.empty or not {"shot_x", "shot_y"}.issubset(shots.columns):
        ax.text(*mplsoccer_center_xy(pitch), "No shots in current filter", ha="center", va="center", color=MUTED, fontsize=12)
        return fig

    shots = shots.dropna(subset=["shot_x", "shot_y"]).copy()
    shots["plot_x"], shots["plot_y"] = coords_to_statsbomb(shots, "shot_x", "shot_y")
    shots = shots[shots["plot_x"] >= half_start]
    if shots.empty:
        ax.text(*mplsoccer_center_xy(pitch), "No shots in current filter", ha="center", va="center", color=MUTED, fontsize=12)
        return fig

    goals = shots["is_goal"] if "is_goal" in shots.columns else pd.Series(False, index=shots.index)
    sizes = np.clip(shots["xg"].fillna(0).to_numpy() * 700 + 34 if "xg" in shots.columns else 42, 34, 145)
    plot_x, plot_y = mplsoccer_pitch_xy(shots, "shot_x", "shot_y", pitch)
    pitch_plot.scatter(plot_x.loc[~goals], plot_y.loc[~goals], s=sizes[~goals], color="#2563eb", edgecolors="white", linewidth=0.8, alpha=0.78, label="Shot", ax=ax)
    if goals.any():
        pitch_plot.scatter(plot_x.loc[goals], plot_y.loc[goals], s=sizes[goals], color="#16a34a", edgecolors=BLACK, linewidth=0.8, alpha=0.92, label="Goal", ax=ax)
    ax.legend(loc="lower left", bbox_to_anchor=(0.01, 0.01), fontsize=8, frameon=True)
    fig.tight_layout()
    return fig


def prematch_report_pdf_bytes(df: pd.DataFrame, label: str = "", opponent: str = "") -> bytes:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    buffer = BytesIO()
    insights = generate_set_piece_insights(df, label)
    roles = build_role_archetypes(df, label).head(8)
    teams = build_team_archetypes(df).head(8)

    _PDF_BG   = "#0b0f14"
    _PDF_INK  = "#f1f5f9"
    _PDF_MUTED = "#9ca3af"
    _PDF_HEAD = "#22c55e"

    with PdfPages(buffer) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        fig.patch.set_facecolor(_PDF_BG)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_facecolor(_PDF_BG)
        ax.axis("off")
        title = f"{label} pre-match report"
        if opponent:
            title = f"{title}: {opponent}"
        ax.text(0.07, 0.94, title, fontsize=22, fontweight="bold", color=_PDF_INK)
        ax.text(0.07, 0.905, "Roles, archetypes, delivery tendencies, and preparation notes", fontsize=10, color=_PDF_MUTED)

        y = 0.84
        ax.text(0.07, y, "Key insights", fontsize=13, fontweight="bold", color=_PDF_HEAD)
        y -= 0.035
        for insight in insights:
            wrapped = textwrap.wrap(insight, width=92)
            for i, line in enumerate(wrapped):
                prefix = "- " if i == 0 else "  "
                ax.text(0.08, y, prefix + line, fontsize=9.4, color=_PDF_INK)
                y -= 0.022
            y -= 0.006

        if not roles.empty:
            y -= 0.02
            ax.text(0.07, y, "Taker roles", fontsize=13, fontweight="bold", color=_PDF_HEAD)
            y -= 0.035
            for _, row in roles.iterrows():
                line = f"{row['Taker']} ({row['Team']}): {row['Role']} · {row['Archetype']} · {row['Events']} events · {row['xG / event']:.3f} xG/event"
                ax.text(0.08, y, line[:118], fontsize=8.8, color=_PDF_INK)
                y -= 0.024

        if not teams.empty and y > 0.18:
            y -= 0.02
            ax.text(0.07, y, "Team archetypes", fontsize=13, fontweight="bold", color=_PDF_HEAD)
            y -= 0.035
            for _, row in teams.iterrows():
                line = f"{row['Team']}: {row['Archetype']} · {row['Primary delivery']} · {row['Shot rate']:.1f}% shot rate"
                ax.text(0.08, y, line[:118], fontsize=8.8, color=_PDF_INK)
                y -= 0.024
                if y < 0.08:
                    break
        add_logo_to_matplotlib_figure(fig)
        pdf.savefig(fig, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)

        fig = mplsoccer_delivery_figure(df, label)
        add_logo_to_matplotlib_figure(fig)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig = mplsoccer_shot_figure(df, label)
        add_logo_to_matplotlib_figure(fig)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig = mplsoccer_delivery_sp_outcome_figure(df, label)
        add_logo_to_matplotlib_figure(fig)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    buffer.seek(0)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Full scouting report PDF — all sections, both teams
# ---------------------------------------------------------------------------

def _pdf_cover_page(pdf, plt, my_team: str, opponent: str,
                    my_kpi: dict, opp_kpi: dict,
                    alerts: list[str], avg_xg_100: float) -> None:
    import matplotlib.gridspec as gridspec

    def _score(kpi):
        base = kpi["xg_per_100"]
        if avg_xg_100 <= 0:
            return 50.0
        return min(200.0, round(base / avg_xg_100 * 100, 1))

    def _threat_label(s):
        if s >= 140: return "HIGH THREAT", "#ef4444"
        if s >= 100: return "ABOVE AVERAGE", "#f59e0b"
        if s >= 60:  return "AVERAGE", "#9ca3af"
        return "LOW THREAT", "#22c55e"

    fig = plt.figure(figsize=(8.27, 11.69), dpi=140)
    fig.patch.set_facecolor("#0b0f14")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")

    # Header bar
    ax.axhspan(0.88, 1.0, color="#161922")
    ax.text(0.06, 0.945, "PRE-MATCH SCOUTING REPORT", fontsize=9, fontweight="bold",
            color="#22c55e", transform=ax.transAxes, va="center",
            fontfamily="monospace")
    add_logo_to_matplotlib_figure(fig)

    # Match title
    ax.text(0.06, 0.83, f"{my_team}", fontsize=22, fontweight="900", color="#ffffff")
    ax.text(0.06, 0.80, f"vs  {opponent}", fontsize=16, fontweight="700", color="#9ca3af")

    import datetime
    ax.text(0.06, 0.76, f"Generated {datetime.date.today().strftime('%d %B %Y')}",
            fontsize=9, color="#4b5563")

    ax.axhline(0.745, xmin=0.06, xmax=0.94, color="#2a2d35", linewidth=0.7)

    # Threat cards
    my_s  = _score(my_kpi)
    opp_s = _score(opp_kpi)
    my_lbl,  my_col  = _threat_label(my_s)
    opp_lbl, opp_col = _threat_label(opp_s)

    for x0, team, s, lbl, col, kpi in [
        (0.06, my_team,  my_s,  my_lbl,  my_col,  my_kpi),
        (0.53, opponent, opp_s, opp_lbl, opp_col, opp_kpi),
    ]:
        rect = plt.Rectangle((x0, 0.63), 0.40, 0.10, transform=ax.transAxes,
                              facecolor="#161922", edgecolor=col, linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x0 + 0.02, 0.725, team, fontsize=8, fontweight="700",
                color="#9ca3af", transform=ax.transAxes)
        ax.text(x0 + 0.02, 0.690, f"{s:.0f}", fontsize=24, fontweight="900",
                color=col, transform=ax.transAxes, va="center")
        ax.text(x0 + 0.14, 0.690, lbl, fontsize=7, fontweight="700",
                color=col, transform=ax.transAxes, va="center")
        ax.text(x0 + 0.02, 0.645, f"{kpi['restarts']:,} SP  ·  {kpi['shots']} shots  ·  {kpi['total_xg']:.2f} xG  ·  {kpi['xg_per_100']:.2f} xG/100",
                fontsize=7.5, color="#6b7280", transform=ax.transAxes)

    ax.text(0.06, 0.615, "Threat index: 100 = dataset average. Scale 0–200.",
            fontsize=7, color="#374151")

    ax.axhline(0.600, xmin=0.06, xmax=0.94, color="#2a2d35", linewidth=0.7)

    # KPI table
    ax.text(0.06, 0.575, "Head-to-head", fontsize=10, fontweight="700", color="#f1f5f9")
    rows = [
        ("Set pieces", f"{my_kpi['restarts']:,}", f"{opp_kpi['restarts']:,}"),
        ("Shots",       f"{my_kpi['shots']:,}",   f"{opp_kpi['shots']:,}"),
        ("Goals",       f"{my_kpi['goals']:,}",   f"{opp_kpi['goals']:,}"),
        ("xG total",    f"{my_kpi['total_xg']:.2f}", f"{opp_kpi['total_xg']:.2f}"),
        ("Shot rate %", f"{my_kpi['shot_rate']:.1f}", f"{opp_kpi['shot_rate']:.1f}"),
        ("xG / 100",    f"{my_kpi['xg_per_100']:.2f}", f"{opp_kpi['xg_per_100']:.2f}"),
    ]
    ax.text(0.35, 0.548, my_team[:20], fontsize=7.5, fontweight="700",
            color="#22c55e", transform=ax.transAxes)
    ax.text(0.65, 0.548, opponent[:20], fontsize=7.5, fontweight="700",
            color="#ef4444", transform=ax.transAxes)
    y = 0.520
    for label, mv, ov in rows:
        try:
            mf, of = float(mv.replace(",", "")), float(ov.replace(",", ""))
            mc = "#ffffff" if mf >= of else "#6b7280"
            oc = "#ffffff" if of >= mf else "#6b7280"
        except Exception:
            mc = oc = "#9ca3af"
        ax.text(0.06, y, label, fontsize=8.5, color="#9ca3af")
        ax.text(0.35, y, mv, fontsize=8.5, color=mc, fontweight="700" if mc == "#ffffff" else "normal")
        ax.text(0.65, y, ov, fontsize=8.5, color=oc, fontweight="700" if oc == "#ffffff" else "normal")
        y -= 0.028

    ax.axhline(y - 0.005, xmin=0.06, xmax=0.94, color="#2a2d35", linewidth=0.7)

    # Alerts
    ax.text(0.06, y - 0.020, f"Scouting alerts — {opponent}", fontsize=10, fontweight="700", color="#f1f5f9")
    ya = y - 0.048
    for alert in alerts[:5]:
        import re as _re
        clean = _re.sub(r"<[^>]+>", "", alert)
        import textwrap as _tw
        for i, line in enumerate(_tw.wrap(clean, 88)):
            prefix = "• " if i == 0 else "  "
            ax.text(0.06, ya, prefix + line, fontsize=8, color="#d1d5db")
            ya -= 0.022
        ya -= 0.004
        if ya < 0.06:
            break

    ax.axhline(0.04, xmin=0.06, xmax=0.94, color="#2a2d35", linewidth=0.5)
    ax.text(0.5, 0.022, "SetPlayPro · Michael Mackin Set Piece Analysis · Confidential",
            fontsize=7, color="#374151", ha="center")

    pdf.savefig(fig, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _pdf_df_page(pdf, plt, df: pd.DataFrame, title: str, subtitle: str = "") -> None:
    fig = plt.figure(figsize=(8.27, 11.69), dpi=140)
    fig.patch.set_facecolor("#0b0f14")
    ax = fig.add_axes([0.06, 0.06, 0.88, 0.88])
    ax.set_facecolor("#0b0f14")
    ax.axis("off")

    ax.text(0, 1.02, title, fontsize=13, fontweight="800", color="#f1f5f9",
            transform=ax.transAxes)
    if subtitle:
        ax.text(0, 0.995, subtitle, fontsize=8.5, color="#6b7280",
                transform=ax.transAxes)

    if df.empty:
        ax.text(0.5, 0.5, "No data available for this section.",
                ha="center", va="center", color="#4b5563", fontsize=10)
        pdf.savefig(fig, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        return

    # Truncate columns for readability
    display = df.head(20).copy()
    for col in display.select_dtypes(include="number").columns:
        display[col] = display[col].apply(
            lambda v: f"{v:.3f}" if isinstance(v, float) and abs(v) < 1000 else (f"{int(v):,}" if pd.notna(v) else "")
        )
    display = display.fillna("").astype(str)
    # Trim long text cells
    for col in display.columns:
        display[col] = display[col].str[:22]

    cols_list = display.columns.tolist()
    col_widths = [max(len(str(c)), display[c].str.len().max()) for c in cols_list]
    total = sum(col_widths) or 1
    widths = [w / total for w in col_widths]

    tbl = ax.table(
        cellText=display.values,
        colLabels=cols_list,
        colWidths=widths,
        loc="upper center",
        cellLoc="left",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.5)
    tbl.scale(1, 1.55)

    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor("#2a2d35")
        if row == 0:
            cell.set_facecolor("#1e2230")
            cell.set_text_props(color="#9ca3af", fontweight="bold")
        else:
            cell.set_facecolor("#161922" if row % 2 == 0 else "#1a1d23")
            cell.set_text_props(color="#f1f5f9")

    add_logo_to_matplotlib_figure(fig)
    ax.text(0.5, -0.02, "SetPlayPro · Confidential", fontsize=6.5, color="#374151",
            ha="center", transform=ax.transAxes)
    pdf.savefig(fig, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _pdf_section_divider(pdf, plt, title: str, subtitle: str = "", color: str = "#22c55e") -> None:
    fig = plt.figure(figsize=(8.27, 11.69), dpi=140)
    fig.patch.set_facecolor("#0b0f14")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    rect = plt.Rectangle((0, 0.44), 1, 0.14, facecolor=color, alpha=0.08)
    ax.add_patch(rect)
    ax.axvline(0.06, ymin=0.44, ymax=0.58, color=color, linewidth=3)
    ax.text(0.10, 0.535, title, fontsize=28, fontweight="900", color="#ffffff", va="center")
    if subtitle:
        ax.text(0.10, 0.467, subtitle, fontsize=11, color="#6b7280", va="center")
    add_logo_to_matplotlib_figure(fig)
    ax.text(0.5, 0.025, "SetPlayPro · Confidential", fontsize=7, color="#374151", ha="center")
    pdf.savefig(fig, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _pdf_two_figures(pdf, plt, fig_l, fig_r, title: str) -> None:
    """Combine two matplotlib figures side-by-side on one A4 page."""
    import matplotlib.gridspec as gridspec
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    fig = plt.figure(figsize=(8.27, 11.69), dpi=140)
    fig.patch.set_facecolor("#0b0f14")

    ax_title = fig.add_axes([0.04, 0.93, 0.92, 0.05])
    ax_title.axis("off")
    ax_title.text(0, 0.5, title, fontsize=12, fontweight="800",
                  color="#f1f5f9", va="center")

    for src_fig, rect in [(fig_l, [0.02, 0.46, 0.46, 0.46]),
                           (fig_r, [0.52, 0.46, 0.46, 0.46])]:
        if src_fig is None:
            continue
        src_fig.canvas = FigureCanvasAgg(src_fig)
        src_fig.canvas.draw()
        buf = BytesIO()
        src_fig.savefig(buf, format="png", dpi=110,
                        facecolor=src_fig.get_facecolor(), bbox_inches="tight")
        buf.seek(0)
        import matplotlib.image as mpimg
        img = mpimg.imread(buf)
        ax_img = fig.add_axes(rect)
        ax_img.imshow(img)
        ax_img.axis("off")
        plt.close(src_fig)

    add_logo_to_matplotlib_figure(fig)
    ax_foot = fig.add_axes([0.04, 0.01, 0.92, 0.02])
    ax_foot.axis("off")
    ax_foot.text(0.5, 0.5, "SetPlayPro · Confidential", fontsize=6.5,
                 color="#374151", ha="center", va="center")

    pdf.savefig(fig, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def full_scouting_report_pdf_bytes(
    my_team: str,
    opponent: str,
    my_corners: pd.DataFrame,
    my_fks: pd.DataFrame,
    my_tis: pd.DataFrame,
    opp_corners: pd.DataFrame,
    opp_fks: pd.DataFrame,
    opp_tis: pd.DataFrame,
    hops: pd.DataFrame,
) -> bytes:
    """Generate a comprehensive pre-match scouting PDF covering all set-piece phases."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import re as _re

    buffer = BytesIO()

    # ── KPI totals ────────────────────────────────────────────────────
    all_sp  = pd.concat([my_corners, my_fks, my_tis,
                         opp_corners, opp_fks, opp_tis], ignore_index=True)
    all_kpi  = set_piece_kpi_values(all_sp)
    avg_xg_100 = float(all_kpi["xg_per_100"]) or 1.0

    my_sp   = pd.concat([my_corners,  my_fks,  my_tis],  ignore_index=True)
    opp_sp  = pd.concat([opp_corners, opp_fks, opp_tis], ignore_index=True)
    my_kpi  = set_piece_kpi_values(my_sp)
    opp_kpi = set_piece_kpi_values(opp_sp)

    opp_hops = (
        hops[hops["Team"].astype(str).eq(opponent)].sort_values("Rating", ascending=False)
        if not hops.empty and "Team" in hops.columns
        else pd.DataFrame()
    )

    # ── Build scouting alerts ─────────────────────────────────────────
    alerts: list[str] = []
    if not opp_hops.empty:
        for _, row in opp_hops.head(3).iterrows():
            if row.get("Tier") == "Elite":
                alerts.append(
                    f"⚠ {row['Player']} — elite aerial threat (HOPS {row['Rating']:.3f}). Mark at every corner."
                )
    if not opp_corners.empty and "Delivery height" in opp_corners.columns:
        top = opp_corners["Delivery height"].value_counts()
        if not top.empty and top.iloc[0] / len(opp_corners) >= 0.55:
            alerts.append(f"• {top.iloc[0] / len(opp_corners) * 100:.0f}% of corners delivered as {top.index[0].lower()} balls.")
    if not opp_corners.empty and "side" in opp_corners.columns:
        sc = opp_corners["side"].value_counts()
        if not sc.empty and sc.iloc[0] / len(opp_corners) >= 0.60:
            alerts.append(f"• Corner side bias: {sc.iloc[0] / len(opp_corners) * 100:.0f}% from {sc.index[0]} side.")
    if opp_kpi["shot_rate"] >= 18:
        alerts.append(f"• High shot rate: {opp_kpi['shot_rate']:.1f}% of set pieces generate a shot.")
    if opp_kpi["top_taker"] not in {"Unknown", ""}:
        alerts.append(f"• Primary corner taker: {opp_kpi['top_taker']}.")

    with PdfPages(buffer) as pdf:
        # Page 1: Cover
        _pdf_cover_page(pdf, plt, my_team, opponent, my_kpi, opp_kpi, alerts, avg_xg_100)

        # ── OPPONENT SECTION ─────────────────────────────────────────
        _pdf_section_divider(pdf, plt, f"{opponent}", "Their set-piece attack — what you need to defend", "#ef4444")

        # Corners — always render; individual functions show "no data" if empty
        fig_del = mplsoccer_delivery_figure(opp_corners, "Corners")
        fig_shot = mplsoccer_shot_figure(opp_corners, "Corners")
        _pdf_two_figures(pdf, plt, fig_del, fig_shot, f"{opponent} — Corner deliveries & shots")
        fig_out = mplsoccer_delivery_sp_outcome_figure(opp_corners, "Corners")
        _pdf_two_figures(pdf, plt, fig_out, None, f"{opponent} — Corner delivery outcomes")
        _pdf_df_page(pdf, plt, build_taker_leaderboard(opp_corners).head(12),
                     f"{opponent} — Corner takers", "Events, shot rate, xG/event, delivery tendency")
        _pdf_df_page(pdf, plt, build_pattern_library(opp_corners).head(12),
                     f"{opponent} — Corner patterns", "Recurring delivery + zone combinations")

        # Free kicks
        fig_fk = freekick_origin_map_figure(opp_fks, f"{opponent} Freekick origins")
        fig_fk_shot = mplsoccer_shot_figure(opp_fks, "Freekicks")
        _pdf_two_figures(pdf, plt, fig_fk, fig_fk_shot, f"{opponent} — Freekick origins & shots")
        _pdf_df_page(pdf, plt, freekick_zone_summary(opp_fks).head(10),
                     f"{opponent} — Freekick zone breakdown")
        _pdf_df_page(pdf, plt, freekick_taker_summary(opp_fks).head(12),
                     f"{opponent} — Freekick takers")
        _pdf_df_page(pdf, plt, freekick_sequence_summary(opp_fks).head(10),
                     f"{opponent} — Freekick sequences")

        # Throw-ins
        fig_ti = throwin_delivery_map_figure(opp_tis, f"{opponent} Throw-in deliveries")
        _pdf_two_figures(pdf, plt, fig_ti, None, f"{opponent} — Throw-in delivery map")
        _pdf_df_page(pdf, plt, throwin_zone_summary(opp_tis).head(10),
                     f"{opponent} — Throw-in zones")
        _pdf_df_page(pdf, plt, throwin_taker_summary(opp_tis).head(12),
                     f"{opponent} — Throw-in takers (throwers)")

        # HOPS aerial threats
        _pdf_df_page(
            pdf, plt,
            opp_hops[["Player", "Rating", "Percentile", "Tier"]].head(20) if not opp_hops.empty else pd.DataFrame(),
            f"{opponent} — HOPS aerial threat watchlist",
            "Players to mark at corners and free kicks",
        )

        # ── OUR SECTION ──────────────────────────────────────────────
        _pdf_section_divider(pdf, plt, f"{my_team}", "Our attacking set pieces — reference", "#22c55e")

        fig_del = mplsoccer_delivery_figure(my_corners, "Corners")
        fig_shot = mplsoccer_shot_figure(my_corners, "Corners")
        _pdf_two_figures(pdf, plt, fig_del, fig_shot, f"{my_team} — Corner deliveries & shots")
        _pdf_df_page(pdf, plt, build_taker_leaderboard(my_corners).head(12),
                     f"{my_team} — Corner takers")

        fig_fk = freekick_origin_map_figure(my_fks, f"{my_team} Freekick origins")
        fig_fk_shot = mplsoccer_shot_figure(my_fks, "Freekicks")
        _pdf_two_figures(pdf, plt, fig_fk, fig_fk_shot, f"{my_team} — Freekick origins & shots")
        _pdf_df_page(pdf, plt, freekick_taker_summary(my_fks).head(12),
                     f"{my_team} — Freekick takers")

        fig_ti = throwin_delivery_map_figure(my_tis, f"{my_team} Throw-in deliveries")
        _pdf_two_figures(pdf, plt, fig_ti, None, f"{my_team} — Throw-in delivery map")

        # HOPS — our squad
        my_hops = (
            hops[hops["Team"].astype(str).eq(my_team)].sort_values("Rating", ascending=False)
            if not hops.empty and "Team" in hops.columns
            else pd.DataFrame()
        )
        if not my_hops.empty:
            _pdf_df_page(
                pdf, plt,
                my_hops[["Player", "Rating", "Percentile", "Tier"]].head(20),
                f"{my_team} — HOPS squad ratings",
            )

    buffer.seek(0)
    return buffer.getvalue()
