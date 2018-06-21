from typing import List
from tokenizer import Token
from env import Env

# Builtins
###############################################################################

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

def eq(*args):
    first = args[0]
    for a in args[1:]:
        if a != first:
            return False
    return True

###############################################################################

global_env = Env({
    '+': add,
    '-': sub,
    '*': mul,
    '/': div,
    '=': eq,
    '<': lambda a, b: a < b,
    '>': lambda a, b: a > b,
})

###############################################################################

def interpret(ast: list):
    """Interprets the AST which is a list of expressions."""
    for expr in ast:
        interpret_expr(expr, global_env)

def interpret_expr(expr, env: Env=global_env):
    # print('[i] curr expr:', expr)
    if not isinstance(expr, list) or len(expr) == 1:
        return interpret_atom(expr, env)
    else:
        if expr[0].value == 'if':
            return interpret_if(expr, env)
        elif expr[0].value == 'let':
            return interpret_var_binding(expr, env)
        elif expr[0].value == 'fn':
            return interpret_fn_def(expr, env)
        else:
            return interpret_fn_call(expr, env)

###############################################################################

def interpret_atom(expr, env):
    token = expr[0] if isinstance(expr, list) else expr
    # print('[i] token:', token)
    if token.type in ('number', 'string', 'bool'):
        return token.value
    elif token.type in ('identifier', 'arithmetic', 'operator'):
        return env[token.value]
    else:
        # This is probably a syntax error. TODO
        pass

def interpret_if(expr, env):
    """If "expression": (if cond-expr if-true-expr if-not-expr)"""
    assert len(expr) >= 3, "if expression must have at least (if cond cons)"
    if len(expr) < 3:
        # TODO this should be checked by the parser
        raise SyntaxError(f"invalid if expression at line {expr[0].line} and column {expr[0].col}")

    # Interpret subexpressions.
    #exprs = [interpret_expr(x, env) for x in expr[1:0]]
    # Skip the `if`.
    exprs = expr[1:]
    cond = interpret_expr(exprs[0], env)
    if not isinstance(cond, bool):
        raise RuntimeError(f"if condition at line {expr[0].line} and column {expr[0].col} needs to evaluate to a bool")

    true_branch = exprs[1]
    false_branch = exprs[2] if len(exprs) > 2 else None
    if cond:
        return interpret_expr(true_branch, env)
    elif false_branch:
        return interpret_expr(false_branch, env)

def interpret_var_binding(expr, env):
    """Variable binding: (let name expr)"""
    assert len(expr) == 3, "variable binding must consist of only 3 lexemes"
    (_, name, value) = expr
    env.define(name.value, interpret_expr(value))

def interpret_fn_def(expr, env):
    """Function definition: (fn identifier (args...) expr)"""
    pass

def interpret_fn_call(expr, env):
    """Function call: (fn-identifier args...)"""
    # Evaluate each subexpression first.
    exprs = [interpret_expr(x, env) for x in expr]
    fn = exprs.pop(0)
    return fn(*exprs)
