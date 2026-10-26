#!/usr/bin/env python3
"""
Pre-aceitacao de um pull request da vitrine de Compiladores MPL 2026-2.

Roda a cada pull request e escreve um LAUDO para o professor. Tem dois tipos de resultado:

  PORTOES  recusam o pull request sozinhos: estrutura, prazo, compilar/executar,
           so biblioteca padrao, nenhum gerador de parser.
  INDICIOS vao para o laudo e NUNCA recusam sozinhos: resultado funcional e
           qualidade do codigo. Na revisao do professor (modulo privado, fora deste
           repositorio) entram tambem autoria, historico e semelhanca entre trabalhos. Indicio
           nao e prova; quem decide e o professor, e a apresentacao (alteracao
           ao vivo) continua sendo a prova de autoria.

Uso:
  pre_aceitacao.py --pasta grupos/turmaB-nome [--criado-em 2026-11-23T23:10:00Z]
                   [--lab URL_OU_PASTA] [--corpus-extra PASTA] [--referencia PASTA ...]
                   [--laudo laudo.md] [--json laudo.json]

--corpus-extra e --referencia sao para uso LOCAL do professor (corpus B e gabarito
nunca entram neste repositorio publico).
"""
import argparse, datetime, io, json, keyword, os, re, shutil, subprocess, sys, tempfile, tokenize

LAB_PADRAO = 'https://github.com/LuizRMSilva1973/compiladores-lab.git'
APRESENTACAO = {'A': datetime.date(2026, 11, 25), 'B': datetime.date(2026, 11, 23)}
FUSO = datetime.timezone(datetime.timedelta(hours=-3))      # Brasilia, sem horario de verao
ENTREGAS = {1: (datetime.date(2026, 8, 31), datetime.date(2026, 9, 2)),
            2: (datetime.date(2026, 9, 28), datetime.date(2026, 9, 30)),
            3: (datetime.date(2026, 10, 26), datetime.date(2026, 10, 28)),
            4: (datetime.date(2026, 11, 16), datetime.date(2026, 11, 18))}
EXT_CODIGO = {'.py', '.java', '.c', '.h', '.cpp', '.hpp', '.cc', '.rb', '.php'}
IGNORAR_DIRS = {'.git', '__pycache__', 'testes', 'evidencias', 'exemplos', 'node_modules'}
IGNORAR_ARQ = {'verificar.py'}            # vem do lab; nao e codigo do grupo
GERADORES = re.compile(r'\b(ply|lark|antlr4?|sly|pyparsing|parsimonious|tatsu|textx|'
                       r'org\.antlr|javacc|jflex|cup|treetop|racc|citrus|parslet|'
                       r'hoa\\compiler|phplrt)\b', re.I)


# ----------------------------------------------------------------- utilidades
def rodar(cmd, cwd=None, timeout=900, env=None):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired as e:
        return 124, (e.stdout or '') + '\n[tempo esgotado]'
    except FileNotFoundError as e:
        return 127, str(e)


def arquivos_codigo(pasta):
    for raiz, dirs, nomes in os.walk(pasta):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
        for n in nomes:
            if n in IGNORAR_ARQ:
                continue
            if os.path.splitext(n)[1].lower() in EXT_CODIGO:
                yield os.path.join(raiz, n)


def ler(caminho):
    try:
        with open(caminho, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return ''


# ----------------------------------------------------------------- portoes
def portao_prazo(pasta, criado_em):
    turma = re.match(r'turma([AB])-', os.path.basename(pasta.rstrip('/')))
    if not turma:
        return False, 'nome da pasta nao comeca com turmaA- ou turmaB-'
    t = turma.group(1)
    if not criado_em:
        return True, f'turma {t}; data do pull request nao informada (rodada local)'
    quando = datetime.datetime.fromisoformat(criado_em.replace('Z', '+00:00')).astimezone(FUSO)
    if quando.date() < APRESENTACAO[t]:
        return False, (f'pull request aberto em {quando:%d/%m/%Y %H:%M}, antes da apresentacao da '
                       f'turma {t} ({APRESENTACAO[t]:%d/%m/%Y})')
    return True, f'turma {t}; aberto em {quando:%d/%m/%Y %H:%M}'


def turma_do_grupo_md(pasta):
    m = re.search(r'Turma:\*{0,2}\s*([AB])\b(?!.*\bou\b)', ler(os.path.join(pasta, 'GRUPO.md')))
    return m.group(1) if m else None


def pendencias_do_envio(pasta):
    """No TESTE (repositorio do proprio grupo): o que ainda impediria o envio de verdade."""
    falta = []
    g = ler(os.path.join(pasta, 'GRUPO.md'))
    if not g:
        falta.append('criar o GRUPO.md (copiar o GRUPO-modelo.md da vitrine) e preencher')
    else:
        if 'Nome 1' in g or '# Nome do grupo' in g:
            falta.append('preencher no GRUPO.md o nome do grupo e os integrantes')
        if not turma_do_grupo_md(pasta):
            falta.append('escrever no GRUPO.md a turma: A (quarta) ou B (segunda)')
        if not re.search(r'https://github\.com/(?!usuario/repositorio)[\w.-]+/[\w.-]+', g):
            falta.append('colocar no GRUPO.md o link do repositorio do grupo')
        if re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', g, re.I):
            falta.append('tirar e-mail do GRUPO.md (a vitrine e publica)')
    return falta


def portao_executaveis(pasta):
    faltam = [n for n in ('compilar', 'executar') if not os.path.isfile(os.path.join(pasta, n))]
    if faltam:
        return False, 'faltam na raiz da pasta: ' + ', '.join(faltam)
    return True, 'compilar e executar presentes'


def modulos_locais(pasta):
    nomes = set()
    for c in arquivos_codigo(pasta):
        if c.endswith('.py'):
            nomes.add(os.path.splitext(os.path.basename(c))[0])
    for raiz, dirs, _ in os.walk(pasta):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
        nomes.update(dirs)
    return nomes


def portao_bibliotecas(pasta):
    """So biblioteca padrao (regra do README do lab) e nenhum gerador de parser."""
    problemas = []
    stdlib = set(getattr(sys, 'stdlib_module_names', ())) | {'__future__'}
    locais = modulos_locais(pasta)
    for c in arquivos_codigo(pasta):
        rel = os.path.relpath(c, pasta)
        texto = ler(c)
        ext = os.path.splitext(c)[1].lower()
        if ext == '.py':
            for m in re.finditer(r'^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))', texto, re.M):
                mod = (m.group(1) or m.group(2)).lstrip('.').split('.')[0]
                if not mod or mod in locais or mod in stdlib:
                    continue
                problemas.append(f'{rel}: importa `{mod}`, que nao e da biblioteca padrao')
        imports = '\n'.join(re.findall(r'^\s*(?:import|from|require|require_once|include|#include|use)\b.*$', texto, re.M))
        g = GERADORES.search(imports)
        if g:
            problemas.append(f'{rel}: usa gerador de parser (`{g.group(0)}`)')
    for raiz, dirs, nomes in os.walk(pasta):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
        for n in nomes:
            if os.path.splitext(n)[1].lower() in {'.y', '.yy', '.l', '.ll', '.g4', '.jj', '.lark'}:
                problemas.append(f'{os.path.relpath(os.path.join(raiz, n), pasta)}: arquivo de gramatica para gerador de parser')
    return (not problemas), problemas


# ----------------------------------------------------------------- funcional
def obter_lab(lab):
    if os.path.isdir(lab):
        return lab, None
    tmp = tempfile.mkdtemp(prefix='lab-')
    rc, saida = rodar(['git', 'clone', '-q', '--depth', '1', lab, tmp], timeout=180)
    if rc:
        raise RuntimeError('nao consegui baixar o compiladores-lab: ' + saida[-300:])
    return tmp, tmp


def funcional(pasta, lab_dir, corpus=None, isolar=False):
    """Roda o verificador OFICIAL (do lab, nao o da pasta do grupo) contra o compilador do grupo."""
    tmp = tempfile.mkdtemp(prefix='grupo-')
    try:
        alvo = os.path.join(tmp, 'g')
        shutil.copytree(pasta, alvo, ignore=shutil.ignore_patterns('.git', '__pycache__', 'evidencias'))
        shutil.copy(os.path.join(lab_dir, 'verificar.py'), os.path.join(alvo, 'verificar.py'))
        shutil.rmtree(os.path.join(alvo, 'testes'), ignore_errors=True)
        shutil.copytree(os.path.join(lab_dir, 'testes'), os.path.join(alvo, 'testes'))
        for n in ('compilar', 'executar'):
            p = os.path.join(alvo, n)
            if os.path.exists(p):
                os.chmod(p, 0o755)
        env = dict(os.environ, LANG='en_US.UTF-8')
        if corpus:
            # copia dentro da pasta de trabalho: o verificador grava arquivos ao lado dos programas
            shutil.copytree(corpus, os.path.join(alvo, 'corpus-extra'))
            env['MPL_TESTES'] = os.path.join(alvo, 'corpus-extra')
        cmd = [sys.executable, 'verificar.py', 'todas']
        if isolar:
            # dentro da caixa a pasta pessoal some: usar o Python do sistema, nao o de um venv em ~
            cmd[0] = shutil.which('python3', path='/usr/local/bin:/usr/bin:/bin') or '/usr/bin/python3'
            # codigo do aluno roda sem rede, sem ver a pasta pessoal e sem poder escrever fora da copia
            caixa = ['bwrap', '--ro-bind', '/', '/', '--dev', '/dev', '--proc', '/proc', '--tmpfs', '/home',
                     '--tmpfs', '/tmp', '--bind', alvo, alvo, '--unshare-all', '--die-with-parent', '--new-session',
                     '--chdir', alvo]
            cmd = caixa + cmd
        rc, saida = rodar(cmd, cwd=alvo, timeout=1200, env=env)
        por_entrega, atual = {}, None
        for linha in saida.splitlines():
            m = re.search(r'Entrega (\d) ══', linha)
            if m:
                atual = int(m.group(1)); por_entrega[atual] = [0, 0]; continue
            if atual is None:
                continue
            if re.match(r'\s{2}ok\s', linha):
                por_entrega[atual][0] += 1; por_entrega[atual][1] += 1
            m = re.search(r'Entrega \d: (\d+) de (\d+)', linha)
            if m:
                total = int(m.group(2))
                passou = int(m.group(1)) if 'passaram' in linha else total - int(m.group(1))
                por_entrega[atual] = [passou, total]
        if not por_entrega:
            raise RuntimeError('o verificador nao rodou: ' + saida.strip()[-400:])
        return por_entrega, saida
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------- qualidade
def linhas_uteis(texto, ext):
    uteis = coment = 0
    em_bloco = False
    for l in texto.splitlines():
        s = l.strip()
        if not s:
            continue
        if ext == '.py':
            if s.startswith('#'):
                coment += 1; continue
        else:
            if em_bloco:
                coment += 1
                if '*/' in s: em_bloco = False
                continue
            if s.startswith('/*'):
                coment += 1; em_bloco = '*/' not in s; continue
            if s.startswith('//') or (ext in {'.rb', '.php'} and s.startswith('#')):
                coment += 1; continue
        uteis += 1
    return uteis, coment


def funcoes_python(texto):
    """(nome, linhas, tem_docstring, docstring) de cada funcao."""
    out = []
    linhas = texto.splitlines()
    defs = [(i, len(l) - len(l.lstrip()), re.match(r'\s*def\s+(\w+)', l).group(1))
            for i, l in enumerate(linhas) if re.match(r'\s*def\s+\w+', l)]
    for k, (i, ind, nome) in enumerate(defs):
        fim = len(linhas)
        for j in range(i + 1, len(linhas)):
            l = linhas[j]
            if l.strip() and (len(l) - len(l.lstrip())) <= ind and not l.lstrip().startswith(('#', ')', ']')):
                fim = j; break
        corpo = linhas[i + 1:fim]
        prim = next((l.strip() for l in corpo if l.strip()), '')
        doc = ''
        if prim.startswith(('"""', "'''", 'r"""')):
            bloco = '\n'.join(l.strip() for l in corpo[:12])
            m = re.search(r'("""|\'\'\')(.*?)(\1)', bloco, re.S)
            doc = (m.group(2) if m else prim).strip()
        out.append((nome, fim - i, bool(doc), doc))
    return out


def qualidade(pasta):
    por_arquivo, funcs = [], []
    for c in sorted(arquivos_codigo(pasta)):
        ext = os.path.splitext(c)[1].lower()
        texto = ler(c)
        u, cm = linhas_uteis(texto, ext)
        por_arquivo.append((os.path.relpath(c, pasta), u, cm))
        if ext == '.py':
            funcs += funcoes_python(texto)
    total_u = sum(u for _, u, _ in por_arquivo)
    total_c = sum(c for _, _, c in por_arquivo)
    tamanhos = sorted((n for _, n, _, _ in funcs), reverse=True)
    return {
        'arquivos': por_arquivo,
        'linhas_codigo': total_u,
        'linhas_comentario': total_c,
        'funcoes': len(funcs),
        'maior_funcao': tamanhos[0] if tamanhos else 0,
        'funcoes_longas': sum(1 for n in tamanhos if n > 60),
        'docstrings': sum(1 for f in funcs if f[2]),
        'funcs_lista': funcs,
    }


# ----------------------------------------------------------------- parte privada
def carregar_privado():
    """Sinais de IA, historico e semelhanca ficam num modulo que NAO esta neste repositorio publico."""
    pasta = os.environ.get('PRE_ACEITACAO_PRIVADO')
    if not pasta:
        raise SystemExit('Sem --publico, este laudo precisa do modulo privado do professor (PRE_ACEITACAO_PRIVADO).')
    sys.path.insert(0, pasta)
    import sinais_privados
    return sinais_privados


# ----------------------------------------------------------------- laudo
def faixa(p):
    return 'BAIXO' if p < 25 else ('MEDIO' if p < 50 else 'ALTO')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pasta', required=True)
    ap.add_argument('--criado-em')
    ap.add_argument('--lab', default=LAB_PADRAO)
    ap.add_argument('--corpus-extra')
    ap.add_argument('--referencia', action='append', default=[])
    ap.add_argument('--grupos', default='grupos')
    ap.add_argument('--laudo')
    ap.add_argument('--json')
    ap.add_argument('--publico', action='store_true',
                    help='laudo para o GitHub: so portoes, funcional e qualidade (sem sinais de IA nem semelhanca)')
    ap.add_argument('--isolar', action='store_true', help='roda o codigo do aluno dentro do bwrap (uso local)')
    ap.add_argument('--teste', action='store_true',
                    help='teste de envio no repositorio do proprio grupo: sem portao de prazo, lista o que falta para o envio')
    a = ap.parse_args()
    pasta = a.pasta.rstrip('/')
    nome = os.path.basename(pasta)

    portoes = []
    falta_envio = []
    if a.teste:
        falta_envio = pendencias_do_envio(pasta)
        t = turma_do_grupo_md(pasta)
        quando = f'a partir de {APRESENTACAO[t]:%d/%m/%Y}' if t else 'depois da apresentacao da sua turma'
        portoes.append(('Prazo', True, f'teste de envio; o envio de verdade (pull request na vitrine) e {quando}'))
    else:
        portoes.append(('Prazo (so depois da apresentacao)',) + portao_prazo(pasta, a.criado_em))
    portoes.append(('compilar e executar na raiz',) + portao_executaveis(pasta))
    ok_lib, prob_lib = portao_bibliotecas(pasta)
    portoes.append(('So biblioteca padrao, sem gerador de parser', ok_lib, '; '.join(prob_lib) or 'ok'))
    recusado = not all(p[1] for p in portoes)

    func, func_extra = {}, {}
    lab_dir, apagar = obter_lab(a.lab)
    erro_func = None
    if not recusado:
        try:
            func, _ = funcional(pasta, lab_dir, isolar=a.isolar)
            if a.corpus_extra:
                func_extra, _ = funcional(pasta, lab_dir, a.corpus_extra, isolar=a.isolar)
        except RuntimeError as e:
            erro_func = str(e)
    q = qualidade(pasta)
    p_txt, ach_txt, p_hist, ach_hist, info_hist, sem = 0, [], 0, [], {}, []
    priv = None if a.publico else carregar_privado()
    if priv:
        p_txt, ach_txt = priv.sinais_texto(pasta, q)
        p_hist, ach_hist, info_hist = priv.sinais_historico(pasta)
    outras = []
    if os.path.isdir(a.grupos):
        outras = [(d, os.path.join(a.grupos, d)) for d in sorted(os.listdir(a.grupos))
                  if os.path.isdir(os.path.join(a.grupos, d)) and d != nome]
    outras += [(f'REFERENCIA:{os.path.basename(r.rstrip("/"))}', r) for r in a.referencia]
    if priv:
        sem = priv.semelhanca(pasta, outras, priv.impressao(os.path.join(lab_dir, 'mplc')))
    p_sem = 0
    if sem and sem[0][1] >= 0.6:
        p_sem = 30
    elif sem and sem[0][1] >= 0.4:
        p_sem = 15
    pontos = min(100, p_txt + p_hist + p_sem)

    # cada entrega ja inclui as anteriores: o placar que vale e o da ultima
    total_ok, total = func[max(func)] if func else (0, 0)
    func_completo = bool(total) and total_ok == total
    if recusado:
        veredito = 'RECUSADO NA ANALISE PRELIMINAR'
    elif not func_completo:
        veredito = 'PASSOU NOS PORTOES, MAS O VERIFICADOR AINDA TEM FALHAS'
    elif not a.publico and pontos >= 50:
        veredito = 'APROVADO NA ANALISE PRELIMINAR — SEGUNDA ANALISE: ATENCAO'
    else:
        veredito = 'APROVADO NA ANALISE PRELIMINAR — PENDENTE: SEGUNDA ANALISE (IA + PROFESSOR)'

    titulo = 'Teste de envio' if a.teste else 'Laudo de pre-aceitacao'
    L = [f'# {titulo} — `{nome}`', '', f'**Veredito: {veredito}**', '']
    if a.teste:
        L += ['> Isto e um **teste**: nada foi enviado. O envio de verdade e o pull request na vitrine, depois da '
              'apresentacao. Passar aqui significa passar na analise preliminar; a segunda analise (IA + professor) '
              'acontece depois do envio de verdade.', '']
        if falta_envio:
            L += ['**Ainda falta para o envio de verdade:**', ''] + [f'- {x}' for x in falta_envio] + ['']
    L += ['## 1. Portoes (recusam sozinhos)', '', '| Portao | Resultado | Detalhe |', '|---|---|---|']
    for titulo, ok, det in portoes:
        L.append(f'| {titulo} | {"ok" if ok else "**RECUSA**"} | {det} |')
    L += ['', '## 2. Funcional (verificador oficial do compiladores-lab, corpus publico)', '']
    if func:
        L += ['| Entrega | Passaram |', '|---|---|'] + [f'| E{n} | {v[0]} de {v[1]} |' for n, v in sorted(func.items())]
        L.append(f'| **Resultado (E4 inclui as anteriores)** | **{total_ok} de {total}** |')
    elif erro_func:
        L.append(f'**Nao foi possivel rodar o verificador:** {erro_func}')
    else:
        L.append('Nao rodou (o pull request parou num portao).')
    if func_extra:
        te, tt = func_extra[max(func_extra)]
        L += ['', f'Corpus extra (local): **{te} de {tt}** — ' + ', '.join(f'E{n} {v[0]}/{v[1]}' for n, v in sorted(func_extra.items()))]
    L += ['', '## 3. Qualidade (informativo)', '',
          f'- {q["linhas_codigo"]} linhas de codigo, {q["linhas_comentario"]} de comentario, em {len(q["arquivos"])} arquivo(s)',
          f'- {q["funcoes"]} funcoes Python; a maior tem {q["maior_funcao"]} linhas; {q["funcoes_longas"]} com mais de 60 linhas', '',
          '| Arquivo | Linhas de codigo | Comentario |', '|---|---|---|']
    L += [f'| `{arq}` | {u} | {c} |' for arq, u, c in q['arquivos']]
    if a.publico:
        L += ['', '---', 'Laudo publico: portoes, funcional e qualidade. A revisao do professor (inclusive autoria e '
              'comparacao entre trabalhos) e feita a parte. A aceitacao final e do professor.']
        laudo = '\n'.join(L) + '\n'
        print(laudo)
        for caminho, conteudo in ((a.laudo, laudo),):
            if caminho:
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
        if apagar:
            shutil.rmtree(apagar, ignore_errors=True)
        return 1 if recusado else 0
    L += ['', f'## 4. Sinais de IA — indicio **{faixa(pontos)}** ({pontos}/100)', '',
          '> Indicio nao e prova e **nunca recusa sozinho**. Serve para o professor saber onde olhar e o que perguntar '
          'na apresentacao. Quem escreveu o compilador consegue altera-lo ao vivo.', '']
    if info_hist:
        L.append(f'Repositorio do grupo: {info_hist.get("url")} — {info_hist.get("commits", "?")} commits com codigo, '
                 f'{info_hist.get("autores", "?")} autor(es), {info_hist.get("dias", "?")} dia(s) com commit, '
                 f'commits por entrega: {info_hist.get("por_entrega", {})}')
        L.append('')
    achados = ach_txt + ach_hist
    if sem:
        mostrar = sem[:5] + [x for x in sem[5:] if x[0].startswith('REFERENCIA:')]
        achados.append(('Semelhanca com outros trabalhos e com a referencia (k-gramas de tokens)', [f'{n}: {j:.0%}' for n, j in mostrar]))
    if not achados:
        L.append('Nenhum sinal encontrado.')
    for titulo, itens in achados:
        L.append(f'- **{titulo}**')
        L += [f'  - {i}' for i in itens]
    L += ['', '---', 'Gerado por `.github/scripts/pre_aceitacao.py`. A aceitacao final e do professor.']
    laudo = '\n'.join(L) + '\n'

    print(laudo)
    if a.laudo:
        with open(a.laudo, 'w', encoding='utf-8') as f:
            f.write(laudo)
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'grupo': nome, 'veredito': veredito, 'portoes': portoes, 'funcional': func,
                       'funcional_extra': func_extra, 'pontos_ia': pontos, 'historico': info_hist,
                       'semelhanca': sem, 'qualidade': {k: v for k, v in q.items() if k != 'funcs_lista'}},
                      f, ensure_ascii=False, indent=2, default=str)
    if apagar:
        shutil.rmtree(apagar, ignore_errors=True)
    return 1 if recusado else 0


if __name__ == '__main__':
    sys.exit(main())
