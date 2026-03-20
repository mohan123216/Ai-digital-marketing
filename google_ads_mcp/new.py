import os
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient

load_dotenv()

# Load credentials from .env
config = {
    "developer_token": os.getenv("DEVELOPER_TOKEN"),
    "client_id": os.getenv("CLIENT_ID"),
    "client_secret": os.getenv("CLIENT_SECRET"),
    "refresh_token": os.getenv("REFRESH_TOKEN"),
    "login_customer_id": os.getenv("LOGIN_CUSTOMER_ID"),
    "use_proto_plus": True,
}

client = GoogleAdsClient.load_from_dict(config)

customer_id = os.getenv("CUSTOMER_ID")
budget_resource = os.getenv("BUDGET_RESOURCE_NAME")

campaign_service = client.get_service("CampaignService")

campaign_operation = client.get_type("CampaignOperation")
campaign = campaign_operation.create

# CHANGE NAME FOR NEW CAMPAIGN
campaign.name = "AI Campaign 2"

campaign.advertising_channel_type = (
    client.enums.AdvertisingChannelTypeEnum.SEARCH
)

campaign.status = client.enums.CampaignStatusEnum.PAUSED

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

print("✅ Campaign Created Successfully")
print(response.results[0].resource_name)