"""
Entrega 1 — analise lexica.

Transformar o texto do programa numa lista de tokens.

O que voces tem que devolver: uma lista de Token. O ultimo elemento e sempre
um token FIM_ARQUIVO. A regra de posicao dele esta em CONTRATOS.md, secao 7.

Leiam antes: LINGUAGEM.md secao 2, e CONTRATOS.md secao 2.
"""
from mplc.erros import ErroMPL


PALAVRAS_RESERVADAS = {
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


class Token:
    __slots__ = ('tipo', 'lexema', 'linha', 'coluna')

    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo
        self.lexema = lexema
        self.linha = linha
        self.coluna = coluna

    def __str__(self):
        return f"{self.linha},{self.coluna},{self.tipo},{self.lexema}"


def analisar(fonte):
    """Recebe o texto do programa. Devolve a lista de Token."""

    tokens = []

    i = 0
    linha = 1
    coluna = 1

    while i < len(fonte):

        c = fonte[i]

        if c in ' \t\r\n':
            if c == '\n':
                linha += 1
                coluna = 1
            else:
                coluna += 1

            i += 1
            continue

        inicio_linha = linha
        inicio_coluna = coluna


        if fonte.startswith('//', i):
            i += 2
            coluna += 2

            while i < len(fonte) and fonte[i] != '\n':
                i += 1
                coluna += 1

            continue

        if fonte.startswith('/*', i):
            linha_inicio_comentario = linha
            coluna_inicio_comentario = coluna

            i += 2
            coluna += 2

            fechado = False

            while i < len(fonte):

                if fonte.startswith('*/', i):
                    i += 2
                    coluna += 2
                    fechado = True
                    break

                if fonte[i] == '\n':
                    i += 1
                    linha += 1
                    coluna = 1
                else:
                    i += 1
                    coluna += 1

            if not fechado:
                raise ErroMPL(
                    'lexico',
                    linha_inicio_comentario,
                    coluna_inicio_comentario,
                    'comentario de bloco nao fechado'
                )

            continue

        if c.isalpha() or c == '_':
            inicio = i

            while i < len(fonte) and (
                fonte[i].isalnum() or fonte[i] == '_'
            ):
                i += 1
                coluna += 1

            lexema = fonte[inicio:i]

            tipo = PALAVRAS_RESERVADAS.get(lexema, 'ID')

            tokens.append(
                Token(
                    tipo,
                    lexema,
                    inicio_linha,
                    inicio_coluna
                )
            )

            continue

        if c.isdigit():

            inicio = i

            while i < len(fonte) and fonte[i].isdigit():
                i += 1
                coluna += 1


            if i < len(fonte) and fonte[i] == '.':


                if i + 1 >= len(fonte) or not fonte[i + 1].isdigit():
                    raise ErroMPL(
                        'lexico',
                        linha,
                        coluna,
                        'numero real invalido'
                    )

                i += 1
                coluna += 1

                while i < len(fonte) and fonte[i].isdigit():
                    i += 1
                    coluna += 1

                lexema = fonte[inicio:i]

                tokens.append(
                    Token(
                        'REAL',
                        lexema,
                        inicio_linha,
                        inicio_coluna
                    )
                )

            else:
                lexema = fonte[inicio:i]

                tokens.append(
                    Token(
                        'INTEIRO',
                        lexema,
                        inicio_linha,
                        inicio_coluna
                    )
                )

            continue


        if c == '"':

            inicio = i

            i += 1
            coluna += 1

            fechado = False

            while i < len(fonte):

                c_atual = fonte[i]

                if c_atual == '\n':
                    raise ErroMPL(
                        'lexico',
                        inicio_linha,
                        inicio_coluna,
                        'texto nao pode atravessar linhas'
                    )


                if c_atual == '"':
                    i += 1
                    coluna += 1
                    fechado = True
                    break


                if c_atual == '\\':

                    if i + 1 >= len(fonte):
                        raise ErroMPL(
                            'lexico',
                            linha,
                            coluna,
                            'escape invalido'
                        )

                    escape = fonte[i + 1]

                    if escape not in ('n', 't', '"', '\\'):
                        raise ErroMPL(
                            'lexico',
                            linha,
                            coluna,
                            'escape invalido'
                        )

                    i += 2
                    coluna += 2
                    continue

                i += 1
                coluna += 1

            if not fechado:
                raise ErroMPL(
                    'lexico',
                    inicio_linha,
                    inicio_coluna,
                    'texto nao fechado'
                )

            lexema = fonte[inicio:i]

            tokens.append(
                Token(
                    'TEXTO',
                    lexema,
                    inicio_linha,
                    inicio_coluna
                )
            )

            continue

        operadores_duplos = {
            '==': 'IGUAL',
            '!=': 'DIFERENTE',
            '<=': 'MENOR_IGUAL',
            '>=': 'MAIOR_IGUAL',
        }

        encontrou_duplo = False

        for simbolo, tipo in operadores_duplos.items():

            if fonte.startswith(simbolo, i):

                tokens.append(
                    Token(
                        tipo,
                        simbolo,
                        inicio_linha,
                        inicio_coluna
                    )
                )

                i += 2
                coluna += 2

                encontrou_duplo = True
                break

        if encontrou_duplo:
            continue

        operadores = {
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

        if c in operadores:

            tokens.append(
                Token(
                    operadores[c],
                    c,
                    inicio_linha,
                    inicio_coluna
                )
            )

            i += 1
            coluna += 1

            continue

        raise ErroMPL(
            'lexico',
            linha,
            coluna,
            f'caractere invalido: {c}'
        )

    tokens.append(
        Token(
            'FIM_ARQUIVO',
            '',
            linha,
            coluna
        )
    )

    return tokens