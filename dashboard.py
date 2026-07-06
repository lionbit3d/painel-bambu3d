import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página da Dashboard
st.set_page_config(page_title="LionBit 3D Studio - Painel de Controle", layout="wide")

# Topo Identificado com a sua Marca
st.title("🦁 LionBit 3D Studio")
st.subheader("Painel Integrado de Manufatura e Gestão de Vendas")

# 📥 BANCO DE DADOS EM MEMÓRIA (Estruturas Iniciais)
# 1. Banco de Encomendas (Sob Medida)
if 'pedidos' not in st.session_state:
    st.session_state.pedidos = pd.DataFrame([
        {
            "Cliente": "João Silva", 
            "Data": "06/07/2026", 
            "Tipo de Projeto": "Suporte de Celular", 
            "Peso (g)": 58.0, 
            "Custo (R$)": 8.70, 
            "Preço Venda (R$)": 34.80, 
            "Margem": "400%",
            "Status": "Concluído"
        }
    ])

# 2. Banco de Varejo / Comércio Consignado
if 'varejo' not in st.session_state:
    st.session_state.varejo = pd.DataFrame([
        {
            "Produto": "Chaveiro Stitch", 
            "Local de Venda": "Banca Central (Consignado)", 
            "Quantidade Enviada": 10, 
            "Quantidade Vendida": 4, 
            "Peso Unit. (g)": 12.0,
            "Custo Unit. (R$)": 1.80, 
            "Preço Unit. Venda (R$)": 10.00
        }
    ])

# ------------------------------------------------------------------------------
# 📈 ÁREA DE MÉTRICAS GLOBAIS (Soma o faturamento de Encomendas + Varejo)
# ------------------------------------------------------------------------------
df_pedidos = st.session_state.pedidos
df_varejo = st.session_state.varejo

# Cálculos Encomendas
custo_pedidos = df_pedidos["Custo (R$)"].sum() if not df_pedidos.empty else 0.0
faturamento_pedidos = df_pedidos["Preço Venda (R$)"].sum() if not df_pedidos.empty else 0.0

# Cálculos Varejo
if not df_varejo.empty:
    df_varejo["Total Custo Enviado"] = df_varejo["Quantidade Enviada"] * df_varejo["Custo Unit. (R$)"]
    df_varejo["Total Faturamento Real"] = df_varejo["Quantidade Vendida"] * df_varejo["Preço Unit. Venda (R$)"]
    custo_varejo = df_varejo["Total Custo Enviado"].sum()
    faturamento_varejo = df_varejo["Total Faturamento Real"].sum()
else:
    custo_varejo, faturamento_varejo = 0.0, 0.0

# Totais Consolidados
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
# 🗂️ CRIAÇÃO DAS ABAS DE NAVEGAÇÃO
# ------------------------------------------------------------------------------
aba_producao, aba_varejo = st.tabs(["🏭 Fluxo de Encomendas", "🏪 Estoque e Comércio Varejo"])

# --- ABA 1: FLUXO DE ENCOMENDAS ---
with aba_producao:
    st.subheader("📋 Gestão de Encomendas Ativas")
    
    # Formulário Lateral movido para dentro da aba de forma elegante
    col_form, col_tab = st.columns([1, 2])
    
    with col_form:
        st.write("### ➕ Nova Encomenda")
        with st.form("form_encomenda", clear_on_submit=True):
            cliente = st.text_input("Nome do Cliente")
            data_sel = st.date_input("Data de Solicitação", datetime.now())
            
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
                    
                    # Formata a data no estilo BR (DD/MM/AAAA)
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
    st.subheader("🏪 Produtos Deixados em Comércio / Pronta Entrega")
    
    col_form2, col_tab2 = st.columns([1, 2])
    
    with col_form2:
        st.write("### ➕ Cadastrar Lote no Varejo")
        with st.form("form_varejo", clear_on_submit=True):
            produto = st.text_input("Nome do Produto (Ex: Vaso Espiral)")
            local = st.text_input("Local / Loja Parceira")
            qtd_enviada = st.number_input("Qtd Enviada (Estoque)", min_value=1, step=1)
            qtd_vendida = st.number_input("Qtd Já Vendida", min_value=0, max_value=int(qtd_enviada if qtd_enviada > 0 else 1), step=1)
            peso_unit = st.number_input("Peso Unitário (g)", min_value=0.0, step=1.0)
            preco_loja = st.number_input("Preço de Venda Final (R$)", min_value=0.0, step=1.0)
            
            if st.form_submit_button("Registrar no Varejo"):
                if produto and local and peso_unit > 0:
                    custo_u = peso_unit * 0.15
                    novo_lote = {
                        "Produto": produto, "Local de Venda": local, 
                        "Quantidade Enviada": qtd_enviada, "Quantidade Vendida": qtd_vendida, 
                        "Peso Unit. (g)": peso_unit, "Custo Unit. (R$)": round(custo_u, 2), 
                        "Preço Unit. Venda (R$)": round(preco_loja, 2)
                    }
                    st.session_state.varejo = pd.concat([st.session_state.varejo, pd.DataFrame([novo_lote])], ignore_index=True)
                    st.rerun()

    with col_tab2:
        st.write("### 📊 Relatório de Itens Consignados / Pronta Entrega")
        if not df_varejo.empty:
            # Mostra a tabela de varejo detalhando o estoque restante
            df_varejo_exibicao = df_varejo.copy()
            df_varejo_exibicao["Estoque Restante"] = df_varejo_exibicao["Quantidade Enviada"] - df_varejo_exibicao["Quantidade Vendida"]
            st.dataframe(df_varejo_exibicao[["Produto", "Local de Venda", "Quantidade Enviada", "Quantidade Vendida", "Estoque Restante", "Custo Unit. (R$)", "Preço Unit. Venda (R$)"]], use_container_width=True)
        else:
            st.info("Nenhum produto em comércio cadastrado ainda.")
