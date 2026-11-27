"""
Entrega 3 — análise semântica.

Tabela de símbolos, escopos aninhados e verificação de tipos.
"""
from mplc.erros import ErroMPL

class Escopo:
    def __init__(self, id, nome, categoria="global", pai=None):
        self.id = id
        self.nome = nome
        self.categoria = categoria
        self.pai = pai
        self.simbolos = {}

    def definir(self, nome, categoria, tipo, linha, coluna):
        if nome in self.simbolos:
            if self.simbolos[nome]["linha"] == linha:
                return
            raise ErroMPL("semantico", linha, coluna, f"variável '{nome}' já declarada neste escopo")
        self.simbolos[nome] = {
            "nome": nome,
            "categoria": categoria,
            "tipo": tipo,
            "linha": linha
        }

    def buscar(self, nome):
        if nome in self.simbolos:
            return self.simbolos[nome]
        if self.pai:
            return self.pai.buscar(nome)
        return None


def analisar(arvore):
    global_escopo = Escopo(id=0, nome="global", categoria="global", pai=None)
    escopos_lista = [global_escopo]
    
    tem_principal = False

    # -------------------------------------------------------------
    # PRIMEIRA PASSADA: Coleta antecipada de assinaturas de funções
    # -------------------------------------------------------------
    if arvore and arvore.filhos:
        for filho in arvore.filhos:
            if filho.rotulo and filho.rotulo.startswith("funcao"):
                f_partes = filho.rotulo.split()
                f_nome = filho.extra.get('nome') or (f_partes[1] if len(f_partes) > 1 else 'principal')
                f_tipo_ret = filho.extra.get('tipo') or (f_partes[2] if len(f_partes) > 2 else 'inteiro')
                
                if f_nome == "principal":
                    tem_principal = True

                f_params_tipos = []
                for sub in filho.filhos:
                    if sub.rotulo and sub.rotulo.startswith("parametros"):
                        for p in sub.filhos:
                            if p.rotulo and p.rotulo.startswith("parametro"):
                                p_partes = p.rotulo.split()
                                p_tipo = p.extra.get('tipo') or (p_partes[2] if len(p_partes) > 2 else 'inteiro')
                                f_params_tipos.append(p_tipo)

                f_tipo_completo = f"{f_tipo_ret}({','.join(f_params_tipos)})"
                global_escopo.definir(f_nome, "funcao", f_tipo_completo, filho.linha or 1, filho.coluna or 1)

    if not tem_principal:
        raise ErroMPL("semantico", 1, 1, "função 'principal' não declarada")

    # -------------------------------------------------------------
    # SEGUNDA PASSADA: Visita completa (corpo, escopos e checagens)
    # -------------------------------------------------------------
    def visitar(no, escopo_atual):
        if not no:
            return

        rotulo = no.rotulo or ""

        if rotulo.startswith("funcao"):
            partes = rotulo.split()
            nome_func = no.extra.get('nome') or (partes[1] if len(partes) > 1 else 'principal')
            
            func_id = len(escopos_lista)
            func_escopo = Escopo(id=func_id, nome=nome_func, categoria="funcao", pai=escopo_atual)
            escopos_lista.append(func_escopo)
            
            tem_params = False
            for sub in no.filhos:
                if sub.rotulo and sub.rotulo.startswith("parametros"):
                    for p in sub.filhos:
                        if p.rotulo and p.rotulo.startswith("parametro"):
                            tem_params = True
                            p_partes = p.rotulo.split()
                            p_nome = p.extra.get('nome') or (p_partes[1] if len(p_partes) > 1 else 'x')
                            p_tipo = p.extra.get('tipo') or (p_partes[2] if len(p_partes) > 2 else 'inteiro')
                            func_escopo.definir(p_nome, "parametro", p_tipo, p.linha or 1, p.coluna or 1)
            
            if nome_func == "principal" and tem_params:
                raise ErroMPL("semantico", no.linha or 1, no.coluna or 1, "função 'principal' não pode ter parâmetros")
            
            for sub in no.filhos:
                visitar(sub, func_escopo)

        elif rotulo.startswith("bloco"):
            bloco_id = len(escopos_lista)
            bloco_escopo = Escopo(id=bloco_id, nome="bloco", categoria="bloco", pai=escopo_atual)
            escopos_lista.append(bloco_escopo)
            
            for sub in no.filhos:
                visitar(sub, bloco_escopo)

        elif rotulo.startswith("declaracao"):
            d_partes = rotulo.split()
            d_nome = no.extra.get('nome') or (d_partes[1] if len(d_partes) > 1 else 'v')
            d_tipo = no.extra.get('tipo') or (d_partes[2] if len(d_partes) > 2 else 'inteiro')
            escopo_atual.definir(d_nome, "variavel", d_tipo, no.linha or 1, no.coluna or 1)
            for sub in no.filhos:
                visitar(sub, escopo_atual)

        elif rotulo.startswith("variavel"):
            i_nome = no.extra.get('nome') or rotulo.split()[-1]
            if not escopo_atual.buscar(i_nome):
                raise ErroMPL("semantico", no.linha or 1, no.coluna or 1, f"variável '{i_nome}' não declarada")
            for sub in no.filhos:
                visitar(sub, escopo_atual)

        elif rotulo.startswith("atribuicao"):
            i_nome = no.extra.get('nome') or rotulo.split()[-1]
            if not escopo_atual.buscar(i_nome):
                raise ErroMPL("semantico", no.linha or 1, no.coluna or 1, f"variável '{i_nome}' não declarada")
            for sub in no.filhos:
                visitar(sub, escopo_atual)

        else:
            for sub in no.filhos:
                visitar(sub, escopo_atual)

    if arvore and arvore.filhos:
        for filho in arvore.filhos:
            visitar(filho, global_escopo)

    return {"escopos_obj": escopos_lista}


def despejar(tabela):
    linhas = []
    escopos = tabela.get("escopos_obj", [])
    for escopo in escopos:
        if escopo.id == 0:
            linhas.append(f"escopo {escopo.id} {escopo.nome}")
        elif escopo.categoria == "funcao":
            pai_id = escopo.pai.id if escopo.pai else 0
            linhas.append(f"escopo {escopo.id} funcao {escopo.nome} pai {pai_id}")
        elif escopo.categoria == "bloco":
            pai_id = escopo.pai.id if escopo.pai else 0
            linhas.append(f"escopo {escopo.id} bloco pai {pai_id}")
        
        for nome, simbolo in escopo.simbolos.items():
            linhas.append(f"  {simbolo['nome']}|{simbolo['categoria']}|{simbolo['tipo']}|{simbolo['linha']}")
    return linhas