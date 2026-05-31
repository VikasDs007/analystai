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
from utils.helpers import is_identifier_col, get_llm_client, llm_json_decision

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
    """Build a rich, precise prompt that gives the LLM everything it needs."""
    col_info = []
    for col in df.columns:
        s = df[col]
        dtype = str(s.dtype)
        nuniq = s.nunique()
        if col in date_cols or _looks_like_date_col(col):
            col_info.append(
                f"{col} [DATE]: range {s.dropna().min()} → {s.dropna().max()}, "
                f"{nuniq} unique values"
            )
        elif "int" in dtype or "float" in dtype:
            if is_identifier_col(col):
                col_info.append(f"{col} [ID/SKIP]: identifier column, do not use as y-axis metric")
            else:
                skew = float(s.skew()) if len(s.dropna()) > 3 else 0
                col_info.append(
                    f"{col} [NUMERIC]: min={s.min():.1f}, max={s.max():.1f}, "
                    f"mean={s.mean():.1f}, median={s.median():.1f}, "
                    f"std={s.std():.1f}, skew={skew:.1f}, unique={nuniq}"
                )
        else:
            top = s.value_counts().head(5).index.tolist()
            col_info.append(
                f"{col} [CATEGORICAL]: {nuniq} unique values, "
                f"top values: {top}"
            )

    # Correlation matrix — only meaningful pairs
    corr_lines = []
    if len(numeric) >= 2:
        corr = df[numeric].corr().round(2)
        for i, c1 in enumerate(numeric):
            for c2 in numeric[i + 1:]:
                val = corr.loc[c1, c2]
                if abs(val) >= 0.25:  # only report meaningful correlations
                    strength = "STRONG" if abs(val) >= 0.6 else "MODERATE"
                    direction = "positive" if val > 0 else "negative"
                    corr_lines.append(f"  {c1} vs {c2}: r={val} ({strength} {direction})")

    # Category × metric summary — helps LLM pick the right x/y
    cat_metric_lines = []
    main_num = next(
        (c for c in numeric if any(k in c.lower() for k in
         ["sales", "revenue", "profit", "amount", "total", "price", "value"])),
        numeric[0] if numeric else None,
    )
    if main_num:
        for cat in categorical[:4]:
            try:
                top_cat = df.groupby(cat)[main_num].sum().sort_values(ascending=False)
                top3 = ", ".join(f"{k}={v:,.0f}" for k, v in top_cat.head(3).items())
                cat_metric_lines.append(f"  {cat} → {main_num}: {top3}")
            except Exception:
                pass

    return f"""You are a senior data visualisation expert building a business analytics dashboard.
Given the dataset below, choose exactly 6 charts that together give the most complete business picture.

DATASET CONTEXT: {understanding}
TOTAL ROWS: {len(df):,}

COLUMN DETAILS:
{chr(10).join(col_info)}

SIGNIFICANT CORRELATIONS (|r| >= 0.25):
{chr(10).join(corr_lines) if corr_lines else "  None detected"}

TOP CATEGORY BREAKDOWNS:
{chr(10).join(cat_metric_lines) if cat_metric_lines else "  N/A"}

CHART SELECTION RULES (follow strictly):
1. ALWAYS include a time-series chart (line or area) if a date column exists
2. ALWAYS include the main revenue/sales metric broken down by the most important category (bar)
3. ALWAYS include a distribution chart (histogram) for the main numeric metric
4. If profit AND revenue both exist, include a grouped_bar comparing them
5. If 2+ numeric columns have |r| >= 0.3, include a scatter plot
6. If 4+ numeric columns exist, include a heatmap
7. Include a pie chart only if a categorical column has 3–8 meaningful values
8. NEVER use ID columns as x or y
9. NEVER repeat the same chart_type + x + y combination
10. Use agg="sum" for revenue/sales/profit, agg="mean" for rates/percentages/prices
11. Use agg="none" for scatter, histogram, box, heatmap
12. For bar charts, always sort by y descending (the renderer handles this)
13. Add color dimension to scatter when a categorical column with ≤8 unique values exists
14. Prefer "area" over "line" when showing cumulative or volume trends

Return ONLY a valid JSON array (no markdown, no explanation). Exactly 6 items:
[
  {{
    "chart_type": "bar|line|area|scatter|histogram|pie|box|heatmap|grouped_bar",
    "x": "exact_column_name_or_null",
    "y": "exact_column_name_or_array_of_2_for_grouped_bar",
    "color": "exact_column_name_or_null",
    "agg": "sum|mean|count|max|min|none",
    "title": "Specific business-focused title using actual column names",
    "reason": "One sentence explaining the business insight this reveals"
  }}
]"""


def _llm_plan_charts(df, understanding, numeric, categorical, date_cols):
    """Ask the LLM to plan the best charts. Returns validated list of spec dicts."""
    prompt = _build_schema_prompt(df, understanding, numeric, categorical, date_cols)
    try:
        client = get_llm_client()
        resp = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a data visualisation expert. "
                        "Return ONLY a valid JSON array. No markdown fences, no explanation text. "
                        "Every column name you use must exactly match one of the column names provided."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.1,  # low temp for precision
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        specs = json.loads(raw)

        all_cols = set(df.columns.tolist())
        valid = []
        seen = set()  # deduplicate by (chart_type, x, y_key)

        for s in specs:
            if not all(k in s for k in ["chart_type", "x", "y", "agg", "title"]):
                continue

            ct = s.get("chart_type", "")
            x = s.get("x")
            y = s.get("y")
            color = s.get("color")

            # Validate column names exist
            if x and x not in all_cols:
                continue
            if isinstance(y, list):
                y = [c for c in y if c in all_cols]
                if len(y) < 2:
                    continue
                s["y"] = y
            elif y and y not in all_cols:
                continue
            if color and color not in all_cols:
                s["color"] = None

            # Skip ID columns as metrics
            if y and isinstance(y, str) and is_identifier_col(y):
                continue
            if x and is_identifier_col(x) and ct not in ("histogram", "box"):
                continue

            # Deduplicate
            y_key = tuple(y) if isinstance(y, list) else y
            dedup_key = (ct, x, y_key)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            valid.append(s)

        return valid
    except Exception:
        return []


def _validate_chart_specs_with_groq(df, understanding, specs):
        """Ask Groq to verify that proposed chart specs are safe and useful."""
        if not specs:
                return []

        validation = llm_json_decision(
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
    """Precise heuristic chart plan — mirrors the LLM rules when AI is unavailable."""
    from utils.helpers import choose_main_numeric, choose_main_category

    main_num = choose_main_numeric(numeric)
    main_cat = choose_main_category(categorical)
    profit_col = next((c for c in numeric if "profit" in c.lower()), None)
    revenue_col = next((c for c in numeric if any(k in c.lower()
                        for k in ["sales", "revenue", "amount", "total"])), main_num)
    rate_col = next((c for c in numeric if any(k in c.lower()
                     for k in ["rate", "pct", "percent", "discount", "margin"])), None)
    sec_cat = next((c for c in categorical
                    if c != main_cat and df[c].nunique() <= 12), None)

    specs = []
    seen = set()

    def _add(spec):
        key = (spec["chart_type"], spec.get("x"), str(spec.get("y")))
        if key not in seen:
            seen.add(key)
            specs.append(spec)

    # 1. Main category × main metric (bar)
    if main_cat and main_num:
        _add({"chart_type": "bar", "x": main_cat, "y": main_num, "color": None,
              "agg": "sum", "title": f"{main_num.replace('_',' ').title()} by {main_cat.replace('_',' ').title()}",
              "reason": "Shows which category drives the most value"})

    # 2. Time series (line or area)
    if date_cols and main_num:
        ct = "area" if revenue_col == main_num else "line"
        _add({"chart_type": ct, "x": date_cols[0], "y": main_num, "color": None,
              "agg": "sum", "title": f"{main_num.replace('_',' ').title()} Over Time",
              "reason": "Reveals growth trends and seasonal patterns"})

    # 3. Revenue vs Profit grouped bar
    if main_cat and profit_col and revenue_col and profit_col != revenue_col:
        _add({"chart_type": "grouped_bar", "x": main_cat,
              "y": [revenue_col, profit_col], "color": None, "agg": "sum",
              "title": f"Revenue vs Profit by {main_cat.replace('_',' ').title()}",
              "reason": "Compares revenue and profit margin across categories"})

    # 4. Distribution of main metric (histogram)
    if main_num:
        _add({"chart_type": "histogram", "x": main_num, "y": None, "color": main_cat,
              "agg": "none", "title": f"Distribution of {main_num.replace('_',' ').title()}",
              "reason": "Shows spread and outliers in the main metric"})

    # 5. Scatter — strongest correlated pair
    if len(numeric) >= 2:
        try:
            corr = df[numeric].corr().abs()
            np.fill_diagonal(corr.values, 0)
            pair = corr.stack().idxmax()
            c1, c2 = pair
            if c1 != c2 and not is_identifier_col(c1) and not is_identifier_col(c2):
                _add({"chart_type": "scatter", "x": c1, "y": c2,
                      "color": main_cat, "agg": "none",
                      "title": f"{c1.replace('_',' ').title()} vs {c2.replace('_',' ').title()}",
                      "reason": f"Explores the relationship between {c1.replace('_',' ')} and {c2.replace('_',' ')}"})
        except Exception:
            pass

    # 6. Secondary category breakdown
    if sec_cat and main_num and sec_cat != main_cat:
        _add({"chart_type": "bar", "x": sec_cat, "y": main_num, "color": None,
              "agg": "sum", "title": f"{main_num.replace('_',' ').title()} by {sec_cat.replace('_',' ').title()}",
              "reason": "Alternative category breakdown for comparison"})

    # 7. Heatmap if 4+ numeric columns
    if len(numeric) >= 4:
        _add({"chart_type": "heatmap", "x": None, "y": None, "color": None,
              "agg": "none", "title": "Correlation Heatmap",
              "reason": "Shows which metrics move together"})

    # 8. Pie for composition (if main_cat has 3–8 values)
    if main_cat and 3 <= df[main_cat].nunique() <= 8 and len(specs) < 6:
        _add({"chart_type": "pie", "x": main_cat, "y": main_cat, "color": None,
              "agg": "sum", "title": f"Share by {main_cat.replace('_',' ').title()}",
              "reason": "Shows composition and relative share of each category"})

    # 9. Box plot for rate/discount columns
    if rate_col and main_cat and len(specs) < 6:
        _add({"chart_type": "box", "x": main_cat, "y": rate_col, "color": None,
              "agg": "none", "title": f"{rate_col.replace('_',' ').title()} Distribution by {main_cat.replace('_',' ').title()}",
              "reason": "Shows spread and outliers in rates across categories"})

    return specs[:6]


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
    ct    = spec.get("chart_type", "bar")
    x     = spec.get("x")
    y     = spec.get("y")
    color = spec.get("color")
    agg   = spec.get("agg", "none")
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
            data = _apply_agg(df, x, y, agg).head(20)
            fig = px.bar(data, x=x, y=y, color=color or x,
                         color_discrete_sequence=COLORS, text=y, title=f"📊 {title}")
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
                              marker_line_width=0)
            fig.update_layout(showlegend=False, **LAYOUT)
            fig.update_xaxes(tickangle=-30)

            # ── In-chart dropdown: top-N filter ──────────────────────────────
            cats = data[x].tolist()
            if len(cats) > 5:
                buttons = [dict(
                    label="All",
                    method="update",
                    args=[{"x": [data[x].tolist()], "y": [data[y].tolist()]}]
                )]
                for n in [5, 10]:
                    if n < len(cats):
                        top = data.head(n)
                        buttons.append(dict(
                            label=f"Top {n}",
                            method="update",
                            args=[{"x": [top[x].tolist()], "y": [top[y].tolist()]}]
                        ))
                fig.update_layout(
                    updatemenus=[dict(
                        type="dropdown",
                        direction="down",
                        x=1.0, xanchor="right",
                        y=1.12, yanchor="top",
                        bgcolor="white",
                        bordercolor="#E2E8F0",
                        font=dict(size=12, color="#1E293B"),
                        buttons=buttons,
                        showactive=True,
                    )]
                )

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

            # ── In-chart range slider for time navigation ─────────────────────
            fig.update_xaxes(
                rangeslider=dict(visible=True, thickness=0.06, bgcolor="#F8FAFC"),
                rangeselector=dict(
                    buttons=[
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(step="all", label="All"),
                    ],
                    bgcolor="white",
                    bordercolor="#E2E8F0",
                    font=dict(size=11, color="#475569"),
                    activecolor="#6366F1",
                    x=0, y=1.08,
                ),
            )
            fig.update_layout(margin=dict(t=80, b=60, l=50, r=20))

        elif ct == "scatter":
            if not x or not y:
                return None
            fig = px.scatter(df, x=x, y=y, color=color,
                             color_discrete_sequence=COLORS, opacity=0.75,
                             title=f"🔵 {title}",
                             hover_data=df.columns.tolist()[:6])
            fig.update_layout(**LAYOUT)
            # Legend click filtering works natively when color is set
            if color:
                fig.update_layout(
                    legend=dict(
                        bgcolor="white",
                        bordercolor="#E2E8F0",
                        borderwidth=1,
                        title=dict(text=color.replace("_", " ").title()),
                        itemclick="toggle",
                        itemdoubleclick="toggleothers",
                    )
                )

        elif ct == "histogram":
            col = x or y
            if not col:
                return None
            fig = px.histogram(df, x=col, color=color,
                               color_discrete_sequence=COLORS,
                               nbins=25, marginal="box", title=f"📉 {title}")
            fig.update_layout(**LAYOUT)
            # If color column exists, legend click filters series
            if color:
                fig.update_layout(
                    legend=dict(
                        itemclick="toggle",
                        itemdoubleclick="toggleothers",
                    )
                )

        elif ct == "box":
            if not y:
                return None
            fig = px.box(df, x=x, y=y, color=x or color,
                         color_discrete_sequence=COLORS,
                         points="outliers", title=f"📦 {title}")
            fig.update_layout(**LAYOUT)
            # Legend click to show/hide categories
            fig.update_layout(
                legend=dict(
                    itemclick="toggle",
                    itemdoubleclick="toggleothers",
                )
            )

        elif ct == "pie":
            # cat_col is the category to slice by
            # y in the spec should be the category column (set by LLM or heuristic)
            cat_col = x if x and x in df.columns and df[x].dtype == object else None
            if not cat_col:
                cat_col = y if y and isinstance(y, str) and y in df.columns and df[y].dtype == object else None
            if not cat_col:
                # fallback: first categorical column
                obj_cols = [c for c in df.select_dtypes(include=["object"]).columns
                            if not is_identifier_col(c)]
                cat_col = obj_cols[0] if obj_cols else None
            if not cat_col:
                return None

            # Find the best numeric column to aggregate by
            numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                            if not is_identifier_col(c)]
            # Prefer revenue/sales/profit columns
            num_col = next(
                (c for c in numeric_cols if any(k in c.lower()
                 for k in ["sales", "revenue", "profit", "amount", "total", "value"])),
                numeric_cols[0] if numeric_cols else None,
            )

            if not num_col or agg == "count":
                # Count-based pie
                counts = df[cat_col].value_counts().head(8)
                vals = counts.values.tolist()
                names = [str(n) for n in counts.index.tolist()]
            else:
                grp = df.groupby(cat_col)[num_col].agg(agg).sort_values(ascending=False).head(8)
                vals = grp.values.tolist()
                names = [str(n) for n in grp.index.tolist()]

            if not vals:
                return None

            fig = px.pie(
                values=vals,
                names=names,
                hole=0.5,
                color_discrete_sequence=COLORS,
                title=f"🍩 {title}",
            )
            fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
                pull=[0.05] + [0] * (len(vals) - 1),
                hovertemplate="<b>%{label}</b><br>Value: %{value:,.0f}<br>Share: %{percent}<extra></extra>",
            )
            fig.update_layout(**LAYOUT)

        elif ct == "grouped_bar":
            if not x or not isinstance(y, list) or len(y) < 2:
                return None
            data = _apply_agg(df, x, y, agg)
            fig = go.Figure()
            bar_colors = ["#6366F1", "#10B981", "#F59E0B", "#F43F5E"]
            for i, col in enumerate(y):
                fig.add_trace(go.Bar(
                    name=col.replace("_", " ").title(),
                    x=data[x], y=data[col],
                    marker_color=bar_colors[i % len(bar_colors)],
                    text=data[col],
                    texttemplate="%{text:,.0f}", textposition="outside",
                ))
            fig.update_layout(
                barmode="group", title=f"📊 {title}",
                legend=dict(
                    itemclick="toggle",
                    itemdoubleclick="toggleothers",
                    bgcolor="white", bordercolor="#E2E8F0", borderwidth=1,
                ),
                **LAYOUT,
            )

            # ── In-chart dropdown: top-N filter ──────────────────────────────
            cats = data[x].tolist()
            if len(cats) > 5:
                buttons = []
                for n in ["All", 5, 10]:
                    if n == "All":
                        args = [{"x": [data[x].tolist()] * len(y),
                                 "y": [data[col].tolist() for col in y]}]
                        buttons.append(dict(label="All", method="update", args=args))
                    elif n < len(cats):
                        top = data.head(n)
                        args = [{"x": [top[x].tolist()] * len(y),
                                 "y": [top[col].tolist() for col in y]}]
                        buttons.append(dict(label=f"Top {n}", method="update", args=args))
                fig.update_layout(
                    updatemenus=[dict(
                        type="dropdown",
                        direction="down",
                        x=1.0, xanchor="right",
                        y=1.12, yanchor="top",
                        bgcolor="white",
                        bordercolor="#E2E8F0",
                        font=dict(size=12, color="#1E293B"),
                        buttons=buttons,
                        showactive=True,
                    )]
                )

        elif ct == "heatmap":
            numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                            if not is_identifier_col(c)]
            if len(numeric_cols) < 2:
                return None
            corr = df[numeric_cols[:8]].corr().round(2)
            fig = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=[c.replace("_", " ") for c in corr.columns],
                y=[c.replace("_", " ") for c in corr.columns],
                colorscale="RdBu_r", zmid=0, zmin=-1, zmax=1,
                text=corr.values, texttemplate="%{text:.2f}",
                hoverongaps=False,
            ))
            fig.update_layout(title=f"🔥 {title}", **LAYOUT)

        if fig is None:
            return None

        return {"fig": fig, "title": title, "plain": reason, "spec": spec}

    except Exception:
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

def build_charts(df, understanding="", use_llm=True):
    """LLM-driven chart selection with heuristic fallback."""
    numeric, categorical, date_cols = get_col_types(df)
    if not numeric and not categorical:
        return []

    specs = _llm_plan_charts(df, understanding, numeric, categorical, date_cols)
    if not specs:
        specs = _heuristic_plan(df, numeric, categorical, date_cols)
    # No second validation call — the LLM plan is already validated structurally

    charts = []
    for spec in specs:
        result = render_chart(df, spec)
        if result:
            charts.append(result)

    return charts
