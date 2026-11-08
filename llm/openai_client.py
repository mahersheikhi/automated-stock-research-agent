from __future__ import annotations

from config.settings import settings


def summarize_with_openai(prompt: str) -> str | None:
    if not settings.openai_api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as exc:
        return f"OpenAI summary unavailable: {exc}"
