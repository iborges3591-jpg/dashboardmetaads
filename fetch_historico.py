"""
fetch_historico.py
Busca o historico completo (diario) de TODOS os anuncios da conta Meta
(ativos e inativos) desde o inicio do dashboard e grava em historico.json.
"""
import os, json, requests
from datetime import datetime

ACCESS_TOKEN = os.environ["META_ACCESS_TOKEN"]
ACCOUNT_ID   = os.environ.get("META_ACCOUNT_ID", "1600485061005605")
SINCE        = "2026-05-10"
API          = "https://graph.facebook.com/v20.0"

STATUSES = ["ACTIVE", "PAUSED", "CAMPAIGN_PAUSED", "ADSET_PAUSED", "ARCHIVED",
            "DISAPPROVED", "PENDING_REVIEW", "WITH_ISSUES", "IN_PROCESS"]

def paged(url, params):
    out = []
    while url:
        r = requests.get(url, params=params, timeout=60)
        if r.status_code != 200:
            print("  erro", r.status_code, r.text[:300])
            break
        b = r.json()
        out.extend(b.get("data", []))
        url = b.get("paging", {}).get("next")
        params = {}
    return out

def get_convs(actions):
    if not actions:
        return 0
    for t in ["onsite_conversion.messaging_conversation_started_7d",
              "onsite_conversion.messaging_first_reply",
              "onsite_conversion.total_messaging_connection"]:
        for a in actions:
            if a.get("action_type") == t:
                return int(a.get("value", 0))
    return 0

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    ads = paged(f"{API}/act_{ACCOUNT_ID}/ads", {
        "access_token": ACCESS_TOKEN,
        "fields": "id,name,effective_status,created_time,campaign{id,name},adset{id,name}",
        "effective_status": json.dumps(STATUSES),
        "limit": 100,
    })
    print(f"{len(ads)} anuncios encontrados na conta {ACCOUNT_ID}")
    result = {"gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
              "desde": SINCE, "anuncios": []}
    for ad in ads:
        rows = paged(f"{API}/{ad['id']}/insights", {
            "access_token": ACCESS_TOKEN,
            "fields": "date_start,impressions,unique_inline_link_clicks,actions,spend",
            "time_range": json.dumps({"since": SINCE, "until": today}),
            "time_increment": 1, "level": "ad", "limit": 200,
        })
        daily = []
        for r in rows:
            d = datetime.strptime(r["date_start"], "%Y-%m-%d").strftime("%d/%m")
            convs = get_convs(r.get("actions", []))
            spent = round(float(r.get("spend", 0)), 2)
            daily.append({
                "date": d, "iso": r["date_start"],
                "views": int(r.get("impressions", 0)),
                "clicks": int(r.get("unique_inline_link_clicks", 0)),
                "convs": convs, "spent": spent,
                "costPerConv": round(spent / convs, 2) if convs else 0.0,
            })
        daily.sort(key=lambda x: x["iso"])
        result["anuncios"].append({
            "id": ad["id"], "nome": ad.get("name", ""),
            "status": ad.get("effective_status", ""),
            "criado": ad.get("created_time", "")[:10],
            "campanha": (ad.get("campaign") or {}).get("name", ""),
            "conjunto": (ad.get("adset") or {}).get("name", ""),
            "daily": daily,
        })
        print(f"  {ad['id']} {ad.get('name','')[:40]}: {len(daily)} dias, "
              f"{sum(x['convs'] for x in daily)} conv, R$ {sum(x['spent'] for x in daily):.2f}")
    with open("historico.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("historico.json gerado")

if __name__ == "__main__":
    main()
