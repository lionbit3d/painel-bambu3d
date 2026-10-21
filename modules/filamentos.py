"""Cadastro e consulta de rolos no estoque compartilhado com a Bambu Lab."""

import math
import re

import pandas as pd
import requests
import streamlit as st

from modules.catalogo_filamentos import CATALOGOS_POR_MARCA, CORES_POR_TIPO, ESTADOS, MARCAS


COLUNAS = [
    "id", "marca", "material", "cor_nome", "cor_hex", "status",
    "peso_inicial_g", "peso_atual_g", "observacao",
]


def carregar_estoque(url, headers):
    registros = []
    try:
        while True:
            response = requests.get(
                f"{url.rstrip('/')}/rest/v1/filamentos_estoque",
                headers=headers,
                params={
                    "select": ",".join(COLUNAS), "order": "id.desc",
                    "offset": len(registros), "limit": 1000,
                },
                timeout=20,
            )
            response.raise_for_status()
            pagina = response.json()
            if not pagina:
                break
            registros.extend(pagina)
        return pd.DataFrame(registros, columns=COLUNAS), ""
    except (requests.RequestException, ValueError):
        return pd.DataFrame(columns=COLUNAS), "Não foi possível carregar o estoque de filamentos."


def preparar_lote(marca, tipo, cor, quantidade, estado, peso, peso_atual, cor_hex="", observacao=""):
    quantidade_numero = float(quantidade)
    peso, peso_atual = float(peso), float(peso_atual)
    if estado == "Fechado":
        peso_atual = peso
    if not quantidade_numero.is_integer() or not 1 <= quantidade_numero <= 500:
        raise ValueError("Informe uma quantidade entre 1 e 500 rolos.")
    if not math.isfinite(peso) or not math.isfinite(peso_atual) or peso <= 0 or not 0 <= peso_atual <= peso:
        raise ValueError("O peso atual deve estar entre zero e o peso inicial do rolo.")
    if estado not in ESTADOS:
        raise ValueError("Selecione Fechado ou Aberto.")
    if marca not in MARCAS or not str(tipo or "").strip() or not str(cor or "").strip():
        raise ValueError("Preencha marca, tipo e cor.")
    catalogo = CATALOGOS_POR_MARCA.get(marca)
    if catalogo is not None and cor not in catalogo.get(tipo, []):
        raise ValueError("Selecione um tipo e uma cor do catálogo da marca.")
    cor_hex = str(cor_hex or "").strip().lstrip("#")
    if cor_hex and not re.fullmatch(r"[0-9a-fA-F]{6}([0-9a-fA-F]{2})?", cor_hex):
        raise ValueError("Informe a cor HEX com 6 ou 8 caracteres, ou deixe em branco.")
    payload = {
        "marca": marca, "material": str(tipo).strip(), "cor_nome": str(cor).strip(),
        "cor_hex": cor_hex.upper(), "status": estado,
        "peso_inicial_g": round(peso, 2),
        "peso_atual_g": round(peso if estado == "Fechado" else peso_atual, 2),
        "observacao": str(observacao or "").strip(),
    }
    return [payload.copy() for _ in range(int(quantidade_numero))]


def salvar_lote(url, headers, registros):
    try:
        response = requests.post(
            f"{url.rstrip('/')}/rest/v1/filamentos_estoque", headers=headers,
            json=registros, timeout=20,
        )
        response.raise_for_status()
        return True
    except (requests.RequestException, ValueError):
        return False


def resumir_estoque(estoque):
    resumo = estoque.copy()
    resumo["status"] = resumo["status"].fillna("Não informado").replace("Ativo", "Não informado")
    return (
        resumo.groupby(["marca", "material", "cor_nome", "status"], dropna=False)
        .size().reset_index(name="Qtde")
        .rename(columns={"marca": "Marca", "material": "Tipo", "cor_nome": "Cor", "status": "Estado"})
        [["Marca", "Tipo", "Cor", "Qtde", "Estado"]]
    )


def salvar_alteracoes(url, headers, original, editado):
    alterados = 0
    for _, row in editado.iterrows():
        registro = original[original["id"] == row["id"]]
        if registro.empty:
            return alterados, "Um dos rolos não foi encontrado. Atualize a página."
        antes = registro.iloc[0]
        campos = ["marca", "material", "cor_nome", "status", "peso_atual_g", "observacao"]
        if all(str(row[campo]) == str(antes[campo]) for campo in campos):
            continue
        try:
            peso_atual = float(row["peso_atual_g"])
            peso_inicial = float(antes["peso_inicial_g"])
            estado = str(row["status"])
            if not math.isfinite(peso_atual) or not 0 <= peso_atual <= peso_inicial:
                raise ValueError("O peso atual deve estar entre zero e o peso inicial.")
            if estado not in ESTADOS + [str(antes["status"])]:
                raise ValueError("Selecione Fechado ou Aberto.")
            if estado == "Fechado" and peso_atual < peso_inicial:
                estado = "Aberto"
            payload = {
                "marca": str(row["marca"]).strip(), "material": str(row["material"]).strip(),
                "cor_nome": str(row["cor_nome"]).strip(), "status": estado,
                "peso_atual_g": round(peso_atual, 2), "observacao": str(row["observacao"] or "").strip(),
            }
            if not payload["marca"] or not payload["material"] or not payload["cor_nome"]:
                raise ValueError("Preencha marca, tipo e cor dos rolos.")
            # O filtro evita sobrescrever uma baixa de consumo feita em outra sessao.
            response = requests.patch(
                f"{url.rstrip('/')}/rest/v1/filamentos_estoque",
                params={"id": f"eq.{int(row['id'])}", "peso_atual_g": f"eq.{antes['peso_atual_g']}"},
                headers={**headers, "Prefer": "return=representation"}, json=payload, timeout=20,
            )
            response.raise_for_status()
            if not response.json():
                return alterados, "O estoque mudou durante a edição. Atualize a página e tente novamente."
            alterados += 1
        except ValueError as exc:
            return alterados, str(exc)
        except requests.RequestException:
            return alterados, "Não foi possível salvar um dos rolos. Confira o estoque antes de tentar novamente."
    return alterados, ""


def render_estoque_filamentos(url, headers, key_prefix="estoque_filamentos"):
    st.markdown("<h2 style='color: #ffcc00;'>Estoque de Filamentos</h2>", unsafe_allow_html=True)
    aviso = st.session_state.pop(f"{key_prefix}_aviso", "")
    if aviso:
        st.success(aviso)
    estoque, erro = carregar_estoque(url, headers)
    if erro:
        st.error(erro)
        return
    col_cadastro, col_estoque = st.columns([1, 2.3], gap="small")
    with col_cadastro:
        st.subheader("Cadastrar filamento")
        marca = st.selectbox("Marca", MARCAS, key=f"{key_prefix}_marca")
        catalogo = CATALOGOS_POR_MARCA.get(marca, CORES_POR_TIPO)
        cadastro_livre = marca not in CATALOGOS_POR_MARCA
        tipos = list(catalogo)
        if cadastro_livre:
            tipos = ["PLA", "PETG"] + tipos
        tipo = st.selectbox(
            "Tipo", tipos, accept_new_options=cadastro_livre, key=f"{key_prefix}_tipo_{marca}",
        )
        cores = catalogo.get(tipo, sorted({cor for lista in catalogo.values() for cor in lista}))
        with st.form(f"{key_prefix}_cadastro", clear_on_submit=True):
            cor = st.selectbox(
                "Cor", cores, accept_new_options=cadastro_livre,
                key=f"{key_prefix}_cor_{marca}_{tipo}",
            )
            col_qtde, col_estado = st.columns(2)
            with col_qtde:
                quantidade = st.number_input("Qtde (rolos)", min_value=1, max_value=500, value=1, step=1)
            with col_estado:
                estado = st.selectbox("Estado", ESTADOS)
            col_inicial, col_atual = st.columns(2)
            with col_inicial:
                peso = st.number_input("Peso inicial/rolo (g)", min_value=1.0, value=1000.0, step=50.0)
            with col_atual:
                peso_atual = st.number_input("Peso atual/rolo (g)", min_value=0.0, value=1000.0, step=50.0)
            with st.expander("Dados adicionais"):
                cor_hex = st.text_input("Cor HEX", placeholder="Ex: FF0000")
                observacao = st.text_input("Observação")
            if st.form_submit_button("Cadastrar filamentos", icon=":material/add:", width="stretch"):
                try:
                    lote = preparar_lote(marca, tipo, cor, quantidade, estado, peso, peso_atual, cor_hex, observacao)
                except ValueError as exc:
                    st.warning(str(exc))
                else:
                    if salvar_lote(url, headers, lote):
                        st.session_state[f"{key_prefix}_aviso"] = f"{quantidade} rolo(s) cadastrado(s)."
                        st.rerun()
                    else:
                        st.error("Não foi possível confirmar o cadastro. Confira a lista antes de tentar novamente.")
    with col_estoque:
        st.subheader("Estoque cadastrado")
        total, fechados, abertos = st.columns(3)
        total.metric("Total de rolos", len(estoque))
        fechados.metric("Fechados", int((estoque["status"] == "Fechado").sum()))
        abertos.metric("Abertos", int((estoque["status"] == "Aberto").sum()))
        if estoque.empty:
            st.info("Nenhum rolo cadastrado ainda.")
            return
        st.dataframe(resumir_estoque(estoque), hide_index=True, width="stretch")
        with st.expander("Editar rolos", expanded=False):
            original = estoque.fillna("")
            marcas = list(dict.fromkeys(MARCAS + original["marca"].tolist()))
            estados = list(dict.fromkeys(ESTADOS + original["status"].tolist()))
            editado = st.data_editor(
                original,
                column_order=["id", "marca", "material", "cor_nome", "status", "peso_atual_g", "observacao"],
                column_config={
                    "id": st.column_config.NumberColumn("Rolo", width="small"),
                    "marca": st.column_config.SelectboxColumn("Marca", options=marcas, required=True),
                    "material": st.column_config.TextColumn("Tipo", required=True),
                    "cor_nome": st.column_config.TextColumn("Cor", required=True),
                    "status": st.column_config.SelectboxColumn("Estado", options=estados, required=True),
                    "peso_atual_g": st.column_config.NumberColumn("Peso atual (g)", min_value=0.0, step=1.0, required=True),
                    "observacao": st.column_config.TextColumn("Observação"),
                    "cor_hex": None, "peso_inicial_g": None,
                },
                disabled=["id", "peso_inicial_g", "cor_hex"], hide_index=True,
                width="stretch", key=f"{key_prefix}_editor",
            )
            if st.button("Salvar alterações", icon=":material/save:", key=f"{key_prefix}_salvar"):
                quantidade_salva, erro = salvar_alteracoes(url, headers, original, editado)
                if erro:
                    st.error(erro)
                elif quantidade_salva:
                    st.session_state[f"{key_prefix}_aviso"] = f"{quantidade_salva} rolo(s) atualizado(s)."
                    st.rerun()
                else:
                    st.info("Nenhuma alteração para salvar.")
