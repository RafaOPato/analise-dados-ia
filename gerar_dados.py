"""Gera dados 100% fictícios de uma construtora para reproduzir o erro "somar por nome, não por id".

    python gerar_dados.py          # escreve dados/obras.csv e dados/lancamentos.csv

Mesma semente, mesmos arquivos. Cada obra tem um total-alvo; os lançamentos são sorteados e o
último absorve a diferença de centavos, então o total de cada obra é conhecido de antemão e dá
para conferir na mão (é isso que o test_analise.py faz).
"""
import csv
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

SEMENTE = 42
PASTA = Path(__file__).parent / "dados"

# obra_id, nome, bairro, tipo, total-alvo em reais.
# Repare: ids 1 e 7 têm o MESMO nome, assim como 2 e 8. O 4 e o 9 só diferem pelo acento.
OBRAS = [
    (1, "Residencial Aurora", "Bairro Alfa", "residencial", 118640),
    (2, "Edifício Horizonte", "Bairro Beta", "comercial", 96250),
    (3, "Casa Lago Azul", "Bairro Gama", "residencial", 47380),
    (4, "Condominio Jardim Sul", "Bairro Delta", "residencial", 133900),
    (5, "Galpão Central", "Bairro Épsilon", "industrial", 64720),
    (6, "Reforma Loja Praça", "Bairro Zeta", "comercial", 21150),
    (7, "Residencial Aurora", "Bairro Eta", "residencial", 83290),
    (8, "Edifício Horizonte", "Bairro Teta", "comercial", 58410),
    (9, "Condomínio Jardim Sul", "Bairro Iota", "residencial", 39870),
    (10, "Clínica Vida", "Bairro Capa", "comercial", 72560),
]

# Lançamentos que apontam para uma obra que não está no cadastro (obra apagada, id digitado errado).
OBRA_INEXISTENTE = 99
ORFAOS = [
    ("2026-03-14", "Instalações elétricas", "Fornecedor Alfa Ltda", "Cabos e disjuntores - obra fora do cadastro", 218000),
    ("2026-06-02", "Equipamentos", "Fornecedor Beta Ltda", "Aluguel de betoneira - obra fora do cadastro", 169000),
]

CATEGORIAS = ["Fundação", "Estrutura", "Alvenaria", "Instalações elétricas", "Instalações hidráulicas",
              "Acabamento", "Mão de obra", "Equipamentos"]
FORNECEDORES = ["Fornecedor Alfa Ltda", "Fornecedor Beta Ltda", "Fornecedor Gama Ltda",
                "Fornecedor Delta Ltda", "Fornecedor Épsilon Ltda", "Fornecedor Zeta Ltda"]


def repartir(total_centavos, n, rng):
    """Divide o total em n valores positivos que somam exatamente o total."""
    pesos = [rng.uniform(0.3, 2.0) for _ in range(n)]
    soma = sum(pesos)
    partes = [int(total_centavos * p / soma) for p in pesos]
    partes[-1] += total_centavos - sum(partes)
    return partes


def reais(centavos):
    return Decimal(centavos).scaleb(-2)  # 12345 -> Decimal('123.45')


def gerar(semente=SEMENTE):
    """Devolve (obras, lancamentos) nos mesmos tipos que util.carregar() devolve."""
    rng = random.Random(semente)
    obras = [{"obra_id": i, "nome": n, "bairro": b, "tipo": t} for i, n, b, t, _ in OBRAS]
    brutos = []  # (data, obra_id, categoria, fornecedor, descricao, centavos)
    for obra_id, _, _, _, alvo in OBRAS:
        partes = repartir(alvo * 100, rng.randint(14, 30), rng)
        for centavos in partes:
            categoria = rng.choice(CATEGORIAS)
            brutos.append((
                (date(2026, 1, 5) + timedelta(days=rng.randint(0, 270))).isoformat(),
                obra_id, categoria, rng.choice(FORNECEDORES), f"{categoria} - nota {rng.randint(100, 999)}", centavos,
            ))
    for data, categoria, fornecedor, descricao, centavos in ORFAOS:
        brutos.append((data, OBRA_INEXISTENTE, categoria, fornecedor, descricao, centavos))
    brutos.sort(key=lambda b: (b[0], b[1], b[5]))
    lancamentos = [
        {"lancamento_id": n, "obra_id": o, "data": d, "categoria": c, "fornecedor": f, "descricao": ds, "valor": reais(v)}
        for n, (d, o, c, f, ds, v) in enumerate(brutos, start=1)
    ]
    return obras, lancamentos


def escrever(pasta=PASTA):
    pasta = Path(pasta)
    pasta.mkdir(exist_ok=True)
    obras, lancamentos = gerar()
    for nome, linhas in (("obras.csv", obras), ("lancamentos.csv", lancamentos)):
        with open(pasta / nome, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0]), lineterminator="\n")
            w.writeheader()
            w.writerows({k: (f"{v:.2f}" if k == "valor" else v) for k, v in l.items()} for l in linhas)
    return len(obras), len(lancamentos)


if __name__ == "__main__":
    n_obras, n_lanc = escrever()
    print(f"dados/obras.csv: {n_obras} obras | dados/lancamentos.csv: {n_lanc} lançamentos (semente {SEMENTE})")
