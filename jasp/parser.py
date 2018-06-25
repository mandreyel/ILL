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
                elif token.value == 'while':
                    return parse_while_expr(tokens)
                elif token.value == 'each':
                    return parse_each_expr(tokens)
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
            raise syntax_error("unexpected ]", token)
    elif token.type == 'bracket':
        if token.value == 'open':
            return parse_map_expr(tokens)
        else:
            raise syntax_error("unexpected }", token)
    elif token.type in ('string', 'number', 'bool'):
        return AtomExpr(token.value, token.line, token.col)
    else:
        return RefExpr(token.value, token.line, token.col)

###############################################################################

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
    elif not can_eval_to_bool(cond):
        raise syntax_error("if expression condition must evaluate to a boolean value", cond)
    true_branch = parse_expr(tokens)
    false_branch = None
    # A false (else) branch is optional so only parse it if the next token is
    # not a closing paren.
    if tokens[0] != CLOSE_PAREN:
        false_branch = parse_expr(tokens)
    # Make sure the if expression is terminated.
    terminate_expr(tokens)
    return IfExpr(cond, true_branch, false_branch, keywd.line, keywd.col)

def parse_while_expr(tokens: List[Token]) -> WhileExpr:
    assert tokens
    # Consume 'while' keyword.
    keywd = tokens.pop(0)
    if expr_end(tokens):
        raise syntax_error("while expression must have a condition and a body", keywd)
    cond = parse_expr(tokens)
    if expr_end(tokens):
        raise syntax_error("while expression must have a body", keywd)
    elif not can_eval_to_bool(cond):
        raise syntax_error("while expression condition must evaluate to a boolean value", cond)
    body = parse_expr(tokens)
    terminate_expr(tokens)
    return WhileExpr(cond, body, keywd.line, keywd.col)

def parse_each_expr(tokens: List[Token]) -> EachExpr:
    assert tokens
    # Consume 'each' keyword.
    keywd = tokens.pop(0)
    if expr_end(tokens):
        raise syntax_error("each expression must have a collection header and a body", keywd)

    # Each "iteration header"
    open_paren = tokens.pop(0)
    if open_paren != OPEN_PAREN:
        raise syntax_error("each expression must have a non empty iteration header", open_paren)
    elif expr_end(tokens):
        raise syntax_error("each expression must have a non empty iteration header", open_paren)
    collection = parse_expr(tokens)
    if not isinstance(collection, (CollectionExpr, RefExpr, FnCallExpr)):
        raise syntax_error("first element of an each expression iteration header must be a collection", open_paren)
    elif expr_end(tokens):
        raise syntax_error("incomplete each expression", open_paren)
    element = tokens.pop(0)
    if not element.type == 'identifier':
        raise syntax_error("the second element of an each expression iteration header must be valid identifier denoting the current element in the iteration", element)
    element = element.value
    # The collection may be a map in which case another identifier for the map
    # values is necessary.
    if tokens[0].type == 'identifier':
        element = (element, tokens.pop(0).value)
    # Consume closing paren.
    terminate_expr(tokens)

    # Each body
    if expr_end(tokens):
        raise syntax_error("each expression must have a body", keywd)
    body = parse_expr(tokens)
    # Consume closing paren.
    terminate_expr(tokens)
    return EachExpr(collection, element, body, keywd.line, keywd.col)

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
    assert tokens
    exprs = []
    line, col = tokens[0].line, tokens[0].col
    CLOSE_SQUARE_PAREN = Token('square-paren', 'close')
    while not expr_end(tokens, CLOSE_SQUARE_PAREN):
        exprs.append(parse_expr(tokens))
    terminate_expr(tokens, CLOSE_SQUARE_PAREN, ']')
    return VectorExpr(exprs, line, col)

def parse_map_expr(tokens: List[Token]) -> MapExpr:
    assert tokens
    exprs = {}
    line, col = tokens[0].line, tokens[0].col
    CLOSE_BRACKET = Token('bracket', 'close')
    while not expr_end(tokens, CLOSE_BRACKET):
        key = parse_expr(tokens)
        if expr_end(tokens, CLOSE_BRACKET):
            raise syntax_error("map key must have a colon and a value", key)
        if not tokens[0] == Token('colon', ':'):
            raise syntax_error("no colon between key and value in map", key)
        tokens.pop(0)
        if expr_end(tokens, CLOSE_BRACKET):
            raise syntax_error("map key must have a value", key)
        exprs[key] = parse_expr(tokens)
    terminate_expr(tokens, CLOSE_BRACKET, '}')
    return MapExpr(exprs, line, col)

###############################################################################

def can_eval_to_bool(expr: Expr) -> bool:
    return isinstance(expr, (AtomExpr, FnCallExpr, LetExpr, RefExpr))

def expr_end(tokens, expr_terminator=CLOSE_PAREN) -> bool:
    return not tokens or tokens[0] == expr_terminator

def terminate_expr(tokens: List[Token], expr_terminator=CLOSE_PAREN, symbol=')'):
    if not tokens:
        raise syntax_error(f"missing '{symbol}'")
    elif tokens[0] != expr_terminator:
        raise syntax_error(f"missing '{symbol}'", tokens[0])
    tokens.pop(0)

def syntax_error(msg, token=None) -> SyntaxError:
    if token:
        return SyntaxError(f"line {token.line} column {token.col}: " + msg)
    else:
        return SyntaxError(msg)
