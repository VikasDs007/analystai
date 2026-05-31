"""Insight generator agent — produces business insights via OpenAI."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import get_llm_client, build_data_context, llm_json_decision


def run_insight_generator(df, understanding: str, use_llm=True) -> str:
    """Return a markdown string with 3 concise business insights."""
    context = build_data_context(df, understanding)

    insight_plan = llm_json_decision(
        """
You are a cautious insight planner.
Return only valid JSON with these keys:
{
  "focus_areas": ["five short analysis angles"],
  "risk_level": "low|medium|high",
  "confidence": 0.0,
  "guardrails": ["rules to avoid hallucinations"]
}

Choose only focus areas that are strongly grounded in the supplied data context.
""".strip(),
        context,
        max_tokens=500,
        temperature=0.1,
    )

    plan_text = ""
    if isinstance(insight_plan, dict):
        focus_areas = insight_plan.get("focus_areas", [])
        guardrails = insight_plan.get("guardrails", [])
        plan_text = (
            f"Focus areas: {', '.join(focus_areas) if focus_areas else 'N/A'}\n"
            f"Guardrails: {', '.join(guardrails) if guardrails else 'N/A'}"
        )

    try:
        client = get_llm_client()
    except Exception as exc:
        return f"(AI unavailable: {exc})"

    resp = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a business analyst writing a short quick-insights panel. "
                    "Using the data summary below, find exactly 3 concise signals.\n\n"
                    f"Plan validation:\n{plan_text}\n\n"
                    "For each insight:\n"
                    "- Start with a number, percentage, or clear pattern from the data\n"
                    "- Explain the signal and why it matters in plain English\n"
                    "- Do not include a full action plan; keep it short and different from the report\n\n"
                    "Format each insight as a single bullet:\n"
                    "- 💡 **[Short headline with a number]** — [one sentence explaining the signal]\n\n"
                    "Rules: No jargon. No technical terms. "
                    "Write for someone who has never seen a spreadsheet. "
                    "Do not repeat the report wording. Max 220 words total."
                ),
            },
            {"role": "user", "content": context},
        ],
        max_tokens=500,
        temperature=0.5,
    )
    return resp.choices[0].message.content.strip()
