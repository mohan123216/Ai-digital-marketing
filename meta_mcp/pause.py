"""
meta_mcp/pause.py
──────────────────────────────────────────────────────────────────────────────
Pause/Resume functionality for Meta (Facebook/Instagram) campaigns.
"""

import os
import logging
from typing import Any, Dict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).resolve().parent / "launched_campaigns.json"
MCP_STATE_TABLE = "mcp_campaign_state"


def _get_meta_api():
    from facebook_business.api import FacebookAdsApi

    app_id = os.getenv("META_APP_ID")
    app_secret = os.getenv("META_APP_SECRET")
    access_token = os.getenv("META_ACCESS_TOKEN")
    if not all([app_id, app_secret, access_token]):
        raise ValueError("Missing META_APP_ID, META_APP_SECRET, or META_ACCESS_TOKEN.")
    FacebookAdsApi.init(app_id, app_secret, access_token)
    return FacebookAdsApi.get_default_api()


def pause_campaign(
    meta_campaign_id: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Pause a Meta (Facebook/Instagram) campaign by setting its status to PAUSED.
    
    Parameters
    ----------
    meta_campaign_id : str
        The Meta campaign ID (e.g., "123456789" or full campaign object ID)
    dry_run : bool
        If True, no actual API call is made
    
    Returns
    -------
    dict with status, message, and campaign details
    """
    if not meta_campaign_id:
        return {
            "status": "error",
            "message": "Meta campaign ID is required.",
        }

    if str(meta_campaign_id).startswith("dryrun/"):
        return {
            "status": "error",
            "message": "Cannot pause a simulated/dry-run campaign. Campaign was not actually launched.",
        }

    if dry_run:
        return {
            "status": "paused_dry_run",
            "message": "Campaign pause simulated successfully (dry_run=True).",
            "meta_campaign_id": meta_campaign_id,
        }

    try:
        from facebook_business.adobjects.campaign import Campaign

        _get_meta_api()
        campaign = Campaign(meta_campaign_id)
        campaign.update({"status": "PAUSED"})
        campaign.remote_update()

        return {
            "status": "paused",
            "message": "Campaign paused successfully.",
            "meta_campaign_id": meta_campaign_id,
        }

    except Exception as e:
        error_msg = str(e)
        if "invalid_request" in error_msg.lower() or "not found" in error_msg.lower():
            return {
                "status": "not_found",
                "message": f"Campaign not found or invalid ID: {meta_campaign_id}",
                "error_details": str(e),
            }
        logger.error(f"Failed to pause Meta campaign {meta_campaign_id}: {e}")
        return {
            "status": "error",
            "message": f"Failed to pause campaign: {str(e)}",
            "meta_campaign_id": meta_campaign_id,
        }


def resume_campaign(
    meta_campaign_id: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Resume a paused Meta campaign by setting its status to ACTIVE.
    
    Parameters
    ----------
    meta_campaign_id : str
        The Meta campaign ID
    dry_run : bool
        If True, no actual API call is made
    
    Returns
    -------
    dict with status, message, and campaign details
    """
    if not meta_campaign_id:
        return {
            "status": "error",
            "message": "Meta campaign ID is required.",
        }

    if str(meta_campaign_id).startswith("dryrun/"):
        return {
            "status": "error",
            "message": "Cannot resume a simulated/dry-run campaign. Campaign was not actually launched.",
        }

    if dry_run:
        return {
            "status": "active_dry_run",
            "message": "Campaign resume simulated successfully (dry_run=True).",
            "meta_campaign_id": meta_campaign_id,
        }

    try:
        from facebook_business.adobjects.campaign import Campaign

        _get_meta_api()
        campaign = Campaign(meta_campaign_id)
        campaign.update({"status": "ACTIVE"})
        campaign.remote_update()

        return {
            "status": "active",
            "message": "Campaign resumed successfully.",
            "meta_campaign_id": meta_campaign_id,
        }

    except Exception as e:
        error_msg = str(e)
        if "invalid_request" in error_msg.lower() or "not found" in error_msg.lower():
            return {
                "status": "not_found",
                "message": f"Campaign not found or invalid ID: {meta_campaign_id}",
                "error_details": str(e),
            }
        logger.error(f"Failed to resume Meta campaign {meta_campaign_id}: {e}")
        return {
            "status": "error",
            "message": f"Failed to resume campaign: {str(e)}",
            "meta_campaign_id": meta_campaign_id,
        }


def get_campaign_status(meta_campaign_id: str) -> Dict[str, Any]:
    """
    Get the current status of a Meta campaign.
    
    Parameters
    ----------
    meta_campaign_id : str
        The Meta campaign ID
    
    Returns
    -------
    dict with current status
    """
    if not meta_campaign_id or str(meta_campaign_id).startswith("dryrun/"):
        return {
            "status": "unknown",
            "message": "Cannot retrieve status for a simulated campaign.",
            "meta_campaign_id": meta_campaign_id,
        }

    try:
        from facebook_business.adobjects.campaign import Campaign

        _get_meta_api()
        campaign = Campaign(meta_campaign_id)
        campaign.remote_read(fields=["id", "name", "status", "created_time"])

        return {
            "status": "found",
            "campaign_id": campaign.get("id"),
            "campaign_name": campaign.get("name"),
            "current_status": campaign.get("status"),
            "created_time": campaign.get("created_time"),
            "meta_campaign_id": meta_campaign_id,
        }

    except Exception as e:
        error_msg = str(e)
        if "invalid_request" in error_msg.lower() or "not found" in error_msg.lower():
            return {
                "status": "not_found",
                "message": f"Campaign not found: {meta_campaign_id}",
                "error_details": str(e),
            }
        logger.error(f"Failed to get Meta campaign status {meta_campaign_id}: {e}")
        return {
            "status": "error",
            "message": f"Failed to get campaign status: {str(e)}",
            "meta_campaign_id": meta_campaign_id,
        }
