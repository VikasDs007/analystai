"""Review & continue gate after the detective step."""

import html as html_lib
import streamlit as st
import streamlit.components.v1 as components

from agents.cleaner import run_cleaner
from app.config import CACHE_CLEAN_CSV
from app.state.cache import save_cached_pipeline_state
from app.ui.cleaning_diff import compute_cleaning_diff, render_cleaning_diff
from app.ui.layout import try_rerun, render_skeleton
from utils.helpers import safe_agent_call


def _issue_severity_rank(issue):
    sev = issue.get("severity", "")
    if "High" in sev:
        return 0
    if "Medium" in sev:
        return 1
    return 2


def render_review_gate(df, detective_result):
    """Block the pipeline until the user chooses how to handle cleaning."""
    if detective_result is None:
        render_skeleton("AI is profiling your data…", rows=4)
        return

    issues = detective_result.get("issues") or []
    understanding = detective_result.get("understanding", "")
    profile = detective_result.get("profile") or {}

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="background:linear-gradient(135deg,#FFFBEB,#FEF3C7);border:1px solid #FCD34D;'
        'border-radius:14px;padding:1.1rem 1.4rem;margin-bottom:1rem;">'
        '<div style="font-size:1.05rem;font-weight:700;color:#92400E;margin-bottom:4px;">🔍 Data profiling complete</div>'
        '<div style="font-size:0.88rem;color:#B45309;line-height:1.45;">'
        'Review the issues below. Check the ones you want fixed, then click <strong>Clean selected</strong>.'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # ── Stats row ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{profile.get('rows', len(df)):,}")
    c2.metric("Columns", f"{profile.get('columns', len(df.columns)):,}")
    c3.metric("Issues found", str(len(issues)))
    c4.metric("Missing cells", f"{profile.get('missing_pct', 0)}%")

    # ── AI understanding ──────────────────────────────────────────────────────
    if understanding:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#EFF6FF,#F8FAFC);border:1px solid #BFDBFE;'
            f'border-radius:12px;padding:1rem 1.2rem;margin:0.75rem 0;">'
            f'<div style="font-size:0.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;'
            f'color:#3B82F6;margin-bottom:6px;">🤖 AI understanding</div>'
            f'<div style="color:#1E293B;font-size:0.92rem;line-height:1.55;">{html_lib.escape(str(understanding))}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Issue checkboxes ──────────────────────────────────────────────────────
    if issues:
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;'
            'color:#64748B;margin:1rem 0 0.5rem 0;">SELECT ISSUES TO FIX</div>',
            unsafe_allow_html=True,
        )

        sev_color = {"High": ("#FEE2E2", "#DC2626"), "Medium": ("#FEF3C7", "#D97706"), "Low": ("#DCFCE7", "#16A34A")}
        ranked = sorted(issues, key=_issue_severity_rank)

        selected_keys = []
        for idx, iss in enumerate(ranked[:12]):
            sev_raw = iss.get("severity", "Low")
            sev_key = next((k for k in sev_color if k in sev_raw), "Low")
            bg, fg = sev_color[sev_key]
            col_chk, col_info = st.columns([1, 11])
            with col_chk:
                checked = st.checkbox(
                    "fix",
                    value=True,
                    key=f"fix_issue_{idx}",
                    label_visibility="collapsed",
                )
            with col_info:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;'
                    f'background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;margin-bottom:4px;">'
                    f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:20px;'
                    f'font-size:0.7rem;font-weight:700;text-transform:uppercase;white-space:nowrap;">{sev_key}</span>'
                    f'<span style="font-weight:600;color:#1E293B;font-size:0.88rem;">'
                    f'{html_lib.escape(iss.get("type","").replace("_"," ").title())}</span>'
                    f'<span style="color:#64748B;font-size:0.82rem;">in</span>'
                    f'<code style="background:#F1F5F9;padding:2px 8px;border-radius:4px;font-size:0.8rem;color:#6366F1;">'
                    f'{html_lib.escape(str(iss.get("column","")))}</code>'
                    f'<span style="color:#64748B;font-size:0.82rem;">'
                    f'— {iss.get("count",0):,} rows ({iss.get("pct",0)}%)</span>'
                    f'<span style="margin-left:auto;font-size:0.78rem;color:#94A3B8;">'
                    f'Fix: {html_lib.escape(str(iss.get("fix","")))}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if checked:
                selected_keys.append(idx)

        if len(issues) > 12:
            st.caption(f"+ {len(issues) - 12} more issues not shown")
    else:
        st.success("✅ No major quality issues detected. Your data looks clean.")
        selected_keys = []

    # ── Action buttons ────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([2, 2, 1])
    with b1:
        btn_label = f"🧹 Clean selected ({len(selected_keys)} issues)" if issues else "✅ Continue"
        if st.button(btn_label, type="primary", width="stretch", key="gate_auto_clean"):
            selected_issues = [ranked[i] for i in selected_keys] if issues else []
            _apply_auto_clean(df, selected_issues)
            try_rerun()
    with b2:
        if st.button("⏭ Skip cleaning — use raw data", width="stretch", key="gate_skip_clean"):
            _apply_skip_clean(df)
            try_rerun()
    with b3:
        st.download_button(
            "⬇ Raw CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="raw_data.csv",
            mime="text/csv",
            width="stretch",
            key="gate_download_raw",
        )


def _apply_auto_clean(df, issues):
    render_skeleton("Cleaning selected issues…", rows=3)
    result = safe_agent_call(
        run_cleaner, df, issues,
        fallback=(df.copy(), ["⚠️ Cleaning agent failed — using raw data."]),
        agent_name="cleaner",
    )
    df_clean, cleaning_report = result
    st.session_state.df_clean = df_clean
    st.session_state.cleaning_report = cleaning_report
    st.session_state.cleaning_decision = "auto"
    st.session_state.cleaning_diff = compute_cleaning_diff(df, df_clean, cleaning_report)
    try:
        df_clean.to_csv(CACHE_CLEAN_CSV, index=False)
    except Exception:
        pass
    save_cached_pipeline_state()


def _apply_skip_clean(df):
    st.session_state.df_clean = df.copy()
    st.session_state.cleaning_report = ["Skipped automatic cleaning — using raw data as-is."]
    st.session_state.cleaning_decision = "skipped"
    st.session_state.cleaning_diff = compute_cleaning_diff(
        df, st.session_state.df_clean, st.session_state.cleaning_report,
    )
    try:
        st.session_state.df_clean.to_csv(CACHE_CLEAN_CSV, index=False)
    except Exception:
        pass
    save_cached_pipeline_state()


def render_post_cleaning_diff():
    """Show modern structured cleaning results after cleaning."""
    diff = st.session_state.get("cleaning_diff")
    decision = st.session_state.get("cleaning_decision")
    if not diff or decision not in ("auto", "skipped"):
        return

    if decision == "skipped":
        st.markdown(
            '<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;'
            'padding:10px 16px;margin:0.5rem 0 1rem;display:flex;align-items:center;gap:10px;">'
            '<span style="font-size:1.1rem;">⏭</span>'
            '<span style="color:#166534;font-size:0.88rem;font-weight:500;">Using raw data — cleaning was skipped.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # Modern cleaning results card
    rows_before = diff.get("rows_before", 0)
    rows_after = diff.get("rows_after", 0)
    rows_removed = diff.get("rows_removed", 0)
    imputed = diff.get("imputed_cols", [])
    report = diff.get("cleaning_report", [])

    with st.expander("✅ Cleaning complete — view results", expanded=True):
        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Before", f"{rows_before:,} rows")
        m2.metric("After", f"{rows_after:,} rows")
        m3.metric("Removed", f"{rows_removed:,} rows", delta=f"-{rows_removed}" if rows_removed else "0")
        m4.metric("Columns fixed", str(len(imputed)))

        if report:
            st.markdown(
                '<div style="font-size:0.72rem;font-weight:700;letter-spacing:.08em;'
                'text-transform:uppercase;color:#64748B;margin:1rem 0 0.5rem 0;">WHAT WAS FIXED</div>',
                unsafe_allow_html=True,
            )
            for step in report:
                clean_step = step.replace("✅", "").strip()
                st.markdown(
                    f'<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 14px;'
                    f'background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;margin-bottom:6px;">'
                    f'<span style="color:#16A34A;font-size:1rem;flex-shrink:0;">✓</span>'
                    f'<span style="color:#166534;font-size:0.87rem;line-height:1.5;">{html_lib.escape(clean_step)}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
