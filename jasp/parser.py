from typing import List
from tokenizer import Token

def parse(tokens: List[Token]) -> List[List]:
    """
    Transforms a list of tokens in to a list of expressions representing the
    Abstract Syntax Tree.

    E.g. for the input:
        (+ 3 4)
        (* 2 (+ 4 3))
    the following tokens are generated:
        [Token('paren', 'open'),
         Token('arithmetic', '+'),
         Token('number', '3'),
         Token('number', '4'),
         Token('paren', 'close'),
         Token('paren', 'open'),
         Token('arithmetic', '*'),
         Token('number', '2'),
         Token('paren', 'open'),
         Token('arithmetic', '+'),
         Token('number', '4'),
         Token('number', '3'),
         Token('paren', 'close'),
         Token('paren', 'close')]
    and the return value is a nested list of lists, each nested list
    representing a separate expression:
        [[Token('arithmetic', '+'), Token('number', '3'),
        Token('number', '4')], [Token('arithmetic', '*'),
        Token('number', '2'), [Token('arithmetic', '+'),
        Token('number', '4'), Token('number', '3')]]]

    The grammar:
        string: "..."
        number: [1-9][0-9]*
        identifier: [a-z_0-9]+
        atom: string|number
        operator: +,-,*,/,=,<,<=,>,>=
        expr: atom|identifier|(operator expr+)
        keyword: if, let, fn
    """
    if not tokens:
        raise EOFError("no tokens, nothing to parse")
    ast = []
    while tokens:
        expr = check_errors(parse_expr(tokens))
        if not expr:
            break
        ast.append(expr)
    return ast

def parse_expr(tokens: List[Token]) -> list:
    """
    Parses a single expression, such as (+ 2 (* 3 4)) or "a string" or 2 or
    some_symbol
    """
    if not tokens:
        return None
    token = tokens.pop(0)
    if token.type == 'paren':
        if token.value == 'open':
            ast = []
            while tokens:
                token = tokens[0]
                # print(f"[p] curr token: {token}")
                if token.type == 'paren':
                    if token.value == 'close':
                        del tokens[0]
                        return ast
                    else:
                        ast.append(parse_expr(tokens))
                else:
                    ast.append(token)
                    del tokens[0]
            if ast:
                raise SyntaxError(f"missing ) after column {ast[-1].col} on line {ast[-1].line}")
            else:
                raise SyntaxError("missing )")
        else:
            raise SyntaxError(f"unexpected ) at line {token.line} and column {token.col}")
    else:
        return [token]

def check_errors(expr: List[Token]):
    if len(expr) == 1:
        return expr
    return expr
