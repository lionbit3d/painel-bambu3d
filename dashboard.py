import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página da Dashboard
st.set_page_config(page_title="LionBit 3D Studio - Painel de Controle", layout="wide")

# 🎨 DESIGN PREMIUM CORRIGIDO (Contraste Máximo com Fontes Brancas e Botões Ouro)
design_premium = """
<style>
    /* Fundo geral grafite escuro com textos forçados em BRANCO PURO */
    .stApp {
        background-color: #121212;
        color: #ffffff !important;
    }
    h1, h2, h3, p, span, label, th, td, div {
        color: #ffffff !important;
    }
    
    /* Força os rótulos de formulários a ficarem visíveis em branco */
    .stWidgetFormLabel > div {
        color: #ffffff !important;
    }
    
    /* Blocos de métricas superiores com borda dourada */
    div[data-testid="stMetric"] {
        background-color: #1e1e1e;
        border: 2px solid #ffcc00;
        border-radius: 10px;
        padding: 15px;
    }
    div[data-testid="stMetricLabel"] {
        color: #ffcc00 !important;
        font-weight: bold;
        font-size: 16px;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: bold;
    }
    
    /* Abas de Navegação (Tabs) */
    button[data-baseweb="tab"] {
        color: #aaaaaa !important;
        font-size: 16px;
    }
    button[aria-selected="true"] {
        color: #ffcc00 !important;
        border-bottom-color: #ffcc00 !important;
        font-weight: bold;
    }
    
    /* Caixas de Entrada de Texto e Seleção */
    input, select, textarea {
        background-color: #262626 !important;
        color: #ffffff !important;
    }
    
    /* BOTÃO EM FORMULÁRIOS: Fundo ouro com letra preta grossa garantida */
    .stFormSubmitButton > button {
        background-color: #ffcc00 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: 2px solid #ffcc00 !important;
        border-radius: 5px !important;
        width: 100% !important;
        padding: 10px 0px !important;
    }
    .stFormSubmitButton > button:hover {
        background-color: #e6b800 !important;
        color: #000000 !important;
        border-color: #e6b800 !important;
    }
</style>
"""
st.markdown(design_premium, unsafe_allow_html=True)

# 🦁 LOGO REAL DO LIONBIT (Puxando de forma segura da raiz do seu GitHub)
col_logo, col_titulo = st.columns([1, 5]) # Dá o espaçamento correto no topo
with col_logo:
    try:
        # Lê o arquivo local enviado para o GitHub
        st.image("logo.png", width=120)
    except:
        # Caso o arquivo mude de nome, mostra o emoji sem travar o sistema
        st.write("🦁 [Logo]")
with col_titulo:
    st.markdown("<h1 style='color: #ffcc00; margin-bottom: 0; font-family: sans-serif; font-size: 42px;'>LionBit 3D Studio</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #ffffff; margin-top: 0; font-family: sans-serif; font-weight: 300;'>Painel Integrado de Manufatura e Gestão de Vendas</h3>", unsafe_allow_html=True)

# 📥 BANCO DE DADOS EM MEMÓRIA
if 'pedidos' not in st.session_state:
    st.session_state.pedidos = pd.DataFrame([
        {
            "Cliente": "João Silva", "Data": "06/07/2026", "Tipo de Projeto": "Suporte de Celular", 
            "Peso (g)": 58.0, "Custo (R$)": 8.70, "Preço Venda (R$)": 34.80, "Margem": "400%", "Status": "Concluído"
        }
    ])

if 'varejo' not in st.session_state:
    st.session_state.varejo = pd.DataFrame([
        {
            "Produto": "Chaveiro Stitch", "Local de Venda": "Loja A (Shopping)", "Quantidade Enviada": 20, 
            "Quantidade Vendida": 12, "Peso Unit. (g)": 12.0, "Custo Unit. (R$)": 1.80, "Preço Unit. Venda (R$)": 15.00
        },
        {
            "Produto": "Boneco Articulado", "Local de Venda": "Banca Central (Centro)", "Quantidade Enviada": 10, 
            "Quantidade Vendida": 3, "Peso Unit. (g)": 80.0, "Custo Unit. (R$)": 12.00, "Preço Unit. Venda (R$)": 50.00
        }
    ])

# ------------------------------------------------------------------------------
# 📈 ÁREA DE MÉTRICAS GLOBAIS
# ------------------------------------------------------------------------------
df_pedidos = st.session_state.pedidos
df_varejo = st.session_state.varejo

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
                    
                    nova_enc = {
                        "Cliente": cliente, "Data": data_br, "Tipo de Projeto": tipo_projeto,
                        "Peso (g)": peso_gramas, "Custo (R$)": round(custo_calc, 2),
                        "Preço Venda (R$)": round(preco_calc, 2), "Margem": margem_texto, "Status": status_inicial
                    }
                    st.session_state.pedidos = pd.concat([st.session_state.pedidos, pd.DataFrame([nova_enc])], ignore_index=True)
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
                    novo_lote = {
                        "Produto": produto, "Local de Venda": local, "Quantidade Enviada": qtd_enviada, 
                        "Quantidade Vendida": qtd_vendida, "Peso Unit. (g)": peso_unit, 
                        "Custo Unit. (R$)": round(custo_u, 2), "Preço Unit. Venda (R$)": round(preco_loja, 2)
                    }
                    st.session_state.varejo = pd.concat([st.session_state.varejo, pd.DataFrame([novo_lote])], ignore_index=True)
                    st.rerun()

    with col_tab2:
        st.write("### 📊 Relatório de Itens em Lojas Externas")
        if not df_varejo.empty:
            df_varejo_exibicao = df_varejo.copy()
