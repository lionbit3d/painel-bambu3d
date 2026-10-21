import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from modules.catalogo_filamentos import CATALOGOS_POR_MARCA, CORES_POR_TIPO_3DLAB
from modules.filamentos import COLUNAS, preparar_lote, resumir_estoque


class CatalogoFilamentosTest(unittest.TestCase):
    def test_voolt_somente_pla_petg(self):
        catalogo = CATALOGOS_POR_MARCA["Voolt3D"]
        self.assertEqual(len(catalogo), 17)
        self.assertTrue(all(tipo.startswith(("PLA ", "PETG ")) for tipo in catalogo))
        self.assertEqual(catalogo["PLA Velvet"][0], "Amarelo")
        self.assertIn("Natural Translúcido", catalogo["PETG HF"])

    def test_3dlab_linhas_pla_com_cores_proprias(self):
        self.assertEqual(list(CORES_POR_TIPO_3DLAB), [
            "PLA Premium", "PLA Candy Colors", "PLA Cetim", "PLA Hyper",
            "PLA Rainbow", "PLA Silk", "PLA Ultra Silk",
        ])
        self.assertEqual(sum(map(len, CORES_POR_TIPO_3DLAB.values())), 75)
        self.assertNotIn("PLA Velvet", CORES_POR_TIPO_3DLAB)
        self.assertIn("Branco Polar", CORES_POR_TIPO_3DLAB["PLA Hyper"])
        self.assertNotIn("Branco Polar", CORES_POR_TIPO_3DLAB["PLA Candy Colors"])
        for catalogo in CATALOGOS_POR_MARCA.values():
            for cores in catalogo.values():
                self.assertTrue(cores)
                self.assertEqual(len(cores), len(set(cores)))

    def test_lote_3dlab_mantem_pesos_e_quantidade(self):
        lote = preparar_lote("3DLAB", "PLA Hyper", "Branco Polar", 2, "Aberto", 1000, 650)
        self.assertEqual(len(lote), 2)
        self.assertIsNot(lote[0], lote[1])
        self.assertEqual(lote[0]["material"], "PLA Hyper")
        self.assertEqual(lote[0]["peso_atual_g"], 650)

    def test_novos_lotes_rejeitam_material_ou_cor_de_outra_marca(self):
        for marca, tipo, cor in [
            ("Voolt3D", "ABS", "Preto"),
            ("Voolt3D", "PCTG", "Natural"),
            ("Voolt3D", "PLA Premium", "Preto Eclipse"),
            ("3DLAB", "PETG", "Preto"),
            ("3DLAB", "PLA Velvet", "Preto"),
            ("3DLAB", "PLA Hyper", "Caramelo Soft"),
        ]:
            with self.subTest(marca=marca, tipo=tipo, cor=cor), self.assertRaises(ValueError):
                preparar_lote(marca, tipo, cor, 1, "Fechado", 1000, 1000)

    def test_outros_preserva_cadastro_livre(self):
        lote = preparar_lote("Outros", "PLA personalizado", "Cor personalizada", 1, "Fechado", 1000, 500)
        self.assertEqual(lote[0]["peso_atual_g"], 1000)

    def test_resumo_nao_remove_rolos_antigos(self):
        registros = pd.DataFrame([
            {"marca": "Voolt3D", "material": "ABS", "cor_nome": "Preto", "status": "Aberto"},
            {"marca": "3DLAB", "material": "PETG", "cor_nome": "Azul", "status": "Fechado"},
        ])
        resumo = resumir_estoque(registros)
        self.assertEqual(int(resumo["Qtde"].sum()), 2)
        self.assertEqual(set(resumo["Tipo"]), {"ABS", "PETG"})


class CatalogoInterfaceTest(unittest.TestCase):
    def setUp(self):
        self.no_network = patch("requests.sessions.Session.request", side_effect=AssertionError("Rede proibida no teste"))
        self.no_network.start()
        self.addCleanup(self.no_network.stop)
        self.at = AppTest.from_string(
            'from modules.filamentos import render_estoque_filamentos\n'
            'render_estoque_filamentos("https://example.invalid", {})\n',
            default_timeout=15,
        )

    def run_app(self):
        with patch("modules.filamentos.carregar_estoque", return_value=(pd.DataFrame(columns=COLUNAS), "")):
            self.at.run()
        self.assertEqual(len(self.at.exception), 0)

    def selectbox(self, label):
        return next(widget for widget in self.at.selectbox if widget.label == label)

    def test_troca_de_marca_e_tipo_filtra_cores(self):
        self.run_app()
        self.assertNotIn("ABS", self.selectbox("Tipo").options)
        self.selectbox("Marca").select("3DLAB")
        self.run_app()
        self.assertEqual(self.selectbox("Tipo").options, list(CORES_POR_TIPO_3DLAB))
        for tipo, cores in CORES_POR_TIPO_3DLAB.items():
            self.selectbox("Tipo").select(tipo)
            self.run_app()
            self.assertEqual(self.selectbox("Cor").options, cores)
        self.selectbox("Marca").select("Voolt3D")
        self.run_app()
        self.assertIn("PETG HF", self.selectbox("Tipo").options)
        self.assertNotIn("PLA Hyper", self.selectbox("Tipo").options)
        self.selectbox("Tipo").select("PETG HF")
        self.run_app()
        self.assertIn("Natural Translúcido", self.selectbox("Cor").options)

    def test_cadastro_passa_marca_tipo_e_cor_selecionados(self):
        self.run_app()
        self.selectbox("Marca").select("3DLAB")
        self.run_app()
        self.selectbox("Tipo").select("PLA Candy Colors")
        self.run_app()
        self.selectbox("Cor").select("Verde Menta")
        next(w for w in self.at.number_input if w.label == "Qtde (rolos)").set_value(2)
        next(w for w in self.at.button if w.label == "Cadastrar filamentos").click()
        with patch("modules.filamentos.salvar_lote", return_value=True) as salvar:
            self.run_app()
        salvar.assert_called_once()
        lote = salvar.call_args.args[2]
        self.assertEqual(len(lote), 2)
        self.assertEqual(lote[0]["marca"], "3DLAB")
        self.assertEqual(lote[0]["material"], "PLA Candy Colors")
        self.assertEqual(lote[0]["cor_nome"], "Verde Menta")


if __name__ == "__main__":
    unittest.main()
