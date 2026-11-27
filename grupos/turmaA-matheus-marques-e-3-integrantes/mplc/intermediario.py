"""
Entrega 4 — geracao de codigo intermedio.
"""
from mplc.erros import NaoImplementado

def gerar(arvore, tabela=None):
    """Recebe a árvore e a tabela, gerando o código intermédio."""
    raise NaoImplementado("geracao de codigo")

def despejar(codigo):
    """Devolve as linhas do --ir."""
    if isinstance(codigo, str):
        return codigo.splitlines()
    return codigo