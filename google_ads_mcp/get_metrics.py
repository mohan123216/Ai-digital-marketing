from google.ads.googleads.client import GoogleAdsClient
from dotenv import load_dotenv
import os

def get_client():
    load_dotenv()

    config = {
        "developer_token": os.getenv("DEVELOPER_TOKEN"),
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "refresh_token": os.getenv("REFRESH_TOKEN"),
        "use_proto_plus": True,
    }

    login_cid = os.getenv("LOGIN_CUSTOMER_ID")
    if login_cid:
        config["login_customer_id"] = login_cid

    return GoogleAdsClient.load_from_dict(config)


def get_metrics(campaign_ids=None):
    client = get_client()
    service = client.get_service("GoogleAdsService")

    customer_id = os.getenv("CUSTOMER_ID")
    if not customer_id:
        return {"campaign_metrics": [], "ad_metrics": []}

    # If an explicitly empty array is passed, return early
    if campaign_ids is not None and not campaign_ids:
        return {"campaign_metrics": [], "ad_metrics": []}

    # Format campaign IDs for GAQL
    campaign_filter = ""
    if campaign_ids:
        # Assuming campaign_ids are numeric strings or ints
        id_list = ", ".join(str(cid) for cid in campaign_ids)
        campaign_filter = f"AND campaign.id IN ({id_list})"

    # -----------------------
    # Campaign Metrics
    # -----------------------
    campaign_query = f"""
    SELECT
      campaign.id,
      campaign.name,
      metrics.impressions,
      metrics.clicks,
      metrics.ctr,
      metrics.average_cpc,
      metrics.cost_micros,
      metrics.conversions
    FROM campaign
    WHERE segments.date DURING LAST_7_DAYS
    {campaign_filter}
    """

    campaign_data = []

    try:
        response = service.search(customer_id=customer_id, query=campaign_query)
        for row in response:
            campaign_data.append({
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "ctr": row.metrics.ctr,
                "avg_cpc": row.metrics.average_cpc,
                "cost": row.metrics.cost_micros / 1_000_000 if row.metrics.cost_micros else 0,
                "conversions": row.metrics.conversions
            })
    except Exception as e:
        print(f"Error fetching campaign metrics: {e}")

    # -----------------------
    # Ad Metrics
    # -----------------------
    ad_query = f"""
    SELECT
      campaign.id,
      campaign.name,
      ad_group.id,
      ad_group.name,
      ad_group_ad.ad.id,
      ad_group_ad.ad.name,
      metrics.impressions,
      metrics.clicks,
      metrics.ctr,
      metrics.average_cpc,
      metrics.cost_micros,
      metrics.conversions
    FROM ad_group_ad
    WHERE segments.date DURING LAST_7_DAYS
    {campaign_filter}
    """

    ad_data = []

    try:
        response = service.search(customer_id=customer_id, query=ad_query)
        for row in response:
            ad_data.append({
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name,
                "ad_id": row.ad_group_ad.ad.id,
                "ad_name": row.ad_group_ad.ad.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "ctr": row.metrics.ctr,
                "avg_cpc": row.metrics.average_cpc,
                "cost": row.metrics.cost_micros / 1_000_000 if row.metrics.cost_micros else 0,
                "conversions": row.metrics.conversions
            })
    except Exception as e:
        print(f"Error fetching ad metrics: {e}")

    return {
        "campaign_metrics": campaign_data,
        "ad_metrics": ad_data
    }


if __name__ == "__main__":
    data = get_metrics()

    print("\nCampaign Metrics:")
    for c in data["campaign_metrics"]:
        print(c)

    print("\nAd Metrics:")
    for a in data["ad_metrics"]:
        print(a)