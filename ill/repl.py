#!/usr/bin/env python3

import tokenizer
import parser
import interpreter

NAME = 'ILL'
PROMPT = 'I♥L'

if __name__ == "__main__":
    print(f"{NAME} version 0.0.1 (alpha)")
    print("Press CTRL+C or CTRL+D or type q or quit to exit.")
    print("-------------------------------------------------")

    try:
        history = []
        while True:
            s = input(f"{PROMPT}> ")
            if 'q' in s or "quit" in s:
                break
            history.append(s)

            try:
                tokens = tokenizer.tokenize(s)
            except TypeError as e:
                print("ERROR:", e)
                continue

            # print('tokens:', tokens)

            try:
                ast = parser.parse(tokens)
            except (TypeError,SyntaxError) as e:
                print("ERROR:", e)
                continue

            print('ast:', ast)

            for expr in ast:
                result = interpreter.interpret_expr(expr)
                if result is not None: print(result)

            # try:
                # for expr in ast:
                    # result = interpreter.interpret_expr(expr)
                    # if result is not None: print(result)
            # except Exception as e:
                # print("ERROR:", e)
                # continue
    except (KeyboardInterrupt, EOFError):
        print()
    print("Bye!")
