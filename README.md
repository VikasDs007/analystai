# AnalystAI

**Upload a CSV. Get a full business analysis in 30 seconds.**

AnalystAI is a multi-agent AI-powered data analysis platform built with Streamlit and powered by OpenAI via OpenRouter. Created for the OpenAI Hackathon.

AI cleans your data, picks the best charts, writes a business report, and answers plain-English questions — no code needed.

---

## How it works

| Step | What happens |
|------|-------------|
| **1. Upload** | Drop any CSV (sales, inventory, surveys, finance) up to 10 MB |
| **2. Profile & Clean** | AI detects missing values, duplicates, outliers and inconsistent text — you choose which issues to fix |
| **3. Explore** | AI-selected charts, auto-computed KPIs, anomaly detection |
| **4. Report** | AI writes a structured business report with insights and next steps |
| **5. Ask** | Ask any question in plain English and get a data-backed answer |

---

## Features

### Landing page
- Styled upload zone with drag & drop
- Prominent sample data CTA (120-row retail sales dataset)
- 4-step workflow cards
- Social proof bar (hackathon context, privacy note)

### Data profiling & cleaning
- Skeleton loading screen while AI analyses data
- Per-issue checkboxes — choose exactly which issues to fix
- Structured cleaning results card showing before/after metrics
- Full cleaning diff with imputed values and removed rows

### Workspace tabs
- **Overview** — KPI cards with data-aware sub-labels, top issues, anomaly alerts with "Ask AI" buttons, next-steps guidance
- **Data quality** — Modern column profile table (alternating rows, red highlight for high missing %), severity-coloured issue rows, cleaning summary checklist
- **Charts** — AI-selected charts with skeleton loading, 📌 pin to dashboard, data-aware insight cards, suggested next steps per chart, Chart Studio for custom charts
- **Report** — AI-generated business report with quick insights panel, downloadable as `.md`
- **Ask** — Full-width Q&A panel, streaming answers, chat history, "Why this answer" explainer

### Session persistence
- Refreshing the page restores your full session (uploaded file, cleaned data, charts, report, Q&A history, active tab, filters)
- Sample data sessions are not auto-restored (landing page stays clean)
- "Start fresh" banner on restore

### Sidebar
- Active filter multiselects per categorical column
- Download pack (report + cleaned CSV + chart specs as ZIP)
- Restart button

---

## Project structure

```
analystai/
├── app/
│   ├── main.py                  # Entrypoint — routing, top header, session restore
│   ├── config.py                # Paths, session keys, tab definitions
│   ├── styles.py                # Global CSS (APP_CSS, WORKSPACE_LAYOUT_CSS, etc.)
│   ├── ai_config.py             # OpenAI mode config (always-on, no local fallback)
│   ├── state/
│   │   ├── session.py           # Session init + auto-restore on refresh
│   │   └── cache.py             # Disk persistence (CSV + JSON state)
│   ├── ui/
│   │   ├── charts.py            # Chart card renderer (pin, insight, actions, tweak)
│   │   ├── cleaning_diff.py     # Before/after cleaning comparison
│   │   ├── cleaning_gate.py     # Issue checkbox gate + skeleton loading
│   │   ├── filter_banner.py     # "Filters changed" banner
│   │   ├── layout.py            # Shared components (section, progress_bar, render_skeleton)
│   │   ├── navigation.py        # Tab stepper
│   │   ├── pipeline.py          # KPI snapshot, download pack
│   │   ├── report.py            # Structured report renderer
│   │   ├── summary.py           # Above-fold AI understanding card
│   │   └── workspace_header.py  # Compact workspace header + stat cards
│   └── views/
│       ├── hero.py              # Landing hero banner + 4-step workflow cards
│       ├── onboarding.py        # First-run modal
│       ├── qa_panel.py          # Ask-your-data panel (Ask tab only)
│       ├── sidebar.py           # Sidebar (filters, download, restart)
│       ├── upload.py            # Upload zone, preview, confirm, sample data
│       ├── welcome.py           # Social proof bar + sample data preview
│       ├── workspace.py         # Main workspace orchestrator
│       └── workspace_sections.py # Tab content (overview, quality, charts, report, ask)
├── agents/
│   ├── detective.py             # Data profiling + AI understanding
│   ├── cleaner.py               # Issue fixing (AI-planned order)
│   ├── chart_selector.py        # LLM chart planning + heuristic fallback
│   ├── insight_generator.py     # 3 concise business insights
│   ├── report_writer.py         # Business report generator
│   └── chat_box.py              # Insight-aware Q&A chat agent
├── utils/
│   └── helpers.py               # OpenRouter client, KPI computation, data context builder
├── sample_data/
│   └── sample_sales.csv         # 120-row retail sales dataset
├── .streamlit/
│   ├── secrets.toml             # API keys (git-ignored)
│   └── config.toml              # Theme settings
└── requirements.txt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API key

Open `.streamlit/secrets.toml` and add your OpenRouter key:

```toml
OPEN_ROUTER_KEY = "sk-or-v1-..."
```

Get a free key at [openrouter.ai](https://openrouter.ai). The app uses `openai/gpt-oss-120b:free` by default.

### 3. Run

```bash
PYTHONPATH=. streamlit run app/main.py --server.port 8501
```

Or if using a virtual environment:

```bash
PYTHONPATH=. .venv/bin/streamlit run app/main.py --server.port 8501
```

---

## AI architecture

All AI calls go through OpenRouter using the OpenAI-compatible chat completions API. There is no local fallback mode — the app requires an API key.

| Agent | Model | Purpose |
|-------|-------|---------|
| Detective | `openai/gpt-oss-120b:free` | Profile data, write plain-English understanding, plan cleaning order |
| Cleaner | `openai/gpt-oss-120b:free` | Plan cleaning priority order |
| Chart Selector | `openai/gpt-oss-120b:free` | Choose 6–7 best charts for the dataset |
| Insight Generator | `openai/gpt-oss-120b:free` | Write 3 concise business insights |
| Report Writer | `openai/gpt-oss-120b:free` | Write the business report |
| Chat Box | `openai/gpt-oss-120b:free` | Answer follow-up questions from insights and data context |

---

## Problem / Solution / Workflow / AI

### The Problem
Analysts spend hours manually profiling, cleaning, visualizing, and writing reports from CSVs. This is repetitive, error-prone, and slows time-to-insight for business stakeholders.

### The Solution
AnalystAI automates the end-to-end CSV analysis workflow: upload → profile → clean → visualize → report → interactive Q&A. The app uses modular AI agents to plan and explain work while deterministic code (pandas, Plotly) applies transformations and renders results.

### The Workflow
- Upload a CSV and start a session.
- `detective` profiles the data and proposes a prioritized cleaning plan.
- `cleaner` suggests and applies fixes; before/after diffs are shown.
- `chart_selector` recommends charts and KPIs; charts are rendered with Plotly.
- `insight_generator` and `report_writer` produce concise insights and a downloadable business report.
- `chat_box` answers follow-up questions using dataset context and prior outputs.

### How AI/Codex Is Used
- All LLM calls route through OpenRouter (OpenAI-compatible chat API). Models generate profiles, JSON-like plans, chart recommendations, insights, and human-readable reports.
- Agents produce actionable instructions and natural-language explanations; the app executes deterministic data operations (no code execution by the LLM).
- Default model: `openai/gpt-oss-120b:free` (configurable via `.streamlit/secrets.toml`).

### Result / Outcome
- From raw CSV to cleaned dataset, KPI cards, pinned charts, a full business report, and interactive Q&A — quickly and reproducibly.
- Sessions persist (uploads, cleaned data, charts, report, chat history) and users can download a ZIP pack (report + cleaned CSV + chart specs).

## Requirements

- Python 3.9+
- Streamlit 1.28+
- OpenRouter API key (free tier works)

---

## Tech stack

- **Frontend** — Streamlit + custom CSS (Inter font, glassmorphism cards, skeleton loaders)
- **Charts** — Plotly Express + Plotly Graph Objects
- **AI** — OpenRouter (OpenAI `gpt-oss-120b:free`)
- **Data** — pandas, numpy, scipy
- **Persistence** — JSON + CSV on local disk

---

## License

MIT
