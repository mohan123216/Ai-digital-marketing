#!/usr/bin/env python3
"""Script to add URL validation to launch.py"""

file_path = "google_ads_mcp/launch.py"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Validation function to add
validation_func = '''
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
'''

# Check if validation function already exists
if "_validate_final_url" in content:
    print("✅ URL validation function already exists")
else:
    # Add validation function after _parse_budget_usd
    marker = 'def _load_google_client():'
    if marker in content:
        content = content.replace(marker, validation_func + '\n' + marker)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Added URL validation function")
    else:
        print("❌ Could not find insertion point")

# Now add the validation call before appending final_url
if 'ad_group_ad.ad.final_urls.append(final_url)' in content:
    # Read again to get updates
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '_validate_final_url(final_url)' not in content:
        old_line = "        ad_group_ad.ad.final_urls.append(final_url)"
        new_code = '''        # Validate final_url before appending
        is_valid, error_msg = _validate_final_url(final_url)
        if not is_valid:
            return {
                "status": "validation_error",
                "message": f"Ad launch failed: {error_msg}",
            }

        ad_group_ad.ad.final_urls.append(final_url)'''
        
        content = content.replace(old_line, new_code)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Added URL validation check before appending")
    else:
        print("✅ URL validation check already exists")
else:
    print("❌ Could not find final_urls.append line")

print("✅ All updates complete!")
