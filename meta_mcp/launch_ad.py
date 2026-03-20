#!/usr/bin/env python3
"""
Meta Ad Launcher for Professional Mode - Run ads directly from your profile
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage

load_dotenv()

# ========== CONFIGURATION ==========
DEFAULT_IMAGE_PATH = "./ad_image.png"  # Your image
DEFAULT_LINK = "https://yourwebsite.com"
DEFAULT_HEADLINE = "Special Offer Just for You!"
DEFAULT_DESCRIPTION = "Check out our amazing products with 50% off today only!"
DEFAULT_CALL_TO_ACTION = "SHOP_NOW"
# ===================================

def get_first_ad_set():
    """Get the first ad set ID from launched_campaigns.json"""
    state_file = Path(__file__).parent / "launched_campaigns.json"
    
    if not state_file.exists():
        print("❌ No launched_campaigns.json found")
        return None
    
    with open(state_file, 'r') as f:
        data = json.load(f)
    
    launched = data.get("launched", {})
    if not launched:
        print("❌ No campaigns found in state file")
        return None
    
    # Get the first campaign
    first_key = list(launched.keys())[0]
    first_campaign = launched[first_key]
    
    ad_set_id = first_campaign.get("meta_adset_id")
    campaign_name = first_campaign.get("campaign_name", "Unknown")
    
    print(f"\n📌 Using campaign: {campaign_name}")
    print(f"   Ad Set ID: {ad_set_id}")
    
    return ad_set_id

def create_ad_with_professional_mode():
    """Create ad using Professional Mode (profile instead of page)"""
    
    print("=" * 50)
    print("🚀 PROFESSIONAL MODE AD LAUNCHER")
    print("=" * 50)
    
    # Get credentials
    app_id = os.getenv("META_APP_ID")
    app_secret = os.getenv("META_APP_SECRET")
    access_token = os.getenv("META_ACCESS_TOKEN")
    ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
    page_id=os.getenv("META_PAGE_ID")
    # In Professional Mode, we use the user ID instead of page ID
    # Get your Facebook user ID
    user_id = get_my_user_id(access_token)
    if not user_id:
        print("❌ Could not get user ID")
        return None
    
    print(f"✅ Professional Mode active for user: {user_id}")
    
    # Get ad set ID
    ad_set_id = get_first_ad_set()
    if not ad_set_id:
        print("\n❌ Could not find any ad sets to use")
        return None
    
    # Check image
    if not os.path.exists(DEFAULT_IMAGE_PATH):
        print(f"\n❌ Image not found: {DEFAULT_IMAGE_PATH}")
        print("Please place an ad image in the current directory named 'ad_image.png'")
        return None
    
    try:
        # Initialize API
        FacebookAdsApi.init(app_id, app_secret, access_token)
        
        if not ad_account_id.startswith("act_"):
            ad_account_id = f"act_{ad_account_id}"
        
        account = AdAccount(ad_account_id)
        
        # Step 1: Upload image
        print("\n📤 Uploading image...")
        image = AdImage(parent_id=account.get_id_assured())
        image[AdImage.Field.filename] = DEFAULT_IMAGE_PATH
        image.remote_create()
        image_hash = image[AdImage.Field.hash]
        print(f"✅ Image uploaded with hash: {image_hash}")
        
        # Step 2: Create creative - FOR PROFESSIONAL MODE
        # In Professional Mode, you use the user ID instead of page ID
        print("\n🎨 Creating ad creative for Professional Mode...")
        creative = AdCreative(parent_id=account.get_id_assured())
        
        # For Professional Mode, we use the user ID in the object_story_spec
        creative.update({
            AdCreative.Field.name: f"Creative_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            AdCreative.Field.object_story_spec: {
                "page_id": page_id,  # Use your user ID instead of page ID
                "link_data": {
                    "link": DEFAULT_LINK,
                    "message": DEFAULT_DESCRIPTION,
                    "name": DEFAULT_HEADLINE,
                    "description": DEFAULT_DESCRIPTION[:100],
                    "image_hash": image_hash,
                    "call_to_action": {
                        "type": DEFAULT_CALL_TO_ACTION
                    }
                }
            }
        })
        
        creative.remote_create()
        creative_id = creative["id"]
        print(f"✅ Creative created with ID: {creative_id}")
        
        # Step 3: Create ad
        print("\n📢 Creating ad...")
        ad_name = f"Professional_Ad_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ad = Ad(parent_id=account.get_id_assured())
        ad.update({
            Ad.Field.name: ad_name,
            Ad.Field.adset_id: ad_set_id,
            Ad.Field.creative: {"creative_id": creative_id},
            Ad.Field.status: "PAUSED"
        })
        ad.remote_create()
        
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Ad created with Professional Mode!")
        print("=" * 50)
        print(f"\n📊 Ad Details:")
        print(f"   Ad ID: {ad['id']}")
        print(f"   Ad Name: {ad_name}")
        print(f"   Ad Set ID: {ad_set_id}")
        print(f"   Creative ID: {creative_id}")
        print(f"   Running from: Your Profile (ID: {user_id})")
        print(f"   Status: PAUSED")
        
        # Save to log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ad_id": ad["id"],
            "ad_name": ad_name,
            "ad_set_id": ad_set_id,
            "creative_id": creative_id,
            "image_hash": image_hash,
            "mode": "professional"
        }
        
        log_file = Path(__file__).parent / "ad_launch_log.json"
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        print(f"\n📝 Log saved to: {log_file}")
        
        return ad["id"]
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_my_user_id(access_token):
    """Get your Facebook user ID"""
    try:
        url = "https://graph.facebook.com/v18.0/me"
        params = {"access_token": access_token, "fields": "id,name"}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Logged in as: {data.get('name')}")
            return data.get("id")
        else:
            print(f"❌ Failed to get user info: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting user ID: {e}")
        return None

def create_simple_boost_post():
    """Simpler approach - just boost an existing post from your profile"""
    print("\n🔄 Alternative: Boost an existing post")
    print("Since you're in Professional Mode, you can also:")
    print("1. Go to your Facebook profile")
    print("2. Create a post")
    print("3. Click 'Boost Post' button")
    print("4. Set your budget and audience")
    print("5. This is often easier for first-time ads!")

if __name__ == "__main__":
    # First, get your user info
    access_token = os.getenv("META_ACCESS_TOKEN")
    user_id = get_my_user_id(access_token)
    
    if user_id:
        print(f"\n👤 Your Professional Profile ID: {user_id}")
        print("This will be used as your 'page_id' in the API")
        
        # Try to create the ad
        result = create_ad_with_professional_mode()
        
        if result:
            print("\n" + "=" * 50)
            print("🎉 AD LAUNCH COMPLETE")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("❌ AD LAUNCH FAILED")
            print("=" * 50)
            create_simple_boost_post()
    else:
        print("❌ Could not verify your Facebook account")