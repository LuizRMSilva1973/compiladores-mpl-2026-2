"""Interpretador iterativo com pilha e registro de ativacao por chamada."""
import json
import operator

from mplc.erros import ErroMPL


BINARIOS = {'+': operator.add, '-': operator.sub, '*': operator.mul,
            '==': operator.eq, '!=': operator.ne, '<': operator.lt,
            '<=': operator.le, '>': operator.gt, '>=': operator.ge,
            'e': operator.and_, 'ou': operator.or_}


def binario(op, a, b):
    if op in ('/', '%'):
        if b == 0:
            raise ZeroDivisionError
        if type(a) is int and type(b) is int:
            quociente = abs(a) // abs(b)
            if (a < 0) != (b < 0):
                quociente = -quociente
            return quociente if op == '/' else a - quociente * b
        return a / b
    return BINARIOS[op](a, b)


def executar(texto_mplb, saida):
    codigo, funcoes, rotulos = [], {}, {}
    for texto in texto_mplb.splitlines():
        if not texto.strip() or texto.startswith('#'):
            continue
        op, args = texto.split(' ', 1)
        args = json.loads(args)
        if op == 'FUNC':
            funcoes[args[0]] = (len(codigo) + 1, args[1])
        elif op == 'LABEL':
            rotulos[args[0]] = len(codigo) + 1
        codigo.append((op, args))

    pc = funcoes['principal'][0]
    locais, pilha, chamadas = {}, [], []
    linha, coluna = 1, 1
    while True:
        op, args = codigo[pc]
        pc += 1
        try:
            if op == 'POS':
                linha, coluna = args
            elif op == 'PUSH':
                pilha.append(args[0])
            elif op == 'LOAD':
                pilha.append(locais[args[0]])
            elif op == 'STORE':
                locais[args[0]] = pilha.pop()
            elif op == 'REAL':
                pilha.append(float(pilha.pop()))
            elif op == 'BINARY':
                b, a = pilha.pop(), pilha.pop()
                pilha.append(binario(args[0], a, b))
            elif op == 'UNARY':
                valor = pilha.pop()
                pilha.append(not valor if args[0] == 'nao' else -valor)
            elif op == 'JMP':
                pc = rotulos[args[0]]
            elif op == 'JZ':
                if not pilha.pop():
                    pc = rotulos[args[0]]
            elif op == 'CALL':
                if len(chamadas) >= 1000:
                    raise ErroMPL('execucao', linha, coluna, 'estouro de pilha')
                destino, parametros = funcoes[args[0]]
                valores = [pilha.pop() for _ in range(args[1])][::-1]
                chamadas.append((pc, locais, len(pilha), linha, coluna))
                locais = dict(zip(parametros, valores))
                pc = destino
            elif op == 'RET':
                valor = pilha.pop()
                if not chamadas:
                    return
                pc, locais, base, linha, coluna = chamadas.pop()
                del pilha[base:]
                pilha.append(valor)
            elif op == 'PRINT':
                valor = pilha.pop()
                if type(valor) is bool:
                    texto = 'verdadeiro' if valor else 'falso'
                elif type(valor) is float:
                    texto = format(valor, '.6f')
                else:
                    texto = str(valor)
                saida.write(texto + '\n')
            elif op not in ('LABEL', 'FUNC', 'END'):
                raise ErroMPL('execucao', linha, coluna, f'instrucao desconhecida {op}')
        except ZeroDivisionError:
            raise ErroMPL('execucao', linha, coluna, 'divisao ou resto por zero') from None
