"""Testes. Rodar: python -m unittest -v

As quatro regras do `Contrato` valem para QUALQUER método de análise. O método correto passa nas
quatro. O ingênuo (agrupa por nome) falha nas quatro; aqui ele está marcado como `expectedFailure`
para a suíte inteira ficar verde e, ao mesmo tempo, provar que os testes pegam o erro.
Para ver as falhas de verdade:   VER_FALHAS=1 python -m unittest -v

Os números de ESPERADO foram conferidos fora do código (awk sobre o CSV), não saíram do analise_correta.
"""
import json
import os
import re
import unittest
from decimal import Decimal
from pathlib import Path

import analise_correta
import analise_ingenua
import gerar_dados
import gerar_dashboard
from util import carregar

# total-alvo de cada obra (igual a OBRAS em gerar_dados.py), conferido com awk sobre dados/lancamentos.csv
ESPERADO = {1: "118640.00", 2: "96250.00", 3: "47380.00", 4: "133900.00", 5: "64720.00",
            6: "21150.00", 7: "83290.00", 8: "58410.00", 9: "39870.00", 10: "72560.00"}
TOTAL_GERAL = Decimal("740040.00")  # 736170.00 das obras + 3870.00 de lançamentos sem obra

def deve_falhar(teste):
    # copia a função: expectedFailure marca o objeto-função, e sem a cópia marcaria o teste do método correto também
    copia = lambda self: teste(self)
    copia.__name__ = teste.__name__
    return copia if os.environ.get("VER_FALHAS") else unittest.expectedFailure(copia)


class Contrato:
    metodo = None  # módulo com totais_por_obra(obras, lancamentos)

    @classmethod
    def setUpClass(cls):
        cls.obras, cls.lancamentos = carregar()
        cls.linhas = cls.metodo.totais_por_obra(cls.obras, cls.lancamentos)

    def test_uma_linha_por_obra_cadastrada(self):
        linhas_de_obra = [r for r in self.linhas if not r.get("orfao")]
        self.assertEqual(len(linhas_de_obra), len(self.obras))

    def test_obras_de_mesmo_nome_ficam_separadas(self):
        aurora = [r["total"] for r in self.linhas if r["nome"] == "Residencial Aurora"]
        self.assertEqual(sorted(aurora), [Decimal("83290.00"), Decimal("118640.00")])

    def test_total_de_cada_obra_bate_com_a_conta_na_mao(self):
        por_id = {r["obra_id"]: r["total"] for r in self.linhas if r["obra_id"] is not None}
        self.assertEqual(por_id, {i: Decimal(v) for i, v in ESPERADO.items()})

    def test_soma_das_partes_fecha_com_o_total_geral(self):
        self.assertEqual(sum(r["total"] for r in self.linhas), TOTAL_GERAL)


class TestMetodoCorreto(Contrato, unittest.TestCase):
    metodo = analise_correta


class TestMetodoIngenuo(Contrato, unittest.TestCase):
    metodo = analise_ingenua

    test_uma_linha_por_obra_cadastrada = deve_falhar(Contrato.test_uma_linha_por_obra_cadastrada)
    test_obras_de_mesmo_nome_ficam_separadas = deve_falhar(Contrato.test_obras_de_mesmo_nome_ficam_separadas)
    test_total_de_cada_obra_bate_com_a_conta_na_mao = deve_falhar(Contrato.test_total_de_cada_obra_bate_com_a_conta_na_mao)
    test_soma_das_partes_fecha_com_o_total_geral = deve_falhar(Contrato.test_soma_das_partes_fecha_com_o_total_geral)


class TestConferencia(unittest.TestCase):
    """O que analise_correta.conferir() acusa, e quando recusa o resultado."""

    @classmethod
    def setUpClass(cls):
        cls.obras, cls.lancamentos = carregar()
        cls.linhas = analise_correta.totais_por_obra(cls.obras, cls.lancamentos)
        cls.relatorio = analise_correta.conferir(cls.obras, cls.lancamentos, cls.linhas)

    def test_total_geral_confere_com_a_conta_na_mao(self):
        self.assertEqual(self.relatorio["total_geral"], TOTAL_GERAL)

    def test_acusa_lancamentos_sem_obra(self):
        self.assertEqual(self.relatorio["orfaos"], {"quantidade": 2, "total": Decimal("3870.00"), "obra_ids": [99]})

    def test_acusa_nomes_repetidos(self):
        self.assertEqual(self.relatorio["nomes_repetidos"], [
            {"nome": "Residencial Aurora", "obra_ids": [1, 7]},
            {"nome": "Edifício Horizonte", "obra_ids": [2, 8]},
        ])

    def test_acusa_nomes_que_so_diferem_no_acento(self):
        self.assertEqual(self.relatorio["nomes_parecidos"], [
            {"nomes": ["Condominio Jardim Sul", "Condomínio Jardim Sul"], "obra_ids": [4, 9]},
        ])

    def test_recusa_resultado_ingenuo(self):
        ingenuo = analise_ingenua.totais_por_obra(self.obras, self.lancamentos)
        with self.assertRaises(analise_correta.ErroDeConciliacao):
            analise_correta.conferir(self.obras, self.lancamentos, ingenuo)

    def test_recusa_linha_que_sumiu(self):
        sem_uma = [r for r in self.linhas if r["obra_id"] != 7]
        with self.assertRaisesRegex(analise_correta.ErroDeConciliacao, "soma das partes"):
            analise_correta.conferir(self.obras, self.lancamentos, sem_uma)

    def test_recusa_obras_juntadas_mesmo_com_a_soma_certa(self):
        # o caso perigoso: juntar as duas Auroras NÃO muda a soma. Só a contagem de linhas pega.
        a, b = (r for r in self.linhas if r["obra_id"] in (1, 7))
        juntada = {**a, "total": a["total"] + b["total"], "lancamentos": a["lancamentos"] + b["lancamentos"]}
        resto = [r for r in self.linhas if r["obra_id"] not in (1, 7)]
        self.assertEqual(sum(r["total"] for r in resto + [juntada]), TOTAL_GERAL)
        with self.assertRaisesRegex(analise_correta.ErroDeConciliacao, "9 linhas para 10 obras"):
            analise_correta.conferir(self.obras, self.lancamentos, resto + [juntada])

    def test_recusa_obra_id_repetido_no_cadastro(self):
        with self.assertRaisesRegex(analise_correta.ErroDeConciliacao, "obra_id repetido"):
            analise_correta.conferir(self.obras + [self.obras[0]], self.lancamentos, self.linhas)


class TestDadosEDashboard(unittest.TestCase):
    def test_gerador_e_deterministico(self):
        self.assertEqual(gerar_dados.gerar(), gerar_dados.gerar())

    def test_csvs_do_repositorio_sao_os_que_o_gerador_produz(self):
        self.assertEqual(carregar(), gerar_dados.gerar())

    def test_dashboard_html_embute_o_json_atual(self):
        html = Path(gerar_dashboard.SAIDA).read_text(encoding="utf-8")
        embutido = re.search(r'<script id="dados" type="application/json">(.*?)</script>', html, re.S).group(1)
        self.assertEqual(json.loads(embutido), gerar_dashboard.montar())

    def test_dashboard_nao_depende_de_rede(self):
        html = Path(gerar_dashboard.SAIDA).read_text(encoding="utf-8")
        self.assertNotRegex(html, r'''(src|href)\s*=\s*["']?(https?:)?//|@import|url\(\s*["']?https?:|fetch\(|XMLHttpRequest''')


if __name__ == "__main__":
    unittest.main()
