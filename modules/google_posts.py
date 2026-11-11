"""VISIBILIDADE — copies new Instagram posts to the Google Business Profile."""
import re
from datetime import datetime, timedelta, timezone

import requests

from .common import CLIENT, GBP_V4, GRAPH, SETTINGS, env, google_headers, load_state, location_path, remember, save_state


def clean(text):
    text = re.sub(r"[#@]\w+", "", text or "")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()[:1450]


def run():
    state = load_state()
    today = datetime.now(timezone.utc).date().isoformat()
    if state.get("google_last_day") == today:      # max one Google post per day
        print("Google posts: already posted today")
        return
    since = datetime.now(timezone.utc) - timedelta(days=7)
    ig = requests.get(f"{GRAPH}/{env('IG_USER_ID')}/media", timeout=30, params={
        "fields": "id,caption,media_type,media_url,thumbnail_url,timestamp",
        "limit": 15, "access_token": env("IG_ACCESS_TOKEN")}).json()
    new = sorted([p for p in ig.get("data", [])
                  if p["id"] not in state.get("google_posted", [])
                  and datetime.strptime(p["timestamp"], "%Y-%m-%dT%H:%M:%S%z") > since],
                 key=lambda p: p["timestamp"])
    if not new:
        print("Google posts: nothing new")
        return
    h = google_headers()
    for p in new[: int(SETTINGS.get("google_posts_per_run", 1))]:
        img = p.get("thumbnail_url") if p["media_type"] == "VIDEO" else p.get("media_url")
        body = {"languageCode": CLIENT.get("language", "pt-PT"), "topicType": "STANDARD",
                "summary": clean(p.get("caption")),
                "callToAction": {"actionType": "LEARN_MORE", "url": CLIENT["website"]}}
        if img:
            body["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": img}]
        r = requests.post(f"{GBP_V4}/{location_path()}/localPosts", json=body, headers=h, timeout=60)
        print("Google post", p["id"], "OK" if r.ok else r.text)
        if r.ok:
            remember(state, "google_posted", p["id"])
            state["google_last_day"] = today
    save_state(state)
