"""o erro do compilador. o formato ta fixado no CONTRATOS.md, secao 7."""


class ErroMPL(Exception):
    """erro de compilacao ou de execucao, junto com o lugar onde aconteceu."""

    def __init__(self, fase, linha, coluna, mensagem):
        super().__init__(mensagem)
        self.fase = fase          # 'lexico', 'sintatico', 'semantico' ou 'execucao'
        self.linha = linha        # a primeira linha do arquivo e 1
        self.coluna = coluna      # a primeira coluna de cada linha e 1
        self.mensagem = mensagem

    def __str__(self):
        return f"erro {self.fase}: linha {self.linha}, coluna {self.coluna}: {self.mensagem}"


class NaoImplementado(Exception):
    """marca uma fase que ainda nao foi escrita, vai sumindo conforme as entregas avancam."""
