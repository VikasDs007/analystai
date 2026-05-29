# AnalystAI

A multi-agent AI-powered data analysis platform built with Streamlit. Created by OpenAI Codex.

## Project Structure

```
analystai/
├── app/                 # Streamlit application
│   └── main.py
├── agents/              # AI agents for different tasks
│   ├── detective.py     # Data investigation
│   ├── cleaner.py       # Data cleaning & preprocessing
│   ├── chart_selector.py # Visualization recommendations
│   ├── insight_generator.py # Insight generation
│   └── storyteller.py   # Data storytelling
├── utils/               # Utility functions
│   └── helpers.py
├── sample_data/         # Sample datasets
│   └── sample_sales.csv
├── .streamlit/          # Streamlit configuration
│   ├── secrets.toml     # API keys (git-ignored)
│   └── config.toml      # Theme & UI settings
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key (if required):**
   - Open `.streamlit/secrets.toml`
   - Set an appropriate API key for your chosen backend if required (e.g., Groq).

3. **Run the application:**
   ```bash
   streamlit run app/main.py
   ```

## Agents

- **Detective**: Analyzes data structure and patterns
- **Cleaner**: Handles missing values and data preprocessing
- **Chart Selector**: Recommends appropriate visualizations
- **Insight Generator**: Extracts meaningful insights from data
- **Storyteller**: Creates narrative around findings

## Features

- Multi-agent AI analysis
- Interactive data visualizations
- Automated insights and recommendations
- Clean, modern UI with custom theme

## Requirements

- Python 3.9+
- Streamlit 1.28+
- API key (optional)

## License

MIT
