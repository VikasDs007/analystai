import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

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
.main .block-container{padding:1.5rem 2.5rem 3rem;max-width:1400px;}

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
.sec-hdr{display:flex;align-items:center;gap:12px;margin:2.5rem 0 1.2rem 0;}
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
           padding:1.4rem;box-shadow:0 1px 3px rgba(0,0,0,0.05);transition:transform .2s;}
.feat-card:hover{transform:translateY(-3px);}
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

def progress_bar(step):
    """step: 0=detect,1=clean,2=charts,3=insights,4=report,5=qa"""
    steps = ["🔍 Detect","🧹 Clean","📊 Charts","💡 Insights","📖 Report","🤖 Q&A"]
    html = '<div class="prog-bar">'
    for i, s in enumerate(steps):
        cls = "done" if i < step else ("active" if i == step else "")
        html += f'<div class="prog-step {cls}"><div class="prog-dot {cls}"></div>{s}</div>'
        if i < len(steps)-1:
            html += '<span class="prog-arrow">›</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def try_rerun():
    """Attempt to rerun the Streamlit script safely across versions."""
    try:
        # preferred API when available
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            raise AttributeError
    except Exception:
        try:
            # newer Streamlit exposes a runtime rerun exception
            from streamlit.runtime.scriptrunner.script_runner import RerunException
            raise RerunException
        except Exception:
            # fallback: reload browser page via JS
            st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k in ["df_raw","df_clean","detective_result","cleaning_report",
          "charts","insights","report","qa_history","last_file_id",
          "filters","anomalies","custom_charts","onboarding_seen"]:
    if k not in st.session_state:
        st.session_state[k] = None
if not st.session_state.qa_history:
    st.session_state.qa_history = []
if not st.session_state.filters:
    st.session_state.filters = {}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sb-logo">📊 AnalystAI</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748B;font-size:0.78rem;margin-top:-8px;">Data Intelligence Platform</p>', unsafe_allow_html=True)
    st.markdown("---")

    steps_info = [("🔍","Detective","Understands your data"),("🧹","Cleaner","Fixes quality issues"),
                  ("📊","Charts","Visualises patterns"),("💡","Insights","Explains findings"),
                  ("📖","Report","Business summary"),("🤖","Q&A","Answers questions")]
    st.markdown('<p style="font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:6px;">PIPELINE</p>', unsafe_allow_html=True)
    for i,(ico,nm,dsc) in enumerate(steps_info,1):
        st.markdown(f"""<div class="sb-step">
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
    st.markdown('<p style="font-size:0.72rem;color:#475569;text-align:center;">Powered by Groq · Llama 3.1</p>', unsafe_allow_html=True)
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
            # remove persisted onboard file if it exists so this behaves like a new user
            try:
                _ONBOARD_FLAG = os.path.join(_ROOT, ".analystai_onboarded")
                if os.path.exists(_ONBOARD_FLAG):
                    os.remove(_ONBOARD_FLAG)
            except Exception:
                pass
            try_rerun()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""<div class="hero">
    <div class="hero-title">Data Intelligence, Simplified</div>
    <div class="hero-sub">Upload your CSV · Get instant insights · Ask questions in plain English</div>
    <div style="margin-top:1rem;">
        <span class="hero-badge">⚡ Powered by Groq</span>
        <span class="hero-badge">🧠 Llama 3.1</span>
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
    # If a file is already loaded in session, show it and require manual removal
    if st.session_state.get("df_raw") is None:
        uploaded_file = st.file_uploader("CSV", type=["csv"],
                                         label_visibility="collapsed",
                                         help="Upload any CSV file")
    else:
        uploaded_file = None
        # display current loaded file info and a manual remove control
        st.markdown(f"**Loaded file:** {st.session_state.get('last_file_id','(in-memory)')}  ")
        if st.button("Remove loaded file"):
            # clear all dataset-related session state — manual removal
            for k in ["df_raw","df_clean","detective_result","cleaning_report",
                      "charts","insights","report","anomalies","custom_charts",
                      "qa_history","last_file_id","filters"]:
                st.session_state[k] = None
            try_rerun()
with btn_col:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    use_sample = st.button("📊 Sample Data", use_container_width=True)

# ── Load data ─────────────────────────────────────────────────────────────────
df = None; file_id = None
if use_sample:
    try:
        df = pd.read_csv(os.path.join(_ROOT,"sample_data","sample_sales.csv"))
        file_id = "sample"
        st.success(f"✅ Sample dataset — {len(df):,} rows · {len(df.columns)} columns")
    except Exception as e:
        st.error(f"Could not load sample: {e}")
elif uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        file_id = uploaded_file.name + str(uploaded_file.size)
        st.success(f"✅ **{uploaded_file.name}** — {len(df):,} rows · {len(df.columns)} columns")
    except Exception as e:
        st.error(f"Could not read file: {e}")

if df is not None and file_id != st.session_state.last_file_id:
    st.session_state.df_raw = df
    st.session_state.last_file_id = file_id
    for k in ["df_clean","detective_result","cleaning_report",
              "charts","insights","report","anomalies","custom_charts"]:
        st.session_state[k] = None
    st.session_state.qa_history = []
    st.session_state.filters = {}

if st.session_state.df_raw is not None:
    df = st.session_state.df_raw

# ══════════════════════════════════════════════════════════════════════════════
if df is not None:

    with st.expander("🗂️  Raw Data Preview", expanded=False):
        st.dataframe(df, use_container_width=True, height=220)
        st.caption(f"{len(df):,} rows × {len(df.columns)} columns")

    # ── Step 1: Detective ─────────────────────────────────────────────────────
    progress_bar(0)
    if st.session_state.detective_result is None:
        with st.spinner("🔍  Analysing your data…"):
            st.session_state.detective_result = run_detective(df)

    res           = st.session_state.detective_result
    understanding = res["understanding"]
    issues        = res["issues"]
    profile       = res["profile"]

    section("#EFF6FF","🕵️","Data Overview")

    # AI understanding
    st.markdown(f"""<div style="background:linear-gradient(135deg,#EFF6FF,#F0F9FF);
        border:1px solid #BFDBFE;border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;">
        <p style="font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;
                  color:#3B82F6;margin-bottom:6px;">🤖 AI UNDERSTANDING</p>
        <p style="color:#1E293B;font-size:0.95rem;line-height:1.6;margin:0;">{understanding}</p>
    </div>""", unsafe_allow_html=True)

    # ── Business KPI cards ────────────────────────────────────────────────────
    # Run cleaner first if not done (needed for KPIs)
    if st.session_state.df_clean is None:
        with st.spinner("🧹  Cleaning data…"):
            df_clean, cleaning_report = run_cleaner(df, issues)
            st.session_state.df_clean = df_clean
            st.session_state.cleaning_report = cleaning_report

    df_clean        = st.session_state.df_clean
    cleaning_report = st.session_state.cleaning_report

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
        # Render badge column as HTML
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

    # ── Step 2: Data Quality ──────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    progress_bar(1)
    section("#FFF7ED","🚨","Data Quality")

    if issues:
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
    else:
        st.markdown("""<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;
            padding:14px 18px;display:flex;align-items:center;gap:10px;">
            <span style="font-size:1.3rem;">✅</span>
            <span style="color:#166534;font-weight:500;">Data looks clean — no issues detected.</span>
        </div>""", unsafe_allow_html=True)

    with st.expander("✅  Cleaned Data Preview", expanded=False):
        st.dataframe(df_clean, use_container_width=True, height=220)
        st.download_button("⬇️  Download Cleaned CSV",
                           data=df_clean.to_csv(index=False).encode("utf-8"),
                           file_name="cleaned_data.csv", mime="text/csv",
                           use_container_width=True)

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
        with st.spinner("🤖  AI is choosing the best charts for your data…"):
            try:
                st.session_state.charts = build_charts(df_view, understanding)
            except Exception as e:
                st.session_state.charts = []
                st.warning(f"Chart error: {e}")

    # Regenerate button
    regen_col, info_col = st.columns([1, 4])
    with regen_col:
        if st.button("🔄  Regenerate Charts", use_container_width=True,
                     help="Ask the AI to re-pick charts"):
            st.session_state.charts = None
            st.rerun()
    with info_col:
        st.markdown('<p style="color:#64748B;font-size:0.83rem;padding-top:8px;">Charts are selected by AI based on your data structure and correlations. Use the Chart Studio below to add or customise.</p>', unsafe_allow_html=True)

    charts = st.session_state.charts or []

    # Render AI charts
    if charts:
        st.markdown('<div style="margin-bottom:0.5rem;"><span class="llm-badge">🤖 AI Selected</span></div>', unsafe_allow_html=True)
        i = 0
        while i < len(charts):
            if i + 1 < len(charts):
                l, r = st.columns(2)
                for ctx, ci in [(l, charts[i]), (r, charts[i+1])]:
                    with ctx:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        st.plotly_chart(ci["fig"], use_container_width=True)
                        st.markdown(f'<p class="chart-lbl">{ci["title"]}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="chart-desc">{ci["plain"]}</p>', unsafe_allow_html=True)
                        # Show the spec that produced this chart
                        spec = ci.get("spec", {})
                        st.markdown(
                            f'<p style="font-size:0.72rem;color:#C7D2FE;margin-top:4px;">'
                            f'type={spec.get("chart_type","")} · x={spec.get("x","—")} · '
                            f'y={spec.get("y","—")} · agg={spec.get("agg","—")}</p>',
                            unsafe_allow_html=True
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                i += 2
            else:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.plotly_chart(charts[i]["fig"], use_container_width=True)
                st.markdown(f'<p class="chart-lbl">{charts[i]["title"]}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="chart-desc">{charts[i]["plain"]}</p>', unsafe_allow_html=True)
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
        add_btn = st.form_submit_button("➕  Add Chart", use_container_width=True)
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
                st.plotly_chart(ci["fig"], use_container_width=True)
                st.markdown(f'<p class="chart-lbl">{ci["title"]}</p>', unsafe_allow_html=True)
            with col_del:
                st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Remove", key=f"del_chart_{idx}"):
                    st.session_state.custom_charts.pop(idx)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🗑️  Clear All Custom Charts"):
            st.session_state.custom_charts = []
            st.rerun()

    # ── Step 4: Insights ──────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    progress_bar(3)
    section("#FFFBEB","💡","Key Insights")

    if st.session_state.insights is None:

        with st.spinner("💡  Generating insights…"):
            try:
                st.session_state.insights = run_insight_generator(df_view, understanding)
            except Exception as e:
                st.session_state.insights = f"⚠️ Could not generate insights: {e}"

    raw = st.session_state.insights or ""
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    for block in blocks:
        st.markdown(f'<div class="insight-card">{md_to_html(block)}</div>',
                    unsafe_allow_html=True)

    # ── Step 5: Report ────────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    progress_bar(4)
    section("#F0F9FF","📖","Business Report")

    if st.session_state.report is None:
        with st.spinner("📖  Writing your report…"):
            try:
                st.session_state.report = run_storyteller(
                    df_view, understanding,
                    st.session_state.insights or "Analysis complete.",
                    st.session_state.cleaning_report or [],
                )
            except Exception as e:
                st.session_state.report = (
                    f"## Analysis Complete\n\n**What We Found:** {understanding}\n\n"
                    f"**Records Analysed:** {len(df_view):,}\n\n⚠️ Full report unavailable: {e}"
                )

    st.markdown(f'<div class="report-card">{md_to_html(st.session_state.report)}</div>',
                unsafe_allow_html=True)

    dl1, dl2, _ = st.columns([1,1,3])
    with dl1:
        st.download_button("⬇️  Report (.md)",
                           data=st.session_state.report.encode("utf-8"),
                           file_name="analysis_report.md", mime="text/markdown",
                           use_container_width=True)
    with dl2:
        st.download_button("⬇️  Filtered CSV",
                           data=df_view.to_csv(index=False).encode("utf-8"),
                           file_name="filtered_data.csv", mime="text/csv",
                           use_container_width=True)

    # ── Step 6: Q&A ───────────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    progress_bar(5)
    section("#F0FDF4","🤖","Ask Your Data")

    st.markdown('<p style="color:#64748B;font-size:0.88rem;margin-bottom:0.8rem;">Ask anything in plain English — the AI answers using your actual data.</p>', unsafe_allow_html=True)

    # Suggested question chips
    suggestions = suggest_questions(df_view)
    if suggestions:
        chip_html = '<div style="margin-bottom:1rem;">'
        for q in suggestions:
            chip_html += f'<span class="q-chip" onclick="void(0)">💬 {q}</span>'
        chip_html += '</div>'
        st.markdown(chip_html, unsafe_allow_html=True)
        # Streamlit buttons for each suggestion (chips are visual only; buttons are functional)
        cols = st.columns(len(suggestions))
        for i, q in enumerate(suggestions):
            with cols[i]:
                if st.button(f"💬 {q[:40]}…" if len(q)>40 else f"💬 {q}",
                             key=f"sq_{i}", use_container_width=True):
                    with st.spinner("🤖  Thinking…"):
                        try:
                            ans = handle_question(df_view, understanding,
                                                  st.session_state.insights or "", q)
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

    # Input form
    with st.form("qa_form", clear_on_submit=True):
        qc, bc = st.columns([5,1])
        with qc:
            question = st.text_input("q", placeholder="Ask a question about your data…",
                                     label_visibility="collapsed")
        with bc:
            submitted = st.form_submit_button("Ask →", use_container_width=True)

    if submitted and question.strip():
        with st.spinner("🤖  Thinking…"):
            try:
                ans = handle_question(df_view, understanding,
                                      st.session_state.insights or "", question.strip())
                st.session_state.qa_history.append({"q":question.strip(),"a":ans})
                st.rerun()
            except Exception as e:
                st.error(f"❌ Could not answer: {e}")

    if st.session_state.qa_history:
        if st.button("🗑️  Clear chat"):
            st.session_state.qa_history = []
            st.rerun()

    st.markdown("""<div class="footer">
        <span>AnalystAI</span> · Data Intelligence Platform ·
        Powered by Groq + Llama 3.1 · Built with Streamlit
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
        st.dataframe(sdf.head(8), use_container_width=True)
        st.caption("120 rows of sales data — click 'Sample Data' above to analyse it")
    except Exception:
        pass

    st.markdown("""<div class="footer">
        <span>AnalystAI</span> · Data Intelligence Platform ·
        Powered by Groq + Llama 3.1 · Built with Streamlit
    </div>""", unsafe_allow_html=True)
