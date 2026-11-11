"""
ONE-OFF ADD-ON — review kit, printable PDF generated from client.yaml.
  print/review_postcards.pdf   8 cards (A7, 105x74 mm) per A4 -> print 7 sheets = 56 cards
  print/review_stand.pdf       A5 table stand (fold in the middle)
Run:  python run.py print
"""
import io

import qrcode
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, A5, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .common import CLIENT, ROOT

pdfmetrics.registerFont(TTFont("Sans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("SansB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
COL = CLIENT.get("colors", {})
PRIMARY = HexColor(COL.get("primary", "#222222"))
ACCENT = HexColor(COL.get("accent", "#E8B04B"))
BG = HexColor(COL.get("background", "#FFFFFF"))

# Texts per sector — add a sector once, reuse for every client in it
TEXTS = {
    "pet-food": ("O seu cão gostou?", "Conte-nos no Google — ajuda outros tutores a encontrar alimentação natural."),
    "fitness": ("Gostou do treino?", "A sua avaliação no Google ajuda outras pessoas a começar."),
    "veg-box": ("Gostou do cabaz desta semana?", "Diga-nos no Google — ajuda outras famílias a comer melhor."),
    "party": ("A festa foi um sucesso?", "Deixe-nos uma avaliação no Google — ajuda outros pais a escolher."),
    "default": ("Gostou da experiência?", "A sua opinião no Google ajuda-nos muito."),
}


def qr_image(url):
    q = qrcode.QRCode(border=1, box_size=12, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(url)
    img = q.make_image(fill_color=COL.get("primary", "#000000"), back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def wrap(c, text, font, size, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if c.stringWidth(t, font, size) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def draw_card(c, x, y, w, h, qr):
    title, sub = TEXTS.get(CLIENT.get("sector"), TEXTS["default"])
    c.setFillColor(BG)
    c.rect(x, y, w, h, stroke=0, fill=1)
    c.setFillColor(PRIMARY)
    c.rect(x, y + h - 6 * mm, w, 6 * mm, stroke=0, fill=1)
    pad = 8 * mm
    tx_w = w - 2 * pad - 42 * mm
    c.setFont("SansB", 15)
    ty = y + h - 20 * mm
    for ln in wrap(c, title, "SansB", 15, tx_w):
        c.drawString(x + pad, ty, ln)
        ty -= 6.5 * mm
    c.setFillColor(ACCENT)
    c.setFont("SansB", 16)
    c.drawString(x + pad, ty - 1 * mm, "★★★★★")
    c.setFillColor(HexColor("#333333"))
    c.setFont("Sans", 9)
    ty -= 9 * mm
    for ln in wrap(c, sub, "Sans", 9, tx_w):
        c.drawString(x + pad, ty, ln)
        ty -= 4.5 * mm
    c.drawImage(qr, x + w - pad - 38 * mm, y + h / 2 - 22 * mm, 38 * mm, 38 * mm)
    c.setFont("Sans", 7)
    c.drawCentredString(x + w - pad - 19 * mm, y + h / 2 - 26 * mm, "Aponte a câmara")
    c.setFillColor(PRIMARY)
    c.setFont("SansB", 10)
    c.drawString(x + pad, y + 9 * mm, CLIENT["name"])
    c.setFont("Sans", 7.5)
    c.setFillColor(HexColor("#555555"))
    c.drawString(x + pad, y + 5 * mm, CLIENT.get("website", "").replace("https://", ""))
    c.setFillColor(HexColor("#888888"))
    c.drawRightString(x + w - pad, y + 5 * mm, "Obrigado!")


def postcards(out, qr):
    c = canvas.Canvas(str(out), pagesize=A4)
    W, H = A4
    cw, ch = W / 2, H / 4                    # 8 cards of 105 x 74 mm (A7) per A4
    for col in range(2):
        for row in range(4):
            draw_card(c, col * cw, row * ch, cw, ch, qr)
    c.setStrokeColor(HexColor("#BBBBBB"))
    c.setLineWidth(0.3)
    c.setDash(2, 2)
    c.line(W / 2, 0, W / 2, H)
    for row in range(1, 4):
        c.line(0, row * ch, W, row * ch)
    c.showPage()
    c.save()


def stand(out, qr):
    W, H = landscape(A5)
    c = canvas.Canvas(str(out), pagesize=(W, H))
    title, sub = TEXTS.get(CLIENT.get("sector"), TEXTS["default"])
    c.setFillColor(BG)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    for half in (0, 1):                      # same face on both sides of the fold
        ox = half * W / 2
        c.setFillColor(PRIMARY)
        c.rect(ox, H - 12 * mm, W / 2, 12 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("SansB", 12)
        c.drawCentredString(ox + W / 4, H - 8 * mm, CLIENT["name"])
        c.setFillColor(PRIMARY)
        c.setFont("SansB", 17)
        c.drawCentredString(ox + W / 4, H - 26 * mm, title)
        c.setFillColor(ACCENT)
        c.setFont("SansB", 20)
        c.drawCentredString(ox + W / 4, H - 36 * mm, "★★★★★")
        c.drawImage(qr, ox + W / 4 - 27 * mm, 26 * mm, 54 * mm, 54 * mm)
        c.setFillColor(HexColor("#333333"))
        c.setFont("Sans", 9)
        yy = 18 * mm
        for ln in wrap(c, sub, "Sans", 9, W / 2 - 20 * mm):
            c.drawCentredString(ox + W / 4, yy, ln)
            yy -= 4.5 * mm
    c.setStrokeColor(HexColor("#BBBBBB"))
    c.setDash(2, 2)
    c.line(W / 2, 0, W / 2, H)
    c.showPage()
    c.save()


def run():
    link = CLIENT["google_review_link"]
    outdir = ROOT / "print"
    outdir.mkdir(exist_ok=True)
    qr = qr_image(link)
    postcards(outdir / "review_postcards.pdf", qr)
    stand(outdir / "review_stand.pdf", qr)
    qrcode.make(link).save(outdir / "review_qr.png")   # also for NFC stands, stickers, receipts
    print("Print kit written to print/")
