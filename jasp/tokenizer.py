from typing import List
from token import Token
import re

WHITESPACE_RE = re.compile('\s+')
DIGIT_RE = re.compile('[0-9]')
FLOAT_RE = re.compile('(0|[1-9][0-9]*)\.[0-9]+')
IDENTIFIER_RE1 = re.compile('[a-z_]')
IDENTIFIER_RE2 = re.compile('[a-z_\-0-9]')
ARITHMETIC_RE = re.compile('[+\-\*/]')
OPERATOR_RE = re.compile('[=<>]')

def tokenize(source: str) -> List[Token]:
    """
    Returns a list of dicts with the keys 'type' and 'value', each representing
    a token in the source.

    The possible token types are: 
        - paren: (,)
        - number: 0|[1-9][0-9]* # TODO add float support
        - string: anything enclosed in double quotes, including escaped double quotes (\") 
        - bool: true,false
        - identifier: [a-z_][a-z_0-9]*
        - arithmetic: +,-,*,/
        - operator: =,<,<=,>,>= (negation is done with the not keyword)
        - EOF: indicates end of file

    E.g. for the input `(+ 3 243)`, the following structure is returned:
        [{'type': 'paren', 'value': 'open'},
         {'type': 'arithmetic', 'value': '+'},
         {'type': 'number', 'value': '3'},
         {'type': 'number', 'value': '243'},
         {'type': 'paren', 'value': 'close'}]
    """
    tokens = []
    i = 0
    line = 1
    col = 1
    while i < len(source):
        char = source[i]
        if char == '\n':
            line += 1
            col = 1
        if char == '(':
            tokens.append(Token('paren', 'open', line, col))
        elif char == ')':
            tokens.append(Token('paren', 'close', line, col))
        elif WHITESPACE_RE.search(char):
            pass
        elif char == '0':
            if i < len(source) - 1 and DIGIT_RE.match(source[i+1]):
                raise TypeError("you may only use a single zero")
            tokens.append(Token('number', int(char), line, col))
        elif DIGIT_RE.match(char):
            value = char
            while i < len(source) - 1:
                i += 1
                char = source[i]
                if not DIGIT_RE.match(char):
                    # Restore i.
                    i -= 1
                    break
                value += char
            tokens.append(Token('number', int(value), line, col))
        elif char == '"':
            prev = ''
            value = ""
            while i < len(source) - 1:
                prev = char
                i += 1
                char = source[i]
                if char == '"' and prev != '\\':
                    # Don't restore i to skip closing quote.
                    break
                value += char
            if i + 1 == len(source) and source[i] != '"':
                raise TypeError("missing closing double quotes")
            tokens.append(Token('string', value, line, col))
        elif IDENTIFIER_RE1.match(char):
            value = char
            while i < len(source) - 1:
                i += 1
                char = source[i]
                if not IDENTIFIER_RE2.match(char):
                    # Restore i.
                    i -= 1
                    break
                value += char
            if value in ('true', 'false'):
                tokens.append(Token('bool', value == 'true', line, col))
            else:
                tokens.append(Token('identifier', value, line, col))
        elif ARITHMETIC_RE.match(char):
            tokens.append(Token('arithmetic', char, line, col))
        elif OPERATOR_RE.match(char):
            value = char
            if i < len(source) - 1 and source[i+1] == '=':
                value += '='
                i += 1
            tokens.append(Token('operator', value, line, col))
        i += 1
        col += 1
    # tokens.append(Token('EOF', None))
    return tokens
