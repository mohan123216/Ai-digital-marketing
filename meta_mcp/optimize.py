"""
meta_mcp/optimize.py
──────────────────────────────────────────────────────────────────────────────
Campaign Optimization Agent for Meta Ads (Facebook/Instagram).

Decision Logic (mirrors Google Ads logic):
  • ROI_actual > ROI_pred AND CR_actual > CR_pred  → Increase budget
  • ROI_actual < ROI_pred (moderate)               → Reduce budget
  • ROI_actual < 0.5 × ROI_pred                   → Pause campaign
  • CTR < 2%                                       → Flag wrong audience/creative (manual)
  • CTR high but CR low                            → Flag creative/offer mismatch (manual)

Budget Adjustment:
  New Budget = Old Budget × (1 + Adjustment Rate)

Only budget and status changes are programmatic. Creative/audience changes require manual action.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── constants ──────────────────────────────────────────────────────────────────
MIN_DAILY_BUDGET_CENTS  = 1000     # $10.00 minimum (Meta API units = cents)
MAX_ADJUSTMENT_RATE     = 0.30
LOW_CTR_THRESHOLD       = 0.02     # 2%
HIGH_CTR_THRESHOLD      = 0.05     # 5%

# Cache of Meta-enforced minimum daily budgets per AdSet (minor units of ad account currency).
# This avoids repeatedly attempting budgets below the platform minimum (e.g., error_subcode 1885272).
_MIN_DAILY_BUDGET_FLOOR_BY_ADSET_ID: dict[str, int] = {}


def _safe_call(obj: object, name: str) -> str | int | None:
    """Safely call a method if present (used for FacebookRequestError helpers)."""
    fn = getattr(obj, name, None)
    if callable(fn):
        try:
            return fn()
        except Exception:
            return None
    return None


# ── Meta helpers ───────────────────────────────────────────────────────────────

def _get_meta_api():
    from facebook_business.api import FacebookAdsApi
    app_id      = os.getenv("META_APP_ID")
    app_secret  = os.getenv("META_APP_SECRET")
    access_token = os.getenv("META_ACCESS_TOKEN")
    if not all([app_id, app_secret, access_token]):
        raise ValueError("Missing META_APP_ID, META_APP_SECRET, or META_ACCESS_TOKEN.")
    FacebookAdsApi.init(app_id, app_secret, access_token)
    return FacebookAdsApi.get_default_api()


def _normalize_ad_account_id(ad_account_id: str) -> str:
    ad_account_id = str(ad_account_id).strip()
    if not ad_account_id.startswith("act_"):
        return f"act_{ad_account_id}"
    return ad_account_id


# ── Meta API mutations ─────────────────────────────────────────────────────────

def _adjust_meta_adset_budget(
    meta_adset_id: str,
    current_daily_budget_cents: int,
    adjustment_rate: float,
    override_new_budget_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Adjust the Meta AdSet daily budget.
    Meta uses minor currency units (cents for USD: $1.00 = 100 cents).
    """
    from facebook_business.adobjects.adset import AdSet
    _get_meta_api()

    def _is_budget_too_low_error(exc: Exception) -> bool:
        subcode = _safe_call(exc, "api_error_subcode")
        if isinstance(subcode, int) and subcode == 1885272:
            return True

        title = _safe_call(exc, "api_error_user_title")
        if isinstance(title, str) and "budget is too low" in title.lower():
            return True

        user_msg = _safe_call(exc, "api_error_user_msg")
        if isinstance(user_msg, str) and "budget must be more than" in user_msg.lower():
            return True

        text = str(exc) or ""
        return ("Budget is too low" in text) or ("1885272" in text and "daily_budget" in text)

    def _parse_min_budget_minor_units_from_error(exc: Exception) -> int | None:
        """Extract the minimum required budget from the API error user message, in minor units."""
        import re

        user_msg = _safe_call(exc, "api_error_user_msg")
        if not isinstance(user_msg, str) or not user_msg.strip():
            # Fallback to the general error message, but avoid parsing the full string with version numbers etc.
            user_msg = _safe_call(exc, "api_error_message")  # type: ignore[assignment]

        text = (user_msg or "").strip()
        if not text:
            # Fallback to stringified exception; try to anchor on the specific phrase
            text = str(exc) or ""

        if not text:
            return None

        # Example: "Your ad set budget must be more than ₹92.13 ..."
        # Prefer anchored parse to avoid matching unrelated numbers (API version, IDs).
        m = re.search(
            r"budget must be more than\\s+[^0-9]*([0-9][0-9,]*\\.?[0-9]{0,2})",
            text,
            re.IGNORECASE,
        )
        if not m:
            # Fallback: first numeric token in message
            m = re.search(r"([0-9][0-9,]*\\.[0-9]{1,2}|[0-9][0-9,]*)", text)
        if not m:
            return None

        amount_s = m.group(1).replace(",", "")
        if not amount_s:
            return None

        if "." in amount_s:
            whole, frac = amount_s.split(".", 1)
            frac = (frac + "00")[:2]
            try:
                return int(whole) * 100 + int(frac)
            except Exception:
                return None

        try:
            return int(amount_s) * 100
        except Exception:
            return None

    adset = AdSet(meta_adset_id)

    def _default_min_floor_minor_units_for_adset() -> int:
        """Match launch behavior: ensure budget >= a safe platform/currency floor.

        Meta minimum differs by ad account currency. We best-effort detect currency:
          - INR -> 10000 (₹100.00) like launcher (avoids 1885272 for ~₹92.13 minimums)
          - otherwise -> MIN_DAILY_BUDGET_CENTS (keeps existing $10-style floor for USD accounts)
        """
        try:
            adset.remote_read(fields=["account_id"])
            account_id = adset.get("account_id")
            if account_id:
                from facebook_business.adobjects.adaccount import AdAccount

                acct = AdAccount(_normalize_ad_account_id(str(account_id)))
                data = acct.api_get(fields=["currency"])
                currency = (data.get("currency") or "").upper()
                if currency == "INR":
                    return 10000
        except Exception:
            pass
        return MIN_DAILY_BUDGET_CENTS

    old_budget_cents = int(current_daily_budget_cents or 0)
    if old_budget_cents <= 0:
        try:
            adset.remote_read(fields=["daily_budget", "account_id"])
            old_budget_cents = int(adset.get("daily_budget", 0) or 0)
        except Exception:
            old_budget_cents = 0

    if override_new_budget_usd is not None:
        new_budget_cents = max(int(round(override_new_budget_usd * 100)), MIN_DAILY_BUDGET_CENTS)
    else:
        if old_budget_cents <= 0:
            raise ValueError("Unable to read current Meta AdSet daily budget; provide user_overrides.new_budget_usd to apply.")
        new_budget_cents = max(
            int(round(old_budget_cents * (1 + adjustment_rate))),
            MIN_DAILY_BUDGET_CENTS,
        )

    learned_floor = _MIN_DAILY_BUDGET_FLOOR_BY_ADSET_ID.get(str(meta_adset_id), 0) or 0
    if learned_floor > 0:
        new_budget_cents = max(new_budget_cents, learned_floor)
    else:
        # Preemptively set a reasonable floor (mirrors launch flow) to avoid repeated "budget too low" errors.
        learned_floor = _default_min_floor_minor_units_for_adset()
        _MIN_DAILY_BUDGET_FLOOR_BY_ADSET_ID[str(meta_adset_id)] = learned_floor
        new_budget_cents = max(new_budget_cents, learned_floor)

    requested_budget_minor_units = new_budget_cents
    try:
        adset.update({"daily_budget": new_budget_cents})
        adset.remote_update()
    except Exception as exc:
        if not _is_budget_too_low_error(exc):
            raise

        min_required = _parse_min_budget_minor_units_from_error(exc)
        if not min_required:
            raise

        bumped_budget = max(new_budget_cents, min_required + 1, MIN_DAILY_BUDGET_CENTS)
        _MIN_DAILY_BUDGET_FLOOR_BY_ADSET_ID[str(meta_adset_id)] = bumped_budget
        adset.update({"daily_budget": bumped_budget})
        adset.remote_update()
        new_budget_cents = bumped_budget
    else:
        if learned_floor > 0:
            _MIN_DAILY_BUDGET_FLOOR_BY_ADSET_ID[str(meta_adset_id)] = max(learned_floor, int(new_budget_cents))

    response: Dict[str, Any] = {
        "new_daily_budget_usd": round(new_budget_cents / 100.0, 2),
        "meta_adset_id": meta_adset_id,
        "user_override": override_new_budget_usd is not None,
        "requested_daily_budget_minor_units": int(requested_budget_minor_units),
        "applied_daily_budget_minor_units": int(new_budget_cents),
        "min_daily_budget_floor_minor_units": int(_MIN_DAILY_BUDGET_FLOOR_BY_ADSET_ID.get(str(meta_adset_id), 0) or 0),
    }
    if old_budget_cents > 0:
        response["old_daily_budget_usd"] = round(old_budget_cents / 100.0, 2)
        response["adjustment_pct"] = round(((new_budget_cents - old_budget_cents) / old_budget_cents) * 100, 1)
    return response


def _set_meta_campaign_status(meta_campaign_id: str, status: str) -> Dict[str, Any]:
    """
    Set Meta campaign status to ACTIVE or PAUSED.
    """
    from facebook_business.adobjects.campaign import Campaign
    _get_meta_api()
    campaign = Campaign(meta_campaign_id)
    campaign.update({"status": status})
    campaign.remote_update()
    return {"new_status": status, "meta_campaign_id": meta_campaign_id}


# ── performance gap analysis (same as Google Ads) ──────────────────────────────

def _compute_adjustment_rate(roi_gap: float, cr_gap: float) -> float:
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


def _compute_actual_roi(agg: Dict[str, Any]) -> float:
    cost = agg.get("cost", 0) or 0
    conversions = agg.get("conversions", 0) or 0
    if cost <= 0:
        return 0.0
    return round((conversions / cost) * 10, 4)


def _compute_actual_cr(agg: Dict[str, Any]) -> float:
    clicks = agg.get("clicks", 0) or 0
    conversions = agg.get("conversions", 0) or 0
    if clicks <= 0:
        return 0.0
    return round(conversions / clicks, 6)


# ── fetch Meta Insights ────────────────────────────────────────────────────────

def get_meta_campaign_insights(meta_campaign_id: str) -> List[Dict[str, Any]]:
    """
    Fetch last 7 days of campaign insights from Meta.
    Returns a list of metric dicts.
    """
    try:
        from facebook_business.adobjects.campaign import Campaign
        _get_meta_api()
        campaign = Campaign(meta_campaign_id)
        insights = campaign.get_insights(fields=[
            "impressions", "clicks", "spend", "conversions", "ctr"
        ], params={
            "date_preset": "last_7d",
            "level": "campaign",
        })
        results = []
        for i in insights:
            results.append({
                "impressions": int(i.get("impressions", 0) or 0),
                "clicks":      int(i.get("clicks", 0) or 0),
                "cost":        float(i.get("spend", 0) or 0),
                "conversions": float(i.get("conversions", 0) or 0),
                "ctr":         float(i.get("ctr", 0) or 0) / 100.0,  # Meta returns as %
            })
        return results
    except Exception as exc:
        logger.warning(f"Failed to fetch Meta insights for campaign {meta_campaign_id}: {exc}")
        return []


def get_meta_adset_current_budget_cents(meta_adset_id: str) -> int:
    """Return current daily budget in cents for a Meta AdSet."""
    try:
        from facebook_business.adobjects.adset import AdSet
        _get_meta_api()
        adset = AdSet(meta_adset_id)
        adset.remote_read(fields=["daily_budget"])
        return int(adset.get("daily_budget", 0) or 0)
    except Exception as exc:
        logger.warning(f"Failed to fetch Meta adset budget {meta_adset_id}: {exc}")
        return 0


# ── main optimiser ─────────────────────────────────────────────────────────────

def optimize_meta_campaign(
    meta_campaign_id: str,
    meta_adset_id: str,
    actual_campaign_metrics: List[Dict[str, Any]],
    predicted_roi: float,
    predicted_conversion_rate_pct: float,
    current_daily_budget_cents: int = 0,
    dry_run: bool = False,
    user_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the full optimisation loop for one Meta Ads campaign.

    Parameters
    ----------
    meta_campaign_id : str   Meta campaign ID (numeric string).
    meta_adset_id    : str   Meta AdSet ID (numeric string) — budget lives here.
    actual_campaign_metrics : list[dict]   Aggregated metrics (from Insights or mock).
    predicted_roi            : float       AI-predicted ROI.
    predicted_conversion_rate_pct : float  Predicted CR in percent.
    current_daily_budget_cents : int       Current daily budget in cents (100 = $1).
    dry_run : bool           If True, compute but do NOT call Meta API.
    user_overrides : dict    Optional: {"new_budget_usd": float}
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    actions:  List[Dict[str, Any]] = []
    warnings: List[str] = []
    user_overrides = user_overrides or {}

    # ── aggregate metrics ────────────────────────────────────────────────────
    agg: Dict[str, float] = {
        "impressions": 0, "clicks": 0, "conversions": 0, "cost": 0,
    }
    for row in actual_campaign_metrics:
        agg["impressions"]  += row.get("impressions",  0) or 0
        agg["clicks"]       += row.get("clicks",       0) or 0
        agg["conversions"]  += row.get("conversions",  0) or 0
        agg["cost"]         += row.get("cost",         0) or row.get("cost_usd", 0) or 0

    agg["ctr"]     = (agg["clicks"] / agg["impressions"]) if agg["impressions"] > 0 else 0
    agg["avg_cpc"] = (agg["cost"] / agg["clicks"]) if agg["clicks"] > 0 else 0

    actual_roi = _compute_actual_roi(agg)
    actual_cr  = _compute_actual_cr(agg)
    predicted_cr = predicted_conversion_rate_pct / 100.0

    roi_gap = actual_roi - predicted_roi
    cr_gap  = actual_cr  - predicted_cr

    analysis = {
        "actual_roi":         actual_roi,
        "predicted_roi":      predicted_roi,
        "roi_gap":            round(roi_gap, 4),
        "actual_cr_pct":      round(actual_cr * 100, 4),
        "predicted_cr_pct":   predicted_conversion_rate_pct,
        "cr_gap":             round(cr_gap * 100, 4),
        "actual_ctr_pct":     round(agg["ctr"] * 100, 4),
        "actual_impressions": int(agg["impressions"]),
        "actual_clicks":      int(agg["clicks"]),
        "actual_conversions": int(agg["conversions"]),
        "actual_cost_usd":    round(agg["cost"], 2),
        "avg_cpc_usd":        round(agg["avg_cpc"], 4),
        "current_daily_budget_usd": round(current_daily_budget_cents / 100.0, 2),
    }

    # ── insufficient data guard ──────────────────────────────────────────────
    if agg["impressions"] < 100 or agg["cost"] < 1:
        return {
            "timestamp": timestamp,
            "meta_campaign_id": meta_campaign_id,
            "meta_adset_id": meta_adset_id,
            "dry_run": dry_run,
            "status": "insufficient_data",
            "message": (
                f"Not enough data to optimise. "
                f"Impressions: {int(agg['impressions'])}, Cost: ${agg['cost']:.2f}. "
                "Need at least 100 impressions and $1 spend."
            ),
            "analysis": analysis,
            "actions": [],
            "warnings": warnings,
        }

    # ── decision tree ────────────────────────────────────────────────────────

    # 1. Both ROI and CR above predicted → scale up
    if actual_roi > predicted_roi and actual_cr > predicted_cr:
        adj_rate = _compute_adjustment_rate(roi_gap, cr_gap)
        action: Dict[str, Any] = {
            "action": "increase_budget",
            "reason": (
                f"ROI {actual_roi:.2f}x > predicted {predicted_roi:.2f}x "
                f"(+{roi_gap:.2f}), CR {actual_cr*100:.2f}% > predicted {predicted_cr*100:.2f}%"
            ),
            "adjustment_rate": adj_rate,
            "programmatic": True,
        }
        if not dry_run:
            try:
                override_budget = user_overrides.get("new_budget_usd")
                action["api_result"] = _adjust_meta_adset_budget(
                    meta_adset_id,
                    current_daily_budget_cents,
                    adj_rate,
                    override_budget,
                )
            except Exception as exc:
                user_msg = _safe_call(exc, "api_error_user_msg")
                action["api_error"] = (user_msg if isinstance(user_msg, str) and user_msg.strip() else str(exc))
        actions.append(action)

    # 2. ROI severely below predicted → pause
    elif actual_roi < predicted_roi * 0.5 and agg["impressions"] >= 500:
        action = {
            "action": "pause_campaign",
            "reason": (
                f"Actual ROI {actual_roi:.2f}x is below 50% of predicted "
                f"{predicted_roi:.2f}x. Campaign paused to stop budget waste."
            ),
            "programmatic": True,
        }
        if not dry_run:
            try:
                action["api_result"] = _set_meta_campaign_status(meta_campaign_id, "PAUSED")
            except Exception as exc:
                user_msg = _safe_call(exc, "api_error_user_msg")
                action["api_error"] = (user_msg if isinstance(user_msg, str) and user_msg.strip() else str(exc))
        actions.append(action)

    # 3. ROI moderately below predicted → reduce budget
    elif actual_roi < predicted_roi:
        adj_rate = _compute_adjustment_rate(roi_gap, cr_gap)
        action = {
            "action": "reduce_budget",
            "reason": (
                f"Actual ROI {actual_roi:.2f}x < predicted {predicted_roi:.2f}x "
                f"(gap: {roi_gap:.2f})"
            ),
            "adjustment_rate": adj_rate,
            "programmatic": True,
        }
        if not dry_run:
            try:
                override_budget = user_overrides.get("new_budget_usd")
                action["api_result"] = _adjust_meta_adset_budget(
                    meta_adset_id,
                    current_daily_budget_cents,
                    adj_rate,
                    override_budget,
                )
            except Exception as exc:
                user_msg = _safe_call(exc, "api_error_user_msg")
                action["api_error"] = (user_msg if isinstance(user_msg, str) and user_msg.strip() else str(exc))
        actions.append(action)

    else:
        actions.append({
            "action": "no_change",
            "reason": "Performance within expected range. No budget adjustment needed.",
            "programmatic": False,
        })

    # 4. Low CTR → wrong audience or creative (manual)
    if agg["ctr"] < LOW_CTR_THRESHOLD and agg["impressions"] >= 200:
        actions.append({
            "action":        "flag_low_ctr",
            "reason":        f"CTR is {agg['ctr']*100:.2f}% (threshold: {LOW_CTR_THRESHOLD*100:.0f}%). "
                             "Likely wrong audience targeting or poor creative.",
            "recommendation": "Update your Meta ad creative (images, copy, headline) or refine your "
                              "audience targeting in Meta Ads Manager.",
            "programmatic":   False,
            "manual_action":  "Edit your Meta Ad creative or audience targeting in Meta Ads Manager.",
        })

    # 5. High CTR but low conversion → landing page / offer mismatch (manual)
    if agg["ctr"] >= HIGH_CTR_THRESHOLD and actual_cr < predicted_cr * 0.5:
        actions.append({
            "action":        "flag_landing_page",
            "reason":        (
                f"CTR is high ({agg['ctr']*100:.2f}%) but conversion rate "
                f"{actual_cr*100:.2f}% < 50% of predicted {predicted_cr*100:.2f}%."
            ),
            "recommendation": "Landing page offer doesn't match ad promise. "
                              "Review page copy, CTA, and load time.",
            "programmatic":   False,
            "manual_action":  "Update your landing page design, copy, or offer to better match your Meta ad.",
        })

    final_status = "optimized" if actions else "no_action"
    if any(a["action"] == "pause_campaign" for a in actions):
        final_status = "paused"

    return {
        "timestamp":        timestamp,
        "meta_campaign_id": meta_campaign_id,
        "meta_adset_id":    meta_adset_id,
        "dry_run":          dry_run,
        "status":           final_status,
        "analysis":         analysis,
        "actions":          actions,
        "warnings":         warnings,
    }
