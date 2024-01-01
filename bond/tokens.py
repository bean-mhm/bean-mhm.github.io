import copy
import jsonpickle


class TokenPos:
    line: int
    col: int

    def __init__(self, line: int = 1, col: int = 0):
        self.line = line
        self.col = col

    def __str__(self) -> str:
        return f'{self.line}, {self.col}'


class Token:
    pos: TokenPos

    def __init__(self, type: str, pos: TokenPos):
        self.type = type
        self.pos = copy.deepcopy(pos)


class VarToken(Token):
    name: str

    def __init__(self, pos: TokenPos, name: str):
        super().__init__(type(self).__name__, pos)
        self.name = name


class EqualSignToken(Token):
    def __init__(self, pos: TokenPos):
        super().__init__(type(self).__name__, pos)


class FunctionCallStartToken(Token):
    name: str

    def __init__(self, pos: TokenPos, name: str):
        super().__init__(type(self).__name__, pos)
        self.name = name


class FunctionCallEndToken(Token):
    def __init__(self, pos: TokenPos):
        super().__init__(type(self).__name__, pos)


class StringLiteralToken(Token):
    value: str

    def __init__(self, pos: TokenPos, value: str):
        super().__init__(type(self).__name__, pos)
        self.value = value


class TokenizationResult:
    ok: bool
    tokens: list

    def __init__(self):
        self.ok = False
        self.tokens = []

    def __str__(self) -> str:
        return jsonpickle.encode(self.__dict__, unpicklable=False, indent=2)
