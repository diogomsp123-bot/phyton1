from itertools import product
import re
import streamlit as st

# ============================================================
# LOGICA PROPOSICIONAL (Núcleo)
# ============================================================

OPERATORS = {"~", "&", "|", "^", "->", "<->"}
PRECEDENCE = {"<->": 1, "->": 2, "|": 3, "^": 3, "&": 4, "~": 5}
RIGHT_ASSOCIATIVE = {"~", "->", "<->"}


def tokenize(expression):
    expression = (
        expression.replace("¬", "~")
        .replace("∧", "&")
        .replace("∨", "|")
        .replace("→", "->")
        .replace("↔", "<->")
        .replace("⊕", "^")
    )
    pattern = r"<->|->|[()~&|^]|[A-Za-z][A-Za-z0-9_]*"
    tokens = re.findall(pattern, expression.replace(" ", ""))
    if "".join(tokens) != expression.replace(" ", ""):
        raise ValueError("Há símbolos inválidos na expressão.")
    if not tokens:
        raise ValueError("A expressão está vazia.")
    return tokens


def to_postfix(expression):
    tokens = tokenize(expression)
    output, stack = [], []
    previous = None

    for token in tokens:
        if token not in OPERATORS and token not in ("(", ")"):
            if previous is not None and (
                previous not in OPERATORS and previous != "(" or previous == ")"
            ):
                raise ValueError("Falta um operador entre duas proposições.")
            output.append(token)
        elif token == "(":
            if previous is not None and (
                previous not in OPERATORS and previous != "(" or previous == ")"
            ):
                raise ValueError("Falta um operador antes do parênteses.")
            stack.append(token)
        elif token == ")":
            if previous in (None, "(", *OPERATORS):
                raise ValueError("Parênteses vazio ou operador incompleto.")
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("Parênteses desbalanceados.")
            stack.pop()
        else:
            if token == "~":
                if previous is not None and (
                    previous not in OPERATORS and previous != "(" or previous == ")"
                ):
                    raise ValueError(
                        "A negação deve aparecer antes da proposição."
                    )
            else:
                if previous is None or previous in OPERATORS or previous == "(":
                    raise ValueError(
                        f"O operador {token} está sem operando à esquerda."
                    )
            while stack and stack[-1] in OPERATORS:
                top = stack[-1]
                should_pop = PRECEDENCE[top] > PRECEDENCE[token] or (
                    PRECEDENCE[top] == PRECEDENCE[token]
                    and token not in RIGHT_ASSOCIATIVE
                )
                if not should_pop:
                    break
                output.append(stack.pop())
            stack.append(token)
        previous = token

    if previous in OPERATORS or previous == "(":
        raise ValueError(
            "A expressão termina com um operador ou parênteses incompleto."
        )
    while stack:
        top = stack.pop()
        if top in ("(", ")"):
            raise ValueError("Parênteses desbalanceados.")
        output.append(top)

    depth = 0
    for token in output:
        if token == "~":
            if depth < 1:
                raise ValueError("Negação sem proposição.")
        elif token in OPERATORS:
            if depth < 2:
                raise ValueError(
                    f"Operador {token} sem operandos suficientes."
                )
            depth -= 1
        else:
            depth += 1
    if depth != 1:
        raise ValueError("Expressão lógica inválida.")
    return output


def variables_in(postfix):
    return sorted({token for token in postfix if token not in OPERATORS})


def evaluate(postfix, valuation):
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


def exactly_one_sop(variables, rows, expression_index=0):
    terms = []
    for valuation, results in rows:
        if results[expression_index]:
            literals = [v if valuation[v] else f"~{v}" for v in variables]
            terms.append("(" + " & ".join(literals) + ")")
    return " | ".join(terms) if terms else "FALSO (contradição)"


def gate_list(expression):
    postfix = to_postfix(expression)
    gates = []
    for token in postfix:
        if token in OPERATORS:
            gate = {
                "~": "NOT",
                "&": "AND",
                "|": "OR",
                "^": "XOR",
                "->": "OR + NOT (implicação)",
                "<->": "XNOR (equivalência)",
            }
            gates.append(gate[token])
    return gates


# ============================================================
# INTERFACE GRÁFICA (Streamlit)
# ============================================================

st.set_page_config(
    page_title="Calculadora de Lógica Proposicional", layout="wide"
)

st.title("🧮 Calculadora de Lógica Proposicional")
st.markdown(
    "Interface interativa para análise de expressões lógicas, tabelas-verdade, equivalências e argumentos."
)

# Sidebar para navegação
st.sidebar.header("Menu de Tarefas")
tarefa = st.sidebar.selectbox(
    "Escolha a funcionalidade:",
    [
        "1. Tabela-Verdade e Classificação",
        "2. Equivalência Lógica e Argumentos",
        "3. Resolução de Problemas com Condições",
        "4. Bônus: Soma de Produtos e Portas",
    ],
)

# Guia de ajuda rápida na barra lateral
st.sidebar.markdown("---")
st.sidebar.markdown(
    """**Operadores Aceitos:**
- Negação: `~` ou `¬`
- Conjunção (E): `&` ou `∧`
- Disjunção (OU): `|` ou `∨`
- OU Exclusivo: `^` ou `⊕`
- Implicação: `->` ou `→`
- Bicondicional: `<->` ou `↔`"""
)

# -------------------------------------------------
# TAREFA 1
# -------------------------------------------------
if tarefa.startswith("1"):
    st.header("Tabela-Verdade e Classificação")
    expr = st.text_input(
        "Digite a expressão lógica:", value="(p -> q) & p"
    )

    if st.button("Gerar Tabela-Verdade"):
        try:
            variables, rows, postfixes = truth_table([expr])
            headers = variables + [expr]

            # Montar dados para tabela formatada
            data = []
            for valuation, results in rows:
                row_data = [vf(valuation[v]) for v in variables] + [
                    vf(x) for x in results
                ]
                data.append(row_data)

            import pandas as pd

            df = pd.DataFrame(data, columns=headers)
            st.dataframe(df, use_container_width=True)

            # Classificação
            outcomes = [result[0] for _, result in rows]
            if all(outcomes):
                classification = "TAUTOLOGIA"
                st.success(f"Classificação: **{classification}**")
            elif not any(outcomes):
                classification = "CONTRADIÇÃO"
                st.error(f"Classificação: **{classification}**")
            else:
                classification = "CONTINGÊNCIA"
                st.info(f"Classificação: **{classification}**")

        except Exception as e:
            st.error(f"Erro na expressão: {e}")

# -------------------------------------------------
# TAREFA 2
# -------------------------------------------------
elif tarefa.startswith("2"):
    st.header("Equivalência Lógica e Validade de Argumentos")
    sub_opcao = st.radio(
        "Selecione o modo:",
        ["Verificar Equivalência", "Verificar Validade de Argumento"],
    )

    if sub_opcao == "Verificar Equivalência":
        st.subheader("Equivalência entre duas sentenças")
        first = st.text_input("Primeira sentença:", value="p -> q")
        second = st.text_input("Segunda sentença:", value="~p | q")

        if st.button("Verificar Equivalência"):
            try:
                variables, rows, _ = truth_table([first, second])
                equivalent = all(results[0] == results[1] for _, results in rows)

                headers = variables + [first, second]
                data = [
                    [vf(val[v]) for v in variables] + [vf(res[0]), vf(res[1])]
                    for val, res in rows
                ]
                import pandas as pd

                st.dataframe(pd.DataFrame(data, columns=headers), use_container_width=True)

                if equivalent:
                    st.success("As sentenças são **LOGICAMENTE EQUIVALENTES**.")
                else:
                    st.error("As sentenças **NÃO** são logicamente equivalentes.")
                    for valuation, results in rows:
                        if results[0] != results[1]:
                            diffs = ", ".join(
                                f"{v}={vf(valuation[v])}" for v in variables
                            )
                            st.write(f"Valoração que mostra a diferença: `{diffs}`")
                            break
            except Exception as e:
                st.error(f"Erro: {e}")

    else:
        st.subheader("Validade de Argumento")
        premises_text = st.text_area(
            "Premissas (uma por linha):", value="p -> q\np"
        )
        conclusion = st.text_input("Conclusão:", value="q")

        if st.button("Verificar Validade"):
            try:
                premises = [p.strip() for p in premises_text.split("\n") if p.strip()]
                if not premises:
                    st.warning("Insira pelo menos uma premissa.")
                else:
                    expressions = premises + [conclusion]
                    variables, rows, _ = truth_table(expressions)
                    
                    counterexample = None
                    for valuation, results in rows:
                        if all(results[:-1]) and not results[-1]:
                            counterexample = (valuation, results)
                            break

                    headers = variables + [f"P{i+1}" for i in range(len(premises))] + ["Conclusão"]
                    data = [
                        [vf(val[v]) for v in variables] + [vf(x) for x in res]
                        for val, res in rows
                    ]
                    import pandas as pd
                    st.dataframe(pd.DataFrame(data, columns=headers), use_container_width=True)

                    if counterexample is None:
                        st.success("ARGUMENTO VÁLIDO: Não existe linha com premissas V e conclusão F.")
                    else:
                        valuation, results = counterexample
                        st.error("ARGUMENTO INVÁLIDO. Contraexemplo encontrado:")
                        diffs = ", ".join(f"{v}={vf(valuation[v])}" for v in variables)
                        st.write(f"Valoração: `{diffs}`")
            except Exception as e:
                st.error(f"Erro: {e}")

# -------------------------------------------------
# TAREFA 3
# -------------------------------------------------
elif tarefa.startswith("3"):
    st.header("Resolução de Problemas com Múltiplas Condições")
    conditions_text = st.text_area(
        "Condições (uma por linha):", value="p | q\n~p -> r"
    )
    restriction_type = st.selectbox(
        "Restrição Opcional:",
        [
            "Nenhuma restrição adicional",
            "Exatamente uma das proposições escolhidas é verdadeira",
            "Exatamente uma das condições/sentenças é verdadeira",
        ],
    )

    names = ""
    if restriction_type.startswith("Exatamente uma das proposições"):
        names = st.text_input("Quais proposições? (separadas por vírgula):", value="p,q,r")

    if st.button("Resolver Problema"):
        try:
            conditions = [c.strip() for c in conditions_text.split("\n") if c.strip()]
            if not conditions:
                st.warning("Informe pelo menos uma condição.")
            else:
                variables, rows, _ = truth_table(conditions)
                
                if restriction_type.startswith("Exatamente uma das proposições"):
                    prop_list = [n.strip() for n in names.split(",") if n.strip()]
                    valid = [
                        val for val, res in rows
                        if all(res) and sum(val[n] for n in prop_list if n in val) == 1
                    ]
                elif restriction_type.startswith("Exatamente uma das condições"):
                    valid = [
                        val for val, res in rows
                        if all(res) and sum(res) == 1
                    ]
                else:
                    valid = [val for val, res in rows if all(res)]

                st.write(f"Total de valorações satisfatórias: **{len(valid)}**")
                if valid:
                    data = [[vf(val[v]) for v in variables] for val in valid]
                    import pandas as pd
                    st.dataframe(pd.DataFrame(data, columns=variables), use_container_width=True)
                else:
                    st.info("Nenhuma valoração satisfaz as condições dadas.")
        except Exception as e:
            st.error(f"Erro: {e}")

# -------------------------------------------------
# TAREFA 4 (BÔNUS)
# -------------------------------------------------
elif tarefa.startswith("4"):
    st.header("Bônus: Soma de Produtos e Portas Lógicas")
    expr = st.text_input("Digite a expressão:", value="p & q | ~r")

    if st.button("Analisar Expressão"):
        try:
            variables, rows, _ = truth_table([expr])
            
            st.subheader("Soma de Produtos Canônica (SOP)")
            sop = exactly_one_sop(variables, rows)
            st.code(sop, language="text")

            st.subheader("Portas Lógicas Necessárias")
            gates = gate_list(expr)
            if gates:
                for idx, g in enumerate(gates, 1):
                    st.markdown(f"- Porta {idx}: **{g}**")
            else:
                st.write("Nenhuma porta necessária (expressão simples).")

        except Exception as e:
            st.error(f"Erro: {e}")