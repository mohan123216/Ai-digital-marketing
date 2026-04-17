import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


def _fallback_ad_generation(
    product_name: str,
    target_audience: Optional[str] = None,
    ad_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate fallback ad content without LLM."""
    # Generate headlines
    headlines = [
        f"Discover {product_name}",
        f"Transform Your Life with {product_name}",
        f"{product_name} - Premium Quality",
        f"Shop {product_name} Today",
        f"Limited Time: {product_name} Offer",
    ]

    # Generate keywords
    base_keywords = []
    for token in (product_name or "").replace("-", " ").split():
        cleaned = token.strip().lower()
        if cleaned and cleaned not in base_keywords:
            base_keywords.append(cleaned)

    if target_audience:
        for token in str(target_audience).replace("-", " ").replace("&", " ").split():
            cleaned = token.strip().lower()
            if cleaned and cleaned not in base_keywords:
                base_keywords.append(cleaned)

    keywords = base_keywords + ["buy", "shop", "online", "exclusive", "limited offer", "best price"]

    # Generate description
    descriptions = [
        f"Experience the excellence of {product_name}. High quality, competitive pricing. Shop now!",
        f"{product_name} - your solution for quality and value. Trusted by thousands. Order today!",
        f"Upgrade your lifestyle with {product_name}. Premium features at an affordable price.",
    ]

    return {
        "headlines": headlines[:3],
        "keywords": keywords[:12],
        "descriptions": descriptions[:2],
    }


def generate_ad_content(
    product_name: str,
    title: Optional[str] = None,
    target_audience: Optional[str] = None,
    ad_text: Optional[str] = None,
    campaign_goal: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate ad headlines, keywords, and descriptions using LLM.
    
    Args:
        product_name: Product/service name
        title: Campaign title
        target_audience: Target audience description
        ad_text: Additional ad copy or marketing text
        campaign_goal: Campaign goal (roi, conversions, traffic, etc.)
    
    Returns:
        Dict with headlines, keywords, and descriptions
    """
    if not settings.GROQ_API_KEY:
        return _fallback_ad_generation(product_name, target_audience, ad_text)

    # Build context for LLM
    context_parts = []
    if title:
        context_parts.append(f"Campaign Title: {title}")
    if product_name:
        context_parts.append(f"Product Name: {product_name}")
    if target_audience:
        context_parts.append(f"Target Audience: {target_audience}")
    if ad_text:
        context_parts.append(f"Marketing Text: {ad_text}")
    if campaign_goal:
        context_parts.append(f"Campaign Goal: {campaign_goal}")

    context = "\n".join(context_parts)

    prompt = (
        "You are an expert digital marketing copywriter. Generate high-performing ad content.\n"
        "Return ONLY valid JSON (no markdown, no extra text) with these keys:\n"
        "- headlines (array of 3-5 compelling headlines, max 30 chars each)\n"
        "- keywords (array of 10-15 high-performing keywords/phrases for targeting)\n"
        "- descriptions (array of 2-3 product descriptions, max 90 chars each)\n"
        "Focus on:\n"
        "  - Action-oriented headlines (use power words)\n"
        "  - Long-tail keywords with high intent\n"
        "  - Clear value propositions in descriptions\n"
        "  - Mobile-friendly copy\n"
        "Ensure all content aligns with the campaign context provided."
    )

    payload = {
        "model": settings.GROQ_MODEL,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": context},
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
        
        # Validate and extract fields
        headlines = parsed.get("headlines", [])
        if not isinstance(headlines, list):
            headlines = []
        headlines = [str(h).strip()[:30] for h in headlines if str(h).strip()]
        
        keywords = parsed.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []
        keywords = [str(k).strip() for k in keywords if str(k).strip()]
        
        descriptions = parsed.get("descriptions", [])
        if not isinstance(descriptions, list):
            descriptions = []
        descriptions = [str(d).strip()[:90] for d in descriptions if str(d).strip()]
        
        # Ensure minimum content
        if not headlines or not keywords or not descriptions:
            return _fallback_ad_generation(product_name, target_audience, ad_text)
        
        return {
            "headlines": headlines[:5],
            "keywords": keywords[:15],
            "descriptions": descriptions[:3],
        }
    
    except Exception as exc:
        logger.error(f"LLM ad generation failed: {exc}")
        return _fallback_ad_generation(product_name, target_audience, ad_text)


def generate_headlines_only(
    product_name: str,
    title: Optional[str] = None,
    target_audience: Optional[str] = None,
    count: int = 5,
) -> List[str]:
    """Generate only headlines using LLM."""
    result = generate_ad_content(
        product_name=product_name,
        title=title,
        target_audience=target_audience,
    )
    headlines = result.get("headlines", [])
    return headlines[:count]


def generate_keywords_only(
    product_name: str,
    title: Optional[str] = None,
    target_audience: Optional[str] = None,
    campaign_goal: Optional[str] = None,
    count: int = 12,
) -> List[str]:
    """Generate only keywords using LLM."""
    result = generate_ad_content(
        product_name=product_name,
        title=title,
        target_audience=target_audience,
        campaign_goal=campaign_goal,
    )
    keywords = result.get("keywords", [])
    return keywords[:count]


def generate_descriptions_only(
    product_name: str,
    ad_text: Optional[str] = None,
    target_audience: Optional[str] = None,
    count: int = 2,
) -> List[str]:
    """Generate only descriptions using LLM."""
    result = generate_ad_content(
        product_name=product_name,
        ad_text=ad_text,
        target_audience=target_audience,
    )
    descriptions = result.get("descriptions", [])
    return descriptions[:count]
