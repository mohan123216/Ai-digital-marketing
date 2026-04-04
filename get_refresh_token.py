#!/usr/bin/env python3
"""
Get a new Google Ads refresh token using OAuth flow.
Run this script to authenticate and generate REFRESH_TOKEN for your .env file.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required for Google Ads API
SCOPES = ['https://www.googleapis.com/auth/adwords']

def get_refresh_token():
    """
    Perform OAuth2 flow and print the refresh token.
    """
    
    # Load credentials from .env or ask user
    client_id = input("Enter your CLIENT_ID (from Google Cloud Console): ").strip()
    client_secret = input("Enter your CLIENT_SECRET (from Google Cloud Console): ").strip()
    
    # Create credentials dict that InstalledAppFlow expects
    credentials_dict = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"]
        }
    }
    
    try:
        # Start OAuth flow
        flow = InstalledAppFlow.from_client_config(
            credentials_dict,
            scopes=SCOPES
        )
        
        print("\n🔐 Opening browser for Google login...")
        print("If browser doesn't open, manually visit the URL shown in the console.")
        
        credentials = flow.run_local_server(port=8080)
        
        # Extract refresh token
        refresh_token = credentials.refresh_token
        
        if refresh_token:
            print("\n✅ SUCCESS! Here's your refresh token:\n")
            print(f"REFRESH_TOKEN={refresh_token}\n")
            print("📝 Copy this value and update your .env file:")
            print("   google_ads_mcp/.env")
            print("   Replace the REFRESH_TOKEN= line with the value above")
        else:
            print("❌ No refresh token received. Try again.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you've entered the correct CLIENT_ID and CLIENT_SECRET")

if __name__ == "__main__":
    get_refresh_token()
