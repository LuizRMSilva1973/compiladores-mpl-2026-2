# Minha pequena linguagem

Trabalho semestral de **Compiladores** — Ciência da Computação, UNISAGRADO.
Prof. Luiz Ricardo Mantovani da Silva · 2026-2

Cada grupo escreve um **compilador completo** para a MPL, uma linguagem
pequena de palavras-chave em português. O compilador de vocês vai ler um
programa em `.mpl`, atravessar as quatro fases da disciplina e produzir um
arquivo que **roda de verdade** numa máquina virtual que vocês também vão
escrever.

No fim do semestre vocês executam um programa escrito por vocês, numa
linguagem compilada por vocês.

---

## Comece por aqui

```bash
git clone https://github.com/LuizRMSilva1973/compiladores-lab.git
cd compiladores-lab
```

```bash
make verificar E=1
```

Vai dar vermelho — é para dar. O esqueleto responde à linha de comando mas
ainda não tem nenhuma fase escrita. O vermelho é o seu ponto de partida, e
ele vai virando verde conforme vocês preenchem `mplc/`.

Não precisa instalar nada além do Python 3. Se o notebook de vocês der
trabalho, o [Google Cloud Shell](https://shell.cloud.google.com) já vem com
Python 3.12, Java 21 e git — e é o mesmo ambiente da correção.

---

## Os três documentos que mandam

| Arquivo | O que decide |
|---|---|
| [LINGUAGEM.md](LINGUAGEM.md) | **o que** o compilador aceita: a sintaxe e as regras de tipo da MPL |
| [CONTRATOS.md](CONTRATOS.md) | **como** ele se comunica: a linha de comando e o formato de cada despejo |
| [entregas/](entregas/) | o enunciado de cada entrega, com o que vale nota |

Quando a sua intuição discordar de um deles, é o arquivo que vale. Se o
arquivo estiver errado, me procurem — já aconteceu de eu escrever um exemplo
errado no contrato e só descobrir rodando.

---

## As entregas

| # | Entrega | Turma A (quarta) | Turma B (segunda) | Vale |
|---|---|---|---|---|
| [E1](entregas/E1.md) | Analisador léxico | 02/09 | 31/08 | 0,8 |
| [E2](entregas/E2.md) | Analisador sintático e árvore | 30/09 | 28/09 | 1,2 |
| [E3](entregas/E3.md) | Tabela de símbolos e tipos | 28/10 | 26/10 | 1,2 |
| [E4](entregas/E4.md) | Código intermediário, geração e VM | 18/11 | 16/11 | 1,8 |
| [Apres.](entregas/APRESENTACAO.md) | Demonstração e defesa | 25/11 | 23/11 | 1,0 |

São **quatro entregas sobre o mesmo compilador**, não quatro trabalhos. O que
vocês escreverem na E1 continua rodando na E4 — e o verificador da E4 confere
tudo o que veio antes. Deixar a E1 pela metade custa caro em novembro.

---

## Regras do jogo

**A entrega é o repositório, nunca a máquina de vocês.** A correção clona o
repositório numa máquina limpa e roda `make verificar E=n`. Se não passar
lá, não conta como entregue. Testem antes de entregar — de preferência na
Cloud Shell, que é o ambiente da correção.

**Grupos de até 3.** O mesmo grupo do começo ao fim. Mudança de grupo só até
a E1.

**Gerador de parser proibido nas Entregas 1 e 2.** ANTLR, PLY, yacc, lark e
parentes escondem exatamente a parte que está sendo ensinada. Da E3 em diante
o assunto é outro, e aí não faz diferença. Na apresentação vocês podem — e
devem — comparar o parser de vocês com o que um gerador produziria.

**A linguagem de implementação é de vocês, entre as que o ambiente da correção
já tem:** Python 3.12, Java 21, C e C++ (gcc 13), Ruby 3.2 ou PHP 8.3. O
verificador não olha para dentro — ele roda `./compilar` e `./executar` e
compara o que sai. O esqueleto em `mplc/` é Python porque é o caminho mais
curto, mas ninguém é obrigado a usá-lo.

A lista existe por um motivo prático: a correção roda numa Cloud Shell limpa, e
o que não estiver lá não roda. Querem outra linguagem? Falem comigo **antes** de
começar — o critério é ela existir no ambiente sem instalação. Em nenhum caso
dependam de biblioteca externa: só a biblioteca padrão.

**Escrever o compilador é a tarefa.** Usar IA para explicar um conceito,
revisar uma mensagem de erro ou entender um trecho é bem-vindo, e eu faço
isso também. Entregar um compilador que vocês não sabem alterar é outra
coisa — e a apresentação foi desenhada para separar os dois casos: cada grupo
recebe **uma alteração pequena na linguagem, na hora, com 10 minutos para
fazer**. Quem escreveu o compilador faz. Não é desconfiança; é o formato.

---

## O verificador

```bash
make verificar E=2      # confere a Entrega 2 e, junto, a 1
make verificar          # confere as quatro
make evidencias E=2     # grava evidencias/verificacao-2.txt, que vai na entrega
```

**Antes de entregar, rodem `make prova`.** Ele clona o repositório de vocês num
diretório limpo e verifica lá — que é exatamente o que a correção faz. É o
teste que pega o defeito mais comum de todos, e que não tem nada a ver com
compiladores: *funciona aqui e não no clone*. Arquivo esquecido fora do commit,
caminho absoluto, passo de compilação que ninguém roda. Vale para qualquer
linguagem, e é a única prova que realmente antecipa a correção.

Ele não lê o código de vocês. Ele roda o compilador e compara a saída com um
corpus de **10 programas válidos**, **26 programas que precisam ser
recusados na compilação** e **3 que precisam falhar na execução** — com a
fase e a linha do erro conferidas.

Os programas recusados são metade da nota escondida do trabalho. Um
compilador que aceita tudo passa em todos os testes positivos e não vale
nada: é por isso que o corpus tem mais programas errados do que certos.

**A correção usa um segundo corpus, que vocês não têm.** Mesma linguagem,
mesmas regras, programas diferentes. Um compilador de verdade passa nos dois
sem que vocês precisem fazer nada; um programa que apenas reproduza as saídas
esperadas deste corpus passa aqui e reprova lá. Estou dizendo isto abertamente
para ninguém perder tempo pelo caminho errado.

---

## Como entregar

1. `git push` no repositório do grupo.
2. Abram a [página do trabalho](https://profluiz.mantovanitec.com/disciplinas/aulas/compiladores/trabalho.html).
3. No formulário do fim da página: escolham a entrega, identifiquem os
   integrantes (nome, RA e e-mail), colem a URL do repositório e anexem o
   `evidencias/verificacao-N.txt`.
4. Cada integrante recebe uma cópia por e-mail. **Guardem esse e-mail**: é o
   comprovante.

---

## Tabela de tokens (Entrega 1)

A coluna do primeiro caractere de cada linha é **1**. O analisador em
`mplc/lexico.py` percorre o fonte da esquerda para a direita, descarta
espaços (` `, `\t`, `\r`, `\n`) e os dois tipos de comentário, e emite um
token por casamento. Operadores de dois caracteres são tentados **antes**
dos de um, para que `<=`, `>=`, `==` e `!=` não se partam. A lista termina
sempre com `FIM_ARQUIVO` (lexema vazio): na linha seguinte, coluna 1, se o
arquivo acaba em quebra de linha; senão, logo após o último caractere.

| Tipo | O que reconhece | Expressão regular / regra |
|---|---|---|
| `INTEIRO` | literal inteiro | `[0-9]+` |
| `REAL` | literal real (dígito dos dois lados do ponto) | `[0-9]+\.[0-9]+` |
| `LOGICO` | literal lógico | `verdadeiro` \| `falso` |
| `TEXTO` | literal entre aspas, numa linha só | `"` (`\\[nt"\\]` \| `[^"\\\n\r]`)* `"` |
| `ID` | identificador (não reservado) | `[a-zA-Z_][a-zA-Z0-9_]*` |
| `FUNCAO` | palavra reservada | `funcao` |
| `RETORNE` | palavra reservada | `retorne` |
| `SE` | palavra reservada | `se` |
| `SENAO` | palavra reservada | `senao` |
| `ENQUANTO` | palavra reservada | `enquanto` |
| `ESCREVA` | palavra reservada | `escreva` |
| `TIPO_INTEIRO` | nome de tipo | `inteiro` |
| `TIPO_REAL` | nome de tipo | `real` |
| `TIPO_LOGICO` | nome de tipo | `logico` |
| `TIPO_TEXTO` | nome de tipo | `texto` |
| `TIPO_VAZIO` | nome de tipo | `vazio` |
| `E` | operador lógico | `e` |
| `OU` | operador lógico | `ou` |
| `NAO` | operador lógico | `nao` |
| `MAIS` | operador | `+` |
| `MENOS` | operador | `-` |
| `VEZES` | operador | `*` |
| `DIVIDE` | operador | `/` |
| `RESTO` | operador | `%` |
| `IGUAL` | operador | `==` |
| `DIFERENTE` | operador | `!=` |
| `MENOR` | operador | `<` |
| `MENOR_IGUAL` | operador | `<=` |
| `MAIOR` | operador | `>` |
| `MAIOR_IGUAL` | operador | `>=` |
| `ATRIBUI` | atribuição | `=` |
| `ABRE_PAR` | delimitador | `(` |
| `FECHA_PAR` | delimitador | `)` |
| `ABRE_CHAVE` | delimitador | `{` |
| `FECHA_CHAVE` | delimitador | `}` |
| `VIRGULA` | delimitador | `,` |
| `PONTO_VIRGULA` | delimitador | `;` |
| `FIM_ARQUIVO` | fim do fonte | (lexema vazio) |

Comentários não geram token: `//` até o fim da linha, e `/* ... */` de
bloco (não aninha; o primeiro `*/` fecha). Bloco aberto sem `*/` é erro
léxico na posição do `/*`.

Erros léxicos, ancorados no caractere que estragou o token:

- escape fora de `\n`, `\t`, `\"`, `\\` — na barra
- texto sem fecha-aspas, ou quebrando a linha — na aspa de abertura
- `3.` ou `.5` (ponto sem dígito de um dos lados) — no ponto
- caractere que não começa nenhum token — nele mesmo

---

## Gramática (Entrega 2)

Gramática em EBNF implementada por descida recursiva em `mplc/sintatico.py`:
cada não-terminal abaixo é uma função com o mesmo nome. Os terminais em
maiúsculas são os tipos de token da tabela acima. `{ x }` significa zero ou
mais repetições e `[ x ]` significa opcional.

```ebnf
programa       = { funcao } FIM_ARQUIVO ;
funcao         = FUNCAO tipo_retorno ID parametros bloco ;
parametros     = ABRE_PAR [ parametro { VIRGULA parametro } ] FECHA_PAR ;
parametro      = tipo ID ;
tipo           = TIPO_INTEIRO | TIPO_REAL | TIPO_LOGICO | TIPO_TEXTO ;
tipo_retorno   = tipo | TIPO_VAZIO ;

bloco          = ABRE_CHAVE { comando } FECHA_CHAVE ;
comando        = declaracao | atribuicao | se | enquanto | escreva
               | retorne | chamada PONTO_VIRGULA | bloco ;
declaracao     = tipo ID [ ATRIBUI expressao ] PONTO_VIRGULA ;
atribuicao     = ID ATRIBUI expressao PONTO_VIRGULA ;
se             = SE condicao bloco [ SENAO bloco ] ;
enquanto       = ENQUANTO condicao bloco ;
condicao       = ABRE_PAR expressao FECHA_PAR ;
escreva        = ESCREVA ABRE_PAR expressao FECHA_PAR PONTO_VIRGULA ;
retorne        = RETORNE [ expressao ] PONTO_VIRGULA ;

expressao      = ou ;
ou             = e { OU e } ;
e              = igualdade { E igualdade } ;
igualdade      = relacional { ( IGUAL | DIFERENTE ) relacional } ;
relacional     = aditivo { ( MENOR | MENOR_IGUAL | MAIOR | MAIOR_IGUAL ) aditivo } ;
aditivo        = multiplicativo { ( MAIS | MENOS ) multiplicativo } ;
multiplicativo = unario { ( VEZES | DIVIDE | RESTO ) unario } ;
unario         = ( NAO | MENOS ) unario | primario ;
primario       = INTEIRO | REAL | LOGICO | TEXTO
               | chamada | ID
               | ABRE_PAR expressao FECHA_PAR ;
chamada        = ID ABRE_PAR [ expressao { VIRGULA expressao } ] FECHA_PAR ;
```

**Como a precedência está codificada:** há uma regra por nível da seção 3.3
da especificação, do mais fraco (`ou`) para o mais forte (`primario`), e cada
regra só se refere à regra do nível logo abaixo. Por isso um operador mais
forte sempre fica mais fundo na árvore: em `1 + 2 * 3`, o `*` é consumido
dentro de `multiplicativo` antes que `aditivo` monte o `+`. A associatividade
à esquerda vem da repetição `{ op próximo }`, e não de recursão à direita. No
parser ela é um laço que pendura a árvore montada até ali como filho
**esquerdo** do novo operador, então `10 - 4 - 3` vira `(10 - 4) - 3`. Só
`unario` chama a si mesmo, porque `nao` e o `-` unário associam à direita.

Duas decisões que a gramática deixa explícitas:

- Um comando que começa por `ID` é decidido olhando **um token à frente**:
  `=` é atribuição, `(` é chamada usada como comando. Qualquer outro token
  ali é erro sintático, relatado nesse token.
- `vazio` só aparece em `tipo_retorno`. `vazio x;` e `funcao f(vazio x)` são
  recusados já na sintaxe.

---

## Escopos (Entrega 3)

Os escopos são uma **árvore de dicionários encadeados** (`mplc/semantica.py`):
cada `Escopo` tem um dicionário `nome → Simbolo` só com o que foi declarado
nele e um ponteiro para o pai, e procurar um nome é subir pelos pais até
achar. Isso dá o sombreamento de graça — o primeiro achado é o mais de
dentro — e fechar um bloco é só voltar o escopo atual para o pai, o que faz a
variável de fora reaparecer sem apagar nada. Não usamos uma pilha que
descarta o escopo ao fechar porque o `--tabela` precisa de todos os escopos
no fim, numerados na ordem em que abriram, e a Entrega 4 também vai
precisar: a `Tabela` guarda essa lista, e o analisador pendura em cada uso de
nome na árvore o `Simbolo` exato que ele resolveu. Assim, quando os nomes
virarem posições de memória, cada `x` sombreado já é um objeto diferente e
basta dar um endereço a cada `Simbolo`, sem refazer a busca por nome.

O resto da análise, em duas passadas: a primeira põe as assinaturas de todas
as funções no escopo 0, para que uma função possa chamar outra que aparece
depois; a segunda percorre os corpos abrindo os escopos (parâmetros, bloco do
corpo, e um por `se`, `senao`, `enquanto` e `{ }`) e conferindo os tipos. A
garantia de retorno olha só a estrutura: `retorne` garante, um bloco garante
se algum comando dele garante, `se/senao` garante se os dois lados garantem,
e `se` sem `senao` e `enquanto` nunca garantem, qualquer que seja a condição.

---

## Código intermediário, geração e máquina virtual (Entrega 4)

O caminho é `árvore anotada → três endereços (--ir) → .mplb → VM`.

**Três endereços** (`mplc/intermediario.py`). Cada expressão devolve um
operando (constante, variável ou temporário `tN`); um nó binário grava o
resultado num temporário novo, então cada linha do `--ir` tem no máximo um
operador. Cada `Simbolo` da Entrega 3 vira um nome único na função — os `x`
sombreados viram `x`, `x.4`, `x.5` (o número é o do escopo; `.` não existe em
identificador, então não colide). A conversão `inteiro → real` é uma linha
explícita, `t1 = real t0`, posta só onde a semântica exige real. Por isso
`real x = 7 / 2;` vira `t0 = 7 / 2` seguido de `t1 = real t0`: a divisão é
entre inteiros e dá `3`, e só depois vira `3.000000`.

**O `.mplb`** (`mplc/gerador.py`) é texto: o código de uma máquina de pilha.
Cada variável, parâmetro e temporário ganha uma **posição** no registro de
ativação, com os parâmetros primeiro. Formato:

```
.funcao <nome> <nº de parâmetros> <nº de posições>
.local <posição> <nome>                    ; só documentação
    <linha do fonte>  <INSTRUÇÃO> [argumento]   ; comentário
<rótulo>:
.fim
```

A linha do fonte em cada instrução é o que deixa a VM relatar o erro de
execução na linha certa.

**A VM** (`mplc/vm.py`) tem uma pilha de **registros de ativação**; cada um
guarda as posições da chamada, a pilha de operandos dela e o `pc`. O ponto de
volta é o `pc` do registro de quem chamou, que fica parado embaixo até o
retorno. A VM não usa a recursão do Python: o laço é iterativo, e o estouro de
pilha é a regra `LIMITE_CHAMADAS` (10000 chamadas aninhadas), relatado na
linha da chamada com código de saída 2.

### Conjunto de instruções

Notação da pilha: `… a b → … r` quer dizer que `b` está no topo, os dois saem
e `r` entra. A pilha é a do registro de ativação atual.

| Instrução | Pilha | O que faz |
|---|---|---|
| `EMPILHA c` | `… → … c` | empilha a constante `c`: `42`, `2.5`, `verdadeiro`, `"oi\n"` |
| `CARREGA p` | `… → … v` | empilha o valor da posição `p` do registro atual |
| `GUARDA p` | `… v → …` | desempilha e grava na posição `p` |
| `SOMA` | `… a b → … a+b` | soma números; com dois textos, concatena |
| `SUBTRAI` | `… a b → … a-b` | subtração |
| `MULTIPLICA` | `… a b → … a*b` | multiplicação |
| `DIVIDE` | `… a b → … a/b` | dois inteiros: divisão inteira truncada para zero (`-7/2` é `-3`); senão, real. `b` zero é erro de execução |
| `RESTO` | `… a b → … a%b` | resto com o sinal do dividendo (`-7%3` é `-1`), calculado como `a - b*(a/b)`. `b` zero é erro de execução |
| `NEGA` | `… a → … -a` | menos unário |
| `IGUAL` | `… a b → … a==b` | lógico |
| `DIFERENTE` | `… a b → … a!=b` | lógico |
| `MENOR` | `… a b → … a<b` | lógico |
| `MENOR_IGUAL` | `… a b → … a<=b` | lógico |
| `MAIOR` | `… a b → … a>b` | lógico |
| `MAIOR_IGUAL` | `… a b → … a>=b` | lógico |
| `E` | `… a b → … a e b` | os dois lados já foram avaliados (sem curto-circuito) |
| `OU` | `… a b → … a ou b` | idem |
| `NAO` | `… a → … nao a` | negação lógica |
| `PARA_REAL` | `… i → … r` | converte inteiro em real (a única conversão implícita da MPL) |
| `DESVIA L` | `… → …` | continua no rótulo `L` |
| `DESVIA_SE_FALSO L` | `… c → …` | desempilha `c`; se for `falso`, continua em `L` |
| `CHAMA f` | `… a1..an → …` | tira os `n` argumentos do topo e cria um registro de ativação novo para `f`, com eles nas posições `0..n-1`; empilha o registro e começa `f` do início |
| `RETORNA_VALOR` | `… v → ` (chamador: `… → … v`) | desempilha `v`, descarta o registro atual e empilha `v` na pilha de quem chamou, que continua de onde parou |
| `RETORNA` | `… → ` | descarta o registro atual e volta para quem chamou; no `principal`, encerra o programa |
| `ESCREVA` | `… v → …` | desempilha e imprime no formato da seção 4.5 (real com 6 casas, `verdadeiro`/`falso`) |

### O programa do grupo

[`exemplos/hanoi.mpl`](exemplos/hanoi.mpl): como a MPL não converte número em
texto, o programa escreve essa conversão na própria MPL (divisão inteira e
resto, com recursão). Depois resolve a Torre de Hanói com 3 discos (recursão
dupla), conta os movimentos para até 20 discos e calcula raízes quadradas
pelo método de Newton. A saída esperada está em
[`exemplos/hanoi.saida`](exemplos/hanoi.saida).

```bash
./compilar exemplos/hanoi.mpl && ./executar exemplos/hanoi.mplb
```
