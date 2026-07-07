import streamlit as st
import pandas as pd
import json
import ipaddress
import socket
import ssl
import time
import warnings
from datetime import datetime, timedelta, timezone
import requests

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None


st.set_page_config(page_title="LionBit 3D Studio - Painel de Controle", layout="wide")

SUPABASE_URL = "https://ntybsaywkdmqcjhslehw.supabase.co/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50eWJzYXl3a2RtcWNqaHNsZWh3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMzNTQwMjgsImV4cCI6MjA5ODkzMDAyOH0.0pV_Lu60COGdjBCuVVSmqf2TNqH3I_0xlLSeJckenzA"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

PEDIDOS_COLUMNS = [
    "id",
    "Cliente",
    "Consultor",
    "Data",
    "Tipo de Projeto",
    "Peso (g)",
    "Custo (R$)",
    "Preço Venda (R$)",
    "Margem",
    "Status",
]

VAREJO_COLUMNS = [
    "id",
    "Produto",
    "Local de Venda",
    "Quantidade Enviada",
    "Quantidade Vendida",
    "Peso Unit. (g)",
    "Custo Unit. (R$)",
    "Preço Unit. Venda (R$)",
]

IMPRESSOES_COLUMNS = [
    "id",
    "created_at",
    "encomenda_id",
    "printer_name",
    "arquivo",
    "status",
    "progresso",
    "tempo_restante_min",
    "gcode_state",
    "observacao",
    "finalizada_em",
]

LISTA_PROJETOS = [
    "Suporte de Celular",
    "Letreiro de Quarto",
    "Boneco Articulado",
    "Boneco Decorativo",
    "Chaveiro",
    "Utilitário",
    "Utensílio Doméstico",
    "Peça Técnica",
]

OPCOES_MARGEM = {"250%": 2.5, "300%": 3.0, "350%": 3.5, "400%": 4.0}
STATUS_OPTIONS = ["Pendente", "Imprimindo", "Concluído"]
CONSULTORES = ["Isaac", "Renato"]
BRASILIA_TZ = timezone(timedelta(hours=-3))


def is_private_host(host):
    try:
        return ipaddress.ip_address(host).is_private
    except ValueError:
        return False


def bambu_network_message(host, port, detail):
    if is_private_host(host):
        return (
            f"Nao consegui acessar {host}:{port}. Esse IP e privado da sua rede local; "
            "o Streamlit Cloud nao consegue chegar nele pela internet. "
            "Para controlar pelo site publicado, precisa rodar o app na mesma rede da impressora "
            "ou configurar uma VPN/tunel/gateway seguro. Detalhe: "
            f"{detail}"
        )
    return f"Nao consegui acessar {host}:{port}. Detalhe: {detail}"

design_premium = """
<style>
    .stApp { background-color: #121212; color: #ffffff !important; }
    h1, h2, h3, p, span, label, th, td { color: #ffffff !important; }
    div[data-testid="stMetric"] { background-color: #1e1e1e; border: 2px solid #ffcc00; border-radius: 10px; padding: 15px; }
    div[data-testid="stMetricLabel"] { color: #ffcc00 !important; font-weight: bold; font-size: 16px; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: bold; }
    button[data-baseweb="tab"] { color: #aaaaaa !important; font-size: 16px; }
    button[aria-selected="true"] { color: #ffcc00 !important; border-bottom-color: #ffcc00 !important; font-weight: bold; }
    .stTextInput input, .stSelectbox select, .stNumberInput input { background-color: #262626 !important; color: #ffffff !important; border: 1px solid #ffcc00 !important; }
    div[data-baseweb="select"] { background-color: #262626 !important; border-radius: 4px !important; }
    div[role="button"] { background-color: #1e1e1e !important; color: #ffffff !important; border: 1px solid #ffcc00 !important; }
    ul[role="listbox"] { background-color: #1e1e1e !important; }
    li[role="option"] { color: #ffffff !important; background-color: #1e1e1e !important; }
    li[role="option"]:hover { background-color: #ffcc00 !important; color: #000000 !important; }
    .stFormSubmitButton > button { background-color: #ffcc00 !important; color: #000000 !important; font-weight: bold !important; border: 2px solid #ffcc00 !important; border-radius: 5px !important; width: 100% !important; padding: 10px 0px !important; }
    .stFormSubmitButton > button:hover { background-color: #e6b800 !important; color: #000000 !important; border-color: #e6b800 !important; }
    .stButton > button { background-color: #ffcc00 !important; color: #000000 !important; font-weight: bold !important; border: 2px solid #ffcc00 !important; border-radius: 5px !important; width: 100% !important; }
    .stButton > button:hover { background-color: #e6b800 !important; color: #000000 !important; border-color: #e6b800 !important; }
    .stButton > button p, .stButton > button span { color: #000000 !important; }
    div[data-testid="stTableEditor"], div.glide-data-grid, .gdg-elements {
        background-color: #1a1a1a !important;
    }
    div[data-testid="stTableEditor"] button, div[data-testid="stDataFrame"] button {
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1px solid #d0d0d0 !important;
    }
    div[data-testid="stTableEditor"] button svg, div[data-testid="stDataFrame"] button svg {
        color: #111111 !important;
        fill: #111111 !important;
        stroke: #111111 !important;
    }
    div[class*="popover"], div[class*="dropdown"], div[class*="menu"] {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
    }
    span[class*="text"], input[class*="edit"] {
        color: #ffffff !important;
    }

    div[data-testid="stSegmentedControl"] {
        background-color: transparent !important;
    }
    div[data-testid="stSegmentedControl"] label,
    div[data-testid="stSegmentedControl"] label > div,
    div[data-testid="stSegmentedControl"] button,
    div[data-testid="stSegmentedControl"] div[role="button"] {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #ffcc00 !important;
        font-weight: bold !important;
    }
    div[data-testid="stSegmentedControl"] label *,
    div[data-testid="stSegmentedControl"] button *,
    div[data-testid="stSegmentedControl"] div[role="button"] * {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    div[data-testid="stSegmentedControl"] label:hover,
    div[data-testid="stSegmentedControl"] button:hover,
    div[data-testid="stSegmentedControl"] div[role="button"]:hover {
        background-color: #2b2b2b !important;
        color: #ffffff !important;
        border-color: #ffcc00 !important;
    }
    div[data-testid="stSegmentedControl"] label:has(input:checked),
    div[data-testid="stSegmentedControl"] label:has(input:checked) > div,
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
    div[data-testid="stSegmentedControl"] div[aria-checked="true"],
    div[data-testid="stSegmentedControl"] div[aria-selected="true"] {
        background-color: #ffcc00 !important;
        color: #000000 !important;
        border-color: #ffcc00 !important;
    }
    div[data-testid="stSegmentedControl"] label:has(input:checked) *,
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] *,
    div[data-testid="stSegmentedControl"] div[aria-checked="true"] *,
    div[data-testid="stSegmentedControl"] div[aria-selected="true"] * {
        color: #000000 !important;
        fill: #000000 !important;
    }
</style>
"""
st.markdown(design_premium, unsafe_allow_html=True)


def format_brl(value):
    try:
        formatted = f"R$ {float(value):,.2f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"


def format_currency_columns(df, columns):
    df_formatado = df.copy()
    for column in columns:
        if column in df_formatado.columns:
            df_formatado[column] = df_formatado[column].apply(format_brl)
    return df_formatado


def today_brasilia():
    return datetime.now(BRASILIA_TZ).date()


def parse_float(value):
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        value = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def margin_multiplier_from_text(value):
    if pd.isna(value):
        return 3.0
    if isinstance(value, str):
        cleaned = value.replace("%", "").strip()
        if not cleaned:
            return 3.0
        return parse_float(cleaned) / 100
    return parse_float(value) / 100


def format_margin_from_values(custo, preco):
    custo = parse_float(custo)
    preco = parse_float(preco)
    if custo <= 0 or preco <= 0:
        return "0%"
    return f"{round((preco / custo) * 100):.0f}%"


def calculate_order_values(peso_gramas, margem_texto):
    custo_calc = parse_float(peso_gramas) * 0.15
    preco_calc = custo_calc * margin_multiplier_from_text(margem_texto)
    return round(custo_calc, 2), round(preco_calc, 2)


def empty_pedidos():
    return pd.DataFrame(columns=PEDIDOS_COLUMNS)


def empty_varejo():
    return pd.DataFrame(columns=VAREJO_COLUMNS)


def load_pedidos():
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/encomendas?select=*", headers=HEADERS)
        data = response.json() if response.status_code == 200 else []
        df = pd.DataFrame(data) if data else empty_pedidos()
        if not df.empty:
            df = df.rename(
                columns={
                    "cliente": "Cliente",
                    "data_solicitacao": "Data",
                    "consultor": "Consultor",
                    "tipo_projeto": "Tipo de Projeto",
                    "peso_g": "Peso (g)",
                    "custo_rs": "Custo (R$)",
                    "preco_venda_rs": "Preço Venda (R$)",
                    "margem": "Margem",
                    "status": "Status",
                }
            )
            for column in PEDIDOS_COLUMNS:
                if column not in df.columns:
                    df[column] = ""
            df["Consultor"] = df["Consultor"].fillna("").replace("", "Isaac")
            df["Margem"] = df["Margem"].fillna("").replace("", "300%")
            df["Status"] = df["Status"].fillna("").replace("", "Pendente")
            df["Tipo de Projeto"] = df["Tipo de Projeto"].fillna("").replace("", LISTA_PROJETOS[0])
        return df
    except Exception:
        return empty_pedidos()


def load_varejo():
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/varejo?select=*", headers=HEADERS)
        data = response.json() if response.status_code == 200 else []
        df = pd.DataFrame(data) if data else empty_varejo()
        if not df.empty:
            df = df.rename(
                columns={
                    "produto": "Produto",
                    "local_venda": "Local de Venda",
                    "qtd_enviada": "Quantidade Enviada",
                    "qtd_vendida": "Quantidade Vendida",
                    "peso_unit_g": "Peso Unit. (g)",
                    "custo_unit_rs": "Custo Unit. (R$)",
                    "preco_unit_venda_rs": "Preço Unit. Venda (R$)",
                }
            )
        return df
    except Exception:
        return empty_varejo()


def render_header():
    col_logo, col_titulo = st.columns(2)
    with col_logo:
        try:
            st.image("logo.png", width=120)
        except Exception:
            st.write("🦁 [Logo]")
    with col_titulo:
        st.markdown(
            "<h1 style='color: #ffcc00; margin-bottom: 0; font-family: sans-serif; font-size: 42px;'>LionBit 3D Studio</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h3 style='color: #ffffff; margin-top: 0; font-family: sans-serif; font-weight: 300;'>Painel Integrado de Manufatura e Gestão de Vendas</h3>",
            unsafe_allow_html=True,
        )


def prepare_varejo_metrics(df_varejo):
    if df_varejo.empty:
        return df_varejo

    df_varejo = df_varejo.copy()
    df_varejo["Total Custo Enviado"] = df_varejo["Quantidade Enviada"] * df_varejo["Custo Unit. (R$)"]
    df_varejo["Total Faturamento Real"] = df_varejo["Quantidade Vendida"] * df_varejo["Preço Unit. Venda (R$)"]
    df_varejo["Lucro Gerado (R$)"] = df_varejo["Total Faturamento Real"] - (
        df_varejo["Quantidade Vendida"] * df_varejo["Custo Unit. (R$)"]
    )
    return df_varejo


def render_global_metrics(df_pedidos, df_varejo):
    custo_pedidos = df_pedidos["Custo (R$)"].sum() if not df_pedidos.empty else 0.0
    faturamento_pedidos = df_pedidos["Preço Venda (R$)"].sum() if not df_pedidos.empty else 0.0

    if not df_varejo.empty:
        custo_varejo = df_varejo["Total Custo Enviado"].sum()
        faturamento_varejo = df_varejo["Total Faturamento Real"].sum()
    else:
        custo_varejo, faturamento_varejo = 0.0, 0.0

    custo_global = custo_pedidos + custo_varejo
    faturamento_global = faturamento_pedidos + faturamento_varejo
    lucro_global = faturamento_global - custo_global

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total de Pedidos Ativos", len(df_pedidos) + len(df_varejo))
    col2.metric("📉 Custo Total de Material", format_brl(custo_global))
    col3.metric("💰 Faturamento Bruto", format_brl(faturamento_global))
    col4.metric("🔥 Lucro Líquido Geral", format_brl(lucro_global))


def sync_encomenda_changes(df_original, df_editado):
    if "id" not in df_original.columns or "id" not in df_editado.columns:
        return

    alterou_registro = False
    for _, linha_editada in df_editado.iterrows():
        registro = df_original[df_original["id"] == linha_editada["id"]]
        if registro.empty:
            continue

        linha_original = registro.iloc[0]
        peso_editado = parse_float(linha_editada["Peso (g)"])
        peso_original = parse_float(linha_original["Peso (g)"])
        custo_original = parse_float(linha_original["Custo (R$)"])
        preco_original = parse_float(linha_original["Preço Venda (R$)"])
        custo_editado = parse_float(linha_editada["Custo (R$)"])
        preco_editado = parse_float(linha_editada["Preço Venda (R$)"])

        peso_mudou = peso_editado != peso_original
        custo_mudou = round(custo_editado, 2) != round(custo_original, 2)
        preco_mudou = round(preco_editado, 2) != round(preco_original, 2)
        margem_mudou = str(linha_editada["Margem"]) != str(linha_original["Margem"])

        if custo_mudou:
            custo_final = custo_editado
        elif peso_mudou:
            custo_final = peso_editado * 0.15
        else:
            custo_final = custo_original

        if preco_mudou:
            preco_final = preco_editado
            margem_final = format_margin_from_values(custo_final, preco_final)
        else:
            margem_final = linha_editada["Margem"]
            preco_final = custo_final * margin_multiplier_from_text(margem_final)

        payload = {
            "cliente": linha_editada["Cliente"],
            "consultor": linha_editada["Consultor"],
            "tipo_projeto": linha_editada["Tipo de Projeto"],
            "peso_g": peso_editado,
            "custo_rs": round(custo_final, 2),
            "preco_venda_rs": round(preco_final, 2),
            "margem": margem_final,
            "status": linha_editada["Status"],
        }
        mudou = any(
            [
                str(linha_editada["Cliente"]) != str(linha_original["Cliente"]),
                str(linha_editada["Consultor"]) != str(linha_original["Consultor"]),
                str(linha_editada["Tipo de Projeto"]) != str(linha_original["Tipo de Projeto"]),
                peso_mudou,
                custo_mudou,
                preco_mudou,
                margem_mudou,
                str(linha_editada["Status"]) != str(linha_original["Status"]),
            ]
        )

        if mudou:
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/encomendas?id=eq.{linha_editada['id']}",
                headers=HEADERS,
                json=payload,
            )
            alterou_registro = True

    if alterou_registro:
        st.success("Encomenda atualizada no banco de dados!")
        st.rerun()
    else:
        st.info("Nenhuma alteração para salvar.")


def delete_encomenda(encomenda_id):
    response = requests.delete(f"{SUPABASE_URL}/rest/v1/encomendas?id=eq.{encomenda_id}", headers=HEADERS)
    return response.status_code in [200, 204]


def update_encomenda_status(encomenda_id, status):
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/encomendas?id=eq.{encomenda_id}",
        headers=HEADERS,
        json={"status": status},
    )
    return response.status_code in [200, 204]


def empty_impressoes():
    return pd.DataFrame(columns=IMPRESSOES_COLUMNS)


def load_bambu_print_jobs():
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/impressoes_bambu?select=*&order=created_at.desc",
            headers=HEADERS,
        )
        data = response.json() if response.status_code == 200 else []
        return pd.DataFrame(data) if data else empty_impressoes()
    except Exception:
        return empty_impressoes()


def current_print_file(print_data):
    arquivo = str(print_data.get("arquivo") or "").strip()
    if arquivo:
        return arquivo
    raw = print_data.get("raw", {})
    if isinstance(raw, dict):
        print_payload = raw.get("print", {})
        for field in ["gcode_file", "subtask_name", "project_id", "task_id"]:
            value = str(print_payload.get(field) or "").strip()
            if value:
                return value
    return ""


def save_bambu_print_job(encomenda_id, printer_name, print_data):
    raw = print_data.get("raw", {})
    print_payload = raw.get("print", {}) if isinstance(raw, dict) else {}
    payload = {
        "encomenda_id": int(encomenda_id),
        "printer_name": printer_name,
        "arquivo": current_print_file(print_data) or "Arquivo sem nome",
        "status": print_data.get("estado", "Imprimindo"),
        "progresso": parse_float(print_data.get("progresso", 0)),
        "tempo_restante_min": int(parse_float(print_payload.get("mc_remaining_time", 0))),
        "gcode_state": str(print_payload.get("gcode_state", "")),
    }
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/impressoes_bambu",
        headers=HEADERS,
        json=payload,
    )
    return response.status_code in [200, 201], payload["arquivo"]


def finish_bambu_print_job(job_id):
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/impressoes_bambu?id=eq.{job_id}",
        headers=HEADERS,
        json={
            "status": "Finalizada",
            "finalizada_em": datetime.now(BRASILIA_TZ).isoformat(),
        },
    )
    return response.status_code in [200, 204]


def pedido_label(row):
    return f"{row['Cliente']} | {row['Tipo de Projeto']} | {row['Data']} | {row['Status']} | ID {row['id']}"


def get_order_summary(df_pedidos):
    if df_pedidos.empty or "id" not in df_pedidos.columns:
        return {}
    return {
        int(row["id"]): {
            "Cliente": row.get("Cliente", ""),
            "Tipo de Projeto": row.get("Tipo de Projeto", ""),
            "Status do Pedido": row.get("Status", ""),
        }
        for _, row in df_pedidos.iterrows()
    }


def render_bambu_order_linking(printer, print_data, df_pedidos):
    st.markdown("### Vinculo com encomendas")
    jobs = load_bambu_print_jobs()
    open_orders = (
        df_pedidos[df_pedidos["Status"].isin(["Pendente", "Imprimindo"])]
        if not df_pedidos.empty
        else df_pedidos
    )
    arquivo_atual = current_print_file(print_data)

    if not arquivo_atual:
        st.info("Nenhum arquivo de impressao ativo para vincular agora.")
    elif open_orders.empty:
        st.info("Nenhuma encomenda pendente ou em impressao para vincular.")
    else:
        opcoes_pedidos = {pedido_label(row): row for _, row in open_orders.iterrows()}
        pedido_escolhido = st.selectbox("Vincular arquivo atual a encomenda", list(opcoes_pedidos.keys()))
        if st.button("Vincular impressao atual", use_container_width=True):
            pedido = opcoes_pedidos[pedido_escolhido]
            duplicado = False
            if not jobs.empty:
                duplicado = not jobs[
                    (jobs["encomenda_id"].astype(int) == int(pedido["id"]))
                    & (jobs["arquivo"].astype(str) == arquivo_atual)
                    & (jobs["status"].astype(str) != "Finalizada")
                ].empty
            if duplicado:
                st.warning("Essa impressao ja esta vinculada a essa encomenda.")
            else:
                ok, arquivo = save_bambu_print_job(pedido["id"], printer["name"], print_data)
                if ok:
                    if str(pedido["Status"]) == "Pendente":
                        update_encomenda_status(pedido["id"], "Imprimindo")
                    st.success(f"Impressao vinculada: {arquivo}")
                    st.rerun()
                else:
                    st.error("Nao consegui salvar o vinculo da impressao.")

    if jobs.empty:
        return

    order_summary = get_order_summary(df_pedidos)
    jobs_view = jobs.copy()
    jobs_view["Cliente"] = jobs_view["encomenda_id"].apply(lambda value: order_summary.get(int(value), {}).get("Cliente", ""))
    jobs_view["Tipo de Projeto"] = jobs_view["encomenda_id"].apply(
        lambda value: order_summary.get(int(value), {}).get("Tipo de Projeto", "")
    )
    jobs_view["Status do Pedido"] = jobs_view["encomenda_id"].apply(
        lambda value: order_summary.get(int(value), {}).get("Status do Pedido", "")
    )
    jobs_view["Tempo restante"] = jobs_view["tempo_restante_min"].apply(format_remaining_time)

    st.write("#### Impressoes vinculadas")
    st.dataframe(
        jobs_view[["Cliente", "Tipo de Projeto", "arquivo", "status", "progresso", "Tempo restante", "Status do Pedido"]],
        hide_index=True,
        use_container_width=True,
    )

    opcoes_jobs = {
        f"{row['arquivo']} | {row['Cliente']} | {row['status']} | ID {row['id']}": row
        for _, row in jobs_view.iterrows()
    }
    job_escolhido = st.selectbox("Gerenciar impressao vinculada", list(opcoes_jobs.keys()))
    job = opcoes_jobs[job_escolhido]

    col_finalizar, col_concluir = st.columns(2)
    with col_finalizar:
        if st.button("Marcar impressao como finalizada", use_container_width=True):
            if finish_bambu_print_job(job["id"]):
                st.success("Impressao finalizada.")
                st.rerun()
            else:
                st.error("Nao consegui finalizar essa impressao.")
    with col_concluir:
        if st.button("Marcar pedido como concluido", use_container_width=True):
            if update_encomenda_status(job["encomenda_id"], "Concluído"):
                st.success("Pedido marcado como concluido.")
                st.rerun()
            else:
                st.error("Nao consegui concluir esse pedido.")


def get_secret_section(section_name):
    try:
        return dict(st.secrets.get(section_name, {}))
    except Exception:
        return {}


def get_bambu_printers():
    printers = []
    for section_name, fallback_name in [("bambu_isaac", "Isaac"), ("bambu_renato", "Renato")]:
        config = get_secret_section(section_name)
        printers.append(
            {
                "name": config.get("name", fallback_name),
                "host": config.get("host", ""),
                "access_code": config.get("access_code", ""),
                "serial": config.get("serial", ""),
                "port": int(config.get("port", 8883) or 8883),
            }
        )
    return printers




def get_bambu_gateway_config():
    config = get_secret_section("bambu_gateway")
    url = str(config.get("url", "")).rstrip("/")
    token = str(config.get("token", ""))
    return {
        "url": url,
        "token": token,
        "enabled": bool(url and token),
    }


def gateway_request(path, method="GET", timeout=35):
    gateway = get_bambu_gateway_config()
    if not gateway["enabled"]:
        return None

    try:
        response = requests.request(
            method,
            f"{gateway['url']}{path}",
            headers={"X-Lionbit-Token": gateway["token"]},
            timeout=timeout,
        )
        payload = response.json()
    except requests.RequestException as exc:
        return {"ok": False, "message": f"Gateway indisponivel: {exc}", "data": {}}
    except ValueError:
        return {"ok": False, "message": "Gateway retornou resposta invalida", "data": {}}

    if response.status_code >= 400 and payload.get("ok") is not False:
        payload = {"ok": False, "message": f"Gateway retornou HTTP {response.status_code}", "data": payload}
    payload.setdefault("data", {})
    return payload


def read_bambu_status_via_gateway():
    return gateway_request("/status", timeout=45)


def send_bambu_light_command_via_gateway(mode):
    result = gateway_request(f"/light/{mode}", method="POST", timeout=30)
    if not result:
        return False, "Gateway nao configurado"
    return bool(result.get("ok")), result.get("message", "Sem resposta do gateway")

def test_tcp_connection(host, port, timeout=2):
    if not host:
        return False, "IP pendente"
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True, "Porta acessivel"
    except (TimeoutError, socket.timeout) as exc:
        return False, bambu_network_message(host, port, str(exc) or "timed out")
    except OSError as exc:
        return False, bambu_network_message(host, port, str(exc))


def mqtt_client_factory():
    if mqtt is None:
        return None

    client_id = f"lionbit-streamlit-{int(time.time())}"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id, protocol=mqtt.MQTTv311)
        except Exception:
            client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)
    return client


def read_bambu_status(printer, timeout=6):
    required_fields = ["host", "access_code", "serial"]
    missing = [field for field in required_fields if not printer.get(field)]
    if missing:
        return {"ok": False, "message": f"Config pendente: {', '.join(missing)}", "data": {}}
    if mqtt is None:
        return {"ok": False, "message": "Dependencia paho-mqtt ausente", "data": {}}

    tcp_ok, tcp_message = test_tcp_connection(printer["host"], printer["port"])
    if not tcp_ok:
        return {"ok": False, "message": tcp_message, "data": {}}

    messages = []
    connection = {"rc": None}
    topic = f"device/{printer['serial']}/report"
    client = mqtt_client_factory()
    client.username_pw_set("bblp", printer["access_code"])

    def on_connect(client, userdata, flags, rc):
        connection["rc"] = rc
        if rc == 0:
            client.subscribe(topic, qos=0)

    def on_message(client, userdata, message):
        try:
            messages.append(json.loads(message.payload.decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError):
            messages.append({"raw": message.payload.decode("utf-8", errors="replace")})

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(printer["host"], printer["port"], keepalive=30)
        client.loop_start()
        started = time.time()
        while time.time() - started < min(2, timeout) and connection["rc"] is None:
            time.sleep(0.1)

        request_payload = {
            "pushing": {
                "sequence_id": str(int(time.time())),
                "command": "pushall",
            }
        }
        client.publish(f"device/{printer['serial']}/request", json.dumps(request_payload), qos=0)

        started = time.time()
        while time.time() - started < timeout and not messages:
            time.sleep(0.25)
        client.loop_stop()
        client.disconnect()
    except Exception as exc:
        return {"ok": False, "message": str(exc), "data": {}}

    if connection["rc"] not in [0, None]:
        return {"ok": False, "message": f"MQTT recusou conexao: {connection['rc']}", "data": {}}
    if not messages:
        return {"ok": False, "message": "Conectou, mas nao recebeu dados", "data": {}}
    return {"ok": True, "message": "Online", "data": messages[-1]}


def send_bambu_light_command(printer, mode):
    required_fields = ["host", "access_code", "serial"]
    missing = [field for field in required_fields if not printer.get(field)]
    if missing:
        return False, f"Config pendente: {', '.join(missing)}"
    if mqtt is None:
        return False, "Dependencia paho-mqtt ausente"

    tcp_ok, tcp_message = test_tcp_connection(printer["host"], printer["port"])
    if not tcp_ok:
        return False, tcp_message

    client = mqtt_client_factory()
    client.username_pw_set("bblp", printer["access_code"])
    payload = {
        "system": {
            "sequence_id": str(int(time.time())),
            "command": "ledctrl",
            "led_node": "chamber_light",
            "led_mode": mode,
            "led_on_time": 500,
            "led_off_time": 500,
            "loop_times": 1,
            "interval_time": 1000,
        }
    }
    try:
        client.connect(printer["host"], printer["port"], keepalive=30)
        client.loop_start()
        client.publish(f"device/{printer['serial']}/request", json.dumps(payload), qos=0)
        time.sleep(0.5)
        client.loop_stop()
        client.disconnect()
        return True, "Comando enviado"
    except Exception as exc:
        return False, str(exc)


def format_print_state(value):
    state = str(value or "-").strip().upper()
    state_labels = {
        "RUNNING": "Imprimindo",
        "FINISH": "Finalizado",
        "FAILED": "Falhou",
        "PAUSE": "Pausado",
        "PAUSED": "Pausado",
        "PREPARE": "Preparando",
        "IDLE": "Parada",
    }
    return state_labels.get(state, str(value or "-"))


def format_remaining_time(value):
    try:
        total_minutes = int(float(value))
    except (TypeError, ValueError):
        total_minutes = 0
    hours, minutes = divmod(max(total_minutes, 0), 60)
    return f"{hours}h{minutes:02d}min"


def pick_print_data(status_data):
    print_data = status_data.get("print", {}) if isinstance(status_data, dict) else {}
    return {
        "estado": format_print_state(print_data.get("gcode_state", "-")),
        "arquivo": print_data.get("gcode_file", "-"),
        "progresso": print_data.get("mc_percent", 0),
        "bico": print_data.get("nozzle_temper", "-"),
        "mesa": print_data.get("bed_temper", "-"),
        "camara": print_data.get("chamber_temper", "-"),
        "tempo_restante": format_remaining_time(print_data.get("mc_remaining_time", 0)),
        "raw": status_data,
    }


def render_bambu_lab(df_pedidos):
    st.markdown("<h2 style='color: #ffcc00;'>🖨️ Bambu Lab</h2>", unsafe_allow_html=True)
    printers = get_bambu_printers()
    selected_name = st.selectbox("Impressora", [printer["name"] for printer in printers])
    printer = next(printer for printer in printers if printer["name"] == selected_name)

    gateway_config = get_bambu_gateway_config()

    col_status, col_actions = st.columns([2, 1])
    with col_status:
        st.write(f"### {printer['name']}")
        st.write(f"IP: {printer['host'] or '-'}")
        st.write(f"Serial: {'configurado' if printer['serial'] else '-'}")
        st.write(f"Conexao: {'Cloudflare Tunnel' if gateway_config['enabled'] else 'Direta'}")

        if st.button("Atualizar impressora", use_container_width=True):
            with st.spinner("Consultando impressora..."):
                if gateway_config["enabled"]:
                    st.session_state["bambu_status"] = read_bambu_status_via_gateway()
                else:
                    st.session_state["bambu_status"] = read_bambu_status(printer)

        status = st.session_state.get("bambu_status")
        if status:
            if status["ok"]:
                data = pick_print_data(status["data"])
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Estado", data["estado"])
                m2.metric("Progresso", f"{data['progresso']}%")
                m3.metric("Bico", f"{data['bico']} °C")
                m4.metric("Mesa", f"{data['mesa']} °C")
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Arquivo": data["arquivo"],
                                "Tempo restante": data["tempo_restante"],
                                "Camara (°C)": data["camara"],
                            }
                        ]
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
                render_bambu_order_linking(printer, data, df_pedidos)
            else:
                st.warning(status["message"])

    with col_actions:
        st.write("### Controles")
        if st.button("Ligar luz", use_container_width=True):
            with st.spinner("Enviando comando..."):
                if gateway_config["enabled"]:
                    ok, message = send_bambu_light_command_via_gateway("on")
                else:
                    ok, message = send_bambu_light_command(printer, "on")
            if ok:
                st.success(message)
            else:
                st.error(message)
        if st.button("Desligar luz", use_container_width=True):
            with st.spinner("Enviando comando..."):
                if gateway_config["enabled"]:
                    ok, message = send_bambu_light_command_via_gateway("off")
                else:
                    ok, message = send_bambu_light_command(printer, "off")
            if ok:
                st.success(message)
            else:
                st.error(message)


def render_encomendas(df_pedidos):
    st.markdown("<h2 style='color: #ffcc00;'>📋 Gestão de Encomendas Ativas</h2>", unsafe_allow_html=True)
    col_form, col_tab = st.columns([1, 2])

    with col_form:
        st.write("### ➕ Nova Encomenda")
        with st.form("form_encomenda", clear_on_submit=True):
            cliente = st.text_input("Nome do Cliente")
            consultor = st.selectbox("Consultor", CONSULTORES)
            data_sel = st.date_input("Data de Solicitação", today_brasilia(), format="DD/MM/YYYY")
            tipo_projeto = st.selectbox("Tipo de Projeto", LISTA_PROJETOS)
            peso_gramas = st.number_input("Peso em Gramas (g)", min_value=0.0, step=1.0)
            margem_texto = st.selectbox("Margem de Venda", list(OPCOES_MARGEM.keys()), index=1)
            status_inicial = st.selectbox("Status", STATUS_OPTIONS)

            if st.form_submit_button("Salvar Encomenda"):
                if cliente and peso_gramas > 0:
                    custo_calc, preco_calc = calculate_order_values(peso_gramas, margem_texto)
                    data_br = data_sel.strftime("%d/%m/%Y")

                    payload = {
                        "cliente": cliente,
                        "consultor": consultor,
                        "data_solicitacao": data_br,
                        "tipo_projeto": tipo_projeto,
                        "peso_g": peso_gramas,
                        "custo_rs": custo_calc,
                        "preco_venda_rs": preco_calc,
                        "margem": margem_texto,
                        "status": status_inicial,
                    }
                    requests.post(f"{SUPABASE_URL}/rest/v1/encomendas", headers=HEADERS, json=payload)
                    st.success("Salvo no banco de dados!")
                    st.rerun()
                else:
                    st.warning("Preencha o cliente e um peso maior que zero.")

    with col_tab:
        st.write("### 🔍 Cronograma Prontuário")
        filtro_status = st.multiselect("Filtrar por Status:", STATUS_OPTIONS, default=["Pendente", "Imprimindo"])
        df_pedidos_filtrado = (
            df_pedidos[df_pedidos["Status"].isin(filtro_status)] if not df_pedidos.empty else df_pedidos
        )

        if not df_pedidos_filtrado.empty:
            df_pedidos_exibicao = df_pedidos_filtrado.copy()
            df_pedidos_exibicao["Custo (R$)"] = df_pedidos_exibicao["Custo (R$)"].apply(parse_float)
            df_pedidos_exibicao["Preço Venda (R$)"] = df_pedidos_exibicao["Preço Venda (R$)"].apply(parse_float)
            tabela_editavel = st.data_editor(
                df_pedidos_exibicao,
                column_config={
                    "id": None,
                    "created_at": None,
                    "Cliente": st.column_config.TextColumn("Cliente", required=True),
                    "Consultor": st.column_config.SelectboxColumn(
                        "Consultor",
                        options=CONSULTORES,
                        required=True,
                    ),
                    "Tipo de Projeto": st.column_config.SelectboxColumn(
                        "Tipo de Projeto",
                        options=LISTA_PROJETOS,
                        required=True,
                    ),
                    "Peso (g)": st.column_config.NumberColumn(
                        "Peso (g)",
                        min_value=0.0,
                        step=1.0,
                        required=True,
                    ),
                    "Custo (R$)": st.column_config.NumberColumn(
                        "Custo (R$)",
                        min_value=0.0,
                        step=0.01,
                        format="R$ %.2f",
                        required=True,
                    ),
                    "Preço Venda (R$)": st.column_config.NumberColumn(
                        "Preço Venda (R$)",
                        min_value=0.0,
                        step=0.01,
                        format="R$ %.2f",
                        required=True,
                    ),
                    "Margem": st.column_config.TextColumn(
                        "Margem",
                        required=True,
                    ),
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        options=STATUS_OPTIONS,
                        required=True,
                    ),
                },
                disabled=[
                    "Data",
                ],
                use_container_width=True,
            )
            col_salvar, col_excluir = st.columns(2)
            with col_salvar:
                if st.button("Salvar alterações do prontuário", use_container_width=True):
                    sync_encomenda_changes(df_pedidos_filtrado, tabela_editavel)
            with col_excluir:
                opcoes_exclusao = {
                    f"{row['Cliente']} | {row['Tipo de Projeto']} | {row['Data']} | ID {row['id']}": row["id"]
                    for _, row in df_pedidos_filtrado.iterrows()
                }
                encomenda_para_excluir = st.selectbox("Excluir encomenda", list(opcoes_exclusao.keys()))
                if st.button("Excluir encomenda selecionada", use_container_width=True):
                    if delete_encomenda(opcoes_exclusao[encomenda_para_excluir]):
                        st.success("Encomenda excluída do banco de dados!")
                        st.rerun()
                    else:
                        st.error("Não consegui excluir essa encomenda agora.")
        else:
            st.info("Nenhuma encomenda encontrada para os filtros selecionados.")


def render_varejo(df_varejo):
    st.subheader("🏪 Produtos Deixados em Comércio / Pronta Entrega")
    col_form2, col_tab2 = st.columns([1, 2])

    with col_form2:
        st.write("### ➕ Cadastrar Lote no Varejo")
        with st.form("form_varejo", clear_on_submit=True):
            produto = st.text_input("Nome do Produto (Ex: Vaso Espiral)")
            local = st.text_input("Local / Loja Parceira")
            qtd_enviada = st.number_input("Qtd Enviada (Estoque)", min_value=1, step=1)
            qtd_vendida = st.number_input(
                "Qtd Já Vendida",
                min_value=0,
                max_value=int(qtd_enviada if qtd_enviada > 0 else 1),
                step=1,
            )
            peso_unit = st.number_input("Peso Unitário (g)", min_value=0.0, step=1.0)
            preco_loja = st.number_input("Preço de Venda Final (R$)", min_value=0.0, step=1.0)

            if st.form_submit_button("Registrar no Varejo"):
                if produto and local and peso_unit > 0:
                    custo_u = peso_unit * 0.15
                    payload = {
                        "produto": produto,
                        "local_venda": local,
                        "qtd_enviada": qtd_enviada,
                        "qtd_vendida": qtd_vendida,
                        "peso_unit_g": peso_unit,
                        "custo_unit_rs": round(custo_u, 2),
                        "preco_unit_venda_rs": round(preco_loja, 2),
                    }
                    requests.post(f"{SUPABASE_URL}/rest/v1/varejo", headers=HEADERS, json=payload)
                    st.success("Salvo no banco de dados!")
                    st.rerun()

    with col_tab2:
        st.write("### 📊 Relatório de Itens Consignados / Pronta Entrega")
        if not df_varejo.empty:
            df_varejo_exibicao = df_varejo.copy()
            df_varejo_exibicao["Estoque Restante"] = (
                df_varejo_exibicao["Quantidade Enviada"] - df_varejo_exibicao["Quantidade Vendida"]
            )
            df_varejo_exibicao = format_currency_columns(
                df_varejo_exibicao,
                ["Custo Unit. (R$)", "Preço Unit. Venda (R$)"],
            )
            st.dataframe(
                df_varejo_exibicao[
                    [
                        "Produto",
                        "Local de Venda",
                        "Quantidade Enviada",
                        "Quantidade Vendida",
                        "Estoque Restante",
                        "Custo Unit. (R$)",
                        "Preço Unit. Venda (R$)",
                    ]
                ],
                use_container_width=True,
            )
        else:
            st.info("Nenhum produto em comércio cadastrado ainda.")


def render_desempenho_lojas(df_varejo):
    st.markdown("<h2 style='color: #ffcc00;'>📊 Desempenho de Lojas</h2>", unsafe_allow_html=True)

    if df_varejo.empty:
        st.info("Nenhum produto em comércio cadastrado ainda.")
        return

    desempenho = (
        df_varejo.groupby("Local de Venda", as_index=False)[
            ["Quantidade Vendida", "Total Faturamento Real", "Lucro Gerado (R$)"]
        ]
        .sum()
        .sort_values("Total Faturamento Real", ascending=False)
    )
    desempenho = format_currency_columns(desempenho, ["Total Faturamento Real", "Lucro Gerado (R$)"])
    st.dataframe(desempenho, use_container_width=True)


render_header()

df_pedidos = load_pedidos()
df_varejo = prepare_varejo_metrics(load_varejo())

render_global_metrics(df_pedidos, df_varejo)

st.markdown("---")

PANEL_OPTIONS = {
    "producao": "Fluxo de Encomendas",
    "varejo": "Estoque e Comercio Varejo",
    "desempenho": "Desempenho de Lojas",
    "bambu": "Bambu Lab",
}
st.session_state.setdefault("opcao_painel", "producao")

nav_cols = st.columns(4)
for nav_col, (panel_key, panel_label) in zip(nav_cols, PANEL_OPTIONS.items()):
    with nav_col:
        label = f"Selecionado - {panel_label}" if st.session_state["opcao_painel"] == panel_key else panel_label
        if st.button(label, key=f"nav_{panel_key}", use_container_width=True):
            st.session_state["opcao_painel"] = panel_key
            st.rerun()

opcao_painel = st.session_state["opcao_painel"]

if opcao_painel == "producao":
    render_encomendas(df_pedidos)
elif opcao_painel == "varejo":
    render_varejo(df_varejo)
elif opcao_painel == "desempenho":
    render_desempenho_lojas(df_varejo)
elif opcao_painel == "bambu":
    render_bambu_lab(df_pedidos)
