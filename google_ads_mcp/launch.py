import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

STATE_FILE = Path(__file__).resolve().parent / "launched_campaigns.json"
DEFAULT_CHANNEL = "Google Ads"


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


def _load_google_client():
    from google.ads.googleads.client import GoogleAdsClient

    login_customer_id = os.getenv("LOGIN_CUSTOMER_ID")
    config = {
        "developer_token": os.getenv("DEVELOPER_TOKEN"),
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "refresh_token": os.getenv("REFRESH_TOKEN"),
        "use_proto_plus": True,
    }
    if login_customer_id:
        config["login_customer_id"] = login_customer_id
    return GoogleAdsClient.load_from_dict(config)


def launch_selected_recommendation(
    campaign_id: str,
    recommendation: Dict[str, Any],
    dry_run: bool = False,
    customer_id_override: str | None = None,
    budget_resource_override: str | None = None,
    login_customer_id_override: str | None = None,
) -> Dict[str, Any]:
    """Launch a Google Ads campaign from a selected recommendation.

    Relaunch is blocked for the same recommendation key.
    """
    platform = recommendation.get("platform", "")
    if platform and platform != DEFAULT_CHANNEL:
        raise ValueError(
            f"Only '{DEFAULT_CHANNEL}' can be launched from this script. Selected platform: {platform}"
        )

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

    customer_id = customer_id_override or os.getenv("CUSTOMER_ID")
    budget_resource = budget_resource_override or os.getenv("BUDGET_RESOURCE_NAME")
    previous_login_customer_id = os.getenv("LOGIN_CUSTOMER_ID")
    if login_customer_id_override:
        os.environ["LOGIN_CUSTOMER_ID"] = login_customer_id_override

    if not customer_id or not budget_resource:
        raise ValueError("Missing CUSTOMER_ID or BUDGET_RESOURCE_NAME in environment.")

    location = recommendation.get("target_location", "Unknown")
    segment = recommendation.get("target_segment", "General")
    age_group = recommendation.get("target_age_group", "Auto")
    budget_usd = _parse_budget_usd(recommendation.get("budget"))
    predicted_roi = recommendation.get("predicted_roi", "N/A")
    predicted_conv = recommendation.get("predicted_conversion_rate", "N/A")

    # Use recommendation metrics in campaign name for traceability.
    campaign_name = (
        f"AI {segment} {location} {age_group} "
        f"ROI{predicted_roi} CR{predicted_conv} B{int(budget_usd)} {key}"
    )[:255]
    try:
        if dry_run:
            resource_name = f"dryrun/customers/{customer_id}/campaigns/{key}"
        else:
            client = _load_google_client()
            campaign_service = client.get_service("CampaignService")
            campaign_operation = client.get_type("CampaignOperation")
            campaign = campaign_operation.create

            campaign.name = campaign_name
            campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
            campaign.status = client.enums.CampaignStatusEnum.ENABLED
            campaign.manual_cpc = client.get_type("ManualCpc")
            campaign.campaign_budget = budget_resource

            campaign.network_settings.target_google_search = True
            campaign.network_settings.target_search_network = True
            campaign.network_settings.target_content_network = False

            campaign.contains_eu_political_advertising = (
                client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
            )

            response = campaign_service.mutate_campaigns(
                customer_id=customer_id,
                operations=[campaign_operation],
            )
            resource_name = response.results[0].resource_name
    finally:
        if login_customer_id_override:
            if previous_login_customer_id:
                os.environ["LOGIN_CUSTOMER_ID"] = previous_login_customer_id
            else:
                os.environ.pop("LOGIN_CUSTOMER_ID", None)
    launched_at = datetime.utcnow().isoformat() + "Z"

    state["launched"][key] = {
        "campaign_id": campaign_id,
        "platform": DEFAULT_CHANNEL,
        "resource_name": resource_name,
        "launched_at": launched_at,
        "recommendation": recommendation,
        "launchable": False,
    }
    _save_state(state)

    return {
        "status": "launched_dry_run" if dry_run else "launched",
        "message": "Campaign launch simulated successfully." if dry_run else "Campaign launched successfully.",
        "recommendation_key": key,
        "resource_name": resource_name,
        "campaign_name": campaign_name,
        "launchable": False,
    }


def get_recommendation_launch_status(campaign_id: str, recommendation: Dict[str, Any]) -> Dict[str, Any]:
    """Return launchability status for a recommendation."""
    state = _load_state()
    key = _recommendation_key(campaign_id, recommendation)
    existing = state.get("launched", {}).get(key)
    return {
        "recommendation_key": key,
        "launchable": existing is None,
        "status": "not_launched" if existing is None else "already_launched",
        "existing": existing,
    }


def build_launch_payload_from_file(payload_file: str, index: int = 0) -> Dict[str, Any]:
    with open(payload_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    campaign_id = data.get("campaign_id", "unknown_campaign")
    recommendations = data.get("recommendations", [])
    if not recommendations:
        raise ValueError("No recommendations found in payload file.")
    if index < 0 or index >= len(recommendations):
        raise IndexError(f"Recommendation index {index} out of range (0..{len(recommendations)-1}).")

    return {
        "campaign_id": campaign_id,
        "recommendation": recommendations[index],
    }


def _main() -> None:
    parser = argparse.ArgumentParser(description="Launch selected Google Ads recommendation once.")
    parser.add_argument("--payload-file", type=str, help="Path to recommendation API response JSON file")
    parser.add_argument("--index", type=int, default=0, help="Recommendation index to launch")
    parser.add_argument("--campaign-id", type=str, help="Campaign ID when passing recommendation JSON directly")
    parser.add_argument("--dry-run", action="store_true", help="Simulate launch without Google Ads API call")
    parser.add_argument(
        "--recommendation-json",
        type=str,
        help="Single recommendation JSON string (must include platform, target fields, budget, predictions)",
    )
    args = parser.parse_args()

    if args.payload_file:
        payload = build_launch_payload_from_file(args.payload_file, args.index)
    elif args.recommendation_json and args.campaign_id:
        payload = {
            "campaign_id": args.campaign_id,
            "recommendation": json.loads(args.recommendation_json),
        }
    else:
        raise ValueError("Provide either --payload-file OR both --campaign-id and --recommendation-json")

    result = launch_selected_recommendation(
        campaign_id=payload["campaign_id"],
        recommendation=payload["recommendation"],
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _main()
