from datetime import datetime

import streamlit as st

from config import LISTA_PROJETOS, OPCOES_MARGEM, STATUS_OPTIONS
from database import create_encomenda, update_encomenda_status


def render_encomendas(df_pedidos):
    st.markdown("<h2 style='color: #ffcc00;'>📋 Gestão de Encomendas Ativas</h2>", unsafe_allow_html=True)
    col_form, col_tab = st.columns([1, 2])

    with col_form:
        st.write("### ➕ Nova Encomenda")
        with st.form("form_encomenda", clear_on_submit=True):
            cliente = st.text_input("Nome do Cliente")
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
                        "data_solicitacao": data_br,
                        "tipo_projeto": tipo_projeto,
                        "peso_g": peso_gramas,
                        "custo_rs": round(custo_calc, 2),
                        "preco_venda_rs": round(preco_calc, 2),
                        "margem": margem_texto,
                        "status": status_inicial,
                    }
                    create_encomenda(payload)
                    st.success("Salvo no banco de dados!")
                    st.rerun()

    with col_tab:
        st.write("### 🔍 Cronograma Prontuário")
        filtro_status = st.multiselect(
            "Filtrar por Status:",
            STATUS_OPTIONS,
            default=["Pendente", "Imprimindo"],
        )
        df_pedidos_filtrado = (
            df_pedidos[df_pedidos["Status"].isin(filtro_status)]
            if not df_pedidos.empty
            else df_pedidos
        )

        if not df_pedidos_filtrado.empty:
            tabela_editavel = st.data_editor(
                df_pedidos_filtrado,
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
                    "Data",
                    "Tipo de Projeto",
                    "Peso (g)",
                    "Custo (R$)",
                    "Preço Venda (R$)",
                    "Margem",
                ],
                use_container_width=True,
            )
            _sync_status_changes(df_pedidos_filtrado, tabela_editavel)
        else:
            st.info("Nenhuma encomenda encontrada para os filtros selecionados.")


def _sync_status_changes(df_original, df_editado):
    if "id" not in df_original.columns or "id" not in df_editado.columns:
        return

    alterou_status = False
    for _, linha_editada in df_editado.iterrows():
        registro = df_original[df_original["id"] == linha_editada["id"]]
        if registro.empty:
            continue

        status_original = registro.iloc[0]["Status"]
        if linha_editada["Status"] != status_original:
            update_encomenda_status(linha_editada["id"], linha_editada["Status"])
            alterou_status = True

    if alterou_status:
        st.success("Status atualizado no banco de dados!")
        st.rerun()
