# User Flow — AnalystAI

```mermaid
flowchart TD
  A[User uploads CSV or clicks Sample Data] --> B(Agent: Detective — profile data)
  B --> C{Is data clean?}
  C -- No --> D(Agent: Cleaner — produce df_clean + cleaning_report)
  D --> E(Agent: Chart Selector — propose charts)
  C -- Yes --> E
  E --> F(Agent: Insight Generator — summaries)
  F --> G(Storyteller/Q&A) --> H[User asks question]
  H --> I[Agent answers with data-backed response]
  E --> J[User exports Download Pack]
```

Flow notes

- Each agent step writes to `st.session_state` so the UI reflects progress.
- User can remove file or load sample data at any time; removing clears cached state.
- Download pack aggregates the report, cleaned CSV, and chart specs into a zip.
