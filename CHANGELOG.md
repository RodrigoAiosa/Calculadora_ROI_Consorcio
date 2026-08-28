# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

## [2.1.0] — Consórcio Imobiliário como Investimento

### Adicionado
- **Nova aba "🏠 Investir em Aluguel"** — modela um caso de uso diferente do
  resto da calculadora: comprar um imóvel via consórcio para alugar (gerar
  renda), não para uso próprio.
- **`src/investimento_imovel.py`** — motor de cálculo do fluxo de caixa em
  3 fases (Pré-Contemplação, Locação + Parcelas, Renda Líquida) ao longo de
  um horizonte de longo prazo (padrão: 20 anos), com yield de aluguel,
  reajuste do aluguel pelo IPCA, valorização imobiliária anual e ITBI/escritura.
- **Resumo Financeiro do horizonte**: total desembolsado, aluguéis
  recebidos, valor do imóvel corrigido, patrimônio total gerado, ROI total,
  ROI anualizado e TIR (Taxa Interna de Retorno) do fluxo de caixa completo.
- **`calcular_tir_mensal`** extraída de `calcular_cet` como função pública
  reutilizável em `src/calculations.py` (elimina duplicação de lógica de
  TIR entre CET e o novo módulo de investimento imobiliário).
- 11 novos testes unitários (`tests/test_investimento_imovel.py`), incluindo
  um teste de regressão para o caso em que o horizonte de simulação termina
  antes do fim do prazo do consórcio.

### Corrigido
- Bug descoberto durante o desenvolvimento: quando o horizonte de simulação
  (ex: 10 anos) termina antes do fim do prazo do consórcio (ex: 200 meses),
  a Fase 2 somava parcelas/aluguéis além do fim da série mensal, gerando
  totais inconsistentes com o gráfico. Corrigido limitando o fim da Fase 2
  e o mês de contemplação ao horizonte total.

## [2.0.0] — Implementação do roadmap completo

### Adicionado
- **CET (Custo Efetivo Total)** — cálculo via TIR do fluxo de caixa, com
  cenários Otimista (mês 1), Conservador (último mês) e Personalizado.
- **Reajuste anual (INCC/IPCA)** — saldo devedor e crédito reajustados a
  cada 12 meses (aniversário do grupo), com recálculo da parcela.
- **Seguro sobre saldo devedor decrescente** — substituindo o seguro fixo
  sobre o valor total do crédito.
- **Lance embutido** (além do lance próprio já existente) — parte do
  crédito usada como lance, sem desembolso extra, mas com crédito líquido
  menor.
- **Simulador de probabilidade de contemplação por sorteio** (aba nova).
- **Comparador de administradoras via CSV**, com ranking por CET (aba
  nova).
- **Exportação de proposta em PDF** (1 página, via reportlab).
- **Glossário educativo** (aba nova, 10 termos do setor).
- Tooltips (`help=`) em todos os inputs da sidebar.
- Testes unitários para `formatting.py`, `probabilidade.py`,
  `comparador.py`, `excel_export.py` e `pdf_export.py` (antes só
  `calculations.py` tinha cobertura).
- CI com GitHub Actions (`pytest` + `mypy` em Python 3.11 e 3.12).
- `mypy.ini` e checagem de tipos limpa em todo `src/`.
- `Dockerfile` e `.dockerignore` para deploy fora do Streamlit Cloud.
- Badges no README (build, Python, licença, Streamlit).

### Alterado
- **Motor de cálculo do consórcio reescrito** (`gerar_cronograma_consorcio`)
  para gerar um cronograma mês a mês em vez de uma parcela constante —
  modelo simplificado da v1 continua disponível via
  `reajuste_anual=0, seguro_sobre_saldo=False`.
- `calcular_investimento` e `calcular_lance` agora aceitam uma lista de
  parcelas (podem variar mês a mês) em vez de um valor constante.
- Migrado `use_container_width=True` (deprecado) para `width='stretch'` em
  todos os gráficos e tabelas.

### Corrigido
- Divisão por zero em `calcular_lance` e `calcular_financiamento` quando
  `prazo_meses=0`.
- Emojis no PDF exportado apareciam como caixas pretas (fonte padrão do
  reportlab não tem esses glifos) — corrigido removendo emojis do texto
  antes de renderizar.

## [1.0.0] — Versão inicial

- Comparação consórcio x financiamento (Tabela Price).
- Comparação consórcio x investir e comprar à vista.
- Simulação de lance (próprio) para contemplação antecipada.
- Cenários pré-definidos (veículo, moto, imóvel, máquina).
- Exportação para Excel (abas Resumo e Projeção Mensal).
- Tema escuro customizado, gráficos Plotly, testes básicos de
  `calculations.py`.
