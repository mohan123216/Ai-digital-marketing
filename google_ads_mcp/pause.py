"""
google_ads_mcp/pause.py
──────────────────────────────────────────────────────────────────────────────
Pause/Resume functionality for Google Ads campaigns.
"""

import os
import logging
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).resolve().parent / "launched_campaigns.json"
MCP_STATE_TABLE = "mcp_campaign_state"


def _get_supabase_client():
    """Return a Supabase admin client, or None if not configured."""
    try:
        import sys
        _root = str(Path(__file__).resolve().parent.parent)
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from app.services.supabase_client import get_supabase_admin_client
        return get_supabase_admin_client()
    except Exception:
        return None


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


def _get_customer_id() -> str:
    cid = os.getenv("CUSTOMER_ID", "")
    return cid.replace("-", "")


def pause_campaign(
    resource_name: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Pause a Google Ads campaign by setting its status to PAUSED.
    
    Parameters
    ----------
    resource_name : str
        The resource name of the campaign (e.g., customers/1234567890/campaigns/9876543210)
    dry_run : bool
        If True, no actual API call is made
    
    Returns
    -------
    dict with status, message, and campaign details
    """
    if not resource_name:
        return {
            "status": "error",
            "message": "Campaign resource_name is required.",
        }

    if resource_name.startswith("dryrun/"):
        return {
            "status": "error",
            "message": "Cannot pause a simulated/dry-run campaign. Campaign was not actually launched.",
        }

    if dry_run:
        return {
            "status": "paused_dry_run",
            "message": "Campaign pause simulated successfully (dry_run=True).",
            "resource_name": resource_name,
        }

    try:
        client = _load_google_client()
        campaign_service = client.get_service("CampaignService")
        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.update
        campaign.resource_name = resource_name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED

        from google.api_core import protobuf_helpers
        client.copy_from(
            campaign_op.update_mask,
            protobuf_helpers.field_mask(None, campaign._pb),
        )

        campaign_service.mutate_campaigns(
            customer_id=_get_customer_id(),
            operations=[campaign_op],
        )

        return {
            "status": "paused",
            "message": "Campaign paused successfully.",
            "resource_name": resource_name,
        }

    except Exception as e:
        error_msg = str(e)
        if "invalid_grant" in error_msg:
            return {
                "status": "auth_error",
                "message": "Google Ads authentication failed. Your OAuth refresh token has expired.",
                "error_type": "invalid_grant",
            }
        logger.error(f"Failed to pause campaign {resource_name}: {e}")
        return {
            "status": "error",
            "message": f"Failed to pause campaign: {str(e)}",
            "resource_name": resource_name,
        }


def resume_campaign(
    resource_name: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Resume a paused Google Ads campaign by setting its status to ENABLED.
    
    Parameters
    ----------
    resource_name : str
        The resource name of the campaign
    dry_run : bool
        If True, no actual API call is made
    
    Returns
    -------
    dict with status, message, and campaign details
    """
    if not resource_name:
        return {
            "status": "error",
            "message": "Campaign resource_name is required.",
        }

    if resource_name.startswith("dryrun/"):
        return {
            "status": "error",
            "message": "Cannot resume a simulated/dry-run campaign. Campaign was not actually launched.",
        }

    if dry_run:
        return {
            "status": "enabled_dry_run",
            "message": "Campaign resume simulated successfully (dry_run=True).",
            "resource_name": resource_name,
        }

    try:
        client = _load_google_client()
        campaign_service = client.get_service("CampaignService")
        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.update
        campaign.resource_name = resource_name
        campaign.status = client.enums.CampaignStatusEnum.ENABLED

        from google.api_core import protobuf_helpers
        client.copy_from(
            campaign_op.update_mask,
            protobuf_helpers.field_mask(None, campaign._pb),
        )

        campaign_service.mutate_campaigns(
            customer_id=_get_customer_id(),
            operations=[campaign_op],
        )

        return {
            "status": "enabled",
            "message": "Campaign resumed successfully.",
            "resource_name": resource_name,
        }

    except Exception as e:
        error_msg = str(e)
        if "invalid_grant" in error_msg:
            return {
                "status": "auth_error",
                "message": "Google Ads authentication failed. Your OAuth refresh token has expired.",
                "error_type": "invalid_grant",
            }
        logger.error(f"Failed to resume campaign {resource_name}: {e}")
        return {
            "status": "error",
            "message": f"Failed to resume campaign: {str(e)}",
            "resource_name": resource_name,
        }


def get_campaign_status(resource_name: str) -> Dict[str, Any]:
    """
    Get the current status of a Google Ads campaign.
    
    Parameters
    ----------
    resource_name : str
        The resource name of the campaign
    
    Returns
    -------
    dict with current status
    """
    if not resource_name or resource_name.startswith("dryrun/"):
        return {
            "status": "unknown",
            "message": "Cannot retrieve status for a simulated campaign.",
            "resource_name": resource_name,
        }

    try:
        client = _load_google_client()
        service = client.get_service("GoogleAdsService")
        query = f"""
            SELECT campaign.id, campaign.name, campaign.status
            FROM campaign
            WHERE campaign.resource_name = '{resource_name}'
            LIMIT 1
        """
        rows = list(service.search(customer_id=_get_customer_id(), query=query))
        if rows:
            campaign = rows[0].campaign
            status_enum = campaign.status
            status_name = client.enums.CampaignStatusEnum(status_enum).name
            return {
                "status": "found",
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "current_status": status_name,
                "resource_name": resource_name,
            }
        else:
            return {
                "status": "not_found",
                "message": "Campaign not found.",
                "resource_name": resource_name,
            }

    except Exception as e:
        logger.error(f"Failed to get campaign status {resource_name}: {e}")
        return {
            "status": "error",
            "message": f"Failed to get campaign status: {str(e)}",
            "resource_name": resource_name,
        }
