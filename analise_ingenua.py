"""A análise ERRADA, de propósito: agrupa por NOME da obra.

É o equivalente a um   SELECT o.nome, SUM(l.valor) FROM lancamentos l JOIN obras o ON o.obra_id = l.obra_id
                         GROUP BY o.nome
que parece certo, roda sem erro e devolve números plausíveis. É a forma típica desse erro, escrita
aqui para a reprodução (a consulta real eu não tenho). Não use isto; está aqui para os testes e o
dashboard mostrarem o erro.
"""
from collections import defaultdict
from decimal import Decimal

from util import brl, carregar


def totais_por_obra(obras, lancamentos):
    nome_de = {o["obra_id"]: o["nome"] for o in obras}
    soma = defaultdict(Decimal)
    qtd = defaultdict(int)
    for l in lancamentos:
        if l["obra_id"] in nome_de:  # JOIN comum (INNER): lançamento sem obra some em silêncio
            soma[nome_de[l["obra_id"]]] += l["valor"]
            qtd[nome_de[l["obra_id"]]] += 1
    linhas = [{"obra_id": None, "nome": n, "total": t, "lancamentos": qtd[n]} for n, t in soma.items()]
    return sorted(linhas, key=lambda r: -r["total"])  # obra_id None: agrupar por nome joga o id fora


def main():
    obras, lancamentos = carregar()
    linhas = totais_por_obra(obras, lancamentos)
    print("ANÁLISE INGÊNUA (agrupa por nome) - não confie nestes números\n")
    for r in linhas:
        print(f"  {r['nome']:<24} {brl(r['total']):>16}   ({r['lancamentos']} lançamentos)")
    print(f"\n  linhas: {len(linhas)} | obras cadastradas: {len(obras)}")
    print(f"  soma das linhas: {brl(sum(r['total'] for r in linhas))}")
    print(f"  soma de todos os lançamentos: {brl(sum(l['valor'] for l in lancamentos))}")


if __name__ == "__main__":
    main()
