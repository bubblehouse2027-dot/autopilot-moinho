"""Shared helpers for every module: config, Google auth, Claude, state, e-mail."""
import json
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
CFG = yaml.safe_load((ROOT / "client.yaml").read_text(encoding="utf-8"))
CLIENT = CFG["client"]
SETTINGS = CFG.get("settings", {})
STATE_FILE = ROOT / "state.json"
GBP_V4 = "https://mybusiness.googleapis.com/v4"
GRAPH = "https://graph.facebook.com/v21.0"


def enabled(module):
    return bool(CFG.get("modules", {}).get(module))


def env(name, default=None):
    return os.environ.get(name) or default


# ---------- state (what was already posted / replied) ----------
def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def remember(state, key, value, keep=500):
    lst = state.setdefault(key, [])
    lst.append(value)
    state[key] = lst[-keep:]


# ---------- Google ----------
def google_headers():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": env("GBP_CLIENT_ID"),
        "client_secret": env("GBP_CLIENT_SECRET"),
        "refresh_token": env("GBP_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }, timeout=30)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def location_path():
    return f"accounts/{env('GBP_ACCOUNT_ID')}/locations/{env('GBP_LOCATION_ID')}"


# ---------- Claude (optional) ----------
def claude(prompt, max_tokens=400):
    """Returns Claude's answer, or None if no ANTHROPIC_API_KEY is set."""
    key = env("ANTHROPIC_API_KEY")
    if not key:
        return None
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=60,
                      headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                      json={"model": env("CLAUDE_MODEL", "claude-haiku-5-5"), "max_tokens": max_tokens,
                            "messages": [{"role": "user", "content": prompt}]})
    if not r.ok:
        print("Claude API error:", r.text)
        return None
    return r.json()["content"][0]["text"].strip()


# ---------- e-mail ----------
def send_email(subject, body, to=None):
    to = to or env("ALERT_TO")
    if not env("SMTP_USER") or not to:
        print(f"[e-mail not configured] {subject}\n{body}")
        return
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"], msg["From"], msg["To"] = subject, env("SMTP_USER"), to
    with smtplib.SMTP_SSL(env("SMTP_HOST", "smtp.gmail.com"), 465) as s:
        s.login(env("SMTP_USER"), env("SMTP_PASSWORD"))
        s.send_message(msg)
