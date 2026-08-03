import os
import json
import requests
from datetime import datetime

# ── Configurações ──────────────────────────────────────────────────────────────
ACCESS_TOKEN = os.environ["META_ACCESS_TOKEN"]
API_VERSION  = "v19.0"
BASE_URL     = f"https://graph.facebook.com/{API_VERSION}"

# IDs dos anúncios — hardcoded ou via secret (secret tem prioridade)
AD_MAP = {k: v for k, v in {
    "apcd_3": os.environ.get("META_AD_ID_APCD_3", ""),
    "aux_1":  os.environ.get("META_AD_ID_AUX_1",  ""),
    "aux_1b": os.environ.get("META_AD_ID_AUX_1B", ""),
    "aux_2":  os.environ.get("META_AD_ID_AUX_2",  "") or "120252735568490635",
    "aux_3":  os.environ.get("META_AD_ID_AUX_3",  "") or "120252735456570635",
    "aux_4":  os.environ.get("META_AD_ID_AUX_4",  "") or "120252735040200635",
    "aux_5":  os.environ.get("META_AD_ID_AUX_5",  "") or "120252671205230635",
}.items() if v}

# Período: data de início das campanhas até hoje (histórico completo)
CAMPAIGN_SINCE = "2026-05-10"
hoje = datetime.today()
fim  = hoje.strftime("%Y-%m-%d")


def buscar_insights_diarios(ad_id):
    """Busca métricas diárias com suporte a paginação."""
    url    = f"{BASE_URL}/{ad_id}/insights"
    params = {
        "access_token":   ACCESS_TOKEN,
        "level":          "ad",
        "time_increment": 1,
        "time_range":     json.dumps({"since": CAMPAIGN_SINCE, "until": fim}),
        "fields":         "date_start,impressions,inline_link_clicks,spend,actions,cost_per_action_type",
        "limit":          90,
    }
    all_data = []
    while True:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        all_data.extend(body.get("data", []))
        next_url = body.get("paging", {}).get("next")
        if not next_url:
            break
        url    = next_url
        params = {}
    return all_data


def extrair_conversas(actions, cost_per_action):
    tipos = [
        "onsite_conversion.messaging_conversation_started_7d",
        "onsite_conversion.messaging_first_reply",
        "lead",
    ]
    convs = 0
    custo = 0.0
    for a in (actions or []):
        if a.get("action_type") in tipos:
            convs = int(a.get("value", 0))
            break
    for c in (cost_per_action or []):
        if c.get("action_type") in tipos:
            custo = float(c.get("value", 0))
            break
    return convs, custo


def formatar_data(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m")


# ── Ler data.json existente (preservar histórico não sobrescrito) ──────────────
data_file = "data.json"
try:
    with open(data_file, "r", encoding="utf-8") as f:
        existing = json.load(f)
except Exception:
    existing = {}


# ── Coleta via API ─────────────────────────────────────────────────────────────
resultado = {}

for chave, ad_id in AD_MAP.items():
    print(f"Buscando dados para {chave} (ID: {ad_id})...")
    try:
        registros = buscar_insights_diarios(ad_id)
        if not registros:
            print(f"  → 0 dias coletados. Mantendo histórico existente.")
            resultado[chave] = existing.get(chave, [])
            continue
        dias = []
        for r in registros:
            convs, custo_conv = extrair_conversas(
                r.get("actions"),
                r.get("cost_per_action_type")
            )
            dias.append({
                "date":        formatar_data(r["date_start"]),
                "views":       int(r.get("impressions", 0)),
                "clicks":      int(r.get("inline_link_clicks", 0)),
                "convs":       convs,
                "costPerConv": round(custo_conv, 2),
                "spent":       round(float(r.get("spend", 0)), 2),
            })
        resultado[chave] = dias
        print(f"  → {len(dias)} dias coletados.")
    except Exception as e:
        print(f"  [ERRO] {chave}: {e}")
        resultado[chave] = existing.get(chave, [])


# ── Fundir aux_1 + aux_1b (mesma campanha, novo criativo a partir de 04/06) ───
if "aux_1b" in resultado:
    base  = resultado.get("aux_1", existing.get("aux_1", []))
    extra = resultado.pop("aux_1b")
    by_date = {d["date"]: d for d in base}
    for d in extra:
        by_date[d["date"]] = d
    resultado["aux_1"] = sorted(by_date.values(), key=lambda x: datetime.strptime(x["date"] + "/2026", "%d/%m/%Y"))


# ── Preservar chaves existentes não actualizadas ──────────────────────────────
for key, val in existing.items():
    if key not in ("ultima_atualizacao", "periodo") and key not in resultado:
        resultado[key] = val


# ── Gravar data.json ──────────────────────────────────────────────────────────
data_json = {
    "ultima_atualizacao": hoje.strftime("%d/%m/%Y"),
    "periodo": f"{formatar_data(CAMPAIGN_SINCE)} a {hoje.strftime('%d/%m')}",
}
data_json.update(resultado)

with open(data_file, "w", encoding="utf-8") as f:
    json.dump(data_json, f, ensure_ascii=False, indent=2)

print(f"\n✅ data.json gerado com sucesso! ({hoje.strftime('%d/%m/%Y')})")
