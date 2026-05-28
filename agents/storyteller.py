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


# ── Business report ───────────────────────────────────────────────────────────

def run_storyteller(df, understanding: str, insights: str,
                    cleaning_report: list) -> str:
    """Return a markdown business report."""
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
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a short business report for a small business owner "
                    "based on the analysis below.\n\n"
                    "Use this exact structure:\n\n"
                    "## 📋 What We Found\n"
                    "(2 sentences describing the dataset)\n\n"
                    "## 🧹 What We Fixed\n"
                    "(bullet list of data cleaning steps)\n\n"
                    "## 🏆 Top 3 Takeaways\n"
                    "(3 bullet points — specific numbers, plain language)\n\n"
                    "## 🚀 What To Do Next\n"
                    "(3 concrete, actionable recommendations)\n\n"
                    "## ✅ Summary\n"
                    "(1 encouraging sentence)\n\n"
                    "Rules: No jargon. Use actual numbers from the findings. "
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
                    question: str) -> str:
    """Answer a natural language question about the dataframe."""
    context = build_data_context(df, understanding)
    full_context = (
        f"{context}\n\n"
        f"KEY INSIGHTS ALREADY FOUND:\n{insights}"
    )

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
        return (
            f"I can't answer that confidently from the available data. {reason}. "
            "Try asking about columns or metrics that appear in the dataset."
        )

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
                return f"Total {primary.replace('_', ' ')}: {_fmt(series.sum())}."
            if answer_type == "mean":
                return f"Average {primary.replace('_', ' ')}: {_fmt(series.mean())}."
            if answer_type == "max":
                idx = series.idxmax()
                return f"Highest {primary.replace('_', ' ')}: {_fmt(series.max())} in row {idx + 1}."
            if answer_type == "min":
                idx = series.idxmin()
                return f"Lowest {primary.replace('_', ' ')}: {_fmt(series.min())} in row {idx + 1}."
            return f"Count of non-missing {primary.replace('_', ' ')} values: {int(series.count()):,}."

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
            return "\n".join(lines)

        if answer_type == "comparison" and primary in df.columns and secondary in df.columns:
            first = pd.to_numeric(df[primary], errors="coerce")
            second = pd.to_numeric(df[secondary], errors="coerce")
            return (
                f"{primary.replace('_', ' ').title()} average: {_fmt(first.mean())}; "
                f"{secondary.replace('_', ' ').title()} average: {_fmt(second.mean())}."
            )

        if answer_type == "correlation" and primary in df.columns and secondary in df.columns:
            corr = pd.to_numeric(df[primary], errors="coerce").corr(
                pd.to_numeric(df[secondary], errors="coerce")
            )
            return (
                f"Correlation between {primary.replace('_', ' ')} and {secondary.replace('_', ' ')}: "
                f"{corr:.2f}."
            )

        return None

    exact_answer = _exact_answer(answer_plan)
    if exact_answer:
        return exact_answer

    guardrails = ""
    if isinstance(answer_plan, dict):
        guardrails = answer_plan.get("calculation_plan", "")
        required_columns = answer_plan.get("required_columns", [])
        if required_columns:
            guardrails += f"\nRequired columns: {', '.join(required_columns)}"

    client = get_groq_client()
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
    return resp.choices[0].message.content.strip()
