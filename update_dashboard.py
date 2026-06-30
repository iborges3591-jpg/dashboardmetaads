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
    "apcd_1":    os.environ.get("META_AD_ID_APCD_1"),
    "apcd_2":    os.environ.get("META_AD_ID_APCD_2"),
    "apcd_3":    os.environ.get("META_AD_ID_APCD_3"),
    "aux_1":     os.environ.get("META_AD_ID_AUX_1"),
    "aux_1b":    os.environ.get("META_AD_ID_AUX_1B"),   # continuação de aux_1 a partir de 04/06
    "aux_pinos":  os.environ.get("META_AD_ID_AUX_PINOS"),
    "priscila_1": os.environ.get("META_AD_ID_PRISCILA_1"),  # Indenização para o trabalhador
    "priscila_2": os.environ.get("META_AD_ID_PRISCILA_2"),  # Trabalhador CLT que sofreu
}.items() if v}

BUDGETS = {
    "apcd_1": {
        "10/05": 40, "11/05": 40, "12/05": 40, "13/05": 40, "14/05": 40,
        "15/05": 40, "16/05": 40, "17/05": 40, "18/05": 40, "19/05": 40,
        "20/05": 40, "21/05": 40, "22/05": 40, "23/05": 40, "24/05": 40,
        "25/05": 40, "26/05": 40, "27/05": 40, "28/05": 40, "29/05": 40,
        "30/05": 40, "31/05": 40,
        "01/06": 40, "02/06": 40, "03/06": 40, "04/06": 40, "05/06": 40,
        "06/06": 40, "07/06": 40, "08/06": 40, "09/06": 40, "10/06": 40,
        "11/06": 40, "12/06": 40, "13/06": 40, "14/06": 40, "15/06": 40,
        "16/06": 40, "17/06": 40, "18/06": 40, "19/06": 40, "20/06": 40,
        "21/06": 40, "22/06": 40, "23/06": 40, "24/06": 40, "25/06": 40,
        "26/06": 40, "27/06": 40, "28/06": 40, "29/06": 40, "30/06": 40,
    },
    "apcd_2": {
        "10/05": 40, "11/05": 40, "12/05": 40, "13/05": 40, "14/05": 40,
        "15/05": 40, "16/05": 40, "17/05": 40, "18/05": 40, "19/05": 40,
        "20/05": 40, "21/05": 40, "22/05": 40, "23/05": 40, "24/05": 40,
        "25/05": 40, "26/05": 40, "27/05": 40, "28/05": 40, "29/05": 40,
        "30/05": 40, "31/05": 40,
        "01/06": 40, "02/06": 40, "03/06": 40, "04/06": 40, "05/06": 40,
        "06/06": 40, "07/06": 40, "08/06": 40, "09/06": 40, "10/06": 40,
        "11/06": 40, "12/06": 40, "13/06": 40, "14/06": 40, "15/06": 40,
        "16/06": 40, "17/06": 40, "18/06": 40, "19/06": 40, "20/06": 40,
        "21/06": 40, "22/06": 40, "23/06": 40, "24/06": 40, "25/06": 40,
        "26/06": 40, "27/06": 40, "28/06": 40, "29/06": 40, "30/06": 40,
    },
    "apcd_3": {
        "25/05": 50, "26/05": 50, "27/05": 50, "28/05": 50, "29/05": 50,
        "30/05": 50, "31/05": 50,
        "01/06": 50, "02/06": 50, "03/06": 50, "04/06": 50, "05/06": 50,
        "06/06": 50, "07/06": 50, "08/06": 50, "09/06": 50, "10/06": 50,
        "11/06": 50, "12/06": 50, "13/06": 50, "14/06": 50, "15/06": 50,
        "16/06": 50, "17/06": 50, "18/06": 50, "19/06": 50, "20/06": 50,
        "21/06": 50, "22/06": 50, "23/06": 50, "24/06": 50, "25/06": 50,
        "26/06": 50, "27/06": 50, "28/06": 50, "29/06": 50, "30/06": 50,
    },
    "aux_1": {
        "10/05": 60, "11/05": 60, "12/05": 60, "13/05": 60, "14/05": 60,
        "15/05": 60, "16/05": 60, "17/05": 60, "18/05": 60, "19/05": 60,
        "20/05": 60, "21/05": 60, "22/05": 60, "23/05": 60, "24/05": 60,
        "25/05": 60, "26/05": 60, "27/05": 60, "28/05": 60, "29/05": 60,
        "30/05": 60, "31/05": 60,
        "01/06": 60, "02/06": 60, "03/06": 60, "04/06": 60, "05/06": 60,
        "06/06": 60, "07/06": 60, "08/06": 60, "09/06": 60, "10/06": 60,
        "11/06": 60, "12/06": 60, "13/06": 60, "14/06": 60, "15/06": 60,
        "16/06": 60, "17/06": 60, "18/06": 60, "19/06": 60, "20/06": 60,
        "21/06": 60, "22/06": 60, "23/06": 60, "24/06": 60, "25/06": 60,
        "26/06": 60, "27/06": 60, "28/06": 60, "29/06": 60, "30/06": 60,
    },
    # aux_1b usa o mesmo orçamento de aux_1 (mesma campanha, novo ID a partir de 04/06)
    "aux_1b": {
        "04/06": 60, "05/06": 60, "06/06": 60, "07/06": 60, "08/06": 60,
        "09/06": 60, "10/06": 60, "11/06": 60, "12/06": 60, "13/06": 60,
        "14/06": 60, "15/06": 60, "16/06": 60, "17/06": 60, "18/06": 60,
        "19/06": 60, "20/06": 60, "21/06": 60, "22/06": 60, "23/06": 60,
        "24/06": 60, "25/06": 60, "26/06": 60, "27/06": 60, "28/06": 60,
        "29/06": 60, "30/06": 60,
    },
    "aux_pinos": {
        "09/06": 50,  "10/06": 90,  "11/06": 100, "12/06": 90,  "13/06": 80,
        "14/06": 70,  "15/06": 70,  "16/06": 70,  "17/06": 70,  "18/06": 70,
        "19/06": 70,  "20/06": 70,  "21/06": 70,  "22/06": 70,  "23/06": 70,
        "24/06": 70,  "25/06": 70,  "26/06": 70,  "27/06": 70,  "28/06": 70,
        "29/06": 70,  "30/06": 70,
    },
    "priscila_1": {
        "10/05": 50, "11/05": 50, "12/05": 50, "13/05": 50, "14/05": 50,
        "15/05": 50, "16/05": 50, "17/05": 50, "18/05": 50, "19/05": 50,
        "20/05": 50, "21/05": 50, "22/05": 50, "23/05": 50, "24/05": 50,
        "25/05": 50, "26/05": 50, "27/05": 50, "28/05": 50, "29/05": 50,
        "30/05": 50, "31/05": 50,
        "01/06": 50, "02/06": 50, "03/06": 50, "04/06": 50, "05/06": 50,
        "06/06": 50, "07/06": 50, "08/06": 50, "09/06": 50, "10/06": 50,
        "11/06": 50, "12/06": 50, "13/06": 50, "14/06": 50, "15/06": 50,
        "16/06": 50, "17/06": 50, "18/06": 50, "19/06": 50, "20/06": 50,
        "21/06": 50, "22/06": 50, "23/06": 50, "24/06": 50, "25/06": 50,
        "26/06": 50, "27/06": 50, "28/06": 50, "29/06": 50, "30/06": 50,
    },
    "priscila_2": {
        "10/05": 50, "11/05": 50, "12/05": 50, "13/05": 50, "14/05": 50,
        "15/05": 50, "16/05": 50, "17/05": 50, "18/05": 50, "19/05": 50,
        "20/05": 50, "21/05": 50, "22/05": 50, "23/05": 50, "24/05": 50,
        "25/05": 50, "26/05": 50, "27/05": 50, "28/05": 50, "29/05": 50,
        "30/05": 50, "31/05": 50,
        "01/06": 50, "02/06": 50, "03/06": 50, "04/06": 50, "05/06": 50,
        "06/06": 50, "07/06": 50, "08/06": 50, "09/06": 50, "10/06": 50,
        "11/06": 50, "12/06": 50, "13/06": 50, "14/06": 50, "15/06": 50,
        "16/06": 50, "17/06": 50, "18/06": 50, "19/06": 50, "20/06": 50,
        "21/06": 50, "22/06": 50, "23/06": 50, "24/06": 50, "25/06": 50,
        "26/06": 50, "27/06": 50, "28/06": 50, "29/06": 50, "30/06": 50,
    },
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
    """Busca dados diários com suporte a paginação (Meta limita a ~25 registos por página)."""
    url = f"https://graph.facebook.com/v20.0/{ad_id}/insights"
    params = {
        "access_token": ACCESS_TOKEN,
        "fields": "date_start,impressions,unique_inline_link_clicks,actions,spend",
        "time_range": json.dumps({"since": since, "until": until}),
        "time_increment": 1,
        "level": "ad",
        "limit": 90,  # até 3 meses de dados diários numa só página
    }

    all_data = []
    current_url = url
    current_params = params

    while True:
        resp = requests.get(current_url, params=current_params, timeout=30)
        if resp.status_code != 200:
            print(f"  ⚠️ Erro {resp.status_code} para ad {ad_id}: {resp.text[:300]}")
            return []

        body = resp.json()
        all_data.extend(body.get("data", []))

        # Seguir próxima página se existir
        next_page = body.get("paging", {}).get("next")
        if not next_page:
            break
        current_url = next_page
        current_params = {}  # URL de paginação já contém todos os parâmetros

    return all_data

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

    # aux_1b é a continuação de aux_1 (mesmo anúncio, novo ID Meta a partir de 04/06).
    # É tratado internamente mas fundido em "aux_1" no output final.
    all_keys = ["apcd_1", "apcd_2", "apcd_3", "aux_1", "aux_pinos"]
    missing = [k for k in all_keys if k not in ADS_MAP and "aux_1b" not in ADS_MAP]
    # aux_1 pode estar em falta do ADS_MAP mas ser coberto por aux_1b — não alertar nesse caso
    missing_display = [k for k in all_keys if k not in ADS_MAP and not (k == "aux_1" and "aux_1b" in ADS_MAP)]
    if missing_display:
        print(f"  ⚠️ Secrets não configurados (dados históricos mantidos): {', '.join(missing_display)}\n")

    for key in all_keys:
        if key not in ADS_MAP and not (key == "aux_1" and "aux_1b" in ADS_MAP):
            result[key] = existing.get(key, [])

    raw = {}   # armazenamento temporário antes de fundir aux_1 + aux_1b

    for ad_key, ad_id in ADS_MAP.items():
        print(f"  📊 Buscando dados de '{ad_key}' (ID: {ad_id})...")
        rows = fetch_insights(ad_id, CAMPAIGN_SINCE, today)

        if not rows:
            print(f"  ⚠️ Sem dados — mantendo histórico existente")
            raw[ad_key] = existing.get(ad_key, [])
            continue

        daily = []
        for row in rows:
            date_br = br_date(row["date_start"])
            views   = int(row.get("impressions", 0))
            clicks  = int(row.get("unique_inline_link_clicks", 0))
            convs   = get_convs(row.get("actions", []))
            spent   = round(float(row.get("spend", 0)), 2)
            cpc     = round(spent / convs, 2) if convs > 0 else 0.0
            # aux_1b herda o orçamento de aux_1 (mesma campanha)
            budget_key = "aux_1" if ad_key == "aux_1b" else ad_key
            budget  = get_budget(budget_key, date_br)

            daily.append({
                "date":        date_br,
                "views":       views,
                "clicks":      clicks,
                "convs":       convs,
                "costPerConv": cpc,
                "spent":       spent,
                "budget":      budget,
            })

        raw[ad_key] = daily
        total_convs = sum(d["convs"] for d in daily)
        total_spent = sum(d["spent"] for d in daily)
        print(f"  ✅ {len(daily)} dias | {total_convs} conversas | R$ {total_spent:.2f} investido")

    # ── Fundir aux_1 + aux_1b numa única série cronológica ──────────────────────
    aux1_data  = raw.get("aux_1",  existing.get("aux_1",  []))
    aux1b_data = raw.get("aux_1b", [])

    if aux1b_data:
        # Evita duplicar datas (se por alguma razão ambos os IDs devolverem o mesmo dia)
        existing_dates = {d["date"] for d in aux1_data}
        for entry in aux1b_data:
            if entry["date"] not in existing_dates:
                aux1_data.append(entry)
        # Ordenar por data (DD/MM → comparação como MMDD)
        aux1_data.sort(key=lambda d: (d["date"][3:5], d["date"][0:2]))
        total_convs = sum(d["convs"] for d in aux1_data)
        total_spent = sum(d["spent"] for d in aux1_data)
        print(f"\n  🔗 aux_1 fundido com aux_1b → {len(aux1_data)} dias totais | "
              f"{total_convs} conversas | R$ {total_spent:.2f}")

    result["aux_1"] = aux1_data

    # apcd_1 = CIRURGIA COM PINOS — parou em ~12/06/2026, sem continuação
    # Limpar entradas do ARTROSE que foram fundidas incorretamente (datas 13-30/06 exceto zeros originais)
    apcd1_data = raw.get("apcd_1", existing.get("apcd_1", []))
    _zeros_originais = {"15/06", "17/06"}
    apcd1_data = [d for d in apcd1_data if not (
        d["date"][3:5] == "06" and int(d["date"][:2]) > 12 and d["date"] not in _zeros_originais
    )]
    apcd1_data.sort(key=lambda d: (d["date"][3:5], d["date"][0:2]))
    result["apcd_1"] = apcd1_data

    # Copiar restantes (excluindo apcd_1b e aux_1b que já foram fundidos)
    for key in ["apcd_2", "apcd_3", "aux_pinos", "priscila_1", "priscila_2"]:
        if key in raw:
            result[key] = raw[key]
        elif key not in result:
            result[key] = existing.get(key, [])

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ data.json atualizado com sucesso!\n")

if __name__ == "__main__":
    main()
