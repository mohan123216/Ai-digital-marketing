"""
google_ads_mcp/optimize.py
──────────────────────────────────────────────────────────────────────────────
Campaign Optimization Agent for Google Ads.

Decision Logic:
  • ROI_actual > ROI_pred AND CR_actual > CR_pred  → Increase budget
  • ROI_actual < ROI_pred (moderate)               → Reduce budget
  • ROI_actual < 0.5 × ROI_pred                   → Pause campaign
  • CTR < 2%                                       → Flag wrong audience/creative (manual action needed)
  • CTR high but CR low                            → Flag landing page mismatch (manual action needed)

Budget Adjustment:
  New Budget = Old Budget × (1 + Adjustment Rate)
  Where adjustment rate depends on the performance gap.

All budget/status mutations are applied only when dry_run=False AND action is programmatic.
Creative/targeting issues require manual intervention and are clearly flagged as such.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── constants ──────────────────────────────────────────────────────────────────
MIN_DAILY_BUDGET_MICROS = 1_000_000   # $1.00 minimum
MAX_ADJUSTMENT_RATE     = 0.30        # never move budget > 30% in one step
LOW_CTR_THRESHOLD       = 0.02        # 2 %
HIGH_CTR_THRESHOLD      = 0.05        # 5 %


# ── helpers ────────────────────────────────────────────────────────────────────

def _get_client():
    """Return an authenticated GoogleAdsClient."""
    from google.ads.googleads.client import GoogleAdsClient
    config = {
        "developer_token":  os.getenv("DEVELOPER_TOKEN"),
        "client_id":        os.getenv("CLIENT_ID"),
        "client_secret":    os.getenv("CLIENT_SECRET"),
        "refresh_token":    os.getenv("REFRESH_TOKEN"),
        "use_proto_plus":   True,
    }
    login_cid = os.getenv("LOGIN_CUSTOMER_ID")
    if login_cid:
        config["login_customer_id"] = login_cid
    return GoogleAdsClient.load_from_dict(config)


def _get_customer_id() -> str:
    cid = os.getenv("CUSTOMER_ID", "")
    return cid.replace("-", "")


def _campaign_resource(numeric_id: str) -> str:
    return f"customers/{_get_customer_id()}/campaigns/{numeric_id}"


def _budget_resource_for_campaign(client, numeric_campaign_id: str) -> Optional[str]:
    """Fetch the budget resource name linked to this campaign."""
    service = client.get_service("GoogleAdsService")
    query = f"""
        SELECT campaign.id, campaign.campaign_budget
        FROM campaign
        WHERE campaign.id = {numeric_campaign_id}
        LIMIT 1
    """
    try:
        rows = list(service.search(customer_id=_get_customer_id(), query=query))
        if rows:
            return rows[0].campaign.campaign_budget
    except Exception as exc:
        logger.warning(f"Failed to get budget resource for campaign {numeric_campaign_id}: {exc}")
    return None


def _get_current_budget_micros(client, budget_resource: str) -> int:
    """Get current amount_micros for a campaign budget."""
    service = client.get_service("GoogleAdsService")
    query = f"""
        SELECT campaign_budget.amount_micros
        FROM campaign_budget
        WHERE campaign_budget.resource_name = '{budget_resource}'
        LIMIT 1
    """
    try:
        rows = list(service.search(customer_id=_get_customer_id(), query=query))
        if rows:
            return rows[0].campaign_budget.amount_micros
    except Exception as exc:
        logger.warning(f"Failed to get current budget: {exc}")
    return 0


# ── Google Ads mutations ───────────────────────────────────────────────────────

def _adjust_budget(
    campaign_resource_name: str,
    adjustment_rate: float,
    override_new_budget_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Increase or decrease the daily budget for the campaign.
    If override_new_budget_usd is provided, set to that exact value instead.
    Returns info dict with old/new values.
    """
    numeric_id = campaign_resource_name.split("/")[-1]
    client = _get_client()
    budget_resource = _budget_resource_for_campaign(client, numeric_id)
    if not budget_resource:
        return {"error": "Budget resource not found"}

    current_micros = _get_current_budget_micros(client, budget_resource)
    if current_micros <= 0:
        return {"error": "Could not read current budget"}

    if override_new_budget_usd is not None:
        # User-specified exact budget override
        new_micros = int(round(override_new_budget_usd * 1_000_000))
    else:
        new_micros = int(current_micros * (1 + adjustment_rate))

    # Google Ads requires micros to be a multiple of 10,000 (1 cent)
    new_micros = round(new_micros / 10000) * 10000
    new_micros = max(new_micros, MIN_DAILY_BUDGET_MICROS)

    budget_service = client.get_service("CampaignBudgetService")
    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.update
    budget.resource_name = budget_resource
    budget.amount_micros = new_micros

    from google.api_core import protobuf_helpers
    client.copy_from(
        budget_op.update_mask,
        protobuf_helpers.field_mask(None, budget._pb),
    )

    response = budget_service.mutate_campaign_budgets(
        customer_id=_get_customer_id(),
        operations=[budget_op],
    )

    old_usd  = current_micros / 1_000_000
    new_usd  = new_micros     / 1_000_000
    return {
        "old_daily_budget_usd": round(old_usd, 2),
        "new_daily_budget_usd": round(new_usd, 2),
        "adjustment_pct": round(((new_micros - current_micros) / current_micros) * 100, 1),
        "budget_resource": budget_resource,
        "user_override": override_new_budget_usd is not None,
    }


def _set_campaign_status(campaign_resource_name: str, status: str) -> Dict[str, Any]:
    """
    Set campaign status: ENABLED | PAUSED | REMOVED.
    Returns dict with result.
    """
    client = _get_client()
    campaign_service = client.get_service("CampaignService")
    campaign_op = client.get_type("CampaignOperation")
    campaign = campaign_op.update
    campaign.resource_name = campaign_resource_name

    status_enum = client.enums.CampaignStatusEnum.CampaignStatus.Value(status)
    campaign.status = status_enum

    from google.api_core import protobuf_helpers
    client.copy_from(
        campaign_op.update_mask,
        protobuf_helpers.field_mask(None, campaign._pb),
    )

    campaign_service.mutate_campaigns(
        customer_id=_get_customer_id(),
        operations=[campaign_op],
    )
    return {"new_status": status, "campaign_resource": campaign_resource_name}


# ── performance gap analysis ───────────────────────────────────────────────────

def _compute_adjustment_rate(roi_gap: float, cr_gap: float) -> float:
    """
    Map performance gap to a budget adjustment rate (capped at MAX_ADJUSTMENT_RATE).
    Positive rate → increase; negative → decrease.
    """
    if roi_gap > 0.5 and cr_gap > 0.03:
        rate = 0.25
    elif roi_gap > 0.3 and cr_gap > 0.01:
        rate = 0.15
    elif roi_gap > 0.1:
        rate = 0.10
    elif roi_gap < -0.5:
        rate = -0.25
    elif roi_gap < -0.2:
        rate = -0.15
    elif roi_gap < -0.1:
        rate = -0.10
    else:
        rate = 0.0
    return max(-MAX_ADJUSTMENT_RATE, min(MAX_ADJUSTMENT_RATE, rate))


def _compute_actual_roi(actual_metrics: Dict[str, Any]) -> float:
    """Estimate ROI from cost and conversion value (simplified: value = conversions × avg_order)."""
    cost = actual_metrics.get("cost", 0) or actual_metrics.get("cost_usd", 0) or 0
    conversions = actual_metrics.get("conversions", 0) or 0
    # Without revenue data we use a proxy: conversions per dollar spent × 10 (normalised scale)
    if cost <= 0:
        return 0.0
    return round((conversions / cost) * 10, 4)


def _compute_actual_cr(actual_metrics: Dict[str, Any]) -> float:
    """Conversion rate = conversions / clicks (0–1 scale)."""
    clicks = actual_metrics.get("clicks", 0) or 0
    conversions = actual_metrics.get("conversions", 0) or 0
    if clicks <= 0:
        return 0.0
    return round(conversions / clicks, 6)


# ── main optimiser ─────────────────────────────────────────────────────────────

def optimize_campaign(
    campaign_resource_name: str,
    actual_campaign_metrics: List[Dict[str, Any]],
    predicted_roi: float,
    predicted_conversion_rate_pct: float,
    dry_run: bool = False,
    user_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the full optimisation loop for one Google Ads campaign.

    Parameters
    ----------
    campaign_resource_name : str
        Full Google Ads resource name, e.g. "customers/123/campaigns/456".
    actual_campaign_metrics : list[dict]
        Row(s) returned by get_metrics – aggregated over last 7 days.
    predicted_roi : float
        The AI-predicted ROI stored at launch time.
    predicted_conversion_rate_pct : float
        Predicted conversion rate in percent (e.g. 3.5 for 3.5%).
    dry_run : bool
        If True, compute decisions but do NOT call the Google Ads API.
    user_overrides : dict, optional
        When applying (dry_run=False), user can provide:
          - "new_budget_usd": override the computed budget with a specific dollar value
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    actions:  List[Dict[str, Any]] = []
    warnings: List[str] = []
    user_overrides = user_overrides or {}

    # ── aggregate actual metrics across all rows for this campaign ──────────
    agg: Dict[str, float] = {
        "impressions": 0, "clicks": 0, "conversions": 0,
        "cost": 0, "ctr": 0, "avg_cpc": 0,
    }
    for row in actual_campaign_metrics:
        agg["impressions"]  += row.get("impressions",  0) or 0
        agg["clicks"]       += row.get("clicks",       0) or 0
        agg["conversions"]  += row.get("conversions",  0) or 0
        agg["cost"]         += row.get("cost",         0) or row.get("cost_usd", 0) or 0
    if agg["impressions"] > 0:
        agg["ctr"] = agg["clicks"] / agg["impressions"]
    if agg["clicks"] > 0:
        agg["avg_cpc"] = agg["cost"] / agg["clicks"]

    # ── derived actuals ──────────────────────────────────────────────────────
    actual_roi = _compute_actual_roi(agg)
    actual_cr  = _compute_actual_cr(agg)
    predicted_cr = predicted_conversion_rate_pct / 100.0

    roi_gap = actual_roi - predicted_roi
    cr_gap  = actual_cr  - predicted_cr

    analysis = {
        "actual_roi":           actual_roi,
        "predicted_roi":        predicted_roi,
        "roi_gap":              round(roi_gap, 4),
        "actual_cr_pct":        round(actual_cr * 100, 4),
        "predicted_cr_pct":     predicted_conversion_rate_pct,
        "cr_gap":               round(cr_gap * 100, 4),
        "actual_ctr_pct":       round(agg["ctr"] * 100, 4),
        "actual_impressions":   int(agg["impressions"]),
        "actual_clicks":        int(agg["clicks"]),
        "actual_conversions":   int(agg["conversions"]),
        "actual_cost_usd":      round(agg["cost"], 2),
        "avg_cpc_usd":          round(agg["avg_cpc"], 4),
    }

    # ── insufficient data guard ──────────────────────────────────────────────
    if agg["impressions"] < 100 or agg["cost"] < 1:
        return {
            "timestamp": timestamp,
            "campaign_resource_name": campaign_resource_name,
            "dry_run": dry_run,
            "status": "insufficient_data",
            "message": (
                f"Not enough data yet to optimise. "
                f"Impressions: {int(agg['impressions'])}, Cost: ${agg['cost']:.2f}. "
                "Campaigns need at least 100 impressions and $1 spend before optimisation runs."
            ),
            "analysis": analysis,
            "actions": [],
            "warnings": warnings,
        }

    # ── decision tree ────────────────────────────────────────────────────────

    # 1. Both ROI and CR above predicted → scale up
    if actual_roi > predicted_roi and actual_cr > predicted_cr:
        adj_rate = _compute_adjustment_rate(roi_gap, cr_gap)

        # Best guess for what the new budget would be (for UI display)
        # We can't know exact value in dry_run without querying ads, so we provide the rate
        action: Dict[str, Any] = {
            "action":   "increase_budget",
            "reason":   (
                f"ROI {actual_roi:.2f}x > predicted {predicted_roi:.2f}x "
                f"(+{roi_gap:.2f}), CR {actual_cr*100:.2f}% > predicted {predicted_cr*100:.2f}%"
            ),
            "adjustment_rate": adj_rate,
            "programmatic": True,  # Can be auto-applied
        }
        if not dry_run:
            try:
                override_budget = user_overrides.get("new_budget_usd")
                result = _adjust_budget(campaign_resource_name, adj_rate, override_budget)
                action["api_result"] = result
            except Exception as exc:
                action["api_error"] = str(exc)
        actions.append(action)

    # 2. ROI well below predicted → consider pausing
    elif actual_roi < predicted_roi * 0.5 and agg["impressions"] >= 500:
        action = {
            "action": "pause_campaign",
            "reason": (
                f"Actual ROI {actual_roi:.2f}x is below 50% of predicted "
                f"{predicted_roi:.2f}x. Campaign paused to stop budget waste."
            ),
            "programmatic": True,  # Can be auto-applied
        }
        if not dry_run:
            try:
                result = _set_campaign_status(campaign_resource_name, "PAUSED")
                action["api_result"] = result
            except Exception as exc:
                action["api_error"] = str(exc)
        actions.append(action)

    # 3. ROI moderately below predicted → reduce budget
    elif actual_roi < predicted_roi:
        adj_rate = _compute_adjustment_rate(roi_gap, cr_gap)
        action = {
            "action":   "reduce_budget",
            "reason":   (
                f"Actual ROI {actual_roi:.2f}x < predicted {predicted_roi:.2f}x "
                f"(gap: {roi_gap:.2f})"
            ),
            "adjustment_rate": adj_rate,
            "programmatic": True,  # Can be auto-applied
        }
        if not dry_run:
            try:
                override_budget = user_overrides.get("new_budget_usd")
                result = _adjust_budget(campaign_resource_name, adj_rate, override_budget)
                action["api_result"] = result
            except Exception as exc:
                action["api_error"] = str(exc)
        actions.append(action)

    else:
        actions.append({
            "action": "no_change",
            "reason": "Performance within expected range. No budget adjustment needed.",
            "programmatic": False,
        })

    # 4. Low CTR diagnostic — requires manual creative/targeting changes
    if agg["ctr"] < LOW_CTR_THRESHOLD and agg["impressions"] >= 200:
        actions.append({
            "action":           "flag_low_ctr",
            "reason":           f"CTR is {agg['ctr']*100:.2f}% (threshold: {LOW_CTR_THRESHOLD*100:.0f}%). "
                                "Likely wrong audience or poor creative.",
            "recommendation":   "Review and update audience targeting segments and ad creative. "
                                "Consider A/B testing different headlines and descriptions.",
            "programmatic":     False,  # Requires manual creative change
            "manual_action":    "Change your ad creatives and/or audience targeting in Google Ads.",
        })

    # 5. High CTR but low conversion → landing page — requires manual page changes
    if agg["ctr"] >= HIGH_CTR_THRESHOLD and actual_cr < predicted_cr * 0.5:
        actions.append({
            "action":           "flag_landing_page",
            "reason":           (
                f"CTR is high ({agg['ctr']*100:.2f}%) but conversion rate "
                f"{actual_cr*100:.2f}% < 50% of predicted {predicted_cr*100:.2f}%."
            ),
            "recommendation":   "Landing page offer doesn't match ad promise. "
                                "Review page copy, CTA, and load time.",
            "programmatic":     False,  # Requires manual landing page change
            "manual_action":    "Update your landing page design, copy, CTA, or offer to match ad intent.",
        })

    final_status = "optimized" if actions else "no_action"
    if any(a["action"] == "pause_campaign" for a in actions):
        final_status = "paused"

    return {
        "timestamp":                timestamp,
        "campaign_resource_name":   campaign_resource_name,
        "dry_run":                  dry_run,
        "status":                   final_status,
        "analysis":                 analysis,
        "actions":                  actions,
        "warnings":                 warnings,
    }
