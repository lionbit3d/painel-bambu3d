import streamlit as st

from config import PAGE_LAYOUT, PAGE_TITLE
from database import load_pedidos, load_varejo
from modules.dashboard import (
    prepare_varejo_metrics,
    render_desempenho_lojas,
    render_global_metrics,
    render_header,
)
from modules.encomendas import render_encomendas
from modules.varejo import render_varejo
from styles import apply_design_premium


st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT)

apply_design_premium()
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
