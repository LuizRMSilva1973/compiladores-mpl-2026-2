"""
entrega 4, terceira metade (sim, sao tres): a maquina virtual.

le o .mplb e executa. e uma maquina de pilha com REGISTRO DE ATIVACAO:

  - cada chamada empilha um Registro novo, com as posicoes (locais) dela, a
    pilha de operandos dela e o contador de programa (pc) dela. o ponto de
    volta e o pc guardado no registro de quem chamou, que fica parado la
    embaixo ate o RETORNA desempilhar o de cima;
  - e por isso que a recursao funciona: fatorial(5) e fatorial(4) tem cada
    um o seu `n`, em registros diferentes. se os locais fossem globais da VM,
    a chamada de dentro ia pisar no `n` da de fora;
  - o laco principal e ITERATIVO (a VM nao usa a recursao do Python pras
    chamadas da MPL), entao o estouro de pilha e uma regra nossa
    (LIMITE_CHAMADAS), apontado na linha da chamada, com codigo de saida 2.

divisao e resto por zero tambem sao erro de execucao, na linha do comando.

o conjunto de instrucoes, uma por linha, ta no README.md.
"""
import re

from mplc.erros import ErroMPL
from mplc.intermediario import decodificar_texto


LIMITE_CHAMADAS = 10000

_TEXTO = re.compile(r'"(?:\\.|[^"\\])*"')


# --------------------------------------------------------------------- leitura

class FuncaoVM:
    def __init__(self, nome, parametros, posicoes):
        self.nome = nome
        self.parametros = parametros
        self.posicoes = posicoes
        self.codigo = []          # [(INSTRUCAO, argumento, linha do fonte)]
        self.rotulos = {}         # rotulo -> indice em codigo


def _constante(texto):
    if texto.startswith('"'):
        return decodificar_texto(texto)
    if texto == 'verdadeiro':
        return True
    if texto == 'falso':
        return False
    if '.' in texto:
        return float(texto)
    return int(texto)


def _argumento(resto):
    """o argumento de uma instrucao (o que vem antes do ; de comentario)."""
    resto = resto.strip()
    if resto.startswith('"'):
        return _TEXTO.match(resto).group(0)
    resto = resto.split(';', 1)[0].strip()
    return resto or None


def carregar(texto):
    funcoes, atual = {}, None
    for bruta in texto.splitlines():
        linha = bruta.strip()
        if not linha or linha.startswith(';'):
            continue
        if linha.startswith('.funcao'):
            _, nome, np, nl = linha.split()[:4]
            atual = funcoes[nome] = FuncaoVM(nome, int(np), int(nl))
        elif linha.startswith('.local'):
            pass
        elif linha.startswith('.fim'):
            atual = None
        elif linha.endswith(':') and ' ' not in linha:
            atual.rotulos[linha[:-1]] = len(atual.codigo)
        else:
            num, instr, *resto = linha.split(None, 2)
            arg = _argumento(resto[0]) if resto else None
            if instr == 'EMPILHA':
                arg = _constante(arg)
            elif instr in ('CARREGA', 'GUARDA'):
                arg = int(arg)
            atual.codigo.append((instr, arg, int(num)))

    # resolve os rotulos pra indices uma vez so, antes de rodar.
    for f in funcoes.values():
        f.codigo = [(i, f.rotulos[a] if i in ('DESVIA', 'DESVIA_SE_FALSO') else a, n)
                    for i, a, n in f.codigo]
    return funcoes


# ------------------------------------------------------------------- execucao

class Registro:
    """o registro de ativacao de uma chamada."""
    __slots__ = ('funcao', 'locais', 'pilha', 'pc')

    def __init__(self, funcao, argumentos):
        self.funcao = funcao
        self.locais = argumentos + [None] * (funcao.posicoes - len(argumentos))
        self.pilha = []
        self.pc = 0


def _inteiros(a, b):
    return type(a) is int and type(b) is int


def _div_inteira(a, b):
    """truncada em direcao ao zero (o // do Python arredonda pra baixo)."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def formatar(v):
    if isinstance(v, bool):
        return 'verdadeiro' if v else 'falso'
    if isinstance(v, float):
        return f'{v:.6f}'
    return str(v)


def executar(texto_mplb, saida):
    """executa o bytecode e escreve o que o programa imprimir em `saida`."""
    funcoes = carregar(texto_mplb)
    if 'principal' not in funcoes:
        raise ErroMPL('execucao', 1, 1, "o .mplb nao tem a funcao 'principal'")

    def erro(linha, mensagem):
        raise ErroMPL('execucao', linha, 1, mensagem)

    chamadas = [Registro(funcoes['principal'], [])]
    reg = chamadas[0]
    codigo, pilha, locais = reg.funcao.codigo, reg.pilha, reg.locais

    while True:
        if reg.pc >= len(codigo):            # caiu do fim: retorno implicito
            instr, arg, linha = 'RETORNA', None, 0
        else:
            instr, arg, linha = codigo[reg.pc]
        reg.pc += 1

        if instr == 'CARREGA':
            pilha.append(locais[arg])
        elif instr == 'GUARDA':
            locais[arg] = pilha.pop()
        elif instr == 'EMPILHA':
            pilha.append(arg)

        elif instr in ('SOMA', 'SUBTRAI', 'MULTIPLICA', 'DIVIDE', 'RESTO',
                       'IGUAL', 'DIFERENTE', 'MENOR', 'MENOR_IGUAL',
                       'MAIOR', 'MAIOR_IGUAL', 'E', 'OU'):
            b = pilha.pop()
            a = pilha.pop()
            if instr == 'SOMA':
                r = a + b
            elif instr == 'SUBTRAI':
                r = a - b
            elif instr == 'MULTIPLICA':
                r = a * b
            elif instr == 'DIVIDE':
                if b == 0:
                    erro(linha, 'divisao por zero')
                r = _div_inteira(a, b) if _inteiros(a, b) else a / b
            elif instr == 'RESTO':
                if b == 0:
                    erro(linha, 'resto de divisao por zero')
                r = a - b * _div_inteira(a, b)     # sinal do dividendo
            elif instr == 'IGUAL':
                r = a == b
            elif instr == 'DIFERENTE':
                r = a != b
            elif instr == 'MENOR':
                r = a < b
            elif instr == 'MENOR_IGUAL':
                r = a <= b
            elif instr == 'MAIOR':
                r = a > b
            elif instr == 'MAIOR_IGUAL':
                r = a >= b
            elif instr == 'E':
                r = a and b
            else:
                r = a or b
            pilha.append(r)

        elif instr == 'NEGA':
            pilha.append(-pilha.pop())
        elif instr == 'NAO':
            pilha.append(not pilha.pop())
        elif instr == 'PARA_REAL':
            pilha.append(float(pilha.pop()))

        elif instr == 'DESVIA':
            reg.pc = arg
        elif instr == 'DESVIA_SE_FALSO':
            if not pilha.pop():
                reg.pc = arg

        elif instr == 'ESCREVA':
            saida.write(formatar(pilha.pop()) + '\n')

        elif instr == 'CHAMA':
            funcao = funcoes[arg]
            if len(chamadas) >= LIMITE_CHAMADAS:
                erro(linha, f"estouro de pilha: mais de {LIMITE_CHAMADAS} chamadas "
                            f"aninhadas (chamando '{arg}')")
            n = funcao.parametros
            argumentos = pilha[len(pilha) - n:] if n else []
            del pilha[len(pilha) - n:]
            reg = Registro(funcao, argumentos)
            chamadas.append(reg)
            codigo, pilha, locais = funcao.codigo, reg.pilha, reg.locais

        elif instr in ('RETORNA', 'RETORNA_VALOR'):
            valor = pilha.pop() if instr == 'RETORNA_VALOR' else None
            chamadas.pop()
            if not chamadas:
                return
            reg = chamadas[-1]
            codigo, pilha, locais = reg.funcao.codigo, reg.pilha, reg.locais
            if instr == 'RETORNA_VALOR':
                pilha.append(valor)

        else:
            erro(linha, f"instrucao desconhecida no .mplb: '{instr}'")
