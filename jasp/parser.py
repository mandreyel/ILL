from typing import List
from expr import *
from token import Token, CLOSE_PAREN, OPEN_PAREN

def parse(tokens: List[Token]) -> List[Expr]:
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
    and the return value is a list of Expr sbuclass instances:
        [FnCallExpr(AtomExpr('+'), AtomExpr(3), AtomExpr(3)),
         FnCallExpr(AtomExpr('*'), AtomExpr(2),
             FnCallExpr(AtomExpr('+'), AtomExpr(4), AtomExpr(4)))]
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

def parse_expr(tokens: List[Token]) -> Expr:
    """
    Parses and returns a single expression and consumes the tokens representing
    the expression. If the expression is invalid, a SyntaxError is thrown.
    """
    if not tokens:
        return None
    token = tokens.pop(0)
    if token.type == 'paren':
        if token.value == 'open':
            token = tokens[0]
            if token.type == 'identifier':
                if token.value == 'let':
                    return parse_let_expr(tokens)
                elif token.value == 'if':
                    return parse_if_expr(tokens)
                elif token.value == 'fn':
                    return parse_fn_def_expr(tokens)
                else:
                    return parse_fn_call_expr(tokens)
            else:
                return parse_fn_call_expr(tokens)
        else:
            raise syntax_error("unexpected )", token)
    elif token.type == 'square-paren':
        if token.value == 'open':
            return parse_vector_expr(tokens)
        else:
            raise syntax_error("unexpected [", token)
    elif token.type in ('string', 'number', 'bool'):
        return AtomExpr(token.value, token.line, token.col)
    else:
        return RefExpr(token.value, token.line, token.col)

###############################################################################

def parse_if_expr(tokens: List[Token]) -> IfExpr:
    """If "expression": (if cond-expr true-branch-expr false-branch-expr)"""
    assert tokens
    # Consume 'if' keyword.
    keywd = tokens.pop(0)
    if expr_end(tokens):
        raise syntax_error("if expression must have a condition and at least a true branch", keywd)
    cond = parse_expr(tokens)
    if expr_end(tokens):
        raise syntax_error("if expression must have a true branch", keywd)
    true_branch = parse_expr(tokens)
    false_branch = None
    # A false (else) branch is optional so only parse it if the next token is
    # not a closing paren.
    if tokens[0] != CLOSE_PAREN:
        false_branch = parse_expr(tokens)
    # Make sure the if expression is terminated.
    terminate_expr(tokens)
    return IfExpr(cond, true_branch, false_branch, keywd.line, keywd.col)

def parse_let_expr(tokens: List[Token]) -> LetExpr:
    """Variable binding: (let name expr)"""
    assert tokens
    # Consume 'let' keyword.
    keywd = tokens.pop(0)
    if expr_end(tokens):
        raise syntax_error("incomplete let expression", keywd)
    name = tokens.pop(0)
    if name.type != 'identifier':
        raise syntax_error("variable name must be a valid identifier", name)
    if expr_end(tokens):
        raise syntax_error("let expression must have a value", keywd)
    value = parse_expr(tokens)
    # Make sure let expression is properly terminated.
    terminate_expr(tokens)
    return LetExpr(name.value, value, keywd.line, keywd.col)

def parse_fn_def_expr(tokens: List[Token]) -> FnDefExpr:
    """
    Function definition:
        (fn identifier (params...) expr) or
        (fn identifier (params...) (exprs...))
    """
    assert tokens
    # Consume 'fn' keyword.
    keywd = tokens.pop(0)
    if expr_end(tokens):
        raise syntax_error("incomplete function definition", keywd)
    name = tokens.pop(0)
    if name.type != 'identifier':
        raise syntax_error("variable name must be an identifier", name)
    if expr_end(tokens):
        raise syntax_error("function definition must have a parameter list", keywd)

    # Paremeter list
    open_paren = tokens.pop(0)
    if open_paren != OPEN_PAREN:
        raise syntax_error("missing function parameter list", open_paren)
    if not tokens:
        raise syntax_error("function definition must have a parameter list (may be empty)", open_paren)
    if CLOSE_PAREN not in tokens:
        raise syntax_error("unterminated function parameter list", open_paren)
    close_paren_idx = tokens.index(CLOSE_PAREN)
    params = []
    for i in range(close_paren_idx):
        param = tokens.pop(0)
        if param.type != 'identifier':
            raise syntax_error("function parameter must be a valid identifier", param)
        params.append(param.value)
    # Consume closing paren.
    terminate_expr(tokens)

    # Function body
    if expr_end(tokens):
        raise syntax_error("function must have a function body", keywd)
    body = parse_expr(tokens)

    # Make sure the function definition is terminated.
    terminate_expr(tokens)
    return FnDefExpr(name.value, params, body, keywd.line, keywd.col)

def parse_fn_call_expr(tokens: List[Token]) -> FnCallExpr:
    """Function call: (fn-identifier args...)"""
    assert tokens
    line, col = tokens[0].line, tokens[0].col
    fn_expr = parse_expr(tokens)
    args = []
    while not expr_end(tokens):
        expr = parse_expr(tokens)
        args.append(expr)
    if not tokens:
        raise syntax_error("missing ')'", Token(None, None, line, col))
    # Make sure the function call expression is terminated.
    terminate_expr(tokens)
    return FnCallExpr(fn_expr, args, line, col)

def parse_vector_expr(tokens: List[Token]) -> VectorExpr:
    exprs = []
    line, col = tokens[0].line, tokens[0].col
    while tokens and tokens[0] != Token('square-paren', 'close'):
        exprs.append(parse_expr(tokens))
    if not tokens:
        raise syntax_error("missing ']'")
    elif tokens[0] != Token('square-paren', 'close'):
        raise syntax_error("missing ']'", tokens[0])
    tokens.pop(0)
    return VectorExpr(exprs, line, col)

###############################################################################

def expr_end(tokens) -> bool:
    return not tokens or tokens[0] == CLOSE_PAREN

def terminate_expr(tokens: List[Token]):
    if not tokens:
        raise syntax_error("missing ')'")
    elif tokens[0] != CLOSE_PAREN:
        raise syntax_error("missing ')'", tokens[0])
    tokens.pop(0)

def syntax_error(msg, token=None) -> SyntaxError:
    if token:
        return SyntaxError(f"line {token.line} column {token.col}: " + msg)
    else:
        return SyntaxError(msg)
