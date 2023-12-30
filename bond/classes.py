class TokenPos:
    line: int
    col: int

    def __init__(self, line: int, col: int):
        self.line = line
        self.col = col

    def __str__(self):
        return f'{self.line}, {self.col}'


class BaseToken:
    pos: TokenPos

    def __init__(self, pos: TokenPos):
        self.pos = pos


class VarToken(BaseToken):
    name: str

    def __init__(self, pos: TokenPos, name: str):
        super().__init__(pos)
        self.name = name


class AssignmentToken(BaseToken):
    left: VarToken
    right: BaseToken

    def __init__(self, pos: TokenPos, left: VarToken, right: BaseToken):
        super().__init__(pos)
        self.left = left
        self.right = right


class FunctionToken(BaseToken):
    name: str
    args: list

    def __init__(self, pos: TokenPos, name: str, args: list):
        super().__init__(pos)
        self.name = name
        self.args = args


class StringLiteralToken(BaseToken):
    value: str

    def __init__(self, pos: TokenPos, value: str):
        super().__init__(pos)
        self.value = value


class ParseResult:
    tokens: list = []
    ok: bool = False
