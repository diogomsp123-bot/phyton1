from itertools import product
import re

# ============================================================
# Interpretador de logica proposicional
# Operadores aceitos:
#   ~p       negacao
#   p & q    conjuncao (E)
#   p | q    disjuncao inclusiva (OU)
#   p ^ q    OU exclusivo
#   p -> q   implicacao
#   p <-> q  bicondicional
# Parenteses podem ser usados para agrupar expressoes.
# ============================================================

OPERATORS = {"~", "&", "|", "^", "->", "<->"}
PRECEDENCE = {"<->": 1, "->": 2, "|": 3, "^": 3, "&": 4, "~": 5}
RIGHT_ASSOCIATIVE = {"~", "->", "<->"}


def tokenize(expression):
    """Transforma uma expressao em tokens e valida seus caracteres."""
    expression = expression.replace("¬", "~").replace("∧", "&")
    expression = expression.replace("∨", "|").replace("→", "->")
    expression = expression.replace("↔", "<->").replace("⊕", "^")
    pattern = r"<->|->|[()~&|^]|[A-Za-z][A-Za-z0-9_]*"
    tokens = re.findall(pattern, expression.replace(" ", ""))
    if "".join(tokens) != expression.replace(" ", ""):
        raise ValueError("Ha simbolos invalidos na expressao.")
    if not tokens:
        raise ValueError("A expressao esta vazia.")
    return tokens


def to_postfix(expression):
    """Converte a expressao infixa para notacao posfixa (RPN)."""
    tokens = tokenize(expression)
    output, stack = [], []
    previous = None

    for token in tokens:
        if token not in OPERATORS and token not in ("(", ")"):
            if previous is not None and (
                previous not in OPERATORS and previous != "("
                or previous == ")"
            ):
                raise ValueError("Falta um operador entre duas proposicoes.")
            output.append(token)
        elif token == "(":
            if previous is not None and (
                previous not in OPERATORS and previous != "("
                or previous == ")"
            ):
                raise ValueError("Falta um operador antes do parenteses.")
            stack.append(token)
        elif token == ")":
            if previous in (None, "(", *OPERATORS):
                raise ValueError("Parenteses vazio ou operador incompleto.")
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("Parenteses desbalanceados.")
            stack.pop()
        else:
            if token == "~":
                if previous is not None and (
                    previous not in OPERATORS and previous != "("
                    or previous == ")"
                ):
                    raise ValueError("A negacao deve aparecer antes da proposicao.")
            else:
                if previous is None or previous in OPERATORS or previous == "(":
                    raise ValueError(f"O operador {token} esta sem operando a esquerda.")
            while stack and stack[-1] in OPERATORS:
                top = stack[-1]
                should_pop = (
                    PRECEDENCE[top] > PRECEDENCE[token]
                    or (PRECEDENCE[top] == PRECEDENCE[token]
                        and token not in RIGHT_ASSOCIATIVE)
                )
                if not should_pop:
                    break
                output.append(stack.pop())
            stack.append(token)
        previous = token

    if previous in OPERATORS or previous == "(":
        raise ValueError("A expressao termina com um operador ou parenteses incompleto.")
    while stack:
        top = stack.pop()
        if top in ("(", ")"):
            raise ValueError("Parenteses desbalanceados.")
        output.append(top)

    # Confere a quantidade de operandos exigida pelos operadores.
    depth = 0
    for token in output:
        if token == "~":
            if depth < 1:
                raise ValueError("Negacao sem proposicao.")
        elif token in OPERATORS:
            if depth < 2:
                raise ValueError(f"Operador {token} sem operandos suficientes.")
            depth -= 1
        else:
            depth += 1
    if depth != 1:
        raise ValueError("Expressao logica invalida.")
    return output


def variables_in(postfix):
    return sorted({token for token in postfix if token not in OPERATORS})


def evaluate(postfix, valuation):
    """Avalia a expressao e retorna tambem os valores das subexpressoes."""
    stack = []
    for token in postfix:
        if token not in OPERATORS:
            stack.append((valuation[token], token))
        elif token == "~":
            value, text = stack.pop()
            stack.append((not value, f"~({text})"))
        else:
            right, right_text = stack.pop()
            left, left_text = stack.pop()
            if token == "&":
                value = left and right
            elif token == "|":
                value = left or right
            elif token == "^":
                value = left != right
            elif token == "->":
                value = (not left) or right
            elif token == "<->":
                value = left == right
            stack.append((value, f"({left_text} {token} {right_text})"))
    return stack[0][0]


def truth_table(expressions):
    """Cria a tabela de todas as expressoes, compartilhando as variaveis."""
    postfixes = [to_postfix(expr) for expr in expressions]
    variables = sorted(set().union(*(set(variables_in(p)) for p in postfixes)))
    rows = []
    for values in product([True, False], repeat=len(variables)):
        valuation = dict(zip(variables, values))
        results = [evaluate(p, valuation) for p in postfixes]
        rows.append((valuation, results))
    return variables, rows, postfixes


def vf(value):
    return "V" if value else "F"


def print_table(expressions, show_classification=True):
    variables, rows, postfixes = truth_table(expressions)
    headers = variables + expressions
    data = []
    for valuation, results in rows:
        data.append([vf(valuation[v]) for v in variables] + [vf(x) for x in results])

    widths = [max(len(str(h)), max(len(row[i]) for row in data))
              for i, h in enumerate(headers)]
    print("\n" + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)))
    print("-+-".join("-" * w for w in widths))
    for row in data:
        print(" | ".join(row[i].ljust(widths[i]) for i in range(len(headers))))

    if show_classification:
        for expr, idx in zip(expressions, range(len(expressions))):
            outcomes = [result[idx] for _, result in rows]
            if all(outcomes):
                classification = "TAUTOLOGIA"
            elif not any(outcomes):
                classification = "CONTRADICAO"
            else:
                classification = "CONTINGENCIA"
            print(f"\n{expr}: {classification}")
    return variables, rows, postfixes


def ask_expression(prompt="Digite a expressao logica: "):
    return input(prompt).strip()


def task1():
    print("\n=== TAREFA 1: TABELA-VERDADE ===")
    expr = ask_expression()
    print_table([expr])


def task2_equivalence():
    print("\n=== EQUIVALENCIA LOGICA ===")
    first = ask_expression("Primeira sentenca: ")
    second = ask_expression("Segunda sentenca: ")
    variables, rows, _ = truth_table([first, second])
    equivalent = all(results[0] == results[1] for _, results in rows)
    print_table([first, second], show_classification=False)
    print("\nAs sentencas sao LOGICAMENTE EQUIVALENTES." if equivalent
          else "\nAs sentencas NAO sao logicamente equivalentes.")
    if not equivalent:
        for valuation, results in rows:
            if results[0] != results[1]:
                print("Valoração que mostra a diferenca:",
                      ", ".join(f"{v}={vf(valuation[v])}" for v in variables))
                break


def task2_argument():
    print("\n=== VALIDADE DE ARGUMENTO ===")
    print("Digite as premissas uma por vez. Deixe em branco para terminar.")
    premises = []
    while True:
        expr = input(f"Premissa {len(premises) + 1} (Enter termina): ").strip()
        if not expr:
            break
        premises.append(expr)
    if not premises:
        print("E necessario informar pelo menos uma premissa.")
        return
    conclusion = ask_expression("Conclusao: ")
    expressions = premises + [conclusion]
    variables, rows, _ = truth_table(expressions)
    counterexample = None
    for valuation, results in rows:
        if all(results[:-1]) and not results[-1]:
            counterexample = (valuation, results)
            break
    print_table(expressions, show_classification=False)
    if counterexample is None:
        print("\nARGUMENTO VALIDO: nao existe linha com premissas V e conclusao F.")
    else:
        valuation, results = counterexample
        print("\nARGUMENTO INVALIDO. Contraexemplo:")
        print(", ".join(f"{v}={vf(valuation[v])}" for v in variables))
        print("Premissas:", ", ".join(vf(x) for x in results[:-1]))
        print("Conclusao:", vf(results[-1]))


def task2():
    print("\n=== TAREFA 2: EQUIVALENCIA E ARGUMENTOS ===")
    print("1 - Verificar equivalencia entre duas sentencas")
    print("2 - Verificar validade de um argumento")
    choice = input("Escolha: ").strip()
    if choice == "1":
        task2_equivalence()
    elif choice == "2":
        task2_argument()
    else:
        print("Opcao invalida.")


def task3():
    print("\n=== TAREFA 3: RESOLUCAO DE PROBLEMAS ===")
    print("Digite cada condicao como uma sentenca logica.")
    print("Exemplo: p | q")
    print("Deixe em branco para terminar.")
    conditions = []
    while True:
        expr = input(f"Condicao {len(conditions) + 1}: ").strip()
        if not expr:
            break
        conditions.append(expr)
    if not conditions:
        print("Informe pelo menos uma condicao.")
        return

    print("\nRestricao opcional:")
    print("1 - Nenhuma restricao adicional")
    print("2 - Exatamente uma das proposicoes escolhidas e verdadeira")
    print("3 - Exatamente uma das sentencas/condicoes e verdadeira")
    restriction = input("Escolha (Enter = nenhuma): ").strip()

    if restriction == "2":
        names = input("Quais proposicoes? Separe por virgula (ex.: p,q,r): ")
        names = [n.strip() for n in names.split(",") if n.strip()]
        if not names:
            print("Nenhuma proposicao informada.")
            return
        # Exatamente uma variavel verdadeira: soma dos valores == 1.
        variables, rows, _ = truth_table(conditions)
        unknown = set(names) - set(variables)
        if unknown:
            print("Proposicoes nao usadas nas condicoes:", ", ".join(sorted(unknown)))
            return
        valid = []
        for valuation, results in rows:
            if all(results) and sum(valuation[n] for n in names) == 1:
                valid.append(valuation)
    elif restriction == "3":
        variables, rows, _ = truth_table(conditions)
        valid = [valuation for valuation, results in rows
                 if all(results) and sum(results) == 1]
    elif restriction in ("", "1"):
        variables, rows, _ = truth_table(conditions)
        valid = [valuation for valuation, results in rows if all(results)]
    else:
        print("Opcao invalida.")
        return

    print("\nValorações que satisfazem todas as condicoes:")
    if not valid:
        print("Nenhuma valoração satisfaz as condicoes.")
    else:
        for index, valuation in enumerate(valid, start=1):
            print(f"{index}. " + ", ".join(f"{v}={vf(valuation[v])}" for v in variables))
        print(f"\nTotal: {len(valid)} valoração(oes).")
        if len(valid) == 1:
            print("Existe uma unica solucao.")


def exactly_one_sop(variables, rows, expression_index=0):
    """Gera soma de produtos canonica para as linhas em que a expressao e V."""
    terms = []
    for valuation, results in rows:
        if results[expression_index]:
            literals = [v if valuation[v] else f"~{v}" for v in variables]
            terms.append("(" + " & ".join(literals) + ")")
    return " | ".join(terms) if terms else "FALSO (contradicao)"


def gate_list(expression):
    """Mostra uma lista textual das portas correspondentes aos operadores."""
    postfix = to_postfix(expression)
    gates = []
    for token in postfix:
        if token in OPERATORS:
            gate = {"~": "NOT", "&": "AND", "|": "OR", "^": "XOR",
                    "->": "OR + NOT (implicacao: ~p | q)",
                    "<->": "XNOR (equivalencia)"}
            gates.append(gate[token])
    return gates


def bonus():
    print("\n=== BONUS: SOMA DE PRODUTOS E PORTAS LOGICAS ===")
    expr = ask_expression()
    variables, rows, _ = truth_table([expr])
    print_table([expr])
    print("\nSoma de produtos canonica:")
    print(exactly_one_sop(variables, rows))
    print("\nPortas necessarias (descricao textual):")
    gates = gate_list(expr)
    print(", ".join(gates) if gates else "Nenhuma porta: a expressao e uma unica proposicao.")


def main():
    while True:
        print("\n" + "=" * 54)
        print(" CALCULADORA DE LOGICA PROPOSICIONAL")
        print("=" * 54)
        print("1 - Tabela-verdade e classificacao")
        print("2 - Equivalencia logica ou validade de argumento")
        print("3 - Resolver problema com varias condicoes")
        print("4 - Bonus: soma de produtos e portas logicas")
        print("0 - Sair")
        choice = input("Escolha uma opcao: ").strip()
        try:
            if choice == "1":
                task1()
            elif choice == "2":
                task2()
            elif choice == "3":
                task3()
            elif choice == "4":
                bonus()
            elif choice == "0":
                print("Ate mais!")
                break
            else:
                print("Opcao invalida.")
        except (ValueError, KeyError, IndexError) as error:
            print(f"\nErro na expressao: {error}")
            print("Confira os operadores e os parenteses e tente novamente.")


if __name__ == "__main__":
    main()
