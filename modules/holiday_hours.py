"""VISIBILIDADE — pushes the special opening hours from client.yaml to Google."""
from datetime import date

import requests

from .common import CFG, env, google_headers, load_state, save_state


def _d(s):
    y, m, d = map(int, s.split("-"))
    return {"year": y, "month": m, "day": d}


def _t(s):
    h, m = map(int, s.split(":"))
    return {"hours": h, "minutes": m}


def run():
    items = [i for i in CFG.get("holiday_hours", []) if i["date"] >= date.today().isoformat()]
    sig = repr(items)
    state = load_state()
    if not items or state.get("holiday_sig") == sig:
        print("Holiday hours: nothing to change")
        return
    periods = []
    for i in items:
        p = {"startDate": _d(i["date"]), "endDate": _d(i["date"])}
        if i.get("closed"):
            p["closed"] = True
        else:
            p.update(openTime=_t(i["open"]), closeTime=_t(i["close"]))
        periods.append(p)
    r = requests.patch(
        f"https://mybusinessbusinessinformation.googleapis.com/v1/locations/{env('GBP_LOCATION_ID')}",
        params={"updateMask": "specialHours"}, headers=google_headers(), timeout=30,
        json={"specialHours": {"specialHourPeriods": periods}})
    print("Holiday hours", "OK" if r.ok else r.text)
    if r.ok:
        state["holiday_sig"] = sig
        save_state(state)
