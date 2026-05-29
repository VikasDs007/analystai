import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sys
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

# Cache file for last uploaded CSV so reloads don't lose user data
_CACHE_CSV = os.path.join(_ROOT, ".analystai_last_upload.csv")
_CACHE_STATE = os.path.join(_ROOT, ".analystai_last_state.json")
_CACHE_CLEAN_CSV = os.path.join(_ROOT, ".analystai_last_cleaned.csv")

from agents.detective import run_detective
from agents.cleaner import run_cleaner
from agents.chart_selector import (
    build_charts, get_anomalies, get_col_types,
    render_chart, CHART_TYPES, AGG_OPTIONS
)
from agents.insight_generator import run_insight_generator
from agents.storyteller import run_storyteller, handle_question
from utils.helpers import (
    compute_business_kpis, suggest_questions,
    md_to_html, col_type_badge, choose_main_numeric
)

st.set_page_config(
    page_title="AnalystAI — Data Intelligence Platform",
    page_icon="📊", layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
html,body{background:
    radial-gradient(circle at top left, rgba(59,130,246,0.08), transparent 35%),
    radial-gradient(circle at top right, rgba(168,85,247,0.08), transparent 28%),
    linear-gradient(180deg,#F8FAFC 0%,#EEF2FF 100%);
}
.main .block-container{padding:1.5rem 2.5rem 3rem;max-width:1400px;}

/* App shell */
.app-shell{background:rgba(255,255,255,0.72);backdrop-filter:blur(14px);
          border:1px solid rgba(226,232,240,0.8);border-radius:20px;
          box-shadow:0 20px 60px rgba(15,23,42,0.06);padding:1.4rem 1.6rem;margin-bottom:1.2rem;}
.app-hero{background:linear-gradient(135deg,#0F172A 0%,#1E3A8A 55%,#4F46E5 100%);
          border:1px solid rgba(147,197,253,0.2);border-radius:22px;padding:1.6rem 1.8rem;
          margin-bottom:1rem;position:relative;overflow:hidden;color:white;box-shadow:0 18px 50px rgba(15,23,42,0.16);}
.app-hero::after{content:'';position:absolute;inset:auto -120px -120px auto;width:300px;height:300px;
                background:radial-gradient(circle,rgba(255,255,255,0.16),transparent 68%);border-radius:50%;}
.hero-kicker{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.12);
             border:1px solid rgba(255,255,255,0.18);color:#E0E7FF;border-radius:999px;
             padding:4px 12px;font-size:0.72rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;}
.hero-title-xl{font-size:2.35rem;line-height:1.1;font-weight:750;margin:0.65rem 0 0.45rem;color:#FFFFFF;letter-spacing:-0.03em;}
.hero-copy{color:#C7D2FE;font-size:0.98rem;line-height:1.6;max-width:760px;margin:0;}
.hero-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:1rem;}
.hero-pill{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.16);color:#EFF6FF;
           border-radius:999px;padding:7px 14px;font-size:0.8rem;font-weight:600;}

/* Snapshot cards */
.snapshot-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin:1rem 0 1.25rem;}
.snapshot-card{background:rgba(255,255,255,0.88);border:1px solid #E2E8F0;border-radius:16px;
               padding:1rem 1.05rem;box-shadow:0 10px 24px rgba(15,23,42,0.05);
               transition:transform .2s,box-shadow .2s;}
.snapshot-card:hover{transform:translateY(-2px);box-shadow:0 16px 30px rgba(15,23,42,0.08);}
.snapshot-lbl{font-size:0.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#64748B;margin-bottom:8px;}
.snapshot-val{font-size:1.35rem;font-weight:750;line-height:1;color:#0F172A;}
.snapshot-sub{font-size:0.78rem;color:#64748B;margin-top:6px;line-height:1.4;}
.snapshot-card.primary{background:linear-gradient(180deg,#FFFFFF 0%,#F8FAFF 100%);border-color:#C7D2FE;}

.next-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:0.6rem 0 1rem;}
.next-card{background:linear-gradient(180deg,rgba(255,255,255,0.95),rgba(248,250,252,0.96));
           border:1px solid #E2E8F0;border-radius:16px;padding:1rem 1.1rem;box-shadow:0 8px 20px rgba(15,23,42,0.04);}
.next-ico{font-size:1.2rem;margin-bottom:8px;display:inline-flex;}
.next-title{font-weight:700;color:#0F172A;font-size:0.93rem;margin-bottom:4px;}
.next-desc{color:#64748B;font-size:0.82rem;line-height:1.5;}

/* Sidebar */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F172A 0%,#1E293B 100%);border-right:1px solid #334155;}
[data-testid="stSidebar"] *{color:#CBD5E1 !important;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#F1F5F9 !important;}
[data-testid="stSidebar"] hr{border-color:#334155 !important;}
.sb-logo{font-size:1.4rem;font-weight:700;color:#38BDF8 !important;letter-spacing:-0.5px;}
.sb-step{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:8px;margin:3px 0;}
.sb-step:hover{background:rgba(56,189,248,0.08);}
.sb-num{background:#1D4ED8;color:white !important;width:22px;height:22px;border-radius:50%;
        display:flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700;flex-shrink:0;}
.sb-txt{font-size:0.82rem;color:#94A3B8 !important;}

/* Hero */
.hero{background:linear-gradient(135deg,#0F172A 0%,#1E3A5F 50%,#0F172A 100%);
      border:1px solid #1E40AF;border-radius:16px;padding:2.5rem 3rem;
      margin-bottom:1.5rem;position:relative;overflow:hidden;}
.hero::before{content:'';position:absolute;top:-50%;right:-10%;width:400px;height:400px;
              background:radial-gradient(circle,rgba(56,189,248,0.12) 0%,transparent 70%);border-radius:50%;}
.hero-title{font-size:2.2rem;font-weight:700;
            background:linear-gradient(90deg,#38BDF8,#818CF8,#F472B6);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            background-clip:text;margin:0;line-height:1.2;}
.hero-sub{color:#94A3B8;font-size:1rem;margin-top:0.5rem;}
.hero-badge{display:inline-flex;align-items:center;gap:6px;
            background:rgba(56,189,248,0.1);border:1px solid rgba(56,189,248,0.3);
            color:#38BDF8 !important;border-radius:20px;padding:4px 12px;
            font-size:0.75rem;font-weight:500;margin-top:1rem;margin-right:8px;}

/* Section headers */
.sec-hdr{display:flex;align-items:center;gap:12px;margin:2.1rem 0 1rem 0;}
.sec-icon{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;
          justify-content:center;font-size:1.1rem;flex-shrink:0;}
.sec-title{font-size:1.2rem;font-weight:600;color:#1E293B;margin:0;}
.sec-line{flex:1;height:1px;background:linear-gradient(90deg,#E2E8F0,transparent);}

/* KPI cards — 6-col grid */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:1rem 0;}
.kpi-card{background:white;border-radius:12px;padding:1.1rem 1.3rem;
          border:1px solid #E2E8F0;box-shadow:0 1px 3px rgba(0,0,0,0.06);
          position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s;}
.kpi-card:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(0,0,0,0.1);}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;}
.kpi-blue::before  {background:linear-gradient(90deg,#3B82F6,#60A5FA);}
.kpi-green::before {background:linear-gradient(90deg,#10B981,#34D399);}
.kpi-purple::before{background:linear-gradient(90deg,#8B5CF6,#A78BFA);}
.kpi-amber::before {background:linear-gradient(90deg,#F59E0B,#FCD34D);}
.kpi-rose::before  {background:linear-gradient(90deg,#F43F5E,#FB7185);}
.kpi-lbl{font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:#94A3B8;margin-bottom:4px;}
.kpi-ico{font-size:1.4rem;float:right;margin-top:-2px;opacity:.7;}
.kpi-val{font-size:1.9rem;font-weight:700;color:#0F172A;line-height:1;}
.kpi-sub{font-size:0.72rem;color:#64748B;margin-top:4px;}

/* Progress steps */
.prog-bar{display:flex;align-items:center;gap:0;margin:1rem 0 1.5rem 0;
          background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:10px 16px;}
.prog-step{display:flex;align-items:center;gap:6px;font-size:0.8rem;font-weight:500;color:#94A3B8;flex:1;}
.prog-step.done{color:#10B981;}
.prog-step.active{color:#6366F1;font-weight:600;}
.prog-dot{width:8px;height:8px;border-radius:50%;background:#E2E8F0;flex-shrink:0;}
.prog-dot.done{background:#10B981;}
.prog-dot.active{background:#6366F1;box-shadow:0 0 0 3px rgba(99,102,241,0.2);}
.prog-arrow{color:#CBD5E1;margin:0 4px;font-size:0.7rem;}

/* Issue rows */
.issue-row{display:flex;align-items:center;gap:12px;padding:10px 16px;
           border-radius:8px;background:#F8FAFC;border:1px solid #E2E8F0;margin-bottom:8px;}
.badge{padding:2px 10px;border-radius:20px;font-size:0.7rem;font-weight:600;text-transform:uppercase;}
.badge-high  {background:#FEE2E2;color:#DC2626;}
.badge-medium{background:#FEF3C7;color:#D97706;}
.badge-low   {background:#DCFCE7;color:#16A34A;}

/* Clean steps */
.clean-step{display:flex;align-items:center;gap:10px;padding:9px 16px;
            border-radius:8px;background:#F0FDF4;border:1px solid #BBF7D0;
            margin-bottom:7px;font-size:0.87rem;color:#166534;}

/* Anomaly callout */
.anomaly-card{background:#FFF7ED;border:1px solid #FED7AA;border-left:4px solid #F97316;
              border-radius:10px;padding:12px 16px;margin-bottom:10px;}
.anomaly-title{font-weight:600;color:#C2410C;font-size:0.88rem;margin-bottom:4px;}
.anomaly-desc{font-size:0.82rem;color:#92400E;line-height:1.5;}

/* Chart cards */
.chart-card{background:white;border-radius:12px;border:1px solid #E2E8F0;
            box-shadow:0 1px 3px rgba(0,0,0,0.05);padding:1rem;margin-bottom:1.2rem;}
.chart-lbl{font-size:0.75rem;font-weight:600;color:#64748B;text-transform:uppercase;
           letter-spacing:.06em;margin-bottom:3px;}
.chart-desc{font-size:0.83rem;color:#94A3B8;line-height:1.5;}

/* Insight cards */
.insight-card{background:white;border-radius:12px;border:1px solid #E2E8F0;
              border-left:4px solid #6366F1;padding:1.2rem 1.4rem;
              margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}

/* Report card */
.report-card{background:linear-gradient(135deg,#F8FAFF,#F0F4FF);
             border:1px solid #C7D2FE;border-radius:12px;padding:1.8rem 2rem;margin-bottom:1rem;}

/* Suggested question chips */
.q-chip{display:inline-block;background:#EEF2FF;border:1px solid #C7D2FE;
        color:#4338CA;border-radius:20px;padding:5px 14px;font-size:0.82rem;
        font-weight:500;margin:4px;cursor:pointer;transition:all .15s;}
.q-chip:hover{background:#E0E7FF;border-color:#A5B4FC;}
.suggest-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin-top:0.75rem;}
.suggest-card{background:white;border:1px solid #E2E8F0;border-radius:14px;padding:0.85rem 0.95rem;
          box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.suggest-label{font-size:0.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#6366F1;margin-bottom:0.4rem;}
.suggest-help{font-size:0.82rem;color:#64748B;line-height:1.45;margin-bottom:0.7rem;}

/* Chat */
.chat-box{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
          padding:1.2rem;max-height:440px;overflow-y:auto;margin-bottom:1rem;}
.chat-msg{display:flex;gap:10px;margin-bottom:14px;align-items:flex-start;}
.chat-msg.user{flex-direction:row-reverse;}
.chat-av{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;
         justify-content:center;font-size:0.8rem;flex-shrink:0;font-weight:600;}
.av-u{background:#6366F1;color:white !important;}
.av-a{background:#0EA5E9;color:white !important;}
.chat-bub{max-width:78%;padding:10px 14px;border-radius:12px;font-size:0.87rem;line-height:1.55;}
.bub-u{background:#6366F1;color:white !important;border-radius:12px 2px 12px 12px;}
.bub-a{background:white;color:#1E293B !important;border:1px solid #E2E8F0;border-radius:2px 12px 12px 12px;}

/* Feature cards (welcome) */
.feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:1.5rem 0;}
.feat-card{background:white;border-radius:12px;border:1px solid #E2E8F0;
           padding:1.4rem;box-shadow:0 1px 3px rgba(0,0,0,0.05);transition:transform .2s,border-color .2s,box-shadow .2s;}
.feat-card:hover{transform:translateY(-3px);border-color:#C7D2FE;box-shadow:0 12px 26px rgba(99,102,241,0.08);}
.feat-ico{font-size:1.8rem;margin-bottom:10px;}
.feat-ttl{font-weight:600;color:#1E293B;font-size:0.95rem;margin-bottom:6px;}
.feat-dsc{font-size:0.82rem;color:#64748B;line-height:1.5;}

/* Misc */
.divider{height:1px;background:linear-gradient(90deg,transparent,#E2E8F0,transparent);margin:2rem 0;}
.footer{text-align:center;padding:1.5rem;color:#94A3B8;font-size:0.78rem;
        border-top:1px solid #E2E8F0;margin-top:3rem;}
.footer span{color:#6366F1;font-weight:600;}
div[data-testid="stMetric"]{background:white;border-radius:10px;padding:1rem;border:1px solid #E2E8F0;}
.stButton>button{border-radius:8px !important;font-weight:500 !important;transition:all .2s !important;}
div[data-testid="stExpander"]{border:1px solid #E2E8F0 !important;border-radius:10px !important;}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def section(bg, icon, title):
    st.markdown(f"""<div class="sec-hdr">
        <div class="sec-icon" style="background:{bg};">{icon}</div>
        <p class="sec-title">{title}</p>
        <div class="sec-line"></div>
    </div>""", unsafe_allow_html=True)

def render_next_steps():
    """Render a simple next-steps guidance band."""
    return (
        """
    <div class="next-grid">
        <div class="next-card">
            <div class="next-ico">🔍</div>
            <div class="next-title">Detect patterns</div>
            <div class="next-desc">Review what the model found, then jump into the cleaned data preview for the details.</div>
        </div>
        <div class="next-card">
            <div class="next-ico">📊</div>
            <div class="next-title">Compare metrics</div>
            <div class="next-desc">Use Chart Studio to create a custom view or regenerate AI-picked charts.</div>
        </div>
        <div class="next-card">
            <div class="next-ico">🤖</div>
            <div class="next-title">Ask a question</div>
            <div class="next-desc">Use the suggested prompts or type your own to get a data-backed answer.</div>
        </div>
    </div>
    """
    )


def _current_pipeline_step():
    """Return the current pipeline step index (0..5) for the sidebar.

    Steps: 0=Detective, 1=Cleaner, 2=Charts, 3=Insights, 4=Report, 5=Q&A
    The function inspects `st.session_state` keys to determine progress.
    """
    # If no detective output yet, we are at Detect
    if st.session_state.get("detective_result") is None:
        return 0
    # If cleaned data not present, show Cleaner
    if st.session_state.get("df_clean") is None:
        return 1
    # If there are no generated charts or cached specs, show Charts
    charts = st.session_state.get("charts")
    cached = st.session_state.get("cached_chart_specs")
    if (not charts) and (not cached):
        return 2
    # If insights not generated, show Insights
    if st.session_state.get("insights") is None:
        return 3
    # If report not generated, show Report
    if st.session_state.get("report") is None:
        return 4
    # Otherwise show Q&A
    return 5


def count_imputed_values(cleaning_report):
    """Estimate the number of imputed/missing values from the cleaning_report.

    The cleaning_report is expected to be a list of human-readable step strings.
    We look for integer counts followed by keywords like 'imput' or 'missing'.
    """
    import re
    if not cleaning_report:
        return 0
    total = 0
    for item in cleaning_report:
        try:
            if not isinstance(item, str):
                continue
            m = re.search(r"(\d{1,9})\s*(?:missing|imput|imputed|filled)", item, re.IGNORECASE)
            if m:
                total += int(m.group(1))
        except Exception:
            continue
    return total


def build_dataset_snapshot(df, df_clean):
    """Build a simple list of snapshot items for the top hero stat cards."""
    try:
        missing = int(df.isnull().sum().sum())
    except Exception:
        missing = 0
    items = [
        {"label": "File", "value": st.session_state.get("last_file_name") or st.session_state.get("last_file_id", "dataset"), "sub": "active source", "color": "primary"},
        {"label": "Rows", "value": f"{len(df):,}", "sub": f"{len(df.columns)} columns", "color": "primary"},
        {"label": "Cleaned Rows", "value": f"{len(df_clean):,}", "sub": "after cleaning", "color": ""},
        {"label": "Missing", "value": f"{missing:,}", "sub": "total nulls", "color": ""},
    ]
    return items


def render_stat_cards(items):
    """Render snapshot items into HTML grid for `st.markdown`."""
    html = '<div class="snapshot-grid">'
    for it in items:
        cls = "snapshot-card primary" if it.get("color") == "primary" else "snapshot-card"
        html += f"<div class=\"{cls}\">"
        html += f"<div class=\"snapshot-lbl\">{it.get('label')}</div>"
        html += f"<div class=\"snapshot-val\">{it.get('value')}</div>"
        html += f"<div class=\"snapshot-sub\">{it.get('sub','')}</div>"
        html += "</div>"
    html += "</div>"
    return html


def progress_bar(step_index):
    """Render a simple progress bar indicating pipeline step progress."""
    try:
        steps = ["Detective", "Cleaner", "Charts", "Insights", "Report", "Q&A"]
        html = '<div class="prog-bar">'
        for i, label in enumerate(steps):
            cls = 'prog-step'
            if i < step_index:
                cls += ' done'
            elif i == step_index:
                cls += ' active'
            html += f'<div class="{cls}"><span class="prog-dot"></span>{label}</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    except Exception:
        # Fail silently if rendering errors occur
        pass


def try_rerun():
    """Rerun the Streamlit app across versions."""
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
        return
    legacy = getattr(st, "experimental_rerun", None)
    if callable(legacy):
        legacy()


def create_download_pack_bytes():
    """Create an in-memory zip containing report, cleaned CSV, and chart specs.

    Returns bytes suitable for `st.download_button`.
    """
    import io
    import zipfile

    bio = io.BytesIO()
    try:
        with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
            # analysis report
            report = st.session_state.get("report") or ""
            z.writestr("analysis_report.md", report)

            # cleaned data
            df_clean = st.session_state.get("df_clean")
            if df_clean is not None:
                try:
                    csv_bytes = df_clean.to_csv(index=False).encode("utf-8")
                    z.writestr("cleaned_data.csv", csv_bytes)
                except Exception:
                    # skip if conversion fails
                    pass

            # chart specs / cached specs
            specs = st.session_state.get("cached_chart_specs") or st.session_state.get("charts") or []
            try:
                z.writestr("chart_specs.json", json.dumps(specs, ensure_ascii=False, indent=2))
            except Exception:
                pass
    except Exception:
        return b""
    bio.seek(0)
    return bio.read()

def render_data_in_use(df, df_clean):
        """Render a compact 'Data In Use' panel showing filename, counts, filters, and columns."""
        file_name = st.session_state.get("last_file_name") or st.session_state.get("last_file_id", "(in-memory)")
        filters = st.session_state.get("filters") or {}
        filters_txt = "None"
        if filters:
                parts = [f"{k}: {', '.join(map(str,v))}" for k, v in filters.items() if v]
                filters_txt = ", ".join(parts) if parts else "None"

        col_list = list(df.columns[:24])
        chips_html = ""
        for c in col_list:
                chips_html += f"<span style=\"background:#FFF; border:1px solid #E6EEF9; padding:6px 8px; border-radius:10px; margin:4px; font-size:0.82rem;\">{c}</span>"

        html = f"""
        <div style="display:flex;gap:18px;align-items:flex-start;margin:12px 0;">
            <div style="flex:1;min-width:260px;background:linear-gradient(180deg,#FFFFFF,#FBFCFF);border:1px solid #E8F0FF;padding:12px;border-radius:12px;">
                <div style="font-weight:700;color:#0F172A;margin-bottom:6px;">Current dataset</div>
                <div style="color:#334155;font-size:0.95rem;margin-bottom:6px;"><strong>File:</strong> {file_name}</div>
                <div style="color:#64748B;font-size:0.9rem;">Rows: <strong>{len(df):,}</strong> · Columns: <strong>{len(df.columns):,}</strong></div>
                <div style="color:#64748B;font-size:0.9rem;margin-top:6px;">Cleaned rows: <strong>{len(df_clean):,}</strong></div>
                <div style="color:#64748B;font-size:0.9rem;margin-top:8px;"><strong>Active filters:</strong> {filters_txt}</div>
            </div>
            <div style="flex:2;min-width:360px;background:#FFFFFF;border:1px solid #E8F0FF;padding:12px;border-radius:12px;">
                <div style="font-weight:700;color:#0F172A;margin-bottom:6px;">Columns (showing up to 24)</div>
                <div style="display:flex;flex-wrap:wrap;">{chips_html}</div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


def _fmt_chart_value(value):
    """Format numeric values for chart explanations."""
    try:
        val = float(value)
        if abs(val) >= 1000000:
            return f"{val/1000000:.2f}M"
        if abs(val) >= 1000:
            return f"{val:,.0f}"
        return f"{val:.2f}"
    except Exception:
        return str(value)


def build_chart_explanation(df, spec, fallback_text=""):
    """Return a plain-language explanation for non-technical users."""
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
                return f"This chart compares {y.replace('_', ' ')} across {x.replace('_', ' ')}."
            grouped = data.groupby(x)[y]
            grouped = grouped.agg(agg if agg != "none" else "sum").sort_values(ascending=False)
            if grouped.empty:
                return f"This chart compares {y.replace('_', ' ')} across {x.replace('_', ' ')}."
            top_label = grouped.index[0]
            top_value = _fmt_chart_value(grouped.iloc[0])
            return (
                f"This chart compares {y.replace('_', ' ')} across {x.replace('_', ' ')}. "
                f"{top_label} is currently the highest at about {top_value}."
            )

        if chart_type == "grouped_bar" and x and isinstance(y, list) and len(y) >= 2 and x in df.columns:
            y_cols = [col for col in y if col in df.columns]
            if len(y_cols) >= 2:
                data = df[[x] + y_cols].dropna()
                if not data.empty:
                    grouped = data.groupby(x)[y_cols].agg(agg if agg != "none" else "sum")
                    top_label = grouped[y_cols[0]].sort_values(ascending=False).index[0]
                    return (
                        f"This chart compares {y_cols[0].replace('_', ' ')} and {y_cols[1].replace('_', ' ')} "
                        f"for each {x.replace('_', ' ')}. {top_label} stands out most in the first metric."
                    )

        if chart_type in ("line", "area") and x and y and x in df.columns and y in df.columns:
            tmp = df[[x, y]].dropna().copy()
            tmp[x] = pd.to_datetime(tmp[x], errors="coerce")
            tmp = tmp.dropna(subset=[x]).sort_values(x)
            if len(tmp) >= 2:
                start_val = float(tmp[y].iloc[0])
                end_val = float(tmp[y].iloc[-1])
                direction = "up" if end_val >= start_val else "down"
                return (
                    f"This chart shows how {y.replace('_', ' ')} changes over time. "
                    f"The latest value is {direction} compared with the starting period."
                )

        if chart_type in ("histogram", "box"):
            col = x if x in df.columns else y if isinstance(y, str) and y in df.columns else None
            if col:
                series = pd.to_numeric(df[col], errors="coerce").dropna()
                if not series.empty:
                    median = _fmt_chart_value(series.median())
                    return (
                        f"This chart shows how {col.replace('_', ' ')} is distributed. "
                        f"Most values are centered around {median}."
                    )

        if chart_type == "scatter" and x and y and x in df.columns and y in df.columns:
            data = df[[x, y]].dropna()
            if len(data) >= 3:
                corr = data[x].corr(data[y])
                if pd.notna(corr):
                    strength = "strong" if abs(corr) >= 0.6 else "moderate" if abs(corr) >= 0.3 else "weak"
                    direction = "positive" if corr >= 0 else "negative"
                    return (
                        f"This chart checks whether {x.replace('_', ' ')} and {y.replace('_', ' ')} move together. "
                        f"It shows a {strength} {direction} relationship."
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
                        f"This chart shows which metrics are most related. "
                        f"The strongest link is between {top_pair[0].replace('_', ' ')} and {top_pair[1].replace('_', ' ')} "
                        f"(correlation {top_val:.2f})."
                    )
    except Exception:
        pass

    if fallback_text:
        return fallback_text
    return "This chart highlights a key pattern in the dataset to support faster decision-making."


def build_chart_actions(spec):
    """Return dataset-agnostic next actions based on chart type."""
    chart_type = (spec or {}).get("chart_type", "")

    base_actions = [
        "Validate outliers with the source team before taking action.",
        "Filter by key segments to check whether this pattern is consistent.",
        "Track this metric weekly to see whether the trend is improving.",
    ]

    action_map = {
        "bar": [
            "Review the top and bottom categories to identify what drives the gap.",
            "Prioritize one low-performing category for a focused improvement experiment.",
            "Compare this view with another dimension (time or segment) before deciding.",
        ],
        "grouped_bar": [
            "Identify categories where one metric is high but another metric is weak.",
            "Set one balancing target so both metrics improve together.",
            "Investigate categories with the largest metric spread first.",
        ],
        "line": [
            "Check recent periods where the direction changed and investigate the cause.",
            "Set an alert threshold for sudden drops or spikes.",
            "Use moving averages to reduce noise before decisions.",
        ],
        "area": [
            "Check if cumulative growth is stable or concentrated in a few periods.",
            "Break down the latest period to find which segment contributed most.",
            "Set a near-term target based on recent trend speed.",
        ],
        "scatter": [
            "Review points that are far from the pattern; they may indicate process issues.",
            "Test whether the relationship changes by segment or timeframe.",
            "Avoid causal assumptions; validate with additional context before action.",
        ],
        "histogram": [
            "Use the distribution to define realistic benchmark ranges.",
            "Investigate extreme tails to reduce risk or inconsistency.",
            "Split distribution by segment to detect hidden sub-patterns.",
        ],
        "box": [
            "Focus on categories with the widest spread to improve consistency.",
            "Investigate outliers before using averages for planning.",
            "Use median and quartiles for target setting in skewed data.",
        ],
        "pie": [
            "Focus on the largest slices first to maximize impact.",
            "Investigate whether small slices are strategic or noise.",
            "Recheck this split over time to detect concentration risk.",
        ],
        "heatmap": [
            "Use strong relationships to choose candidate drivers for deeper analysis.",
            "Watch for highly similar metrics and avoid duplicate tracking.",
            "Validate surprising links with domain owners before changing strategy.",
        ],
    }

    return action_map.get(chart_type, base_actions)


def render_possible_actions(spec):
    """Render possible actions under each chart for non-technical users."""
    actions = build_chart_actions(spec)
    if not actions:
        return
    html = '<p class="chart-desc" style="margin-top:6px;"><strong>Possible actions:</strong></p><ul style="margin-top:0;padding-left:18px;color:#64748B;font-size:0.83rem;line-height:1.55;">'
    for item in actions[:3]:
        html += f"<li>{item}</li>"
    html += "</ul>"
    st.markdown(html, unsafe_allow_html=True)

def render_ai_chart_card(chart, chart_index, df_source, all_columns):
    """Render an AI-selected chart plus a small tweak expander."""
    spec = chart.get("spec", {})
    st.plotly_chart(chart["fig"], width="stretch", key=f"ai_chart_{chart_index}")
    st.markdown(f'<p class="chart-lbl">{chart["title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="chart-desc">{chart["plain"]}</p>', unsafe_allow_html=True)
    explainer = build_chart_explanation(df_source, spec, fallback_text=chart.get("plain", ""))
    st.markdown(f'<p class="chart-desc"><strong>What this chart tells you:</strong> {explainer}</p>', unsafe_allow_html=True)
    render_possible_actions(spec)
    st.markdown(
        f'<p style="font-size:0.72rem;color:#C7D2FE;margin-top:4px;">'
        f'type={spec.get("chart_type","")} · x={spec.get("x","—")} · '
        f'y={spec.get("y","—")} · agg={spec.get("agg","—")}</p>',
        unsafe_allow_html=True,
    )

    with st.expander("📊 Tweak this chart", expanded=False):
        axis_options = ["— keep current —"] + list(all_columns)
        current_x = spec.get("x") if spec.get("x") in all_columns else None
        current_y = spec.get("y")
        if isinstance(current_y, list):
            current_y = next((value for value in current_y if value in all_columns), None)
        elif current_y not in all_columns:
            current_y = None

        x_index = axis_options.index(current_x) if current_x in axis_options else 0
        y_index = axis_options.index(current_y) if current_y in axis_options else 0

        tweak_x = st.selectbox(
            "Override X Axis",
            axis_options,
            index=x_index,
            key=f"tweak_x_{chart_index}",
        )
        tweak_y = st.selectbox(
            "Override Y Axis",
            axis_options,
            index=y_index,
            key=f"tweak_y_{chart_index}",
        )

        tweaked_spec = dict(spec)
        if tweak_x != "— keep current —":
            tweaked_spec["x"] = tweak_x
        if tweak_y != "— keep current —":
            if isinstance(tweaked_spec.get("y"), list):
                y_values = list(tweaked_spec.get("y") or [])
                if y_values:
                    y_values[0] = tweak_y
                    tweaked_spec["y"] = y_values
                else:
                    tweaked_spec["y"] = tweak_y
            else:
                tweaked_spec["y"] = tweak_y

        tweaked = render_chart(df_source, tweaked_spec)
        if tweaked:
            st.plotly_chart(tweaked["fig"], width="stretch", key=f"ai_chart_tweak_{chart_index}")
        else:
            st.caption("Choose valid axes to preview the tweaked chart.")

def _load_cached_pipeline_state():
    """Restore the first generated pipeline outputs from disk if available."""
    if not os.path.exists(_CACHE_STATE):
        return
    try:
        with open(_CACHE_STATE, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if payload.get("detective_result"):
            st.session_state.detective_result = payload["detective_result"]
        if payload.get("cleaning_report"):
            st.session_state.cleaning_report = payload["cleaning_report"]
        if payload.get("anomalies") is not None:
            st.session_state.anomalies = payload["anomalies"]
        if payload.get("chart_specs"):
            st.session_state.cached_chart_specs = payload["chart_specs"]
        if payload.get("insights"):
            st.session_state.insights = payload["insights"]
        if payload.get("report"):
            st.session_state.report = payload["report"]
        if payload.get("last_file_id"):
            st.session_state.last_file_id = payload.get("last_file_id")
        if payload.get("last_file_name"):
            st.session_state.last_file_name = payload.get("last_file_name")
        if os.path.exists(_CACHE_CLEAN_CSV):
            st.session_state.df_clean = pd.read_csv(_CACHE_CLEAN_CSV)
    except Exception:
        pass


def _save_cached_pipeline_state():
    """Persist the generated outputs so refreshes reuse the first result."""
    payload = {
        "detective_result": st.session_state.get("detective_result"),
        "cleaning_report": st.session_state.get("cleaning_report"),
        "anomalies": st.session_state.get("anomalies"),
        "chart_specs": st.session_state.get("cached_chart_specs"),
        "insights": st.session_state.get("insights"),
        "report": st.session_state.get("report"),
        "last_file_id": st.session_state.get("last_file_id"),
        "last_file_name": st.session_state.get("last_file_name"),
    }
    try:
        with open(_CACHE_STATE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _clear_cached_pipeline_state():
    """Remove persisted generated outputs."""
    for path in [_CACHE_STATE, _CACHE_CLEAN_CSV]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

# ── Session state ─────────────────────────────────────────────────────────────
for k in ["df_raw","df_clean","detective_result","cleaning_report",
          "charts","insights","report","qa_history","last_file_id","last_file_name",
          "filters","anomalies","custom_charts","onboarding_seen",
          "cached_chart_specs","qa_question_input","clear_qa_question_input",
          "skip_cache_reload"]:
    if k not in st.session_state:
        st.session_state[k] = None
if not st.session_state.qa_history:
    st.session_state.qa_history = []
if not st.session_state.filters:
    st.session_state.filters = {}

if st.session_state.get("clear_qa_question_input"):
    st.session_state.qa_question_input = ""
    st.session_state.clear_qa_question_input = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sb-logo">📊 AnalystAI</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748B;font-size:0.78rem;margin-top:-8px;">Data Intelligence Platform</p>', unsafe_allow_html=True)
    st.markdown("---")

    steps_info = [("🔍","Detective","Understands your data"),("🧹","Cleaner","Fixes quality issues"),
                  ("📊","Charts","Visualises patterns"),("💡","Insights","Explains findings"),
                  ("📖","Report","Business summary"),("🤖","Q&A","Answers questions")]
    st.markdown('<p style="font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:6px;">PIPELINE</p>', unsafe_allow_html=True)
    step_index = _current_pipeline_step()
    for i,(ico,nm,dsc) in enumerate(steps_info,1):
        active = " sb-active" if (i-1) == step_index else ""
        st.markdown(f"""<div class="sb-step{active}">
            <div class="sb-num">{i}</div>
            <div><div style="font-size:0.84rem;font-weight:500;color:#E2E8F0;">{ico} {nm}</div>
            <div class="sb-txt">{dsc}</div></div></div>""", unsafe_allow_html=True)

    # ── Filters (shown only when data is loaded) ──────────────────────────────
    if st.session_state.df_clean is not None:
        st.markdown("---")
        st.markdown('<p style="font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:6px;">🔽 FILTERS</p>', unsafe_allow_html=True)
        df_c = st.session_state.df_clean
        _, cat_cols, _ = get_col_types(df_c)
        new_filters = {}
        for col in cat_cols[:4]:
            opts = sorted(df_c[col].dropna().unique().tolist())
            sel = st.multiselect(col.replace("_"," ").title(), opts,
                                 default=st.session_state.filters.get(col, []),
                                 key=f"filter_{col}")
            if sel:
                new_filters[col] = sel
        if new_filters != st.session_state.filters:
            st.session_state.filters = new_filters
            # Invalidate charts/insights/report when filters change
            for k in ["charts","insights","report"]:
                st.session_state[k] = None

    st.markdown("---")
    for tip in ["CSV files work best","Keep headers in row 1","Name date cols with 'date'","Remove currency symbols"]:
        st.markdown(f'<p style="font-size:0.79rem;color:#64748B;padding:2px 0;">• {tip}</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<p style="font-size:0.72rem;color:#475569;text-align:center;">Created by OpenAI Codex</p>', unsafe_allow_html=True)

    # Controls: Restart + Download Pack
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Restart Analysis"):
            keys = ["df_raw","df_clean","detective_result","charts","insights","report","qa_history","last_file_name","filters","cached_chart_specs"]
            for k in keys:
                if k in st.session_state:
                    del st.session_state[k]
            try_rerun()
    with col2:
        report = st.session_state.get("report")
        df_clean_state = st.session_state.get("df_clean")
        cached_specs = st.session_state.get("cached_chart_specs")
        has_artifacts = (
            (report is not None and report != "")
            or (df_clean_state is not None)
            or (cached_specs is not None)
        )
        data = create_download_pack_bytes() if has_artifacts else b""
        st.download_button("Download Pack", data=data, file_name="analystai_pack.zip", disabled=not has_artifacts)
    # Help / Onboarding
    with st.expander("❓ Help & Onboarding", expanded=False):
        st.markdown("""
        - Upload a CSV or click **Sample Data** to get started.
        - Pipeline: Detect → Clean → Charts → Insights → Report → Q&A.
        - Use the **Chart Studio** to build custom charts and pin them to the report.
        - For issues or to re-run the guided tour, click **Show Onboarding** below.
        """)
        if st.button("Show Onboarding"):
            # mark as not seen so onboarding appears on next run
            st.session_state.onboarding_seen = None

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""<div class="hero">
    <div class="hero-title">Data Intelligence, Simplified</div>
    <div class="hero-sub">Upload your CSV · Get instant insights · Ask questions in plain English</div>
    <div style="margin-top:1rem;">
        <span class="hero-badge">⚡ Created by OpenAI Codex</span>
        <span class="hero-badge">📊 Auto-Visualisation</span>
        <span class="hero-badge">🔽 Live Filters</span>
        <span class="hero-badge">🤖 AI Q&amp;A</span>
    </div>
</div>""", unsafe_allow_html=True)

# ── Onboarding (persisted for new users) ──────────────────────────────────────
_ONBOARD_FLAG = os.path.join(_ROOT, ".analystai_onboarded")
if not st.session_state.get("onboarding_seen"):
    try:
        if os.path.exists(_ONBOARD_FLAG):
            st.session_state.onboarding_seen = True
        else:
            try:
                with st.modal("Welcome to AnalystAI", key="onboard_modal"):
                    st.markdown("""
                    ### Welcome 🎉
                    AnalystAI helps you analyse CSVs, clean data, build charts, and ask questions.

                    Quick tour:
                    - Upload a CSV or click **Sample Data** to start.
                    - The app will detect issues, auto-clean, and propose charts.
                    - Use **Chart Studio** to customize charts and **Ask Your Data** for Q&A.

                    Click **Got it** to continue — this message will not appear again on this machine.
                    """)
                    if st.button("Got it — start analyzing"):
                        try:
                            open(_ONBOARD_FLAG, "w").write("onboarded")
                        except Exception:
                            pass
                        st.session_state.onboarding_seen = True
                        try_rerun()
            except Exception:
                with st.expander("Welcome to AnalystAI — Quick Tour", expanded=True):
                    st.markdown("""
                    - Upload a CSV or click **Sample Data** to start.
                    - The app analyses, cleans and visualises your data.
                    - Use **Chart Studio** to customize charts and **Ask Your Data** for Q&A.
                    """)
                    if st.button("Got it — start analyzing (expander)"):
                        try:
                            open(_ONBOARD_FLAG, "w").write("onboarded")
                        except Exception:
                            pass
                        st.session_state.onboarding_seen = True
                        try_rerun()
    except Exception:
        st.session_state.onboarding_seen = True

# ── Upload ────────────────────────────────────────────────────────────────────
up_col, btn_col = st.columns([4,1])
with up_col:
    uploaded_file = st.file_uploader("CSV", type=["csv"],
                                     label_visibility="collapsed",
                                     help="Upload any CSV file",
                                     key="csv_uploader")

    if st.session_state.get("df_raw") is None and uploaded_file is None and not st.session_state.get("skip_cache_reload"):
        try:
            if os.path.exists(_CACHE_CSV):
                df_cached = pd.read_csv(_CACHE_CSV)
                st.session_state.df_raw = df_cached
                st.session_state.last_file_id = "cached"
                st.session_state.last_file_name = "Cached upload"
                _load_cached_pipeline_state()
        except Exception:
            # ignore cache load errors
            pass

    if st.session_state.get("df_raw") is not None and uploaded_file is None:
        # display current loaded file info and a manual remove control
        file_name = st.session_state.get("last_file_name") or "(in-memory)"
        st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin:6px 0 10px 0;">'
                    f'<div style="flex:1;color:#0F172A;font-weight:600;">Loaded: {file_name}</div>'
                    f'</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("Remove File"):
                # clear dataset and generated artifacts
                keys = ["df_raw","df_clean","detective_result","cleaning_report",
                        "charts","insights","report","qa_history","last_file_id","last_file_name",
                        "filters","cached_chart_specs"]
                for k in keys:
                    if k in st.session_state:
                        del st.session_state[k]
                if "csv_uploader" in st.session_state:
                    del st.session_state["csv_uploader"]
                st.session_state.skip_cache_reload = True
                _clear_cached_pipeline_state()
                try_rerun()

with btn_col:
    if st.button("Load sample data"):
        try:
            sample_path = os.path.join(_ROOT, "sample_data", "sample_sales.csv")
            df_sample = pd.read_csv(sample_path)
            st.session_state.df_raw = df_sample
            st.session_state.last_file_id = "sample"
            st.session_state.last_file_name = "sample_sales.csv"
            st.session_state.skip_cache_reload = False
            _save_cached_pipeline_state()
            try_rerun()
        except Exception as e:
            st.error(f"Failed to load sample data: {e}")

    if st.session_state.get("skip_cache_reload") and st.session_state.get("df_raw") is None:
        st.session_state.skip_cache_reload = False
    

# Ensure a local `df` variable is available (from uploader or cached session)
df = None
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state.df_raw = df
        # record filename when available
        try:
            st.session_state.last_file_name = uploaded_file.name
        except Exception:
            st.session_state.last_file_name = st.session_state.get("last_file_name", "uploaded.csv")
        st.session_state.last_file_id = "uploaded"
        try:
            df.to_csv(_CACHE_CSV, index=False)
        except Exception:
            pass
        _save_cached_pipeline_state()
    except Exception as e:
        st.error(f"Failed to read uploaded CSV: {e}")
elif st.session_state.get("df_raw") is not None:
    df = st.session_state.get("df_raw")

# ══════════════════════════════════════════════════════════════════════════════
if df is not None:
    # ── Step 1 and 2 logs are progressively disclosed ────────────────────────
    if st.session_state.detective_result is None:
        with st.spinner("🔍  Analysing your data…"):
            st.session_state.detective_result = run_detective(df)

    res           = st.session_state.detective_result
    understanding = res["understanding"]
    issues        = res["issues"]
    profile       = res["profile"]

    if st.session_state.df_clean is None:
        with st.spinner("🧹  Cleaning data…"):
            df_clean, cleaning_report = run_cleaner(df, issues)
            st.session_state.df_clean = df_clean
            st.session_state.cleaning_report = cleaning_report
            try:
                df_clean.to_csv(_CACHE_CLEAN_CSV, index=False)
            except Exception:
                pass
            _save_cached_pipeline_state()

    df_clean        = st.session_state.df_clean
    cleaning_report = st.session_state.cleaning_report

    original_rows = len(df)
    duplicates_dropped = max(original_rows - len(df_clean), 0)
    values_imputed = count_imputed_values(cleaning_report)

    # Top dashboard hero
    st.markdown(f"""
    <div class="app-hero">
        <div class="hero-kicker">AnalystAI workspace</div>
        <div class="hero-title-xl">A cleaner, faster way to explore your CSV.</div>
        <p class="hero-copy">
            Your dataset is loaded and ready. Review the snapshot below, inspect quality issues,
            build charts, and ask questions without leaving the analysis flow.
        </p>
        <div class="hero-actions">
            <span class="hero-pill">File: {st.session_state.get('last_file_name') or st.session_state.get('last_file_id', 'dataset')}</span>
            <span class="hero-pill">{st.session_state.get('last_file_id', 'dataset')}</span>
            <span class="hero-pill">{len(df):,} rows</span>
            <span class="hero-pill">{len(df.columns):,} columns</span>
            <span class="hero-pill">Powered by Groq</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(render_stat_cards(build_dataset_snapshot(df, df_clean)), unsafe_allow_html=True)
    st.markdown(render_next_steps(), unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    section("#EFF6FF","🗂️","Data In Use")
    render_data_in_use(df, df_clean)

    with st.expander("🕵️‍♂️ View Data Processing Logs", expanded=False):
        with st.expander("🗂️  Raw Data Preview", expanded=False):
            st.dataframe(df, width="stretch", height=220)
            st.caption(f"{len(df):,} rows × {len(df.columns)} columns")

        progress_bar(0)
        section("#EFF6FF","🕵️","Data Overview")

        # AI understanding
        st.markdown(f"""<div style="background:linear-gradient(135deg,#EFF6FF,#F0F9FF);
            border:1px solid #BFDBFE;border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;">
            <p style="font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;
                      color:#3B82F6;margin-bottom:6px;">🤖 AI UNDERSTANDING</p>
            <p style="color:#1E293B;font-size:0.95rem;line-height:1.6;margin:0;">{understanding}</p>
        </div>""", unsafe_allow_html=True)

        # Column details with type badges
        with st.expander("🔬  Column Details", expanded=False):
            col_rows = []
            for col, info in profile["column_details"].items():
                row = {
                    "Column": col,
                    "Type Badge": col_type_badge(info["dtype"], col),
                    "Raw Type": info["dtype"],
                    "Missing": f"{info['missing']} ({info['missing_pct']}%)",
                    "Unique": info["unique"],
                    "Sample": str(info["sample"][:2]),
                }
                if "mean" in info:
                    row["Mean"] = f"{info['mean']:,}"
                    row["Min"]  = f"{info['min']:,}"
                    row["Max"]  = f"{info['max']:,}"
                col_rows.append(row)
            badge_html = "<table style='width:100%;border-collapse:collapse;font-size:0.85rem;'>"
            badge_html += "<tr style='background:#F8FAFC;'>"
            for h in ["Column","Type","Missing","Unique","Sample","Mean","Min","Max"]:
                badge_html += f"<th style='padding:8px 12px;text-align:left;border-bottom:1px solid #E2E8F0;color:#64748B;font-weight:600;font-size:0.75rem;text-transform:uppercase;'>{h}</th>"
            badge_html += "</tr>"
            for row in col_rows:
                badge_html += "<tr style='border-bottom:1px solid #F1F5F9;'>"
                badge_html += f"<td style='padding:8px 12px;font-weight:500;color:#1E293B;'>{row['Column']}</td>"
                badge_html += f"<td style='padding:8px 12px;'>{row['Type Badge']}</td>"
                badge_html += f"<td style='padding:8px 12px;color:#64748B;'>{row['Missing']}</td>"
                badge_html += f"<td style='padding:8px 12px;color:#64748B;'>{row['Unique']}</td>"
                badge_html += f"<td style='padding:8px 12px;color:#94A3B8;font-size:0.8rem;'>{row['Sample']}</td>"
                for k in ["Mean","Min","Max"]:
                    badge_html += f"<td style='padding:8px 12px;color:#64748B;'>{row.get(k,'—')}</td>"
                badge_html += "</tr>"
            badge_html += "</table>"
            st.markdown(badge_html, unsafe_allow_html=True)

        progress_bar(1)
        section("#FFF7ED","🚨","Data Quality")

        high = [i for i in issues if "High"   in i["severity"]]
        med  = [i for i in issues if "Medium" in i["severity"]]
        low  = [i for i in issues if "Low"    in i["severity"]]
        pill = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:1rem;">'
        if high: pill += f'<span style="background:#FEE2E2;color:#DC2626;padding:4px 14px;border-radius:20px;font-size:0.8rem;font-weight:600;">🔴 {len(high)} High</span>'
        if med:  pill += f'<span style="background:#FEF3C7;color:#D97706;padding:4px 14px;border-radius:20px;font-size:0.8rem;font-weight:600;">🟡 {len(med)} Medium</span>'
        if low:  pill += f'<span style="background:#DCFCE7;color:#16A34A;padding:4px 14px;border-radius:20px;font-size:0.8rem;font-weight:600;">🟢 {len(low)} Low</span>'
        pill += '</div>'
        st.markdown(pill, unsafe_allow_html=True)

        bmap = {"High":"badge-high","Medium":"badge-medium","Low":"badge-low"}
        for iss in issues:
            sk = next((k for k in bmap if k in iss["severity"]),"Low")
            st.markdown(f"""<div class="issue-row">
                <span class="badge {bmap[sk]}">{sk}</span>
                <span style="font-weight:600;color:#1E293B;font-size:0.88rem;">{iss['type'].replace('_',' ').title()}</span>
                <span style="color:#64748B;font-size:0.85rem;">in</span>
                <code style="background:#F1F5F9;padding:2px 8px;border-radius:4px;font-size:0.82rem;color:#6366F1;">{iss['column']}</code>
                <span style="color:#64748B;font-size:0.85rem;">— {iss['count']:,} rows ({iss['pct']}%)</span>
                <span style="margin-left:auto;font-size:0.78rem;color:#94A3B8;">Fix: {iss['fix']}</span>
            </div>""", unsafe_allow_html=True)

        section("#F0FDF4","🧹","Data Cleaning")
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        metrics_col1.metric("Original Rows", f"{original_rows:,}")
        metrics_col2.metric("Duplicates Dropped", f"{duplicates_dropped:,}")
        metrics_col3.metric("Values Imputed", f"{values_imputed:,}")

        for step in cleaning_report:
            st.markdown(f'<div class="clean-step">✅ {step.replace("✅","").strip()}</div>',
                        unsafe_allow_html=True)
        delta = len(df) - len(df_clean)
        st.markdown(f"""<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;
            padding:12px 18px;margin-top:8px;display:flex;align-items:center;gap:12px;">
            <span style="font-size:1.2rem;">📉</span>
            <span style="color:#166534;font-weight:500;">
                {len(df):,} rows → <strong>{len(df_clean):,} rows</strong>
                {"  ·  " + str(delta) + " duplicate rows removed" if delta > 0 else "  ·  no rows removed"}
            </span></div>""", unsafe_allow_html=True)

        with st.expander("✅  Cleaned Data Preview", expanded=False):
            st.dataframe(df_clean, width="stretch", height=220)
            st.download_button("⬇️  Download Cleaned CSV",
                               data=df_clean.to_csv(index=False).encode("utf-8"),
                               file_name="cleaned_data.csv", mime="text/csv",
                               width="stretch")
    # Apply sidebar filters
    df_view = df_clean.copy()
    for col, vals in st.session_state.filters.items():
        if col in df_view.columns and vals:
            df_view = df_view[df_view[col].isin(vals)]

    kpis = compute_business_kpis(df_view)
    kpi_html = '<div class="kpi-grid">'
    for k in kpis:
        kpi_html += f"""<div class="kpi-card {k['color']}">
            <div class="kpi-lbl">{k['label']}<span class="kpi-ico">{k['icon']}</span></div>
            <div class="kpi-val">{k['value']}</div>
            <div class="kpi-sub">{k['sub']}</div>
        </div>"""
    kpi_html += '</div>'
    st.markdown(kpi_html, unsafe_allow_html=True)

    if st.session_state.filters:
        active = ", ".join(f"{c}: {v}" for c,v in st.session_state.filters.items())
        st.caption(f"🔽 Filters active: {active} — showing {len(df_view):,} of {len(df_clean):,} rows")

    # ── Step 2: Data Quality and cleaning are inside the logs panel ──────────

    # ── Anomaly callouts ──────────────────────────────────────────────────────
    if st.session_state.anomalies is None:
        st.session_state.anomalies = get_anomalies(df_clean)
    anomalies = st.session_state.anomalies
    if anomalies:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        section("#FFF7ED","⚠️","Anomaly Alerts")
        desc_map = {
            ("discount_pct","profit"): "Higher discounts are associated with lower profit. Consider reviewing your discount strategy.",
            ("discount_pct","total_sales"): "Discounts don't appear to be driving proportionally higher sales volume.",
        }
        for c1, c2, val in anomalies:
            pair = tuple(sorted([c1,c2]))
            desc = desc_map.get(pair, f"When {c1.replace('_',' ')} increases, {c2.replace('_',' ')} tends to decrease. Worth investigating.")
            strength = "Strong" if val < -0.4 else "Moderate"
            st.markdown(f"""<div class="anomaly-card">
                <div class="anomaly-title">⚠️ {strength} Negative Correlation: {c1.replace('_',' ').title()} ↔ {c2.replace('_',' ').title()} ({val})</div>
                <div class="anomaly-desc">{desc}</div>
            </div>""", unsafe_allow_html=True)

    # ── Step 3: Charts ────────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    progress_bar(2)
    section("#F5F3FF","📊","Visual Analysis")

    # Add Chart Studio CSS once
    st.markdown("""
    <style>
    .studio-card{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1rem;}
    .studio-title{font-size:0.85rem;font-weight:600;color:#1E293B;margin-bottom:0.8rem;display:flex;align-items:center;gap:8px;}
    .llm-badge{background:linear-gradient(90deg,#6366F1,#8B5CF6);color:white;padding:2px 10px;
               border-radius:20px;font-size:0.7rem;font-weight:600;letter-spacing:.04em;}
    .manual-badge{background:#F0FDF4;border:1px solid #BBF7D0;color:#16A34A;padding:2px 10px;
                  border-radius:20px;font-size:0.7rem;font-weight:600;}
    .chart-remove{float:right;background:#FEE2E2;color:#DC2626;border:none;border-radius:6px;
                  padding:2px 8px;font-size:0.75rem;cursor:pointer;font-weight:600;}
    </style>
    """, unsafe_allow_html=True)

    # ── LLM-generated charts ──────────────────────────────────────────────────
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
            with st.spinner("🤖  AI is choosing the best charts for your data…"):
                try:
                    st.session_state.charts = build_charts(df_view, understanding)
                    st.session_state.cached_chart_specs = [
                        chart.get("spec") for chart in (st.session_state.charts or [])
                        if chart.get("spec")
                    ]
                    _save_cached_pipeline_state()
                except Exception as e:
                    st.session_state.charts = []
                    st.warning(f"Chart error: {e}")

    # Regenerate button
    regen_col, info_col = st.columns([1, 4])
    with regen_col:
        if st.button("🔄  Regenerate Charts", width="stretch",
                     help="Ask the AI to re-pick charts"):
            st.session_state.charts = None
            st.rerun()
    with info_col:
        st.markdown('<p style="color:#64748B;font-size:0.83rem;padding-top:8px;">Charts are selected by AI based on your data structure and correlations. Use the Chart Studio below to add or customise.</p>', unsafe_allow_html=True)

    charts = st.session_state.charts or []
    all_cols = df_view.columns.tolist()

    # Render AI charts
    if charts:
        st.markdown('<div style="margin-bottom:0.5rem;"><span class="llm-badge">🤖 AI Selected</span></div>', unsafe_allow_html=True)
        i = 0
        while i < len(charts):
            if i + 1 < len(charts):
                l, r = st.columns(2)
                for offset, (ctx, ci) in enumerate([(l, charts[i]), (r, charts[i+1])]):
                    with ctx:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        render_ai_chart_card(ci, f"pair_{i}_{offset}", df_view, all_cols)
                        st.markdown('</div>', unsafe_allow_html=True)
                i += 2
            else:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                render_ai_chart_card(charts[i], f"single_{i}", df_view, all_cols)
                st.markdown('</div>', unsafe_allow_html=True)
                i += 1
    else:
        st.info("No charts could be generated. Use the Chart Studio below to build one manually.")

    # ── Chart Studio — manual override ───────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:1rem;">
        <div class="sec-icon" style="background:#F0FDF4;">🎨</div>
        <p class="sec-title">Chart Studio</p>
        <span class="manual-badge">✏️ Manual</span>
        <div class="sec-line"></div>
    </div>
    <p style="color:#64748B;font-size:0.85rem;margin-bottom:1rem;">
        Build your own chart. Choose any columns, chart type, and aggregation — then click Add Chart.
    </p>
    """, unsafe_allow_html=True)

    # Get available columns for the selectors
    all_cols   = df_view.columns.tolist()
    num_cols, cat_cols, dt_cols = get_col_types(df_view)
    axis_opts  = ["— none —"] + all_cols
    color_opts = ["— none —"] + cat_cols

    with st.form("chart_studio_form"):
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            ct = st.selectbox("Chart Type", CHART_TYPES, index=0,
                              help="Type of chart to build")
        with c2:
            x_sel = st.selectbox("X Axis", axis_opts, index=0,
                                 help="Column for X axis (or category grouping)")
        with c3:
            y_sel = st.selectbox("Y Axis", axis_opts, index=0,
                                 help="Column for Y axis (metric)")

        c4, c5, c6 = st.columns(3)
        with c4:
            agg_sel = st.selectbox("Aggregation", AGG_OPTIONS, index=0,
                                   help="How to aggregate Y values per X group")
        with c5:
            color_sel = st.selectbox("Color By", color_opts, index=0,
                                     help="Split chart by this column")
        with c6:
            y2_sel = st.selectbox("Y Axis 2 (grouped bar only)", axis_opts, index=0,
                                  help="Second metric for grouped bar charts")

        chart_title = st.text_input("Chart Title", placeholder="e.g. Sales by Region",
                                    help="Give your chart a name")
        add_btn = st.form_submit_button("➕  Add Chart", width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)

    if add_btn:
        x_val     = None if x_sel == "— none —" else x_sel
        y_val     = None if y_sel == "— none —" else y_sel
        color_val = None if color_sel == "— none —" else color_sel
        y2_val    = None if y2_sel == "— none —" else y2_sel

        # For grouped_bar, combine y and y2
        if ct == "grouped_bar" and y_val and y2_val:
            y_final = [y_val, y2_val]
        else:
            y_final = y_val

        spec = {
            "chart_type": ct,
            "x": x_val,
            "y": y_final,
            "color": color_val,
            "agg": agg_sel,
            "title": chart_title or f"{ct} — {y_val or ''} by {x_val or ''}",
            "reason": "Manually created chart",
        }
        result = render_chart(df_view, spec)
        if result:
            if "custom_charts" not in st.session_state or st.session_state.custom_charts is None:
                st.session_state.custom_charts = []
            st.session_state.custom_charts.append(result)
            st.success(f"✅ Chart added: {spec['title']}")
            st.rerun()
        else:
            st.error("❌ Could not build that chart. Check your column selections — make sure X and Y are compatible with the chart type.")

    # Render custom charts
    if "custom_charts" not in st.session_state:
        st.session_state.custom_charts = []
    custom_charts = st.session_state.custom_charts or []

    if custom_charts:
        st.markdown('<div style="margin:1rem 0 0.5rem;"><span class="manual-badge">✏️ Your Custom Charts</span></div>', unsafe_allow_html=True)
        for idx, ci in enumerate(custom_charts):
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            col_chart, col_del = st.columns([5, 1])
            with col_chart:
                st.plotly_chart(ci["fig"], width="stretch")
                st.markdown(f'<p class="chart-lbl">{ci["title"]}</p>', unsafe_allow_html=True)
                custom_explainer = build_chart_explanation(df_view, ci.get("spec", {}), fallback_text="This chart helps explain a key trend or comparison in your selected data.")
                st.markdown(f'<p class="chart-desc"><strong>What this chart tells you:</strong> {custom_explainer}</p>', unsafe_allow_html=True)
                render_possible_actions(ci.get("spec", {}))
            with col_del:
                st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Remove", key=f"del_chart_{idx}"):
                    st.session_state.custom_charts.pop(idx)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🗑️  Clear All Custom Charts"):
            st.session_state.custom_charts = []
            st.rerun()

    # ── Step 4: Insights + Report ──────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    progress_bar(4)

    if st.session_state.insights is None:
        with st.spinner("💡  Generating insights…"):
            try:
                st.session_state.insights = run_insight_generator(df_view, understanding)
            except Exception as e:
                st.session_state.insights = f"⚠️ Could not generate insights: {e}"
            _save_cached_pipeline_state()

    raw = st.session_state.insights or ""
    st.markdown('<p style="color:#64748B;font-size:0.85rem;margin-bottom:0.8rem;">Quick insights are shown first. The report below turns them into a fuller narrative, so each section stays distinct.</p>', unsafe_allow_html=True)

    insight_lines = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("-") or line.startswith("•") or line.startswith("1.") or line.startswith("2.") or line.startswith("3."):
            insight_lines.append(line.lstrip("-•0123456789. ").strip())
    if not insight_lines and raw:
        insight_lines = [raw.strip()]

    if insight_lines:
        st.markdown("""
        <div class="suggest-grid">
            <div class="suggest-card">
                <div class="suggest-label">Quick insights</div>
                <div class="suggest-help">Short signals from the dataset, kept separate from the report.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        for insight in insight_lines[:3]:
            st.markdown(f'<div class="insight-card">{md_to_html(insight)}</div>', unsafe_allow_html=True)

    if st.session_state.report is None:
        with st.spinner("📖  Writing your report…"):
            try:
                st.session_state.report = st.write_stream(run_storyteller(
                    df_view, understanding,
                    st.session_state.insights or "Analysis complete.",
                    st.session_state.cleaning_report or [],
                    stream=True,
                ))
            except Exception as e:
                st.session_state.report = (
                    f"## Analysis Complete\n\n**What We Found:** {understanding}\n\n"
                    f"**Records Analysed:** {len(df_view):,}\n\n⚠️ Full report unavailable: {e}"
                )
            _save_cached_pipeline_state()

    st.markdown(f'<div class="report-card">{md_to_html(st.session_state.report)}</div>',
                unsafe_allow_html=True)

    dl1, dl2, _ = st.columns([1,1,3])
    with dl1:
        st.download_button("⬇️  Report (.md)",
                           data=st.session_state.report.encode("utf-8"),
                           file_name="analysis_report.md", mime="text/markdown",
                   width="stretch")
    with dl2:
        st.download_button("⬇️  Filtered CSV",
                           data=df_view.to_csv(index=False).encode("utf-8"),
                           file_name="filtered_data.csv", mime="text/csv",
                   width="stretch")

    # ── Step 6: Q&A ───────────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    progress_bar(5)
    section("#F0FDF4","🤖","Ask Your Data")

    st.markdown('<p style="color:#64748B;font-size:0.88rem;margin-bottom:0.8rem;">Ask anything in plain English — the AI answers using your actual data.</p>', unsafe_allow_html=True)

    # Suggested question chips
    suggestions = suggest_questions(df_view)
    if suggestions:
        st.markdown("""
        <div class="suggest-grid">
            <div class="suggest-card">
                <div class="suggest-label">Suggested prompts</div>
                <div class="suggest-help">Tap a question to launch a guided answer based on the cleaned dataset.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        button_cols = st.columns(2)
        for i, q in enumerate(suggestions):
            target_col = button_cols[i % 2]
            with target_col:
                if st.button(f"💬 {q}", key=f"sq_{i}", width="stretch"):
                    with st.spinner("🤖  Thinking…"):
                        try:
                            ans = st.write_stream(handle_question(
                                df_view, understanding,
                                st.session_state.insights or "", q,
                                stream=True,
                            ))
                            st.session_state.qa_history.append({"q":q,"a":ans})
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {e}")

    # Chat history
    if st.session_state.qa_history:
        chat_html = '<div class="chat-box">'
        for entry in st.session_state.qa_history:
            chat_html += f"""
            <div class="chat-msg user">
                <div class="chat-av av-u">You</div>
                <div class="chat-bub bub-u">{entry['q']}</div>
            </div>
            <div class="chat-msg">
                <div class="chat-av av-a">AI</div>
                <div class="chat-bub bub-a">{entry['a']}</div>
            </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

    # Input area
    qc, bc = st.columns([5,1])
    with qc:
        st.text_input(
            "q",
            placeholder="Ask a question about your data…",
            label_visibility="collapsed",
            key="qa_question_input",
        )
    with bc:
        submitted = st.button("Ask →", width="stretch", key="qa_submit_button")

    question = (st.session_state.get("qa_question_input") or "").strip()

    if submitted and question:
        with st.spinner("🤖  Thinking…"):
            try:
                ans = st.write_stream(handle_question(
                    df_view, understanding,
                    st.session_state.insights or "", question,
                    stream=True,
                ))
                st.session_state.qa_history.append({"q":question,"a":ans})
                st.session_state.clear_qa_question_input = True
                st.rerun()
            except Exception as e:
                st.error(f"❌ Could not answer: {e}")

    if st.session_state.qa_history:
        if st.button("🗑️  Clear chat"):
            st.session_state.qa_history = []
            st.rerun()

    st.markdown("""<div class="footer">
        <span>AnalystAI</span> · Data Intelligence Platform ·
        Created by OpenAI Codex · Built with Streamlit
    </div>""", unsafe_allow_html=True)

# ── Welcome state ─────────────────────────────────────────────────────────────
else:
    st.markdown("""<div style="text-align:center;padding:2rem 0 1rem;">
        <p style="font-size:3rem;margin:0;">📊</p>
        <h2 style="color:#1E293B;font-weight:700;margin:0.5rem 0;">Drop your data. Get instant intelligence.</h2>
        <p style="color:#64748B;font-size:1rem;max-width:520px;margin:0.5rem auto 0;">
            Upload any CSV or load the sample dataset to see AnalystAI analyse,
            clean, visualise, and explain your data in seconds.
        </p></div>""", unsafe_allow_html=True)

    st.markdown("""<div class="feat-grid">
        <div class="feat-card"><div class="feat-ico">🔍</div><div class="feat-ttl">Instant Understanding</div>
            <div class="feat-dsc">AI reads your data and explains what it is and what stands out — in plain English.</div></div>
        <div class="feat-card"><div class="feat-ico">🧹</div><div class="feat-ttl">Auto Data Cleaning</div>
            <div class="feat-dsc">Detects missing values, duplicates, outliers, inconsistent text — fixes them automatically.</div></div>
        <div class="feat-card"><div class="feat-ico">📊</div><div class="feat-ttl">Smart Visualisations</div>
            <div class="feat-dsc">Picks the right charts automatically — trend, bar, donut, scatter, heatmap and more.</div></div>
        <div class="feat-card"><div class="feat-ico">💰</div><div class="feat-ttl">Business KPIs</div>
            <div class="feat-dsc">Auto-computes revenue, profit margin, avg order value and other key metrics.</div></div>
        <div class="feat-card"><div class="feat-ico">⚠️</div><div class="feat-ttl">Anomaly Detection</div>
            <div class="feat-dsc">Flags negative correlations and data patterns that could hurt your business.</div></div>
        <div class="feat-card"><div class="feat-ico">🤖</div><div class="feat-ttl">AI Q&amp;A Chat</div>
            <div class="feat-dsc">Ask any question in plain English. Get specific, data-backed answers instantly.</div></div>
    </div>""", unsafe_allow_html=True)

    try:
        sdf = pd.read_csv(os.path.join(_ROOT,"sample_data","sample_sales.csv"))
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:600;color:#1E293B;margin-bottom:8px;">👀 Sample Dataset Preview</p>', unsafe_allow_html=True)
        st.dataframe(sdf.head(8), width="stretch")
        st.caption("120 rows of sales data — click 'Sample Data' above to analyse it")
    except Exception:
        pass

    st.markdown("""<div class="footer">
        <span>AnalystAI</span> · Data Intelligence Platform ·
        Created by OpenAI Codex · Built with Streamlit
    </div>""", unsafe_allow_html=True)
