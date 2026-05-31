"""Tab content sections for the analysis workspace."""

import re
import streamlit as st
import pandas as pd

from agents.chart_selector import (
    AGG_OPTIONS,
    CHART_TYPES,
    build_charts,
    get_anomalies,
    get_col_types,
    render_chart,
)
from agents.insight_generator import run_insight_generator
from agents.report_writer import run_report_writer
from app.state.cache import save_cached_pipeline_state
from app.styles import inject_chart_studio_styles
from app.ui.charts import build_chart_explanation, render_ai_chart_card, render_possible_actions
from app.ui.layout import progress_bar, render_data_in_use, render_next_steps, render_skeleton, section
from app.ui.pipeline import count_imputed_values
from app.ui.report import render_structured_report
from utils.helpers import col_type_badge, compute_business_kpis, md_to_html


def render_overview_tab(df, df_clean, df_view, kpis, profile, understanding, issues, cleaning_report):
    # ── KPI cards — first thing the user sees ─────────────────────────────────
    section("#EFF6FF", "📈", "Key metrics")
    st.markdown(kpis_html(kpis), unsafe_allow_html=True)
    if st.session_state.filters:
        active = ", ".join(f"{c}: {v}" for c, v in st.session_state.filters.items())
        st.caption(f"🔽 Filters active: {active} — showing {len(df_view):,} of {len(df_clean):,} rows")

    # ── Top issues — shown here in overview, not globally above tabs ──────────
    if issues:
        ranked = sorted(issues, key=lambda i: 0 if "High" in i.get("severity","") else 1 if "Medium" in i.get("severity","") else 2)[:3]
        bmap = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}
        section("#FFF7ED", "🚨", "Top data quality issues")
        for iss in ranked:
            sk = next((k for k in bmap if k in iss.get("severity", "")), "Low")
            st.markdown(
                f"""<div class="issue-row compact-issue">
                    <span class="badge {bmap[sk]}">{sk}</span>
                    <span style="font-weight:600;color:#1E293B;font-size:0.88rem;">{iss['type'].replace('_',' ').title()}</span>
                    <span style="color:#64748B;font-size:0.85rem;">in</span>
                    <code style="background:#F1F5F9;padding:2px 8px;border-radius:4px;font-size:0.82rem;color:#6366F1;">{iss['column']}</code>
                    <span style="color:#64748B;font-size:0.85rem;">— {iss['count']:,} rows ({iss['pct']}%)</span>
                    <span style="margin-left:auto;font-size:0.78rem;color:#94A3B8;">Fix: {iss['fix']}</span>
                </div>""",
                unsafe_allow_html=True,
            )
        if len(issues) > 3:
            st.caption(f"+ {len(issues) - 3} more issues — see **Data quality** tab for the full list")
    else:
        st.success("✅ No major data quality issues detected.")

    # ── Anomaly alerts with actionable Ask AI button ───────────────────────────
    anomalies = st.session_state.anomalies or []
    if anomalies:
        section("#FFF7ED", "⚠️", "Anomaly alerts")
        desc_map = {
            ("discount_pct", "profit"): "Higher discounts are associated with lower profit.",
            ("discount_pct", "total_sales"): "Discounts don't appear to drive proportionally higher sales.",
        }
        for c1, c2, val in anomalies[:3]:
            pair = tuple(sorted([c1, c2]))
            desc = desc_map.get(
                pair,
                f"When {c1.replace('_', ' ')} increases, {c2.replace('_', ' ')} tends to decrease.",
            )
            strength = "Strong" if val < -0.4 else "Moderate"
            anom_col, btn_col = st.columns([5, 1])
            with anom_col:
                st.markdown(
                    f"""<div class="anomaly-card">
                    <div class="anomaly-title">⚠️ {strength}: {c1.replace('_', ' ').title()} ↔ {c2.replace('_', ' ').title()} ({val})</div>
                    <div class="anomaly-desc">{desc}</div>
                </div>""",
                    unsafe_allow_html=True,
                )
            with btn_col:
                ask_q = f"Why does {c1.replace('_', ' ')} negatively correlate with {c2.replace('_', ' ')}?"
                if st.button("Ask AI →", key=f"ask_anom_{c1}_{c2}", use_container_width=True):
                    if st.session_state.qa_history is None:
                        st.session_state.qa_history = []
                    st.session_state.qa_history.append({"q": ask_q, "a": "", "cites": [], "plan": None})
                    from app.ui.navigation import set_workspace_tab
                    set_workspace_tab("ask")
                    from app.ui.layout import try_rerun
                    try_rerun()

    # ── Data in use — below KPIs so user sees numbers first ───────────────────
    with st.expander("🗂️ Dataset details — file, columns & filters", expanded=False):
        render_data_in_use(df, df_clean)

    # ── Raw data preview with informative label ────────────────────────────────
    with st.expander(
        f"📋 Raw data — {len(df):,} rows × {len(df.columns)} columns (before cleaning)",
        expanded=False,
    ):
        st.dataframe(df, use_container_width=True, height=220)

    # ── Next steps — at the bottom once user has context ──────────────────────
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    section("#F0FDF4", "🚀", "What to do next")
    st.markdown(render_next_steps(), unsafe_allow_html=True)


def render_quality_tab(df, df_clean, profile, issues, cleaning_report, understanding):
    progress_bar(0)

    # ── Column profile — modern card table ────────────────────────────────────
    section("#EFF6FF", "🕵️", "Column profile")
    col_rows = []
    for col, info in profile["column_details"].items():
        row = {
            "Column": col,
            "Type Badge": col_type_badge(info["dtype"], col),
            "Missing": f"{info['missing']} ({info['missing_pct']}%)",
            "Unique": info["unique"],
            "Sample": str(info["sample"][:2]),
        }
        if "mean" in info:
            row["Mean"] = f"{info['mean']:,}"
            row["Min"]  = f"{info['min']:,}"
            row["Max"]  = f"{info['max']:,}"
        col_rows.append(row)

    badge_html = (
        "<div style='overflow-x:auto;'>"
        "<table style='width:100%;border-collapse:collapse;font-size:0.84rem;'>"
        "<thead><tr style='background:#F8FAFC;'>"
    )
    for h in ["Column", "Type", "Missing", "Unique", "Sample", "Mean", "Min", "Max"]:
        badge_html += (
            f"<th style='padding:10px 14px;text-align:left;border-bottom:2px solid #E2E8F0;"
            f"color:#64748B;font-weight:700;font-size:0.72rem;text-transform:uppercase;"
            f"letter-spacing:.06em;white-space:nowrap;'>{h}</th>"
        )
    badge_html += "</tr></thead><tbody>"
    for i, row in enumerate(col_rows):
        bg = "#FFFFFF" if i % 2 == 0 else "#F8FAFC"
        badge_html += f"<tr style='background:{bg};border-bottom:1px solid #F1F5F9;'>"
        badge_html += f"<td style='padding:10px 14px;font-weight:600;color:#0F172A;'>{row['Column']}</td>"
        badge_html += f"<td style='padding:10px 14px;'>{row['Type Badge']}</td>"
        miss_val = row['Missing']
        miss_color = "#DC2626" if "(" in miss_val and float(miss_val.split("(")[1].rstrip("%)")) > 10 else "#64748B"
        badge_html += f"<td style='padding:10px 14px;color:{miss_color};font-weight:500;'>{miss_val}</td>"
        badge_html += f"<td style='padding:10px 14px;color:#64748B;'>{row['Unique']}</td>"
        badge_html += f"<td style='padding:10px 14px;color:#94A3B8;font-size:0.8rem;font-family:monospace;'>{row['Sample']}</td>"
        for k in ["Mean", "Min", "Max"]:
            badge_html += f"<td style='padding:10px 14px;color:#475569;'>{row.get(k, '—')}</td>"
        badge_html += "</tr>"
    badge_html += "</tbody></table></div>"
    st.markdown(badge_html, unsafe_allow_html=True)

    # ── All quality issues ────────────────────────────────────────────────────
    progress_bar(1)
    section("#FFF7ED", "🚨", "All quality issues")

    high = [i for i in issues if "High" in i["severity"]]
    med  = [i for i in issues if "Medium" in i["severity"]]
    low  = [i for i in issues if "Low" in i["severity"]]

    # Summary pills
    pill = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:1rem;">'
    if high:
        pill += f'<span style="background:#FEE2E2;color:#DC2626;padding:5px 16px;border-radius:20px;font-size:0.8rem;font-weight:700;">🔴 {len(high)} High</span>'
    if med:
        pill += f'<span style="background:#FEF3C7;color:#D97706;padding:5px 16px;border-radius:20px;font-size:0.8rem;font-weight:700;">🟡 {len(med)} Medium</span>'
    if low:
        pill += f'<span style="background:#DCFCE7;color:#16A34A;padding:5px 16px;border-radius:20px;font-size:0.8rem;font-weight:700;">🟢 {len(low)} Low</span>'
    if not issues:
        pill += '<span style="background:#F0FDF4;color:#16A34A;padding:5px 16px;border-radius:20px;font-size:0.8rem;font-weight:700;">✅ No issues found</span>'
    pill += "</div>"
    st.markdown(pill, unsafe_allow_html=True)

    sev_styles = {
        "High":   ("background:#FEE2E2;color:#DC2626;", "#FFF5F5", "#FCA5A5"),
        "Medium": ("background:#FEF3C7;color:#D97706;", "#FFFBEB", "#FCD34D"),
        "Low":    ("background:#DCFCE7;color:#16A34A;", "#F0FDF4", "#86EFAC"),
    }
    for iss in issues:
        sk = next((k for k in sev_styles if k in iss["severity"]), "Low")
        badge_style, row_bg, border_color = sev_styles[sk]
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;padding:11px 16px;'
            f'background:{row_bg};border:1px solid {border_color};border-radius:10px;margin-bottom:8px;">'
            f'<span style="{badge_style}padding:3px 12px;border-radius:20px;font-size:0.7rem;font-weight:700;'
            f'text-transform:uppercase;white-space:nowrap;">{sk}</span>'
            f'<span style="font-weight:600;color:#1E293B;font-size:0.88rem;">{iss["type"].replace("_"," ").title()}</span>'
            f'<span style="color:#64748B;font-size:0.82rem;">in</span>'
            f'<code style="background:rgba(255,255,255,0.7);padding:2px 8px;border-radius:4px;font-size:0.8rem;color:#6366F1;">{iss["column"]}</code>'
            f'<span style="color:#64748B;font-size:0.82rem;">— {iss["count"]:,} rows ({iss["pct"]}%)</span>'
            f'<span style="margin-left:auto;font-size:0.78rem;color:#64748B;font-style:italic;">💡 {iss["fix"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Cleaning summary ──────────────────────────────────────────────────────
    section("#F0FDF4", "🧹", "Cleaning summary")
    original_rows = len(df)
    duplicates_dropped = max(original_rows - len(df_clean), 0)
    values_imputed = count_imputed_values(cleaning_report)

    c1, c2, c3 = st.columns(3)
    c1.metric("Original rows", f"{original_rows:,}")
    c2.metric("Duplicates removed", f"{duplicates_dropped:,}")
    c3.metric("Values filled", f"{values_imputed:,}")

    if cleaning_report:
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;'
            'color:#64748B;margin:1rem 0 0.5rem 0;">STEPS APPLIED</div>',
            unsafe_allow_html=True,
        )
        for step in cleaning_report:
            clean = step.replace("✅", "").strip()
            st.markdown(
                f'<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 14px;'
                f'background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;margin-bottom:6px;">'
                f'<span style="color:#16A34A;font-size:1rem;flex-shrink:0;">✓</span>'
                f'<span style="color:#166534;font-size:0.87rem;line-height:1.5;">{clean}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    delta = len(df) - len(df_clean)
    st.markdown(
        f'<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;'
        f'padding:12px 18px;margin-top:8px;display:flex;align-items:center;gap:12px;">'
        f'<span style="font-size:1.2rem;">📉</span>'
        f'<span style="color:#166534;font-weight:600;">'
        f'{len(df):,} rows → <strong>{len(df_clean):,} rows</strong>'
        f'{"  ·  " + str(delta) + " duplicate rows removed" if delta > 0 else "  ·  no rows removed"}'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    with st.expander("📋 Cleaned data preview", expanded=False):
        st.dataframe(df_clean, use_container_width=True, height=220)
        st.download_button(
            "⬇ Download cleaned CSV",
            data=df_clean.to_csv(index=False).encode("utf-8"),
            file_name="cleaned_data.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_charts_tab(df_view, understanding):
    progress_bar(2)
    section("#F5F3FF", "📊", "Visual analysis")
    inject_chart_studio_styles()
    all_cols = df_view.columns.tolist()

    # ── Toolbar — always at top ───────────────────────────────────────────────
    tb_left, tb_mid, tb_right = st.columns([1, 2, 3])
    with tb_left:
        if st.button("↺ Regenerate", use_container_width=True):
            st.session_state.charts = None
            st.session_state.cached_chart_specs = None
            st.rerun()
    with tb_mid:
        st.markdown(
            '<span style="background:linear-gradient(90deg,#6366F1,#8B5CF6);color:white;'
            'padding:4px 12px;border-radius:20px;font-size:0.7rem;font-weight:700;'
            'letter-spacing:.04em;display:inline-block;margin-top:4px;">🤖 AI SELECTED</span>',
            unsafe_allow_html=True,
        )
    with tb_right:
        st.markdown(
            '<span style="font-size:0.8rem;color:#94A3B8;line-height:2.4;">'
            'Charts are chosen by AI based on your data · Customize below in Chart Studio</span>',
            unsafe_allow_html=True,
        )

    if st.session_state.charts is None:
        cached_specs = st.session_state.get("cached_chart_specs")
        if cached_specs:
            rebuilt = []
            for spec in cached_specs:
                result = render_chart(df_view, spec)
                if result:
                    rebuilt.append(result)
            st.session_state.charts = rebuilt
        else:
            # Skeleton loading screen — set charts=[] as safety before building
            st.session_state.charts = []
            render_skeleton("AI is selecting the best charts for your data…", rows=3, show_chart=True)
            try:
                built = build_charts(df_view, understanding)
                st.session_state.charts = built
                st.session_state.cached_chart_specs = [
                    c.get("spec") for c in built if c.get("spec")
                ]
                save_cached_pipeline_state()
            except Exception as e:
                st.session_state.charts = []
                st.markdown(
                    f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;'
                    f'padding:14px 18px;margin:8px 0;">'
                    f'<div style="font-weight:700;color:#991B1B;margin-bottom:6px;">🔴 Chart generation failed</div>'
                    f'<div style="color:#7F1D1D;font-size:0.9rem;">{str(e)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.rerun()

    charts = st.session_state.charts or []

    # ── Pinned dashboard — compact thumbnails ────────────────────────────────
    pinned = st.session_state.get("pinned_charts") or []
    if pinned:
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;'
            'color:#6366F1;margin:1rem 0 0.5rem 0;">📌 PINNED DASHBOARD</div>',
            unsafe_allow_html=True,
        )
        pin_cols = st.columns(min(len(pinned), 4))
        for i, p in enumerate(pinned):
            with pin_cols[i % 4]:
                try:
                    # Compact figure — reduce margins for thumbnail look
                    import copy
                    fig_thumb = copy.deepcopy(p["fig"])
                    fig_thumb.update_layout(
                        height=180,
                        margin=dict(t=30, b=20, l=20, r=10),
                        title_font_size=11,
                        showlegend=False,
                    )
                    st.plotly_chart(
                        fig_thumb,
                        use_container_width=True,
                        config={"displaylogo": False, "displayModeBar": False},
                        key=f"pinned_{i}",
                    )
                    st.caption(p.get("title", "Pinned")[:30])
                except Exception:
                    st.caption("(Could not render)")

    if charts:
        i = 0
        while i < len(charts):
            if i + 1 < len(charts):
                left, right = st.columns(2)
                for offset, (ctx, ci) in enumerate([(left, charts[i]), (right, charts[i + 1])]):
                    with ctx:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        render_ai_chart_card(ci, f"pair_{i}_{offset}", df_view, all_cols)
                        st.markdown("</div>", unsafe_allow_html=True)
                i += 2
            else:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                render_ai_chart_card(charts[i], f"single_{i}", df_view, all_cols)
                st.markdown("</div>", unsafe_allow_html=True)
                i += 1
    else:
        st.info("No charts generated yet. Use Chart Studio below to build one.")

    # ── Chart Studio ──────────────────────────────────────────────────────────
    st.markdown(
        '<div style="border-top:1px solid #E2E8F0;margin:1.5rem 0 1rem;"></div>'
        '<div style="font-size:0.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;'
        'color:#64748B;margin-bottom:0.75rem;">🎨 CHART STUDIO — BUILD YOUR OWN</div>',
        unsafe_allow_html=True,
    )

    num_cols, cat_cols, _ = get_col_types(df_view)
    axis_opts  = ["— none —"] + all_cols
    color_opts = ["— none —"] + cat_cols

    with st.form("chart_studio_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            ct = st.selectbox("Chart type", CHART_TYPES, index=0)
        with c2:
            x_sel = st.selectbox("X axis", axis_opts, index=0)
        with c3:
            y_sel = st.selectbox("Y axis", axis_opts, index=0)
        c4, c5 = st.columns(2)
        with c4:
            agg_sel = st.selectbox("Aggregation", AGG_OPTIONS, index=0)
        with c5:
            color_sel = st.selectbox("Color by", color_opts, index=0)
        # Y axis 2 only relevant for grouped_bar
        y2_sel = "— none —"
        if ct == "grouped_bar":
            y2_sel = st.selectbox("Y axis 2 (grouped bar only)", axis_opts, index=0)
        chart_title = st.text_input("Chart title", placeholder="e.g. Sales by region")
        add_btn = st.form_submit_button("➕ Add chart", use_container_width=True, type="primary")

    if add_btn:
        x_val    = None if x_sel    == "— none —" else x_sel
        y_val    = None if y_sel    == "— none —" else y_sel
        color_val= None if color_sel== "— none —" else color_sel
        y2_val   = None if y2_sel   == "— none —" else y2_sel
        y_final  = [y_val, y2_val] if ct == "grouped_bar" and y_val and y2_val else y_val
        spec = {
            "chart_type": ct, "x": x_val, "y": y_final, "color": color_val,
            "agg": agg_sel,
            "title": chart_title or f"{ct} — {y_val or ''} by {x_val or ''}",
            "reason": "Manually created chart",
        }
        result = render_chart(df_view, spec)
        if result:
            if st.session_state.custom_charts is None:
                st.session_state.custom_charts = []
            st.session_state.custom_charts.append(result)
            st.success(f"✅ Added: {spec['title']}")
            st.rerun()
        else:
            st.error("Could not build that chart — check column selections.")

    if st.session_state.custom_charts is None:
        st.session_state.custom_charts = []
    for idx, ci in enumerate(st.session_state.custom_charts or []):
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        col_chart, col_del = st.columns([6, 1])
        with col_chart:
            st.plotly_chart(
                ci["fig"],
                use_container_width=True,
                config={"displaylogo": False},
                key=f"custom_chart_{idx}",
            )
            st.markdown(f'<p class="chart-lbl">{ci["title"]}</p>', unsafe_allow_html=True)
            expl = build_chart_explanation(df_view, ci.get("spec", {}))
            st.markdown(f'<p class="chart-desc"><strong>Insight:</strong> {expl}</p>', unsafe_allow_html=True)
            render_possible_actions(ci.get("spec", {}), df=df_view)
        with col_del:
            if st.button("🗑 Remove", key=f"del_chart_{idx}", use_container_width=True):
                st.session_state.custom_charts.pop(idx)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_report_tab(df_view, understanding, kpis, cleaning_report):
    progress_bar(4)

    # ── Toolbar: download buttons at top + regenerate ─────────────────────────
    from app.ui.report import report_to_docx_bytes, report_to_pdf_bytes

    tb1, tb2, tb3, tb4 = st.columns([2, 1, 1, 1])
    with tb1:
        if st.button("↺ Regenerate report", use_container_width=True):
            st.session_state.report = None
            st.session_state.insights = None
            st.rerun()
    with tb2:
        report_text = st.session_state.get("report") or ""
        st.download_button(
            "⬇ .md",
            data=report_text.encode("utf-8") if report_text else b"",
            file_name="analysis_report.md",
            mime="text/markdown",
            use_container_width=True,
            disabled=not report_text,
        )
    with tb3:
        docx_bytes = report_to_docx_bytes(report_text) if report_text else b""
        st.download_button(
            "⬇ .docx",
            data=docx_bytes,
            file_name="analysis_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            disabled=not report_text,
        )
    with tb4:
        pdf_bytes = report_to_pdf_bytes(report_text) if report_text else b""
        st.download_button(
            "⬇ .pdf",
            data=pdf_bytes if pdf_bytes else b"",
            file_name="analysis_report.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=not (report_text and pdf_bytes),
            help="PDF export requires weasyprint or xhtml2pdf to be installed" if not pdf_bytes else None,
        )

        # Debug/status indicator: show whether PDF bytes were produced and size.
        try:
            pdf_size = len(pdf_bytes or b"")
        except Exception:
            pdf_size = 0
        if report_text:
            if pdf_size:
                st.caption(f"PDF ready — {pdf_size:,} bytes")
            else:
                st.caption("PDF not available yet — installer fallback used or generation failed.")

    # ── Compact KPI strip ─────────────────────────────────────────────────────
    if kpis:
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:700;letter-spacing:.08em;'
            'text-transform:uppercase;color:#64748B;margin:1rem 0 0.5rem 0;">KEY METRICS</div>',
            unsafe_allow_html=True,
        )
        st.markdown(kpis_html(kpis), unsafe_allow_html=True)

    # ── Generate insights ─────────────────────────────────────────────────────
    if st.session_state.insights is None:
        render_skeleton("Generating insights…", rows=3)
        try:
            st.session_state.insights = run_insight_generator(df_view, understanding)
        except Exception as e:
            st.session_state.insights = f"Could not generate insights: {e}"
        save_cached_pipeline_state()
        st.rerun()

    # ── Render insights as structured cards ───────────────────────────────────
    raw = st.session_state.insights or ""
    if raw and not raw.startswith("Could not"):
        section("#EEF2FF", "💡", "Quick insights")
        # Parse insight lines — handle both bullet and numbered formats
        insight_lines = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # Strip leading bullets/numbers
            clean = re.sub(r'^[-•*]\s*', '', line)
            clean = re.sub(r'^\d+\.\s*', '', clean)
            if clean:
                insight_lines.append(clean)

        for i, insight in enumerate(insight_lines[:5]):
            # Extract headline (bold part) and body
            bold_match = re.search(r'\*\*(.+?)\*\*', insight)
            if bold_match:
                headline = bold_match.group(1)
                body = insight[bold_match.end():].lstrip(' —–-').strip()
                # Convert remaining bold markers
                body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body)
            else:
                headline = insight[:60] + ("…" if len(insight) > 60 else "")
                body = ""

            st.markdown(
                f'<div style="background:white;border:1px solid #E2E8F0;border-left:4px solid #6366F1;'
                f'border-radius:10px;padding:14px 18px;margin-bottom:10px;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
                f'<div style="font-weight:700;color:#0F172A;font-size:0.92rem;margin-bottom:4px;">'
                f'💡 {headline}</div>'
                f'{"<div style=color:#475569;font-size:0.85rem;line-height:1.55;>" + body + "</div>" if body else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Generate report ───────────────────────────────────────────────────────
    if st.session_state.report is None:
        render_skeleton("Writing business report…", rows=4)
        try:
            # Collect streamed chunks into a single string (avoid streaming UI which can show raw HTML)
            gen = run_report_writer(
                df_view,
                understanding,
                st.session_state.insights or "Analysis complete.",
                cleaning_report or [],
                stream=True,
                kpis=kpis,
            )
            full_report = ""
            for chunk in gen:
                if chunk:
                    full_report += chunk
            st.session_state.report = full_report.strip()
        except Exception as e:
            st.session_state.report = (
                f"## Analysis Complete\n\n**What we found:** {understanding}\n\n"
                f"**Records:** {len(df_view):,}\n\nReport unavailable: {e}"
            )
        save_cached_pipeline_state()
        st.rerun()

    # ── Render report ─────────────────────────────────────────────────────────
    section("#F8FAFF", "📖", "Business report")
    report_text_to_render = st.session_state.report or ""

    # Style the markdown report with a card wrapper
    st.markdown(
        """
        <style>
        /* Style the report markdown output */
        .report-md-wrap h1, .report-md-wrap h2 {
            color: #0F172A; font-weight: 700;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 6px; margin: 1.4rem 0 0.7rem;
        }
        .report-md-wrap h3 { color: #334155; font-weight: 600; margin: 1rem 0 0.4rem; }
        .report-md-wrap p  { color: #334155; line-height: 1.7; margin: 0 0 10px; }
        .report-md-wrap ul, .report-md-wrap ol { padding-left: 20px; margin: 6px 0 12px; }
        .report-md-wrap li { color: #334155; margin-bottom: 6px; line-height: 1.6; }
        .report-md-wrap strong { color: #0F172A; }
        </style>
        <div class="report-md-wrap" style="background:linear-gradient(135deg,#F8FAFF,#F0F4FF);
             border:1px solid #C7D2FE;border-radius:14px;padding:1.8rem 2.2rem;margin-bottom:1rem;">
        """,
        unsafe_allow_html=True,
    )
    # Render using structured, themed HTML (fixes encoding and applies styles)
    from app.ui.report import render_structured_report
    rendered_html = render_structured_report(report_text_to_render, df_view, kpis, cleaning_report, st.session_state.insights or "")
    # Use Streamlit's HTML component to render raw HTML/CSS reliably.
    try:
        import streamlit.components.v1 as components
        components.html(rendered_html, height=600, scrolling=True)
    except Exception:
        # Fallback to markdown with unsafe HTML if components unavailable
        st.markdown(rendered_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Download filtered CSV ─────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    st.download_button(
        "⬇ Download filtered CSV",
        data=df_view.to_csv(index=False).encode("utf-8"),
        file_name="filtered_data.csv",
        mime="text/csv",
        use_container_width=False,
    )


def render_ask_tab_hint():
    st.markdown(
        """
        <div class="ask-tab-hint">
            <p><strong>Chat with your data</strong></p>
            <p>Use the <strong>Ask your data</strong> panel on the right to ask questions.
            On smaller screens, scroll down to the chat panel below the tabs.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpis_html(kpis):
    html = '<div class="kpi-grid">'
    for k in kpis:
        html += f"""<div class="kpi-card {k['color']}">
            <div class="kpi-lbl">{k['label']}<span class="kpi-ico">{k['icon']}</span></div>
            <div class="kpi-val">{k['value']}</div>
            <div class="kpi-sub">{k['sub']}</div>
        </div>"""
    html += "</div>"
    return html


def ensure_anomalies(df_clean):
    if st.session_state.anomalies is None:
        st.session_state.anomalies = get_anomalies(df_clean)
