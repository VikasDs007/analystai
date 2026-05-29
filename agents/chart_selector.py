"""Chart selector agent — LLM-driven chart selection with manual override."""

import json
import re
import warnings
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import is_identifier_col, get_groq_client, groq_json_decision

# ── Theme ─────────────────────────────────────────────────────────────────────
COLORS = ["#6366F1","#0EA5E9","#10B981","#F59E0B","#F43F5E",
          "#8B5CF6","#06B6D4","#84CC16","#FB923C","#EC4899"]

LAYOUT = dict(
    plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
    font=dict(color="#1E293B", family="Inter, sans-serif", size=13),
    xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", showgrid=True),
    yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", showgrid=True),
    margin=dict(t=60, b=50, l=50, r=20),
    title_font_size=15, title_font_color="#1E293B",
    hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#E2E8F0"),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
)

CHART_TYPES = ["bar", "line", "scatter", "histogram", "pie",
               "box", "heatmap", "grouped_bar", "area"]
AGG_OPTIONS = ["sum", "mean", "count", "max", "min", "none"]


# ── Column-type detection ─────────────────────────────────────────────────────

def _looks_like_date_col(col):
    name = col.lower()
    return "date" in name or "time" in name or name.endswith("_at")


def _parse_dates(series):
    for kwargs in [
        {"format": "mixed", "dayfirst": True},
        {"infer_datetime_format": True},
        {"dayfirst": True},
    ]:
        try:
            parsed = pd.to_datetime(series, errors="coerce", **kwargs)
            if parsed.notna().mean() > 0.7:
                return parsed
        except Exception:
            pass
    return None


def get_col_types(df):
    """Return (numeric_cols, categorical_cols, date_cols)."""
    numeric = [c for c in df.select_dtypes(include=[np.number]).columns
               if not is_identifier_col(c)]
    categorical = [c for c in df.select_dtypes(include=["object", "string"]).columns
                   if df[c].nunique() <= 20 and not is_identifier_col(c)]
    date_cols = []
    for col in df.columns:
        if col in numeric or not _looks_like_date_col(col):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parsed = _parse_dates(df[col].dropna().head(30))
        if parsed is not None:
            date_cols.append(col)
    return numeric, categorical, date_cols


# ── LLM chart planner ─────────────────────────────────────────────────────────

def _build_schema_prompt(df, understanding, numeric, categorical, date_cols):
    col_info = []
    for col in df.columns:
        s = df[col]
        dtype = str(s.dtype)
        nuniq = s.nunique()
        if col in date_cols or _looks_like_date_col(col):
            col_info.append(f"{col} [date]: range {s.dropna().min()} to {s.dropna().max()}")
        elif "int" in dtype or "float" in dtype:
            col_info.append(
                f"{col} [numeric]: min={s.min():.1f}, max={s.max():.1f}, "
                f"mean={s.mean():.1f}, unique={nuniq}"
            )
        else:
            top = s.value_counts().head(3).index.tolist()
            col_info.append(f"{col} [categorical]: {nuniq} unique, top={top}")

    corr_lines = []
    if len(numeric) >= 2:
        corr = df[numeric].corr().round(2)
        for i, c1 in enumerate(numeric):
            for c2 in numeric[i+1:]:
                corr_lines.append(f"  {c1} vs {c2}: {corr.loc[c1, c2]}")

    return f"""You are a data visualisation expert. Given this dataset, choose the BEST 6-7 charts.

DATASET: {understanding}
ROWS: {len(df)}

COLUMNS:
{chr(10).join(col_info)}

CORRELATIONS:
{chr(10).join(corr_lines) if corr_lines else "  N/A"}

RULES:
- Pick charts that give maximum business insight
- Use variety — do not repeat the same chart_type unless it shows a different dimension
- For date columns use chart_type "line" or "area"
- For 2 numeric columns with correlation > 0.4 or < -0.3, use "scatter"
- For distributions use "histogram" or "box"
- For category comparisons use "bar" or "grouped_bar"
- For composition use "pie"
- For correlation matrix use "heatmap"
- "grouped_bar" y must be a JSON array of 2 column names e.g. ["col1","col2"]
- "heatmap" x and y should be null (uses all numeric cols)
- agg must be one of: sum, mean, count, max, min, none
- Use agg "none" for scatter, histogram, box, heatmap

Return ONLY a valid JSON array, no markdown fences, no explanation. Each item:
{{
  "chart_type": "bar|line|scatter|histogram|pie|box|heatmap|grouped_bar|area",
  "x": "column_name_or_null",
  "y": "column_name_or_array_for_grouped_bar",
  "color": "column_name_or_null",
  "agg": "sum|mean|count|max|min|none",
  "title": "Short descriptive title",
  "reason": "One sentence why this chart is useful"
}}"""


def _llm_plan_charts(df, understanding, numeric, categorical, date_cols):
    """Ask the LLM to plan the best charts. Returns list of spec dicts."""
    prompt = _build_schema_prompt(df, understanding, numeric, categorical, date_cols)
    try:
        client = get_groq_client()
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500, temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        specs = json.loads(raw)
        # Validate each spec has required keys
        valid = []
        for s in specs:
            if all(k in s for k in ["chart_type", "x", "y", "agg", "title"]):
                valid.append(s)
        return valid
    except Exception as e:
        return []  # fall back to heuristic


def _validate_chart_specs_with_groq(df, understanding, specs):
        """Ask Groq to verify that proposed chart specs are safe and useful."""
        if not specs:
                return []

        validation = groq_json_decision(
                """
You are a strict chart-plan reviewer.
Return only valid JSON with these keys:
{
    "approved_specs": [
        {
            "chart_type": "bar|line|scatter|histogram|pie|box|heatmap|grouped_bar|area",
            "x": "column_name_or_null",
            "y": "column_name_or_array_or_null",
            "color": "column_name_or_null",
            "agg": "sum|mean|count|max|min|none",
            "title": "short title",
            "reason": "one sentence"
        }
    ],
    "confidence": 0.0,
    "reason": "why these charts are safe"
}

Keep only chart specs that are compatible with the dataset and useful for analysis.
""".strip(),
                f"Dataset understanding: {understanding}\n\nSpecs:\n{specs}",
                max_tokens=1200,
                temperature=0.1,
        )

        if isinstance(validation, dict) and isinstance(validation.get("approved_specs"), list):
                return validation["approved_specs"]
        return specs


def _heuristic_plan(df, numeric, categorical, date_cols):
    """Fallback heuristic chart plan when LLM is unavailable."""
    from utils.helpers import choose_main_numeric, choose_main_category
    main_num = choose_main_numeric(numeric)
    main_cat = choose_main_category(categorical)
    profit_col = next((c for c in numeric if "profit" in c.lower()), None)
    sec_cat = next((c for c in categorical
                    if c != main_cat and ("rep" in c.lower() or "product" in c.lower()
                                          or "name" in c.lower())), None)
    specs = []
    if main_cat and main_num:
        specs.append({"chart_type":"bar","x":main_cat,"y":main_num,"color":None,"agg":"sum",
                      "title":f"{main_num} by {main_cat}","reason":"Category breakdown"})
    if date_cols and main_num:
        specs.append({"chart_type":"line","x":date_cols[0],"y":main_num,"color":None,"agg":"sum",
                      "title":"Trend Over Time","reason":"Time series"})
    if main_cat and profit_col and profit_col != main_num:
        specs.append({"chart_type":"grouped_bar","x":main_cat,"y":[main_num,profit_col],
                      "color":None,"agg":"sum","title":"Revenue vs Profit","reason":"Comparison"})
    if main_num:
        specs.append({"chart_type":"histogram","x":main_num,"y":None,"color":None,"agg":"none",
                      "title":f"Distribution of {main_num}","reason":"Distribution"})
    if sec_cat and main_num:
        specs.append({"chart_type":"bar","x":sec_cat,"y":main_num,"color":None,"agg":"sum",
                      "title":f"Top {sec_cat}","reason":"Leaderboard"})
    if len(numeric) >= 2:
        y2 = next((c for c in numeric if c != main_num), None)
        if y2:
            specs.append({"chart_type":"scatter","x":main_num,"y":y2,"color":main_cat,"agg":"none",
                          "title":f"{main_num} vs {y2}","reason":"Correlation"})
    if len(numeric) >= 3:
        specs.append({"chart_type":"heatmap","x":None,"y":None,"color":None,"agg":"none",
                      "title":"Correlation Heatmap","reason":"All correlations"})
    return specs


# ── Chart renderer ────────────────────────────────────────────────────────────

def _apply_agg(df, x, y, agg):
    """Aggregate df by x column for y metric."""
    if agg == "none" or not x or not y:
        return df
    if isinstance(y, list):
        return df.groupby(x)[y].agg(agg).reset_index()
    return df.groupby(x)[y].agg(agg).reset_index().sort_values(y, ascending=False)


def render_chart(df, spec):
    """Render a single chart spec into a Plotly figure. Returns dict or None."""
    ct   = spec.get("chart_type", "bar")
    x    = spec.get("x")
    y    = spec.get("y")
    color = spec.get("color")
    agg  = spec.get("agg", "none")
    title = spec.get("title", "Chart")
    reason = spec.get("reason", "")

    # Validate columns exist
    all_cols = df.columns.tolist()
    if x and x not in all_cols:
        x = None
    if isinstance(y, list):
        y = [c for c in y if c in all_cols]
        if not y:
            y = None
    elif y and y not in all_cols:
        y = None
    if color and color not in all_cols:
        color = None

    try:
        fig = None

        if ct == "bar":
            if not x or not y:
                return None
            data = _apply_agg(df, x, y, agg).head(15)
            fig = px.bar(data, x=x, y=y, color=color or x,
                         color_discrete_sequence=COLORS, text=y, title=f"📊 {title}")
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
                              marker_line_width=0)
            fig.update_layout(showlegend=False, **LAYOUT)
            fig.update_xaxes(tickangle=-30)

        elif ct in ("line", "area"):
            if not x or not y:
                return None
            tmp = df.copy()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                parsed = _parse_dates(tmp[x])
            if parsed is None:
                return None
            tmp[x] = parsed
            tmp = tmp.dropna(subset=[x]).sort_values(x)
            if agg != "none":
                tmp = tmp.set_index(x)[y].resample("MS").agg(agg).reset_index()
            fig = px.line(tmp, x=x, y=y, color=color,
                          color_discrete_sequence=COLORS, markers=True, title=f"📈 {title}")
            if ct == "area":
                fig.update_traces(fill="tozeroy", fillcolor="rgba(99,102,241,0.08)")
            fig.update_traces(line_width=2.5, marker_size=7)
            fig.update_layout(**LAYOUT)

        elif ct == "scatter":
            if not x or not y:
                return None
            fig = px.scatter(df, x=x, y=y, color=color,
                             color_discrete_sequence=COLORS, opacity=0.75,
                             title=f"🔵 {title}")
            fig.update_layout(**LAYOUT)

        elif ct == "histogram":
            col = x or y
            if not col:
                return None
            fig = px.histogram(df, x=col, color=color,
                               color_discrete_sequence=COLORS,
                               nbins=25, marginal="box", title=f"📉 {title}")
            fig.update_layout(**LAYOUT)

        elif ct == "box":
            if not y:
                return None
            fig = px.box(df, x=x, y=y, color=x or color,
                         color_discrete_sequence=COLORS,
                         points="outliers", title=f"📦 {title}")
            fig.update_layout(**LAYOUT)

        elif ct == "pie":
            # y is the category column, agg count or sum
            cat_col = y or x
            if not cat_col:
                return None
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            num_col = next((c for c in numeric_cols if not is_identifier_col(c)), None)
            if agg == "count" or not num_col:
                counts = df[cat_col].value_counts().head(8)
                vals, names = counts.values, counts.index
            else:
                grp = df.groupby(cat_col)[num_col].agg(agg).sort_values(ascending=False).head(8)
                vals, names = grp.values, grp.index
            fig = px.pie(values=vals, names=names, hole=0.5,
                         color_discrete_sequence=COLORS, title=f"🍩 {title}")
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              pull=[0.05] + [0]*(len(vals)-1))
            fig.update_layout(**LAYOUT)

        elif ct == "grouped_bar":
            if not x or not isinstance(y, list) or len(y) < 2:
                return None
            data = _apply_agg(df, x, y, agg)
            fig = go.Figure()
            bar_colors = ["#6366F1", "#10B981", "#F59E0B", "#F43F5E"]
            for i, col in enumerate(y):
                fig.add_trace(go.Bar(
                    name=col.replace("_"," ").title(),
                    x=data[x], y=data[col],
                    marker_color=bar_colors[i % len(bar_colors)],
                    text=data[col],
                    texttemplate="%{text:,.0f}", textposition="outside",
                ))
            fig.update_layout(barmode="group", title=f"📊 {title}", **LAYOUT)

        elif ct == "heatmap":
            numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                            if not is_identifier_col(c)]
            if len(numeric_cols) < 2:
                return None
            corr = df[numeric_cols[:8]].corr().round(2)
            fig = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=[c.replace("_"," ") for c in corr.columns],
                y=[c.replace("_"," ") for c in corr.columns],
                colorscale="RdBu_r", zmid=0, zmin=-1, zmax=1,
                text=corr.values, texttemplate="%{text:.2f}",
            ))
            fig.update_layout(title=f"🔥 {title}", **LAYOUT)

        if fig is None:
            return None

        return {"fig": fig, "title": title, "plain": reason, "spec": spec}

    except Exception as e:
        return None


# ── Anomaly detection ─────────────────────────────────────────────────────────

def get_anomalies(df):
    numeric, _, _ = get_col_types(df)
    if len(numeric) < 2:
        return []
    corr = df[numeric].corr()
    alerts = []
    seen = set()
    for i, c1 in enumerate(numeric):
        for c2 in numeric[i+1:]:
            pair = tuple(sorted([c1, c2]))
            if pair in seen:
                continue
            seen.add(pair)
            val = corr.loc[c1, c2]
            if val <= -0.2:
                alerts.append((c1, c2, round(float(val), 2)))
    return sorted(alerts, key=lambda x: x[2])


# ── Main entry point ──────────────────────────────────────────────────────────

def build_charts(df, understanding=""):
    """LLM-driven chart selection with heuristic fallback."""
    numeric, categorical, date_cols = get_col_types(df)
    if not numeric and not categorical:
        return []

    # Ask LLM for chart plan
    specs = _llm_plan_charts(df, understanding, numeric, categorical, date_cols)

    # Fall back to heuristic if LLM failed or returned nothing
    if not specs:
        specs = _heuristic_plan(df, numeric, categorical, date_cols)

    specs = _validate_chart_specs_with_groq(df, understanding, specs)

    # Render each spec
    charts = []
    for spec in specs:
        result = render_chart(df, spec)
        if result:
            charts.append(result)

    return charts
