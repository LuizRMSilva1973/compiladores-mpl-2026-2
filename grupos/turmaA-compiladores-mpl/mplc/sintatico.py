"""
Entrega 2 — analise sintatica.

Transformar a lista de tokens numa arvore.

O parser usa descida recursiva: uma funcao por nivel de precedencia. Os niveis
mais fracos chamam os mais fortes; operadores binarios sao acumulados em um
laco (associatividade a esquerda), enquanto os unarios chamam a si proprios
(associatividade a direita).

Gerador de parser (ANTLR, PLY, yacc) esta proibido nesta entrega e na
anterior.
"""
from decimal import Decimal, InvalidOperation

from mplc.erros import ErroMPL


TIPOS_RETORNO = {
    'TIPO_INTEIRO': 'inteiro',
    'TIPO_REAL': 'real',
    'TIPO_LOGICO': 'logico',
    'TIPO_TEXTO': 'texto',
    'TIPO_VAZIO': 'vazio',
}

TIPOS_VALOR = {
    'TIPO_INTEIRO': 'inteiro',
    'TIPO_REAL': 'real',
    'TIPO_LOGICO': 'logico',
    'TIPO_TEXTO': 'texto',
}

OP_BINARIOS = {
    'OU': 'ou',
    'E': 'e',
    'IGUAL': '==',
    'DIFERENTE': '!=',
    'MENOR': '<',
    'MENOR_IGUAL': '<=',
    'MAIOR': '>',
    'MAIOR_IGUAL': '>=',
    'MAIS': '+',
    'MENOS': '-',
    'VEZES': '*',
    'DIVIDE': '/',
    'RESTO': '%',
}


class No:
    """Um no da arvore. O rotulo e o que sai no --ast."""

    def __init__(self, rotulo, filhos=None, linha=0, coluna=0, **extra):
        self.rotulo = rotulo
        self.filhos = filhos or []
        self.linha = linha
        self.coluna = coluna
        self.extra = extra


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    @property
    def atual(self):
        return self.tokens[self.pos]

    def avancar(self):
        tok = self.atual
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def aceita(self, tipo):
        if self.atual.tipo == tipo:
            return self.avancar()
        return None

    def espera(self, tipo):
        if self.atual.tipo != tipo:
            raise self.erro_esperado(tipo)
        return self.avancar()

    def erro_esperado(self, esperado):
        tok = self.atual
        return ErroMPL(
            'sintatico',
            tok.linha,
            tok.coluna,
            f'esperado {esperado}'
        )

    def erro_mensagem(self, mensagem):
        tok = self.atual
        raise ErroMPL('sintatico', tok.linha, tok.coluna, mensagem)

    # ------------------------------------------------------------- programa

    def programa(self):
        funcoes = []
        while self.atual.tipo != 'FIM_ARQUIVO':
            funcoes.append(self.funcao())
        self.espera('FIM_ARQUIVO')
        return No('programa', funcoes)

    def funcao(self):
        inicio = self.espera('FUNCAO')
        tipo_tok = self.tipo_retorno()
        nome_tok = self.espera('ID')
        self.espera('ABRE_PAR')

        parametros = self.parametros()

        self.espera('FECHA_PAR')
        bloco = self.bloco()

        tipo = TIPOS_RETORNO[tipo_tok.tipo]
        no = No(
            f'funcao {nome_tok.lexema} {tipo}',
            [parametros, bloco],
            linha=inicio.linha,
            coluna=inicio.coluna,
            nome=nome_tok.lexema,
            tipo=tipo,
        )
        return no

    def parametros(self):
        filhos = []
        if self.atual.tipo == 'FECHA_PAR':
            return No('parametros', filhos)

        while True:
            tipo_tok = self.tipo_valor()
            nome_tok = self.espera('ID')
            tipo = TIPOS_VALOR[tipo_tok.tipo]
            filhos.append(No(
                f'parametro {nome_tok.lexema} {tipo}',
                linha=nome_tok.linha,
                coluna=nome_tok.coluna,
                nome=nome_tok.lexema,
                tipo=tipo,
            ))
            if not self.aceita('VIRGULA'):
                break
        return No('parametros', filhos)

    def tipo_retorno(self):
        if self.atual.tipo in TIPOS_RETORNO:
            return self.avancar()
        raise self.erro_esperado('tipo de retorno')

    def tipo_valor(self):
        if self.atual.tipo in TIPOS_VALOR:
            return self.avancar()
        raise self.erro_esperado('tipo')

    # --------------------------------------------------------------- comandos

    def bloco(self):
        inicio = self.espera('ABRE_CHAVE')
        comandos = []
        while self.atual.tipo not in ('FECHA_CHAVE', 'FIM_ARQUIVO'):
            comandos.append(self.comando())
        self.espera('FECHA_CHAVE')
        return No('bloco', comandos, linha=inicio.linha, coluna=inicio.coluna)

    def comando(self):
        tok = self.atual

        if tok.tipo in TIPOS_VALOR:
            return self.declaracao()
        if tok.tipo == 'ID':
            return self.comando_id()
        if tok.tipo == 'SE':
            return self.condicional()
        if tok.tipo == 'ENQUANTO':
            return self.repeticao()
        if tok.tipo == 'ESCREVA':
            return self.escrita()
        if tok.tipo == 'RETORNE':
            return self.retorno()
        if tok.tipo == 'ABRE_CHAVE':
            return self.bloco()

        raise ErroMPL(
            'sintatico', tok.linha, tok.coluna,
            f'comando inesperado: {tok.lexema or tok.tipo}'
        )

    def declaracao(self):
        tipo_tok = self.tipo_valor()
        nome_tok = self.espera('ID')
        filhos = []
        if self.aceita('ATRIBUI'):
            filhos.append(self.expressao())
        self.espera('PONTO_VIRGULA')
        tipo = TIPOS_VALOR[tipo_tok.tipo]
        return No(
            f'declaracao {nome_tok.lexema} {tipo}',
            filhos,
            linha=tipo_tok.linha,
            coluna=tipo_tok.coluna,
            nome=nome_tok.lexema,
            tipo=tipo,
        )

    def comando_id(self):
        nome_tok = self.espera('ID')
        if self.atual.tipo == 'ATRIBUI':
            self.avancar()
            expr = self.expressao()
            self.espera('PONTO_VIRGULA')
            return No(
                f'atribuicao {nome_tok.lexema}',
                [expr],
                linha=nome_tok.linha,
                coluna=nome_tok.coluna,
                nome=nome_tok.lexema,
            )
        if self.atual.tipo == 'ABRE_PAR':
            chamada = self.chamada_apos_nome(nome_tok)
            self.espera('PONTO_VIRGULA')
            return chamada
        raise self.erro_esperado("'=' ou '('")

    def condicional(self):
        inicio = self.espera('SE')
        self.espera('ABRE_PAR')
        condicao = self.expressao()
        self.espera('FECHA_PAR')
        entao = self.bloco()
        filhos = [condicao, entao]
        if self.aceita('SENAO'):
            filhos.append(self.bloco())
        return No('se', filhos, linha=inicio.linha, coluna=inicio.coluna)

    def repeticao(self):
        inicio = self.espera('ENQUANTO')
        self.espera('ABRE_PAR')
        condicao = self.expressao()
        self.espera('FECHA_PAR')
        corpo = self.bloco()
        return No('enquanto', [condicao, corpo], linha=inicio.linha, coluna=inicio.coluna)

    def escrita(self):
        inicio = self.espera('ESCREVA')
        self.espera('ABRE_PAR')
        expr = self.expressao()
        self.espera('FECHA_PAR')
        self.espera('PONTO_VIRGULA')
        return No('escreva', [expr], linha=inicio.linha, coluna=inicio.coluna)

    def retorno(self):
        inicio = self.espera('RETORNE')
        filhos = []
        if self.atual.tipo != 'PONTO_VIRGULA':
            filhos.append(self.expressao())
        self.espera('PONTO_VIRGULA')
        return No('retorne', filhos, linha=inicio.linha, coluna=inicio.coluna)

    # ------------------------------------------------------------- expressoes
    # Cada nivel chama o proximo nivel mais forte. Os binarios sao agrupados
    # a esquerda com um while; unarios sao recursivos a direita.

    def expressao(self):
        return self.ou()

    def _binario_esquerda(self, proximo, tipos):
        esquerda = proximo()
        while self.atual.tipo in tipos:
            operador = self.avancar()
            direita = proximo()
            esquerda = No(
                f'binario {OP_BINARIOS[operador.tipo]}',
                [esquerda, direita],
                linha=operador.linha,
                coluna=operador.coluna,
                operador=OP_BINARIOS[operador.tipo],
            )
        return esquerda

    def ou(self):
        return self._binario_esquerda(self.e, {'OU'})

    def e(self):
        return self._binario_esquerda(self.igualdade, {'E'})

    def igualdade(self):
        return self._binario_esquerda(self.relacional, {'IGUAL', 'DIFERENTE'})

    def relacional(self):
        return self._binario_esquerda(
            self.aditiva,
            {'MENOR', 'MENOR_IGUAL', 'MAIOR', 'MAIOR_IGUAL'}
        )

    def aditiva(self):
        return self._binario_esquerda(self.multiplicativa, {'MAIS', 'MENOS'})

    def multiplicativa(self):
        return self._binario_esquerda(self.unario, {'VEZES', 'DIVIDE', 'RESTO'})

    def unario(self):
        if self.atual.tipo in ('NAO', 'MENOS'):
            tok = self.avancar()
            op = 'nao' if tok.tipo == 'NAO' else '-'
            filho = self.unario()
            return No(
                f'unario {op}',
                [filho],
                linha=tok.linha,
                coluna=tok.coluna,
                operador=op,
            )
        return self.primario()

    def primario(self):
        tok = self.atual

        if tok.tipo == 'INTEIRO':
            self.avancar()
            return No(
                f'literal inteiro {tok.lexema}',
                linha=tok.linha,
                coluna=tok.coluna,
                tipo='inteiro',
                valor=tok.lexema,
            )

        if tok.tipo == 'REAL':
            self.avancar()
            try:
                valor = format(Decimal(tok.lexema), '.6f')
            except (InvalidOperation, ValueError):
                valor = tok.lexema
            return No(
                f'literal real {valor}',
                linha=tok.linha,
                coluna=tok.coluna,
                tipo='real',
                valor=valor,
            )

        if tok.tipo == 'LOGICO':
            self.avancar()
            return No(
                f'literal logico {tok.lexema}',
                linha=tok.linha,
                coluna=tok.coluna,
                tipo='logico',
                valor=tok.lexema,
            )

        if tok.tipo == 'TEXTO':
            self.avancar()
            return No(
                f'literal texto {tok.lexema}',
                linha=tok.linha,
                coluna=tok.coluna,
                tipo='texto',
                valor=tok.lexema,
            )

        if tok.tipo == 'ID':
            nome = self.avancar()
            if self.atual.tipo == 'ABRE_PAR':
                return self.chamada_apos_nome(nome)
            return No(
                f'variavel {nome.lexema}',
                linha=nome.linha,
                coluna=nome.coluna,
                nome=nome.lexema,
            )

        if tok.tipo == 'ABRE_PAR':
            self.avancar()
            expr = self.expressao()
            self.espera('FECHA_PAR')
            return expr

        raise ErroMPL(
            'sintatico', tok.linha, tok.coluna,
            'expressao esperada'
        )

    def chamada_apos_nome(self, nome_tok):
        self.espera('ABRE_PAR')
        argumentos = []
        if self.atual.tipo != 'FECHA_PAR':
            argumentos.append(self.expressao())
            while self.aceita('VIRGULA'):
                argumentos.append(self.expressao())
        self.espera('FECHA_PAR')
        return No(
            f'chamada {nome_tok.lexema}',
            argumentos,
            linha=nome_tok.linha,
            coluna=nome_tok.coluna,
            nome=nome_tok.lexema,
        )


def analisar(tokens):
    """Recebe a lista de Token. Devolve a raiz da arvore (um No 'programa')."""
    return Parser(tokens).programa()


def despejar(no, nivel=0, saida=None):
    """Imprime a arvore no formato do --ast. Ja esta pronto: dois espacos por nivel."""
    saida = saida if saida is not None else []
    saida.append('  ' * nivel + no.rotulo)
    for f in no.filhos:
        despejar(f, nivel + 1, saida)
    return saida