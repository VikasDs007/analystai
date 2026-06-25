"""Global Streamlit CSS for AnalystAI — refactored with HSL properties and glassmorphism."""

import streamlit as st

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── CSS Custom Properties (Design Tokens) ────────────────────────────────── */
:root {
  /* Brand colors (Royal Violet/Indigo) */
  --primary-h: 245;
  --primary-s: 82%;
  --primary-l: 61%;
  
  --primary: hsl(var(--primary-h), var(--primary-s), var(--primary-l));
  --primary-light: hsl(var(--primary-h), var(--primary-s), calc(var(--primary-l) + 10%));
  --primary-dark: hsl(var(--primary-h), var(--primary-s), calc(var(--primary-l) - 12%));
  --primary-bg: hsla(var(--primary-h), var(--primary-s), var(--primary-l), 0.06);
  --primary-border: hsla(var(--primary-h), var(--primary-s), var(--primary-l), 0.16);

  /* Accent colors */
  --accent-sky: #0EA5E9;
  --accent-sky-light: #38BDF8;
  --accent-emerald: #10B981;
  --accent-amber: #F59E0B;
  --accent-rose: #F43F5E;
  --accent-violet: #8B5CF6;

  /* Light Theme Neutrals */
  --bg-base: #F8FAFC;
  --bg-surface: rgba(255, 255, 255, 0.78); /* Glassmorphism background */
  --bg-muted: #F1F5F9;
  --border: rgba(226, 232, 240, 0.65);
  --border-light: rgba(238, 242, 255, 0.7);
  --text-primary: #0F172A;
  --text-secondary: #334155;
  --text-muted: #64748B;
  --text-faint: #94A3B8;

  /* Semantic States */
  --success: #10B981;
  --success-bg: rgba(240, 253, 244, 0.7);
  --success-border: rgba(187, 247, 208, 0.5);
  --warning: #F59E0B;
  --warning-bg: rgba(254, 243, 199, 0.7);
  --warning-border: rgba(252, 211, 77, 0.5);
  --danger: #DC2626;
  --danger-bg: rgba(254, 226, 226, 0.7);
  --danger-border: rgba(254, 202, 202, 0.5);

  /* Layout Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 22px;
  --radius-full: 999px;

  /* Premium Glass Shadows */
  --shadow-sm: 0 2px 5px rgba(15, 23, 42, 0.03);
  --shadow-md: 0 10px 25px rgba(15, 23, 42, 0.04);
  --shadow-lg: 0 18px 40px rgba(99, 102, 241, 0.08);
  --shadow-xl: 0 26px 70px rgba(15, 23, 42, 0.08);

  /* Performance Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 220ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);

  /* Dark Theme Overrides */
  --dm-bg-base: #090D16;
  --dm-bg-surface: rgba(17, 24, 39, 0.68);
  --dm-bg-muted: #1F2937;
  --dm-border: rgba(75, 85, 99, 0.28);
  --dm-text-primary: #F3F4F6;
  --dm-text-secondary: #E5E7EB;
  --dm-text-muted: #9CA3AF;
}

/* ── Dark Mode Activation ─────────────────────────────────────────────────── */
body.dark-mode {
  --bg-base: var(--dm-bg-base);
  --bg-surface: var(--dm-bg-surface);
  --bg-muted: var(--dm-bg-muted);
  --border: var(--dm-border);
  --border-light: rgba(75, 85, 99, 0.2);
  --text-primary: var(--dm-text-primary);
  --text-secondary: var(--dm-text-secondary);
  --text-muted: var(--dm-text-muted);
  --text-faint: #6B7280;
  --primary-bg: rgba(99, 102, 241, 0.12);
  --success-bg: rgba(16, 185, 129, 0.12);
  --warning-bg: rgba(245, 158, 11, 0.12);
  --danger-bg: rgba(220, 38, 38, 0.12);
}

/* ── Base Reset & Gradients ───────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
}
html, body {
  background:
    radial-gradient(circle at top left, rgba(99, 102, 241, 0.08), transparent 38%),
    radial-gradient(circle at top right, rgba(139, 92, 246, 0.08), transparent 32%),
    linear-gradient(180deg, var(--bg-base) 0%, var(--primary-bg) 100%);
  color: var(--text-primary);
  transition: background var(--transition-slow), color var(--transition-slow);
}
.main .block-container {
  padding: 2rem 3rem 4rem;
  max-width: 1440px;
}

/* ── Typography & Focus Accessibility ─────────────────────────────────────── */
:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* ── Animations ───────────────────────────────────────────────────────────── */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
.tab-content-enter {
  animation: fadeInUp var(--transition-slow) cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes confettiFall {
  0%   { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
  100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
}
.confetti-piece {
  position: fixed; top: -10px; width: 10px; height: 10px;
  z-index: 99999; pointer-events: none;
  animation: confettiFall 3s ease-in forwards;
}

/* ── Hero Component ───────────────────────────────────────────────────────── */
.hero {
  background: linear-gradient(135deg, #090D16 0%, #171E30 55%, var(--primary-dark) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-xl);
  padding: 3rem 3.5rem;
  margin-bottom: 2rem;
  position: relative; overflow: hidden;
  color: white;
  box-shadow: var(--shadow-xl);
}
.hero::before {
  content: ''; position: absolute; top: -40%; right: -10%;
  width: 450px; height: 450px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}
.hero::after {
  content: ''; position: absolute; inset: auto -80px -80px auto;
  width: 320px; height: 320px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.15), transparent 68%);
  border-radius: 50%;
  pointer-events: none;
}
.hero-title {
  font-size: 2.8rem; font-weight: 800; margin: 0; line-height: 1.15;
  background: linear-gradient(90deg, #60A5FA, #A78BFA, #F472B6);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -1px;
}
.hero-sub { color: #9CA3AF; font-size: 1.12rem; margin-top: 0.75rem; line-height: 1.6; font-weight: 400; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.35);
  color: #A78BFA; border-radius: var(--radius-full);
  padding: 5px 14px; font-size: 0.76rem; font-weight: 600;
  margin-top: 1rem; margin-right: 8px;
  letter-spacing: 0.02em;
}
.hero-cta {
  display: inline-flex; align-items: center; gap: 8px;
  background: linear-gradient(135deg, var(--primary), var(--accent-violet));
  color: white !important; border: none; border-radius: var(--radius-full);
  padding: 13px 30px; font-size: 0.98rem; font-weight: 700;
  cursor: pointer; transition: all var(--transition-base);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35);
  text-decoration: none; margin-top: 1.5rem;
}
.hero-cta:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(99, 102, 241, 0.45);
}

/* ── Design System Glassmorphic Cards ─────────────────────────────────────── */
.snapshot-card, .kpi-card, .feat-card, .next-card, .chart-card, .insight-card, .suggest-card, .review-gate, .chat-panel {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(14px) saturate(120%);
  -webkit-backdrop-filter: blur(14px) saturate(120%);
  transition: transform var(--transition-base), box-shadow var(--transition-base), border-color var(--transition-base);
}

.snapshot-card:hover, .kpi-card:hover, .feat-card:hover, .next-card:hover, .chart-card:hover, .insight-card:hover, .suggest-card:hover {
  transform: translateY(-4px) scale(1.006);
  box-shadow: var(--shadow-lg);
  border-color: rgba(99, 102, 241, 0.32);
}

/* ── Snapshot Cards ────────────────────────────────────────────────────────── */
.snapshot-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)) !important;
  gap: 14px; margin: 1.2rem 0 1.5rem;
}
.snapshot-card {
  border-radius: var(--radius-lg); padding: 1.1rem 1.2rem;
}
.snapshot-card.primary {
  border-color: var(--primary-border);
  background: linear-gradient(180deg, var(--bg-surface) 0%, rgba(99, 102, 241, 0.05) 100%);
}
.snapshot-lbl {
  font-size: 0.74rem; font-weight: 700; letter-spacing: .08em;
  text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;
}
.snapshot-val { font-size: 1.45rem; font-weight: 800; line-height: 1; color: var(--text-primary); }
.snapshot-sub { font-size: 0.8rem; color: var(--text-muted); margin-top: 6px; line-height: 1.45; }

/* ── Next Steps ────────────────────────────────────────────────────────────── */
.next-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin: 0.8rem 0 1.25rem; }
.next-card {
  border-radius: var(--radius-lg);
  padding: 1.2rem 1.3rem;
}
.next-ico { font-size: 1.4rem; margin-bottom: 8px; display: inline-flex; }
.next-title { font-weight: 700; color: var(--text-primary); font-size: 0.96rem; margin-bottom: 4px; }
.next-desc { color: var(--text-muted); font-size: 0.84rem; line-height: 1.55; }

/* ── Sidebar Redesign ──────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #060B13 0%, #0F1622 100%) !important;
  border-right: 1px solid rgba(75, 85, 99, 0.18) !important;
}
[data-testid="stSidebar"] * { color: #9CA3AF !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #F3F4F6 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(75, 85, 99, 0.18) !important; }
.sb-logo { font-size: 1.5rem; font-weight: 800; color: #60A5FA !important; letter-spacing: -0.5px; }
.sb-step {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; border-radius: var(--radius-md); margin: 4px 0;
  transition: all var(--transition-fast);
}
.sb-step:hover { background: rgba(99, 102, 241, 0.1); }
.sb-num {
  background: var(--primary); color: white !important; width: 24px; height: 24px;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 700; flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.3);
}
.sb-txt { font-size: 0.85rem; color: #D1D5DB !important; font-weight: 500; }

/* ── Section Headers ───────────────────────────────────────────────────────── */
.sec-hdr { display: flex; align-items: center; gap: 14px; margin: 2.3rem 0 1.2rem 0; }
.sec-icon {
  width: 38px; height: 38px; border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}
.sec-title { font-size: 1.25rem; font-weight: 700; color: var(--text-secondary); margin: 0; letter-spacing: -0.2px; }
.sec-line { flex: 1; height: 1px; background: linear-gradient(90deg, var(--border), transparent); }

/* ── KPI Cards ─────────────────────────────────────────────────────────────── */
.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px; margin: 1.2rem 0;
}
.kpi-card {
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.45rem;
}
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; }
.kpi-blue::before  { background: linear-gradient(90deg, #2563EB, #60A5FA); }
.kpi-green::before { background: linear-gradient(90deg, #059669, #34D399); }
.kpi-purple::before { background: linear-gradient(90deg, #7C3AED, #A78BFA); }
.kpi-amber::before { background: linear-gradient(90deg, #D97706, #FCD34D); }
.kpi-rose::before  { background: linear-gradient(90deg, #E11D48, #FB7185); }
.kpi-lbl {
  font-size: 0.74rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .08em; color: var(--text-muted); margin-bottom: 6px;
}
.kpi-ico { font-size: 1.5rem; float: right; margin-top: -3px; opacity: .8; }
.kpi-val { font-size: 2.1rem; font-weight: 800; color: var(--text-primary); line-height: 1.05; }
.kpi-sub { font-size: 0.76rem; color: var(--text-muted); margin-top: 6px; font-weight: 500; }

/* ── Progress & Stepper ────────────────────────────────────────────────────── */
.prog-bar {
  display: flex; align-items: center; gap: 0; margin: 1.2rem 0 1.8rem 0;
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 12px 20px;
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  box-shadow: var(--shadow-sm);
}
.prog-step {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.84rem; font-weight: 500; color: var(--text-muted); flex: 1;
}
.prog-step.done { color: var(--success); font-weight: 600; }
.prog-step.active { color: var(--primary); font-weight: 700; }
.prog-dot {
  width: 9px; height: 9px; border-radius: 50%; background: var(--text-faint); flex-shrink: 0;
  transition: all var(--transition-base);
}
.prog-dot.done { background: var(--success); }
.prog-dot.active { background: var(--primary); box-shadow: 0 0 0 4px hsla(var(--primary-h), var(--primary-s), var(--primary-l), 0.25); }
.prog-arrow { color: var(--text-faint); margin: 0 6px; font-size: 0.75rem; font-weight: 700; }

/* ── Issue Rows ────────────────────────────────────────────────────────────── */
.issue-row {
  display: flex; align-items: center; gap: 12px; padding: 12px 18px;
  border-radius: var(--radius-md); background: var(--bg-muted);
  border: 1px solid var(--border); margin-bottom: 8px;
}
.badge { padding: 3px 12px; border-radius: var(--radius-full); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.02em; }
.badge-high   { background: var(--danger-bg); color: var(--danger); border: 1px solid var(--danger-border); }
.badge-medium { background: var(--warning-bg); color: #D97706; border: 1px solid var(--warning-border); }
.badge-low    { background: var(--success-bg); color: #16A34A; border: 1px solid var(--success-border); }

/* ── Clean Steps ───────────────────────────────────────────────────────────── */
.clean-step {
  display: flex; align-items: center; gap: 10px; padding: 10px 18px;
  border-radius: var(--radius-md); background: var(--success-bg);
  border: 1px solid var(--success-border); margin-bottom: 8px;
  font-size: 0.9rem; color: #166534; font-weight: 500;
}

/* ── Anomaly Callouts ──────────────────────────────────────────────────────── */
.anomaly-card {
  border-radius: var(--radius-md); border-left: 5px solid #F97316;
  padding: 14px 18px; margin-bottom: 12px;
}
.anomaly-title { font-weight: 700; color: #C2410C; font-size: 0.92rem; margin-bottom: 4px; }
.anomaly-desc { font-size: 0.85rem; color: #92400E; line-height: 1.55; }

/* ── Chart Cards ───────────────────────────────────────────────────────────── */
.chart-card {
  border-radius: var(--radius-lg);
  padding: 1.25rem; margin-bottom: 1.5rem;
}
.chart-lbl {
  font-size: 0.78rem; font-weight: 700; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .08em; margin-bottom: 5px;
}
.chart-desc { font-size: 0.86rem; color: var(--text-secondary); line-height: 1.6; }

/* ── Insight Cards ─────────────────────────────────────────────────────────── */
.insight-card {
  border-radius: var(--radius-lg);
  border-left: 5px solid var(--primary);
  padding: 1.3rem 1.6rem; margin-bottom: 12px;
}

/* ── Report Card ───────────────────────────────────────────────────────────── */
.report-card {
  background: linear-gradient(135deg, var(--bg-surface) 0%, rgba(99, 102, 241, 0.04) 100%);
  border: 1px solid var(--primary-border); border-radius: var(--radius-lg);
  padding: 2rem 2.4rem; margin-bottom: 1.2rem;
}

/* ── Suggested Prompts / Chips ──────────────────────────────────────────────── */
.q-chip {
  display: inline-block; background: var(--primary-bg);
  border: 1px solid var(--primary-border); color: var(--primary-dark);
  border-radius: var(--radius-full); padding: 6px 16px; font-size: 0.84rem;
  font-weight: 600; margin: 5px; cursor: pointer;
  transition: all var(--transition-fast);
}
.q-chip:hover {
  background: hsla(var(--primary-h), var(--primary-s), var(--primary-l), 0.14);
  border-color: hsla(var(--primary-h), var(--primary-s), var(--primary-l), 0.4);
}
.suggest-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px; margin-top: 1rem;
}
.suggest-card {
  border-radius: var(--radius-lg); padding: 1rem 1.2rem;
}
.suggest-label {
  font-size: 0.74rem; font-weight: 800; letter-spacing: .08em;
  text-transform: uppercase; color: var(--primary); margin-bottom: 6px;
}
.suggest-help { font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 0.8rem; }

/* ── Premium Chat Panel ────────────────────────────────────────────────────── */
.chat-panel {
  border-radius: var(--radius-xl);
  padding: 0; overflow: hidden;
}
.chat-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; background: linear-gradient(90deg, var(--bg-surface), rgba(99, 102, 241, 0.05));
  border-bottom: 1px solid var(--border);
}
.chat-title { font-weight: 800; color: var(--text-primary); font-size: 1.05rem; display: flex; align-items: center; gap: 10px; }
.chat-badge {
  background: linear-gradient(135deg, var(--primary), var(--accent-violet));
  color: white; padding: 6px 12px; border-radius: var(--radius-full);
  font-size: 0.8rem; font-weight: 750;
  box-shadow: 0 3px 8px rgba(99, 102, 241, 0.25);
}
.chat-history {
  padding: 20px; max-height: 440px; overflow-y: auto;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent);
}
.message { display: flex; gap: 14px; margin-bottom: 16px; align-items: flex-start; }
.message.user { flex-direction: row-reverse; }
.avatar {
  width: 38px; height: 38px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-weight: 700;
  box-shadow: var(--shadow-sm);
}
.avatar.user { background: linear-gradient(135deg, var(--primary), var(--accent-violet)); color: white; }
.avatar.assistant { background: linear-gradient(135deg, #0EA5E9, #60A5FA); color: white; }
.bubble {
  max-width: 78%; padding: 12px 18px; border-radius: 16px;
  font-size: 0.96rem; line-height: 1.55;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
}
.bubble.user {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white !important; border-radius: 16px 4px 16px 16px;
}
.bubble.assistant {
  background: var(--bg-surface); color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: 4px 16px 16px 16px;
}
.msg-meta { font-size: 0.76rem; color: var(--text-faint); margin-top: 6px; }
.typing {
  height: 18px; width: 44px; border-radius: 12px;
  background: var(--bg-muted);
  display: inline-block; position: relative;
}
.typing::after {
  content: ''; position: absolute; left: 8px; top: 4px;
  width: 6px; height: 6px; background: var(--text-muted); border-radius: 50%;
  box-shadow: 10px 0 0 var(--text-muted), 20px 0 0 var(--text-muted);
  animation: typing 1.6s infinite linear;
}
.chat-input {
  display: flex; gap: 10px; padding: 14px; border-top: 1px solid var(--border);
  background: var(--bg-surface);
}
.chat-text { flex: 1; border-radius: var(--radius-md); padding: 10px 14px; border: 1px solid var(--border); background: var(--bg-base); color: var(--text-primary); }
.chat-actions { display: flex; gap: 8px; align-items: center; }
.chat-send {
  background: linear-gradient(135deg, var(--primary), var(--accent-violet));
  color: white !important; border: none; padding: 11px 18px; border-radius: 10px; font-weight: 700;
  box-shadow: 0 3px 8px rgba(99, 102, 241, 0.2);
}
.chat-secondary { background: transparent; border: 1px solid var(--border); padding: 9px 14px; border-radius: 10px; }
.chat-history::-webkit-scrollbar { width: 8px; }
.chat-history::-webkit-scrollbar-thumb {
  background: var(--border); border-radius: 8px;
}

/* ── Feature Grid ─────────────────────────────────────────────────────────── */
.feat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin: 1.8rem 0; }
.feat-card {
  border-radius: var(--radius-lg); padding: 1.5rem;
}
.feat-ico { font-size: 2rem; margin-bottom: 12px; }
.feat-ttl { font-weight: 700; color: var(--text-secondary); font-size: 1rem; margin-bottom: 6px; }
.feat-dsc { font-size: 0.85rem; color: var(--text-muted); line-height: 1.6; }

/* ── Custom Review Gate ───────────────────────────────────────────────────── */
.review-gate {
  background: linear-gradient(135deg, #FFFDF5 0%, #FEF8E7 100%);
  border: 1px solid #FDE047; border-radius: var(--radius-lg);
  padding: 1.25rem 1.6rem; margin: 1rem 0 1.2rem;
}
body.dark-mode .review-gate {
  background: linear-gradient(135deg, #1E1B4B 0%, #231A11 100%);
  border-color: #B45309;
}
.review-gate-title { font-size: 1.1rem; font-weight: 800; color: #A16207; margin: 0 0 6px; }
body.dark-mode .review-gate-title { color: #F59E0B; }
.review-gate-sub { font-size: 0.9rem; color: #A16207; margin: 0; line-height: 1.5; }
body.dark-mode .review-gate-sub { color: #F3F4F6; }

/* ── Misc ──────────────────────────────────────────────────────────────────── */
.divider { height: 1px; background: linear-gradient(90deg, transparent, var(--border), transparent); margin: 2.2rem 0; }
.footer {
  text-align: center; padding: 2rem; color: var(--text-faint);
  font-size: 0.8rem; border-top: 1px solid var(--border); margin-top: 4rem;
}
.footer span { color: var(--primary); font-weight: 700; }
div[data-testid="stMetric"] {
  background: var(--bg-surface) !important; border-radius: 12px !important;
  padding: 1.1rem !important; border: 1px solid var(--border) !important;
  box-shadow: var(--shadow-sm) !important;
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
}
.stButton>button { border-radius: var(--radius-md) !important; font-weight: 600 !important; transition: all var(--transition-base) !important; }
div[data-testid="stExpander"] {
  background: var(--bg-surface) !important;
  border: 1px solid var(--border) !important; border-radius: 12px !important;
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
}
</style>
"""

REPORT_CSS = """
<style>
.report-toc { position: sticky; top: 84px; z-index: 30; margin-bottom: 10px; background: transparent; padding: 6px 0; }
.report-toc a { color: var(--primary); text-decoration: none; margin-right: 10px; opacity: 0.92; font-weight: 500; }
.report-toc a.active { font-weight: 750; text-decoration: underline; opacity: 1; }
html { scroll-behavior: smooth; }
</style>
"""

CHART_STUDIO_CSS = """
<style>
.studio-card {
  background: var(--bg-muted); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 1.3rem 1.5rem; margin-bottom: 1.2rem;
}
.studio-title {
  font-size: 0.9rem; font-weight: 700; color: var(--text-secondary);
  margin-bottom: 0.9rem; display: flex; align-items: center; gap: 8px;
}
.llm-badge {
  background: linear-gradient(135deg, var(--primary), var(--accent-violet));
  color: white; padding: 3px 12px; border-radius: var(--radius-full);
  font-size: 0.72rem; font-weight: 700; letter-spacing: .04em;
}
.manual-badge {
  background: var(--success-bg); border: 1px solid var(--success-border);
  color: #16A34A; padding: 3px 12px; border-radius: var(--radius-full);
  font-size: 0.72rem; font-weight: 700;
}
.chart-remove {
  float: right; background: var(--danger-bg); color: var(--danger);
  border: none; border-radius: 8px; padding: 4px 10px;
  font-size: 0.78rem; cursor: pointer; font-weight: 700;
}
</style>
"""

WORKSPACE_LAYOUT_CSS = """
<style>
.workspace-header {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 1.2rem 1.45rem; margin-bottom: 1.2rem;
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
}
.workspace-header-title { font-size: 1.1rem; font-weight: 800; color: var(--text-primary); }
.workspace-header-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; }
.wh-pill {
  font-size: 0.8rem; color: var(--text-secondary);
  background: var(--bg-muted); border: 1px solid var(--border);
  border-radius: var(--radius-full); padding: 5px 12px;
  font-weight: 500;
}
.workspace-header-status { text-align: right; min-width: 130px; }
.wh-status-label { display: block; font-weight: 800; font-size: 0.95rem; color: var(--text-primary); }
.wh-status-sub { font-size: 0.78rem; color: var(--text-muted); }
.status-ready .wh-status-label { color: var(--success); }
.status-progress .wh-status-label { color: var(--primary-dark); }

.above-fold-grid { margin: 0.6rem 0 1.2rem; }
.above-fold-card {
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.5), rgba(248, 250, 252, 0.5));
  border: 1px solid var(--primary-border); border-radius: var(--radius-lg);
  padding: 1.2rem 1.4rem;
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
}
body.dark-mode .above-fold-card {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(15, 23, 42, 0.2));
}
.above-fold-label {
  font-size: 0.74rem; font-weight: 800; letter-spacing: .06em;
  text-transform: uppercase; color: var(--primary); margin: 0 0 8px;
}
.above-fold-body { color: var(--text-secondary); font-size: 0.94rem; line-height: 1.6; margin: 0; }
.compact-issue { margin-bottom: 6px; }

.workspace-stepper-wrap { margin: 0.25rem 0 1.2rem; }
.workspace-layout { margin-top: 0.25rem; }

.ask-panel-sticky {
  position: sticky; top: 1rem; max-height: calc(100vh - 2rem); overflow-y: auto;
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 0.85rem 1rem 1.2rem;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
}
.ask-panel-hint { font-size: 0.84rem; color: var(--text-muted); margin: 0 0 0.85rem; }
.ask-chat-box { max-height: 300px; }
.ask-tab-hint {
  background: var(--success-bg); border: 1px solid var(--success-border);
  border-radius: var(--radius-md); padding: 1.1rem 1.3rem;
  color: #166534; font-size: 0.92rem; line-height: 1.55;
  font-weight: 500;
}

.sb-section-label {
  font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .08em; color: #64748B !important; margin-bottom: 6px;
}
.sb-tip { font-size: 0.82rem; color: #94A3B8 !important; padding: 3px 0; margin: 0; }

.snapshot-grid { grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)) !important; }

@media (max-width: 1100px) {
  .ask-panel-sticky { position: relative; top: 0; max-height: none; margin-top: 1rem; }
}

.review-gate {
  background: linear-gradient(135deg, #FFFDF5 0%, #FEF8E7 100%);
  border: 1px solid #FDE047; border-radius: var(--radius-lg);
  padding: 1.25rem 1.6rem; margin: 1rem 0 1.2rem;
}
body.dark-mode .review-gate {
  background: linear-gradient(135deg, #1E1B4B 0%, #231A11 100%);
  border-color: #B45309;
}
.review-gate-title { font-size: 1.1rem; font-weight: 800; color: #A16207; margin: 0 0 6px; }
body.dark-mode .review-gate-title { color: #F59E0B; }
.review-gate-sub { font-size: 0.9rem; color: #A16207; margin: 0; line-height: 1.5; }
body.dark-mode .review-gate-sub { color: #F3F4F6; }

.filter-dirty-banner {
  background: var(--warning-bg); border: 1px solid var(--warning-border);
  border-radius: 12px; padding: 1rem 1.25rem; margin: 0.6rem 0 1.25rem;
  color: #92400E; font-size: 0.93rem;
  font-weight: 500;
}
</style>
"""

def inject_styles():
    st.markdown(f"{APP_CSS}", unsafe_allow_html=True)
    st.markdown(f"{REPORT_CSS}", unsafe_allow_html=True)

def inject_chart_studio_styles():
    st.markdown(f"{CHART_STUDIO_CSS}", unsafe_allow_html=True)

def inject_workspace_layout_styles():
    st.markdown(f"{WORKSPACE_LAYOUT_CSS}", unsafe_allow_html=True)
