"""
entrega 2: analise sintatica.

transforma a lista de tokens numa arvore.

descida recursiva, uma funcao por nivel de precedencia, na ordem da secao
3.3 da especificacao. a gramatica completa em EBNF ta no README.md.

os niveis binarios sao lacos e nao recursao a direita: cada volta do laco
pendura a arvore montada ate ali como filho ESQUERDO do operador novo. e
isso que faz 10 - 4 - 3 virar (10 - 4) - 3. ja os unarios, que associam a
direita, chamam a si mesmos.

todo erro e apontado no token que apareceu no lugar do esperado, nunca no
fim do token anterior (CONTRATOS.md, secao 7).
"""
from mplc.erros import ErroMPL


class No:
    """um no da arvore. o rotulo e o que aparece no --ast."""

    def __init__(self, rotulo, filhos=None, linha=0, coluna=0, **extra):
        self.rotulo = rotulo      # 'binario +', 'literal inteiro 1', 'bloco', ...
        self.filhos = filhos or []
        self.linha = linha
        self.coluna = coluna
        self.extra = extra        # o que a semantica quiser pendurar depois


# tipos que uma variavel ou parametro pode ter. 'vazio' so vale como retorno
# de funcao (LINGUAGEM.md, secao 3), entao 'vazio x;' ja da erro de sintaxe.
TIPOS_VALOR = {
    'TIPO_INTEIRO': 'inteiro',
    'TIPO_REAL': 'real',
    'TIPO_LOGICO': 'logico',
    'TIPO_TEXTO': 'texto',
}
TIPOS_RETORNO = dict(TIPOS_VALOR, TIPO_VAZIO='vazio')

# um dicionario por nivel binario, do mais fraco pro mais forte.
# a chave e o tipo do token e o valor e o simbolo que vai no rotulo.
NIVEL_OU = {'OU': 'ou'}
NIVEL_E = {'E': 'e'}
NIVEL_IGUALDADE = {'IGUAL': '==', 'DIFERENTE': '!='}
NIVEL_RELACIONAL = {'MENOR': '<', 'MENOR_IGUAL': '<=', 'MAIOR': '>', 'MAIOR_IGUAL': '>='}
NIVEL_ADITIVO = {'MAIS': '+', 'MENOS': '-'}
NIVEL_MULTIPLICATIVO = {'VEZES': '*', 'DIVIDE': '/', 'RESTO': '%'}
NIVEL_UNARIO = {'NAO': 'nao', 'MENOS': '-'}


def _descrever(tok):
    """como o token aparece na mensagem de erro."""
    if tok.tipo == 'FIM_ARQUIVO':
        return 'o fim do arquivo'
    return f"'{tok.lexema}'"


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ------------------------------------------------------------ utilitarios

    @property
    def atual(self):
        return self.tokens[self.pos]

    def olhar(self, adiante=1):
        """o token 'adiante' posicoes depois do atual (sem passar do FIM_ARQUIVO)."""
        return self.tokens[min(self.pos + adiante, len(self.tokens) - 1)]

    def avancar(self):
        tok = self.atual
        if tok.tipo != 'FIM_ARQUIVO':
            self.pos += 1
        return tok

    def erro(self, esperado, tok=None):
        tok = tok or self.atual
        raise ErroMPL('sintatico', tok.linha, tok.coluna,
                      f'esperava {esperado}, mas veio {_descrever(tok)}')

    def exigir(self, tipo, esperado):
        if self.atual.tipo != tipo:
            self.erro(esperado)
        return self.avancar()

    def tipo(self, aceitos, esperado):
        """consome um nome de tipo e devolve do jeito que ele vai no rotulo."""
        if self.atual.tipo not in aceitos:
            self.erro(esperado)
        return aceitos[self.avancar().tipo]

    # --------------------------------------------------------------- programa

    def programa(self):
        funcoes = []
        while self.atual.tipo != 'FIM_ARQUIVO':
            funcoes.append(self.funcao())
        return No('programa', funcoes, 1, 1)

    def funcao(self):
        inicio = self.exigir('FUNCAO', "'funcao'")
        retorno = self.tipo(TIPOS_RETORNO, 'o tipo de retorno da funcao')
        nome = self.exigir('ID', 'o nome da funcao').lexema
        parametros = self.parametros()
        corpo = self.bloco()
        return No(f'funcao {nome} {retorno}', [parametros, corpo],
                  inicio.linha, inicio.coluna, nome=nome, tipo=retorno)

    def parametros(self):
        abre = self.exigir('ABRE_PAR', "'(' depois do nome da funcao")
        lista = []
        if self.atual.tipo != 'FECHA_PAR':
            lista.append(self.parametro())
            while self.atual.tipo == 'VIRGULA':
                self.avancar()
                lista.append(self.parametro())
        self.exigir('FECHA_PAR', "',' ou ')' na lista de parametros")
        return No('parametros', lista, abre.linha, abre.coluna)

    def parametro(self):
        inicio = self.atual
        tipo = self.tipo(TIPOS_VALOR, 'o tipo do parametro')
        nome = self.exigir('ID', 'o nome do parametro').lexema
        return No(f'parametro {nome} {tipo}', [], inicio.linha, inicio.coluna,
                  nome=nome, tipo=tipo)

    # --------------------------------------------------------------- comandos

    def bloco(self):
        abre = self.exigir('ABRE_CHAVE', "'{'")
        comandos = []
        while self.atual.tipo not in ('FECHA_CHAVE', 'FIM_ARQUIVO'):
            comandos.append(self.comando())
        self.exigir('FECHA_CHAVE', "'}' fechando o bloco")
        return No('bloco', comandos, abre.linha, abre.coluna)

    def comando(self):
        tok = self.atual
        if tok.tipo in TIPOS_VALOR:
            return self.declaracao()
        if tok.tipo == 'SE':
            return self.se()
        if tok.tipo == 'ENQUANTO':
            return self.enquanto()
        if tok.tipo == 'ESCREVA':
            return self.escreva()
        if tok.tipo == 'RETORNE':
            return self.retorne()
        if tok.tipo == 'ABRE_CHAVE':
            return self.bloco()
        if tok.tipo == 'ID':
            seguinte = self.olhar().tipo
            if seguinte == 'ATRIBUI':
                return self.atribuicao()
            if seguinte == 'ABRE_PAR':
                chamada = self.chamada()
                self.exigir('PONTO_VIRGULA', "';' depois da chamada")
                return chamada
            self.erro(f"'=' ou '(' depois de '{tok.lexema}'", self.olhar())
        self.erro('um comando')

    def declaracao(self):
        inicio = self.atual
        tipo = self.tipo(TIPOS_VALOR, 'um tipo')
        nome = self.exigir('ID', 'o nome da variavel').lexema
        filhos = []
        if self.atual.tipo == 'ATRIBUI':
            self.avancar()
            filhos.append(self.expressao())
        self.exigir('PONTO_VIRGULA', "';' no fim da declaracao")
        return No(f'declaracao {nome} {tipo}', filhos, inicio.linha, inicio.coluna,
                  nome=nome, tipo=tipo)

    def atribuicao(self):
        alvo = self.exigir('ID', 'o nome da variavel')
        self.exigir('ATRIBUI', "'='")
        valor = self.expressao()
        self.exigir('PONTO_VIRGULA', "';' no fim da atribuicao")
        return No(f'atribuicao {alvo.lexema}', [valor], alvo.linha, alvo.coluna,
                  nome=alvo.lexema)

    def condicao(self, comando):
        """o '( expressao )' do se e do enquanto."""
        self.exigir('ABRE_PAR', f"'(' depois de '{comando}'")
        cond = self.expressao()
        self.exigir('FECHA_PAR', "')' fechando a condicao")
        return cond

    def se(self):
        inicio = self.exigir('SE', "'se'")
        filhos = [self.condicao('se'), self.bloco()]
        if self.atual.tipo == 'SENAO':
            self.avancar()
            filhos.append(self.bloco())
        return No('se', filhos, inicio.linha, inicio.coluna)

    def enquanto(self):
        inicio = self.exigir('ENQUANTO', "'enquanto'")
        filhos = [self.condicao('enquanto'), self.bloco()]
        return No('enquanto', filhos, inicio.linha, inicio.coluna)

    def escreva(self):
        inicio = self.exigir('ESCREVA', "'escreva'")
        self.exigir('ABRE_PAR', "'(' depois de 'escreva'")
        valor = self.expressao()
        self.exigir('FECHA_PAR', "')' fechando o escreva")
        self.exigir('PONTO_VIRGULA', "';' depois do escreva")
        return No('escreva', [valor], inicio.linha, inicio.coluna)

    def retorne(self):
        inicio = self.exigir('RETORNE', "'retorne'")
        filhos = []
        if self.atual.tipo != 'PONTO_VIRGULA':
            filhos.append(self.expressao())
        self.exigir('PONTO_VIRGULA', "';' depois do retorne")
        return No('retorne', filhos, inicio.linha, inicio.coluna)

    # ------------------------------------------------------------ expressoes
    #
    # uma funcao por nivel, do mais fraco (ou) pro mais forte (primario).
    # cada nivel so enxerga o nivel logo abaixo dele.

    def expressao(self):
        return self.ou()

    def binario(self, operadores, proximo):
        """nivel binario associativo a esquerda: proximo (op proximo)*."""
        esquerda = proximo()
        while self.atual.tipo in operadores:
            op = self.avancar()
            direita = proximo()
            esquerda = No(f'binario {operadores[op.tipo]}', [esquerda, direita],
                          op.linha, op.coluna, op=operadores[op.tipo])
        return esquerda

    def ou(self):
        return self.binario(NIVEL_OU, self.e)

    def e(self):
        return self.binario(NIVEL_E, self.igualdade)

    def igualdade(self):
        return self.binario(NIVEL_IGUALDADE, self.relacional)

    def relacional(self):
        return self.binario(NIVEL_RELACIONAL, self.aditivo)

    def aditivo(self):
        return self.binario(NIVEL_ADITIVO, self.multiplicativo)

    def multiplicativo(self):
        return self.binario(NIVEL_MULTIPLICATIVO, self.unario)

    def unario(self):
        # associativo a direita: aqui sim a funcao chama ela mesma.
        if self.atual.tipo in NIVEL_UNARIO:
            op = self.avancar()
            operando = self.unario()
            return No(f'unario {NIVEL_UNARIO[op.tipo]}', [operando],
                      op.linha, op.coluna, op=NIVEL_UNARIO[op.tipo])
        return self.primario()

    def primario(self):
        tok = self.atual
        if tok.tipo == 'INTEIRO':
            self.avancar()
            return No(f'literal inteiro {int(tok.lexema)}', [], tok.linha, tok.coluna,
                      tipo='inteiro', valor=int(tok.lexema))
        if tok.tipo == 'REAL':
            self.avancar()
            valor = float(tok.lexema)
            return No(f'literal real {valor:.6f}', [], tok.linha, tok.coluna,
                      tipo='real', valor=valor)
        if tok.tipo == 'LOGICO':
            self.avancar()
            return No(f'literal logico {tok.lexema}', [], tok.linha, tok.coluna,
                      tipo='logico', valor=tok.lexema == 'verdadeiro')
        if tok.tipo == 'TEXTO':
            self.avancar()
            return No(f'literal texto {tok.lexema}', [], tok.linha, tok.coluna,
                      tipo='texto', valor=tok.lexema)
        if tok.tipo == 'ID':
            if self.olhar().tipo == 'ABRE_PAR':
                return self.chamada()
            self.avancar()
            return No(f'variavel {tok.lexema}', [], tok.linha, tok.coluna,
                      nome=tok.lexema)
        if tok.tipo == 'ABRE_PAR':
            # parenteses nao viram no, a forma da arvore ja guarda o agrupamento.
            self.avancar()
            dentro = self.expressao()
            self.exigir('FECHA_PAR', "')'")
            return dentro
        self.erro('uma expressao')

    def chamada(self):
        nome = self.exigir('ID', 'o nome da funcao')
        self.exigir('ABRE_PAR', "'('")
        argumentos = []
        if self.atual.tipo != 'FECHA_PAR':
            argumentos.append(self.expressao())
            while self.atual.tipo == 'VIRGULA':
                self.avancar()
                argumentos.append(self.expressao())
        self.exigir('FECHA_PAR', "',' ou ')' nos argumentos")
        return No(f'chamada {nome.lexema}', argumentos, nome.linha, nome.coluna,
                  nome=nome.lexema)


def analisar(tokens):
    """recebe a lista de Token e devolve a raiz da arvore (um No 'programa')."""
    return _Parser(tokens).programa()


def despejar(no, nivel=0, saida=None):
    """imprime a arvore no formato do --ast (essa ja veio pronta): dois espacos por nivel."""
    saida = saida if saida is not None else []
    saida.append('  ' * nivel + no.rotulo)
    for f in no.filhos:
        despejar(f, nivel + 1, saida)
    return saida
