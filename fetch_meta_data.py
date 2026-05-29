import os
import json
import requests
from datetime import datetime, timedelta

# ── Configurações ──────────────────────────────────────────────
ACCESS_TOKEN  = os.environ["META_ACCESS_TOKEN"]
AD_ACCOUNT_ID = "act_1600485061005605"
API_VERSION   = "v19.0"
BASE_URL      = f"https://graph.facebook.com/{API_VERSION}"

# Mapeamento: chave do data.json → secret com o Ad ID
AD_MAP = {
    "apcd_1": os.environ.get("META_AD_ID_APCD_1", ""),
    "apcd_2": os.environ.get("META_AD_ID_APCD_2", ""),
    "apcd_3": os.environ.get("META_AD_ID_APCD_3", ""),
    "aux_1":  os.environ.get("META_AD_ID_AUX_1", ""),
    "aux_2":  os.environ.get("META_AD_ID_AUX_2", ""),
    "aux_3":  os.environ.get("META_AD_ID_AUX_3", ""),
    "aux_4":  os.environ.get("META_AD_ID_AUX_4", ""),
    "aux_5":  os.environ.get("META_AD_ID_AUX_5", ""),
}

# Período: do dia 1º do mês atual até hoje
hoje      = datetime.today()
inicio    = hoje.replace(day=1).strftime("%Y-%m-%d")
fim       = hoje.strftime("%Y-%m-%d")

def buscar_insights_diarios(ad_id):
    """Busca métricas diárias de um anúncio específico."""
    url = f"{BASE_URL}/{ad_id}/insights"
    params = {
        "access_token": ACCESS_TOKEN,
        "level":        "ad",
        "time_increment": 1,          # 1 = por dia
        "time_range":   json.dumps({"since": inicio, "until": fim}),
        "fields":       "impressions,inline_link_clicks,spend,actions,cost_per_action_type",
        "limit":        90,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("data", [])

def extrair_conversas(actions, cost_per_action):
    """Extrai conversas iniciadas por mensagem dos campos actions."""
    tipos_conversa = [
        "onsite_conversion.messaging_conversation_started_7d",
        "onsite_conversion.messaging_first_reply",
        "lead",
    ]
    convs = 0
    custo = 0.0

    for a in (actions or []):
        if a.get("action_type") in tipos_conversa:
            convs = int(a.get("value", 0))
            break

    for c in (cost_per_action or []):
        if c.get("action_type") in tipos_conversa:
            custo = float(c.get("value", 0))
            break

    return convs, custo

def formatar_data(date_str):
    """Converte '2026-05-10' → '10/05'."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return d.strftime("%d/%m")

# ── Coleta dos dados ───────────────────────────────────────────
resultado = {}

for chave, ad_id in AD_MAP.items():
    if not ad_id:
        print(f"[AVISO] Secret não encontrado para {chave}, pulando.")
        resultado[chave] = []
        continue

    print(f"Buscando dados para {chave} (ID: {ad_id})...")
    try:
        registros = buscar_insights_diarios(ad_id)
        dias = []
        for r in registros:
            convs, custo_conv = extrair_conversas(
                r.get("actions"),
                r.get("cost_per_action_type")
            )
            spent = float(r.get("spend", 0))
            dias.append({
                "date":        formatar_data(r["date_start"]),
                "views":       int(r.get("impressions", 0)),
                "clicks":      int(r.get("inline_link_clicks", 0)),
                "convs":       convs,
                "costPerConv": round(custo_conv, 2),
                "spent":       round(spent, 2),
            })
        resultado[chave] = dias
        print(f"  → {len(dias)} dias coletados.")
    except Exception as e:
        print(f"  [ERRO] {chave}: {e}")
        resultado[chave] = []

# ── Monta o data.json final ────────────────────────────────────
data_json = {
    "ultima_atualizacao": hoje.strftime("%d/%m/%Y"),
    "periodo": f"01/{hoje.strftime('%m')} a {hoje.strftime('%d/%m')}",
}
data_json.update(resultado)

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data_json, f, ensure_ascii=False, indent=2)

print(f"\n✅ data.json gerado com sucesso! ({hoje.strftime('%d/%m/%Y')})")
