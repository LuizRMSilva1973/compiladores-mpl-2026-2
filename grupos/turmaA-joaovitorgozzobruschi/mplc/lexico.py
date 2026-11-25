"""
entrega 1: analise lexica.

transforma o texto do programa numa lista de tokens.

o que sai daqui e uma lista de Token, e o ultimo e sempre um FIM_ARQUIVO.
a regra da posicao dele ta no CONTRATOS.md, secao 7.

ver LINGUAGEM.md secao 2 e CONTRATOS.md secao 2.
"""
from mplc.erros import ErroMPL


class Token:
    __slots__ = ('tipo', 'lexema', 'linha', 'coluna')

    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo          # 'ID', 'INTEIRO', 'MAIS', ... (a lista ta no contrato)
        self.lexema = lexema      # o texto exato, do jeito que apareceu no fonte
        self.linha = linha
        self.coluna = coluna      # coluna do PRIMEIRO caractere do token

    def __str__(self):
        # essa e a linha que o --tokens imprime, entao nao mexer no formato
        return f"{self.linha},{self.coluna},{self.tipo},{self.lexema}"


# palavra reservada nao pode ser identificador. 'sePossivel' nao cai aqui
# porque o identificador inteiro e lido antes de consultar a tabela.
PALAVRAS = {
    'funcao': 'FUNCAO',
    'retorne': 'RETORNE',
    'se': 'SE',
    'senao': 'SENAO',
    'enquanto': 'ENQUANTO',
    'escreva': 'ESCREVA',
    'inteiro': 'TIPO_INTEIRO',
    'real': 'TIPO_REAL',
    'logico': 'TIPO_LOGICO',
    'texto': 'TIPO_TEXTO',
    'vazio': 'TIPO_VAZIO',
    'verdadeiro': 'LOGICO',
    'falso': 'LOGICO',
    'e': 'E',
    'ou': 'OU',
    'nao': 'NAO',
}

# os operadores de dois caracteres vem PRIMEIRO. se testar '<' antes de '<=',
# "x <= 3" vira quatro tokens em vez de tres.
SIMBOLOS_DUPLOS = {
    '==': 'IGUAL',
    '!=': 'DIFERENTE',
    '<=': 'MENOR_IGUAL',
    '>=': 'MAIOR_IGUAL',
}

SIMBOLOS_SIMPLES = {
    '+': 'MAIS',
    '-': 'MENOS',
    '*': 'VEZES',
    '/': 'DIVIDE',
    '%': 'RESTO',
    '<': 'MENOR',
    '>': 'MAIOR',
    '=': 'ATRIBUI',
    '(': 'ABRE_PAR',
    ')': 'FECHA_PAR',
    '{': 'ABRE_CHAVE',
    '}': 'FECHA_CHAVE',
    ',': 'VIRGULA',
    ';': 'PONTO_VIRGULA',
}

ESCAPES_VALIDOS = {'n', 't', '"', '\\'}
ESPACOS = {' ', '\t', '\r', '\n'}


def _letra(ch):
    return 'a' <= ch <= 'z' or 'A' <= ch <= 'Z' or ch == '_'


def _digito(ch):
    return '0' <= ch <= '9'


def analisar(fonte):
    """recebe o texto do programa e devolve a lista de Token."""
    n = len(fonte)
    i = 0
    linha = 1
    coluna = 1
    tokens = []

    def olhar(k=0):
        j = i + k
        return fonte[j] if j < n else ''

    def avancar():
        nonlocal i, linha, coluna
        ch = fonte[i]
        i += 1
        if ch == '\n':
            linha += 1
            coluna = 1
        else:
            coluna += 1
        return ch

    def emitir(tipo, lexema, lin, col):
        tokens.append(Token(tipo, lexema, lin, col))

    def pular_bloco(inicio_linha, inicio_coluna):
        """consome um comentario /* ... */. o primeiro */ ja fecha, nao tem aninhamento."""
        while i < n:
            if olhar() == '*' and olhar(1) == '/':
                avancar()
                avancar()
                return
            avancar()
        raise ErroMPL(
            'lexico', inicio_linha, inicio_coluna,
            'comentario de bloco nao fechado',
        )

    def ler_texto(inicio_linha, inicio_coluna):
        """literal entre aspas, numa linha so. o lexema guarda as aspas e os escapes crus."""
        lexema = avancar()  # a aspa de abertura
        while True:
            if i >= n:
                raise ErroMPL(
                    'lexico', inicio_linha, inicio_coluna,
                    'texto nao fechado',
                )
            ch = olhar()
            if ch == '\n' or ch == '\r':
                raise ErroMPL(
                    'lexico', inicio_linha, inicio_coluna,
                    'texto nao fechado',
                )
            if ch == '"':
                lexema += avancar()
                return lexema
            if ch == '\\':
                barra_linha, barra_coluna = linha, coluna
                lexema += avancar()
                proximo = olhar()
                if proximo not in ESCAPES_VALIDOS:
                    raise ErroMPL(
                        'lexico', barra_linha, barra_coluna,
                        'escape invalido',
                    )
                lexema += avancar()
            else:
                lexema += avancar()

    def ler_numero(inicio_linha, inicio_coluna):
        lexema = ''
        while _digito(olhar()):
            lexema += avancar()
        if olhar() == '.':
            if not _digito(olhar(1)):
                raise ErroMPL(
                    'lexico', linha, coluna,
                    'numero real exige digito dos dois lados do ponto',
                )
            lexema += avancar()
            while _digito(olhar()):
                lexema += avancar()
            emitir('REAL', lexema, inicio_linha, inicio_coluna)
        else:
            emitir('INTEIRO', lexema, inicio_linha, inicio_coluna)

    def ler_palavra(inicio_linha, inicio_coluna):
        lexema = avancar()
        while _letra(olhar()) or _digito(olhar()):
            lexema += avancar()
        tipo = PALAVRAS.get(lexema, 'ID')
        emitir(tipo, lexema, inicio_linha, inicio_coluna)

    while i < n:
        ch = olhar()

        if ch in ESPACOS:
            avancar()
            continue

        if ch == '/' and olhar(1) == '/':
            while i < n and olhar() != '\n':
                avancar()
            continue

        if ch == '/' and olhar(1) == '*':
            ini_l, ini_c = linha, coluna
            avancar()
            avancar()
            pular_bloco(ini_l, ini_c)
            continue

        ini_l, ini_c = linha, coluna

        if ch == '"':
            lexema = ler_texto(ini_l, ini_c)
            emitir('TEXTO', lexema, ini_l, ini_c)
            continue

        if _letra(ch):
            ler_palavra(ini_l, ini_c)
            continue

        if _digito(ch):
            ler_numero(ini_l, ini_c)
            continue

        if ch == '.':
            raise ErroMPL(
                'lexico', ini_l, ini_c,
                'numero real exige digito dos dois lados do ponto',
            )

        par = ch + olhar(1)
        if par in SIMBOLOS_DUPLOS:
            avancar()
            avancar()
            emitir(SIMBOLOS_DUPLOS[par], par, ini_l, ini_c)
            continue

        if ch in SIMBOLOS_SIMPLES:
            avancar()
            emitir(SIMBOLOS_SIMPLES[ch], ch, ini_l, ini_c)
            continue

        raise ErroMPL(
            'lexico', ini_l, ini_c,
            f'caractere invalido {ch!r}',
        )

    emitir('FIM_ARQUIVO', '', linha, coluna)
    return tokens
