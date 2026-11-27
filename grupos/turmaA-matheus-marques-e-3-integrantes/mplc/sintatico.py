from mplc.erros import ErroMPL


class ErroSintatico(ErroMPL):
    def __init__(self, linha, coluna, mensagem):
        super().__init__('sintatico', linha, coluna, mensagem)


class No:
    """Um no da arvore. O rotulo e o que sai no --ast."""

    def __init__(self, rotulo, filhos=None, linha=0, coluna=0, **extra):
        self.rotulo = rotulo      
        self.filhos = filhos or []
        self.linha = linha
        self.coluna = coluna
        self.extra = extra        


def analisar(tokens):
    """Recebe a lista de Token. Devolve a raiz da arvore (um No 'programa')."""
    parser = Parser(tokens)
    return parser.parse()


def despejar(no, nivel=0, saida=None):
    """Imprime a arvore no formato do --ast. Ja esta pronto: dois espacos por nivel."""
    saida = saida if saida is not None else []
    saida.append('  ' * nivel + no.rotulo)
    for f in no.filhos:
        despejar(f, nivel + 1, saida)
    return saida


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def atual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def proximo_tipo(self, tipo):
        t = self.atual()
        return t is not None and t.tipo == tipo

    def consome(self, tipo=None):
        t = self.atual()
        if t is None:
            ult = self.tokens[-1] if self.tokens else None
            linha = ult.linha if ult else 1
            coluna = ult.coluna if ult else 1
            raise ErroSintatico(linha, coluna, "fim de arquivo inesperado")
        if tipo is not None and t.tipo != tipo:
            raise ErroSintatico(t.linha, t.coluna, f"esperado '{tipo}', encontrado '{t.tipo}'")
        self.pos += 1
        return t

    def parse(self):
        funcoes = []
        while self.atual() is not None and self.atual().tipo != "FIM_ARQUIVO":
            if self.proximo_tipo("FUNCAO"):
                funcoes.append(self.funcao())
            else:
                t = self.atual()
                raise ErroSintatico(t.linha, t.coluna, f"esperado 'FUNCAO', encontrado '{t.tipo}'")
        if not funcoes:
            raise ErroSintatico(1, 1, "programa vazio")
        linha = funcoes[0].linha
        coluna = funcoes[0].coluna
        return No("programa", funcoes, linha=linha, coluna=coluna)

    def funcao(self):
        t_func = self.consome("FUNCAO")
        t_tipo = self.atual()
        
        # Em sin-06, temos: funcao principal()
        # O tipo de retorno falta. O token atual é "principal" (coluna 8).
        # Se a seguir vier "(", significa que o nome da função foi colocado onde deveria estar o tipo, ou omitiu-se o tipo.
        # Vamos verificar se o token após o atual (ou o atual se for "(") indica falta de tipo.
        # Na verdade, se o próximo token for "(", o token atual ("principal") é o nome da função, logo o tipo está em falta na posição do token atual!
        # Vamos inspecionar o token seguinte:
        # Se o token atual for um ID e o *seguinte* for ABRE_PAR, então o tipo de retorno está omitido e o erro deve ser no token atual (principal, coluna 8).
        
        # Vamos testar explicitamente:
        next_t = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
        if t_tipo and next_t and next_t.tipo == "ABRE_PAR":
            raise ErroSintatico(t_tipo.linha, t_tipo.coluna, "tipo de retorno esperado")

        if t_tipo and t_tipo.tipo == "ABRE_PAR":
            raise ErroSintatico(t_tipo.linha, t_tipo.coluna, "tipo de retorno esperado")

        if t_tipo and (t_tipo.tipo in ("TIPO", "INTEIRO", "REAL", "VAZIO", "ID") or t_tipo.lexema in ("inteiro", "real", "vazio", "texto", "logico")):
            self.consome()
        else:
            raise ErroSintatico(t_tipo.linha if t_tipo else t_func.linha, t_tipo.coluna if t_tipo else t_func.coluna, "tipo de retorno esperado")

        t_nome = self.consome("ID")
        
        self.consome("ABRE_PAR")
        parametros = []
        if not self.proximo_tipo("FECHA_PAR"):
            parametros.append(self.parametro())
            while self.proximo_tipo("VIRGULA"):
                self.consome("VIRGULA")
                parametros.append(self.parametro())
        self.consome("FECHA_PAR")
        
        bloco = self.bloco()
        rotulo = f"funcao {t_nome.lexema} {t_tipo.lexema}"
        filhos = [No("parametros", parametros, linha=t_nome.linha, coluna=t_nome.coluna), bloco]
        return No(rotulo, filhos, linha=t_func.linha, coluna=t_func.coluna)

    def parametro(self):
        t_tipo = self.consome()
        t_nome = self.consome("ID")
        return No(f"parametro {t_nome.lexema} {t_tipo.lexema}", linha=t_tipo.linha, coluna=t_tipo.coluna)

    def bloco(self):
        t_ch = self.consome("ABRE_CHAVE")
        comandos = []
        while self.atual() is not None and not self.proximo_tipo("FECHA_CHAVE"):
            comandos.append(self.comando())
        self.consome("FECHA_CHAVE")
        return No("bloco", comandos, linha=t_ch.linha, coluna=t_ch.coluna)

    def comando(self):
        t = self.atual()
        if t is None:
            raise ErroSintatico(1, 1, "comando esperado")

        if t.tipo == "ABRE_CHAVE":
            return self.bloco()

        elif t.tipo in ("TIPO", "INTEIRO", "REAL") or (t.lexema in ("inteiro", "real", "texto", "logico")):
            tipo_token = self.consome()
            id_token = self.consome("ID")
            filhos = []
            if self.proximo_tipo("ATRIBUI"):
                self.consome("ATRIBUI")
                filhos.append(self.expressao())
            self.consome("PONTO_VIRGULA")
            return No(f"declaracao {id_token.lexema} {tipo_token.lexema}", filhos, linha=id_token.linha, coluna=id_token.coluna)

        elif t.tipo == "SE":
            self.consome("SE")
            self.consome("ABRE_PAR")
            cond = self.expressao()
            self.consome("FECHA_PAR")
            bloco_verd = self.bloco()
            filhos = [cond, bloco_verd]
            if self.proximo_tipo("SENAO"):
                self.consome("SENAO")
                bloco_fals = self.bloco()
                filhos.append(bloco_fals)
            return No("se", filhos, linha=t.linha, coluna=t.coluna)

        elif t.tipo == "ENQUANTO":
            self.consome("ENQUANTO")
            self.consome("ABRE_PAR")
            cond = self.expressao()
            self.consome("FECHA_PAR")
            bloco_enq = self.bloco()
            return No("enquanto", [cond, bloco_enq], linha=t.linha, coluna=t.coluna)

        elif t.tipo == "RETORNE":
            t_ret = self.consome("RETORNE")
            filhos = []
            if not self.proximo_tipo("PONTO_VIRGULA"):
                filhos.append(self.expressao())
            self.consome("PONTO_VIRGULA")
            return No("retorne", filhos, linha=t_ret.linha, coluna=t_ret.coluna)

        elif t.tipo == "ESCREVA":
            t_esc = self.consome("ESCREVA")
            self.consome("ABRE_PAR")
            expr = self.expressao()
            self.consome("FECHA_PAR")
            self.consome("PONTO_VIRGULA")
            return No("escreva", [expr], linha=t_esc.linha, coluna=t_esc.coluna)

        elif t.tipo == "ID":
            id_token = self.consome("ID")
            if self.proximo_tipo("ATRIBUI"):
                self.consome("ATRIBUI")
                expr = self.expressao()
                self.consome("PONTO_VIRGULA")
                return No(f"atribuicao {id_token.lexema}", [expr], linha=id_token.linha, coluna=id_token.coluna)
            elif self.proximo_tipo("ABRE_PAR"):
                self.consome("ABRE_PAR")
                args = []
                if not self.proximo_tipo("FECHA_PAR"):
                    args.append(self.expressao())
                    while self.proximo_tipo("VIRGULA"):
                        self.consome("VIRGULA")
                        args.append(self.expressao())
                self.consome("FECHA_PAR")
                self.consome("PONTO_VIRGULA")
                chamada_no = No(f"chamada {id_token.lexema}", args, linha=id_token.linha, coluna=id_token.coluna)
                return No("comando", [chamada_no], linha=id_token.linha, coluna=id_token.coluna)
            else:
                raise ErroSintatico(id_token.linha, id_token.coluna, "atribuição ou chamada esperada")
        else:
            raise ErroSintatico(t.linha, t.coluna, f"comando invalido ('{t.lexema}')")

    def expressao(self):
        return self.ou()

    def ou(self):
        esq = self.e()
        while self.proximo_tipo("OU"):
            op = self.consome("OU")
            dir = self.e()
            esq = No(f"binario {op.lexema}", [esq, dir], linha=op.linha, coluna=op.coluna)
        return esq

    def e(self):
        esq = self.igualdade()
        while self.proximo_tipo("E"):
            op = self.consome("E")
            dir = self.igualdade()
            esq = No(f"binario {op.lexema}", [esq, dir], linha=op.linha, coluna=op.coluna)
        return esq

    def igualdade(self):
        esq = self.relacional()
        t = self.atual()
        while t is not None and t.tipo in ("IGUAL", "DIFERENTE"):
            op = self.consome()
            dir = self.relacional()
            esq = No(f"binario {op.lexema}", [esq, dir], linha=op.linha, coluna=op.coluna)
            t = self.atual()
        return esq

    def relacional(self):
        esq = self.adicao()
        t = self.atual()
        while t is not None and t.tipo in ("MENOR", "MENOR_IGUAL", "MAIOR", "MAIOR_IGUAL"):
            op = self.consome()
            dir = self.adicao()
            esq = No(f"binario {op.lexema}", [esq, dir], linha=op.linha, coluna=op.coluna)
            t = self.atual()
        return esq

    def adicao(self):
        esq = self.multiplicacao()
        t = self.atual()
        while t is not None and t.tipo in ("MAIS", "MENOS"):
            op = self.consome()
            dir = self.multiplicacao()
            esq = No(f"binario {op.lexema}", [esq, dir], linha=op.linha, coluna=op.coluna)
            t = self.atual()
        return esq

    def multiplicacao(self):
        esq = self.unario()
        t = self.atual()
        while t is not None and t.tipo in ("VEZES", "DIVIDE", "DIVISAO", "RESTO"):
            op = self.consome()
            dir = self.unario()
            esq = No(f"binario {op.lexema}", [esq, dir], linha=op.linha, coluna=op.coluna)
            t = self.atual()
        return esq

    def unario(self):
        t = self.atual()
        if t and (t.tipo in ("MAIS", "MENOS") or t.lexema in ("nao", "!")):
            op = self.consome()
            dir = self.unario()
            return No(f"unario {op.lexema}", [dir], linha=op.linha, coluna=op.coluna)
        return self.primario()

    def primario(self):
        t = self.atual()
        if t is None:
            raise ErroSintatico(1, 1, "expressao esperada")

        if t.tipo in ("NUM_INT", "INTEIRO") or t.tipo == "NUM_INT":
            tok = self.consome()
            return No(f"literal inteiro {tok.lexema}", linha=tok.linha, coluna=tok.coluna)
        elif t.tipo in ("NUM_REAL", "REAL") or t.tipo == "NUM_REAL":
            tok = self.consome()
            valor_real = f"{float(tok.lexema):.6f}"
            return No(f"literal real {valor_real}", linha=tok.linha, coluna=tok.coluna)
        elif t.tipo in ("STRING", "TEXTO"):
            tok = self.consome()
            return No(f"literal texto {tok.lexema}", linha=tok.linha, coluna=tok.coluna)
        elif t.lexema in ("verdadeiro", "falso") or t.tipo == "BOOLEANO":
            tok = self.consome()
            return No(f"literal logico {tok.lexema}", linha=tok.linha, coluna=tok.coluna)
        elif t.tipo == "ID":
            tok = self.consome("ID")
            if self.proximo_tipo("ABRE_PAR"):
                self.consome("ABRE_PAR")
                args = []
                if not self.proximo_tipo("FECHA_PAR"):
                    args.append(self.expressao())
                    while self.proximo_tipo("VIRGULA"):
                        self.consome("VIRGULA")
                        args.append(self.expressao())
                self.consome("FECHA_PAR")
                return No(f"chamada {tok.lexema}", args, linha=tok.linha, coluna=tok.coluna)
            else:
                return No(f"variavel {tok.lexema}", linha=tok.linha, coluna=tok.coluna)
        elif t.tipo == "ABRE_PAR":
            self.consome("ABRE_PAR")
            expr = self.expressao()
            self.consome("FECHA_PAR")
            return expr
        else:
            raise ErroSintatico(t.linha, t.coluna, f"expressao invalida ('{t.lexema}')")
