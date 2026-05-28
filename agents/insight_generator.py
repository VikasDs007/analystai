"""Insight generator agent — produces 5 business insights using Groq LLM."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import get_groq_client, build_data_context, groq_json_decision


def run_insight_generator(df, understanding: str) -> str:
    """Return a markdown string with 5 business insights."""
    context = build_data_context(df, understanding)

    insight_plan = groq_json_decision(
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

    client = get_groq_client()
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a business advisor talking to a small business owner. "
                    "Using the data summary below, find exactly 5 clear insights.\n\n"
                    f"Plan validation:\n{plan_text}\n\n"
                    "For each insight:\n"
                    "- Start with a specific number or percentage from the data\n"
                    "- Explain what it MEANS for the business in plain English\n"
                    "- Suggest one concrete action to take\n\n"
                    "Format each insight as:\n"
                    "💡 **[Bold one-line finding with a number]**\n"
                    "[2 sentences: what it means + what to do]\n\n"
                    "Rules: No jargon. No technical terms. "
                    "Write for someone who has never seen a spreadsheet. "
                    "Max 400 words total."
                ),
            },
            {"role": "user", "content": context},
        ],
        max_tokens=800,
        temperature=0.5,
    )
    return resp.choices[0].message.content.strip()
