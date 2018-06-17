import tokenizer
import parser

if __name__ == "__main__":
    print("lips version 0.0.1")
    print("Press CTRL+C or CTRL+D or type q or quit to exit.")
    print("-------------------------------------------------")

    try:
        history = []
        while True:
            s = input("lips > ")
            if 'q' in s or "quit" in s:
                break
            history.append(s)

            try:
                tokens = tokenizer.tokenize(s)
            except TypeError as e:
                print("ERROR:", e)
                continue

            print('tokens:', tokens)
            try:
                asts = parser.parse(tokens)
            except (TypeError,SyntaxError) as e:
                print("ERROR:", e)
                continue
            print('asts:', asts)
    except (KeyboardInterrupt, EOFError):
        print()
    print("Bye!")
