SUPABASE_URL = "https://ntybsaywkdmqcjhslehw.supabase.co/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50eWJzYXl3a2RtcWNqaHNsZWh3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMzNTQwMjgsImV4cCI6MjA5ODkzMDAyOH0.0pV_Lu60COGdjBCuVVSmqf2TNqH3I_0xlLSeJckenzA"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

PAGE_TITLE = "LionBit 3D Studio - Painel de Controle"
PAGE_LAYOUT = "wide"
URL_SUA_LOGO = "logo.png"

PEDIDOS_COLUMNS = [
    "id",
    "Cliente",
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

PEDIDOS_RENAME_COLUMNS = {
    "data_solicitacao": "Data",
    "tipo_projeto": "Tipo de Projeto",
    "peso_g": "Peso (g)",
    "custo_rs": "Custo (R$)",
    "preco_venda_rs": "Preço Venda (R$)",
    "margem": "Margem",
    "status": "Status",
}

VAREJO_RENAME_COLUMNS = {
    "produto": "Produto",
    "local_venda": "Local de Venda",
    "qtd_enviada": "Quantidade Enviada",
    "qtd_vendida": "Quantidade Vendida",
    "peso_unit_g": "Peso Unit. (g)",
    "custo_unit_rs": "Custo Unit. (R$)",
    "preco_unit_venda_rs": "Preço Unit. Venda (R$)",
}

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
