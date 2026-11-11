"""
VISIBILIDADE — reviews.
- review_replies : 4-5★ answered automatically, 1-3★ e-mailed to you (never auto-answered)
- review_to_post : new 5★ reviews become a branded Instagram image + calendar row
"""
import csv
import random
import textwrap
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageDraw, ImageFont

from .common import (CLIENT, GBP_V4, ROOT, SETTINGS, claude, enabled, google_headers,
                     load_state, location_path, remember, save_state, send_email)

STARS = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
TEMPLATES = [
    "Muito obrigado, {n}! Ficamos mesmo felizes por saber que gostou. Até breve!",
    "Obrigado pela sua avaliação, {n}! É um prazer tê-lo(a) como cliente.",
    "{n}, muito obrigado pelas palavras simpáticas! Conte sempre connosco.",
    "Que bom ler isto, {n}! Obrigado por escolher {b}. Até à próxima!",
]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def reply_text(name, stars, comment):
    txt = claude(
        f"Escreve uma resposta curta (máx. 2 frases), calorosa, em português de Portugal, a esta "
        f"avaliação de {stars} estrelas no Google para '{CLIENT['name']}'. Tom: {CLIENT.get('tone', '')}. "
        f"Cliente: {name}. Comentário: \"{comment or '(sem texto)'}\". Não inventes factos. Só o texto.", 200)
    return txt or random.choice(TEMPLATES).format(n=name, b=CLIENT["name"])


def review_image(name, comment, out):
    c = CLIENT.get("colors", {})
    W = 1080
    img = Image.new("RGB", (W, W), c.get("background", "#FFFFFF"))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 24], fill=c.get("primary", "#222222"))
    d.text((W // 2, 170), "★★★★★", font=ImageFont.truetype(FONT_B, 90), fill=c.get("accent", "#E8B04B"), anchor="mm")
    body = "“" + (comment.strip() if comment else "Excelente!") + "”"
    lines = textwrap.wrap(body, 30)[:8]
    f = ImageFont.truetype(FONT, 50)
    y = 540 - len(lines) * 34
    for ln in lines:
        d.text((W // 2, y), ln, font=f, fill=c.get("primary", "#222222"), anchor="mm")
        y += 68
    d.text((W // 2, y + 50), f"— {name}", font=ImageFont.truetype(FONT_B, 44), fill="#555555", anchor="mm")
    d.text((W // 2, 990), f"{CLIENT['name']} · Avaliação Google", font=ImageFont.truetype(FONT, 34),
           fill="#777777", anchor="mm")
    logo = ROOT / CLIENT.get("logo", "")
    if CLIENT.get("logo") and logo.exists():
        lg = Image.open(logo).convert("RGBA")
        lg.thumbnail((180, 180))
        img.paste(lg, (W - lg.width - 40, 40), lg)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=92)


def queue_review_post(rid, name, comment):
    rel = f"reviews/{rid[:12]}.jpg"
    review_image(name, comment, ROOT / "content" / "media" / rel)
    when = datetime.now(ZoneInfo("Europe/Lisbon")) + timedelta(days=1)
    caption = claude(
        f"Escreve uma legenda curta de Instagram em português de Portugal (2-3 frases + 3 hashtags) a "
        f"agradecer esta avaliação de 5 estrelas de {name} a '{CLIENT['name']}': \"{comment}\". "
        f"Tom: {CLIENT.get('tone', '')}. Termina a convidar outros clientes a avaliar.", 200) \
        or f"Obrigado, {name}! ⭐⭐⭐⭐⭐ Avaliações como esta fazem o nosso dia. Já é cliente? Deixe também a sua opinião no Google (link na bio)."
    with (ROOT / "content" / "calendar.csv").open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow([when.strftime("%Y-%m-%d"), SETTINGS.get("review_post_slot", "12:30"),
                                "image", caption, rel, "ig+fb"])
    print("Queued review post", rel)


def run():
    state = load_state()
    h = google_headers()
    data = requests.get(f"{GBP_V4}/{location_path()}/reviews", params={"pageSize": 50},
                        headers=h, timeout=30).json()
    alerts = []
    for rv in data.get("reviews", []):
        rid = rv["reviewId"]
        stars = STARS.get(rv.get("starRating"), 0)
        name = (rv.get("reviewer", {}).get("displayName") or "Cliente").split(" ")[0]
        comment = rv.get("comment", "")

        if enabled("review_to_post") and rid not in state.get("review_posted", []):
            if stars >= int(SETTINGS.get("review_post_min_stars", 5)) and len(comment) >= 20:
                queue_review_post(rid, name, comment)
            remember(state, "review_posted", rid)

        if enabled("review_replies") and not rv.get("reviewReply") and rid not in state.get("replied", []):
            if stars >= 4:
                r = requests.put(f"{GBP_V4}/{rv['name']}/reply", headers=h, timeout=30,
                                 json={"comment": reply_text(name, stars, comment)})
                print("Reply", rid, "OK" if r.ok else r.text)
            else:
                alerts.append(f"{stars}★ — {name}:\n{comment}\n")
            remember(state, "replied", rid)

    if alerts:
        send_email(f"[{CLIENT['name']}] Avaliação a responder manualmente", "\n".join(alerts))
    save_state(state)
