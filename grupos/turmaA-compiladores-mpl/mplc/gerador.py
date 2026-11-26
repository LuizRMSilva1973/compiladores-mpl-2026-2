"""Traduz tres enderecos para assembly textual de uma maquina de pilha."""
import json


def gerar(codigo_intermediario):
    linhas = ['# MPLB 1 - maquina de pilha']

    def emitir(op, *args):
        linhas.append(op + ' ' + json.dumps(args, ensure_ascii=False))

    for linha, coluna, op, *args in codigo_intermediario:
        emitir('POS', linha, coluna)
        if op == 'const':
            emitir('PUSH', args[1])
            emitir('STORE', args[0])
        elif op in ('copia', 'real'):
            emitir('LOAD', args[1])
            if op == 'real':
                emitir('REAL')
            emitir('STORE', args[0])
        elif op in ('binario', 'unario'):
            destino, operador, *operandos = args
            for operando in operandos:
                emitir('LOAD', operando)
            emitir('BINARY' if op == 'binario' else 'UNARY', operador)
            emitir('STORE', destino)
        elif op == 'chama':
            destino, nome, argumentos = args
            for argumento in argumentos:
                emitir('LOAD', argumento)
            emitir('CALL', nome, len(argumentos))
            emitir('STORE', destino)
        elif op == 'retorne':
            if args[0] is not None:
                emitir('LOAD', args[0])
            else:
                emitir('PUSH', None)
            emitir('RET')
        elif op == 'escreva':
            emitir('LOAD', args[0])
            emitir('PRINT')
        elif op == 'seFalso':
            emitir('LOAD', args[0])
            emitir('JZ', args[1])
        else:
            emitir({'funcao': 'FUNC', 'fim': 'END', 'rotulo': 'LABEL', 'desvie': 'JMP'}[op], *args)
    return linhas
