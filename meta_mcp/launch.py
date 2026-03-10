import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

load_dotenv()

STATE_FILE = Path(__file__).resolve().parent / "launched_campaigns.json"
SUPPORTED_CHANNELS = {"Instagram", "Facebook"}


COUNTRY_CODE_MAP = {
    "united states": "US",
    "usa": "US",
    "india": "IN",
    "united kingdom": "GB",
    "uk": "GB",
    "canada": "CA",
    "australia": "AU",
    "germany": "DE",
    "france": "FR",
    "singapore": "SG",
}

FALLBACK_GOAL_CONFIG = {
    "objective": "OUTCOME_TRAFFIC",
    "optimization_goal": "LINK_CLICKS",
    "billing_event": "IMPRESSIONS",
}

GOAL_CONFIG_MAP = {
    "roi": {
        "objective": "OUTCOME_SALES",
        "optimization_goal": "OFFSITE_CONVERSIONS",
        "billing_event": "IMPRESSIONS",
    },
    "conversions": {
        "objective": "OUTCOME_SALES",
        "optimization_goal": "OFFSITE_CONVERSIONS",
        "billing_event": "IMPRESSIONS",
    },
    "leads": {
        "objective": "OUTCOME_LEADS",
        "optimization_goal": "LEAD_GENERATION",
        "billing_event": "IMPRESSIONS",
    },
    "traffic": {
        "objective": "OUTCOME_TRAFFIC",
        "optimization_goal": "LANDING_PAGE_VIEWS",
        "billing_event": "IMPRESSIONS",
    },
    "engagement": {
        "objective": "OUTCOME_ENGAGEMENT",
        "optimization_goal": "POST_ENGAGEMENT",
        "billing_event": "IMPRESSIONS",
    },
    "brand_awareness": {
        "objective": "OUTCOME_AWARENESS",
        "optimization_goal": "REACH",
        "billing_event": "IMPRESSIONS",
    },
}


def _load_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {"launched": {}}
    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "launched" not in data:
            return {"launched": {}}
        return data
    except Exception:
        return {"launched": {}}


def _save_state(state: Dict[str, Any]) -> None:
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _recommendation_key(campaign_id: str, recommendation: Dict[str, Any]) -> str:
    raw = {
        "campaign_id": campaign_id,
        "platform": recommendation.get("platform"),
        "target_location": recommendation.get("target_location"),
        "target_segment": recommendation.get("target_segment"),
        "target_age_group": recommendation.get("target_age_group"),
        "budget": recommendation.get("budget"),
    }
    payload = json.dumps(raw, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _parse_budget_usd(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def _normalize_ad_account_id(ad_account_id: str) -> str:
    ad_account_id = ad_account_id.strip()
    if not ad_account_id.startswith("act_"):
        return f"act_{ad_account_id}"
    return ad_account_id


def _resolve_country_code(location: str) -> str:
    if not location:
        return "US"
    normalized = str(location).strip().lower()
    if len(normalized) == 2 and normalized.isalpha():
        return normalized.upper()
    return COUNTRY_CODE_MAP.get(normalized, "US")


def _parse_age_range(age_group: str) -> Tuple[int, int]:
    default_min, default_max = 25, 45
    if not age_group:
        return default_min, default_max
    text = str(age_group).strip()
    if "-" not in text:
        return default_min, default_max
    try:
        min_age_s, max_age_s = text.split("-", 1)
        min_age = max(18, int(min_age_s))
        max_age = min(65, int(max_age_s))
        if min_age > max_age:
            return default_min, default_max
        return min_age, max_age
    except Exception:
        return default_min, default_max


def _gender_targeting(gender: Any) -> Dict[str, Any]:
    if not gender:
        return {}
    value = str(gender).strip().lower()
    if value == "male":
        return {"genders": [1]}
    if value == "female":
        return {"genders": [2]}
    return {}


def _extract_interest_targets(interests: Any) -> List[Dict[str, str]]:
    """Meta detailed targeting needs IDs; accept plain numeric IDs or 'id:name' strings."""
    if not isinstance(interests, list):
        return []

    parsed: List[Dict[str, str]] = []
    for item in interests:
        text = str(item).strip()
        if not text:
            continue
        if ":" in text:
            maybe_id, maybe_name = text.split(":", 1)
            if maybe_id.strip().isdigit():
                parsed.append({"id": maybe_id.strip(), "name": maybe_name.strip() or maybe_id.strip()})
                continue
        if text.isdigit():
            parsed.append({"id": text, "name": text})
            continue

        match = re.search(r"(\d{5,})", text)
        if match:
            found_id = match.group(1)
            parsed.append({"id": found_id, "name": text})

    return parsed[:10]


def _goal_config(recommendation: Dict[str, Any]) -> Dict[str, str]:
    goal = str(recommendation.get("campaign_goal", "traffic")).strip().lower().replace(" ", "_")
    return GOAL_CONFIG_MAP.get(goal, FALLBACK_GOAL_CONFIG).copy()


def _build_targeting(recommendation: Dict[str, Any]) -> Dict[str, Any]:
    country_code = _resolve_country_code(str(recommendation.get("target_location", "")))
    min_age, max_age = _parse_age_range(str(recommendation.get("target_age_group", "")))
    platform = str(recommendation.get("platform", "")).strip()

    targeting: Dict[str, Any] = {
        "geo_locations": {"countries": [country_code]},
        "age_min": min_age,
        "age_max": max_age,

        # Required for Graph API v24+
        "targeting_automation": {
            "advantage_audience": 0
        }
    }

    if platform == "Instagram":
        targeting.update(
            {
                "publisher_platforms": ["instagram"],
                "instagram_positions": ["stream", "story", "reels"],
            }
        )
    else:
        targeting.update(
            {
                "publisher_platforms": ["facebook"],
                "facebook_positions": ["feed", "story", "marketplace"],
            }
        )

    targeting.update(_gender_targeting(recommendation.get("target_gender")))

    interest_targets = _extract_interest_targets(recommendation.get("target_interests"))
    if interest_targets:
        targeting["flexible_spec"] = [{"interests": interest_targets}]

    return targeting

def _sanitize_name_part(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return re.sub(r"\s+", " ", text)


def _build_names(key: str, recommendation: Dict[str, Any]) -> Tuple[str, str]:
    product_name = _sanitize_name_part(recommendation.get("product_name") or "Product")
    platform = _sanitize_name_part(recommendation.get("platform") or "Meta")
    goal = _sanitize_name_part(recommendation.get("campaign_goal") or "traffic")
    segment = _sanitize_name_part(recommendation.get("target_segment") or "General")
    location = _sanitize_name_part(recommendation.get("target_location") or "US")
    age_group = _sanitize_name_part(recommendation.get("target_age_group") or "25-45")
    predicted_roi = _sanitize_name_part(recommendation.get("predicted_roi") or "NA")

    campaign_name = f"PA | {product_name} | {platform} | {goal} | {location} | ROI{predicted_roi} | {key}"[:255]
    adset_name = f"PA-AS | {segment} | {age_group} | {location} | {platform} | {key}"[:255]
    return campaign_name, adset_name


def _create_meta_assets(
    recommendation: Dict[str, Any],
    key: str,
    ad_account_id: str,
    daily_budget_minor_units: int,
) -> Dict[str, str]:
    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.adaccount import AdAccount

    app_id = os.getenv("META_APP_ID")
    app_secret = os.getenv("META_APP_SECRET")
    access_token = os.getenv("META_ACCESS_TOKEN")

    if not app_id or not app_secret or not access_token:
        raise ValueError("Missing META_APP_ID, META_APP_SECRET, or META_ACCESS_TOKEN in environment.")

    FacebookAdsApi.init(app_id, app_secret, access_token)

    account = AdAccount(_normalize_ad_account_id(ad_account_id))
    campaign_name, adset_name = _build_names(key, recommendation)
    goal_cfg = _goal_config(recommendation)

    campaign_params = {
        "name": campaign_name,
        "objective": goal_cfg["objective"],
        "status": "PAUSED",
        "special_ad_categories": [],
        "is_adset_budget_sharing_enabled": False,
    }
    try:
        campaign = account.create_campaign(params=campaign_params)
    except Exception:
        # Fallback objective for account setups that don't support selected outcome.
        campaign_params["objective"] = FALLBACK_GOAL_CONFIG["objective"]
        campaign = account.create_campaign(params=campaign_params)
    campaign_id = campaign["id"]

    adset_params = {
    "name": adset_name,
    "campaign_id": campaign_id,
    "daily_budget": daily_budget_minor_units,
    "billing_event": goal_cfg["billing_event"],
    "optimization_goal": goal_cfg["optimization_goal"],
    "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    "targeting": _build_targeting(recommendation),
    "status": "PAUSED",
}
    try:
        adset = account.create_ad_set(params=adset_params)
    except Exception:
        # Fallback optimization for accounts lacking prerequisites (pixel/events/etc.).
        adset_params["billing_event"] = FALLBACK_GOAL_CONFIG["billing_event"]
        adset_params["optimization_goal"] = FALLBACK_GOAL_CONFIG["optimization_goal"]
        adset = account.create_ad_set(params=adset_params)

    return {
        "campaign_id": str(campaign_id),
        "adset_id": str(adset["id"]),
        "campaign_name": campaign_name,
        "adset_name": adset_name,
        "objective": campaign_params["objective"],
        "optimization_goal": adset_params["optimization_goal"],
        "billing_event": adset_params["billing_event"],
    }


def launch_selected_recommendation(
    campaign_id: str,
    recommendation: Dict[str, Any],
    dry_run: bool = False,
    ad_account_id_override: str | None = None,
) -> Dict[str, Any]:
    platform = str(recommendation.get("platform", "")).strip()
    if platform not in SUPPORTED_CHANNELS:
        raise ValueError(f"Meta launcher supports only {sorted(SUPPORTED_CHANNELS)}. Selected platform: {platform}")

    state = _load_state()
    key = _recommendation_key(campaign_id, recommendation)
    already = state["launched"].get(key)
    if already:
        return {
            "status": "already_launched",
            "message": "This recommendation has already been launched.",
            "recommendation_key": key,
            "launchable": False,
            "existing": already,
        }

    ad_account_id = ad_account_id_override or os.getenv("META_AD_ACCOUNT_ID")
    if not ad_account_id:
        raise ValueError("Missing META_AD_ACCOUNT_ID in environment.")

    total_budget_usd = _parse_budget_usd(recommendation.get("budget"))
    duration_days = recommendation.get("duration_days")
    try:
        duration_days = int(duration_days) if duration_days else 30
    except Exception:
        duration_days = 30
    duration_days = max(duration_days, 1)

    daily_budget_usd = max(total_budget_usd / duration_days, 1.0)
    # Meta expects minor currency units (e.g., cents/paise)
    daily_budget_minor_units = max(int(round(daily_budget_usd * 100)), 10000) 

    if dry_run:
        campaign_name, adset_name = _build_names(key, recommendation)
        goal_cfg = _goal_config(recommendation)
        resource = {
            "campaign_id": f"dryrun_campaign_{key}",
            "adset_id": f"dryrun_adset_{key}",
            "campaign_name": campaign_name,
            "adset_name": adset_name,
            "objective": goal_cfg["objective"],
            "optimization_goal": goal_cfg["optimization_goal"],
            "billing_event": goal_cfg["billing_event"],
        }
    else:
        resource = _create_meta_assets(
            recommendation=recommendation,
            key=key,
            ad_account_id=ad_account_id,
            daily_budget_minor_units=daily_budget_minor_units,
        )

    launched_at = datetime.utcnow().isoformat() + "Z"
    state["launched"][key] = {
        "campaign_id": campaign_id,
        "platform": platform,
        "meta_campaign_id": resource["campaign_id"],
        "meta_adset_id": resource["adset_id"],
        "launched_at": launched_at,
        "recommendation": recommendation,
        "daily_budget_minor_units": daily_budget_minor_units,
        "daily_budget_usd": round(daily_budget_usd, 2),
        "launchable": False,
    }
    _save_state(state)

    return {
        "status": "launched_dry_run" if dry_run else "launched",
        "message": "Meta launch simulated successfully." if dry_run else f"Campaign launched successfully on {platform}.",
        "recommendation_key": key,
        "platform": platform,
        "meta_campaign_id": resource["campaign_id"],
        "meta_adset_id": resource["adset_id"],
        "campaign_name": resource["campaign_name"],
        "adset_name": resource["adset_name"],
        "daily_budget_usd": round(daily_budget_usd, 2),
        "objective": resource["objective"],
        "optimization_goal": resource["optimization_goal"],
        "billing_event": resource["billing_event"],
        "launchable": False,
    }


def get_recommendation_launch_status(campaign_id: str, recommendation: Dict[str, Any]) -> Dict[str, Any]:
    state = _load_state()
    key = _recommendation_key(campaign_id, recommendation)
    existing = state.get("launched", {}).get(key)
    return {
        "recommendation_key": key,
        "launchable": existing is None,
        "status": "not_launched" if existing is None else "already_launched",
        "existing": existing,
    }


def _main() -> None:
    parser = argparse.ArgumentParser(description="Launch selected Meta recommendation once.")
    parser.add_argument("--campaign-id", type=str, required=True, help="Campaign ID")
    parser.add_argument("--recommendation-json", type=str, required=True, help="Recommendation JSON")
    parser.add_argument("--dry-run", action="store_true", help="Simulate launch without Meta API call")
    args = parser.parse_args()

    result = launch_selected_recommendation(
        campaign_id=args.campaign_id,
        recommendation=json.loads(args.recommendation_json),
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _main()
