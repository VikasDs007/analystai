"""Global Streamlit CSS for AnalystAI."""

import streamlit as st

APP_CSS = """
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

/* Premium chat enhancements */
.chat-panel{background:linear-gradient(180deg,rgba(255,255,255,0.6),rgba(248,250,252,0.6));
  border-radius:14px;border:1px solid rgba(226,232,240,0.9);padding:0;overflow:hidden;}
.chat-header{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:linear-gradient(90deg,#FFFFFF,#F8FAFF);border-bottom:1px solid #EEF2FF}
.chat-title{font-weight:700;color:#0F172A;font-size:0.98rem;display:flex;align-items:center;gap:10px}
.chat-badge{background:linear-gradient(90deg,#6366F1,#8B5CF6);color:white;padding:6px 10px;border-radius:999px;font-size:0.78rem;font-weight:700}
.chat-history{padding:18px;max-height:420px;overflow-y:auto;background:linear-gradient(180deg,#FBFDFF,white)}
.message{display:flex;gap:12px;margin-bottom:14px;align-items:flex-start}
.message.user{flex-direction:row-reverse}
.avatar{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700}
.avatar.user{background:linear-gradient(90deg,#6366F1,#8B5CF6);color:white}
.avatar.assistant{background:linear-gradient(90deg,#06B6D4,#60A5FA);color:white}
.bubble{max-width:78%;padding:12px 16px;border-radius:14px;font-size:0.95rem;line-height:1.5;box-shadow:0 6px 18px rgba(15,23,42,0.06)}
.bubble.user{background:linear-gradient(90deg,#6366F1,#4F46E5);color:white;border-radius:14px 6px 14px 14px}
.bubble.assistant{background:white;color:#0F172A;border:1px solid #EEF2FF}
.msg-meta{font-size:0.75rem;color:#94A3B8;margin-top:6px}
.typing{height:18px;width:44px;border-radius:12px;background:linear-gradient(90deg,#E6EEF9,#F3F8FF);display:inline-block;position:relative}
.typing::after{content:'';position:absolute;left:8px;top:4px;width:6px;height:6px;background:#9FBFF8;border-radius:50%;box-shadow:10px 0 0 #9FBFF8,20px 0 0 #9FBFF8;animation:typing 1.6s linear infinite}
@keyframes typing{0%{opacity:0.2}50%{opacity:1}100%{opacity:0.2}}
.chat-input{display:flex;gap:8px;padding:12px;border-top:1px solid #EEF2FF;background:linear-gradient(90deg,white,#FBFDFF)}
.chat-text{flex:1;border-radius:12px;padding:10px 12px;border:1px solid #E6EEF9;background:#FFF}
.chat-actions{display:flex;gap:8px;align-items:center}
.chat-send{background:linear-gradient(90deg,#6366F1,#8B5CF6);color:white;border:none;padding:10px 14px;border-radius:10px;font-weight:700}
.chat-secondary{background:transparent;border:1px solid #EEF2FF;padding:8px 12px;border-radius:10px}
.chat-history::-webkit-scrollbar{width:10px}
.chat-history::-webkit-scrollbar-thumb{background:linear-gradient(180deg,#E6EEF9,#C7D2FE);border-radius:8px}


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
"""

REPORT_CSS = """
.report-toc{position:sticky;top:84px;z-index:30;margin-bottom:10px;background:transparent;padding:6px 0}
.report-toc a{color:#4F46E5;text-decoration:none;margin-right:10px;opacity:0.92}
.report-toc a.active{font-weight:700;text-decoration:underline;opacity:1}
html{scroll-behavior:smooth}
"""

CHART_STUDIO_CSS = """
.studio-card{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1rem;}
.studio-title{font-size:0.85rem;font-weight:600;color:#1E293B;margin-bottom:0.8rem;display:flex;align-items:center;gap:8px;}
.llm-badge{background:linear-gradient(90deg,#6366F1,#8B5CF6);color:white;padding:2px 10px;
           border-radius:20px;font-size:0.7rem;font-weight:600;letter-spacing:.04em;}
.manual-badge{background:#F0FDF4;border:1px solid #BBF7D0;color:#16A34A;padding:2px 10px;
              border-radius:20px;font-size:0.7rem;font-weight:600;}
.chart-remove{float:right;background:#FEE2E2;color:#DC2626;border:none;border-radius:6px;
              padding:2px 8px;font-size:0.75rem;cursor:pointer;font-weight:600;}
"""


def inject_styles():
    st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)
    st.markdown(f"<style>{REPORT_CSS}</style>", unsafe_allow_html=True)


def inject_chart_studio_styles():
    st.markdown(f"<style>{CHART_STUDIO_CSS}</style>", unsafe_allow_html=True)


WORKSPACE_LAYOUT_CSS = """
.workspace-header{display:flex;align-items:center;justify-content:space-between;gap:16px;
  background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:1rem 1.25rem;margin-bottom:1rem;
  box-shadow:0 4px 14px rgba(15,23,42,0.04);}
.workspace-header-title{font-size:1.05rem;font-weight:700;color:#0F172A;}
.workspace-header-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;}
.wh-pill{font-size:0.78rem;color:#475569;background:#F8FAFC;border:1px solid #E2E8F0;
  border-radius:999px;padding:4px 10px;}
.workspace-header-status{text-align:right;min-width:120px;}
.wh-status-label{display:block;font-weight:700;font-size:0.9rem;color:#0F172A;}
.wh-status-sub{font-size:0.75rem;color:#64748B;}
.status-ready .wh-status-label{color:#059669;}
.status-progress .wh-status-label{color:#4F46E5;}

.above-fold-grid{margin:0.5rem 0 1rem;}
.above-fold-card{background:linear-gradient(135deg,#EFF6FF,#F8FAFC);border:1px solid #BFDBFE;
  border-radius:12px;padding:1rem 1.2rem;}
.above-fold-label{font-size:0.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  color:#3B82F6;margin:0 0 8px;}
.above-fold-body{color:#1E293B;font-size:0.92rem;line-height:1.55;margin:0;}
.compact-issue{margin-bottom:6px;}

.workspace-stepper-wrap{margin:0.25rem 0 1rem;}
.workspace-layout{margin-top:0.25rem;}

.ask-panel-sticky{position:sticky;top:1rem;max-height:calc(100vh - 2rem);overflow-y:auto;
  background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:0.75rem 0.9rem 1rem;
  box-shadow:0 8px 24px rgba(15,23,42,0.06);}
.ask-panel-hint{font-size:0.82rem;color:#64748B;margin:0 0 0.75rem;}
.ask-chat-box{max-height:280px;}
.ask-tab-hint{background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;padding:1rem 1.2rem;
  color:#166534;font-size:0.9rem;line-height:1.5;}

.sb-section-label{font-size:0.7rem;font-weight:600;text-transform:uppercase;
  letter-spacing:.08em;color:#94A3B8 !important;margin-bottom:6px;}
.sb-tip{font-size:0.79rem;color:#94A3B8 !important;padding:2px 0;margin:0;}

.snapshot-grid{grid-template-columns:repeat(auto-fit,minmax(140px,1fr)) !important;}

@media (max-width: 1100px){
  .ask-panel-sticky{position:relative;top:0;max-height:none;margin-top:1rem;}
}

.review-gate{background:linear-gradient(135deg,#FFFBEB,#FEF3C7);border:1px solid #FCD34D;
  border-radius:14px;padding:1.1rem 1.25rem;margin:0.75rem 0 1rem;}
.review-gate-title{font-size:1.05rem;font-weight:700;color:#92400E;margin:0 0 4px;}
.review-gate-sub{font-size:0.88rem;color:#B45309;margin:0;line-height:1.45;}

.filter-dirty-banner{background:#FEF3C7;border:1px solid #FCD34D;border-radius:10px;
  padding:0.85rem 1rem;margin:0.5rem 0 1rem;color:#92400E;font-size:0.9rem;}
"""


def inject_workspace_layout_styles():
    st.markdown(f"<style>{WORKSPACE_LAYOUT_CSS}</style>", unsafe_allow_html=True)
