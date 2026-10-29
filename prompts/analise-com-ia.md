# Análise de dados com IA: prompt reutilizável e checklist de validação

Aviso honesto: **não rodei este prompt contra nenhum modelo neste repositório.** Ele é a consequência prática do erro reproduzido aqui (agrupar por nome em vez de id). O que o repositório prova, em código e com testes, são as conferências do checklist. Se o prompt melhora ou não a resposta de um modelo específico, eu ainda não medi.

## Como usar

1. Descreva o esquema, não só "os dados": tabelas, colunas e qual coluna é a **chave**. Diga explicitamente quais colunas **não** são únicas.
2. Cole o prompt abaixo e preencha o que está entre `{{ }}`.
3. Antes de repassar qualquer número, passe a resposta pelo checklist da seção seguinte. O prompt tenta reduzir o risco (não medi se reduz); o checklist é o que decide.

## O prompt

```text
Você é um analista de dados. Vou pedir um número que alguém vai usar para decidir.
Siga estas regras antes de responder.

CONTEXTO
- Tabelas e colunas: {{ex.: obras(obra_id, nome, bairro); lancamentos(lancamento_id, obra_id, data, valor)}}
- Chave de cada tabela: {{ex.: obras.obra_id e lancamentos.lancamento_id. obras.nome NÃO é único}}
- Pergunta: {{ex.: gasto total por obra}}

REGRAS
1. Agrupe e junte SEMPRE pela chave (id), nunca por nome, descrição ou rótulo.
   O nome só entra como coluna de exibição, depois do agrupamento.
2. Antes de agrupar, mostre quantos valores distintos de id e de nome existem e liste
   os nomes que aparecem em mais de um id.
3. Mostre a consulta (SQL ou código) ANTES do resultado. Não me entregue só o número.
4. Não use junção que perde linhas em silêncio. Diga quantos lançamentos ficaram sem
   correspondência e quanto dinheiro eles somam.
5. Concilie e mostre as contas:
   a) soma das partes == total geral, calculado por um caminho separado;
   b) número de linhas do resultado == número de ids distintos esperado.
   Se alguma não fechar, diga isso ANTES de qualquer conclusão.
6. Escreva as suposições que fez (ex.: "assumi que nomes iguais são a mesma obra").
   O que não deu para verificar, diga que não verificou. Não preencha lacuna com palpite.
7. Formato da resposta: (a) consulta; (b) tabela com o id em uma coluna; (c) conferências
   com os números; (d) suposições e dúvidas.
```

### Versão curta, para o dia a dia

```text
Agrupe por {{id}}, nunca por nome. Mostre a consulta antes do resultado. Diga quantas linhas
ficaram sem correspondência. Mostre soma das partes == total geral e linhas == ids distintos.
Liste nomes repetidos. Escreva as suposições.
```

### Prompt de segunda passada (revisão da consulta)

Útil quando a consulta já existe e você quer que o modelo (ou outro) a revise:

```text
Revise esta consulta como se fosse um erro em produção. Procure: agrupamento por coluna que
não é única; junção que descarta linhas; filtro que muda o universo; soma de coluna com
duplicatas; total calculado do mesmo jeito que as partes. Para cada achado, diga o que
quebra e dê um exemplo numérico. Se não achou nada, diga o que você NÃO conseguiu verificar.

{{consulta}}
```

## Checklist de validação de resposta de IA em análise de dados

Marque cada item antes de usar o número. A coluna da direita mostra onde este repositório faz essa checagem em código.

| # | Pergunta | Como conferir | Neste repositório |
|---|---|---|---|
| 1 | Agrupou pela chave (id) e não por nome ou rótulo? | Leia a consulta: o `GROUP BY` e o `JOIN` usam id? | `analise_correta.totais_por_obra` x `analise_ingenua.totais_por_obra` |
| 2 | A coluna de agrupamento é única? | `COUNT(DISTINCT id)` contra `COUNT(DISTINCT nome)`; liste nomes com mais de um id | `conferir()["nomes_repetidos"]` |
| 3 | Quase iguais também contam? | Normalize acento, caixa e espaço e compare de novo | `normalizar()` e `conferir()["nomes_parecidos"]` |
| 4 | O modelo mostrou a consulta? | Se só veio o número, peça a consulta e refaça | regra 3 do prompt |
| 5 | A soma das partes bate com o total geral? | Calcule o total por um caminho separado (outra consulta, outra ferramenta) | `ErroDeConciliacao: soma das partes ...` |
| 6 | O número de linhas bate com o número de entidades? | Linhas do resultado contra `COUNT(DISTINCT id)` | `ErroDeConciliacao: ... linhas para ... obras` |
| 7 | Algo se perdeu na junção? | Conte lançamentos sem correspondência (órfãos) e some o valor deles | linha "(sem obra no cadastro)" e `conferir()["orfaos"]` |
| 8 | Confere na mão em 1 ou 2 casos? | Escolha uma entidade e some com outra ferramenta (filtro da planilha, `awk`) | `ESPERADO` em `test_analise.py`, conferido com `awk` |
| 9 | A ordem de grandeza faz sentido? | Compare com o mês anterior, o orçamento ou o que você esperava. Só uma pessoa que conhece o negócio avalia isso | (julgamento humano) |
| 10 | O que o modelo supôs? | Procure frases como "assumi que" e valide cada uma | regra 6 do prompt |
| 11 | A conferência está em código ou só na sua cabeça? | Se for rodar de novo amanhã, a checagem precisa rodar sozinha e recusar o resultado | `conferir()` levanta exceção |
| 12 | Quem decide? | A IA sugere, o código confere, a pessoa decide | `gerar_dashboard.py` só gera se `conferir()` passar |

Regras de bolso:

- **Somar certo não prova nada sobre o agrupamento.** Juntar duas obras no agrupamento não muda a soma (se a junção for feita pelo nome, o total pode inflar). Por isso os itens 5 e 6 andam juntos.
- **Número que "faz sentido" não é critério.** Use o item 8 (conta na mão) e o 9 (ordem de grandeza) com um valor de referência.
- **Pedir a consulta é grátis; descobrir o erro depois não é.**
