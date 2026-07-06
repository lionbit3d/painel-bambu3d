import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página da Dashboard
st.set_page_config(page_title="Controle de Impressão 3D - Bambu Lab A1", layout="wide")

st.title("📊 Painel de Controle de Manufatura 3D")
st.subheader("Gerenciamento de Pedidos, Custos e Lucros por Gramatura")

# 📥 BANCO DE DADOS EM MEMÓRIA (Estrutura inicial com as novas colunas)
if 'pedidos' not in st.session_state:
    st.session_state.pedidos = pd.DataFrame([
        {
            "Cliente": "João Silva", 
            "Data": "2026-07-06", 
            "Tipo de Projeto": "Suporte de Celular", 
            "Peso (g)": 58.0, 
            "Custo (R$)": 8.70, 
            "Preço Venda (R$)": 34.80, 
            "Margem Selecionada": "400%",
            "Status": "Concluído"
        }
    ])

# 📈 ÁREA DE MÉTRICAS GLOBAIS (Cálculos Automáticos)
df = st.session_state.pedidos

# Garante que as colunas numéricas estão com o formato correto antes de somar
if not df.empty:
    df["Custo (R$)"] = df["Peso (g)"] * 0.15
    df["Lucro (R$)"] = df["Preço Venda (R$)"] - df["Custo (R$)"]
    
    total_pedidos = len(df)
    custo_total = df["Custo (R$)"].sum()
    faturamento_total = df["Preço Venda (R$)"].sum()
    lucro_total = df["Lucro (R$)"].sum()
else:
    total_pedidos = 0
    custo_total = 0.0
    faturamento_total = 0.0
    lucro_total = 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("📦 Total de Pedidos", total_pedidos)
col2.metric("📉 Custo Total de Filamento", f"R$ {custo_total:.2f}")
col3.metric("💰 Faturamento Bruto", f"R$ {faturamento_total:.2f}")
col4.metric("🔥 Lucro Líquido Real", f"R$ {lucro_total:.2f}")

st.markdown("---")

# ➕ FORMULÁRIO LATERAL DE CADASTRO COM REGRAS MATEMÁTICAS
st.sidebar.header("➕ Cadastrar Novo Pedido")
with st.sidebar.form("novo_pedido_form", clear_on_submit=True):
    cliente = st.text_input("Nome do Cliente")
    
    # Campo de data padrão com o dia de hoje
    data_solicitacao = st.date_input("Data de Solicitação", datetime.now())
    
    # Lista suspensa com tipos de projeto sugeridos
    lista_projetos = [
        "Suporte de Celular", 
        "Letreiro de Quarto", 
        "Boneco Articulado", 
        "Boneco Decorativo", 
        "Chaveiro", 
        "Utilitário", 
        "Utensílio Doméstico",
        "Peça Técnica / Reposição",
        "Vaso / Decoração Paramétrica",
        "Litofania (Foto 3D)",
        "Organizador de Mesa"
    ]
    tipo_projeto = st.selectbox("Tipo de Projeto", lista_projetos)
    
    # Entrada de peso em gramas
    peso_gramas = st.number_input("Peso em Gramas (g)", min_value=0.0, step=1.0, help="Verifique o peso estimado no Bambu Studio")
    
    # Opções selecionáveis de margem conforme pedido
    opcoes_margem = {"250%": 2.5, "300%": 3.0, "350%": 3.5, "400%": 4.0}
    margem_texto = st.selectbox("Margem de Venda (Multiplicador)", list(opcoes_margem.keys()), index=1)
    
    status_inicial = st.selectbox("Status Inicial", ["Pendente", "Imprimindo", "Concluído"])
    
    botao_salvar = st.form_submit_button("Calcular e Salvar no Sistema")
    
    if botao_salvar and cliente and peso_gramas > 0:
        # Fórmulas matemáticas exatas solicitadas
        custo_calculado = peso_gramas * 0.15
        fator_multiplicador = opcoes_margem[margem_texto]
        preco_venda_calculado = custo_calculado * fator_multiplicador
        
        # Monta a nova linha do banco de dados
        novo_pedido = {
            "Cliente": cliente,
            "Data": str(data_solicitacao),
            "Tipo de Projeto": tipo_projeto,
            "Peso (g)": peso_gramas,
            "Custo (R$)": round(custo_calculado, 2),
            "Preço Venda (R$)": round(preco_venda_calculado, 2),
            "Margem Selecionada": margem_texto,
            "Status": status_inicial
        }
        
        st.session_state.pedidos = pd.concat([st.session_state.pedidos, pd.DataFrame([novo_pedido])], ignore_index=True)
        st.success("✅ Pedido calculado e salvo com sucesso!")
        st.rerun()

# 📋 EXIBIÇÃO DA TABELA DE PEDIDOS ATUAIS
st.subheader("📋 Lista de Pedidos e Fluxo de Caixa")

# Filtro rápido por Status no topo da tabela
filtro_status = st.multiselect("Filtrar visualização por Status:", ["Pendente", "Imprimindo", "Concluído"], default=["Pendente", "Imprimindo", "Concluído"])
df_filtrado = df[df["Status"].isin(filtro_status)]

# Exibe a tabela formatada de forma profissional na tela
st.dataframe(df_filtrado, use_container_width=True)
