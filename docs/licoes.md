# Lições: somar por nome em vez de id

## O que aconteceu

Num sistema de gestão de uma construtora, a IA montou um painel (dashboard) de obras. O total apareceu bem acima do real. A causa era o agrupamento: o modelo somou por **nome** da obra, e duas obras diferentes tinham nomes iguais ou parecidos. Este relato é da memória do autor.

O que eu **não** tenho, e por isso não escrevi: o valor real exato, a consulta que o modelo escreveu, quanto tempo o erro ficou visível, se os nomes reais das obras eram idênticos ou só parecidos, e se o total do painel inflou por junção pelo nome (linhas duplicadas) ou só a linha de uma obra mostrou a soma de duas. Os números deste repositório vêm de dados inventados (`gerar_dados.py`, semente 42). A reprodução tem o mesmo mecanismo, não os mesmos valores.

## Por que o erro passa

1. **Roda sem erro.** Agrupar por uma coluna de texto é válido em qualquer banco.
2. **O resultado é plausível.** R$ 201.930,00 numa obra grande não chama atenção sozinho.
3. **Juntar duas obras no agrupamento não muda a soma.** Isso vale só para a variante reproduzida (junção por id, agrupamento por nome); no caso real, se a junção tiver sido feita pelo nome, o total pode ter inflado. Na reprodução a soma das linhas ainda destoa em R$ 3.870,00, mas só por causa dos lançamentos sem obra. Sem esses lançamentos o total fecharia e a conferência óbvia, "o total bate?", passaria. Só uma conferência de contagem (linhas contra obras cadastradas) ou uma conta na mão numa obra pega a junção.
4. **Em geral ninguém abre a consulta.** Quem usa o painel vê o gráfico.

## O que eu levo disso

1. **Nome é rótulo, id é identidade.** Nome serve para mostrar. Para somar, juntar e contar, só a chave. Vale para obra, cliente, fornecedor, produto: qualquer coisa que duas pessoas possam cadastrar com o mesmo nome.
   *No repo:* `analise_correta.totais_por_obra` agrupa por `obra_id`; o nome só aparece na linha de saída.
2. **Conferir o total não basta.** Conferir o total pega o que se perde (lançamento sem obra: R$ 3.870,00 de diferença no ingênuo). Não pega o que se junta. Para o que se junta, conte as linhas contra as entidades cadastradas.
   *No repo:* `test_recusa_obras_juntadas_mesmo_com_a_soma_certa`.
3. **Faça a IA mostrar a consulta.** O número sem a consulta não é auditável. Com a consulta, o `GROUP BY nome` salta aos olhos.
   *No repo:* regra 3 do prompt em `prompts/analise-com-ia.md`.
4. **Faça a conferência morar no código, não na memória de quem lembrou.** Uma checagem que roda sozinha e recusa o resultado vale mais que um aviso de "lembre de conferir".
   *No repo:* `conferir()` levanta `ErroDeConciliacao`; `gerar_dashboard.py` não gera o HTML se ela falhar.
5. **Avisos visíveis para o que só um humano resolve.** Nome repetido pode ser dois imóveis diferentes ou um cadastro duplicado. O código não decide; mostra.
   *No repo:* faixa amarela no topo do `dashboard.html` e a lista "ATENÇÃO" na conferência.
6. **Teste com contraexemplo.** Deixar o método errado no repositório, marcado como falha esperada, mostra que os testes pegam o erro. Se alguém "consertar" o método ingênuo sem querer, a suíte avisa (sucesso inesperado).
   *No repo:* `TestMetodoIngenuo` e `VER_FALHAS=1`.
7. **Conta na mão com ferramenta diferente.** Os valores de `ESPERADO` foram conferidos com `awk` sobre o CSV (coincidem com os totais-alvo de `OBRAS` em `gerar_dados.py`; o `awk` os confirma por fora do código de análise), não com o código que está sendo testado. Teste que usa a mesma lógica para gerar o esperado só prova que o código concorda consigo mesmo.
8. **Dinheiro em `Decimal`.** Não é o tema, mas uma conferência `==` entre somas de `float` falha por centavos e treina a pessoa a ignorar a conferência.
9. **Desconfiar é parte do método.** Um número plausível ainda pode estar errado. O checklist transforma essa desconfiança em passos que alguém pode repetir.

## O que isto não prova

- Não prova que um prompt específico faz um modelo específico acertar. Não medi isso aqui.
- Não reproduz a variante em que a junção pelo nome duplica linhas e infla o total; só o agrupamento por nome depois de juntar por id.
- Não cobre erros de outro tipo: período errado, filtro de status, moeda, duplicata de lançamento (a mesma nota lançada duas vezes). O checklist menciona alguns, mas o código só conferiu agrupamento, soma, contagem e órfãos.
- Detecção de nomes parecidos é simples (acento, caixa, espaço). Abreviação e erro de digitação ficam de fora.

## O que eu faria a seguir

- Uma chave de unicidade no banco para o par (cliente, nome da obra) quando fizer sentido, para o nome repetido nem entrar. Troca: às vezes há mesmo duas obras com o mesmo nome e a regra de negócio permite.
- Um teste de consistência de segunda fonte: o mesmo número calculado por duas consultas escritas de forma independente, comparadas automaticamente.
- Registrar a consulta que gerou cada número do painel, junto do número.
