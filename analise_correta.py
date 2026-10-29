"""A análise CERTA: agrupa por ID e confere o resultado antes de mostrar.

    python analise_correta.py

Duas famílias de checagem:
  - bloqueiam (levantam ErroDeConciliacao): id de obra repetido no cadastro, soma das partes diferente
    do total geral, número de linhas diferente do número de obras cadastradas;
  - avisam (vão para o relatório): lançamentos sem obra, nomes repetidos, nomes parecidos.
"""
import sys
import unicodedata
from collections import defaultdict
from decimal import Decimal

from util import brl, carregar


class ErroDeConciliacao(Exception):
    """O resultado não fecha com os dados de origem. Não mostre esse resultado a ninguém."""


def totais_por_obra(obras, lancamentos):
    """Uma linha por obra_id. Lançamento sem obra no cadastro vai para uma linha própria, não some."""
    por_id = {o["obra_id"]: o for o in obras}
    soma, qtd, orfaos = defaultdict(Decimal), defaultdict(int), []
    for l in lancamentos:
        if l["obra_id"] in por_id:
            soma[l["obra_id"]] += l["valor"]
            qtd[l["obra_id"]] += 1
        else:
            orfaos.append(l)
    linhas = [{"obra_id": i, "nome": o["nome"], "bairro": o["bairro"], "total": soma[i], "lancamentos": qtd[i]}
              for i, o in por_id.items()]
    if orfaos:
        linhas.append({"obra_id": None, "orfao": True, "nome": "(sem obra no cadastro)", "bairro": "",
                       "total": sum((l["valor"] for l in orfaos), Decimal(0)), "lancamentos": len(orfaos)})
    return sorted(linhas, key=lambda r: -r["total"])


def normalizar(nome):
    """'  Condomínio  Jardim Sul ' -> 'condominio jardim sul' (sem acento, caixa baixa, espaço único)."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", nome) if not unicodedata.combining(c))
    return " ".join(sem_acento.casefold().split())


def _grupos(obras, chave):
    grupos = defaultdict(list)
    for o in obras:
        grupos[chave(o["nome"])].append(o)
    return [g for g in grupos.values() if len(g) > 1]


def conferir(obras, lancamentos, linhas):
    """Confere `linhas` contra os dados de origem. Levanta ErroDeConciliacao se não fechar."""
    ids = [o["obra_id"] for o in obras]
    if len(ids) != len(set(ids)):
        raise ErroDeConciliacao("obra_id repetido no cadastro: o id deixou de identificar a obra")

    total_geral = sum((l["valor"] for l in lancamentos), Decimal(0))
    soma_partes = sum((r["total"] for r in linhas), Decimal(0))
    if soma_partes != total_geral:
        raise ErroDeConciliacao(f"soma das partes {brl(soma_partes)} != total geral {brl(total_geral)}")

    linhas_de_obra = [r for r in linhas if not r.get("orfao")]
    if len(linhas_de_obra) != len(obras):
        raise ErroDeConciliacao(f"{len(linhas_de_obra)} linhas para {len(obras)} obras cadastradas "
                                "(obras de mesmo nome foram juntadas?)")

    conhecidos = set(ids)
    orfaos = [l for l in lancamentos if l["obra_id"] not in conhecidos]
    exatos = _grupos(obras, lambda n: n)
    parecidos = [g for g in _grupos(obras, normalizar) if len({o["nome"] for o in g}) > 1]
    return {
        "total_geral": total_geral,
        "soma_das_partes": soma_partes,
        "obras_cadastradas": len(obras),
        "orfaos": {"quantidade": len(orfaos), "total": sum((l["valor"] for l in orfaos), Decimal(0)),
                   "obra_ids": sorted({l["obra_id"] for l in orfaos})},
        "nomes_repetidos": [{"nome": g[0]["nome"], "obra_ids": [o["obra_id"] for o in g]} for g in exatos],
        "nomes_parecidos": [{"nomes": sorted({o["nome"] for o in g}), "obra_ids": [o["obra_id"] for o in g]}
                            for g in parecidos],
    }


def main():
    obras, lancamentos = carregar()
    linhas = totais_por_obra(obras, lancamentos)
    try:
        c = conferir(obras, lancamentos, linhas)
    except ErroDeConciliacao as e:
        print(f"CONFERÊNCIA FALHOU: {e}\nNenhum número é mostrado.")
        return 1
    print("ANÁLISE CORRETA (agrupa por obra_id)\n")
    for r in linhas:
        rotulo = r["nome"] if r.get("orfao") else f"{r['nome']} (id {r['obra_id']})"
        print(f"  {rotulo:<34} {brl(r['total']):>16}   ({r['lancamentos']} lançamentos)")
    print("\nConferência")
    print(f"  OK  soma das partes {brl(c['soma_das_partes'])} == total geral {brl(c['total_geral'])}")
    print(f"  OK  {c['obras_cadastradas']} linhas de obra para {c['obras_cadastradas']} obras cadastradas")
    o = c["orfaos"]
    if o["quantidade"]:
        print(f"  AVISO  {o['quantidade']} lançamentos sem obra no cadastro (obra_id {o['obra_ids']}): {brl(o['total'])}")
    for g in c["nomes_repetidos"]:
        print(f"  AVISO  nome repetido: '{g['nome']}' nas obras {g['obra_ids']} (agrupar por nome juntaria as duas)")
    for g in c["nomes_parecidos"]:
        print(f"  AVISO  nomes parecidos: {g['nomes']} nas obras {g['obra_ids']} (provável cadastro duplicado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
