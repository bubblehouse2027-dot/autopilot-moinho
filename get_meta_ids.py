"""
Run once on your laptop after creating the System User token (step 3 in README).
  pip install requests
  python get_meta_ids.py <SYSTEM_USER_TOKEN>
Prints the four values for GitHub Secrets.
"""
import sys

import requests

tok = sys.argv[1]
r = requests.get("https://graph.facebook.com/v21.0/me/accounts", params={
    "fields": "id,name,access_token,instagram_business_account{id,username}",
    "access_token": tok}).json()
if "error" in r:
    sys.exit(r["error"]["message"])
for p in r.get("data", []):
    ig = p.get("instagram_business_account") or {}
    print(f"\n=== Facebook page: {p['name']} ===")
    print("FB_PAGE_ID      =", p["id"])
    print("FB_PAGE_TOKEN   =", p["access_token"])
    print("IG_USER_ID      =", ig.get("id", "NOT LINKED — link Instagram to this page first"),
          f"(@{ig.get('username', '?')})")
    print("IG_ACCESS_TOKEN =", tok)
