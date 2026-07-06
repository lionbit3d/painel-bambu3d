import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# Configuração da página da Dashboard
st.set_page_config(page_title="LionBit 3D Studio - Painel de Controle", layout="wide")

# ==============================================================================
# 🔑 CONEXÃO DIRETA COM O BANCO DE DADOS EM NUVEM (SUPABASE VIA API HTTP)
# ==============================================================================
SUPABASE_URL = "https://ntybsaywkdmqcjhslehw.supabase.co/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50eWJzYXl3a2RtcWNqaHNsZWh3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMzNTQwMjgsImV4cCI6MjA5ODkzMDAyOH0.0pV_Lu60COGdjBCuVVSmqf2TNqH3I_0xlLSeJckenzA"

# Cabeçalhos de autenticação exigidos pelo Supabase
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# 🎨 DESIGN PREMIUM (Cinza-Grafite de Alto Contraste, Fontes Claras e Botões Dourados)
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
</style>
"""
st.markdown(design_premium, unsafe_allow_html=True)

# 🦁 LOGO REAL DO LIONBIT
URL_SUA_LOGO = "logo.png"

col_logo, col_titulo = st.columns(2) 
with col_logo:
    try: st.image(URL_SUA_LOGO, width=120)
    except: st.write("🦁 [Logo]")
with col_titulo:
    st.markdown("<h1 style='color: #ffcc00; margin-bottom: 0; font-family: sans-serif; font-size: 42px;'>LionBit 3D Studio</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #ffffff; margin-top: 0; font-family: sans-serif; font-weight: 300;'>Painel Integrado de Manufatura e Gestão de Vendas</h3>", unsafe_allow_html=True)

# 📥 LEITURA DOS DADOS EM TEMPO REAL VIA API HTTP PURA
try:
    url_get_pedidos = f"{SUPABASE_URL}/rest/v1/encomendas?select=*"
    resposta_pedidos = requests.get(url_get_pedidos, headers=HEADERS)
    dados_p = resposta_pedidos.json() if resposta_pedidos.status_code == 200 else []
    df_pedidos = pd.DataFrame(dados_p) if dados_p else pd.DataFrame(columns=["Cliente", "Data", "Tipo de Projeto", "Peso (g)", "Custo (R$)", "Preço Venda (R$)", "Margem", "Status"])
    if not df_pedidos.empty:
        df_pedidos = df_pedidos.rename(columns={"data_solicitacao": "Data", "tipo_projeto": "Tipo de Projeto", "peso_g": "Peso (g)", "custo_rs": "Custo (R$)", "preco_venda_rs": "Preço Venda (R$)", "margem": "Margem", "status": "Status"})
except:
    df_pedidos = pd.DataFrame(columns=["Cliente", "Data", "Tipo de Projeto", "Peso (g)", "Custo (R$)", "Preço Venda (R$)", "Margem", "Status"])

try:
    url_get_varejo = f"{SUPABASE_URL}/rest/v1/varejo?select=*"
    resposta_varejo = requests.get(url_get_varejo, headers=HEADERS)
    dados_v = resposta_varejo.json() if resposta_varejo.status_code == 200 else []
    df_varejo = pd.DataFrame(dados_v) if dados_v else pd.DataFrame(columns=["Produto", "Local de Venda", "Quantidade Enviada", "Quantidade Vendida", "Peso Unit. (g)", "Custo Unit. (R$)", "Preço Unit. Venda (R$)"])
    if not df_varejo.empty:
        df_varejo = df_varejo.rename(columns={"produto": "Produto", "local_venda": "Local de Venda", "qtd_enviada": "Quantidade Enviada", "qtd_vendida": "Quantidade Vendida", "peso_unit_g": "Peso Unit. (g)", "custo_unit_rs": "Custo Unit. (R$)", "preco_unit_venda_rs": "Preço Unit. Venda (R$)"})
except:
    df_varejo = pd.DataFrame(columns=["Produto", "Local de Venda", "Quantidade Enviada", "Quantidade Vendida", "Peso Unit. (g)", "Custo Unit. (R$)", "Preço Unit. Venda (R$)"])

# --- ÁREA DE MÉTRICAS GLOBAIS ---
custo_pedidos = df_pedidos["Custo (R$)"].sum() if not df_pedidos.empty else 0.0
faturamento_pedidos = df_pedidos["Preço Venda (R$)"].sum() if not df_pedidos.empty else 0.0

if not df_varejo.empty:
    df_varejo["Total Custo Enviado"] = df_varejo["Quantidade Enviada"] * df_varejo["Custo Unit. (R$)"]
    df_varejo["Total Faturamento Real"] = df_varejo["Quantidade Vendida"] * df_varejo["Preço Unit. Venda (R$)"]
    df_varejo["Lucro Gerado (R$)"] = df_varejo["Total Faturamento Real"] - (df_varejo["Quantidade Vendida"] * df_varejo["Custo Unit. (R$)"])
    custo_varejo = df_varejo["Total Custo Enviado"].sum()
    faturamento_varejo = df_varejo["Total Faturamento Real"].sum()
else:
    custo_varejo, faturamento_varejo = 0.0, 0.0

custo_global = custo_pedidos + custo_varejo
faturamento_global = faturamento_pedidos + faturamento_varejo
lucro_global = faturamento_global - custo_global

col1, col2, col3, col4 = st.columns(4)
col1.metric("📦 Total de Pedidos Ativos", len(df_pedidos) + len(df_varejo))
col2.metric("📉 Custo Total de Material", f"R$ {custo_global:.2f}")
col3.metric("💰 Faturamento Bruto", f"R$ {faturamento_global:.2f}")
col4.metric("🔥 Lucro Líquido Geral", f"R$ {lucro_global:.2f}")

st.markdown("---")

# ------------------------------------------------------------------------------
# 🗂️ ABAS DE NAVEGAÇÃO
# ------------------------------------------------------------------------------
aba_producao, aba_varejo, aba_graficos = st.tabs(["🏭 Fluxo de Encomendas", "🏪 Estoque e Comércio Varejo", "📊 Desempenho de Lojas"])

# --- ABA 1: FLUXO DE ENCOMENDAS ---
with aba_producao:
    st.markdown("<h2 style='color: #ffcc00;'>📋 Gestão de Encomendas Ativas</h2>", unsafe_allow_html=True)
    col_form, col_tab = st.columns(2)
    
    with col_form:
        st.write("### ➕ Nova Encomenda")
        with st.form("form_encomenda", clear_on_submit=True):
            cliente = st.text_input("Nome do Cliente")
            data_sel = st.date_input("Data de Solicitação", datetime.now(), format="DD/MM/YYYY")
            lista_projetos = ["Suporte de Celular", "Letreiro de Quarto", "Boneco Articulado", "Boneco Decorativo", "Chaveiro", "Utilitário", "Utensílio Doméstico", "Peça Técnica"]
            tipo_projeto = st.selectbox("Tipo de Projeto", lista_projetos)
            peso_gramas = st.number_input("Peso em Gramas (g)", min_value=0.0, step=1.0)
            opcoes_margem = {"250%": 2.5, "300%": 3.0, "350%": 3.5, "400%": 4.0}
            margem_texto = st.selectbox("Margem de Venda", list(opcoes_margem.keys()), index=1)
            status_inicial = st.selectbox("Status", ["Pendente", "Imprimindo", "Concluído"])
            
            if st.form_submit_button("Salvar Encomenda"):
                if cliente and peso_gramas > 0:
                    custo_calc = peso_gramas * 0.15
                    preco_calc = custo_calc * opcoes_margem[margem_texto]
                    data_br = data_sel.strftime("%d/%m/%Y")
                    
                    payload = {"cliente": cliente, "data_solicitacao": data_br, "tipo_projeto": tipo_projeto, "peso_g": peso_gramas, "custo_rs": round(custo_calc, 2), "preco_venda_rs": round(preco_calc, 2), "margem": margem_texto, "status": status_inicial}
                    requests.post(f"{SUPABASE_URL}/rest/v1/encomendas", headers=HEADERS, json=payload)
                    st.success("Salvo no banco de dados!")
                    st.rerun()

    with col_tab:
        st.write("### 🔍 Cronograma Prontuário")
        filtro_status = st.multiselect("Filtrar por Status:", ["Pendente", "Imprimindo", "Concluído"], default=["Pendente", "Imprimindo"])
        df_pedidos_filtrado = df_pedidos[df_pedidos["Status"].isin(filtro_status)] if not df_pedidos.empty else df_pedidos
        st.dataframe(df_pedidos_filtrado, use_container_width=True)

# --- ABA 2: ESTOQUE E COMÉRCIO VAREJO ---
with aba_varejo:
    st.markdown("<h2 style='color: #ffcc00;'>🏪 Produtos em Comércio (Varejo / Consignação)</h2>", unsafe_allow_html=True)
    col_form2, col_tab2 = st.columns(2)
    
    with col_form2:
        st.write("### ➕ Cadastrar Lote no Varejo")
        with st.form("form_varejo", clear_on_submit=True):
            produto = st.text_input("Nome do Produto")
            local = st.text_input("Loja Parceira / Ponto de Venda")
            qtd_enviada = st.number_input("Qtd Enviada para a Loja", min_value=1, step=1)
            qtd_vendida = st.number_input("Qtd Já Vendida pela Loja", min_value=0, max_value=int(qtd_enviada if qtd_enviada > 0 else 1), step=1)
            peso_unit = st.number_input("Peso de 1 Unidade (g)", min_value=0.0, step=1.0)
            preco_loja = st.number_input("Preço Cobrado no Varejo (R$)", min_value=0.0, step=1.0)
            
            if st.form_submit_button("Registrar no Varejo"):
                if produto and local and peso_unit > 0:
                    custo_u = peso_unit * 0.15
