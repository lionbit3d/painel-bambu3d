import pandas as pd
import requests

from config import (
    HEADERS,
    PEDIDOS_COLUMNS,
    PEDIDOS_RENAME_COLUMNS,
    SUPABASE_URL,
    VAREJO_COLUMNS,
    VAREJO_RENAME_COLUMNS,
)


def empty_pedidos():
    return pd.DataFrame(columns=PEDIDOS_COLUMNS)


def empty_varejo():
    return pd.DataFrame(columns=VAREJO_COLUMNS)


def load_pedidos():
    try:
        url_get_pedidos = f"{SUPABASE_URL}/rest/v1/encomendas?select=*"
        resposta_pedidos = requests.get(url_get_pedidos, headers=HEADERS)
        dados_p = resposta_pedidos.json() if resposta_pedidos.status_code == 200 else []
        df_pedidos = pd.DataFrame(dados_p) if dados_p else empty_pedidos()
        if not df_pedidos.empty:
            df_pedidos = df_pedidos.rename(columns=PEDIDOS_RENAME_COLUMNS)
        return df_pedidos
    except Exception:
        return empty_pedidos()


def load_varejo():
    try:
        url_get_varejo = f"{SUPABASE_URL}/rest/v1/varejo?select=*"
        resposta_varejo = requests.get(url_get_varejo, headers=HEADERS)
        dados_v = resposta_varejo.json() if resposta_varejo.status_code == 200 else []
        df_varejo = pd.DataFrame(dados_v) if dados_v else empty_varejo()
        if not df_varejo.empty:
            df_varejo = df_varejo.rename(columns=VAREJO_RENAME_COLUMNS)
        return df_varejo
    except Exception:
        return empty_varejo()


def create_encomenda(payload):
    return requests.post(f"{SUPABASE_URL}/rest/v1/encomendas", headers=HEADERS, json=payload)


def update_encomenda_status(record_id, status):
    return requests.patch(
        f"{SUPABASE_URL}/rest/v1/encomendas?id=eq.{record_id}",
        headers=HEADERS,
        json={"status": status},
    )


def create_varejo(payload):
    return requests.post(f"{SUPABASE_URL}/rest/v1/varejo", headers=HEADERS, json=payload)
