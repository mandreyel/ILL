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

def _and(*args):
    return args.count(True) == len(args)

def _or(*args):
    return True in args

###############################################################################

global_env = Env({
    '+': add,
    '-': sub,
    '*': mul,
    '/': div,
    '=': eq,
    '<': lambda a, b: a < b,
    '>': lambda a, b: a > b,
    'and': _and,
    'or': _or,
    'print': print,
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
    elif isinstance(expr[0], list):
        return interpret_fn_call(expr, env)
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

def interpret_atom(expr, env: Env):
    token = expr[0] if isinstance(expr, list) else expr
    # print('[i] token:', token)
    if token.type in ('number', 'string', 'bool'):
        return token.value
    elif token.type in ('identifier', 'arithmetic', 'operator'):
        v = env[token.value]
        if callable(v) and isinstance(expr, list):
            return interpret_fn_call(expr, env)
        return v
    else:
        # This is probably a syntax error. TODO
        pass

def interpret_if(expr, env: Env):
    """If "expression": (if cond-expr if-true-expr if-not-expr)"""
    assert len(expr) >= 3, "if expression must have at least (if cond cons)"
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

def interpret_var_binding(expr, env: Env):
    """Variable binding: (let name expr)"""
    assert len(expr) == 3, "variable binding must consist of only 3 lexemes"
    (_, name, value) = expr
    env.define(name.value, interpret_expr(value))

class Function:
    def __init__(self, name: str, body, params=[], parent_env: Env=global_env):
        self.name = name
        self.params = params
        self.body = body
        self.env = Env(parent=parent_env)

    def __call__(self, *args):
        if len(self.params) != len(args):
            raise SyntaxError("function {self.name} expects {len(self.params)} arguments but {len(args)} given")
        # Populate the function environment with the function arguments so that
        # they're available when evaluating the function body.
        # print('[fn] fn *args:', *args)
        for name, arg in zip(self.params, args):
            # print("[fn] defining:", name, arg)
            self.env.define(name, arg)
        # Evaluate the function body.
        assert self.body, "function body must not be empty"
        # print("[fn] evaluating fn body")
        # Interpret the last expression separately as the value of the last
        # expresssion is returned.
        # for expr in self.body[:-1]:
            # print(f"[fn] evaluating {expr}")
            # interpret_expr(expr, self.env)
        return interpret_expr(self.body, self.env)

def interpret_fn_def(expr, env: Env):
    """Function definition: (fn identifier (params...) expr)"""
    assert len(expr) == 4, "function definition must consist of 4 pieces"
    (_, name, params, body) = expr
    name = name.value
    params = [token.value for token in params]
    fn = Function(name=name, params=params, body=body, parent_env=env)
    env.define(name, fn)
    return fn

def interpret_fn_call(expr, env: Env):
    """Function call: (fn-identifier args...)"""
    # Evaluate each subexpression first.
    exprs = [interpret_expr(x, env) for x in expr]
    fn = exprs.pop(0)
    return fn(*exprs)
