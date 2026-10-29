"""Gera dashboard.html: um arquivo só, sem CDN, com os números embutidos como JSON.

    python gerar_dashboard.py

Os números vêm de analise_correta (por id) e analise_ingenua (por nome, só para mostrar o erro).
O JavaScript não calcula os totais por obra nem agrupa: só soma o que o Python entregou para refazer a conferência e mostrar percentuais.
"""
import json
from pathlib import Path

import analise_correta
import analise_ingenua
from util import carregar

AQUI = Path(__file__).parent
MODELO = AQUI / "dashboard_modelo.html"
SAIDA = AQUI / "dashboard.html"


def cent(valor):
    return int(valor * 100)


def montar():
    obras, lancamentos = carregar()
    por_id = analise_correta.totais_por_obra(obras, lancamentos)
    c = analise_correta.conferir(obras, lancamentos, por_id)  # se não fechar, o dashboard nem é gerado
    repetidos = {i for g in c["nomes_repetidos"] for i in g["obra_ids"]}
    ids_do_nome = {}
    for o in obras:
        ids_do_nome.setdefault(o["nome"], []).append(o["obra_id"])
    return json.loads(json.dumps({  # json.loads(dumps()) deixa só tipos de JSON (sem Decimal)
        "empresa": "Construtora Exemplo",
        "totalGeralCentavos": cent(c["total_geral"]),
        "porId": [
            {"obraId": r["obra_id"], "nome": r["nome"], "bairro": r["bairro"], "centavos": cent(r["total"]),
             "lancamentos": r["lancamentos"], "orfao": bool(r.get("orfao")), "nomeRepetido": r["obra_id"] in repetidos}
            for r in por_id
        ],
        "porNome": [
            {"nome": r["nome"], "centavos": cent(r["total"]), "lancamentos": r["lancamentos"],
             "obraIds": ids_do_nome[r["nome"]]}
            for r in analise_ingenua.totais_por_obra(obras, lancamentos)
        ],
        "conferencia": {
            "obrasCadastradas": c["obras_cadastradas"],
            "nomesDistintos": len({o["nome"] for o in obras}),
            "orfaos": {"quantidade": c["orfaos"]["quantidade"], "centavos": cent(c["orfaos"]["total"]),
                       "obraIds": c["orfaos"]["obra_ids"]},
            "nomesRepetidos": [{"nome": g["nome"], "obraIds": g["obra_ids"]} for g in c["nomes_repetidos"]],
            "nomesParecidos": [{"nomes": g["nomes"], "obraIds": g["obra_ids"]} for g in c["nomes_parecidos"]],
        },
    }))


def main():
    dados = json.dumps(montar(), ensure_ascii=False, indent=1).replace("</", "<\\/")
    SAIDA.write_text(MODELO.read_text(encoding="utf-8").replace("__DADOS__", dados), encoding="utf-8", newline="\n")
    print(f"{SAIDA.name}: {SAIDA.stat().st_size / 1024:.1f} KB, autocontido (sem CDN)")


if __name__ == "__main__":
    main()
