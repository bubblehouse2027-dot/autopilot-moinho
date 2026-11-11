"""ONE-OFF ADD-ON — link-in-bio page, generated into docs/index.html (publish with GitHub Pages)."""
import html

from .common import CFG, CLIENT, ROOT


def run():
    c = CLIENT.get("colors", {})
    links = "\n".join(
        f'<a class="btn" href="{html.escape(l["url"])}">{html.escape(l["label"])}</a>'
        for l in CFG.get("links", []))
    page = f"""<!doctype html><html lang="pt-PT"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(CLIENT['name'])}</title>
<style>
body{{margin:0;font-family:system-ui,sans-serif;background:{c.get('background', '#fff')};color:{c.get('primary', '#222')};
display:flex;justify-content:center}}
main{{max-width:440px;width:100%;padding:48px 16px;text-align:center}}
h1{{font-size:26px;margin:0 0 6px}} p{{margin:0 0 28px;opacity:.75}}
.btn{{display:block;margin:12px 0;padding:16px;border-radius:14px;background:{c.get('primary', '#222')};color:#fff;
text-decoration:none;font-weight:600}}
.btn:nth-child(odd){{background:{c.get('accent', '#E8B04B')};color:{c.get('primary', '#222')}}}
</style></head><body><main>
<h1>{html.escape(CLIENT['name'])}</h1><p>@{html.escape(CLIENT.get('instagram_handle', ''))}</p>
{links}
</main></body></html>"""
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "index.html").write_text(page, encoding="utf-8")
    print("Link page written to docs/index.html")
