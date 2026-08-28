"""Glossário educativo dos termos usados na Calculadora de ROI de Consórcio."""

from typing import TypedDict


class TermoGlossario(TypedDict):
    termo: str
    definicao: str


GLOSSARIO: list[TermoGlossario] = [
    {
        "termo": "Taxa de administração",
        "definicao": (
            "Percentual cobrado pela administradora do consórcio sobre o valor do "
            "crédito, diluído nas parcelas ao longo do prazo. É a principal receita "
            "da administradora — não existe cobrança de juros no consórcio, mas "
            "essa taxa cumpre papel parecido no custo total."
        ),
    },
    {
        "termo": "Fundo de reserva",
        "definicao": (
            "Percentual adicional retido para cobrir eventuais inadimplências de "
            "outros participantes do grupo, garantindo que o grupo consiga cumprir "
            "as contemplações previstas mesmo com atrasos pontuais."
        ),
    },
    {
        "termo": "Seguro do consórcio",
        "definicao": (
            "Cobre o saldo devedor em caso de morte ou invalidez do participante. "
            "Normalmente incide como um percentual mensal sobre o saldo devedor "
            "(ou, em modelos mais simples, sobre o valor do crédito)."
        ),
    },
    {
        "termo": "Contemplação",
        "definicao": (
            "Momento em que o participante recebe a carta de crédito (ou o bem) "
            "para usar. Pode acontecer por sorteio (entre todos os participantes "
            "em dia) ou por lance (quem oferece mais é contemplado primeiro)."
        ),
    },
    {
        "termo": "Lance",
        "definicao": (
            "Valor oferecido por um participante para tentar antecipar a própria "
            "contemplação. Pode ser 'lance próprio' (dinheiro extra do bolso do "
            "participante) ou 'lance embutido' (parte do próprio crédito, sem "
            "desembolso extra, mas reduzindo o valor líquido recebido)."
        ),
    },
    {
        "termo": "Reajuste anual (INCC/IPCA)",
        "definicao": (
            "No aniversário do grupo, o saldo devedor e o valor do crédito são "
            "corrigidos por um índice — geralmente o INCC (Índice Nacional de "
            "Custo da Construção) para imóveis, ou o IPCA para veículos e outros "
            "bens — mantendo o crédito com poder de compra equivalente ao do bem."
        ),
    },
    {
        "termo": "CET — Custo Efetivo Total",
        "definicao": (
            "Taxa que resume, em termos anuais, o custo real do consórcio "
            "considerando o valor pago e o valor recebido ao longo do tempo — "
            "permite comparar o consórcio com outras formas de crédito (como um "
            "financiamento) numa métrica só."
        ),
    },
    {
        "termo": "Saldo devedor",
        "definicao": (
            "Valor que ainda falta pagar dentro do grupo do consórcio em um "
            "determinado mês. Some conforme as parcelas (excluindo o seguro) são "
            "pagas, e pode ser reajustado anualmente."
        ),
    },
    {
        "termo": "Cota",
        "definicao": (
            "Cada participante do grupo de consórcio possui uma cota — a unidade "
            "usada para calcular a probabilidade de contemplação por sorteio a "
            "cada assembleia mensal."
        ),
    },
    {
        "termo": "Tabela Price",
        "definicao": (
            "Sistema de amortização de financiamentos com parcelas fixas ao longo "
            "de todo o prazo (juros + amortização variam mês a mês, mas a soma "
            "das duas partes permanece constante). É o sistema mais comum em "
            "financiamentos de veículos e crédito pessoal no Brasil."
        ),
    },
]
