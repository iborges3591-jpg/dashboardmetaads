"""
update_dashboard.py
===================
Busca dados diários de cada anúncio na Meta Marketing API
e atualiza o ficheiro data.json com os resultados.
"""

import os
import json
import requests
from datetime import datetime

# ─── Configuração ────────────────────────────────────────────────────────────

ACCESS_TOKEN = os.environ["META_ACCESS_TOKEN"]

ADS_MAP = {k: v for k, v in {
    "apcd_1": os.environ.get("META_AD_ID_APCD_1"),
    "apcd_2": os.environ.get("META_AD_ID_APCD_2"),
    "apcd_3": os.environ.get("META_AD_ID_APCD_3"),
    "aux_1":  os.environ.get("META_AD_ID_AUX_1"),
    "aux_2":  os.environ.get("META_AD_ID_AUX_2"),
    "aux_3":  os.environ.get("META_AD_ID_AUX_3"),
    "aux_4":  os.environ.get("META_AD_ID_AUX_4"),
    "aux_5":  os.environ.get("META_AD_ID_AUX_5"),
}.items() if v}

BUDGETS = {
    "apcd_1": {"10/05": 40, "11/05": 40, "12/05": 40, "13/05": 40, "14/05": 40, "15/05": 40, "16/05": 40, "17/05": 40, "18/05": 40, "19/05": 40, "20/05": 40, "21/05": 40, "22/05": 40, "23/05": 40, "24/05": 40, "25/05": 40, "26/05": 40, "27/05": 40, "28/05": 40, "29/05": 40, "30/05": 40, "31/05": 40},
    "apcd_2": {"10/05": 40, "11/05": 40, "12/05": 40, "13/05": 40, "14/05": 40, "15/05": 40, "16/05": 40, "17/05": 40, "18/05": 40, "19/05": 40, "20/05": 40, "21/05": 40, "22/05": 40, "23/05": 40, "24/05": 40, "25/05": 40, "26/05": 40, "27/05": 40, "28/05": 40, "29/05": 40, "30/05": 40, "31/05": 40},
    "apcd_3": {"25/05": 50, "26/05": 50, "27/05": 50, "28/05": 50, "29/05": 50, "30/05": 50, "31/05": 50},
    "aux_1":  {"10/05": 60, "11/05": 60, "12/05": 60, "13/05": 60, "14/05": 60, "15/05": 60, "16/05": 60, "17/05": 60, "18/05": 60, "19/05": 60, "20/05": 60, "21/05": 60, "22/05": 60, "23/05": 60, "24/05": 60, "25/05": 60, "26/05": 60, "27/05": 60, "28/05": 60, "29/05": 60, "30/05": 60, "31/05": 60},
    "aux_2":  {"10/05": 45, "11/05": 45, "12/05": 45, "13/05": 45, "14/05": 45, "15/05": 45, "16/05": 45, "17/05": 45, "18/05": 45, "19/05": 45, "20/05": 45, "21/05": 45, "22/05": 45, "23/05": 45, "24/05": 45, "25/05": 45, "26/05": 45, "27/05": 45, "28/05": 45, "29/05": 45, "30/05": 45, "31/05": 45},
    "aux_3":  {"10/05": 45, "11/05": 45, "12/05": 45, "13/05": 45, "14/05": 45, "15/05": 45, "16/05": 45, "17/05": 45, "18/05": 45, "19/05": 45, "20/05": 45, "21/05": 45, "22/05": 45, "23/05": 45, "24/05": 45, "25/05": 45, "26/05": 45, "27/05": 45, "28/05": 45, "29/05": 45, "30/05": 45, "31/05": 45},
    "aux_4":  {"25/05": 50, "26/05": 50, "27/05": 50, "28/05": 50, "29/05": 50, "30/05": 50, "31/05": 50},
    "aux_5":  {"25/05": 50, "26/05": 50, "27/05": 50, "28/05": 50, "29/05": 50, "30/05": 50, "31/05": 50},
}
DEFAULT_BUDGET = 40

CAMPAIGN_SINCE = "2026-05-10"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_budget(ad_key: str, date_br: str) -> int:
    return BUDGETS.get(ad_key, {}).get(date_br, DEFAULT_BUDGET)


def get_convs(actions: list) -> int:
    if not actions:
        return 0
    PRIORITY = [
        "onsite_conversion.messaging_conversation_started_7d",
        "onsite_conversion.messaging_first_reply",
        "onsite_conversion.total_messaging_connection",
    ]
    for conv_type in PRIORITY:
        for action in actions:
            if action.get("action_type") == conv_type:
                return int(action.get("value", 0))
    return 0


def br_date(iso_date: str) -> str:
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return dt.strftime("%d/%m")


# ─── Chamada à API ────────────────────────────────────────────────────────────

def fetch_insights(ad_id: str, since: str, until: str) -> list:
    url = f"https://graph.facebook.com/v20.0/{ad_id}/insights"
    params = {
        "access_token": ACCESS_TOKEN,
        "fields": "date_start,impressions,unique_inline_link_clicks,actions,spend",
        "time_range": json.dumps({"since": since, "until": until}),
        "time_increment": 1,
        "level": "ad",
    }
    resp = requests.get(url, params=params, timeout=30)

    if resp.status_code != 200:
        print(f"  ⚠️  Erro {resp.status_code} para ad {ad_id}: {resp.text[:300]}")
        return []

    return resp.json().get("data", [])


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    today_br = datetime.now().strftime("%d/%m/%Y")
    print(f"\n🔄 Iniciando atualização — {today_br}\n")

    data_file = "data.json"
    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = {}

    result = {
        "ultima_atualizacao": today_br,
        "periodo": f"{br_date(CAMPAIGN_SINCE)} a {br_date(today)}",
    }

    all_keys = ["apcd_1", "apcd_2", "apcd_3", "aux_1", "aux_2", "aux_3", "aux_4", "aux_5"]
    missing = [k for k in all_keys if k not in ADS_MAP]
    if missing:
        print(f"  ⚠️  Secrets não configurados (dados históricos mantidos): {', '.join(missing)}\n")

    for key in missing:
        result[key] = existing.get(key, [])

    for ad_key, ad_id in ADS_MAP.items():
        print(f"  📊 Buscando dados de '{ad_key}' (ID: {ad_id})...")
        rows = fetch_insights(ad_id, CAMPAIGN_SINCE, today)

        if not rows:
            print(f"     ⚠️  Sem dados — mantendo histórico existente")
            result[ad_key] = existing.get(ad_key, [])
            continue

        daily = []
        for row in rows:
            date_br   = br_date(row["date_start"])
            views     = int(row.get("impressions", 0))
            clicks    = int(row.get("unique_inline_link_clicks", 0))
            convs     = get_convs(row.get("actions", []))
            spent     = round(float(row.get("spend", 0)), 2)
            cpc       = round(spent / convs, 2) if convs > 0 else 0.0
            budget    = get_budget(ad_key, date_br)

            daily.append({
                "date":        date_br,
                "views":       views,
                "clicks":      clicks,
                "convs":       convs,
                "costPerConv": cpc,
                "spent":       spent,
                "budget":      budget,
            })

        result[ad_key] = daily
        total_convs = sum(d["convs"] for d in daily)
        total_spent = sum(d["spent"] for d in daily)
        print(f"     ✅ {len(daily)} dias | {total_convs} conversas | R$ {total_spent:.2f} investido")

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ data.json atualizado com sucesso!\n")


if __name__ == "__main__":
    main()
