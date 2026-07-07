import streamlit as st
import pandas as pd
from datetime import datetime
import requests


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


def sync_status_changes(df_original, df_editado):
    if "id" not in df_original.columns or "id" not in df_editado.columns:
        return

    alterou_status = False
    for _, linha_editada in df_editado.iterrows():
        registro = df_original[df_original["id"] == linha_editada["id"]]
        if registro.empty:
            continue

        status_original = registro.iloc[0]["Status"]
        if linha_editada["Status"] != status_original:
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/encomendas?id=eq.{linha_editada['id']}",
                headers=HEADERS,
                json={"status": linha_editada["Status"]},
            )
            alterou_status = True

    if alterou_status:
        st.success("Status atualizado no banco de dados!")
        st.rerun()


def render_encomendas(df_pedidos):
    st.markdown("<h2 style='color: #ffcc00;'>📋 Gestão de Encomendas Ativas</h2>", unsafe_allow_html=True)
    col_form, col_tab = st.columns([1, 2])

    with col_form:
        st.write("### ➕ Nova Encomenda")
        with st.form("form_encomenda", clear_on_submit=True):
            cliente = st.text_input("Nome do Cliente")
            consultor = st.selectbox("Consultor", CONSULTORES)
            data_sel = st.date_input("Data de Solicitação", datetime.now(), format="DD/MM/YYYY")
            tipo_projeto = st.selectbox("Tipo de Projeto", LISTA_PROJETOS)
            peso_gramas = st.number_input("Peso em Gramas (g)", min_value=0.0, step=1.0)
            margem_texto = st.selectbox("Margem de Venda", list(OPCOES_MARGEM.keys()), index=1)
            status_inicial = st.selectbox("Status", STATUS_OPTIONS)

            if st.form_submit_button("Salvar Encomenda"):
                if cliente and peso_gramas > 0:
                    custo_calc = peso_gramas * 0.15
                    preco_calc = custo_calc * OPCOES_MARGEM[margem_texto]
                    data_br = data_sel.strftime("%d/%m/%Y")

                    payload = {
                        "cliente": cliente,
                        "consultor": consultor,
                        "data_solicitacao": data_br,
                        "tipo_projeto": tipo_projeto,
                        "peso_g": peso_gramas,
                        "custo_rs": round(custo_calc, 2),
                        "preco_venda_rs": round(preco_calc, 2),
                        "margem": margem_texto,
                        "status": status_inicial,
                    }
                    requests.post(f"{SUPABASE_URL}/rest/v1/encomendas", headers=HEADERS, json=payload)
                    st.success("Salvo no banco de dados!")
                    st.rerun()

    with col_tab:
        st.write("### 🔍 Cronograma Prontuário")
        filtro_status = st.multiselect("Filtrar por Status:", STATUS_OPTIONS, default=["Pendente", "Imprimindo"])
        df_pedidos_filtrado = (
            df_pedidos[df_pedidos["Status"].isin(filtro_status)] if not df_pedidos.empty else df_pedidos
        )

        if not df_pedidos_filtrado.empty:
            df_pedidos_exibicao = format_currency_columns(
                df_pedidos_filtrado,
                ["Custo (R$)", "Preço Venda (R$)"],
            )
            tabela_editavel = st.data_editor(
                df_pedidos_exibicao,
                column_config={
                    "id": None,
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        options=STATUS_OPTIONS,
                        required=True,
                    ),
                },
                disabled=[
                    "Cliente",
                    "Consultor",
                    "Data",
                    "Tipo de Projeto",
                    "Peso (g)",
                    "Custo (R$)",
                    "Preço Venda (R$)",
                    "Margem",
                ],
                use_container_width=True,
            )
            sync_status_changes(df_pedidos_filtrado, tabela_editavel)
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

aba_producao, aba_varejo, aba_graficos = st.tabs(
    ["🏭 Fluxo de Encomendas", "🏪 Estoque e Comércio Varejo", "📊 Desempenho de Lojas"]
)

with aba_producao:
    render_encomendas(df_pedidos)

with aba_varejo:
    render_varejo(df_varejo)

with aba_graficos:
    render_desempenho_lojas(df_varejo)
