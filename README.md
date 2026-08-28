# 🏦 Calculadora de ROI de Consórcio

Aplicação web interativa construída com **Streamlit** para avaliar se um
consórcio (veículo, imóvel, moto, máquina etc.) vale a pena, comparando-o
com as principais alternativas: **financiamento**, **investir e comprar à
vista** e **antecipação por lance**. Interface em tela cheia com tema
escuro, cenários pré-definidos e exportação para Excel.

---

## 🖥️ Visão geral

A ferramenta responde três perguntas em uma única tela:

1. **Financiamento** — o consórcio (parcela sem juros de banco, mas com taxa
   de administração) é mais barato que financiar o mesmo bem?
2. **Investir e comprar à vista** — será que renderia mais aplicar o valor
   da parcela todo mês e comprar o bem à vista depois, em vez de entrar no
   consórcio?
3. **Lance / contemplação antecipada** — vale a pena ofertar um lance para
   antecipar a contemplação, considerando o custo de oportunidade desse
   dinheiro?

---

## ✨ Funcionalidades

### 📋 Menu Lateral — Cenários Pré-definidos
Selecione um cenário e todos os inputs são preenchidos automaticamente:

| Cenário | Crédito | Prazo | Taxa Adm. | Financ. (a.m.) | Investim. (a.m.) | Correção Bem (a.m.) |
|---|---|---|---|---|---|---|
| 🎯 Personalizado | — | — | — | — | — | — |
| 🚗 Carro Popular | R$ 60.000 | 60m | 17% | 1,7% | 0,85% | 0,35% |
| 🚙 Carro Premium / SUV | R$ 180.000 | 72m | 16% | 1,6% | 0,85% | 0,30% |
| 🏍️ Moto | R$ 22.000 | 48m | 15% | 2,0% | 0,85% | 0,40% |
| 🏠 Apartamento | R$ 350.000 | 180m | 19% | 0,90% | 0,85% | 0,45% |
| 🏢 Imóvel Alto Padrão | R$ 900.000 | 200m | 20% | 0,85% | 0,90% | 0,40% |
| 🚚 Caminhão / Máquina | R$ 280.000 | 84m | 14% | 1,5% | 0,85% | 0,35% |

> Valores ilustrativos/educacionais — ajuste com os dados reais da sua
> simulação (administradora, banco, corretora) antes de decidir.

### 📊 Resumo Geral (cards no topo)
Parcela do consórcio, custo total, economia frente ao financiamento e qual
das três opções é a mais vantajosa no cenário configurado.

### 💳 Aba — Consórcio x Financiamento
Compara parcela e custo total (Tabela Price) e mostra a economia em R$ e %.
Gráfico de custo acumulado das duas opções lado a lado.

### 📈 Aba — Investir e Comprar à Vista
Simula investir mensalmente o valor da parcela do consórcio a uma taxa de
rendimento, comparando com a valorização/correção do bem ao longo do tempo.
Mostra em que mês o valor investido alcançaria o preço do bem.

### 🎯 Aba — Lance / Contemplação Antecipada
Calcula quantos meses um lance antecipa a contemplação, o benefício de
evitar a valorização do bem nesse período e o custo de oportunidade do
dinheiro do lance (o que renderia se ficasse investido).

### 📥 Exportação para Excel
Gera um `.xlsx` com 2 abas formatadas:

- **Resumo** — parâmetros de entrada e resultados das 3 comparações, com
  cores dinâmicas (verde/vermelho conforme o sinal do valor).
- **Projeção Mensal** — custo acumulado, valor investido, valor do bem
  corrigido e saldo devedor (com e sem lance), mês a mês.

---

## 🧮 Fórmulas

| Métrica | Fórmula |
|---|---|
| Parcela do Consórcio | `(crédito × (1 + taxa_adm + fundo_reserva)) / prazo + seguro_mensal` |
| Parcela do Financiamento (Price) | `crédito × [i(1+i)ⁿ] / [(1+i)ⁿ − 1]` |
| Economia vs. Financiamento | `custo_total_financiamento − custo_total_consórcio` |
| Valor investido acumulado (mês *m*) | `parcela × [((1+i)^m − 1) / i]` (juros compostos) |
| Valor do bem corrigido (mês *m*) | `crédito × (1 + correção)^m` |
| Benefício da antecipação (lance) | `crédito × [(1+correção)^meses_antecipados − 1]` |
| Custo de oportunidade do lance | `valor_lance × [(1+investimento)^(prazo−mês_lance) − 1]` |
| Ganho líquido do lance | `benefício_antecipação − custo_oportunidade` |

Todas as fórmulas estão isoladas em `src/calculations.py`, sem dependência
do Streamlit — podem ser testadas e reaproveitadas fora da interface web.

---

## 📁 Estrutura do Projeto

```
roi-consorcio/
│
├── app.py                     # Aplicação principal (orquestra a UI)
├── requirements.txt            # Dependências do projeto
├── README.md                   # Este arquivo
├── LICENSE                     # Licença MIT
├── .gitignore                  # Arquivos ignorados pelo Git
│
├── .streamlit/
│   └── config.toml             # Tema escuro e configurações do servidor
│
├── assets/
│   └── style.css                # CSS customizado (cards, tabs, tema)
│
├── src/
│   ├── __init__.py
│   ├── scenarios.py             # Cenários pré-definidos
│   ├── calculations.py          # Núcleo de cálculo financeiro (puro, sem UI)
│   ├── formatting.py            # Formatação de moeda, %, meses
│   └── excel_export.py          # Geração do relatório .xlsx
│
└── tests/
    └── test_calculations.py     # Testes unitários (pytest)
```

---

## 🚀 Como Rodar

### 1. Clone ou baixe o projeto
```bash
git clone <url-do-repositorio>
cd roi-consorcio
```

### 2. Crie e ative um ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação
```bash
streamlit run app.py
```

A aplicação abrirá automaticamente em `http://localhost:8501`.

### 5. (Opcional) Rode os testes
```bash
pip install pytest
pytest tests/ -v
```

---

## 🛠 Tecnologias

| Biblioteca | Versão | Uso |
|---|---|---|
| [Streamlit](https://streamlit.io/) | ≥ 1.32 | Interface web e sidebar |
| [Plotly](https://plotly.com/python/) | ≥ 5.20 | Gráficos interativos |
| [Pandas](https://pandas.pydata.org/) | ≥ 2.0 | Tabelas de projeção |
| [OpenPyXL](https://openpyxl.readthedocs.io/) | ≥ 3.1 | Exportação para Excel |

---

## ⚠️ Aviso

Esta é uma ferramenta **educacional**. As taxas de administração, seguro,
juros de financiamento, rendimento de investimento e correção do bem usadas
nos cenários pré-definidos são estimativas e variam conforme a
administradora, o banco, a instituição financeira e o momento econômico.
Sempre confira as condições reais antes de tomar qualquer decisão
financeira — esta calculadora não substitui uma simulação oficial nem
consultoria financeira.

---

## 📄 Licença

MIT License — sinta-se livre para usar e modificar.
