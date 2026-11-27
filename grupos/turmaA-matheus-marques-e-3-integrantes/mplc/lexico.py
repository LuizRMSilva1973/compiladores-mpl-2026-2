"""
Entrega 1 — analise lexica.

Transformar o texto do programa numa lista de tokens.

O que voces tem que devolver: uma lista de Token. O ultimo elemento e sempre
um token FIM_ARQUIVO. A regra de posicao dela esta em CONTRATOS.md, secao 7.

Leiam antes: LINGUAGEM.md secao 2, e CONTRATOS.md secao 2.
"""
import sys
import re

class Token:
    __slots__ = ('tipo', 'lexema', 'linha', 'coluna')

    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo          # 'ID', 'INTEIRO', 'MAIS', ...
        self.lexema = lexema      # o texto exato como apareceu no fonte
        self.linha = linha
        self.coluna = coluna      # a coluna do PRIMEIRO caractere do token

    def __str__(self):
        return f"{self.linha},{self.coluna},{self.tipo},{self.lexema}"


def analisar(fonte):
    """Recebe o texto do programa. Devolve a lista de Token."""
    regras = [
        ('COMENTARIO_BLOCO', r'/\*[\s\S]*?\*/'),
        ('COMENTARIO_BLOCO_ERRO', r'/\*[\s\S]*'),
        ('COMENTARIO_LINHA', r'//.*'),
        ('LIT_REAL', r'\b\d+\.\d+\b'),
        ('LIT_INTEIRO', r'\b\d+\b'),
        ('LIT_TEXTO', r'"(?:\\.|[^"\n\\])*"'),
        ('LIT_TEXTO_ERRO_NL', r'"[^"\n]*\n'),
        ('LIT_TEXTO_ERRO', r'"[^"\n]*'),
        ('RESERVADA_FUNCAO', r'\bfuncao(?![A-Za-z0-9_])'),
        ('RESERVADA_RETORNE', r'\bretorne(?![A-Za-z0-9_])'),
        ('RESERVADA_SE', r'\bse(?![A-Za-z0-9_])'),
        ('RESERVADA_SENAO', r'\bsenao(?![A-Za-z0-9_])'),
        ('RESERVADA_ENQUANTO', r'\benquanto(?![A-Za-z0-9_])'),
        ('RESERVADA_ESCREVA', r'\bescreva(?![A-Za-z0-9_])'),
        ('TIPO_INTEIRO', r'\binteiro(?![A-Za-z0-9_])'),
        ('TIPO_REAL', r'\breal(?![A-Za-z0-9_])'),
        ('TIPO_LOGICO', r'\blogico(?![A-Za-z0-9_])'),
        ('TIPO_TEXTO', r'\btexto(?![A-Za-z0-9_])'),
        ('TIPO_VAZIO', r'\bvazio(?![A-Za-z0-9_])'),
        ('LOGICO_VALOR', r'\b(verdadeiro|falso)(?![A-Za-z0-9_])'),
        ('E', r'\be(?![A-Za-z0-9_])'),
        ('OU', r'\bou(?![A-Za-z0-9_])'),
        ('NAO', r'\bnao(?![A-Za-z0-9_])'),
        ('ID', r'\b[a-zA-Z_][a-zA-Z0-9_]*(?![A-Za-z0-9_])'),
        ('IGUAL', r'=='),
        ('DIFERENTE', r'!='),
        ('MENOR_IGUAL', r'<='),
        ('MAIOR_IGUAL', r'>='),
        ('ATRIBUI', r'='),
        ('MAIS', r'\+'),
        ('MENOS', r'-'),
        ('VEZES', r'\*'),
        ('DIVIDE', r'/'),
        ('RESTO', r'%'),
        ('MENOR', r'<'),
        ('MAIOR', r'>'),
        ('ABRE_PAR', r'\('),
        ('FECHA_PAR', r'\)'),
        ('ABRE_CHAVE', r'\{'),
        ('FECHA_CHAVE', r'\}'),
        ('VIRGULA', r','),
        ('PONTO_VIRGULA', r';'),
        ('NOVA_LINHA', r'\n'),
        ('ESPACO', r'[ \t\r]+'),
        ('ERRO_PONTO', r'\.\d+|\d+\.'),
        ('ERRO', r'.')
    ]

    regex_combinada = '|'.join(f'(?P<{nome}>{padrao})' for nome, padrao in regras)
    scanner = re.compile(regex_combinada)

    linha_atual = 1
    inicio_linha = 0
    tokens = []

    for match in scanner.finditer(fonte):
        tipo = match.lastgroup
        valor = match.group(tipo)
        coluna = (match.start() - inicio_linha) + 1

        if tipo == 'NOVA_LINHA':
            linha_atual += 1
            inicio_linha = match.end()
            continue
        elif tipo == 'ESPACO' or tipo == 'COMENTARIO_LINHA':
            continue
        elif tipo == 'COMENTARIO_BLOCO':
            quebras = valor.count('\n')
            if quebras > 0:
                linha_atual += quebras
                inicio_linha = match.start() + valor.rfind('\n') + 1
            continue
        elif tipo == 'COMENTARIO_BLOCO_ERRO':
            print(f"erro lexico: linha {linha_atual}, coluna {coluna}: comentario de bloco nao fechado", file=sys.stderr)
            sys.exit(1)
        elif tipo == 'LIT_TEXTO_ERRO_NL' or tipo == 'LIT_TEXTO_ERRO':
            print(f"erro lexico: linha {linha_atual}, coluna {coluna}: texto nao fechado", file=sys.stderr)
            sys.exit(1)
        elif tipo == 'LIT_TEXTO':
            i = 1
            while i < len(valor) - 1:
                if valor[i] == '\\':
                    if valor[i + 1] not in 'nt"\\':
                        print(f"erro lexico: linha {linha_atual}, coluna {coluna + i}: escape invalido", file=sys.stderr)
                        sys.exit(1)
                    i += 2
                else:
                    i += 1
        elif tipo == 'ERRO' or tipo == 'ERRO_PONTO':
            print(f"erro lexico: linha {linha_atual}, coluna {coluna}: caractere inesperado '{valor}'", file=sys.stderr)
            sys.exit(1)

        if tipo.startswith('RESERVADA_'):
            tipo_token = tipo.replace('RESERVADA_', '')
        elif tipo == 'LOGICO_VALOR':
            tipo_token = 'LOGICO'
        elif tipo.startswith('TIPO_'):
            tipo_token = tipo
        elif tipo == 'LIT_INTEIRO':
            tipo_token = 'INTEIRO'
        elif tipo == 'LIT_REAL':
            tipo_token = 'REAL'
        elif tipo == 'LIT_TEXTO':
            tipo_token = 'TEXTO'
        else:
            tipo_token = tipo

        tokens.append(Token(tipo_token, valor, linha_atual, coluna))

    tokens.append(Token('FIM_ARQUIVO', '', linha_atual, (len(fonte) - inicio_linha) + 1))
    return tokens