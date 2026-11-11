"""
ALL PLANS — monthly e-mail report on the 1st.
Instagram always; Google Maps + reviews if google modules are on; Search Console if search_console is on.
"""
from datetime import date, timedelta

import requests

from .common import CLIENT, GBP_V4, GRAPH, SETTINGS, claude, enabled, env, google_headers, location_path, send_email

END = date.today().replace(day=1) - timedelta(days=1)
START = END.replace(day=1)
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
MONTH = f"{MESES[START.month - 1]} {START.year}"


def instagram():
    tok, uid = env("IG_ACCESS_TOKEN"), env("IG_USER_ID")
    prof = requests.get(f"{GRAPH}/{uid}", params={"fields": "followers_count", "access_token": tok}, timeout=30).json()
    ins = requests.get(f"{GRAPH}/{uid}/insights", timeout=30, params={
        "metric": "reach,profile_views", "period": "day", "metric_type": "total_value",
        "since": START.isoformat(), "until": (END + timedelta(days=1)).isoformat(), "access_token": tok}).json()
    out = {"Seguidores Instagram": prof.get("followers_count", "?")}
    names = {"reach": "Pessoas alcançadas no Instagram", "profile_views": "Visitas ao perfil"}
    for m in ins.get("data", []):
        out[names.get(m["name"], m["name"])] = m.get("total_value", {}).get("value", "?")
    return out


def google_maps(h):
    metrics = {"BUSINESS_IMPRESSIONS_MOBILE_MAPS": "Vistas no Google Maps",
               "BUSINESS_IMPRESSIONS_MOBILE_SEARCH": "Vistas na Pesquisa Google",
               "CALL_CLICKS": "Chamadas a partir do Google",
               "BUSINESS_DIRECTION_REQUESTS": "Pedidos de direções",
               "WEBSITE_CLICKS": "Cliques para o site"}
    params = [("dailyMetrics", m) for m in metrics] + [
        ("dailyRange.start_date.year", START.year), ("dailyRange.start_date.month", START.month),
        ("dailyRange.start_date.day", START.day), ("dailyRange.end_date.year", END.year),
        ("dailyRange.end_date.month", END.month), ("dailyRange.end_date.day", END.day)]
    r = requests.get(f"https://businessprofileperformance.googleapis.com/v1/locations/"
                     f"{env('GBP_LOCATION_ID')}:fetchMultiDailyMetricsTimeSeries",
                     params=params, headers=h, timeout=30).json()
    out = {}
    for block in r.get("multiDailyMetricTimeSeries", []):
        for s in block.get("dailyMetricTimeSeries", []):
            out[metrics[s["dailyMetric"]]] = sum(int(v.get("value", 0))
                                                 for v in s["timeSeries"].get("datedValues", []))
    rv = requests.get(f"{GBP_V4}/{location_path()}/reviews", params={"pageSize": 50}, headers=h, timeout=30).json()
    out["Novas avaliações"] = sum(1 for x in rv.get("reviews", [])
                                  if START.isoformat() <= x["createTime"][:10] <= END.isoformat())
    out["Média de estrelas"] = rv.get("averageRating", "?")
    out["Total de avaliações"] = rv.get("totalReviewCount", "?")
    return out


def search_console(h):
    site = requests.utils.quote(SETTINGS["search_console_site"], safe="")
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
    base = {"startDate": START.isoformat(), "endDate": END.isoformat()}
    tot = requests.post(url, json=base, headers=h, timeout=30).json().get("rows", [{}])[0]
    q = requests.post(url, json={**base, "dimensions": ["query"], "rowLimit": 50}, headers=h, timeout=30).json()
    rows = q.get("rows", [])
    top = [f"{r['keys'][0]} ({int(r['clicks'])} cliques)" for r in sorted(rows, key=lambda r: -r["clicks"])[:10]]
    wins = [r for r in rows if r["impressions"] >= 50 and r["ctr"] < 0.02]
    out = {"Cliques no Google para o site": int(tot.get("clicks", 0)),
           "Vezes que o site apareceu no Google": int(tot.get("impressions", 0))}
    return out, top, wins


def run():
    numbers, extra, wins = {}, "", []
    numbers.update(instagram())
    h = google_headers() if (enabled("google_posts") or enabled("review_replies") or enabled("search_console")) else None
    if h and (enabled("google_posts") or enabled("review_replies")):
        numbers.update(google_maps(h))
    if h and enabled("search_console"):
        sc, top, wins = search_console(h)
        numbers.update(sc)
        if top:
            extra += "\n\nO que as pessoas pesquisam para encontrar o site:\n" + "\n".join(f"  • {t}" for t in top)
    table = "\n".join(f"• {k}: {v}" for k, v in numbers.items())

    if wins:
        w = "\n".join(f"{r['keys'][0]}: {int(r['impressions'])} vistas, {int(r['clicks'])} cliques" for r in wins[:5])
        tip = claude(f"Para cada pesquisa abaixo (muitas vistas, poucos cliques) no site {CLIENT['website']}, "
                     f"sugere em 1 frase simples em português de Portugal o que melhorar (título, página, texto). "
                     f"Máx. 3 sugestões, lista com •:\n{w}", 300)
        extra += "\n\nOportunidades rápidas:\n" + (tip or w)

    intro = claude(f"Escreve 3 frases simples em português de Portugal para o dono de '{CLIENT['name']}' a "
                   f"explicar estes números de {MONTH} e o que significam para o negócio. Positivo mas "
                   f"honesto, sem inventar números:\n{table}", 300) \
        or f"Olá! Aqui está o resumo de {MONTH} da presença online de {CLIENT['name']}."
    body = f"{intro}\n\n{table}{extra}\n\nCom os melhores cumprimentos,\n{CLIENT.get('report_signed_by', '')}"
    send_email(f"{CLIENT['name']} — Relatório de {MONTH}", body, to=CLIENT.get("report_to"))
