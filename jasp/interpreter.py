from typing import List
from tokenizer import Token
from env import Env

def add(*args):
    r = args[0]
    for n in args[1:]:
        r += n
    return r

def sub(*args):
    r = args[0]
    for n in args[1:]:
        r -= n
    return r

def mul(*args):
    r = args[0]
    for n in args[1:]:
        r *= n
    return r

def div(*args):
    if len(args) != 2:
        raise SyntaxError("division takes only 2 arguments")
    return args[0] / args[1]

global_env = Env({
    '+': add,
    '-': sub,
    '*': mul,
    '/': div,
})

def interpret(ast: list):
    """Interprets the AST which is a list of expressions."""
    for expr in ast:
        interpret_expr(expr, global_env)
    pass

def interpret_expr(expr, env: Env=global_env):
    # print('[i] curr expr:', expr)
    if not isinstance(expr, list) or len(expr) == 1:
        token = expr[0] if isinstance(expr, list) else expr
        # print('[i] token:', token)
        if token.type in ('number', 'string'):
            return token.value
        elif token.type in ('identifier', 'arithmetic', 'operator'):
            return env[token.value]
        else:
            # This is probably a syntax error. TODO
            pass
    else:
        if expr[0].value == 'if': # (if cond-expr if-true-expr if-not-expr)
            pass
        elif expr[0].value == 'let': # (let name expr)
            pass
        elif expr[0].value == 'fn': # (fn identifier (args...) expr)
            pass
        else: # (fn-identifier args...)
            exprs = [interpret_expr(x, env) for x in expr]
            fn = exprs.pop(0)
            return fn(*exprs)
