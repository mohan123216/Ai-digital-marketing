import json
import logging
from typing import Any, Dict, List

import httpx

from config import settings

logger = logging.getLogger(__name__)


def _fallback_summary(
    top_recommendation: Dict[str, Any],
    all_recommendations: List[Dict[str, Any]],
    product_name: str,
    product_type: str,
) -> Dict[str, Any]:
    audience = (
        f"{top_recommendation.get('target_segment', 'General audience')} "
        f"in {top_recommendation.get('target_location', 'primary markets')}"
    )
    predicted_platform = top_recommendation.get("platform", "Unknown")
    predicted_roi = top_recommendation.get("predicted_roi", "N/A")
    predicted_conversion = top_recommendation.get("predicted_conversion_rate", "N/A")
    budget = top_recommendation.get("budget", "N/A")

    ml_summary = (
        f"Best channel is {predicted_platform} targeting {audience}. "
        f"Expected ROI is {predicted_roi}x with predicted conversion {predicted_conversion}%. "
        f"Suggested budget is {budget}."
    )
    if product_name or product_type:
        ml_summary += f" Product context: {product_name or 'Unknown product'} ({product_type or 'general type'})."

    base_keywords = []
    for token in (product_name or "").replace("-", " ").split():
        cleaned = token.strip().lower()
        if cleaned and cleaned not in base_keywords:
            base_keywords.append(cleaned)
    for token in (product_type or "").replace("&", " ").replace("-", " ").split():
        cleaned = token.strip().lower()
        if cleaned and cleaned not in base_keywords:
            base_keywords.append(cleaned)
    base_keywords = base_keywords[:6] or ["performance", "conversion", "audience"]

    suggestions = [
        f"{predicted_platform} ad keywords: {', '.join(base_keywords + ['high intent', 'buy now'])}",
        f"{predicted_platform} audience keywords: {', '.join(base_keywords + ['quality', 'trusted'])}",
        f"Conversion keywords for {budget}: {', '.join(base_keywords + ['offer', 'limited time'])}",
    ]
    if all_recommendations:
        platform_terms = [str(item.get("platform", "")).lower() for item in all_recommendations]
        platform_terms = [p for p in platform_terms if p]
        if platform_terms:
            suggestions.append(f"Platform-specific keywords: {', '.join(platform_terms + base_keywords[:3])}")

    return {"llm_summary": ml_summary, "keyword_suggestions": suggestions[:5]}


def summarize_ml_result(
    recommendation_result: Dict[str, Any],
    product_name: str = "",
    product_type: str = "",
) -> Dict[str, Any]:
    top = recommendation_result.get("top_recommendation") or {}
    all_recommendations = recommendation_result.get("recommendations") or []

    if not settings.GROQ_API_KEY:
        return _fallback_summary(top, all_recommendations, product_name, product_type)

    prompt = (
        "You are a marketing strategist. Summarize the ML output for a campaign planner UI.\n"
        "Return strict JSON with keys: llm_summary (string), keyword_suggestions (array of 8-15 short ad keywords/phrases).\n"
        "Use all_recommendations and include these fields in summary: predicted platform, targeted audience, predicted ROI, budget, predicted conversions.\n"
        "Generate keyword suggestions automatically from product_name and product_type.\n"
        "Keep summary concise (max 90 words)."
    )

    payload = {
        "model": settings.GROQ_MODEL,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "top_recommendation": top,
                        "all_recommendations": all_recommendations,
                        "product_name": product_name,
                        "product_type": product_type,
                    }
                ),
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(settings.GROQ_BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        llm_summary = str(parsed.get("llm_summary", "")).strip()
        keyword_suggestions = parsed.get("keyword_suggestions", [])
        if not isinstance(keyword_suggestions, list):
            keyword_suggestions = []
        keyword_suggestions = [str(item).strip() for item in keyword_suggestions if str(item).strip()]
        if not llm_summary:
            return _fallback_summary(top, all_recommendations, product_name, product_type)
        if not keyword_suggestions:
            keyword_suggestions = _fallback_summary(top, all_recommendations, product_name, product_type)["keyword_suggestions"]
        return {"llm_summary": llm_summary, "keyword_suggestions": keyword_suggestions[:15]}
    except Exception as exc:
        logger.error(f"Groq summarization failed: {exc}")
        return _fallback_summary(top, all_recommendations, product_name, product_type)
