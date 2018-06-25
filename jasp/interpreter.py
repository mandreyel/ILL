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

def eq(*args) -> bool:
    first = args[0]
    for a in args[1:]:
        if a != first:
            return False
    return True

def _not(*args) -> bool:
    if len(args) != 1:
        raise SyntaxError("not takes a single argument")
    return not args[0]

def _and(*args) -> bool:
    return args.count(True) == len(args)

def _or(*args) -> bool:
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
    '<=': lambda a, b: a <= b,
    '>': lambda a, b: a > b,
    '>=': lambda a, b: a >= b,
    'not': _not,
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
    # print('[i] curr expr:', expr)
    if isinstance(expr, AtomExpr):
        return interpret_atom(expr, env)
    elif isinstance(expr, VectorExpr):
        return interpret_vector(expr, env)
    elif isinstance(expr, MapExpr):
        return interpret_map(expr, env)
    elif isinstance(expr, LetExpr):
        return interpret_let(expr, env)
    elif isinstance(expr, RefExpr):
        return interpret_ref(expr, env)
    elif isinstance(expr, IfExpr):
        return interpret_if(expr, env)
    elif isinstance(expr, WhileExpr):
        return interpret_while(expr, env)
    elif isinstance(expr, EachExpr):
        return interpret_each(expr, env)
    elif isinstance(expr, FnDefExpr):
        return interpret_fn_def(expr, env)
    elif isinstance(expr, FnCallExpr):
        return interpret_fn_call(expr, env)
    else:
        raise TypeError("unknown type")

###############################################################################

def interpret_atom(expr: AtomExpr, env: Env):
    return expr.value

def interpret_ref(expr: RefExpr, env: Env):
    return env[expr.name]

def interpret_if(expr: IfExpr, env: Env):
    """If "expression": (if cond-expr true-branch-expr false-branch-expr)"""
    cond = interpret_expr(expr.cond, env)
    if cond:
        return interpret_expr(expr.true_branch, env)
    elif expr.false_branch:
        return interpret_expr(expr.false_branch, env)

def interpret_while(expr: WhileExpr, env: Env):
    ret = None
    while True:
        cond = interpret_expr(expr.cond, env)
        if not isinstance(cond, bool):
            raise TypeError("loop condition must evaluate to a boolean value")
        if not cond:
            break
        ret = interpret_expr(expr.body, env)
    return ret

def interpret_each(expr: EachExpr, env: Env):
    ret = None
    each_env = Env(sym_table={expr.elem_name: None}, parent=env)
    coll = interpret_expr(expr.coll)
    if isinstance(coll, list):
        for elem in coll:
            each_env.define(expr.elem_name, elem)
            ret = interpret_expr(expr.body, each_env)
    else:
        assert isinstance(coll, dict)
        for key, val in coll.items():
            key_name, val_name = expr.elem_name
            each_env.define(key_name, key)
            each_env.define(val_name, val)
            ret = interpret_expr(expr.body, each_env)
    return ret

def interpret_let(expr: LetExpr, env: Env):
    """Variable binding: (let name expr)"""
    env.define(expr.name, interpret_expr(expr.value, env))
    return env[expr.name]

class Function:
    def __init__(self, name: str, body: List[Expr], params: List[str]=[]):
        self.name = name
        self.params = params
        self.body = body

    def __call__(self, parent_env: Env, *args):
        if len(self.params) != len(args):
            raise SyntaxError("function {self.name} expects {len(self.params)} arguments but {len(args)} given")
        # Populate the function environment with the function arguments so that
        # they're available when evaluating the function body.
        env = Env(sym_table={name: arg for name, arg in zip(self.params, args)}, parent=parent_env)
        # Evaluate the function body.
        return interpret_expr(self.body, env)

def interpret_fn_def(expr: FnDefExpr, env: Env):
    """Function definition: (fn identifier (params...) expr)"""
    fn = Function(name=expr.name, params=expr.params, body=expr.body)
    env.define(expr.name, fn)
    return fn

def interpret_fn_call(expr: FnCallExpr, env: Env):
    """Function call: (fn-identifier args...)"""
    # Evaluate each subexpression first.
    fn = interpret_expr(expr.fn, env)
    args = [interpret_expr(x, env) for x in expr.args]
    # Since e.g. ((fn anon (a) (+ 2 a)) 5) is a valid expression, the first
    # element may not be an identifier bound to a function in env but a function
    # object, so we need to check if fn is a string or something else.
    assert callable(fn)
    if isinstance(fn, Function):
        return fn(env, *args)
    else:
        return fn(*args)

def interpret_vector(expr: VectorExpr, env: Env) -> list:
    return [interpret_expr(expr, env) for expr in expr.exprs]

def interpret_map(expr: MapExpr, env: Env) -> dict:
    return {interpret_expr(key, env):interpret_expr(val, env) for key, val in expr.expr_dict.items()}
