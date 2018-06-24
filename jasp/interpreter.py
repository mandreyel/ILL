from typing import List
from expr import *
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

def do(*args):
    """
    This is used for when one wants more than a single expression in an if
    branch or a function body. The values of a list of evaluated expressions are
    passed to do and the last value is returned.
    """
    return args[-1]

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
    'do': do,
})

###############################################################################

def interpret(ast: List[Expr]):
    """Interprets the AST which is a list of expressions."""
    for expr in ast:
        interpret_expr(expr, global_env)

def interpret_expr(expr: Expr, env: Env=global_env):
    print('[i] curr expr:', expr)
    # TODO possibly use the visitor pattern here
    if isinstance(expr, AtomExpr):
        return interpret_atom(expr, env)
    elif isinstance(expr, RefExpr):
        return interpret_ref(expr, env)
    elif isinstance(expr, IfExpr):
        return interpret_if(expr, env)
    elif isinstance(expr, LetExpr):
        return interpret_let(expr, env)
    elif isinstance(expr, FnDefExpr):
        return interpret_fn_def(expr, env)
    elif isinstance(expr, FnCallExpr):
        return interpret_fn_call(expr, env)
    else:
        raise TypeError("unknown type")

###############################################################################

def interpret_atom(expr: AtomExpr, env: Env): return expr.value

def interpret_ref(expr: RefExpr, env: Env): return env[expr.name]

def interpret_if(expr: IfExpr, env: Env):
    """If "expression": (if cond-expr true-branch-expr false-branch-expr)"""
    cond = interpret_expr(expr.cond, env)
    if cond:
        return interpret_expr(expr.true_branch, env)
    elif expr.false_branch:
        return interpret_expr(expr.false_branch, env)

def interpret_let(expr: LetExpr, env: Env):
    """Variable binding: (let name expr)"""
    env.define(expr.name, interpret_expr(expr.value, env))
    return env[expr.name]

class Function:
    def __init__(self, name: str, body: List[Expr], params: List[str]=[],
            parent_env: Env=global_env):
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
        # assert self.body
        # for expr in self.body[:-1]:
            # interpret_expr(expr, self.env)
        # Interpret the last expression separately as the value of the last
        # expresssion is returned.
        return interpret_expr(self.body[-1], self.env)

def interpret_fn_def(expr: FnDefExpr, env: Env):
    """Function definition: (fn identifier (params...) expr)"""
    fn = Function(name=expr.name, params=expr.params, body=expr.body, parent_env=env)
    env.define(expr.name, fn)
    return fn

def interpret_fn_call(expr: FnCallExpr, env: Env):
    """Function call: (fn-identifier args...)"""
    # Evaluate each subexpression first.
    fn = interpret_expr(expr.fn, env)
    # Since e.g. ((fn anon (a) (+ 2 a)) 5) is a valid expression, the first
    # element may not be an identifier bound to a function in env but a function
    # object, so we need to check if fn is a string or something else.
    if isinstance(fn, str):
        fn = env[fn]
    args = [interpret_expr(x, env) for x in expr.args]
    return fn(*args)
