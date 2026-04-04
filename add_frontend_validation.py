#!/usr/bin/env python3
"""Script to add URL validation to App.jsx"""

file_path = "frontend/src/App.jsx"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Validation function to add
validation_func = '''  const validateFinalUrl = (url) => {
    if (!url || !url.trim()) return "Final URL is required.";
    url = url.trim();
    if (url.toLowerCase().includes('localhost')) return "Final URL cannot be 'localhost'. Please provide a valid domain (e.g., https://example.com).";
    if (!url.startsWith('http://') && !url.startsWith('https://')) return "Final URL must start with http:// or https://";
    try {
      const u = new URL(url);
      if (!u.hostname || !u.hostname.includes('.')) return "Final URL must contain a valid domain with a top-level domain (e.g., .com, .org).";
    } catch { return "Invalid URL format."; }
    return null;
  };
'''

# Check if validation function already exists
if "validateFinalUrl" in content:
    print("✅ URL validation function already exists")
else:
    # Add validation function before submitAd
    marker = '  const submitAd = async'
    if marker in content:
        content = content.replace(marker, validation_func + '\n\n' + marker)
        print("✅ Added URL validation function")
    else:
        print("❌ Could not find insertion point for validation function")

# Update submitAd to use validation
if "const submitAd = async" in content and "validateFinalUrl(final_url)" not in content:
    old_code = """const submitAd = async (e) => {
    e.preventDefault(); setAdFormError("");
    const { ad_name, headline_1, headline_2, headline_3, description_1, description_2, final_url, display_url_path_1, display_url_path_2, keywords_raw } = adForm;
    if (!headline_1.trim() || !headline_2.trim() || !headline_3.trim()) { setAdFormError("All three headlines are required."); return; }
    if (!description_1.trim() || !description_2.trim()) { setAdFormError("Both descriptions are required."); return; }
    if (!final_url.trim()) { setAdFormError("Final URL is required."); return; }"""
    
    new_code = """const submitAd = async (e) => {
    e.preventDefault(); setAdFormError("");
    const { ad_name, headline_1, headline_2, headline_3, description_1, description_2, final_url, display_url_path_1, display_url_path_2, keywords_raw } = adForm;
    if (!headline_1.trim() || !headline_2.trim() || !headline_3.trim()) { setAdFormError("All three headlines are required."); return; }
    if (!description_1.trim() || !description_2.trim()) { setAdFormError("Both descriptions are required."); return; }
    const urlError = validateFinalUrl(final_url);
    if (urlError) { setAdFormError(urlError); return; }"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ Updated submitAd with URL validation")
    else:
        print("⚠️ Could not find exact submitAd code pattern")

# Update submitMediaAd to use validation
if "const submitMediaAd = async" in content and "validateFinalUrl(final_url)" not in content:
    old_code = """const submitMediaAd = async (e) => {
    e.preventDefault(); setAdFormError("");
    const { ad_name, final_url, long_headline, business_name, headline_1, description_1, keywords_raw } = adForm;
    if (!final_url.trim()) { setAdFormError("Final URL is required."); return; }"""
    
    new_code = """const submitMediaAd = async (e) => {
    e.preventDefault(); setAdFormError("");
    const { ad_name, final_url, long_headline, business_name, headline_1, description_1, keywords_raw } = adForm;
    const urlError = validateFinalUrl(final_url);
    if (urlError) { setAdFormError(urlError); return; }"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ Updated submitMediaAd with URL validation")
    else:
        print("⚠️ Could not find exact submitMediaAd code pattern")

# Write the file
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ All updates complete!")
