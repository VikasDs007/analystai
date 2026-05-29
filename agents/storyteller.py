"""Storyteller agent — generates a business report and answers Q&A."""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import (
    get_groq_client,
    build_data_context,
    groq_json_decision,
    choose_main_numeric,
    choose_main_category,
)


def _text_stream(text, chunk_size=24):
    """Yield a text string in small chunks for Streamlit write_stream()."""
    if text is None:
        return
    text = str(text)
    for idx in range(0, len(text), chunk_size):
        yield text[idx:idx + chunk_size]


def _local_fallback_answer(df, question: str) -> str:
    """Provide a simple deterministic answer when Groq is unavailable."""
    import numpy as np

    lower_q = question.lower()
    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns]

    if not numeric_cols:
        return (
            "I could not use the Groq chat response just now, and this dataset does not "
            "have numeric columns I can summarize locally. Try asking about a column name "
            "or reload the app after checking your Groq API key."
        )

    target = choose_main_numeric(numeric_cols)
    series = pd.to_numeric(df[target], errors="coerce")

    if any(word in lower_q for word in ["total", "sum", "how much"]):
        return f"Total {target.replace('_', ' ')}: {series.sum():,.2f}."
    if any(word in lower_q for word in ["average", "mean", "avg"]):
        return f"Average {target.replace('_', ' ')}: {series.mean():,.2f}."
    if any(word in lower_q for word in ["max", "highest", "top"]):
        return f"Highest {target.replace('_', ' ')}: {series.max():,.2f}."
    if any(word in lower_q for word in ["min", "lowest"]):
        return f"Lowest {target.replace('_', ' ')}: {series.min():,.2f}."

    return (
        f"I could not reach Groq chat right now, but I can confirm this dataset has "
        f"{len(df):,} rows and the main numeric field {target.replace('_', ' ')} has an "
        f"average of {series.mean():,.2f}."
    )


def _local_question_answer(df, question: str):
    """Try to answer common analytics questions without using Groq."""
    import numpy as np

    lower_q = question.lower()
    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
    object_cols = [c for c in df.select_dtypes(include=["object"]).columns]

    if not numeric_cols:
        return None

    target = choose_main_numeric(numeric_cols)
    if not target:
        return None

    series = pd.to_numeric(df[target], errors="coerce")

    if any(word in lower_q for word in ["average", "mean", "avg"]):
        return f"Average {target.replace('_', ' ')}: {series.mean():,.2f}."
    if any(word in lower_q for word in ["total", "sum", "how much"]):
        return f"Total {target.replace('_', ' ')}: {series.sum():,.2f}."
    if any(word in lower_q for word in ["max", "highest", "top"]):
        return f"Highest {target.replace('_', ' ')}: {series.max():,.2f}."
    if any(word in lower_q for word in ["min", "lowest"]):
        return f"Lowest {target.replace('_', ' ')}: {series.min():,.2f}."

    if any(word in lower_q for word in ["count", "how many"]):
        return f"Count of non-missing {target.replace('_', ' ')} values: {int(series.count()):,}."

    if any(word in lower_q for word in ["which", "top 3", "top three", "most"]):
        cat = choose_main_category(object_cols)
        if cat and cat in df.columns:
            grouped = df.groupby(cat)[target].sum().sort_values(ascending=False).head(3)
            lines = [f"Top 3 {cat.replace('_', ' ')} by {target.replace('_', ' ')}:"]
            for name, value in grouped.items():
                lines.append(f"- {name}: {value:,.2f}")
            return "\n".join(lines)

    return None


# ── Business report ───────────────────────────────────────────────────────────

def run_storyteller(df, understanding: str, insights: str,
                    cleaning_report: list, stream: bool = False):
    """Return a markdown business report.

    When stream=True, returns a generator suitable for st.write_stream().
    """
    cleaning_text = (
        "\n".join(cleaning_report)
        if cleaning_report
        else "Data was already clean."
    )

    context = (
        f"What the data is about:\n{understanding}\n\n"
        f"Data cleaning done:\n{cleaning_text}\n\n"
        f"Key findings from analysis:\n{insights}\n\n"
        f"Total records after cleaning: {len(df)}"
    )

    report_plan = groq_json_decision(
        """
You are a cautious report planner.
Return only valid JSON with these keys:
{
  "sections": ["sections to include in the final report"],
  "risk_level": "low|medium|high",
  "confidence": 0.0,
  "guardrails": ["rules to avoid unsupported claims"]
}

Keep the plan grounded in the supplied analysis only.
""".strip(),
        context,
        max_tokens=500,
        temperature=0.1,
    )

    plan_text = ""
    if isinstance(report_plan, dict):
        sections = report_plan.get("sections", [])
        guardrails = report_plan.get("guardrails", [])
        plan_text = (
            f"Sections: {', '.join(sections) if sections else 'N/A'}\n"
            f"Guardrails: {', '.join(guardrails) if guardrails else 'N/A'}"
        )

    client = get_groq_client()

    def _generate():
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a short business report for a small business owner based on the analysis below.\n\n"
                        "Use this structure and keep it narrative, not like the quick-insights panel:\n\n"
                        "## 📋 Overview\n"
                        "(2 sentences on what the dataset contains and the overall business context)\n\n"
                        "## 🧹 Data Cleanup\n"
                        "(bullet list of what was cleaned or standardized)\n\n"
                        "## 📈 Business Read\n"
                        "(2–3 bullets explaining the main patterns in plain English, not the same wording as the quick insights)\n\n"
                        "## 🚀 Recommended Next Steps\n"
                        "(3 concrete actions based on the analysis)\n\n"
                        "## ✅ Closing Note\n"
                        "(1 encouraging sentence)\n\n"
                        "Rules: No jargon. Use actual numbers from the findings. Do not copy the quick-insights bullets. "
                        "Max 300 words. Warm, friendly tone."
                    ),
                },
                {"role": "user", "content": f"{context}\n\nReport plan:\n{plan_text}"},
            ],
            max_tokens=600,
            temperature=0.4,
            stream=True,
        )
        for chunk in resp:
            delta = None
            if getattr(chunk, "choices", None):
                choice = chunk.choices[0]
                if getattr(choice, "delta", None):
                    delta = choice.delta.content
            if delta:
                yield delta

    if stream:
        return _generate()

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a short business report for a small business owner based on the analysis below.\n\n"
                    "Use this structure and keep it narrative, not like the quick-insights panel:\n\n"
                    "## 📋 Overview\n"
                    "(2 sentences on what the dataset contains and the overall business context)\n\n"
                    "## 🧹 Data Cleanup\n"
                    "(bullet list of what was cleaned or standardized)\n\n"
                    "## 📈 Business Read\n"
                    "(2–3 bullets explaining the main patterns in plain English, not the same wording as the quick insights)\n\n"
                    "## 🚀 Recommended Next Steps\n"
                    "(3 concrete actions based on the analysis)\n\n"
                    "## ✅ Closing Note\n"
                    "(1 encouraging sentence)\n\n"
                    "Rules: No jargon. Use actual numbers from the findings. Do not copy the quick-insights bullets. "
                    "Max 300 words. Warm, friendly tone."
                ),
            },
            {"role": "user", "content": f"{context}\n\nReport plan:\n{plan_text}"},
        ],
        max_tokens=600,
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()


# ── Q&A ───────────────────────────────────────────────────────────────────────

def handle_question(df, understanding: str, insights: str,
                    question: str, stream: bool = False):
    """Answer a natural language question about the dataframe.

    When stream=True, returns a generator suitable for st.write_stream().
    """
    context = build_data_context(df, understanding)
    full_context = (
        f"{context}\n\n"
        f"KEY INSIGHTS ALREADY FOUND:\n{insights}"
    )

    local_answer = _local_question_answer(df, question)
    if local_answer:
        return _text_stream(local_answer) if stream else local_answer

    answer_plan = groq_json_decision(
        """
You are a cautious analytics decision engine.
Return only valid JSON with these keys:
{
  "answerable": true,
  "reason": "why the question can or cannot be answered from the data",
    "answer_type": "sum|mean|max|min|count|top_n|comparison|correlation|trend|text_summary|unknown",
    "primary_column": "main column to use if relevant",
    "secondary_column": "secondary column if relevant",
    "group_by_column": "column to group by for top_n or comparison",
    "top_n": 3,
  "required_columns": ["columns needed to answer"],
  "calculation_plan": "how to answer using the data",
  "guardrails": ["rules to avoid mistakes"],
  "confidence": 0.0
}

Be strict: if the question needs data that is missing or ambiguous, set "answerable" to false.
""".strip(),
        f"Question: {question}\n\nData context:\n{full_context}",
        max_tokens=500,
        temperature=0.1,
    )

    if isinstance(answer_plan, dict) and not answer_plan.get("answerable", True):
        reason = answer_plan.get("reason", "I cannot answer that confidently from the available data.")
        message = (
            f"I can't answer that confidently from the available data. {reason}. "
            "Try asking about columns or metrics that appear in the dataset."
        )
        return _text_stream(message) if stream else message

    def _fmt(value):
        try:
            return f"{float(value):,.2f}" if float(value) != int(float(value)) else f"{int(float(value)):,}"
        except Exception:
            return str(value)

    def _exact_answer(plan):
        if not isinstance(plan, dict):
            return None

        answer_type = (plan.get("answer_type") or "unknown").lower()
        primary = plan.get("primary_column") or choose_main_numeric([
            c for c in df.select_dtypes(include=["number"]).columns
        ])
        secondary = plan.get("secondary_column")
        group_by = plan.get("group_by_column") or choose_main_category([
            c for c in df.select_dtypes(include=["object"]).columns
        ])
        top_n = plan.get("top_n") or 3

        if answer_type in {"sum", "mean", "max", "min", "count"} and primary in df.columns:
            series = pd.to_numeric(df[primary], errors="coerce")
            if answer_type == "sum":
                result = f"Total {primary.replace('_', ' ')}: {_fmt(series.sum())}."
                return _text_stream(result) if stream else result
            if answer_type == "mean":
                result = f"Average {primary.replace('_', ' ')}: {_fmt(series.mean())}."
                return _text_stream(result) if stream else result
            if answer_type == "max":
                idx = series.idxmax()
                result = f"Highest {primary.replace('_', ' ')}: {_fmt(series.max())} in row {idx + 1}."
                return _text_stream(result) if stream else result
            if answer_type == "min":
                idx = series.idxmin()
                result = f"Lowest {primary.replace('_', ' ')}: {_fmt(series.min())} in row {idx + 1}."
                return _text_stream(result) if stream else result
            result = f"Count of non-missing {primary.replace('_', ' ')} values: {int(series.count()):,}."
            return _text_stream(result) if stream else result

        if answer_type == "top_n" and primary in df.columns and group_by in df.columns:
            metric = pd.to_numeric(df[primary], errors="coerce")
            grouped = (
                df.assign(_metric=metric)
                  .groupby(group_by, dropna=False)["_metric"]
                  .sum()
                  .sort_values(ascending=False)
                  .head(int(top_n))
            )
            lines = [f"Top {int(top_n)} {group_by.replace('_', ' ')} by {primary.replace('_', ' ')}:"]
            for name, value in grouped.items():
                lines.append(f"- {name}: {_fmt(value)}")
            result = "\n".join(lines)
            return _text_stream(result) if stream else result

        if answer_type == "comparison" and primary in df.columns and secondary in df.columns:
            first = pd.to_numeric(df[primary], errors="coerce")
            second = pd.to_numeric(df[secondary], errors="coerce")
            result = (
                f"{primary.replace('_', ' ').title()} average: {_fmt(first.mean())}; "
                f"{secondary.replace('_', ' ').title()} average: {_fmt(second.mean())}."
            )
            return _text_stream(result) if stream else result

        if answer_type == "correlation" and primary in df.columns and secondary in df.columns:
            corr = pd.to_numeric(df[primary], errors="coerce").corr(
                pd.to_numeric(df[secondary], errors="coerce")
            )
            result = (
                f"Correlation between {primary.replace('_', ' ')} and {secondary.replace('_', ' ')}: "
                f"{corr:.2f}."
            )
            return _text_stream(result) if stream else result

        return None

    exact_answer = _exact_answer(answer_plan)
    if exact_answer:
        return _text_stream(exact_answer) if stream else exact_answer

    guardrails = ""
    if isinstance(answer_plan, dict):
        guardrails = answer_plan.get("calculation_plan", "")
        required_columns = answer_plan.get("required_columns", [])
        if required_columns:
            guardrails += f"\nRequired columns: {', '.join(required_columns)}"

    client = get_groq_client()

    def _generate():
        try:
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a friendly business advisor. "
                            "Answer the question using ONLY the actual data provided. "
                            "Be specific — name exact products, categories, or values "
                            "with real numbers from the data. "
                            "Keep it under 100 words. No technical jargon."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"{full_context}\n\n"
                            f"Question: {question}\n\n"
                            f"Decision plan:\n{guardrails}"
                        ),
                    },
                ],
                max_tokens=200,
                temperature=0.3,
                stream=True,
            )
            yielded = False
            for chunk in resp:
                delta = None
                if getattr(chunk, "choices", None):
                    choice = chunk.choices[0]
                    if getattr(choice, "delta", None):
                        delta = choice.delta.content
                    elif getattr(choice, "message", None):
                        delta = getattr(choice.message, "content", None)
                if delta:
                    yielded = True
                    yield delta
            if not yielded:
                fallback = _local_fallback_answer(df, question)
                yield fallback
        except Exception:
            yield _local_fallback_answer(df, question)

    if stream:
        return _generate()

    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly business advisor. "
                        "Answer the question using ONLY the actual data provided. "
                        "Be specific — name exact products, categories, or values "
                        "with real numbers from the data. "
                        "Keep it under 100 words. No technical jargon."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{full_context}\n\n"
                        f"Question: {question}\n\n"
                        f"Decision plan:\n{guardrails}"
                    ),
                },
            ],
            max_tokens=200,
            temperature=0.3,
        )
        answer = resp.choices[0].message.content.strip()
        return answer
    except Exception:
        return _local_fallback_answer(df, question)
