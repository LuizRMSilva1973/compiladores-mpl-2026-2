"""Reduz a AST tipada a instrucoes de tres enderecos."""
import json


class Gerador:
    def __init__(self, tabela):
        self.codigo = []
        self.contador = 0
        self.posicao = None
        self.locais = {}
        for escopo in tabela.escopos:
            for simbolo in escopo.simbolos.values():
                if simbolo.categoria != 'funcao':
                    self.locais[simbolo] = f'v{len(self.locais)}_{simbolo.nome}'

    def novo(self):
        self.contador += 1
        return f't{self.contador}'

    def emitir(self, no, op, *args):
        origem = self.posicao or no
        self.codigo.append((origem.linha, origem.coluna, op, *args))

    def converter(self, no, valor, origem, destino):
        if origem == 'inteiro' and destino == 'real':
            temp = self.novo()
            self.emitir(no, 'real', temp, valor)
            return temp
        return valor

    def expressao(self, no):
        classe = no.rotulo.split()[0]
        temp = self.novo()
        if classe == 'literal':
            tipo, valor = no.extra['tipo'], no.extra['valor']
            if tipo == 'texto':
                valor = json.loads(valor)
            elif tipo == 'logico':
                valor = valor == 'verdadeiro'
            elif tipo == 'inteiro':
                valor = int(valor)
            else:
                valor = float(valor)
            self.emitir(no, 'const', temp, valor)
        elif classe == 'variavel':
            self.emitir(no, 'copia', temp, self.locais[no.extra['simbolo']])
        elif classe == 'chamada':
            simbolo = no.extra['simbolo']
            args = []
            for arg, tipo in zip(no.filhos, simbolo.parametros):
                valor = self.expressao(arg)
                args.append(self.converter(arg, valor, arg.extra['tipo_expr'], tipo))
            self.emitir(no, 'chama', temp, simbolo.nome, args)
        elif classe == 'unario':
            valor = self.expressao(no.filhos[0])
            self.emitir(no, 'unario', temp, no.extra['operador'], valor)
        elif classe == 'binario':
            valores = [self.expressao(f) for f in no.filhos]
            tipos = [f.extra['tipo_expr'] for f in no.filhos]
            if 'real' in tipos:
                valores = [self.converter(no, v, t, 'real') for v, t in zip(valores, tipos)]
            self.emitir(no, 'binario', temp, no.extra['operador'], *valores)
        return temp

    def comando(self, no):
        classe = no.rotulo.split()[0]
        if classe != 'bloco':
            self.posicao = no
        if classe == 'bloco':
            for filho in no.filhos:
                self.comando(filho)
        elif classe in ('declaracao', 'atribuicao'):
            simbolo = no.extra['simbolo']
            if no.filhos:
                expr = no.filhos[0]
                valor = self.expressao(expr)
                valor = self.converter(no, valor, expr.extra['tipo_expr'], simbolo.tipo)
            else:
                valor = self.novo()
                padrao = {'inteiro': 0, 'real': 0.0, 'logico': False, 'texto': ''}
                self.emitir(no, 'const', valor, padrao[simbolo.tipo])
            self.emitir(no, 'copia', self.locais[simbolo], valor)
        elif classe in ('se', 'enquanto'):
            inicio, fim = self.novo(), self.novo()
            self.emitir(no, 'rotulo', inicio)
            condicao = self.expressao(no.filhos[0])
            self.emitir(no, 'seFalso', condicao, fim)
            self.comando(no.filhos[1])
            if classe == 'enquanto':
                self.emitir(no, 'desvie', inicio)
            elif len(no.filhos) == 3:
                depois = self.novo()
                self.emitir(no, 'desvie', depois)
                self.emitir(no, 'rotulo', fim)
                self.comando(no.filhos[2])
                fim = depois
            self.emitir(no, 'rotulo', fim)
        elif classe == 'escreva':
            self.emitir(no, 'escreva', self.expressao(no.filhos[0]))
        elif classe == 'retorne':
            valor = None
            if no.filhos:
                expr = no.filhos[0]
                valor = self.expressao(expr)
                valor = self.converter(no, valor, expr.extra['tipo_expr'], self.retorno)
            self.emitir(no, 'retorne', valor)
        elif classe == 'chamada':
            self.expressao(no)


def gerar(arvore, tabela):
    gerador = Gerador(tabela)
    for funcao in arvore.filhos:
        gerador.posicao = None
        gerador.retorno = funcao.extra['tipo']
        parametros = [gerador.locais[p.extra['simbolo']] for p in funcao.filhos[0].filhos]
        gerador.emitir(funcao, 'funcao', funcao.extra['nome'], parametros)
        gerador.comando(funcao.filhos[1])
        gerador.emitir(funcao, 'retorne', None)
        gerador.emitir(funcao, 'fim')
    return gerador.codigo


def despejar(codigo):
    linhas = []
    for _, _, op, *args in codigo:
        if op == 'binario':
            destino, operador, a, b = args
            linha = f'{destino} = {a} {operador} {b}'
        elif op == 'unario':
            destino, operador, valor = args
            linha = f'{destino} = {operador} {valor}'
        else:
            linha = op + ' ' + ' '.join(json.dumps(a, ensure_ascii=False) for a in args)
        linhas.append(linha.rstrip())
    return linhas
