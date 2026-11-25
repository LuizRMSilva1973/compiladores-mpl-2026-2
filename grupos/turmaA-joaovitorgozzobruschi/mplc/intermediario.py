"""
entrega 4, primeira metade: codigo de tres enderecos.

a propriedade que define essa representacao (e a unica que o verificador
mede): cada linha de operacao tem NO MAXIMO UM OPERADOR. entao uma expressao
tipo a + b * c vira duas linhas, com um temporario no meio.

como a traducao funciona: cada expressao devolve um OPERANDO, que pode ser
uma constante, o nome de uma variavel ou um temporario novo. um no binario
pega o operando de cada filho e grava o resultado num temporario dele, e
assim a arvore vira uma sequencia de linhas com um operador cada, de baixo
pra cima.

tres decisoes que facilitam a vida da VM:

  - a conversao inteiro -> real e EXPLICITA (`t1 = real t0`) e so acontece
    onde a semantica diz que o contexto precisa de real. em `real x = 7 / 2;`
    a divisao e entre dois inteiros, entao vira `t0 = 7 / 2` (inteira, da 3)
    e so DEPOIS `t1 = real t0`. por isso a VM consegue decidir a divisao pelo
    tipo dos valores que chegam: se veio inteiro dos dois lados, e inteira.
  - cada Simbolo vira um nome unico dentro da funcao. os tres `x` sombreados
    do 06-escopo viram `x`, `x.4` e `x.5` (o numero e o do escopo). como
    ponto nao existe em identificador da MPL, nao colide com nada do fonte.
  - declarar ja atribui: `inteiro x;` vira `x = 0`. dentro de um enquanto
    isso reinicia a variavel a cada volta, que e o que a especificacao pede.

cada instrucao guarda a linha do COMANDO que gerou ela, pro erro de execucao
(CONTRATOS.md secao 7).

ver CONTRATOS.md secao 5.
"""
import re
from decimal import Decimal


PADRAO = {'inteiro': 0, 'real': 0.0, 'logico': False, 'texto': ''}


# ------------------------------------------------------------------ operandos
#
# um operando e uma tupla pequena:
#   ('const', valor_python, texto_original)  -- 3, 2.5, verdadeiro, "oi\n"
#   ('nome', 'x.4')                          -- variavel, parametro ou temporario

def const(valor, original=None):
    return ('const', valor, original)


def nome(n):
    return ('nome', n)


def escrever_operando(op):
    if op[0] == 'nome':
        return op[1]
    _, valor, original = op
    if original is not None:
        return original
    if isinstance(valor, str):            # o "" do texto sem inicializar
        return '"' + valor.replace('\\', '\\\\').replace('"', '\\"') \
                          .replace('\n', '\\n').replace('\t', '\\t') + '"'
    if isinstance(valor, bool):
        return 'verdadeiro' if valor else 'falso'
    if isinstance(valor, float):
        # sempre no formato 0.00001, nunca 1e-05: o '-' do expoente ia contar
        # como operador, e o .mplb tambem fica mais facil de ler assim.
        texto = format(Decimal(repr(valor)), 'f')
        return texto if '.' in texto else texto + '.0'
    return str(valor)


_ESCAPES = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}


def decodificar_texto(lexema):
    """'"a\\nb"' -> 'a<quebra>b'. o lexico ja garantiu que so tem escape valido."""
    return re.sub(r'\\(.)', lambda m: _ESCAPES[m.group(1)], lexema[1:-1])


# ---------------------------------------------------------------- instrucoes

class Instrucao:
    """
    uma linha do codigo de tres enderecos. o `op` diz a forma:

      copia     destino = a
      binario   destino = a <oper> b
      unario    destino = <oper> a          (oper e '-' ou 'nao')
      real      destino = real a            (a conversao inteiro -> real)
      rotulo    L0:
      desvie    desvie L0
      seFalso   seFalso a desvie L0
      param     param a
      chama     [destino =] chama f, n
      retorne   retorne [a]
      escreva   escreva a
    """

    def __init__(self, op, linha, destino=None, a=None, b=None, oper=None, alvo=None, n=0):
        self.op = op
        self.linha = linha
        self.destino = destino    # nome (str) ou None
        self.a = a                # operando
        self.b = b                # operando
        self.oper = oper          # '+', '<=', 'nao', ...
        self.alvo = alvo          # rotulo (desvios) ou nome da funcao (chama)
        self.n = n                # quantos argumentos (chama)

    def __str__(self):
        a = escrever_operando(self.a) if self.a is not None else None
        b = escrever_operando(self.b) if self.b is not None else None
        d = self.destino
        if self.op == 'copia':
            return f'  {d} = {a}'
        if self.op == 'binario':
            return f'  {d} = {a} {self.oper} {b}'
        if self.op == 'unario':
            return f'  {d} = {self.oper} {a}'
        if self.op == 'real':
            return f'  {d} = real {a}'
        if self.op == 'rotulo':
            return f'{self.alvo}:'
        if self.op == 'desvie':
            return f'  desvie {self.alvo}'
        if self.op == 'seFalso':
            return f'  seFalso {a} desvie {self.alvo}'
        if self.op == 'param':
            return f'  param {a}'
        if self.op == 'chama':
            chamada = f'chama {self.alvo}, {self.n}'
            return f'  {d} = {chamada}' if d else f'  {chamada}'
        if self.op == 'retorne':
            return f'  retorne {a}' if a else '  retorne'
        if self.op == 'escreva':
            return f'  escreva {a}'
        raise ValueError(self.op)


class Funcao:
    def __init__(self, nome, tipo, parametros):
        self.nome = nome
        self.tipo = tipo                  # tipo de retorno
        self.parametros = parametros      # [(nome_no_ir, tipo)]
        self.instrucoes = []


class Codigo:
    def __init__(self):
        self.funcoes = []


# ------------------------------------------------------------------ o tradutor

def _especie(no):
    return no.rotulo.split(' ', 1)[0]


class _Tradutor:
    def __init__(self):
        self.rotulos = 0              # numeracao global: L0, L1, ... nao repetem entre funcoes

    # ----------------------------------------------------------------- funcao

    def funcao(self, no):
        simbolo = no.extra['simbolo']
        parametros, bloco = no.filhos
        self.temporarios = 0
        self.nomes = {}               # Simbolo -> nome no IR
        self.usados = set()
        self.linha = no.linha

        params = [(self.nome_de(p.extra['simbolo']), p.extra['tipo']) for p in parametros.filhos]
        self.atual = Funcao(simbolo.nome, simbolo.tipo, params)
        self.comando(bloco)

        # funcao vazio pode terminar sem retorne. as outras a semantica ja
        # garantiu que retornam em todos os caminhos.
        ultima = self.atual.instrucoes[-1] if self.atual.instrucoes else None
        if simbolo.tipo == 'vazio' and (ultima is None or ultima.op != 'retorne'):
            self.emitir('retorne', linha=self._linha_final(bloco))
        return self.atual

    @staticmethod
    def _linha_final(bloco):
        return bloco.filhos[-1].linha if bloco.filhos else bloco.linha

    def nome_de(self, simbolo):
        """um nome unico na funcao pra cada Simbolo (e assim resolve o sombreamento)."""
        if simbolo not in self.nomes:
            n = simbolo.nome
            if n in self.usados or re.fullmatch(r't\d+', n):
                n = f'{simbolo.nome}.{simbolo.escopo.numero}'
            self.usados.add(n)
            self.nomes[simbolo] = n
        return self.nomes[simbolo]

    # ------------------------------------------------------------- utilitarios

    def emitir(self, op, linha=None, **campos):
        self.atual.instrucoes.append(Instrucao(op, linha or self.linha, **campos))

    def temporario(self):
        t = f't{self.temporarios}'
        self.temporarios += 1
        return t

    def rotulo(self):
        r = f'L{self.rotulos}'
        self.rotulos += 1
        return r

    def converter(self, operando, de, para):
        """aplica a unica conversao implicita, se o contexto pedir."""
        if de == 'inteiro' and para == 'real':
            if operando[0] == 'const':           # constante: converte ja aqui
                return const(float(operando[1]))
            t = self.temporario()
            self.emitir('real', destino=t, a=operando)
            return nome(t)
        return operando

    # --------------------------------------------------------------- comandos

    def comando(self, no):
        especie = _especie(no)
        self.linha = no.linha

        if especie == 'bloco':
            for c in no.filhos:
                self.comando(c)

        elif especie == 'declaracao':
            simbolo = no.extra['simbolo']
            if no.filhos:
                valor = self.valor_para(no.filhos[0], simbolo.tipo)
            else:
                valor = const(PADRAO[simbolo.tipo])
            # o nome so nasce depois do valor: em 'inteiro x = x;' o x da
            # direita e o de fora (a semantica ja resolveu assim).
            self.emitir('copia', destino=self.nome_de(simbolo), a=valor)

        elif especie == 'atribuicao':
            simbolo = no.extra['simbolo']
            valor = self.valor_para(no.filhos[0], simbolo.tipo)
            self.emitir('copia', destino=self.nome_de(simbolo), a=valor)

        elif especie == 'se':
            senao, fim = self.rotulo(), None
            cond = self.expressao(no.filhos[0])
            self.emitir('seFalso', a=cond, alvo=senao)
            self.comando(no.filhos[1])
            if len(no.filhos) == 3:
                fim = self.rotulo()
                self.emitir('desvie', linha=no.linha, alvo=fim)
            self.emitir('rotulo', linha=no.linha, alvo=senao)
            if fim:
                self.comando(no.filhos[2])
                self.emitir('rotulo', linha=no.linha, alvo=fim)

        elif especie == 'enquanto':
            inicio, fim = self.rotulo(), self.rotulo()
            self.emitir('rotulo', alvo=inicio)
            cond = self.expressao(no.filhos[0])
            self.emitir('seFalso', linha=no.linha, a=cond, alvo=fim)
            self.comando(no.filhos[1])
            self.emitir('desvie', linha=no.linha, alvo=inicio)
            self.emitir('rotulo', linha=no.linha, alvo=fim)

        elif especie == 'escreva':
            self.emitir('escreva', a=self.expressao(no.filhos[0]))

        elif especie == 'retorne':
            if no.filhos:
                self.emitir('retorne', a=self.valor_para(no.filhos[0], self.atual.tipo))
            else:
                self.emitir('retorne')

        elif especie == 'chamada':
            # chamada como comando. se a funcao devolve algo, o valor vai pra um
            # temporario que ninguem le, mas pelo menos a pilha da VM fica limpa.
            self.chamada(no, usar_valor=no.extra['tipo'] != 'vazio')

    def valor_para(self, expr, tipo):
        """a expressao, ja convertida pra caber em `tipo`."""
        return self.converter(self.expressao(expr), expr.extra['tipo'], tipo)

    # ------------------------------------------------------------ expressoes

    def expressao(self, no):
        """gera o codigo da expressao e devolve o operando com o resultado."""
        especie = _especie(no)

        if especie == 'literal':
            tipo, valor = no.extra['tipo'], no.extra['valor']
            if tipo == 'texto':
                return const(decodificar_texto(valor), valor)
            return const(valor)

        if especie == 'variavel':
            return nome(self.nome_de(no.extra['simbolo']))

        if especie == 'chamada':
            return self.chamada(no, usar_valor=True)

        if especie == 'unario':
            a = self.expressao(no.filhos[0])
            t = self.temporario()
            self.emitir('unario', destino=t, oper=no.extra['op'], a=a)
            return nome(t)

        # binario
        esq, dir = no.filhos
        a, b = self.expressao(esq), self.expressao(dir)
        te, td = esq.extra['tipo'], dir.extra['tipo']
        if {te, td} == {'inteiro', 'real'}:      # aritmetico, relacional ou ==
            a = self.converter(a, te, 'real')
            b = self.converter(b, td, 'real')
        t = self.temporario()
        self.emitir('binario', destino=t, a=a, oper=no.extra['op'], b=b)
        return nome(t)

    def chamada(self, no, usar_valor):
        funcao = no.extra['simbolo']
        # primeiro gera TODOS os argumentos, depois os param: assim uma chamada
        # dentro de um argumento termina antes da pilha comecar a encher.
        args = [self.converter(self.expressao(arg), arg.extra['tipo'], esperado)
                for arg, esperado in zip(no.filhos, funcao.parametros)]
        for a in args:
            self.emitir('param', a=a)
        destino = self.temporario() if usar_valor else None
        self.emitir('chama', destino=destino, alvo=funcao.nome, n=len(args))
        return nome(destino) if destino else None


def gerar(arvore, tabela):
    """devolve o codigo de tres enderecos (um Codigo, com uma Funcao pra cada funcao do fonte)."""
    tradutor = _Tradutor()
    codigo = Codigo()
    for no in arvore.filhos:
        codigo.funcoes.append(tradutor.funcao(no))
    return codigo


def despejar(codigo):
    """devolve as linhas do --ir."""
    linhas = []
    for f in codigo.funcoes:
        params = ', '.join(f'{n} {t}' for n, t in f.parametros)
        linhas.append(f'funcao {f.nome} {f.tipo} ({params})')
        linhas.extend(str(i) for i in f.instrucoes)
        linhas.append('fim')
        linhas.append('')
    return linhas[:-1]
