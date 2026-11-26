"""
Entrega 3 — analise semantica.

Tabela de simbolos, escopos aninhados e verificacao de tipos.

Tres coisas que costumam ser esquecidas e valem nota:
  - o corpo de uma funcao abre DOIS escopos (o dos parametros e o do bloco);
  - uma funcao pode ser chamada antes de aparecer no arquivo, entao a
    primeira passada so coleta assinaturas;
  - funcao com retorno declarado precisa garantir o retorno em TODOS os
    caminhos.

Leiam antes: LINGUAGEM.md secoes 3 a 5, e CONTRATOS.md secao 4.

Representacao: cada escopo e um objeto com um ponteiro para o pai (dicionario
encadeado). Durante a analise, o escopo atual e o topo dessa cadeia; a busca
de um nome sobe pelos pais ate o global. Todos os escopos criados ficam
tambem numa lista, na ordem em que abriram, para o despejo do --tabela.
"""
from mplc.erros import ErroMPL


NUMERICOS = ('inteiro', 'real')


class Simbolo:
    def __init__(self, nome, categoria, tipo, linha, parametros=None):
        self.nome = nome
        self.categoria = categoria      # 'funcao', 'parametro' ou 'variavel'
        self.tipo = tipo                # para funcao, o tipo de retorno
        self.linha = linha
        self.parametros = parametros    # so para funcao: lista de tipos

    def descricao_tipo(self):
        if self.categoria == 'funcao':
            return f"{self.tipo}({','.join(self.parametros)})"
        return self.tipo


class Escopo:
    def __init__(self, numero, descricao, pai):
        self.numero = numero
        self.descricao = descricao
        self.pai = pai
        self.simbolos = {}              # dict preserva a ordem de declaracao

    def buscar(self, nome):
        escopo = self
        while escopo is not None:
            if nome in escopo.simbolos:
                return escopo.simbolos[nome]
            escopo = escopo.pai
        return None


class Tabela:
    def __init__(self):
        self.escopos = []
        self.global_ = self.abrir('global', None)

    def abrir(self, descricao, pai):
        escopo = Escopo(len(self.escopos), descricao, pai)
        self.escopos.append(escopo)
        return escopo


def erro(no, mensagem):
    return ErroMPL('semantico', no.linha, no.coluna, mensagem)


def cabe(origem, destino):
    """Conversao implicita: so inteiro -> real (secao 3.1)."""
    return origem == destino or (origem == 'inteiro' and destino == 'real')


class Analisador:
    def __init__(self):
        self.tabela = Tabela()
        self.atual = self.tabela.global_
        self.funcao = None              # Simbolo da funcao sendo analisada

    # ------------------------------------------------------------- programa

    def programa(self, arvore):
        # primeira passada: as assinaturas, para permitir chamada adiantada
        for f in arvore.filhos:
            nome = f.extra['nome']
            if nome in self.tabela.global_.simbolos:
                raise erro(f, f"funcao '{nome}' declarada duas vezes")
            tipos = [p.extra['tipo'] for p in f.filhos[0].filhos]
            self.tabela.global_.simbolos[nome] = Simbolo(
                nome, 'funcao', f.extra['tipo'], f.linha, tipos)

        principal = self.tabela.global_.simbolos.get('principal')
        if principal is None:
            raise ErroMPL('semantico', 1, 1, "falta a funcao 'principal'")
        if principal.parametros or principal.tipo != 'vazio':
            no = next(f for f in arvore.filhos if f.extra['nome'] == 'principal')
            raise erro(no, "'principal' tem que ser 'funcao vazio principal()'")

        # segunda passada: os corpos
        for f in arvore.filhos:
            self.funcao_corpo(f)
        return self.tabela

    def funcao_corpo(self, no):
        nome = no.extra['nome']
        self.funcao = self.tabela.global_.simbolos[nome]
        parametros, bloco = no.filhos

        anterior = self.atual
        self.atual = self.tabela.abrir(f'funcao {nome}', anterior)
        for p in parametros.filhos:
            self.declarar(p, 'parametro')
        self.bloco(bloco)
        self.atual = anterior

        if self.funcao.tipo != 'vazio' and not garante_retorno(bloco):
            raise erro(no, f"a funcao '{nome}' nao retorna em todos os caminhos")

    def declarar(self, no, categoria):
        nome = no.extra['nome']
        if nome in self.atual.simbolos:
            raise erro(no, f"'{nome}' ja foi declarado neste escopo")
        simbolo = Simbolo(nome, categoria, no.extra['tipo'], no.linha)
        self.atual.simbolos[nome] = simbolo
        no.extra['simbolo'] = simbolo
        return simbolo

    # --------------------------------------------------------------- comandos

    def bloco(self, no):
        anterior = self.atual
        self.atual = self.tabela.abrir('bloco', anterior)
        for comando in no.filhos:
            self.comando(comando)
        self.atual = anterior

    def comando(self, no):
        tipo = no.rotulo.split()[0]

        if tipo == 'declaracao':
            # a expressao e avaliada antes do nome existir: 'inteiro x = x;'
            # usa o x de fora, se houver
            if no.filhos:
                t = self.expressao(no.filhos[0])
                if not cabe(t, no.extra['tipo']):
                    raise erro(no, f"nao da para guardar {t} em '{no.extra['nome']}', "
                                   f"que e {no.extra['tipo']}")
            self.declarar(no, 'variavel')

        elif tipo == 'atribuicao':
            simbolo = self.variavel(no)
            t = self.expressao(no.filhos[0])
            if not cabe(t, simbolo.tipo):
                raise erro(no, f"nao da para guardar {t} em '{simbolo.nome}', "
                               f"que e {simbolo.tipo}")

        elif tipo == 'se':
            self.condicao(no.filhos[0], 'se')
            for b in no.filhos[1:]:
                self.bloco(b)

        elif tipo == 'enquanto':
            self.condicao(no.filhos[0], 'enquanto')
            self.bloco(no.filhos[1])

        elif tipo == 'escreva':
            self.expressao(no.filhos[0])

        elif tipo == 'retorne':
            esperado = self.funcao.tipo
            if esperado == 'vazio':
                if no.filhos:
                    raise erro(no, f"'{self.funcao.nome}' e vazio e nao retorna valor")
            elif not no.filhos:
                raise erro(no, f"'{self.funcao.nome}' tem que retornar {esperado}")
            else:
                t = self.expressao(no.filhos[0])
                if not cabe(t, esperado):
                    raise erro(no, f"'{self.funcao.nome}' retorna {esperado}, nao {t}")

        elif tipo == 'chamada':
            self.chamada(no, como_comando=True)

        elif tipo == 'bloco':
            self.bloco(no)

    def condicao(self, no, comando):
        t = self.expressao(no)
        if t != 'logico':
            raise erro(no, f"a condicao do '{comando}' tem que ser logico, nao {t}")

    def variavel(self, no):
        nome = no.extra['nome']
        simbolo = self.atual.buscar(nome)
        if simbolo is None or simbolo.categoria == 'funcao':
            raise erro(no, f"'{nome}' nao foi declarada")
        no.extra['simbolo'] = simbolo
        return simbolo

    # ------------------------------------------------------------- expressoes

    def expressao(self, no):
        """Devolve o tipo da expressao e o anota no no (extra['tipo_expr'])."""
        t = self._tipo(no)
        no.extra['tipo_expr'] = t
        return t

    def _tipo(self, no):
        tipo = no.rotulo.split()[0]

        if tipo == 'literal':
            return no.extra['tipo']
        if tipo == 'variavel':
            return self.variavel(no).tipo
        if tipo == 'chamada':
            return self.chamada(no, como_comando=False)
        if tipo == 'unario':
            t = self.expressao(no.filhos[0])
            if no.extra['operador'] == 'nao':
                if t != 'logico':
                    raise erro(no, f"'nao' exige logico, nao {t}")
                return 'logico'
            if t not in NUMERICOS:
                raise erro(no, f"'-' exige numero, nao {t}")
            return t
        if tipo == 'binario':
            return self.binario(no)
        raise erro(no, f'expressao desconhecida: {no.rotulo}')

    def binario(self, no):
        op = no.extra['operador']
        a = self.expressao(no.filhos[0])
        b = self.expressao(no.filhos[1])

        if op == '+' and a == 'texto' and b == 'texto':
            return 'texto'
        if op in ('+', '-', '*', '/'):
            if a in NUMERICOS and b in NUMERICOS:
                return 'inteiro' if a == b == 'inteiro' else 'real'
        elif op == '%':
            if a == b == 'inteiro':
                return 'inteiro'
        elif op in ('<', '<=', '>', '>='):
            if a in NUMERICOS and b in NUMERICOS:
                return 'logico'
        elif op in ('==', '!='):
            if a != 'vazio' and (cabe(a, b) or cabe(b, a)):
                return 'logico'
        elif op in ('e', 'ou'):
            if a == b == 'logico':
                return 'logico'
        raise erro(no, f"'{op}' nao aceita {a} e {b}")

    def chamada(self, no, como_comando):
        nome = no.extra['nome']
        funcao = self.tabela.global_.simbolos.get(nome)
        if funcao is None:
            raise erro(no, f"a funcao '{nome}' nao existe")
        no.extra['simbolo'] = funcao

        if len(no.filhos) != len(funcao.parametros):
            raise erro(no, f"'{nome}' recebe {len(funcao.parametros)} argumento(s), "
                           f"nao {len(no.filhos)}")
        for i, (arg, esperado) in enumerate(zip(no.filhos, funcao.parametros), 1):
            t = self.expressao(arg)
            if not cabe(t, esperado):
                raise erro(arg, f"argumento {i} de '{nome}' tem que ser {esperado}, nao {t}")

        if funcao.tipo == 'vazio' and not como_comando:
            raise erro(no, f"'{nome}' e vazio e nao pode ser usada numa expressao")
        return funcao.tipo


def garante_retorno(no):
    """Olha a estrutura, nunca o valor das condicoes."""
    tipo = no.rotulo.split()[0]
    if tipo == 'retorne':
        return True
    if tipo == 'bloco':
        return any(garante_retorno(c) for c in no.filhos)
    if tipo == 'se':
        return len(no.filhos) == 3 and garante_retorno(no.filhos[1]) \
            and garante_retorno(no.filhos[2])
    return False                        # enquanto pode nao executar nenhuma vez


def analisar(arvore):
    """Percorre a arvore, monta a tabela e confere os tipos. Devolve a tabela."""
    return Analisador().programa(arvore)


def despejar(tabela):
    """Devolve as linhas do --tabela, no formato da secao 4 do contrato."""
    linhas = []
    for escopo in tabela.escopos:
        if escopo.pai is None:
            linhas.append(f'escopo {escopo.numero} {escopo.descricao}')
        else:
            linhas.append(f'escopo {escopo.numero} {escopo.descricao} pai {escopo.pai.numero}')
        for s in escopo.simbolos.values():
            linhas.append(f'  {s.nome}|{s.categoria}|{s.descricao_tipo()}|{s.linha}')
    return linhas
