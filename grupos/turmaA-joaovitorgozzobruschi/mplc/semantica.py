"""
entrega 3: analise semantica.

tabela de simbolos, escopos aninhados e verificacao de tipos.

tres coisas que e facil esquecer:
  - o corpo de uma funcao abre DOIS escopos (o dos parametros e o do bloco);
  - uma funcao pode ser chamada antes de aparecer no arquivo, entao a
    primeira passada so junta as assinaturas;
  - funcao com retorno declarado tem que garantir o retorno em TODOS os
    caminhos.

os escopos formam uma arvore de dicionarios encadeados: cada Escopo guarda
os proprios simbolos e aponta pro pai. procurar um nome e ir subindo pelos
pais ate achar, por isso a variavel de dentro esconde a de fora, e a de fora
volta sozinha quando o analisador sai do bloco e o escopo atual volta a ser
o pai. nenhum escopo e apagado quando fecha: a Tabela guarda todos, na ordem
em que abriram, pro --tabela e pra entrega 4.

o analisador tambem anota a arvore: cada expressao ganha extra['tipo'], cada
uso de nome ganha extra['simbolo'] (o Simbolo exato, com o sombreamento ja
resolvido) e cada funcao e bloco ganha extra['escopo'].

ver LINGUAGEM.md secoes 3 a 5 e CONTRATOS.md secao 4.
"""
from mplc.erros import ErroMPL


NUMERICOS = ('inteiro', 'real')
ARITMETICOS = ('+', '-', '*', '/')
RELACIONAIS = ('<', '<=', '>', '>=')
IGUALDADE = ('==', '!=')
LOGICOS = ('e', 'ou')


def cabe(origem, destino):
    """a unica conversao implicita da MPL: inteiro vira real (secao 3.1)."""
    return origem == destino or (origem == 'inteiro' and destino == 'real')


def _especie(no):
    """'binario +' -> 'binario', 'funcao f inteiro' -> 'funcao', ..."""
    return no.rotulo.split(' ', 1)[0]


class Simbolo:
    def __init__(self, nome, categoria, tipo, linha, parametros=None):
        self.nome = nome
        self.categoria = categoria    # 'funcao', 'parametro' ou 'variavel'
        self.tipo = tipo              # numa funcao, o tipo de retorno
        self.linha = linha
        self.parametros = parametros  # so funcao: a lista dos tipos dos parametros
        self.escopo = None            # preenchido por Escopo.declarar

    def tipo_no_despejo(self):
        if self.categoria == 'funcao':
            return f"{self.tipo}({','.join(self.parametros)})"
        return self.tipo


class Escopo:
    def __init__(self, numero, descricao, pai):
        self.numero = numero
        self.descricao = descricao    # 'global', 'funcao <nome>' ou 'bloco'
        self.pai = pai
        self.simbolos = {}            # nome -> Simbolo; o dict guarda a ordem de declaracao

    def declarar(self, simbolo):
        simbolo.escopo = self
        self.simbolos[simbolo.nome] = simbolo

    def buscar(self, nome):
        """sobe pelos pais ate achar. o primeiro que aparecer e o mais de dentro."""
        escopo = self
        while escopo is not None:
            if nome in escopo.simbolos:
                return escopo.simbolos[nome]
            escopo = escopo.pai
        return None


class Tabela:
    def __init__(self):
        self.escopos = []             # todos, na ordem em que abriram
        self.global_ = self.abrir('global', None)

    def abrir(self, descricao, pai):
        escopo = Escopo(len(self.escopos), descricao, pai)
        self.escopos.append(escopo)
        return escopo


class _Analisador:
    def __init__(self):
        self.tabela = Tabela()
        self.atual = self.tabela.global_
        self.funcao = None            # o Simbolo da funcao cujo corpo esta sendo visto

    def erro(self, no, mensagem):
        raise ErroMPL('semantico', no.linha, no.coluna, mensagem)

    # --------------------------------------------------------------- programa

    def programa(self, no):
        # primeira passada: so as assinaturas, pra que qualquer funcao possa
        # chamar qualquer outra, ate uma que aparece depois no arquivo.
        for funcao in no.filhos:
            self.assinatura(funcao)
        self.conferir_principal(no)

        # segunda passada: os corpos.
        for funcao in no.filhos:
            self.corpo(funcao)
        return self.tabela

    def assinatura(self, no):
        nome, parametros = no.extra['nome'], no.filhos[0].filhos
        anterior = self.tabela.global_.simbolos.get(nome)
        if anterior is not None:
            self.erro(no, f"a funcao '{nome}' ja foi declarada na linha {anterior.linha}")
        simbolo = Simbolo(nome, 'funcao', no.extra['tipo'], no.linha,
                          [p.extra['tipo'] for p in parametros])
        self.tabela.global_.declarar(simbolo)
        no.extra['simbolo'] = simbolo

    def conferir_principal(self, programa):
        principal = self.tabela.global_.simbolos.get('principal')
        if principal is None:
            self.erro(programa, "falta a funcao 'principal'")
        no = next(f for f in programa.filhos if f.extra['nome'] == 'principal')
        if principal.tipo != 'vazio':
            self.erro(no, f"'principal' tem que devolver vazio, nao {principal.tipo}")
        if principal.parametros:
            self.erro(no, "'principal' nao recebe parametros")

    def corpo(self, no):
        self.funcao = no.extra['simbolo']
        parametros, bloco = no.filhos

        # primeiro dos dois escopos do corpo: o dos parametros.
        self.atual = self.tabela.abrir(f"funcao {self.funcao.nome}", self.atual)
        no.extra['escopo'] = self.atual
        for p in parametros.filhos:
            self.declarar(p, 'parametro')

        # o segundo e o do bloco, que o proprio bloco abre.
        self.bloco(bloco)
        self.atual = self.atual.pai

        if self.funcao.tipo != 'vazio' and not _garante_retorno(bloco):
            self.erro(no, f"a funcao '{self.funcao.nome}' nem sempre retorna "
                          f"{self.funcao.tipo}: falta retorne em algum caminho")

    def declarar(self, no, categoria):
        nome = no.extra['nome']
        anterior = self.atual.simbolos.get(nome)
        if anterior is not None:
            self.erro(no, f"'{nome}' ja foi declarado neste escopo, na linha {anterior.linha}")
        simbolo = Simbolo(nome, categoria, no.extra['tipo'], no.linha)
        self.atual.declarar(simbolo)
        no.extra['simbolo'] = simbolo

    # --------------------------------------------------------------- comandos

    def bloco(self, no):
        self.atual = self.tabela.abrir('bloco', self.atual)
        no.extra['escopo'] = self.atual
        for comando in no.filhos:
            self.comando(comando)
        # fechar e so voltar pro pai, ai as variaveis de fora aparecem de novo.
        self.atual = self.atual.pai

    def comando(self, no):
        especie = _especie(no)
        if especie == 'declaracao':
            self.declaracao(no)
        elif especie == 'atribuicao':
            self.atribuicao(no)
        elif especie == 'se':
            self.condicao(no.filhos[0])
            self.bloco(no.filhos[1])
            if len(no.filhos) == 3:
                self.bloco(no.filhos[2])
        elif especie == 'enquanto':
            self.condicao(no.filhos[0])
            self.bloco(no.filhos[1])
        elif especie == 'escreva':
            self.expressao(no.filhos[0])
        elif especie == 'retorne':
            self.retorne(no)
        elif especie == 'chamada':
            # como comando, chamar uma funcao vazio pode.
            self.chamada(no)
        elif especie == 'bloco':
            self.bloco(no)

    def declaracao(self, no):
        nome, tipo = no.extra['nome'], no.extra['tipo']
        # o valor inicial e conferido ANTES de declarar: em 'inteiro x = x;'
        # o x da direita e o de fora, nao o que ta nascendo agora.
        if no.filhos:
            valor = self.expressao(no.filhos[0])
            if not cabe(valor, tipo):
                self.erro(no, f"'{nome}' e {tipo} e nao pode receber {valor}")
        self.declarar(no, 'variavel')

    def atribuicao(self, no):
        alvo = self.variavel(no)
        valor = self.expressao(no.filhos[0])
        if not cabe(valor, alvo.tipo):
            self.erro(no, f"'{alvo.nome}' e {alvo.tipo} e nao pode receber {valor}")

    def condicao(self, no):
        tipo = self.expressao(no)
        if tipo != 'logico':
            self.erro(no, f"a condicao tem que ser logico, mas e {tipo}")

    def retorne(self, no):
        esperado, nome = self.funcao.tipo, self.funcao.nome
        if esperado == 'vazio':
            if no.filhos:
                self.erro(no, f"'{nome}' e vazio e nao pode retornar valor")
            return
        if not no.filhos:
            self.erro(no, f"'{nome}' tem que retornar {esperado}")
        tipo = self.expressao(no.filhos[0])
        if not cabe(tipo, esperado):
            self.erro(no, f"'{nome}' retorna {esperado}, nao {tipo}")

    # ------------------------------------------------------------ expressoes

    def expressao(self, no):
        """confere a expressao e devolve o tipo dela (nunca 'vazio')."""
        especie = _especie(no)
        if especie == 'literal':
            tipo = no.extra['tipo']
        elif especie == 'variavel':
            tipo = self.variavel(no).tipo
        elif especie == 'chamada':
            tipo = self.chamada(no)
            if tipo == 'vazio':
                self.erro(no, f"'{no.extra['nome']}' e vazio e nao devolve valor "
                              f"para usar numa expressao")
        elif especie == 'unario':
            tipo = self.unario(no)
        else:
            tipo = self.binario(no)
        no.extra['tipo'] = tipo
        return tipo

    def variavel(self, no):
        """resolve o nome usado como variavel (num uso ou numa atribuicao)."""
        nome = no.extra['nome']
        simbolo = self.atual.buscar(nome)
        if simbolo is None:
            self.erro(no, f"'{nome}' nao foi declarado")
        if simbolo.categoria == 'funcao':
            self.erro(no, f"'{nome}' e uma funcao, nao uma variavel")
        no.extra['simbolo'] = simbolo
        return simbolo

    def chamada(self, no):
        """confere a chamada e devolve o tipo de retorno (pode ser 'vazio')."""
        nome, argumentos = no.extra['nome'], no.filhos
        funcao = self.atual.buscar(nome)
        if funcao is None:
            self.erro(no, f"a funcao '{nome}' nao existe")
        if funcao.categoria != 'funcao':
            self.erro(no, f"'{nome}' e {funcao.categoria} da linha {funcao.linha}, "
                          f"nao uma funcao")
        if len(argumentos) != len(funcao.parametros):
            self.erro(no, f"'{nome}' espera {len(funcao.parametros)} argumento(s), "
                          f"mas recebeu {len(argumentos)}")
        for i, (arg, esperado) in enumerate(zip(argumentos, funcao.parametros), 1):
            tipo = self.expressao(arg)
            if not cabe(tipo, esperado):
                self.erro(arg, f"o argumento {i} de '{nome}' tem que ser {esperado}, nao {tipo}")
        no.extra['simbolo'] = funcao
        no.extra['tipo'] = funcao.tipo
        return funcao.tipo

    def unario(self, no):
        op = no.extra['op']
        tipo = self.expressao(no.filhos[0])
        if op == 'nao' and tipo == 'logico':
            return 'logico'
        if op == '-' and tipo in NUMERICOS:
            return tipo
        self.erro(no, f"'{op}' nao se aplica a {tipo}")

    def binario(self, no):
        op = no.extra['op']
        esq = self.expressao(no.filhos[0])
        dir = self.expressao(no.filhos[1])
        numericos = esq in NUMERICOS and dir in NUMERICOS

        if op in LOGICOS and esq == dir == 'logico':
            return 'logico'
        if op in IGUALDADE and (cabe(esq, dir) or cabe(dir, esq)):
            return 'logico'
        if op in RELACIONAIS and numericos:
            return 'logico'
        if op == '%' and esq == dir == 'inteiro':
            return 'inteiro'
        if op == '+' and esq == dir == 'texto':
            return 'texto'
        if op in ARITMETICOS and numericos:
            return 'inteiro' if esq == dir == 'inteiro' else 'real'
        self.erro(no, f"'{op}' nao aceita {esq} e {dir}")


def _garante_retorno(no):
    """
    o comando garante retorno em todos os caminhos? so olha a estrutura,
    o compilador nunca avalia condicao. um se sem senao e um enquanto podem
    nao executar o corpo, entao nunca garantem, por mais obvia que pareca a
    condicao. um se/senao garante quando os dois lados garantem.
    """
    especie = _especie(no)
    if especie == 'retorne':
        return True
    if especie == 'bloco':
        return any(_garante_retorno(c) for c in no.filhos)
    if especie == 'se':
        return (len(no.filhos) == 3
                and _garante_retorno(no.filhos[1])
                and _garante_retorno(no.filhos[2]))
    return False


def analisar(arvore):
    """percorre a arvore, monta a tabela e confere os tipos. devolve a tabela."""
    return _Analisador().programa(arvore)


def despejar(tabela):
    """devolve as linhas do --tabela, no formato da secao 4 do contrato."""
    linhas = []
    for escopo in tabela.escopos:
        if escopo.pai is None:
            linhas.append(f'escopo {escopo.numero} {escopo.descricao}')
        else:
            linhas.append(f'escopo {escopo.numero} {escopo.descricao} pai {escopo.pai.numero}')
        for s in escopo.simbolos.values():
            linhas.append(f'  {s.nome}|{s.categoria}|{s.tipo_no_despejo()}|{s.linha}')
    return linhas
