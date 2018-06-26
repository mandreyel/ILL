from typing import List
from expr import *
from token import Token, CLOSE_PAREN, OPEN_PAREN

def parse(tokens: List[Token]) -> List[Expr]:
    return Parser(tokens).parse()

###############################################################################

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> List[Expr]:
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
        if self.eof():
            raise EOFError("no tokens, nothing to parse")
        ast = []
        while not self.eof():
            expr = self.parse_expr()
            if not expr:
                break
            ast.append(expr)
        return ast

    def parse_expr(self) -> Expr:
        """
        Parses and returns a single expression. If the expression is invalid,
        a SyntaxError is thrown.
        """
        if self.eof():
            return None
        token = self.advance()
        if token.type == 'paren':
            if token.value == 'open':
                token = self.tokens[self.pos]
                if token.type == 'identifier':
                    if token.value == 'let':
                        return self.parse_let_expr()
                    elif token.value == 'if':
                        return self.parse_if_expr()
                    elif token.value == 'while':
                        return self.parse_while_expr()
                    elif token.value == 'each':
                        return self.parse_each_expr()
                    elif token.value == 'fn':
                        return self.parse_fn_def_expr()
                    else:
                        return self.parse_fn_call_expr()
                else:
                    return self.parse_fn_call_expr()
            else:
                raise syntax_error("unexpected )", token)
        elif token.type == 'square-paren':
            if token.value == 'open':
                return self.parse_vector_expr()
            else:
                raise syntax_error("unexpected ]", token)
        elif token.type == 'bracket':
            if token.value == 'open':
                return self.parse_map_expr()
            else:
                raise syntax_error("unexpected }", token)
        elif token.type in ('string', 'number', 'bool'):
            return AtomExpr(token.value, token.line, token.col)
        else:
            return RefExpr(token.value, token.line, token.col)

###############################################################################
    
    def parse_let_expr(self) -> LetExpr:
        """Variable binding: (let name expr)"""
        # Consume 'let' keyword.
        keywd = self.advance()
        if self.expr_end():
            raise syntax_error("incomplete let expression", keywd)
        name = self.advance()
        if name.type != 'identifier':
            raise syntax_error("variable name must be a valid identifier", name)
        if self.expr_end():
            raise syntax_error("let expression must have a value", keywd)
        value = self.parse_expr()
        # Make sure let expression is properly terminated.
        self.terminate_expr()
        return LetExpr(name.value, value, keywd.line, keywd.col)

    def parse_if_expr(self) -> IfExpr:
        """If "expression": (if cond-expr true-branch-expr false-branch-expr)"""
        # Consume 'if' keyword.
        keywd = self.advance()
        if self.expr_end():
            raise syntax_error("if expression must have a condition and at least a true branch", keywd)
        cond = self.parse_expr()
        if self.expr_end():
            raise syntax_error("if expression must have a true branch", keywd)
        elif not can_eval_to_bool(cond):
            raise syntax_error("if expression condition must evaluate to a boolean value", cond)
        true_branch = self.parse_expr()
        false_branch = None
        # A false (else) branch is optional so only parse it if the next token is
        # not a closing paren.
        if self.tokens[self.pos] != CLOSE_PAREN:
            false_branch = self.parse_expr()
        # Make sure the if expression is terminated.
        self.terminate_expr()
        return IfExpr(cond, true_branch, false_branch, keywd.line, keywd.col)

    def parse_while_expr(self) -> WhileExpr:
        # Consume 'while' keyword.
        keywd = self.advance()
        if self.expr_end():
            raise syntax_error("while expression must have a condition and a body", keywd)
        cond = self.parse_expr()
        if self.expr_end():
            raise syntax_error("while expression must have a body", keywd)
        elif not can_eval_to_bool(cond):
            raise syntax_error("while expression condition must evaluate to a boolean value", cond)
        body = self.parse_expr()
        self.terminate_expr()
        return WhileExpr(cond, body, keywd.line, keywd.col)

    def parse_each_expr(self) -> EachExpr:
        # Consume 'each' keyword.
        keywd = self.advance()
        if self.expr_end():
            raise syntax_error("each expression must have a collection header and a body", keywd)

        # Each "iteration header"
        open_paren = self.advance()
        if open_paren != OPEN_PAREN:
            raise syntax_error("each expression must have a non empty iteration header", open_paren)
        elif self.expr_end():
            raise syntax_error("each expression must have a non empty iteration header", open_paren)
        collection = self.parse_expr()
        if not isinstance(collection, (CollectionExpr, RefExpr, FnCallExpr)):
            raise syntax_error("first element of an each expression iteration header must be a collection", open_paren)
        elif self.expr_end():
            raise syntax_error("incomplete each expression", open_paren)
        element = self.advance()
        if not element.type == 'identifier':
            raise syntax_error("the second element of an each expression iteration header must be valid identifier denoting the current element in the iteration", element)
        if self.expr_end():
            raise syntax_error("incomplete each expression", element)
        element = element.value
        # The collection may be a map in which case another identifier for each
        # map value is necessary.
        if self.tokens[self.pos].type == 'identifier':
            element = (element, self.advance().value)
        # Consume closing paren.
        self.terminate_expr()

        # Each body
        if self.expr_end():
            raise syntax_error("each expression must have a body", keywd)
        body = self.parse_expr()
        # Consume closing paren.
        self.terminate_expr()
        return EachExpr(collection, element, body, keywd.line, keywd.col)

    def parse_fn_def_expr(self) -> FnDefExpr:
        """
        Function definition:
            (fn identifier (params...) expr) or
            (fn identifier (params...) (exprs...))
        """
        # Consume 'fn' keyword.
        keywd = self.advance()
        if self.expr_end():
            raise syntax_error("incomplete function definition", keywd)
        name = self.advance()
        if name.type != 'identifier':
            raise syntax_error("variable name must be an identifier", name)
        if self.expr_end():
            raise syntax_error("function definition must have a parameter list", keywd)

        # Paremeter list
        open_paren = self.advance()
        if open_paren != OPEN_PAREN:
            raise syntax_error("missing function parameter list", open_paren)
        if self.eof():
            raise syntax_error("function definition must have a parameter list (may be empty)", open_paren)
        if CLOSE_PAREN not in self.tokens[self.pos:]:
            raise syntax_error("unterminated function parameter list", open_paren)
        close_paren_idx = self.tokens[self.pos:].index(CLOSE_PAREN)
        params = []
        for _ in range(close_paren_idx):
            param = self.advance()
            if param.type != 'identifier':
                raise syntax_error("function parameter must be a valid identifier", param)
            params.append(param.value)
        # Consume closing paren.
        self.terminate_expr()

        # Function body
        if self.expr_end():
            raise syntax_error("function must have a function body", keywd)
        body = self.parse_expr()

        # Make sure the function definition is terminated.
        self.terminate_expr()
        return FnDefExpr(name.value, params, body, keywd.line, keywd.col)

    def parse_fn_call_expr(self) -> FnCallExpr:
        """Function call: (fn-identifier args...)"""
        line, col = self.tokens[self.pos].line, self.tokens[self.pos].col
        fn_expr = self.parse_expr()
        args = []
        while not self.expr_end():
            args.append(self.parse_expr())
        if self.eof():
            raise syntax_error("missing ')'", Token(None, None, line, col))
        # Make sure the function call expression is terminated.
        self.terminate_expr()
        return FnCallExpr(fn_expr, args, line, col)

    def parse_vector_expr(self) -> VectorExpr:
        exprs = []
        line, col = self.tokens[self.pos].line, self.tokens[self.pos].col
        CLOSE_SQUARE_PAREN = Token('square-paren', 'close')
        while not self.expr_end(CLOSE_SQUARE_PAREN):
            exprs.append(self.parse_expr())
        self.terminate_expr(CLOSE_SQUARE_PAREN, ']')
        return VectorExpr(exprs, line, col)

    def parse_map_expr(self) -> MapExpr:
        exprs = {}
        line, col = self.tokens[self.pos].line, self.tokens[self.pos].col
        CLOSE_BRACKET = Token('bracket', 'close')
        while not self.expr_end(CLOSE_BRACKET):
            key = self.parse_expr()
            if self.expr_end(CLOSE_BRACKET):
                raise syntax_error("map key must have a colon and a value", key)
            if not self.tokens[self.pos] == Token('colon', ':'):
                raise syntax_error("no colon between key and value in map", key)
            self.advance()
            if self.expr_end(CLOSE_BRACKET):
                raise syntax_error("map key must have a value", key)
            exprs[key] = self.parse_expr()
        self.terminate_expr(CLOSE_BRACKET, '}')
        return MapExpr(exprs, line, col)

    ###############################################################################

    def advance(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def eof(self) -> bool:
        return self.pos >= len(self.tokens)

    def expr_end(self, expr_terminator=CLOSE_PAREN) -> bool:
        return self.eof() or self.tokens[self.pos] == expr_terminator

    def terminate_expr(self, expr_terminator=CLOSE_PAREN, symbol=')'):
        if self.eof():
            raise syntax_error(f"missing '{symbol}'", self.tokens[-1])
        elif self.tokens[self.pos] != expr_terminator:
            raise syntax_error(f"missing '{symbol}'", self.tokens[self.pos])
        self.pos += 1

def can_eval_to_bool(expr: Expr) -> bool:
    return isinstance(expr, (AtomExpr, FnCallExpr, LetExpr, RefExpr))

def syntax_error(msg, token=None) -> SyntaxError:
    if token:
        return SyntaxError(f"line {token.line} column {token.col}: " + msg)
    else:
        return SyntaxError(msg)
