"""
Entrega 1 — analise lexica.

Transformar o texto do programa numa lista de tokens.

O que voces tem que devolver: uma lista de Token. O ultimo elemento e sempre
um token FIM_ARQUIVO. A regra de posicao dele esta em CONTRATOS.md, secao 7.

Leiam antes: LINGUAGEM.md secao 2, e CONTRATOS.md secao 2.
"""
from mplc.erros import NaoImplementado


class Token:
    __slots__ = ('tipo', 'lexema', 'linha', 'coluna')

    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo          # 'ID', 'INTEIRO', 'MAIS', ... (a lista esta no contrato)
        self.lexema = lexema      # o texto exato como apareceu no fonte
        self.linha = linha
        self.coluna = coluna      # a coluna do PRIMEIRO caractere do token

    def __str__(self):
        # esta e a linha que o --tokens imprime; nao mexam no formato
        return f"{self.linha},{self.coluna},{self.tipo},{self.lexema}"


def analisar(fonte):
    """Recebe o texto do programa. Devolve a lista de Token."""
    raise NaoImplementado('a analise lexica (Entrega 1)')
