#!/usr/bin/env python3

import tokenizer
import parser
import interpreter
import sys

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print("need a file")
            sys.exit(-1)
        with open(sys.argv[1], 'r') as f:
            s = f.read()
            try:
                tokens = tokenizer.tokenize(s)
            except TypeError as e:
                print("ERROR:", e)
                sys.exit(1)
            try:
                ast = parser.parse(tokens)
            except (TypeError,SyntaxError) as e:
                print("ERROR:", e)
                sys.exit(2)
            interpreter.interpret(ast)
            try:
                pass
            except Exception as e:
                print("ERROR:", e)
    except (KeyboardInterrupt, EOFError):
        print()
