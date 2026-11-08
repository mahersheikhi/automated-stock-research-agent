from __future__ import annotations

from config.settings import settings


def summarize_with_gemini(prompt: str) -> str | None:
    if not settings.gemini_api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return getattr(response, "text", None)
    except Exception as exc:
        return f"Gemini summary unavailable: {exc}"
