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
MCP_STATE_TABLE = "mcp_campaign_state"


def _get_supabase_client():
    """Return a Supabase admin client, or None if not configured."""
    try:
        import sys, os as _os
        _root = str(Path(__file__).resolve().parent.parent)
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from app.services.supabase_client import get_supabase_admin_client
        return get_supabase_admin_client()
    except Exception:
        return None


def _load_state() -> Dict[str, Any]:
    """Load campaign launch state from Supabase, falling back to JSON file."""
    try:
        db = _get_supabase_client()
        if db:
            rows = db.table(MCP_STATE_TABLE).select("*").execute().data or []
            launched = {}
            for row in rows:
                key = row.get("recommendation_key")
                if key:
                    launched[key] = {
                        "campaign_id": row.get("campaign_id"),
                        "platform": row.get("platform"),
                        "ad_type": row.get("ad_type", "text"),
                        "resource_name": row.get("resource_name"),
                        "launched_at": row.get("launched_at"),
                        "recommendation": row.get("recommendation") or {},
                        "launchable": row.get("launchable", False),
                        "status": row.get("status", "launched"),
                    }
            return {"launched": launched}
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Supabase state load failed, using JSON fallback: {e}")

    # JSON fallback
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
    """Persist campaign launch state to Supabase and JSON file."""
    # Persist to Supabase
    try:
        db = _get_supabase_client()
        if db:
            for key, entry in state.get("launched", {}).items():
                row = {
                    "recommendation_key": key,
                    "campaign_id": entry.get("campaign_id"),
                    "platform": entry.get("platform", "Google Ads"),
                    "ad_type": entry.get("ad_type", "text"),
                    "resource_name": entry.get("resource_name"),
                    "launched_at": entry.get("launched_at"),
                    "recommendation": entry.get("recommendation") or {},
                    "launchable": entry.get("launchable", False),
                    "status": entry.get("status", "launched"),
                }
                db.table(MCP_STATE_TABLE).upsert(row, on_conflict="recommendation_key").execute()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Supabase state save failed, using JSON fallback: {e}")

    # Always also write JSON as fallback
    try:
        with STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def _prepare_display_images(original_bytes: bytes) -> tuple[bytes, bytes]:
    """Returns (landscape_1_91_bytes, square_1_1_bytes) properly padded/cropped."""
    import io
    from PIL import Image

    img = Image.open(io.BytesIO(original_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    width, height = img.size
    
    # 1. Square (1:1)
    sq_size = max(width, height)
    sq_img = Image.new("RGB", (sq_size, sq_size), (255, 255, 255))
    sq_img.paste(img, ((sq_size - width) // 2, (sq_size - height) // 2))
    if sq_size < 300:
        sq_img = sq_img.resize((300, 300), Image.Resampling.LANCZOS)
    sq_bytes_io = io.BytesIO()
    sq_img.save(sq_bytes_io, format="JPEG", quality=90)
    sq_bytes = sq_bytes_io.getvalue()
    
    # 2. Landscape (1.91:1)
    target_aspect = 1.91
    current_aspect = width / height
    if current_aspect > target_aspect:
        target_width = width
        target_height = int(width / target_aspect)
    else:
        target_height = height
        target_width = int(height * target_aspect)
        
    ls_img = Image.new("RGB", (target_width, target_height), (255, 255, 255))
    ls_img.paste(img, ((target_width - width) // 2, (target_height - height) // 2))
    if target_width < 600 or target_height < 314:
        scale = max(600 / target_width, 314 / target_height)
        new_w, new_h = int(target_width * scale), int(target_height * scale)
        ls_img = ls_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    ls_bytes_io = io.BytesIO()
    ls_img.save(ls_bytes_io, format="JPEG", quality=90)
    ls_bytes = ls_bytes_io.getvalue()
    
    return ls_bytes, sq_bytes


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



def _validate_final_url(url: str) -> tuple[bool, str]:
    """Validate final_url for Google Ads.
    
    Returns: (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "Final URL is required."
    
    url = url.strip()
    
    # Check for localhost
    if 'localhost' in url.lower():
        return False, "Final URL cannot be 'localhost'. Please provide a valid domain (e.g., https://example.com)."
    
    # Check for valid protocol
    if not (url.startswith('http://') or url.startswith('https://')):
        return False, "Final URL must start with http:// or https://"
    
    # Check for valid domain structure
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.netloc or '.' not in parsed.netloc:
            return False, "Final URL must contain a valid domain with a top-level domain (e.g., .com, .org)."
    except Exception:
        return False, "Invalid URL format."
    
    return True, ""

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


def _print_campaign_metrics(campaign_name: str, recommendation: Dict[str, Any]) -> None:
    """Print campaign metrics before launch."""
    metrics = {
        "platform": recommendation.get("platform"),
        "target_location": recommendation.get("target_location"),
        "target_segment": recommendation.get("target_segment"),
        "target_age_group": recommendation.get("target_age_group"),
        "budget": recommendation.get("budget"),
        "predicted_roi": recommendation.get("predicted_roi"),
        "predicted_conversion_rate": recommendation.get("predicted_conversion_rate"),
    }

    print("\n========== CAMPAIGN METRICS ==========")
    print(f"Campaign Name : {campaign_name}")
    for k, v in metrics.items():
        print(f"{k} : {v}")
    print("======================================\n")


def launch_selected_recommendation(
    campaign_id: str,
    recommendation: Dict[str, Any],
    ad_type: str = "text",
    dry_run: bool = False,
    customer_id_override: str | None = None,
    budget_resource_override: str | None = None,
    login_customer_id_override: str | None = None,
    campaign_name_override: str | None = None,
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
    # If already launched normally, block. If it was a dry_run/simulated, allow re-launch for real.
    if already and already.get("status") != "launched_dry_run":
        return {
            "status": "already_launched",
            "message": "This recommendation has already been launched.",
            "recommendation_key": key,
            "launchable": False,
            "existing": already,
        }

    customer_id = customer_id_override or os.getenv("CUSTOMER_ID")
    previous_login_customer_id = os.getenv("LOGIN_CUSTOMER_ID")
    if login_customer_id_override:
        os.environ["LOGIN_CUSTOMER_ID"] = login_customer_id_override

    if not customer_id:
        raise ValueError("Missing CUSTOMER_ID in environment.")

    location = recommendation.get("target_location", "Unknown")
    segment = recommendation.get("target_segment", "General")
    age_group = recommendation.get("target_age_group", "Auto")
    budget_usd = _parse_budget_usd(recommendation.get("budget"))
    predicted_roi = recommendation.get("predicted_roi", "N/A")
    predicted_conv = recommendation.get("predicted_conversion_rate", "N/A")

    if campaign_name_override:
        campaign_name = campaign_name_override[:255]
    else:
        campaign_name = f"AI - {segment} ({location}, {age_group})".replace("  ", " ")[:100]
    _print_campaign_metrics(campaign_name, recommendation)

    try:
        if dry_run:
            resource_name = f"dryrun/customers/{customer_id}/campaigns/{key}"
        else:
            try:
                client = _load_google_client()
            except Exception as auth_err:
                error_str = str(auth_err)
                if "invalid_grant" in error_str:
                    return {
                        "status": "auth_error",
                        "message": "Google Ads authentication failed. Your OAuth refresh token has expired. Please re-authenticate with Google Ads.",
                        "error_type": "invalid_grant",
                    }
                raise
            
            # Create a non-shared budget for the campaign
            budget_service = client.get_service("CampaignBudgetService")
            budget_op = client.get_type("CampaignBudgetOperation")
            budget = budget_op.create
            budget.name = f"Budget – {campaign_name}"
            budget.amount_micros = int(budget_usd * 1_000_000)
            budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
            budget.explicitly_shared = False
            
            budget_resp = budget_service.mutate_campaign_budgets(
                customer_id=customer_id,
                operations=[budget_op],
            )
            budget_resource = budget_resp.results[0].resource_name

            campaign_service = client.get_service("CampaignService")
            campaign_operation = client.get_type("CampaignOperation")
            campaign = campaign_operation.create

            campaign.name = campaign_name
            
            if ad_type == "video":
                campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.VIDEO
                # VIDEO_TRUE_VIEW_IN_STREAM (skippable in-stream) ads require MANUAL_CPV or MAXIMIZE_CONVERSIONS.
                client.get_type("ManualCpv") # Ensure it exists
                campaign.manual_cpv = client.get_type("ManualCpv")
            elif ad_type == "image":
                campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.DISPLAY
                campaign.manual_cpc.enhanced_cpc_enabled = False
            else:
                campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
                campaign.manual_cpc.enhanced_cpc_enabled = False
                campaign.network_settings.target_google_search = True
                campaign.network_settings.target_search_network = True
                campaign.network_settings.target_content_network = False

            campaign.status = client.enums.CampaignStatusEnum.ENABLED
            campaign.campaign_budget = budget_resource

            # Required in v15+: set to 2 = DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING.
            campaign.contains_eu_political_advertising = 2

            try:
                response = campaign_service.mutate_campaigns(
                    customer_id=customer_id,
                    operations=[campaign_operation],
                )
                resource_name = response.results[0].resource_name
            except Exception as e:
                # Remove simulation fallback to allow real errors to surface or success to occur
                raise e
    finally:
        if login_customer_id_override:
            if previous_login_customer_id:
                os.environ["LOGIN_CUSTOMER_ID"] = previous_login_customer_id
            else:
                os.environ.pop("LOGIN_CUSTOMER_ID", None)

    launched_at = datetime.utcnow().isoformat() + "Z"
    status = "launched_dry_run" if (dry_run or resource_name.startswith("dryrun/")) else "launched"
    state["launched"][key] = {
        "campaign_id": campaign_id,
        "platform": DEFAULT_CHANNEL,
        "ad_type": ad_type,
        "resource_name": resource_name,
        "launched_at": launched_at,
        "recommendation": recommendation,
        "launchable": False,
        "status": status,
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
    # A recommendation is launchable if it hasn't been launched, or if the previous launch was a simulation.
    launchable = (existing is None or existing.get("status") == "launched_dry_run")
    return {
        "recommendation_key": key,
        "launchable": launchable,
        "status": "not_launched" if launchable else "already_launched",
        "existing": existing,
    }


def get_campaign_resource_name_for_run(campaign_run_id: str) -> str | None:
    """Look up the Google Ads campaign resource_name stored when the campaign was launched."""
    state = _load_state()
    for entry in state.get("launched", {}).values():
        if entry.get("campaign_id") == campaign_run_id:
            return entry.get("resource_name")
    return None


# ─── Text / Responsive Search Ad ─────────────────────────────────────────────

def launch_ad_to_campaign(
    campaign_run_id: str,
    ad_payload: Dict[str, Any],
    dry_run: bool = False,
    customer_id_override: str | None = None,
    login_customer_id_override: str | None = None,
) -> Dict[str, Any]:
    """Create an Ad Group + Responsive Search Ad inside an existing SEARCH campaign.

    Parameters
    ----------
    campaign_run_id : str
        The UUID of the campaign_runs row (used to look up the Google resource name).
    ad_payload : dict
        Must contain: headline_1..3, description_1..2, final_url.
        Optional: display_url_path_1/2, keywords (list of str), ad_name.
    dry_run : bool
        When True, no real API calls are made.

    Returns
    -------
    dict with keys: status, ad_resource_name, adgroup_resource_name, message.
    """
    customer_id = customer_id_override or os.getenv("CUSTOMER_ID")
    campaign_resource = get_campaign_resource_name_for_run(campaign_run_id)

    headline_1 = ad_payload.get("headline_1", "")
    headline_2 = ad_payload.get("headline_2", "")
    headline_3 = ad_payload.get("headline_3", "")
    description_1 = ad_payload.get("description_1", "")
    description_2 = ad_payload.get("description_2", "")
    final_url = ad_payload.get("final_url", "")
    path1 = ad_payload.get("display_url_path_1") or ""
    path2 = ad_payload.get("display_url_path_2") or ""
    keywords: list = ad_payload.get("keywords") or []
    ad_name = ad_payload.get("ad_name") or f"AI Ad {datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    # Add timestamp suffix to ensure unique ad group names within the campaign
    timestamp_suffix = datetime.utcnow().strftime('%H%M%S')
    adgroup_name = f"AdGroup – {ad_name} {timestamp_suffix}"

    if not campaign_resource:
        raise ValueError(f"No Google Ads campaign found for run ID {campaign_run_id}. Please launch the campaign first.")
    
    if campaign_resource.startswith("dryrun/"):
        raise ValueError(f"The parent campaign ({campaign_resource}) was a simulated launch. Please launch the campaign for real (click 'Launch Campaign' again) before attaching an ad.")

    if dry_run or not customer_id:
        fake_key = hashlib.sha256(
            json.dumps(ad_payload, sort_keys=True).encode()
        ).hexdigest()[:16]
        reason = (
            "dry_run=True"
            if dry_run
            else ("missing CUSTOMER_ID" if not customer_id else "campaign not yet launched to Google Ads")
        )
        return {
            "status": "launched_dry_run",
            "message": f"Ad launch simulated ({reason}).",
            "ad_resource_name": f"dryrun/customers/0/ads/{fake_key}",
            "adgroup_resource_name": f"dryrun/customers/0/adGroups/{fake_key}",
            "ad_name": ad_name,
            "adgroup_name": adgroup_name,
        }

    previous_login_cid = os.getenv("LOGIN_CUSTOMER_ID")
    if login_customer_id_override:
        os.environ["LOGIN_CUSTOMER_ID"] = login_customer_id_override

    try:
        client = _load_google_client()

        # ── 1. Create Ad Group (SEARCH_STANDARD for Search campaigns) ─────
        adgroup_service = client.get_service("AdGroupService")
        adgroup_op = client.get_type("AdGroupOperation")
        adgroup = adgroup_op.create

        adgroup.name = adgroup_name
        adgroup.campaign = campaign_resource
        adgroup.status = client.enums.AdGroupStatusEnum.ENABLED
        adgroup.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
        adgroup.cpc_bid_micros = 1_000_000  # $1.00 default CPC

        ag_response = adgroup_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=[adgroup_op],
        )
        adgroup_resource = ag_response.results[0].resource_name

        # ── 2. Create Responsive Search Ad ────────────────────────────────
        ad_service = client.get_service("AdGroupAdService")
        ad_op = client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_op.create

        ad_group_ad.ad_group = adgroup_resource
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED

        rsa = ad_group_ad.ad.responsive_search_ad

        def _hl(text: str):
            asset = client.get_type("AdTextAsset")
            asset.text = text[:30]
            return asset

        def _desc(text: str):
            asset = client.get_type("AdTextAsset")
            asset.text = text[:90]
            return asset

        rsa.headlines.extend([_hl(headline_1), _hl(headline_2), _hl(headline_3)])
        rsa.descriptions.extend([_desc(description_1), _desc(description_2)])

        # Validate final_url before appending
        is_valid, error_msg = _validate_final_url(final_url)
        if not is_valid:
            return {
                "status": "validation_error",
                "message": f"Ad launch failed: {error_msg}",
            }

        ad_group_ad.ad.final_urls.append(final_url)
        if path1:
            rsa.path1 = path1[:15]
        if path2:
            rsa.path2 = path2[:15]

        ad_response = ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=[ad_op],
        )
        ad_resource = ad_response.results[0].resource_name

        # ── 3. Add keywords to Ad Group ───────────────────────────────────
        if keywords:
            kw_service = client.get_service("AdGroupCriterionService")
            kw_ops = []
            for kw_text in keywords[:20]:  # cap at 20
                kw_op = client.get_type("AdGroupCriterionOperation")
                criterion = kw_op.create
                criterion.ad_group = adgroup_resource
                criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
                criterion.keyword.text = kw_text.strip()[:80]
                criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
                kw_ops.append(kw_op)
            kw_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=kw_ops,
            )

    finally:
        if login_customer_id_override:
            if previous_login_cid:
                os.environ["LOGIN_CUSTOMER_ID"] = previous_login_cid
            else:
                os.environ.pop("LOGIN_CUSTOMER_ID", None)

    return {
        "status": "launched",
        "message": "Ad launched successfully on Google Ads.",
        "ad_resource_name": ad_resource,
        "adgroup_resource_name": adgroup_resource,
        "ad_name": ad_name,
        "adgroup_name": adgroup_name,
    }


# ─── Image Ad (creates its own Display campaign) ──────────────────────────────

def launch_image_ad_to_campaign(
    campaign_run_id: str,
    ad_payload: Dict[str, Any],
    image_bytes: bytes,
    image_filename: str,
    dry_run: bool = False,
    customer_id_override: str | None = None,
    login_customer_id_override: str | None = None,
) -> Dict[str, Any]:
    """Create a Google Display campaign and launch a Responsive Display Ad with an image.

    Because image ads require a DISPLAY campaign (not SEARCH), this function
    self-creates:
      1. A CampaignBudget (daily budget derived from ad_payload or defaulted to $10).
      2. A Display campaign (advertising_channel_type=DISPLAY, TARGET_SPEND bidding).
      3. A DISPLAY_STANDARD AdGroup.
      4. Uploads the image as an ImageAsset.
      5. Creates a ResponsiveDisplayAd using the image.
      6. Optionally adds keyword contextual targeting.
    """
    customer_id = customer_id_override or os.getenv("CUSTOMER_ID")

    # ── Extract payload fields ─────────────────────────────────────────────────
    final_url     = (ad_payload.get("final_url") or "").strip()
    ad_name       = (ad_payload.get("ad_name") or
                     f"Image Ad {datetime.utcnow().strftime('%Y%m%d%H%M%S')}").strip()
    headline      = (ad_payload.get("headline_1") or ad_name)[:30]
    long_headline = (ad_payload.get("long_headline") or ad_name)[:90]
    business_name = (ad_payload.get("business_name") or "My Business")[:25]
    description   = (ad_payload.get("description_1") or business_name)[:90]
    keywords: list = ad_payload.get("keywords") or []
    # daily budget in micros (1 USD = 1,000,000 micros); default $10/day
    budget_micros = int(_parse_budget_usd(ad_payload.get("budget")) * 1_000_000) or 10_000_000
    campaign_name = f"Display – {ad_name}"
    adgroup_name  = f"DspAG – {ad_name}"

    if not final_url:
        raise ValueError("final_url is required for image ad launch.")

    # ── Verify Campaign Exists ────────────────────────────────────────────────
    state = _load_state()
    launched = None
    for k, v in state.get("launched", {}).items():
        if v.get("campaign_id") == campaign_run_id and v.get("platform") == "Google Ads":
            launched = v
            break
            
    if not launched and not dry_run:
        raise ValueError(f"No Google Ads campaign found for run ID {campaign_run_id}. Please launch the campaign first.")
        
    campaign_resource = launched.get("resource_name") if launched else f"dryrun/customers/{customer_id}/campaigns/fake"

    if campaign_resource.startswith("dryrun/") and not dry_run:
        raise ValueError(f"The parent campaign ({campaign_resource}) was a simulated launch. Please launch the campaign for real (click 'Launch Campaign' again) before attaching an ad.")

    # ── Dry-run / missing config shortcut ─────────────────────────────────────
    if dry_run or not customer_id:
        fake_key = hashlib.sha256(
            json.dumps(ad_payload, sort_keys=True).encode()
        ).hexdigest()[:16]
        reason = "dry_run=True" if dry_run else "missing CUSTOMER_ID"
        return {
            "status": "launched_dry_run",
            "message": f"Image ad launch simulated ({reason}).",
            "campaign_resource_name": campaign_resource,
            "ad_resource_name": f"dryrun/customers/0/ads/{fake_key}",
            "adgroup_resource_name": f"dryrun/customers/0/adGroups/{fake_key}",
            "image_asset_resource_name": f"dryrun/customers/0/assets/{fake_key}",
            "ad_name": ad_name,
        }

    previous_login_cid = os.getenv("LOGIN_CUSTOMER_ID")
    if login_customer_id_override:
        os.environ["LOGIN_CUSTOMER_ID"] = login_customer_id_override

    try:
        client = _load_google_client()

        # ── Step 1: Format & Upload ImageAssets ────────────────────────────
        ls_bytes, sq_bytes = _prepare_display_images(image_bytes)

        asset_service = client.get_service("AssetService")
        
        # Landscape
        ls_op = client.get_type("AssetOperation")
        ls_asset = ls_op.create
        ls_asset.name = f"{ad_name} ls asset {datetime.utcnow().strftime('%H%M%S')}"
        ls_asset.type_ = client.enums.AssetTypeEnum.IMAGE
        ls_asset.image_asset.data = ls_bytes
        ls_asset.image_asset.file_size = len(ls_bytes)
        ls_asset.image_asset.mime_type = client.enums.MimeTypeEnum.IMAGE_JPEG
        
        # Square
        sq_op = client.get_type("AssetOperation")
        sq_asset = sq_op.create
        sq_asset.name = f"{ad_name} sq asset {datetime.utcnow().strftime('%H%M%S')}"
        sq_asset.type_ = client.enums.AssetTypeEnum.IMAGE
        sq_asset.image_asset.data = sq_bytes
        sq_asset.image_asset.file_size = len(sq_bytes)
        sq_asset.image_asset.mime_type = client.enums.MimeTypeEnum.IMAGE_JPEG

        asset_resp = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=[ls_op, sq_op],
        )
        ls_resource = asset_resp.results[0].resource_name
        sq_resource = asset_resp.results[1].resource_name

        # ── Step 2: Create DISPLAY_STANDARD AdGroup ───────────────────────
        adgroup_service = client.get_service("AdGroupService")
        adgroup_op = client.get_type("AdGroupOperation")
        adg = adgroup_op.create
        adg.name = adgroup_name
        adg.campaign = campaign_resource
        adg.status = client.enums.AdGroupStatusEnum.ENABLED
        adg.type_ = client.enums.AdGroupTypeEnum.DISPLAY_STANDARD
        adg.cpc_bid_micros = 500_000   # $0.50 default CPC

        ag_resp = adgroup_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=[adgroup_op],
        )
        adgroup_resource = ag_resp.results[0].resource_name

        # ── Step 5: Create ResponsiveDisplayAd ───────────────────────────
        ad_service = client.get_service("AdGroupAdService")
        ad_op = client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_op.create
        ad_group_ad.ad_group = adgroup_resource
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED

        rda = ad_group_ad.ad.responsive_display_ad

        # marketing_images — landscape (required, ≥1)
        mkt_img = client.get_type("AdImageAsset")
        mkt_img.asset = ls_resource
        rda.marketing_images.append(mkt_img)

        # square_marketing_images — square (required, ≥1)
        sq_img = client.get_type("AdImageAsset")
        sq_img.asset = sq_resource
        rda.square_marketing_images.append(sq_img)

        # headlines — ≥1, max 30 chars each (required)
        hl = client.get_type("AdTextAsset")
        hl.text = headline
        rda.headlines.append(hl)

        # long_headline — required, max 90 chars
        rda.long_headline.text = long_headline

        # descriptions — ≥1, max 90 chars each (required)
        desc = client.get_type("AdTextAsset")
        desc.text = description
        rda.descriptions.append(desc)

        # business_name — required, max 25 chars
        rda.business_name = business_name

        # final_urls — required
        # Validate final_url before appending
        is_valid, error_msg = _validate_final_url(final_url)
        if not is_valid:
            return {
                "status": "validation_error",
                "message": f"Ad launch failed: {error_msg}",
            }

        ad_group_ad.ad.final_urls.append(final_url)

        ad_resp = ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=[ad_op],
        )
        ad_resource = ad_resp.results[0].resource_name

        # ── Step 6: (Optional) Add keyword contextual targeting ───────────
        if keywords:
            kw_service = client.get_service("AdGroupCriterionService")
            kw_ops = []
            for kw_text in keywords[:20]:
                kw_op = client.get_type("AdGroupCriterionOperation")
                crit = kw_op.create
                crit.ad_group = adgroup_resource
                crit.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
                crit.keyword.text = kw_text.strip()[:80]
                crit.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
                kw_ops.append(kw_op)
            kw_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=kw_ops,
            )

    finally:
        if login_customer_id_override:
            if previous_login_cid:
                os.environ["LOGIN_CUSTOMER_ID"] = previous_login_cid
            else:
                os.environ.pop("LOGIN_CUSTOMER_ID", None)

    return {
        "status": "launched",
        "message": "Image ad launched successfully in the Display campaign.",
        "campaign_resource_name": campaign_resource,
        "ad_resource_name": ad_resource,
        "adgroup_resource_name": adgroup_resource,
        "image_asset_resource_name": ls_resource,
        "ad_name": ad_name,
    }


# ─── Video Ad (creates its own Video campaign) ────────────────────────────────

def launch_video_ad_to_campaign(
    campaign_run_id: str,
    ad_payload: Dict[str, Any],
    youtube_url: str | None = None,
    video_bytes: bytes | None = None,
    video_filename: str | None = None,
    dry_run: bool = False,
    customer_id_override: str | None = None,
    login_customer_id_override: str | None = None,
) -> Dict[str, Any]:
    """Create a Google Video campaign and launch an in-stream video ad.

    Only YouTube-hosted videos are supported by the Google Ads API.
    Provide youtube_url (https://www.youtube.com/watch?v=...).

    This function self-creates:
      1. A CampaignBudget.
      2. A Video campaign (advertising_channel_type=VIDEO, TARGET_CPM bidding).
      3. A VIDEO_TRUE_VIEW_IN_STREAM AdGroup.
      4. A YouTubeVideoAsset from the provided youtube_url.
      5. A skippable in-stream video ad (video_non_skippable_in_stream_ad
         is used for ≤15s; skippable for longer).
    """
    import re

    customer_id = customer_id_override or os.getenv("CUSTOMER_ID")

    if not youtube_url and not video_bytes:
        raise ValueError("youtube_url is required to launch a video ad.")
    if not youtube_url:
        if not dry_run:
            raise ValueError(
                "Direct video file upload is not supported by the Google Ads API. "
                "Please host the video on YouTube and provide youtube_url."
            )
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # placeholder for dry_run

    # ── Extract payload fields ─────────────────────────────────────────────────
    final_url     = (ad_payload.get("final_url") or "").strip()
    ad_name       = (ad_payload.get("ad_name") or
                     f"Video Ad {datetime.utcnow().strftime('%Y%m%d%H%M%S')}").strip()
    headline      = (ad_payload.get("headline_1") or ad_name)[:30]
    description   = (ad_payload.get("description_1") or headline)[:90]
    display_url   = (ad_payload.get("display_url") or final_url)[:255]
    keywords: list = ad_payload.get("keywords") or []
    budget_micros = int(_parse_budget_usd(ad_payload.get("budget")) * 1_000_000) or 10_000_000
    campaign_name = f"Video – {ad_name}"
    adgroup_name  = f"VidAG – {ad_name}"

    if not final_url:
        raise ValueError("final_url is required for video ad launch.")

    # Extract YouTube video ID
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", youtube_url)
    if not match:
        raise ValueError(f"Could not extract YouTube video ID from URL: {youtube_url}")
    yt_video_id = match.group(1)

    # ── Verify Campaign Exists ────────────────────────────────────────────────
    state = _load_state()
    launched = None
    for k, v in state.get("launched", {}).items():
        if v.get("campaign_id") == campaign_run_id and v.get("platform") == "Google Ads":
            launched = v
            break
            
    if not launched and not dry_run:
        raise ValueError(f"No Google Ads campaign found for run ID {campaign_run_id}. Please launch the campaign first.")
        
    campaign_resource = launched.get("resource_name") if launched else f"dryrun/customers/{customer_id}/campaigns/fake"

    if campaign_resource.startswith("dryrun/") and not dry_run:
        raise ValueError(f"The parent campaign ({campaign_resource}) was a simulated launch. Please launch the campaign for real (click 'Launch Campaign' again) before attaching an ad.")

    # ── Dry-run shortcut ──────────────────────────────────────────────────────
    if dry_run or not customer_id:
        fake_key = hashlib.sha256(
            json.dumps(ad_payload, sort_keys=True).encode()
        ).hexdigest()[:16]
        reason = "dry_run=True" if dry_run else "missing CUSTOMER_ID"
        return {
            "status": "launched_dry_run",
            "message": f"Video ad launch simulated ({reason}).",
            "campaign_resource_name": campaign_resource,
            "ad_resource_name": f"dryrun/customers/0/ads/{fake_key}",
            "adgroup_resource_name": f"dryrun/customers/0/adGroups/{fake_key}",
            "video_asset_resource_name": f"dryrun/customers/0/assets/{fake_key}_{yt_video_id}",
            "ad_name": ad_name,
        }

    previous_login_cid = os.getenv("LOGIN_CUSTOMER_ID")
    if login_customer_id_override:
        os.environ["LOGIN_CUSTOMER_ID"] = login_customer_id_override

    try:
        client = _load_google_client()

        # ── Step 1: Create YouTubeVideoAsset ──────────────────────────────
        asset_service = client.get_service("AssetService")
        asset_op = client.get_type("AssetOperation")
        yt_asset = asset_op.create
        yt_asset.name = f"{ad_name} yt {yt_video_id}"
        yt_asset.type_ = client.enums.AssetTypeEnum.YOUTUBE_VIDEO
        yt_asset.youtube_video_asset.youtube_video_id = yt_video_id

        asset_resp = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=[asset_op],
        )
        video_asset_resource = asset_resp.results[0].resource_name

        # ── Step 2: Create VIDEO_TRUE_VIEW_IN_STREAM AdGroup ──────────────
        adgroup_service = client.get_service("AdGroupService")
        adgroup_op = client.get_type("AdGroupOperation")
        adg = adgroup_op.create
        adg.name = adgroup_name
        adg.campaign = campaign_resource
        adg.status = client.enums.AdGroupStatusEnum.ENABLED
        adg.type_ = client.enums.AdGroupTypeEnum.VIDEO_TRUE_VIEW_IN_STREAM
        adg.cpv_bid_micros = 500_000   # $0.50 default CPV bid

        ag_resp = adgroup_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=[adgroup_op],
        )
        adgroup_resource = ag_resp.results[0].resource_name

        # ── Step 5: Create skippable in-stream video ad ───────────────────
        ad_service = client.get_service("AdGroupAdService")
        ad_op = client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_op.create
        ad_group_ad.ad_group = adgroup_resource
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED

        # video_true_view_in_stream_ad — used for VIDEO_TRUE_VIEW_IN_STREAM groups
        instream = ad_group_ad.ad.video_true_view_in_stream_ad

        # in-stream video asset (required)
        video_ref = client.get_type("AdVideoAsset")
        video_ref.asset = video_asset_resource
        instream.in_stream_video_ad_info.video = video_asset_resource

        # headline (required, max 30 chars)
        instream.headline = headline

        # description lines (optional but recommended, max 90 chars each)
        instream.description1 = description[:90]
        instream.description2 = (ad_payload.get("description_2") or description)[:90]

        # display_url — required for in-stream ads
        instream.display_url = display_url

        # final_url — required
        # Validate final_url before appending
        is_valid, error_msg = _validate_final_url(final_url)
        if not is_valid:
            return {
                "status": "validation_error",
                "message": f"Ad launch failed: {error_msg}",
            }

        ad_group_ad.ad.final_urls.append(final_url)

        ad_resp = ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=[ad_op],
        )
        ad_resource = ad_resp.results[0].resource_name

        # ── Step 6: (Optional) Add keyword targeting ───────────────────────
        if keywords:
            kw_service = client.get_service("AdGroupCriterionService")
            kw_ops = []
            for kw_text in keywords[:20]:
                kw_op = client.get_type("AdGroupCriterionOperation")
                crit = kw_op.create
                crit.ad_group = adgroup_resource
                crit.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
                crit.keyword.text = kw_text.strip()[:80]
                crit.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
                kw_ops.append(kw_op)
            kw_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=kw_ops,
            )

    finally:
        if login_customer_id_override:
            if previous_login_cid:
                os.environ["LOGIN_CUSTOMER_ID"] = previous_login_cid
            else:
                os.environ.pop("LOGIN_CUSTOMER_ID", None)

    return {
        "status": "launched",
        "message": "Video ad launched successfully in the Video campaign.",
        "campaign_resource_name": campaign_resource,
        "ad_resource_name": ad_resource,
        "adgroup_resource_name": adgroup_resource,
        "video_asset_resource_name": video_asset_resource,
        "ad_name": ad_name,
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
    parser = argparse.ArgumentParser(description="Google Ads campaign management (launch, pause, resume).")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Launch command
    launch_parser = subparsers.add_parser("launch", help="Launch a new campaign")
    launch_parser.add_argument("--payload-file", type=str, help="Path to recommendation API response JSON file")
    launch_parser.add_argument("--index", type=int, default=0, help="Recommendation index to launch")
    launch_parser.add_argument("--campaign-id", type=str, help="Campaign ID when passing recommendation JSON directly")
    launch_parser.add_argument("--dry-run", action="store_true", help="Simulate launch without Google Ads API call")
    launch_parser.add_argument(
        "--recommendation-json",
        type=str,
        help="Single recommendation JSON string (must include platform, target fields, budget, predictions)",
    )

    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause a campaign")
    pause_parser.add_argument("--resource-name", type=str, required=True, help="Campaign resource name")
    pause_parser.add_argument("--dry-run", action="store_true", help="Simulate pause without API call")

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a paused campaign")
    resume_parser.add_argument("--resource-name", type=str, required=True, help="Campaign resource name")
    resume_parser.add_argument("--dry-run", action="store_true", help="Simulate resume without API call")

    # Status command
    status_parser = subparsers.add_parser("status", help="Get campaign status")
    status_parser.add_argument("--resource-name", type=str, required=True, help="Campaign resource name")

    args = parser.parse_args()

    if args.command == "launch":
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

    elif args.command == "pause":
        from google_ads_mcp.pause import pause_campaign
        result = pause_campaign(
            resource_name=args.resource_name,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2))

    elif args.command == "resume":
        from google_ads_mcp.pause import resume_campaign
        result = resume_campaign(
            resource_name=args.resource_name,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2))

    elif args.command == "status":
        from google_ads_mcp.pause import get_campaign_status
        result = get_campaign_status(resource_name=args.resource_name)
        print(json.dumps(result, indent=2))

    else:
        # Default to launch for backward compatibility
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
