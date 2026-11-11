"""
Run ONCE per client on your laptop to connect their Google Business Profile + Search Console.
  pip install google-auth-oauthlib requests
  python get_google_token.py client_secret.json
Log in with the Google account that manages the client's profile. Copy the output into GitHub Secrets.
"""
import sys

import requests
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/business.manage",
          "https://www.googleapis.com/auth/webmasters.readonly"]

creds = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES).run_local_server(
    port=0, access_type="offline", prompt="consent")
h = {"Authorization": f"Bearer {creds.token}"}
print("\nGBP_CLIENT_ID     =", creds.client_id)
print("GBP_CLIENT_SECRET =", creds.client_secret)
print("GBP_REFRESH_TOKEN =", creds.refresh_token)

for a in requests.get("https://mybusinessaccountmanagement.googleapis.com/v1/accounts", headers=h).json().get("accounts", []):
    print(f"\n{a.get('accountName')}  ->  GBP_ACCOUNT_ID = {a['name'].split('/')[1]}")
    locs = requests.get(f"https://mybusinessbusinessinformation.googleapis.com/v1/{a['name']}/locations",
                        params={"readMask": "name,title"}, headers=h).json()
    for l in locs.get("locations", []):
        print(f"   {l['title']}  ->  GBP_LOCATION_ID = {l['name'].split('/')[1]}")

sites = requests.get("https://searchconsole.googleapis.com/webmasters/v3/sites", headers=h).json()
for s in sites.get("siteEntry", []):
    print("Search Console site (put in client.yaml):", s["siteUrl"])
