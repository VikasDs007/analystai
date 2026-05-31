"""Main analysis workspace when a dataset is loaded."""

import json
import concurrent.futures
import threading
import time

import streamlit as st

from agents.detective import run_detective
from app.styles import inject_workspace_layout_styles
from app.ui.cleaning_gate import render_post_cleaning_diff, render_review_gate
from app.ui.filter_banner import render_filters_dirty_banner
from app.ui.navigation import get_workspace_tab, render_workspace_stepper
from app.ui.summary import render_above_fold_summary
from app.ui.workspace_header import render_compact_header
from app.views.qa_panel import render_qa_panel
from app.views.workspace_sections import (
    ensure_anomalies,
    render_ask_tab_hint,
    render_charts_tab,
    render_overview_tab,
    render_quality_tab,
    render_report_tab,
)
from utils.helpers import compute_business_kpis, get_llm_provider_name, has_api_key as has_groq_api_key


_DETECTIVE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1)


def _run_detective(df):
    if st.session_state.get("detective_result") is not None:
        return st.session_state.detective_result
    future = st.session_state.get("analysis_future")
    if st.session_state.get("analysis_in_progress"):
        if future is not None and future.done():
            try:
                st.session_state.detective_result = future.result()
            except Exception:
                st.session_state.detective_result = {
                    "understanding": "",
                    "issues": [],
                    "profile": {"column_details": {}},
                }
            st.session_state.analysis_in_progress = False
            st.session_state.analysis_future = None
            return st.session_state.detective_result
        return None

    def _worker():
        try:
            return run_detective(df, use_llm=True)
        except Exception:
            return {
                "understanding": "",
                "issues": [],
                "profile": {"column_details": {}},
            }

    st.session_state.analysis_in_progress = True
    st.session_state.analysis_start_ts = time.time()
    rows = len(df) if df is not None else 0
    st.session_state.analysis_est_seconds = max(10, int(rows / 10000.0 * 45))
    st.session_state.analysis_future = _DETECTIVE_EXECUTOR.submit(_worker)
    return None


@st.fragment(run_every=1)
def _render_analysis_progress():
    if not st.session_state.get("analysis_in_progress"):
        future = st.session_state.get("analysis_future")
        if future is not None and future.done() and st.session_state.get("detective_result") is None:
            try:
                st.session_state.detective_result = future.result()
            except Exception:
                st.session_state.detective_result = {
                    "understanding": "",
                    "issues": [],
                    "profile": {"column_details": {}},
                }
            st.session_state.analysis_future = None
            st.rerun()
        return

    if st.session_state.get("detective_result") is not None:
        st.session_state.analysis_in_progress = False
        st.session_state.analysis_future = None
        st.rerun()
        return

    future = st.session_state.get("analysis_future")
    if future is not None and future.done():
        try:
            st.session_state.detective_result = future.result()
        except Exception:
            st.session_state.detective_result = {
                "understanding": "",
                "issues": [],
                "profile": {"column_details": {}},
            }
        st.session_state.analysis_in_progress = False
        st.session_state.analysis_future = None
        st.rerun()
        return

    est = st.session_state.get("analysis_est_seconds", 30)
    start = st.session_state.get("analysis_start_ts", time.time())
    elapsed = int(time.time() - start)
    pct = min(98, int((elapsed / float(est)) * 100))
    from app.ui.layout import render_skeleton
    render_skeleton(f"AI is analysing your data… {pct}%", rows=4)

def _filtered_view(df_clean):
    df_view = df_clean.copy()
    for col, vals in (st.session_state.filters or {}).items():
        if col in df_view.columns and vals:
            df_view = df_view[df_view[col].isin(vals)]
    return df_view


def render_workspace(df):
    get_workspace_tab("overview")

    uploaded = bool(st.session_state.get("last_file_id"))
    analysing = bool(st.session_state.get("analysis_in_progress"))
    done = bool(st.session_state.get("detective_result"))
    cols = st.columns([1, 1, 1])
    labels = ["Upload", "Analysing", "Explore results"]
    states = [uploaded, analysing, done]
    for col, lab, stt in zip(cols, labels, states):
        with col:
            status = "✅" if stt else "○"
            if lab == "Analysing" and analysing:
                status = "🔄"
            if lab == "Analysing" and done and not analysing:
                status = "✅"
            st.markdown(f"<div style='text-align:center;font-weight:600;'>{status}<br>{lab}</div>", unsafe_allow_html=True)

    res = _run_detective(df)
    understanding = res["understanding"] if res else ""
    issues = res["issues"] if res else []
    profile = res["profile"] if res else {"column_details": {}}

    if st.session_state.get("analysis_in_progress"):
        _render_analysis_progress()

    inject_workspace_layout_styles()
    render_compact_header(df, st.session_state.get("df_clean"))

    decision = st.session_state.get("cleaning_decision")
    if decision not in ("auto", "skipped"):
        if decision is None:
            st.session_state.cleaning_decision = "pending"
        render_review_gate(df, res)
        return

    df_clean = st.session_state.df_clean
    cleaning_report = st.session_state.cleaning_report or []

    render_above_fold_summary(understanding, issues)
    render_post_cleaning_diff()
    render_filters_dirty_banner()

    df_view = _filtered_view(df_clean)
    ensure_anomalies(df_clean)
    kpis = compute_business_kpis(df_view)

    st.markdown('<div class="workspace-layout">', unsafe_allow_html=True)

    tab = get_workspace_tab()

    # Ask tab gets full width with the QA panel front and centre
    if tab == "ask":
        render_workspace_stepper()
        render_qa_panel(df_view, understanding, st.session_state.insights or "")
    else:
        # All other tabs: full-width main content, no right panel
        render_workspace_stepper()
        if tab == "overview":
            render_overview_tab(df, df_clean, df_view, kpis, profile, understanding, issues, cleaning_report)
        elif tab == "quality":
            render_quality_tab(df, df_clean, profile, issues, cleaning_report, understanding)
        elif tab == "charts":
            render_charts_tab(df_view, understanding)
        elif tab == "report":
            render_report_tab(df_view, understanding, kpis, cleaning_report)

    st.markdown("</div>", unsafe_allow_html=True)

    provider_name = get_llm_provider_name()
    footer_label = f"Powered by {provider_name}" if provider_name else "AI-assisted analysis"
    st.markdown(
        f"""<div class="footer">
        <span>AnalystAI</span> · Data Intelligence Platform · Built with Streamlit · Created by OpenAI Codex · {footer_label}
        </div>""",
        unsafe_allow_html=True,
    )

    try:
        if st.session_state.get("show_tour") and not st.session_state.get("tour_completed"):
            steps = [
                {"id": "tour-upload", "title": "Upload", "text": "Start by uploading a CSV file using the uploader on the left."},
                {"id": "tour-filters", "title": "Filters", "text": "Use the Filters section in the sidebar to narrow your view."},
                {"id": "tour-ask-box", "title": "Ask", "text": "Ask your data in the Ask panel — press Enter or click Ask to run."},
                {"id": "", "title": "Charts", "text": "AI generates chart suggestions in the Charts tab; pin favorites to the dashboard."},
            ]
            steps_json = json.dumps(steps)
            js = """
            <script>
            (function(){
                const steps = %s;
                let idx = 0;
                function cleanup(){
                    const ov = document.getElementById('coach_overlay'); if (ov) ov.remove();
                    const bx = document.getElementById('coach_box'); if (bx) bx.remove();
                }
                function overlay(){
                    const ov = document.createElement('div');
                    ov.id = 'coach_overlay';
                    ov.style.position = 'fixed';
                    ov.style.inset = '0';
                    ov.style.background = 'rgba(15,23,42,0.52)';
                    ov.style.backdropFilter = 'blur(2px)';
                    ov.style.zIndex = '99999';
                    ov.style.opacity = '0';
                    ov.style.transition = 'opacity 180ms ease';
                    document.body.appendChild(ov);
                    requestAnimationFrame(function(){ ov.style.opacity = '1'; });
                    return ov;
                }
                function highlight(el){
                    const r = el.getBoundingClientRect();
                    const box = document.createElement('div');
                    box.id = 'coach_box';
                    box.style.position = 'fixed';
                    box.style.left = (r.left - 4) + 'px';
                    box.style.top = (r.top - 4) + 'px';
                    box.style.width = (r.width + 8) + 'px';
                    box.style.height = (r.height + 8) + 'px';
                    box.style.border = '3px solid #FDE68A';
                    box.style.borderRadius = '12px';
                    box.style.boxShadow = '0 0 0 5000px rgba(15,23,42,0.10)';
                    box.style.pointerEvents = 'none';
                    box.style.zIndex = '100000';
                    document.body.appendChild(box);
                }
                function clamp(n, min, max){ return Math.max(min, Math.min(max, n)); }
                function place(panel, rect){
                    const vw = window.innerWidth, vh = window.innerHeight;
                    const pw = panel.offsetWidth || 360, ph = panel.offsetHeight || 220;
                    const spaces = { right: vw - rect.right - 24, left: rect.left - 24, bottom: vh - rect.bottom - 24, top: rect.top - 24 };
                    let placement = 'right';
                    if (spaces.right < pw && spaces.bottom >= ph) placement = 'bottom';
                    else if (spaces.right < pw && spaces.left >= pw) placement = 'left';
                    else if (spaces.bottom < ph && spaces.top >= ph) placement = 'top';
                    let left = 0, top = 0;
                    if (placement === 'right') { left = rect.right + 12; top = rect.top + rect.height/2 - ph/2; }
                    else if (placement === 'left') { left = rect.left - pw - 12; top = rect.top + rect.height/2 - ph/2; }
                    else if (placement === 'bottom') { left = rect.left + rect.width/2 - pw/2; top = rect.bottom + 12; }
                    else { left = rect.left + rect.width/2 - pw/2; top = rect.top - ph - 12; }
                    panel.style.left = clamp(left, 16, vw - pw - 16) + 'px';
                    panel.style.top = clamp(top, 16, vh - ph - 16) + 'px';
                    panel.setAttribute('data-placement', placement);
                }
                function arrow(placement){
                    const a = document.createElement('div');
                    a.style.position = 'absolute';
                    a.style.width = '0'; a.style.height = '0';
                    a.style.borderLeft = '10px solid transparent';
                    a.style.borderRight = '10px solid transparent';
                    a.style.borderTop = '10px solid transparent';
                    a.style.borderBottom = '10px solid transparent';
                    if (placement === 'left') { a.style.right = '-10px'; a.style.top = '24px'; a.style.borderLeftColor = 'white'; }
                    else if (placement === 'right') { a.style.left = '-10px'; a.style.top = '24px'; a.style.borderRightColor = 'white'; }
                    else if (placement === 'top') { a.style.bottom = '-10px'; a.style.left = '32px'; a.style.borderTopColor = 'white'; }
                    else { a.style.top = '-10px'; a.style.left = '32px'; a.style.borderBottomColor = 'white'; }
                    return a;
                }
                function show(i){
                    cleanup();
                    const s = steps[i];
                    const ov = overlay();
                    const panel = document.createElement('div');
                    panel.style.position = 'fixed';
                    panel.style.maxWidth = '380px';
                    panel.style.minWidth = '300px';
                    panel.style.padding = '18px 18px 14px';
                    panel.style.borderRadius = '16px';
                    panel.style.background = 'linear-gradient(180deg,#fff 0%,#F8FAFC 100%)';
                    panel.style.border = '1px solid rgba(148,163,184,0.28)';
                    panel.style.boxShadow = '0 24px 60px rgba(15,23,42,0.28)';
                    panel.style.zIndex = '100001';
                    panel.style.opacity = '0';
                    panel.style.transform = 'translateY(8px) scale(0.98)';
                    panel.style.transition = 'opacity 180ms ease, transform 180ms ease';
                    panel.innerHTML = '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px;"><div style="font-size:0.78rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748B;">Step ' + (i+1) + ' of ' + steps.length + '</div><button id="coach_done" style="background:transparent;border:none;font-size:18px;cursor:pointer;color:#64748B;">&times;</button></div><h3 style="margin:0 0 8px 0;font-size:1.1rem;">' + s.title + '</h3><div style="margin-top:8px;color:#334155;line-height:1.5;">' + s.text + '</div><div style="margin-top:14px;display:flex;gap:8px;justify-content:flex-end;"><button id="coach_prev" style="padding:8px 12px;border-radius:10px;border:1px solid #CBD5E1;background:#fff;">Prev</button><button id="coach_next" style="padding:8px 12px;border-radius:10px;border:1px solid #1D4ED8;background:#1D4ED8;color:#fff;">Next</button></div>';
                    panel.appendChild(arrow('right'));
                    ov.appendChild(panel);
                    var target = s.id ? document.getElementById(s.id) : null;
                    if (target) {
                        target.scrollIntoView({behavior:'smooth', block:'center', inline:'nearest'});
                        place(panel, target.getBoundingClientRect());
                        highlight(target);
                    } else {
                        panel.style.left = '50%';
                        panel.style.top = '50%';
                        panel.style.transform = 'translate(-50%, -50%) scale(0.98)';
                    }
                    requestAnimationFrame(function(){ panel.style.opacity = '1'; panel.style.transform = 'translateY(0) scale(1)'; });
                    var prevBtn = document.getElementById('coach_prev');
                    var nextBtn = document.getElementById('coach_next');
                    var doneBtn = document.getElementById('coach_done');
                    if (prevBtn) prevBtn.onclick = function(){ idx = Math.max(0, idx-1); show(idx); };
                    if (nextBtn) nextBtn.onclick = function(){ idx = Math.min(steps.length-1, idx+1); show(idx); };
                    if (doneBtn) doneBtn.onclick = function(){ cleanup(); };
                }
                show(0);
            })();
            </script>
            """ % steps_json
            st.markdown(js, unsafe_allow_html=True)
            st.markdown("<div style='margin-top:8px;'><em>Use 'Done' in the tour overlay to finish. Click 'Finish tour' below to persist it.</em></div>", unsafe_allow_html=True)
            if st.button("Finish tour and don't show again"):
                st.session_state.tour_completed = True
                try:
                    from app.state.cache import save_cached_pipeline_state
                    save_cached_pipeline_state()
                except Exception:
                    pass
                st.session_state.show_tour = False
                st.rerun()
    except Exception:
        pass
