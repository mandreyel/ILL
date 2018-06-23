class Env:
    def __init__(self, sym_table={}, parent=None):
        self.sym_table = sym_table
        self.parent = parent

    def define(self, identifier: str, value):
        self.sym_table[identifier] = value

    def __getitem__(self, identifier: str):
        if identifier in self.sym_table:
            return self.sym_table[identifier]
        elif self.parent:
            return self.parent[identifier]
        raise LookupError(f"undefined symbol: {identifier}")

    def __contains__(self, identifier: str) -> bool:
        if identifier in self.sym_table:
            return True
        elif self.parent:
            return identifier in self.parent
        return False
