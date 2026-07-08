import streamlit as st
import pandas as pd
import json
import re
import ipaddress
import socket
import ssl
import time
import warnings
from html import escape
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
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
    "Encomenda",
    "Consultor",
    "Data",
    "Tipo de Projeto",
    "Peso (g)",
    "Custo (R$)",
    "Preço Venda (R$)",
    "Margem",
    "Prioridade",
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

FILAMENTOS_COLUMNS = [
    "id", "created_at", "material", "cor_nome", "cor_hex", "marca",
    "peso_inicial_g", "peso_atual_g", "status", "observacao",
]

CONSUMO_FILAMENTO_COLUMNS = [
    "id", "created_at", "impressao_id", "encomenda_id", "filamento_id",
    "peso_usado_g", "observacao",
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
PRIORIDADE_OPTIONS = ["Verde", "Amarelo", "Vermelho"]
CONSULTORES = ["Isaac", "Renato"]
BRASILIA_TZ = timezone(timedelta(hours=-3))
STATUS_BADGE_COLORS = {
    "Pendente": ("#ffcc00", "#111111"),
    "Imprimindo": ("#9ca3af", "#111111"),
    "Concluído": ("#22c55e", "#06130a"),
    "Concluido": ("#22c55e", "#06130a"),
}
PRIORIDADE_BADGE_COLORS = {
    "Verde": ("#22c55e", "#06130a"),
    "Amarelo": ("#ffcc00", "#111111"),
    "Vermelho": ("#ef4444", "#ffffff"),
}


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
    .stTextInput input::placeholder { color: #d9d9d9 !important; opacity: 1 !important; }
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
    .lion-status-board, .lion-color-table {
        border: 1px solid #3a3a3a;
        border-radius: 8px;
        overflow: hidden;
        margin: 0.5rem 0 1rem 0;
        background: #181818;
    }
    .lion-status-row, .lion-color-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 12px;
        align-items: center;
        padding: 10px 12px;
        border-bottom: 1px solid #2d2d2d;
    }
    .lion-color-row {
        grid-template-columns: 72px minmax(0, 1fr) 190px 90px 90px 90px;
    }
    .lion-status-row:last-child, .lion-color-row:last-child {
        border-bottom: 0;
    }
    .lion-color-head {
        background: #242424;
        color: #ffcc00 !important;
        font-weight: 700;
    }
    .lion-status-title, .lion-color-main {
        color: #ffffff !important;
        font-weight: 700;
    }
    .lion-status-sub, .lion-color-sub {
        color: #c9c9c9 !important;
        font-size: 0.88rem;
    }
    .lion-color-chip {
        display: block;
        width: 100%;
        min-height: 34px;
        padding: 7px 10px;
        border-radius: 6px;
        border: 1px solid rgba(255,255,255,0.5);
        font-weight: 800;
        box-shadow: inset 0 0 0 1px rgba(0,0,0,0.18);
    }
    .lion-badge {
        display: inline-block;
        min-width: 92px;
        text-align: center;
        padding: 5px 10px;
        border-radius: 999px;
        font-weight: 800;
        border: 1px solid rgba(255,255,255,0.22);
    }
    .lion-detail-metrics {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
        margin: 0.45rem 0 1rem 0;
    }
    .lion-detail-card {
        background: #1b1b1b;
        border: 1px solid #3a3a3a;
        border-radius: 8px;
        padding: 9px 10px;
        min-width: 0;
    }
    .lion-detail-label {
        color: #ffcc00 !important;
        font-size: 0.72rem;
        line-height: 1.1;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .lion-detail-value {
        color: #ffffff !important;
        font-size: 0.9rem;
        line-height: 1.15;
        font-weight: 800;
        overflow-wrap: anywhere;
    }
    .lion-detail-table {
        border: 1px solid #3a3a3a;
        border-radius: 8px;
        overflow: hidden;
        background: #181818;
        margin: 0.35rem 0 1rem 0;
    }
    .lion-detail-row {
        display: grid;
        grid-template-columns: minmax(150px, 1.8fr) 90px 84px 112px minmax(160px, 1.4fr);
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        border-bottom: 1px solid #2d2d2d;
        font-size: 0.82rem;
    }
    .lion-detail-row:last-child {
        border-bottom: 0;
    }
    .lion-detail-head {
        background: #242424;
        color: #ffcc00 !important;
        font-weight: 800;
        font-size: 0.78rem;
    }
    .lion-detail-cell {
        color: #ffffff !important;
        overflow-wrap: anywhere;
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


def normalize_hex_color(value):
    cleaned = str(value or "").strip().replace("#", "")
    if re.fullmatch(r"[0-9a-fA-F]{8}", cleaned):
        cleaned = cleaned[:6]
    if re.fullmatch(r"[0-9a-fA-F]{6}", cleaned):
        return f"#{cleaned.upper()}"
    if re.fullmatch(r"[0-9a-fA-F]{3}", cleaned):
        return f"#{cleaned.upper()}"
    return "#262626"


def contrast_text_color(hex_color):
    color = normalize_hex_color(hex_color).lstrip("#")
    if len(color) == 3:
        color = "".join([char * 2 for char in color])
    red, green, blue = [int(color[index:index + 2], 16) for index in (0, 2, 4)]
    brightness = (red * 299 + green * 587 + blue * 114) / 1000
    return "#111111" if brightness > 150 else "#ffffff"


def status_badge_html(status):
    label = str(status or "").strip() or "Pendente"
    background, foreground = STATUS_BADGE_COLORS.get(label, ("#6b7280", "#ffffff"))
    return (
        f"<span class='lion-badge' style='background:{background}; color:{foreground} !important;'>"
        f"{escape(label)}</span>"
    )


def prioridade_badge_html(prioridade):
    label = str(prioridade or "").strip() or "Verde"
    background, foreground = PRIORIDADE_BADGE_COLORS.get(label, ("#6b7280", "#ffffff"))
    return (
        f"<span class='lion-badge' style='background:{background}; color:{foreground} !important;'>"
        f"{escape(label)}</span>"
    )


def color_chip_html(hex_value, label=""):
    color = normalize_hex_color(hex_value)
    foreground = contrast_text_color(color)
    text = str(hex_value or "").strip() or "Sem HEX"
    label_text = str(label or "").strip()
    display = f"{escape(label_text)}<br><span style='color:{foreground} !important; opacity:0.88;'>{escape(text)}</span>" if label_text else escape(text)
    return f"<span class='lion-color-chip' style='background:{color}; color:{foreground} !important;'>{display}</span>"


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
                    "nome_item": "Encomenda",
                    "data_solicitacao": "Data",
                    "consultor": "Consultor",
                    "tipo_projeto": "Tipo de Projeto",
                    "peso_g": "Peso (g)",
                    "custo_rs": "Custo (R$)",
                    "preco_venda_rs": "Preço Venda (R$)",
                    "margem": "Margem",
                    "prioridade": "Prioridade",
                    "status": "Status",
                }
            )
            for column in PEDIDOS_COLUMNS:
                if column not in df.columns:
                    df[column] = ""
            df["Consultor"] = df["Consultor"].fillna("").replace("", "Isaac")
            df["Encomenda"] = df["Encomenda"].fillna("")
            df["Margem"] = df["Margem"].fillna("").replace("", "300%")
            df["Prioridade"] = df["Prioridade"].fillna("").replace("", "Verde")
            df["Status"] = df["Status"].fillna("").replace("", "Pendente")
            df["Tipo de Projeto"] = df["Tipo de Projeto"].fillna("").replace("", LISTA_PROJETOS[0])
            df = df[[column for column in PEDIDOS_COLUMNS if column in df.columns]]
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
            "nome_item": linha_editada["Encomenda"],
            "consultor": linha_editada["Consultor"],
            "tipo_projeto": linha_editada["Tipo de Projeto"],
            "peso_g": peso_editado,
            "custo_rs": round(custo_final, 2),
            "preco_venda_rs": round(preco_final, 2),
            "margem": margem_final,
            "prioridade": linha_editada["Prioridade"],
            "status": linha_editada["Status"],
        }
        mudou = any(
            [
                str(linha_editada["Cliente"]) != str(linha_original["Cliente"]),
                str(linha_editada["Encomenda"]) != str(linha_original["Encomenda"]),
                str(linha_editada["Consultor"]) != str(linha_original["Consultor"]),
                str(linha_editada["Tipo de Projeto"]) != str(linha_original["Tipo de Projeto"]),
                peso_mudou,
                custo_mudou,
                preco_mudou,
                margem_mudou,
                str(linha_editada["Prioridade"]) != str(linha_original["Prioridade"]),
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
    if arquivo and arquivo != "-":
        return arquivo
    raw = print_data.get("raw", {})
    if isinstance(raw, dict):
        print_payload = raw.get("print", {})
        for field in ["gcode_file", "subtask_name", "project_id", "task_id"]:
            value = str(print_payload.get(field) or "").strip()
            if value and value != "-":
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


def empty_filamentos():
    return pd.DataFrame(columns=FILAMENTOS_COLUMNS)


def empty_consumo_filamento():
    return pd.DataFrame(columns=CONSUMO_FILAMENTO_COLUMNS)


def load_filamentos():
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/filamentos_estoque?select=*&order=created_at.desc", headers=HEADERS)
        data = response.json() if response.status_code == 200 else []
        return pd.DataFrame(data) if data else empty_filamentos()
    except Exception:
        return empty_filamentos()


def load_consumo_filamento():
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/consumo_filamento?select=*&order=created_at.desc", headers=HEADERS)
        data = response.json() if response.status_code == 200 else []
        return pd.DataFrame(data) if data else empty_consumo_filamento()
    except Exception:
        return empty_consumo_filamento()


def save_filamento(material, cor_nome, cor_hex, marca, peso_inicial_g, observacao):
    peso = round(parse_float(peso_inicial_g), 2)
    payload = {
        "material": material or "PLA",
        "cor_nome": cor_nome or "",
        "cor_hex": cor_hex or "",
        "marca": marca or "",
        "peso_inicial_g": peso,
        "peso_atual_g": peso,
        "status": "Ativo",
        "observacao": observacao or "",
    }
    response = requests.post(f"{SUPABASE_URL}/rest/v1/filamentos_estoque", headers=HEADERS, json=payload)
    return response.status_code in [200, 201]


def update_filamento_stock(filamento_id, novo_peso):
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/filamentos_estoque?id=eq.{filamento_id}",
        headers=HEADERS,
        json={"peso_atual_g": round(max(parse_float(novo_peso), 0), 2)},
    )
    return response.status_code in [200, 204]


def register_filament_consumption(job, filamento, peso_usado_g, observacao):
    peso_usado = round(parse_float(peso_usado_g), 2)
    if peso_usado <= 0:
        return False, "Informe um peso maior que zero."
    payload = {
        "impressao_id": int(job["id"]),
        "encomenda_id": int(job["encomenda_id"]),
        "filamento_id": int(filamento["id"]),
        "peso_usado_g": peso_usado,
        "observacao": observacao or "",
    }
    response = requests.post(f"{SUPABASE_URL}/rest/v1/consumo_filamento", headers=HEADERS, json=payload)
    if response.status_code not in [200, 201]:
        return False, "Nao consegui registrar o consumo."
    estoque_atual = parse_float(filamento.get("peso_atual_g", 0))
    if not update_filamento_stock(filamento["id"], estoque_atual - peso_usado):
        return False, "Consumo salvo, mas nao consegui atualizar o estoque."
    return True, "Consumo registrado e estoque atualizado."


def filament_label(row):
    peso_atual = parse_float(row.get("peso_atual_g", 0))
    cor = row.get("cor_nome") or row.get("cor_hex") or "Sem cor"
    marca = row.get("marca") or "Sem marca"
    return f"{row.get('material', 'PLA')} | {cor} | {marca} | {peso_atual:.0f}g | ID {row['id']}"


def parse_ams_trays(print_data):
    raw = print_data.get("raw", {})
    print_payload = raw.get("print", {}) if isinstance(raw, dict) else {}
    ams_payload = print_payload.get("ams", {}) if isinstance(print_payload, dict) else {}
    ams_units = ams_payload.get("ams", []) if isinstance(ams_payload, dict) else []
    rows = []
    for ams in ams_units:
        for tray in ams.get("tray", []):
            try:
                slot_label = str(int(tray.get("id", 0)) + 1)
            except (TypeError, ValueError):
                slot_label = str(tray.get("id", "-"))
            rows.append({
                "AMS": ams.get("id", "0"),
                "Slot": slot_label,
                "Material": tray.get("tray_type", "-"),
                "Cor": tray.get("tray_color", "-"),
                "Restante (%)": tray.get("remain", "-"),
                "Status": tray.get("state", "-"),
                "Bico min": tray.get("nozzle_temp_min", "-"),
                "Bico max": tray.get("nozzle_temp_max", "-"),
            })
    return pd.DataFrame(rows)


def render_bambu_alerts(print_data):
    raw = print_data.get("raw", {})
    print_payload = raw.get("print", {}) if isinstance(raw, dict) else {}
    state = str(print_payload.get("gcode_state", "")).upper()
    alerts = []
    if state in ["PAUSE", "PAUSED"]:
        alerts.append("Impressora pausada.")
    if state == "FINISH":
        alerts.append("Impressao finalizada. Confira se o pedido pode ser concluido.")
    if print_payload.get("hms"):
        alerts.append("A impressora reportou alerta HMS.")
    filamentos = load_filamentos()
    if not filamentos.empty:
        baixos = filamentos[filamentos["peso_atual_g"].apply(parse_float) <= 100]
        if not baixos.empty:
            alerts.append(f"{len(baixos)} rolo(s) com 100g ou menos no estoque.")
    for alert in alerts:
        st.warning(alert)


def render_bambu_status_details(print_data):
    raw = print_data.get("raw", {})
    print_payload = raw.get("print", {}) if isinstance(raw, dict) else {}
    details = {
        "Arquivo": current_print_file(print_data) or "-",
        "Tipo": print_payload.get("print_type", "-"),
        "Sinal Wi-Fi": print_payload.get("wifi_signal", "-"),
        "Camada atual": print_payload.get("layer_num", "-"),
        "Total de camadas": print_payload.get("total_layer_num", "-"),
        "Erro": print_payload.get("print_error", 0),
        "SD Card": "Sim" if print_payload.get("sdcard") else "Nao",
    }
    st.dataframe(pd.DataFrame([details]), hide_index=True, use_container_width=True)


def render_color_table(rows, headers):
    header_html = "".join([f"<div>{escape(header)}</div>" for header in headers])
    row_html = [f"<div class='lion-color-row lion-color-head'>{header_html}</div>"]
    for row in rows:
        row_html.append(
            "<div class='lion-color-row'>"
            + "".join([f"<div>{cell}</div>" for cell in row])
            + "</div>"
        )
    st.markdown(f"<div class='lion-color-table'>{''.join(row_html)}</div>", unsafe_allow_html=True)


def render_ams_color_table(ams_df):
    rows = []
    for _, row in ams_df.iterrows():
        rows.append(
            [
                escape(str(row.get("Slot", "-"))),
                f"<span class='lion-color-main'>{escape(str(row.get('Material', '-')))}</span>",
                color_chip_html(row.get("Cor", "-")),
                escape(str(row.get("Restante (%)", "-"))),
                escape(str(row.get("Bico min", "-"))),
                escape(str(row.get("Bico max", "-"))),
            ]
        )
    render_color_table(rows, ["Slot", "Material", "Cor", "Restante", "Bico min", "Bico max"])


def render_filament_color_table(estoque_view):
    rows = []
    for _, row in estoque_view.iterrows():
        rows.append(
            [
                f"<span class='lion-color-main'>{escape(str(row.get('material', '-')))}</span>",
                color_chip_html(row.get("cor_hex", ""), row.get("cor_nome", "")),
                escape(str(row.get("marca", "-") or "-")),
                f"{parse_float(row.get('peso_atual_g', 0)):.0f}g",
                f"{parse_float(row.get('peso_inicial_g', 0)):.0f}g",
                f"{parse_float(row.get('Restante (%)', 0)):.1f}%",
            ]
        )
    render_color_table(rows, ["Material", "Cor", "Marca", "Atual", "Inicial", "Restante"])


def render_ams_summary(print_data):
    st.write("### AMS e filamentos carregados")
    ams_df = parse_ams_trays(print_data)
    if ams_df.empty:
        st.info("Nenhum dado de AMS recebido agora.")
        return
    render_ams_color_table(ams_df)


def render_filament_inventory():
    st.write("### Estoque de filamentos")
    filamentos = load_filamentos()
    consumo = load_consumo_filamento()
    if not filamentos.empty:
        total_estoque = filamentos["peso_atual_g"].apply(parse_float).sum()
        rolos_baixos = len(filamentos[filamentos["peso_atual_g"].apply(parse_float) <= 100])
        total_consumido = consumo["peso_usado_g"].apply(parse_float).sum() if not consumo.empty else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("Rolos cadastrados", len(filamentos))
        c2.metric("Estoque total", f"{total_estoque:.0f}g")
        c3.metric("Consumo registrado", f"{total_consumido:.0f}g", delta=f"{rolos_baixos} baixo(s)")
        estoque_view = filamentos.copy()
        estoque_view["Restante (%)"] = estoque_view.apply(
            lambda row: round((parse_float(row["peso_atual_g"]) / parse_float(row["peso_inicial_g"])) * 100, 1)
            if parse_float(row["peso_inicial_g"]) > 0 else 0,
            axis=1,
        )
        render_filament_color_table(estoque_view)
    else:
        st.info("Nenhum rolo cadastrado ainda.")
    with st.form("form_filamento", clear_on_submit=True):
        st.write("#### Cadastrar rolo")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            material = st.text_input("Material", value="PLA")
            cor_nome = st.text_input("Cor/nome")
        with col_b:
            cor_hex = st.text_input("Cor HEX", placeholder="D5B6A4FF")
            marca = st.text_input("Marca")
        with col_c:
            peso_inicial = st.number_input("Peso inicial (g)", min_value=0.0, value=1000.0, step=50.0)
            observacao = st.text_input("Observacao")
        if st.form_submit_button("Cadastrar filamento"):
            if save_filamento(material, cor_nome, cor_hex, marca, peso_inicial, observacao):
                st.success("Filamento cadastrado.")
                st.rerun()
            else:
                st.error("Nao consegui cadastrar o filamento.")


def pedido_label(row):
    item = str(row.get("Encomenda", "") or row.get("Tipo de Projeto", "")).strip()
    return f"{row['Cliente']} | {item} | {row['Tipo de Projeto']} | {row['Data']} | {row['Status']} | ID {row['id']}"


def get_order_summary(df_pedidos):
    if df_pedidos.empty or "id" not in df_pedidos.columns:
        return {}
    return {
        int(row["id"]): {
            "Cliente": row.get("Cliente", ""),
            "Encomenda": row.get("Encomenda", ""),
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
    jobs_view["Encomenda"] = jobs_view["encomenda_id"].apply(
        lambda value: order_summary.get(int(value), {}).get("Encomenda", "")
    )
    jobs_view["Tipo de Projeto"] = jobs_view["encomenda_id"].apply(
        lambda value: order_summary.get(int(value), {}).get("Tipo de Projeto", "")
    )
    jobs_view["Status do Pedido"] = jobs_view["encomenda_id"].apply(
        lambda value: order_summary.get(int(value), {}).get("Status do Pedido", "")
    )
    jobs_view["Tempo restante"] = jobs_view["tempo_restante_min"].apply(format_remaining_time)

    st.write("#### Impressoes vinculadas")
    st.dataframe(
        jobs_view[["Cliente", "Encomenda", "Tipo de Projeto", "arquivo", "status", "progresso", "Tempo restante", "Status do Pedido"]],
        hide_index=True,
        use_container_width=True,
    )

    opcoes_jobs = {
        f"{row['arquivo']} | {row['Cliente']} | {row['Encomenda']} | {row['status']} | ID {row['id']}": row
        for _, row in jobs_view.iterrows()
    }
    job_escolhido = st.selectbox("Gerenciar impressao vinculada", list(opcoes_jobs.keys()))
    job = opcoes_jobs[job_escolhido]

    filamentos = load_filamentos()
    if filamentos.empty:
        st.info("Cadastre um rolo de filamento para dar baixa no estoque desta impressao.")
    else:
        with st.form("form_consumo_filamento"):
            st.write("#### Baixa de filamento desta impressao")
            filamento_options = {filament_label(row): row for _, row in filamentos.iterrows()}
            filamento_label_escolhido = st.selectbox("Filamento usado", list(filamento_options.keys()))
            peso_usado = st.number_input("Peso usado nesta mesa (g)", min_value=0.0, step=1.0)
            observacao_consumo = st.text_input("Observacao da baixa")
            if st.form_submit_button("Dar baixa no estoque"):
                ok, message = register_filament_consumption(job, filamento_options[filamento_label_escolhido], peso_usado, observacao_consumo)
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

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


def gateway_request(path, method="GET", timeout=35, printer_name=None):
    gateway = get_bambu_gateway_config()
    if not gateway["enabled"]:
        return None

    separator = "&" if "?" in path else "?"
    printer_query = f"{separator}printer={quote(str(printer_name))}" if printer_name else ""
    try:
        response = requests.request(
            method,
            f"{gateway['url']}{path}{printer_query}",
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


def read_bambu_status_via_gateway(printer_name):
    return gateway_request("/status", timeout=45, printer_name=printer_name)


def send_bambu_light_command_via_gateway(mode, printer_name):
    result = gateway_request(f"/light/{mode}", method="POST", timeout=30, printer_name=printer_name)
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


def render_encomenda_status_overview(df_pedidos_filtrado):
    if df_pedidos_filtrado.empty:
        return
    rows = []
    for _, row in df_pedidos_filtrado.iterrows():
        item = str(row.get("Encomenda", "") or row.get("Tipo de Projeto", "")).strip()
        title = f"{row.get('Cliente', '')} | {item}"
        subtitle = f"{row.get('Data', '')} | {parse_float(row.get('Peso (g)', 0)):.0f}g | ID {row.get('id', '')}"
        rows.append(
            "<div class='lion-status-row'>"
            f"<div><div class='lion-status-title'>{escape(title)}</div>"
            f"<div class='lion-status-sub'>{escape(subtitle)}</div></div>"
            f"<div>{prioridade_badge_html(row.get('Prioridade', ''))} {status_badge_html(row.get('Status', ''))}</div>"
            "</div>"
        )
    st.markdown(f"<div class='lion-status-board'>{''.join(rows)}</div>", unsafe_allow_html=True)


def render_detail_metrics(metrics):
    cards = []
    for label, value in metrics:
        cards.append(
            "<div class='lion-detail-card'>"
            f"<div class='lion-detail-label'>{escape(str(label))}</div>"
            f"<div class='lion-detail-value'>{escape(str(value))}</div>"
            "</div>"
        )
    st.markdown(f"<div class='lion-detail-metrics'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_print_jobs_detail_table(jobs_order, colors_by_job):
    header = ["Arquivo", "Status", "Progresso", "Tempo restante", "Cores HEX"]
    rows = [
        "<div class='lion-detail-row lion-detail-head'>"
        + "".join([f"<div>{escape(col)}</div>" for col in header])
        + "</div>"
    ]
    for _, row in jobs_order.iterrows():
        job_id = int(row["id"]) if not pd.isna(row.get("id")) else None
        color_chips = colors_by_job.get(job_id, "")
        if not color_chips:
            color_chips = "<span class='lion-color-sub'>Sem baixa registrada</span>"
        rows.append(
            "<div class='lion-detail-row'>"
            f"<div class='lion-detail-cell'>{escape(str(row.get('arquivo', '') or ''))}</div>"
            f"<div class='lion-detail-cell'>{escape(str(row.get('status', '') or ''))}</div>"
            f"<div class='lion-detail-cell'>{escape(str(row.get('progresso', 0) or 0))}%</div>"
            f"<div class='lion-detail-cell'>{escape(format_remaining_time(row.get('tempo_restante_min', 0)))}</div>"
            f"<div class='lion-detail-cell'>{color_chips}</div>"
            "</div>"
        )
    st.markdown(f"<div class='lion-detail-table'>{''.join(rows)}</div>", unsafe_allow_html=True)


def render_order_detail_content(order_row):
    def safe_int(value):
        try:
            if pd.isna(value):
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    encomenda_id = int(order_row["id"])
    jobs = load_bambu_print_jobs()
    consumo = load_consumo_filamento()
    filamentos = load_filamentos()

    jobs_order = jobs[jobs["encomenda_id"].astype(str) == str(encomenda_id)].copy() if not jobs.empty else empty_impressoes()
    consumo_order = (
        consumo[consumo["encomenda_id"].astype(str) == str(encomenda_id)].copy()
        if not consumo.empty
        else empty_consumo_filamento()
    )
    total_consumido = consumo_order["peso_usado_g"].apply(parse_float).sum() if not consumo_order.empty else 0
    finalizadas = len(jobs_order[jobs_order["status"].astype(str) == "Finalizada"]) if not jobs_order.empty else 0

    st.write(f"### {order_row.get('Encomenda', '') or order_row.get('Tipo de Projeto', '')}")
    st.caption(f"Cliente: {order_row.get('Cliente', '')} | Consultor: {order_row.get('Consultor', '')} | ID {encomenda_id}")

    render_detail_metrics(
        [
            ("Status do pedido", str(order_row.get("Status", "-"))),
            ("Prioridade", str(order_row.get("Prioridade", "-"))),
            ("Mesas vinculadas", len(jobs_order)),
            ("Mesas finalizadas", finalizadas),
            ("Filamento baixado", f"{total_consumido:.0f}g"),
        ]
    )

    jobs_lookup = {
        safe_int(row["id"]): row.get("arquivo", "")
        for _, row in jobs_order.iterrows()
        if safe_int(row.get("id")) is not None
    }
    filamentos_lookup = {
        safe_int(row["id"]): row.to_dict()
        for _, row in filamentos.iterrows()
        if safe_int(row.get("id")) is not None
    }
    colors_by_job = {}
    if not consumo_order.empty:
        for _, row in consumo_order.iterrows():
            job_id = safe_int(row.get("impressao_id"))
            filamento = filamentos_lookup.get(safe_int(row.get("filamento_id")), {})
            cor_hex = filamento.get("cor_hex", "") if isinstance(filamento, dict) else ""
            cor_nome = filamento.get("cor_nome", "") if isinstance(filamento, dict) else ""
            if job_id is not None and (cor_hex or cor_nome):
                colors_by_job.setdefault(job_id, [])
                label = cor_nome or cor_hex
                colors_by_job[job_id].append(color_chip_html(cor_hex, label))
    colors_by_job = {
        job_id: "".join(dict.fromkeys(chips))
        for job_id, chips in colors_by_job.items()
    }

    st.write("#### Impressões vinculadas")
    if jobs_order.empty:
        st.info("Nenhuma impressão vinculada a esta encomenda ainda.")
    else:
        render_print_jobs_detail_table(jobs_order, colors_by_job)

    st.write("#### Filamentos usados")
    if consumo_order.empty:
        st.info("Nenhuma baixa de filamento registrada para esta encomenda.")
        return

    consumo_rows = []
    for _, row in consumo_order.iterrows():
        filamento = filamentos_lookup.get(safe_int(row.get("filamento_id")), {})
        cor_nome = filamento.get("cor_nome", "") if isinstance(filamento, dict) else ""
        cor_hex = filamento.get("cor_hex", "") if isinstance(filamento, dict) else ""
        consumo_rows.append(
            {
                "Impressão": jobs_lookup.get(safe_int(row.get("impressao_id")), ""),
                "Material": filamento.get("material", "") if isinstance(filamento, dict) else "",
                "Cor": cor_nome or cor_hex,
                "Marca": filamento.get("marca", "") if isinstance(filamento, dict) else "",
                "Peso usado (g)": parse_float(row.get("peso_usado_g", 0)),
                "Observação": row.get("observacao", ""),
                "Data": row.get("created_at", ""),
            }
        )
    st.dataframe(pd.DataFrame(consumo_rows), hide_index=True, use_container_width=True)


def open_order_details_dialog(order_row):
    title = f"Detalhes da encomenda | ID {order_row['id']}"
    if hasattr(st, "dialog"):
        @st.dialog(title)
        def _details_dialog():
            render_order_detail_content(order_row)

        _details_dialog()
    else:
        st.session_state["detalhes_encomenda_id"] = int(order_row["id"])


def render_order_details_launcher(df_pedidos_filtrado):
    if df_pedidos_filtrado.empty:
        return

    st.write("### Detalhes do pedido")
    opcoes_detalhes = {
        f"{row['Cliente']} | {row['Encomenda'] or row['Tipo de Projeto']} | ID {row['id']}": row
        for _, row in df_pedidos_filtrado.iterrows()
    }
    col_select, col_button = st.columns([2, 1])
    with col_select:
        detalhe_escolhido = st.selectbox("Abrir detalhes da encomenda", list(opcoes_detalhes.keys()))
    with col_button:
        st.write("")
        if st.button("Abrir detalhes", use_container_width=True):
            open_order_details_dialog(opcoes_detalhes[detalhe_escolhido])

    fallback_id = st.session_state.get("detalhes_encomenda_id")
    if fallback_id:
        registro = df_pedidos_filtrado[df_pedidos_filtrado["id"].astype(int) == int(fallback_id)]
        if not registro.empty:
            with st.expander("Detalhes da encomenda", expanded=True):
                render_order_detail_content(registro.iloc[0])


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
                    st.session_state["bambu_status"] = read_bambu_status_via_gateway(printer["name"])
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
                render_bambu_alerts(data)
                render_bambu_status_details(data)
                render_ams_summary(data)
                render_filament_inventory()
                render_bambu_order_linking(printer, data, df_pedidos)
            else:
                st.warning(status["message"])

    with col_actions:
        st.write("### Controles")
        if st.button("Ligar luz", use_container_width=True):
            with st.spinner("Enviando comando..."):
                if gateway_config["enabled"]:
                    ok, message = send_bambu_light_command_via_gateway("on", printer["name"])
                else:
                    ok, message = send_bambu_light_command(printer, "on")
            if ok:
                st.success(message)
            else:
                st.error(message)
        if st.button("Desligar luz", use_container_width=True):
            with st.spinner("Enviando comando..."):
                if gateway_config["enabled"]:
                    ok, message = send_bambu_light_command_via_gateway("off", printer["name"])
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
            nome_item = st.text_input("Encomenda", placeholder="Ex: Chaveiro do Cruzeiro")
            data_sel = st.date_input("Data de Solicitação", today_brasilia(), format="DD/MM/YYYY")
            tipo_projeto = st.selectbox("Tipo de Projeto", LISTA_PROJETOS)
            peso_gramas = st.number_input("Peso em Gramas (g)", min_value=0.0, step=1.0)
            margem_texto = st.selectbox("Margem de Venda", list(OPCOES_MARGEM.keys()), index=1)
            prioridade = st.selectbox("Prioridade", PRIORIDADE_OPTIONS)
            status_inicial = st.selectbox("Status", STATUS_OPTIONS)

            if st.form_submit_button("Salvar Encomenda"):
                if cliente and peso_gramas > 0:
                    custo_calc, preco_calc = calculate_order_values(peso_gramas, margem_texto)
                    data_br = data_sel.strftime("%d/%m/%Y")

                    payload = {
                        "cliente": cliente,
                        "nome_item": nome_item,
                        "consultor": consultor,
                        "data_solicitacao": data_br,
                        "tipo_projeto": tipo_projeto,
                        "peso_g": peso_gramas,
                        "custo_rs": custo_calc,
                        "preco_venda_rs": preco_calc,
                        "margem": margem_texto,
                        "prioridade": prioridade,
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
            render_encomenda_status_overview(df_pedidos_filtrado)
            df_pedidos_exibicao = df_pedidos_filtrado.copy()
            df_pedidos_exibicao["Custo (R$)"] = df_pedidos_exibicao["Custo (R$)"].apply(parse_float)
            df_pedidos_exibicao["Preço Venda (R$)"] = df_pedidos_exibicao["Preço Venda (R$)"].apply(parse_float)
            tabela_editavel = st.data_editor(
                df_pedidos_exibicao,
                column_config={
                    "id": None,
                    "created_at": None,
                    "Cliente": st.column_config.TextColumn("Cliente", required=True),
                    "Encomenda": st.column_config.TextColumn("Encomenda"),
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
                    "Prioridade": st.column_config.SelectboxColumn(
                        "Prioridade",
                        options=PRIORIDADE_OPTIONS,
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
            render_order_details_launcher(df_pedidos_filtrado)
            col_salvar, col_excluir = st.columns(2)
            with col_salvar:
                if st.button("Salvar alterações do prontuário", use_container_width=True):
                    sync_encomenda_changes(df_pedidos_filtrado, tabela_editavel)
            with col_excluir:
                opcoes_exclusao = {
                    f"{row['Cliente']} | {row['Encomenda']} | {row['Tipo de Projeto']} | {row['Data']} | ID {row['id']}": row["id"]
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
