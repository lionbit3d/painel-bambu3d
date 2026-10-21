"""Catalogos oficiais consultados em 21/10/2026, limitados aos materiais usados."""

CATALOGO_URL = "https://www.voolt3d.com.br/produtos/"
CATALOGO_3DLAB_URL = "https://3dlab.com.br/categoria-produto/filamento-para-impressora-3d/"
MARCAS = ["Voolt3D", "3DLAB", "Outros"]
ESTADOS = ["Fechado", "Aberto"]

CORES_POR_TIPO = {
    "PLA Sólido": [
        "Amarelo", "Azul", "Azul Cyan", "Bege Caucasiano", "Branco Dental",
        "Cinza Claro", "Cinza Grafite", "Laranja", "Marrom", "Marrom Cappuccino",
        "Marrom Caramelo", "Preto", "Rosa", "Rosa Bebê", "Rosa Púrpura", "Roxo",
        "Verde", "Verde Tiffany", "Vermelho", "Vermelho Marsala",
    ],
    "PLA Velvet": [
        "Amarelo", "Amarelo Macaron", "Azul", "Azul Macaron", "Bege Caucasiano",
        "Branco", "Branco Off White", "Cinza Claro", "Cinza Grafite", "Fóssil",
        "Laranja Macaron", "Lilás Macaron", "Marrom", "Marrom Cappuccino", "Preto",
        "Rosa Bebê", "Verde", "Verde Macaron", "Verde Oliva", "Vermelho", "Vermelho Macaron",
    ],
    "PLA V-Silk": [
        "Alumínio", "Amarelo", "Azul Bebê", "Azul Metalizado", "Azul Safira",
        "Azul Sky", "Azul Titanium", "Branco Pérola", "Bronze", "Champagne",
        "Cobre", "Dourado", "Dourado Ultra", "Inox", "Laranja", "Lilás", "Preto",
        "Rosa", "Rosa Ametista", "Rosa Choque", "Rosa Salmão Neon", "Rose Gold",
        "Verde", "Verde Bebê", "Verde Neon", "Vermelho",
    ],
    "PLA Duo Color Shadow V-Silk": [
        "Azul com Preto", "Azul Safira com Ametista", "Dourado com Ametista",
        "Dourado com Preto", "Dourado com Verde", "Laranja com Preto",
        "Rosa com Preto", "Verde com Ametista", "Verde com Preto", "Vermelho com Preto",
    ],
    "PLA Tri Color V-Silk": [
        "Ametista / Azul Safira / Dourado", "Azul / Laranja / Verde Neon",
        "Azul Safira / Dourado / Verde", "Bronze / Prata / Ouro",
        "Dourado / Laranja / Rosa Choque", "Dourado / Rosa Choque / Verde",
    ],
    "PLA Evo": ["Branco Off White", "Preto"],
    "PLA Stone": ["Crema Marfil", "Gesso", "Grafite", "Marmorizado", "Verde Ardósia"],
    "PLA Wood": ["Carvão", "Pinus", "Tabaco"],
    "PLA Cosmos": ["Azul Netuno"],
    "PLA Fibra de Carbono": ["Não especificada"],
    "PLA Grafeno Velvet": ["Não especificada"],
    "PLA Grafeno Condutivo": ["Não especificada"],
    "PLA Outlet": ["Variada (Outlet)"],
    "PETG HF": [
        "Amarelo", "Amarelo Ouro Translúcido", "Azul", "Azul Marinho Translúcido",
        "Bege Caucasiano", "Branco Blackout", "Branco Dental", "Cinza Claro",
        "Cinza Grafite", "Laranja", "Laranja Neon Translúcido", "Laranja Translúcido",
        "Marrom", "Marrom Cappuccino", "Natural Translúcido", "Preto",
        "Rosa Cereja Neon Translúcido", "Roxo Translúcido", "Verde",
        "Verde Limão Translúcido", "Verde Neon Translúcido", "Verde Oliva",
        "Vermelho", "Vermelho Translúcido",
    ],
    "PETG Fibra de Carbono": ["Não especificada"],
    "PETG Grafeno": ["Não especificada"],
    "PETG Outlet": ["Variada (Outlet)"],
}

# As categorias Premium incluem sublinhas; cada cor fica apenas na sua linha.
CORES_POR_TIPO_3DLAB = {
    "PLA Premium": [
        "Amarelo Neon Highlighter", "Amarelo Solar", "Areia Duna", "Azul Céu",
        "Azul Horizonte", "Azul Petróleo", "Azul Tiffany", "Azul Vitral",
        "Bege Natural", "Branco Aurora", "Cinza Urbano", "Crystal Clear",
        "Galáxia Glitter", "Glow Reactor", "Laranja Energia", "Laranja Neon Signal",
        "Lilás Lavanda", "Marrom Terra", "Mármore Carrara", "Nude Skin",
        "Prata Alumínio", "Preto Eclipse", "Rosa Blush", "Rosa Fúcsia",
        "Rosa Pop Art", "Rosê Gold", "Roxo Cósmico", "Sem cor definida (Low Cost)",
        "Verde Abacate", "Verde Campo", "Verde Floresta", "Verde Jade",
        "Verde Musgo", "Verde Noturno", "Vermelho Pulse", "Vermelho Racer",
    ],
    "PLA Candy Colors": [
        "Azul Breeze", "Baunilha Cream", "Caramelo Soft", "Fendy",
        "Rosa Marshmallow", "Verde Menta",
    ],
    "PLA Cetim": ["Amarelo Cetim", "Azul Cetim", "Preto Cetim", "Vermelho Cetim"],
    "PLA Hyper": [
        "Amarelo Safety", "Azul Industrial", "Branco Polar", "Cinza Técnico",
        "Preto Carbono", "Verde Engineering", "Vermelho Alert",
    ],
    "PLA Rainbow": [
        "3D Geek Show (Edição limitada)", "Brasil", "Bymodela (Edição limitada)",
        "Cosplayers (Edição limitada)", "Experience", "Faixa Preta (Edição limitada)",
        "Hexa", "Hi-Tech (Edição limitada)", "Lollipop", "Sunset",
    ],
    "PLA Silk": [
        "Azul Meia-Noite", "Cobre Elemento", "Grafite Luxo", "Lavanda Serenity",
        "Marrom Cacau", "Ouro Imperial", "Prata Lunar", "Pérola Nacar",
        "Rosa Fúcsia", "Sem cor definida (Low Cost)",
    ],
    "PLA Ultra Silk": ["Marrom Café", "Oceano Azul"],
}

CATALOGOS_POR_MARCA = {
    "Voolt3D": CORES_POR_TIPO,
    "3DLAB": CORES_POR_TIPO_3DLAB,
}
