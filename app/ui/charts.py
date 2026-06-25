"""Chart rendering and explanation UI."""

import re
import numpy as np
import pandas as pd
import streamlit as st

from agents.chart_selector import render_chart
from app.ui.layout import try_rerun


def _fmt_chart_value(value):
    try:
        val = float(value)
        if abs(val) >= 1_000_000:
            return f"{val/1_000_000:.2f}M"
        if abs(val) >= 1_000:
            return f"{val:,.0f}"
        return f"{val:.2f}"
    except Exception:
        return str(value)


def _md_bold_to_html(text):
    """Convert **bold** markdown to <strong> HTML tags."""
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', str(text))


def build_chart_explanation(df, spec, fallback_text=""):
    """Return a plain-language, data-aware explanation."""
    if df is None or spec is None:
        return fallback_text or "This chart highlights key patterns in your data."

    chart_type = spec.get("chart_type", "")
    x = spec.get("x")
    y = spec.get("y")
    agg = spec.get("agg", "none")

    try:
        if chart_type in ("bar", "pie") and x and y and x in df.columns and y in df.columns:
            data = df[[x, y]].dropna()
            if data.empty:
                return f"Compares {y.replace('_',' ')} across {x.replace('_',' ')}."
            grouped = data.groupby(x)[y].agg(agg if agg != "none" else "sum").sort_values(ascending=False)
            if grouped.empty:
                return f"Compares {y.replace('_',' ')} across {x.replace('_',' ')}."
            top_label = grouped.index[0]
            top_value = _fmt_chart_value(grouped.iloc[0])
            bottom_label = grouped.index[-1]
            bottom_value = _fmt_chart_value(grouped.iloc[-1])
            return (
                f"<strong>{top_label}</strong> leads with {y.replace('_',' ')} of {top_value}, "
                f"while <strong>{bottom_label}</strong> is lowest at {bottom_value}."
            )

        if chart_type == "grouped_bar" and x and isinstance(y, list) and len(y) >= 2 and x in df.columns:
            y_cols = [col for col in y if col in df.columns]
            if len(y_cols) >= 2:
                data = df[[x] + y_cols].dropna()
                if not data.empty:
                    grouped = data.groupby(x)[y_cols].agg(agg if agg != "none" else "sum")
                    top_label = grouped[y_cols[0]].sort_values(ascending=False).index[0]
                    return (
                        f"Compares <strong>{y_cols[0].replace('_',' ')}</strong> vs "
                        f"<strong>{y_cols[1].replace('_',' ')}</strong> per {x.replace('_',' ')}. "
                        f"<strong>{top_label}</strong> leads on {y_cols[0].replace('_',' ')}."
                    )

        if chart_type in ("line", "area") and x and y and x in df.columns and y in df.columns:
            tmp = df[[x, y]].dropna().copy()
            tmp[x] = pd.to_datetime(tmp[x], errors="coerce")
            tmp = tmp.dropna(subset=[x]).sort_values(x)
            if len(tmp) >= 2:
                start_val = float(tmp[y].iloc[0])
                end_val = float(tmp[y].iloc[-1])
                pct = ((end_val - start_val) / start_val * 100) if start_val != 0 else 0
                direction = "up ↑" if end_val >= start_val else "down ↓"
                return (
                    f"<strong>{y.replace('_',' ')}</strong> trended {direction} — "
                    f"from {_fmt_chart_value(start_val)} to <strong>{_fmt_chart_value(end_val)}</strong> "
                    f"({pct:+.1f}%)."
                )

        if chart_type in ("histogram", "box"):
            col = x if x in df.columns else y if isinstance(y, str) and y in df.columns else None
            if col:
                series = pd.to_numeric(df[col], errors="coerce").dropna()
                if not series.empty:
                    median = _fmt_chart_value(series.median())
                    p25 = _fmt_chart_value(series.quantile(0.25))
                    p75 = _fmt_chart_value(series.quantile(0.75))
                    return (
                        f"<strong>{col.replace('_',' ')}</strong> median is <strong>{median}</strong> "
                        f"(IQR: {p25} – {p75})."
                    )

        if chart_type == "scatter" and x and y and x in df.columns and y in df.columns:
            data = df[[x, y]].dropna()
            if len(data) >= 3:
                corr = data[x].corr(data[y])
                if pd.notna(corr):
                    strength = "strong" if abs(corr) >= 0.6 else "moderate" if abs(corr) >= 0.3 else "weak"
                    direction = "positive" if corr >= 0 else "negative"
                    return (
                        f"<strong>{x.replace('_',' ')}</strong> and <strong>{y.replace('_',' ')}</strong> "
                        f"show a <strong>{strength} {direction}</strong> relationship (r = {corr:.2f})."
                    )

        if chart_type == "heatmap":
            num_df = df.select_dtypes(include=[np.number])
            if num_df.shape[1] >= 2:
                corr = num_df.corr().abs()
                np.fill_diagonal(corr.values, 0)
                top_pair = corr.stack().idxmax()
                top_val = corr.stack().max()
                if pd.notna(top_val):
                    return (
                        f"Strongest link: <strong>{top_pair[0].replace('_',' ')}</strong> ↔ "
                        f"<strong>{top_pair[1].replace('_',' ')}</strong> (r = {top_val:.2f})."
                    )
    except Exception:
        pass

    return fallback_text or "This chart highlights a key pattern in the dataset."


def _build_data_aware_actions(df, spec):
    chart_type = (spec or {}).get("chart_type", "")
    x = (spec or {}).get("x", "")
    y = (spec or {}).get("y", "")
    if isinstance(y, list):
        y = y[0] if y else ""
    x_label = str(x).replace("_", " ") if x else "category"
    y_label = str(y).replace("_", " ") if y else "metric"

    action_map = {
        "bar": [
            f"Investigate why the top {x_label} outperforms — volume, pricing, or mix?",
            f"Set a minimum target for the lowest-performing {x_label} based on the median.",
            "Filter by a second dimension to check if this ranking holds across segments.",
        ],
        "grouped_bar": [
            f"Find {x_label}s where one metric is high but the other is weak.",
            f"Set a combined target so both {y_label} metrics improve together.",
            f"Investigate the {x_label} with the largest gap between the two metrics first.",
        ],
        "line": [
            f"Check periods where {y_label} changed direction and find the cause.",
            f"Set an alert threshold for sudden drops in {y_label}.",
            "Compare this trend against a benchmark or prior year if available.",
        ],
        "area": [
            f"Check if {y_label} growth is consistent or concentrated in a few periods.",
            "Break down the latest period to find which segment drove the change.",
            "Set a near-term target based on the recent trend speed.",
        ],
        "scatter": [
            "Review outlier points far from the trend — they may indicate data issues.",
            f"Test whether the {x_label}–{y_label} relationship holds across segments.",
            "Avoid assuming causation — validate the link with domain knowledge.",
        ],
        "histogram": [
            f"Use the {y_label} distribution to define realistic performance benchmarks.",
            "Investigate the extreme tails to reduce risk or inconsistency.",
            "Split by a category to check if the distribution differs across groups.",
        ],
        "box": [
            f"Focus on {x_label}s with the widest spread to improve consistency.",
            f"Investigate outliers in {y_label} before using averages for planning.",
            "Use the median, not the mean, for target-setting in skewed distributions.",
        ],
        "pie": [
            f"Focus on the largest {x_label} slices first to maximize impact.",
            "Investigate whether small slices are strategic or just noise.",
            "Track this composition over time to detect concentration risk.",
        ],
        "heatmap": [
            "Use the strongest correlations to identify candidate drivers for deeper analysis.",
            "Watch for highly correlated metrics — avoid tracking duplicates.",
            "Validate any surprising links with domain experts before acting.",
        ],
    }

    return action_map.get(chart_type, [
        f"Filter by {x_label} to check if this pattern holds across segments.",
        f"Track {y_label} weekly to see whether the trend is improving.",
        "Validate outliers with the source team before taking action.",
    ])


def render_possible_actions(spec, df=None):
    actions = _build_data_aware_actions(df, spec)
    if not actions:
        return
    items_html = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:5px;">'
        f'<span style="color:#6366F1;font-size:0.8rem;flex-shrink:0;margin-top:1px;">→</span>'
        f'<span style="color:#475569;font-size:0.81rem;line-height:1.5;">{item}</span>'
        f'</div>'
        for item in actions[:3]
    )
    st.markdown(
        f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;'
        f'padding:10px 14px;margin-top:10px;">'
        f'<div style="font-size:0.7rem;font-weight:700;color:#6366F1;text-transform:uppercase;'
        f'letter-spacing:.08em;margin-bottom:8px;">Suggested next steps</div>'
        f'{items_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _apply_tweak(spec, tweak_x, tweak_y):
    tweaked = dict(spec)
    if tweak_x != "— keep current —":
        tweaked["x"] = tweak_x
    if tweak_y != "— keep current —":
        if isinstance(tweaked.get("y"), list):
            y_vals = list(tweaked.get("y") or [])
            if y_vals:
                y_vals[0] = tweak_y
                tweaked["y"] = y_vals
            else:
                tweaked["y"] = tweak_y
        else:
            tweaked["y"] = tweak_y
    return tweaked


def render_ai_chart_card(chart, chart_index, df_source, all_columns):
    """Render an AI-selected chart with pin, explanation, actions, and tweak."""
    spec = chart.get("spec", {})
    agg = spec.get("agg", "none")
    human_label = chart.get("title", "Chart")
    if agg and agg != "none":
        human_label = f"{human_label} ({agg})"

    # ── Chart ─────────────────────────────────────────────────────────────────
    st.plotly_chart(
        chart["fig"],
        width="stretch",
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "modeBarButtonsToAdd": ["drawrect", "eraseshape"],
            "scrollZoom": True,
            "toImageButtonOptions": {"format": "png", "filename": human_label},
        },
        key=f"ai_chart_{chart_index}",
    )

    # ── Title + pin button ────────────────────────────────────────────────────
    pinned = bool(
        "pinned_charts" in st.session_state
        and any(p.get("spec") == spec for p in (st.session_state.get("pinned_charts") or []))
    )
    title_col, pin_col = st.columns([8, 1])
    with title_col:
        st.markdown(
            f'<div style="font-size:0.92rem;font-weight:700;color:#0F172A;margin:4px 0 2px;">'
            f'{human_label}</div>',
            unsafe_allow_html=True,
        )
    with pin_col:
        if st.button(
            "🔖" if pinned else "📌",
            key=f"pin_{chart_index}",
            help="Unpin from dashboard" if pinned else "Pin to dashboard",
            width="stretch",
        ):
            if pinned:
                st.session_state["pinned_charts"] = [
                    p for p in (st.session_state.get("pinned_charts") or [])
                    if p.get("spec") != spec
                ]
            else:
                if st.session_state.get("pinned_charts") is None:
                    st.session_state["pinned_charts"] = []
                st.session_state["pinned_charts"].append(chart)
            try_rerun()

    # ── Insight card ──────────────────────────────────────────────────────────
    explainer = build_chart_explanation(df_source, spec, fallback_text=chart.get("plain", ""))
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#EFF6FF,#F8FAFC);'
        f'border:1px solid #BFDBFE;border-radius:10px;padding:10px 14px;margin:6px 0 4px;">'
        f'<div style="font-size:0.7rem;font-weight:700;color:#3B82F6;text-transform:uppercase;'
        f'letter-spacing:.08em;margin-bottom:4px;">💡 Key insight</div>'
        f'<div style="font-size:0.85rem;color:#1E293B;line-height:1.55;">{explainer}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Suggested next steps ──────────────────────────────────────────────────
    render_possible_actions(spec, df=df_source)

    # ── Tweak expander ────────────────────────────────────────────────────────
    with st.expander("🔧 Tweak this chart", expanded=False):
        axis_options = ["— keep current —"] + list(all_columns)
        current_x = spec.get("x") if spec.get("x") in all_columns else None
        current_y = spec.get("y")
        if isinstance(current_y, list):
            current_y = next((v for v in current_y if v in all_columns), None)
        elif current_y not in all_columns:
            current_y = None

        tweak_x_key = f"tweak_x_{chart_index}"
        tweak_y_key = f"tweak_y_{chart_index}"
        if tweak_x_key not in st.session_state:
            st.session_state[tweak_x_key] = current_x or axis_options[0]
        if tweak_y_key not in st.session_state:
            st.session_state[tweak_y_key] = current_y or axis_options[0]

        col_x, col_y = st.columns(2)
        with col_x:
            tweak_x = st.selectbox(
                "X axis", axis_options,
                index=axis_options.index(st.session_state[tweak_x_key])
                if st.session_state[tweak_x_key] in axis_options else 0,
                key=tweak_x_key,
            )
        with col_y:
            tweak_y = st.selectbox(
                "Y axis", axis_options,
                index=axis_options.index(st.session_state[tweak_y_key])
                if st.session_state[tweak_y_key] in axis_options else 0,
                key=tweak_y_key,
            )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("👁 Preview", key=f"preview_btn_{chart_index}", width="stretch"):
                tweaked = render_chart(df_source, _apply_tweak(spec, tweak_x, tweak_y))
                if tweaked:
                    st.plotly_chart(
                        tweaked["fig"],
                        width="stretch",
                        config={"displaylogo": False},
                        key=f"tweak_preview_{chart_index}",
                    )
                else:
                    st.caption("Choose valid axes to preview.")
        with c2:
            if st.button("🔄 Apply changes", key=f"apply_btn_{chart_index}", width="stretch", type="primary"):
                result = render_chart(df_source, _apply_tweak(spec, tweak_x, tweak_y))
                if result:
                    # Replace this chart in the AI charts list in-place
                    charts = st.session_state.get("charts") or []
                    # Find by matching original spec
                    replaced = False
                    for i, c in enumerate(charts):
                        if c.get("spec") == spec:
                            charts[i] = result
                            replaced = True
                            break
                    if replaced:
                        st.session_state.charts = charts
                        st.success("✅ Chart updated")
                    else:
                        # Not in AI charts — add to custom charts
                        if st.session_state.get("custom_charts") is None:
                            st.session_state.custom_charts = []
                        st.session_state.custom_charts.append(result)
                        st.success("✅ Added to dashboard")
                    try_rerun()
                else:
                    st.error("Could not build that chart — check column selections.")
