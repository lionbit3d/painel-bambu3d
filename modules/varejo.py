import streamlit as st

from database import create_varejo


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
                    create_varejo(payload)
                    st.success("Salvo no banco de dados!")
                    st.rerun()

    with col_tab2:
        st.write("### 📊 Relatório de Itens Consignados / Pronta Entrega")
        if not df_varejo.empty:
            df_varejo_exibicao = df_varejo.copy()
            df_varejo_exibicao["Estoque Restante"] = (
                df_varejo_exibicao["Quantidade Enviada"] - df_varejo_exibicao["Quantidade Vendida"]
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
