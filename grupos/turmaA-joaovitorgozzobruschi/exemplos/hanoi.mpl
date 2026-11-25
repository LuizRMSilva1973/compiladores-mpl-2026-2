// torre de hanoi, raiz quadrada e um conversor de numero pra texto, tudo
// escrito em MPL, compilado pelo nosso compilador e rodando na nossa VM.
//
// a MPL nao converte numero em texto ("disco " + 3 da erro de tipo), entao a
// primeira coisa e escrever essa conversao na propria linguagem: divisao
// inteira e resto, digito por digito, com recursao.

funcao texto digito(inteiro d) {
  se (d == 0) { retorne "0"; }
  se (d == 1) { retorne "1"; }
  se (d == 2) { retorne "2"; }
  se (d == 3) { retorne "3"; }
  se (d == 4) { retorne "4"; }
  se (d == 5) { retorne "5"; }
  se (d == 6) { retorne "6"; }
  se (d == 7) { retorne "7"; }
  se (d == 8) { retorne "8"; }
  retorne "9";
}

funcao texto emTexto(inteiro n) {
  se (n < 0) {
    retorne "-" + emTexto(-n);
  }
  se (n < 10) {
    retorne digito(n);
  }
  // lembrando que n / 10 e divisao INTEIRA: 123 / 10 da 12, nunca 12.3.
  retorne emTexto(n / 10) + digito(n % 10);
}

// recursao dupla: cada chamada tem o seu proprio n, origem, destino e
// auxiliar no registro de ativacao. devolve quantos movimentos fez.
funcao inteiro hanoi(inteiro n, texto origem, texto destino, texto auxiliar) {
  se (n == 0) {
    retorne 0;
  }
  inteiro antes = hanoi(n - 1, origem, auxiliar, destino);
  escreva("  disco " + emTexto(n) + ": " + origem + " -> " + destino);
  inteiro depois = hanoi(n - 1, auxiliar, destino, origem);
  retorne antes + 1 + depois;
}

// a mesma recursao, so que so contando.
funcao inteiro contar(inteiro n) {
  se (n == 0) {
    retorne 0;
  }
  retorne 2 * contar(n - 1) + 1;
}

// metodo de newton: x <- (x + a / x) / 2, ate o passo ficar bem pequeno.
funcao real raiz(real a) {
  real x = a;
  real passo = 1.0;
  enquanto (passo > 0.000001 ou passo < -0.000001) {
    real novo = (x + a / x) / 2;
    passo = novo - x;
    x = novo;
  }
  retorne x;
}

funcao vazio principal() {
  escreva("== numero para texto ==");
  escreva(emTexto(2026) + " tem " + emTexto(4) + " digitos");
  escreva(emTexto(-305));

  escreva("== torre de hanoi com 3 discos ==");
  inteiro movimentos = hanoi(3, "A", "C", "B");
  escreva("movimentos: " + emTexto(movimentos));

  escreva("== quantos movimentos para n discos (2^n - 1) ==");
  inteiro n = 1;
  enquanto (n <= 20) {
    se (n % 5 == 0) {
      escreva(emTexto(n) + " discos: " + emTexto(contar(n)) + " movimentos");
    }
    n = n + 1;
  }

  escreva("== raiz quadrada por Newton ==");
  escreva(raiz(2.0));
  escreva(raiz(81));
  escreva(raiz(2.0) * raiz(2.0));
}
