import argparse
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()


def _init_meta_api() -> None:
    from facebook_business.api import FacebookAdsApi

    access_token = os.getenv("META_ACCESS_TOKEN")
    app_id = os.getenv("META_APP_ID")
    app_secret = os.getenv("META_APP_SECRET")
    if not access_token or not app_id or not app_secret:
        raise ValueError("Missing META_ACCESS_TOKEN, META_APP_ID, or META_APP_SECRET.")

    FacebookAdsApi.init(app_id, app_secret, access_token)


def _to_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def get_metrics(meta_campaign_ids: List[str], date_preset: str = "last_7d") -> Dict[str, Any]:
    """Fetch Meta (Facebook/Instagram) Insights for one or more campaign IDs.

    Returns a response shaped like Google metrics endpoint for UI compatibility:
      {"campaign_metrics": [...], "ad_metrics": []}
    """
    if not meta_campaign_ids:
        return {"campaign_metrics": [], "ad_metrics": []}

    _init_meta_api()
    from facebook_business.adobjects.campaign import Campaign

    results: List[Dict[str, Any]] = []
    for campaign_id in meta_campaign_ids:
        try:
            campaign = Campaign(str(campaign_id))
            campaign_data = campaign.api_get(fields=["name", "status"])

            insights = campaign.get_insights(
                fields=[
                    "impressions",
                    "clicks",
                    "spend",
                    "reach",
                    "ctr",
                    "cpc",
                    "cpm",
                    "conversions",
                ],
                params={
                    "date_preset": date_preset,
                    "level": "campaign",
                },
            )

            # Aggregate if API returns multiple rows
            agg = {
                "impressions": 0,
                "clicks": 0,
                "spend": 0.0,
                "reach": 0,
                "conversions": 0.0,
            }
            ctr_vals: List[float] = []
            cpc_vals: List[float] = []
            cpm_vals: List[float] = []

            for row in insights:
                agg["impressions"] += _to_int(row.get("impressions"))
                agg["clicks"] += _to_int(row.get("clicks"))
                agg["spend"] += _to_float(row.get("spend"))
                agg["reach"] += _to_int(row.get("reach"))
                agg["conversions"] += _to_float(row.get("conversions"))
                ctr_vals.append(_to_float(row.get("ctr")))
                cpc_vals.append(_to_float(row.get("cpc")))
                cpm_vals.append(_to_float(row.get("cpm")))

            results.append(
                {
                    "platform": "Meta Ads",
                    "meta_campaign_id": str(campaign_id),
                    "campaign_name": campaign_data.get("name"),
                    "status": campaign_data.get("status"),
                    "impressions": agg["impressions"],
                    "clicks": agg["clicks"],
                    "reach": agg["reach"],
                    "spend": round(agg["spend"], 4),
                    "conversions": agg["conversions"],
                    "ctr": (sum(ctr_vals) / len(ctr_vals)) if ctr_vals else 0.0,
                    "cpc": (sum(cpc_vals) / len(cpc_vals)) if cpc_vals else 0.0,
                    "cpm": (sum(cpm_vals) / len(cpm_vals)) if cpm_vals else 0.0,
                }
            )
        except Exception:
            # Partial failure: keep collecting other campaigns
            continue

    return {"campaign_metrics": results, "ad_metrics": []}


def _main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Meta campaign insights (last 7 days by default).")
    parser.add_argument("--campaign-id", action="append", required=True, help="Meta campaign ID (repeatable).")
    parser.add_argument("--date-preset", default="last_7d", help="Meta date_preset (e.g. today, yesterday, last_30d)")
    args = parser.parse_args()

    data = get_metrics(args.campaign_id, date_preset=args.date_preset)
    import json

    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    _main()
