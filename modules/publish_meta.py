"""
ESSENCIAL — publishes due posts from content/calendar.csv to Instagram + Facebook.

If you already have a working publisher from Natural Dog BARF / Platinum / Pedro,
paste its logic into publish_due() and keep the same calendar format. Everything
else in the template keeps working.

calendar.csv columns:
  date,time,type,caption,media,platforms[,cover]
  2026-11-04,19:00,image,"Texto…",posts/01.jpg,ig+fb
  type = image | reel | carousel (carousel: media = a.jpg|b.jpg|c.jpg)
  cover = optional cover JPG for reels (e.g. posts/01_capa.jpg)
"""
import csv
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from .common import GRAPH, ROOT, SETTINGS, env, load_state, remember, save_state

CAL = ROOT / "content" / "calendar.csv"
TZ = ZoneInfo("Europe/Lisbon")


def media_url(path):
    return SETTINGS["media_base_url"].rstrip("/") + "/content/media/" + path.strip()


def ig_container(params):
    r = requests.post(f"{GRAPH}/{env('IG_USER_ID')}/media",
                      data={**params, "access_token": env("IG_ACCESS_TOKEN")}, timeout=60).json()
    if "id" not in r:
        raise RuntimeError(r)
    cid = r["id"]
    for _ in range(30):                       # videos need processing time
        st = requests.get(f"{GRAPH}/{cid}", params={"fields": "status_code",
                          "access_token": env("IG_ACCESS_TOKEN")}, timeout=30).json()
        if st.get("status_code") in ("FINISHED", None):
            return cid
        if st.get("status_code") == "ERROR":
            raise RuntimeError(st)
        time.sleep(10)
    raise RuntimeError("Instagram processing timeout")


def post_instagram(row):
    files = row["media"].split("|")
    if row["type"] == "carousel":
        kids = [ig_container({"image_url": media_url(f), "is_carousel_item": "true"}) for f in files]
        cid = ig_container({"media_type": "CAROUSEL", "children": ",".join(kids), "caption": row["caption"]})
    elif row["type"] == "reel":
        params = {"media_type": "REELS", "video_url": media_url(files[0]), "caption": row["caption"],
                  "share_to_feed": "true"}
        if (row.get("cover") or "").strip():          # optional cover image (JPG 1080x1920)
            params["cover_url"] = media_url(row["cover"])
        cid = ig_container(params)
    else:
        cid = ig_container({"image_url": media_url(files[0]), "caption": row["caption"]})
    r = requests.post(f"{GRAPH}/{env('IG_USER_ID')}/media_publish",
                      data={"creation_id": cid, "access_token": env("IG_ACCESS_TOKEN")}, timeout=60).json()
    if "id" not in r:
        raise RuntimeError(r)
    return r["id"]


def post_facebook(row):
    page, tok = env("FB_PAGE_ID"), env("FB_PAGE_TOKEN")
    first = row["media"].split("|")[0]
    if row["type"] == "reel":
        r = requests.post(f"{GRAPH}/{page}/videos", data={"file_url": media_url(first),
                          "description": row["caption"], "access_token": tok}, timeout=120)
    else:
        r = requests.post(f"{GRAPH}/{page}/photos", data={"url": media_url(first),
                          "message": row["caption"], "access_token": tok}, timeout=60)
    r = r.json()
    if "id" not in r:
        raise RuntimeError(r)
    return r["id"]


def run():
    if not CAL.exists():
        print("No content/calendar.csv")
        return
    state = load_state()
    done = set(state.get("published", []))
    now = datetime.now(TZ)
    with CAL.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        key = f"{row['date']} {row['time']} {row['media']}"
        due = datetime.strptime(key[:16], "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if key in done or due > now:
            continue
        if now - due > timedelta(days=2):          # old rows (e.g. new repo): skip, don't flood
            print("Skipped (older than 2 days):", key)
            remember(state, "published", key, keep=2000)
            continue
        plats = row.get("platforms", "ig+fb")
        try:
            if "ig" in plats:
                print("Instagram:", post_instagram(row))
            if "fb" in plats and env("FB_PAGE_ID"):
                print("Facebook:", post_facebook(row))
            remember(state, "published", key, keep=2000)
        except Exception as e:                # one failed post never blocks the rest
            print("FAILED", key, e)
    save_state(state)
