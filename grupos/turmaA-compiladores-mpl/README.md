## Entrega 1 — Analisador Léxico

O analisador léxico transforma o código-fonte da MPL em uma sequência de
tokens. Cada token possui tipo, lexema, linha e coluna.

### Tabela de Tokens

| Token | Expressão regular / reconhecimento |
|---|---|
| `ID` | `[a-zA-Z_][a-zA-Z0-9_]*` |
| `INTEIRO` | `[0-9]+` |
| `REAL` | `[0-9]+\.[0-9]+` |
| `LOGICO` | `verdadeiro` \| `falso` |
| `TEXTO` | `"(...)"`, permitindo os escapes `\n`, `\t`, `\"` e `\\` |
| `FUNCAO` | `funcao` |
| `RETORNE` | `retorne` |
| `SE` | `se` |
| `SENAO` | `senao` |
| `ENQUANTO` | `enquanto` |
| `ESCREVA` | `escreva` |
| `TIPO_INTEIRO` | `inteiro` |
| `TIPO_REAL` | `real` |
| `TIPO_LOGICO` | `logico` |
| `TIPO_TEXTO` | `texto` |
| `TIPO_VAZIO` | `vazio` |
| `E` | `e` |
| `OU` | `ou` |
| `NAO` | `nao` |
| `MAIS` | `+` |
| `MENOS` | `-` |
| `VEZES` | `*` |
| `DIVIDE` | `/` |
| `RESTO` | `%` |
| `IGUAL` | `==` |
| `DIFERENTE` | `!=` |
| `MENOR` | `<` |
| `MENOR_IGUAL` | `<=` |
| `MAIOR` | `>` |
| `MAIOR_IGUAL` | `>=` |
| `ATRIBUI` | `=` |
| `ABRE_PAR` | `(` |
| `FECHA_PAR` | `)` |
| `ABRE_CHAVE` | `{` |
| `FECHA_CHAVE` | `}` |
| `VIRGULA` | `,` |
| `PONTO_VIRGULA` | `;` |
| `FIM_ARQUIVO` | fim da entrada |

### Comentários

| Tipo | Forma reconhecida |
|---|---|
| Comentário de linha | `//` até o fim da linha |
| Comentário de bloco | `/*` até o primeiro `*/` |

### Observações

- Identificadores são sensíveis a maiúsculas e minúsculas.
- Palavras reservadas são reconhecidas antes de `ID`.
- `<=`, `>=`, `==` e `!=` são reconhecidos antes dos operadores de um caractere.
- Números reais exigem dígitos antes e depois do ponto.
- Textos aceitam apenas os escapes `\n`, `\t`, `\"` e `\\`.
- Espaços, tabulações, quebras de linha e `\r` são ignorados.

## Entrega 2 — Analisador Sintático e Árvore

O analisador sintático transforma a sequência de tokens em uma árvore sintática
abstrata (AST), seguindo a especificação da linguagem e os rótulos definidos em
CONTRATOS.md.

### Gramática implementada (EBNF)

```ebnf
<programa> ::= { <funcao> } EOF

<funcao> ::= FUNCAO <tipo_retorno> ID ABRE_PAR [ <parametros> ] FECHA_PAR <bloco>

<parametros> ::= <parametro> { VIRGULA <parametro> }
<parametro> ::= <tipo> ID

<tipo_retorno> ::= TIPO_INTEIRO
                 | TIPO_REAL
                 | TIPO_LOGICO
                 | TIPO_TEXTO
                 | TIPO_VAZIO

<tipo> ::= TIPO_INTEIRO
         | TIPO_REAL
         | TIPO_LOGICO
         | TIPO_TEXTO

<bloco> ::= ABRE_CHAVE { <comando> } FECHA_CHAVE

<comando> ::= <declaracao>
            | <comando_id>
            | <condicional>
            | <repeticao>
            | <escrita>
            | <retorno>
            | <bloco>

<declaracao> ::= <tipo> ID [ ATRIBUI <expressao> ] PONTO_VIRGULA

<comando_id> ::= ID ATRIBUI <expressao> PONTO_VIRGULA
               | <chamada> PONTO_VIRGULA

<condicional> ::= SE ABRE_PAR <expressao> FECHA_PAR <bloco>
                  [ SENAO <bloco> ]

<repeticao> ::= ENQUANTO ABRE_PAR <expressao> FECHA_PAR <bloco>

<escrita> ::= ESCREVA ABRE_PAR <expressao> FECHA_PAR PONTO_VIRGULA

<retorno> ::= RETORNE [ <expressao> ] PONTO_VIRGULA

<chamada> ::= ID ABRE_PAR [ <argumentos> ] FECHA_PAR
<argumentos> ::= <expressao> { VIRGULA <expressao> }

<expressao> ::= <ou>

<ou> ::= <e> { OU <e> }

<e> ::= <igualdade> { E <igualdade> }

<igualdade> ::= <relacional> { (IGUAL | DIFERENTE) <relacional> }

<relacional> ::= <aditiva> { (MENOR | MENOR_IGUAL | MAIOR | MAIOR_IGUAL) <aditiva> }

<aditiva> ::= <multiplicativa> { (MAIS | MENOS) <multiplicativa> }

<multiplicativa> ::= <unario> { (VEZES | DIVIDE | RESTO) <unario> }

<unario> ::= (NAO | MENOS) <unario> | <primario>

<primario> ::= INTEIRO
             | REAL
             | LOGICO
             | TEXTO
             | ID
             | <chamada>
             | ABRE_PAR <expressao> FECHA_PAR
```

## Entrega 3 — Tabela de Símbolos e Verificação de Tipos

A análise semântica (`mplc/semantica.py`) percorre a AST em duas passadas: a
primeira coleta a assinatura de todas as funções no escopo global (permitindo
chamar uma função antes de ela aparecer no arquivo e recursão indireta), e a
segunda visita os corpos, abrindo escopos, declarando nomes e conferindo os
tipos de cada expressão.

### Estrutura dos escopos

Representamos os escopos como um **dicionário encadeado**: cada `Escopo` tem
um dicionário próprio de símbolos (que preserva a ordem de declaração) e um
ponteiro para o escopo pai. Procurar um nome é subir por essa cadeia até o
global, o que dá o sombreamento de graça — o nome mais interno é encontrado
primeiro e, ao fechar o bloco, basta voltar o escopo atual para o pai. Além da
cadeia, todos os escopos ficam guardados numa lista na ordem em que abriram,
porque o `--tabela` precisa mostrar inclusive os escopos que já fecharam, e
porque na Entrega 4 cada símbolo (já anotado no nó da AST) poderá receber sua
posição de memória sem precisar refazer a busca por nome.

### Regras verificadas

- Escopos aninhados com sombreamento; o corpo da função abre dois escopos
  (parâmetros e bloco) e cada `se`/`enquanto`/bloco abre mais um.
- Redeclaração no mesmo escopo, variável ou função não declarada, função
  duplicada e ausência de `funcao vazio principal()`.
- Conversão implícita apenas de `inteiro` para `real` (atribuição, argumento,
  retorno e operadores aritméticos/relacionais).
- Tipos dos operadores conforme a seção 3.2 da especificação; condição de
  `se`/`enquanto` precisa ser `logico`.
- Quantidade e tipo dos argumentos; função `vazio` só pode ser usada como
  comando.
- `retorne` com valor em função `vazio`, ou sem valor em função não-`vazio`.
- Retorno garantido em todos os caminhos, olhando só a estrutura: `retorne`
  garante; um bloco garante se algum comando dele garante; `se` só garante com
  `senao` e os dois lados garantindo; `enquanto` nunca garante.
## Entrega 4 — Geração de código e máquina virtual

O comando `./compilar --ir programa.mpl` mostra o código de três endereços.
Cada expressão é decomposta em temporários com uma operação por linha.
Os símbolos da análise semântica recebem posições distintas, inclusive quando
duas variáveis de blocos diferentes têm o mesmo nome.

O comando `./compilar programa.mpl` traduz esse código para um arquivo
`.mplb` UTF-8 legível. Cada linha contém um mnemônico e uma lista JSON de
argumentos. Textos usam escapes JSON para manter uma instrução por linha.
`./executar programa.mplb` interpreta as instruções.

### Conjunto de instruções

A pilha abaixo é escrita da base para o topo. `S` representa o conteúdo
anterior. Locais incluem as variáveis e os temporários da chamada atual.

| Instrução | Efeito na pilha e execução |
|---|---|
| `POS [linha, coluna]` | `S → S`. Atualiza a posição usada nos erros de execução. |
| `PUSH [valor]` | `S → S, valor`. Empilha uma constante JSON. |
| `LOAD [local]` | `S → S, valor`. Empilha o conteúdo de um local da chamada atual. |
| `STORE [local]` | `S, valor → S`. Guarda o topo em um local. |
| `REAL []` | `S, inteiro → S, real`. Converte o topo para real. |
| `BINARY [op]` | `S, a, b → S, resultado`. Aplica `+ - * / % == != < <= > >= e ou`, nessa ordem de operandos. |
| `UNARY [op]` | `S, a → S, resultado`. Aplica `-` ou `nao`. |
| `JMP [rotulo]` | `S → S`. Salta para o rótulo. |
| `JZ [rotulo]` | `S, condicao → S`. Salta se o topo removido for falso. |
| `CALL [nome, n]` | `S, arg1, ..., argN → S` na entrada. Cria locais próprios e salva o endereço de retorno, a base da pilha e a posição do chamador. |
| `RET []` | Remove o resultado da chamada, restaura o registro anterior e produz `S, resultado` no chamador. No principal encerra a execução. |
| `PRINT []` | `S, valor → S`. Imprime o valor e uma quebra de linha, com seis casas para reais e verdadeiro/falso para lógicos. |
| `FUNC [nome, parametros]` | `S → S`. Define a entrada e a ordem dos parâmetros de uma função. |
| `END []` | `S → S`. Marca o fim da definição da função. |
| `LABEL [rotulo]` | `S → S`. Define um destino de salto. |

Funções vazias retornam `null` internamente. O resultado de chamadas usadas
como comando é guardado em um temporário, mantendo a pilha equilibrada.
O interpretador usa registros de ativação explícitos e um limite de 1000
chamadas suspensas, com erro de execução ao ultrapassá-lo.

As conversões para real ocorrem depois de avaliar a expressão inteira em
atribuições, argumentos e retornos. Assim, `real x = 7 / 2;` guarda
`3.000000`. Na divisão inteira o quociente é truncado em direção a zero,
e o resto é calculado por `a - (a / b) * b`, com o sinal do dividendo.
Os operadores `e` e `ou` avaliam ambos os operandos.

### Programa de apresentação

`exemplos/financiamento.mpl` simula uma dívida de 1000, juros mensais de 2%
e pagamentos de até 200. Mostra o saldo de cada mês, ajusta a última parcela
e calcula o total pago e os juros. Exercita funções, reais, repetição,
condicional e variáveis de bloco.

```sh
./compilar exemplos/financiamento.mpl
./executar exemplos/financiamento.mplb
make verificar E=4
```
