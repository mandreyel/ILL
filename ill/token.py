class Token:
    class Type:
        identifier = 1
        number = 2
        string = 3
        paren = 4
        boolean = 5
        operator = 6
        arithmetic = 7

    def __init__(self, type: str, value: str, line=None, col=None):
        self.type = type
        self.value = value
        # Note: these are 1-based, not 0-based.
        self.line = line
        self.col = col

    def __str__(self) -> str:
        if not self.line and not self.col:
            return f"<{self.type}:{self.value}>"
        return f"<{self.type}:{self.value} @{self.line},{self.col}>"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        """
        Comparison doesn't take into consideration the position of the token
        in the source.
        """
        return self.type == other.type and self.value == other.value
        
    def __nq__(self, other) -> bool:
        return not (self == other)

OPEN_PAREN = Token('paren', 'open')
CLOSE_PAREN = Token('paren', 'close')
