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
    and the return value is a nested list of lists, each nested list representing an expression:
        [[Token('arithmetic', '+'), Token('number', '3'), Token('number', '4')],
         [Token('arithmetic', '*'), Token('number', '2'), [
            Token('arithmetic', '+'), Token('number', '4'), Token('number', '3')]]]

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
        expr = parse_expr(tokens)
        if not expr:
            break
        ast.append(expr)
    return ast

def parse_expr(tokens: List[Token]):
    if not tokens:
        return None
    token = tokens.pop(0)
    if token.type == 'paren':
        if token.value == 'open':
            ast = []
            while tokens:
                token = tokens[0]
                if token.type == 'paren':
                    if token.value == 'close':
                        del tokens[0]
                        return ast
                    else:
                        ast.append(parse_expr(tokens))
                else:
                    del tokens[0]
                    ast.append(token)
            raise SyntaxError("missing )")
        else:
            raise SyntaxError(f"unexpected ) at line {token.line} and column {token.col}")
    else:
        return [token]
