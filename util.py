"""Leitura dos CSVs e formatação de dinheiro, compartilhadas pelos scripts."""
import csv
from decimal import Decimal
from pathlib import Path

PASTA_DADOS = Path(__file__).parent / "dados"


def carregar(pasta=PASTA_DADOS):
    """Devolve (obras, lancamentos). Ids viram int e valor vira Decimal (nunca float para dinheiro)."""
    pasta = Path(pasta)
    with open(pasta / "obras.csv", encoding="utf-8", newline="") as f:
        obras = [{**r, "obra_id": int(r["obra_id"])} for r in csv.DictReader(f)]
    with open(pasta / "lancamentos.csv", encoding="utf-8", newline="") as f:
        lancamentos = [
            {**r, "lancamento_id": int(r["lancamento_id"]), "obra_id": int(r["obra_id"]), "valor": Decimal(r["valor"])}
            for r in csv.DictReader(f)
        ]
    return obras, lancamentos


def brl(valor):
    """Decimal -> 'R$ 1.234,56'."""
    texto = f"{valor:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {texto}"
