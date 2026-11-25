"""
entrega 4, segunda metade: a geracao do codigo executavel.

aqui o codigo de tres enderecos vira o .mplb, que e o codigo de uma MAQUINA
DE PILHA, so que em texto. cada linha de tres enderecos vira poucas instrucoes:

    t2 = t0 + t1        CARREGA 1     ; t0
                        CARREGA 2     ; t1
                        SOMA
                        GUARDA  3     ; t2

os nomes somem nessa etapa: cada variavel, parametro e temporario da funcao
ganha uma POSICAO (slot) no registro de ativacao. os parametros vem primeiro,
na ordem, porque e nessa ordem que o CHAMA tira eles da pilha. o comentario
no fim da linha so diz de quem e a posicao, pra ficar mais facil de ler.

o formato (a lista completa de instrucoes ta no README.md):

    .funcao <nome> <quantos parametros> <quantas posicoes>
    .local <posicao> <nome>          (um por posicao, so documentacao)
    <linha do fonte>  <INSTRUCAO> [argumento]   ; comentario
    <rotulo>:
    .fim

mais detalhes no CONTRATOS.md, secao 6.
"""
from mplc.intermediario import escrever_operando


BINARIOS = {
    '+': 'SOMA', '-': 'SUBTRAI', '*': 'MULTIPLICA', '/': 'DIVIDE', '%': 'RESTO',
    '==': 'IGUAL', '!=': 'DIFERENTE',
    '<': 'MENOR', '<=': 'MENOR_IGUAL', '>': 'MAIOR', '>=': 'MAIOR_IGUAL',
    'e': 'E', 'ou': 'OU',
}
UNARIOS = {'-': 'NEGA', 'nao': 'NAO'}


class _Funcao:
    def __init__(self, f):
        self.f = f
        self.posicoes = {}
        for n, _ in f.parametros:
            self.posicao(n)
        self.linhas = []

    def posicao(self, nome):
        if nome not in self.posicoes:
            self.posicoes[nome] = len(self.posicoes)
        return self.posicoes[nome]

    def instr(self, linha, codigo, arg=None, comentario=None):
        texto = f'{linha:>5}  {codigo:<16}'
        if arg is not None:
            texto += f'{arg}'
        if comentario:
            texto = f'{texto:<40}; {comentario}'
        self.linhas.append(texto.rstrip())

    def empilhar(self, linha, operando):
        if operando[0] == 'nome':
            self.instr(linha, 'CARREGA', self.posicao(operando[1]), operando[1])
        else:
            self.instr(linha, 'EMPILHA', escrever_operando(operando))

    def guardar(self, linha, nome):
        self.instr(linha, 'GUARDA', self.posicao(nome), nome)

    def traduzir(self):
        for i in self.f.instrucoes:
            L = i.linha
            if i.op == 'copia':
                self.empilhar(L, i.a)
                self.guardar(L, i.destino)
            elif i.op == 'binario':
                self.empilhar(L, i.a)
                self.empilhar(L, i.b)
                self.instr(L, BINARIOS[i.oper])
                self.guardar(L, i.destino)
            elif i.op == 'unario':
                self.empilhar(L, i.a)
                self.instr(L, UNARIOS[i.oper])
                self.guardar(L, i.destino)
            elif i.op == 'real':
                self.empilhar(L, i.a)
                self.instr(L, 'PARA_REAL')
                self.guardar(L, i.destino)
            elif i.op == 'rotulo':
                self.linhas.append(f'{i.alvo}:')
            elif i.op == 'desvie':
                self.instr(L, 'DESVIA', i.alvo)
            elif i.op == 'seFalso':
                self.empilhar(L, i.a)
                self.instr(L, 'DESVIA_SE_FALSO', i.alvo)
            elif i.op == 'param':
                self.empilhar(L, i.a)
            elif i.op == 'chama':
                self.instr(L, 'CHAMA', i.alvo, f'{i.n} argumento(s)')
                if i.destino:
                    self.guardar(L, i.destino)
            elif i.op == 'retorne':
                if i.a is not None:
                    self.empilhar(L, i.a)
                    self.instr(L, 'RETORNA_VALOR')
                else:
                    self.instr(L, 'RETORNA')
            elif i.op == 'escreva':
                self.empilhar(L, i.a)
                self.instr(L, 'ESCREVA')
            else:
                raise ValueError(i.op)

        cabeca = [f'.funcao {self.f.nome} {len(self.f.parametros)} {len(self.posicoes)}']
        cabeca += [f'.local {p} {n}' for n, p in self.posicoes.items()]
        return cabeca + self.linhas + ['.fim']


def gerar(codigo_intermediario):
    """devolve as linhas do arquivo .mplb."""
    linhas = [
        '; MPL bytecode -- maquina de pilha. Gerado pelo mplc; o README lista as instrucoes.',
        '; coluna 1: linha do fonte (para os erros de execucao). O que vem depois de ; e comentario.',
    ]
    for f in codigo_intermediario.funcoes:
        linhas.append('')
        linhas.extend(_Funcao(f).traduzir())
    return linhas
