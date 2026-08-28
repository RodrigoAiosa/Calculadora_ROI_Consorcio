# 🏦 Calculadora de ROI de Consórcio

![Tests](https://github.com/RodrigoAiosa/Calculadora_ROI_Consorcio/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Streamlit](https://img.shields.io/badge/streamlit-%3E%3D1.32-FF4B4B)

Aplicação web interativa construída com **Streamlit** para avaliar se um
consórcio (veículo, imóvel, moto, máquina etc.) vale a pena, comparando-o
com as principais alternativas — **financiamento**, **investir e comprar à
vista** e **antecipação por lance** — além de calcular o **CET**, simular a
**probabilidade de contemplação por sorteio** e comparar **administradoras
via CSV**. Interface em tela cheia com tema escuro, cenários pré-definidos
e exportação para Excel e PDF.

---

## 🖥️ Visão geral

A ferramenta responde estas perguntas em uma única tela:

1. **Financiamento** — o consórcio (parcela sem juros de banco, mas com taxa
   de administração) é mais barato que financiar o mesmo bem?
2. **Investir e comprar à vista** — será que renderia mais aplicar o valor
   da parcela todo mês e comprar o bem à vista depois, em vez de entrar no
   consórcio?
3. **Lance / contemplação antecipada** — vale a pena ofertar um lance
   (próprio ou embutido) para antecipar a contemplação?
4. **CET** — qual é o custo efetivo total anualizado do consórcio, numa
   métrica comparável à de um financiamento?
5. **Probabilidade de sorteio** — qual a chance de ser contemplado por
   sorteio (sem lance) até um determinado mês?
6. **Comparação de administradoras** — entre várias propostas (via CSV),
   qual tem o menor CET?

---

## ✨ Funcionalidades

### 📋 Menu Lateral — Cenários Pré-definidos
Selecione um cenário e todos os inputs são preenchidos automaticamente
(crédito, prazo, taxas, reajuste anual, número de cotas do grupo, tipo de
lance padrão etc.) para 6 tipos de bem: carro popular, carro premium/SUV,
moto, apartamento, imóvel alto padrão e caminhão/máquina.

> Valores ilustrativos/educacionais — ajuste com os dados reais da sua
> simulação (administradora, banco, corretora) antes de decidir.

### 📊 Resumo Geral (cards no topo)
Parcela do consórcio, custo total, CET anualizado e qual das opções é a
mais vantajosa no cenário configurado.

### 💳 Aba — Consórcio x Financiamento
Compara parcela e custo total (Tabela Price) e mostra a economia em R$ e %.

### 📈 Aba — Investir e Comprar à Vista
Simula investir mensalmente o valor da parcela do consórcio (parcela pode
variar mês a mês se houver reajuste anual) a uma taxa de rendimento,
comparando com a valorização/correção do bem ao longo do tempo.

### 🎯 Aba — Lance / Contemplação Antecipada
Suporta **lance próprio** (dinheiro extra do bolso, com custo de
oportunidade) e **lance embutido** (parte do próprio crédito, sem
desembolso extra, mas com crédito líquido menor). Calcula quantos meses o
lance antecipa a contemplação e o ganho líquido de cada estratégia.

### 📊 Aba — CET (Custo Efetivo Total)
Calcula a Taxa Interna de Retorno (TIR) mensal e anualizada do fluxo de
caixa do consórcio, com 3 cenários de contemplação:
- 🟢 **Otimista** (mês 1) — comparável a um financiamento tradicional.
- 🔴 **Conservador** (último mês) — pode resultar em CET negativo (o
  consórcio funciona como poupança com deságio quando a contemplação vem
  tarde).
- 🎯 **Personalizado** — qualquer mês do prazo.

> ⚠️ Para meses de contemplação "intermediários", pode não existir uma TIR
> real (propriedade matemática do fluxo de caixa, não um bug). Nesse caso a
> ferramenta mostra um aviso explicando o motivo, em vez de exibir um
> número incorreto.

### 🎲 Aba — Probabilidade de Contemplação por Sorteio
Modelo simplificado (`1 / cotas remanescentes` por mês) que estima a
probabilidade acumulada de um participante ser sorteado até cada mês do
prazo, incluindo os meses para 50% e 90% de chance acumulada.

### 📂 Aba — Comparar Administradoras via CSV
Envie um `.csv` com propostas de diferentes administradoras (mesmo formato
do modelo disponível para download na própria aba) e a ferramenta rankeia
por CET — menor custo primeiro.

### 📖 Aba — Glossário
Termos do setor explicados: taxa de administração, fundo de reserva,
seguro, contemplação, lance, reajuste anual, CET, saldo devedor, cota e
Tabela Price.

### 📥 Exportação para Excel
Gera um `.xlsx` com 2 abas formatadas: **Resumo** (parâmetros e resultados
das 4 comparações) e **Projeção Mensal** (mês a mês).

### 📄 Exportação de Proposta em PDF
Resumo executivo de 1 página com os principais números das 4 comparações,
gerado com `reportlab`.

---

## 🧮 Fórmulas e premissas

| Métrica | Fórmula / premissa |
|---|---|
| Parcela do Consórcio (mês *m*) | Saldo devedor remanescente ÷ meses restantes, reajustado a cada 12 meses |
| Seguro mensal | `% × saldo devedor remanescente` (não sobre o valor cheio do crédito) |
| Parcela do Financiamento (Price) | `crédito × [i(1+i)ⁿ] / [(1+i)ⁿ − 1]` |
| Valor investido acumulado (mês *m*) | `saldo_{m-1} × (1+i) + parcela_m` (juros compostos, parcela pode variar) |
| Valor do bem corrigido (mês *m*) | `crédito × (1 + correção)^m` (correção contínua estimada) |
| Lance próprio — custo de oportunidade | `valor_lance × [(1+investimento)^(prazo−mês_lance) − 1]` |
| Lance embutido — crédito líquido | `crédito_atual − valor_lance` (sem custo de oportunidade, sem desembolso extra) |
| CET | TIR mensal do fluxo `[-parcela, ..., -parcela + crédito (no mês de contemplação), ..., -parcela]`, anualizada por `(1+i)^12 − 1` |
| Probabilidade de sorteio (mês *m*) | `1 / cotas_remanescentes` naquele mês, acumulada como `1 − ∏(1 − p_mês)` |

Todas as fórmulas estão isoladas em `src/calculations.py`,
`src/probabilidade.py` e `src/comparador.py`, sem dependência do Streamlit
— podem ser testadas e reaproveitadas fora da interface web.

---

## 📁 Estrutura do Projeto

```
roi-consorcio/
│
├── app.py                      # Aplicação principal (orquestra a UI)
├── requirements.txt             # Dependências do projeto
├── README.md                    # Este arquivo
├── LICENSE                      # Licença MIT
├── .gitignore
├── Dockerfile                   # Build para self-host / outros provedores
├── .dockerignore
├── mypy.ini                     # Configuração de checagem de tipos
│
├── .github/
│   └── workflows/
│       └── tests.yml            # CI: pytest + mypy em Python 3.11 e 3.12
│
├── .streamlit/
│   └── config.toml              # Tema escuro e configurações do servidor
│
├── assets/
│   └── style.css                # CSS customizado (cards, tabs, tema)
│
├── src/
│   ├── __init__.py
│   ├── scenarios.py              # Cenários pré-definidos
│   ├── calculations.py           # Núcleo de cálculo (cronograma, CET, lance, financiamento, investimento)
│   ├── probabilidade.py          # Simulador de contemplação por sorteio
│   ├── comparador.py             # Comparador de administradoras via CSV
│   ├── pdf_export.py             # Geração de proposta em PDF
│   ├── excel_export.py           # Geração do relatório .xlsx
│   ├── glossario.py              # Termos do glossário educativo
│   └── formatting.py             # Formatação de moeda, %, meses
│
└── tests/
    ├── test_calculations.py      # Testes do núcleo de cálculo (18 casos)
    ├── test_formatting.py        # Testes de formatação
    ├── test_probabilidade.py     # Testes do simulador de sorteio
    ├── test_comparador.py        # Testes do comparador de CSV
    └── test_exports.py           # Smoke tests de Excel e PDF
```

---

## 🚀 Como Rodar

### Localmente

```bash
git clone <url-do-repositorio>
cd roi-consorcio

python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

A aplicação abrirá automaticamente em `http://localhost:8501`.

### Via Docker

```bash
docker build -t roi-consorcio .
docker run -p 8501:8501 roi-consorcio
```

### Testes e checagem de tipos

```bash
pip install pytest pypdf mypy
pytest tests/ -v
mypy
```

---

## 🛠 Tecnologias

| Biblioteca | Versão | Uso |
|---|---|---|
| [Streamlit](https://streamlit.io/) | ≥ 1.32 | Interface web e sidebar |
| [Plotly](https://plotly.com/python/) | ≥ 5.20 | Gráficos interativos |
| [Pandas](https://pandas.pydata.org/) | ≥ 2.0 | Tabelas de projeção e leitura de CSV |
| [OpenPyXL](https://openpyxl.readthedocs.io/) | ≥ 3.1 | Exportação para Excel |
| [ReportLab](https://www.reportlab.com/) | ≥ 4.0 | Exportação de proposta em PDF |

---

## 🔄 CI/CD

Todo push ou pull request para `main` roda automaticamente (via GitHub
Actions, `.github/workflows/tests.yml`):
- A suíte de testes (`pytest`) em Python 3.11 e 3.12.
- Checagem de tipos (`mypy`) sobre `src/`.

---

## ⚠️ Aviso

Esta é uma ferramenta **educacional**. As taxas de administração, seguro,
juros de financiamento, rendimento de investimento, reajuste anual e
correção do bem usadas nos cenários pré-definidos são estimativas e variam
conforme a administradora, o banco, a instituição financeira e o momento
econômico. Sempre confira as condições reais antes de tomar qualquer
decisão financeira — esta calculadora não substitui uma simulação oficial
nem consultoria financeira.

---

## 📄 Licença

MIT License — sinta-se livre para usar e modificar.
