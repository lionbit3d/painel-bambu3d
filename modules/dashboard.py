import streamlit as st

from config import URL_SUA_LOGO


def render_header():
    col_logo, col_titulo = st.columns(2)
    with col_logo:
        try:
            st.image(URL_SUA_LOGO, width=120)
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
    df_varejo["Total Faturamento Real"] = (
        df_varejo["Quantidade Vendida"] * df_varejo["Preço Unit. Venda (R$)"]
    )
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
    col2.metric("📉 Custo Total de Material", f"R$ {custo_global:.2f}")
    col3.metric("💰 Faturamento Bruto", f"R$ {faturamento_global:.2f}")
    col4.metric("🔥 Lucro Líquido Geral", f"R$ {lucro_global:.2f}")


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
    st.dataframe(desempenho, use_container_width=True)
