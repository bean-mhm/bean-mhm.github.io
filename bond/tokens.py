import copy
import jsonpickle


# -----------------------------------------------------------------------------


class TokenPos:
    line: int
    col: int

    def __init__(self, line: int = 1, col: int = 0):
        self.line = line
        self.col = col

    def __str__(self) -> str:
        return f'{self.line}, {self.col}'


# -----------------------------------------------------------------------------


# The first step of parsing extracts parse tokens in sequential order and with no tree-like or
# recursive structure. We then build a recursive syntax tree using regular tokens, which will then
# be processed by the compiler to generate the output.


class ParseToken:
    pos: TokenPos

    def __init__(self, pos: TokenPos, type: str):
        self.type = type
        self.pos = copy.deepcopy(pos)


class VarParseToken(ParseToken):
    name: str

    def __init__(self, pos: TokenPos, name: str):
        super().__init__(pos, type(self).__name__)
        self.name = name


class EqualSignParseToken(ParseToken):
    def __init__(self, pos: TokenPos):
        super().__init__(pos, type(self).__name__)


class FunctionCallStartParseToken(ParseToken):
    name: str

    def __init__(self, pos: TokenPos, name: str):
        super().__init__(pos, type(self).__name__)
        self.name = name


class FunctionCallEndParseToken(ParseToken):
    def __init__(self, pos: TokenPos):
        super().__init__(pos, type(self).__name__)


class StringLiteralParseToken(ParseToken):
    value: str

    def __init__(self, pos: TokenPos, value: str):
        super().__init__(pos, type(self).__name__)
        self.value = value


# -----------------------------------------------------------------------------


class Token:
    pos: TokenPos

    def __init__(self, pos: TokenPos, type: str):
        self.type = type
        self.pos = copy.deepcopy(pos)


class VarToken(Token):
    name: str

    def __init__(self, pos: TokenPos, name: str):
        super().__init__(pos, type(self).__name__)
        self.name = name


class AssignmentToken(Token):
    left: VarToken
    right: Token

    def __init__(self, pos: TokenPos, left: VarToken, right: Token):
        super().__init__(pos, type(self).__name__)


class FunctionCallToken(Token):
    name: str
    args: list = []

    def __init__(self, pos: TokenPos, name: str, args: list = []):
        super().__init__(pos, type(self).__name__)
        self.name = name
        self.args = args


class StringLiteralToken(Token):
    value: str

    def __init__(self, pos: TokenPos, value: str):
        super().__init__(pos, type(self).__name__)
        self.value = value


# -----------------------------------------------------------------------------


class ParseResult:
    ok: bool
    parse_tokens: list

    def __init__(self):
        self.ok = False
        self.parse_tokens = []

    def __str__(self) -> str:
        return jsonpickle.encode(self.__dict__, unpicklable=False, indent=2)


class SyntaxTree:
    tokens: list

    def __init__(self):
        self.tokens = []

    def __str__(self) -> str:
        return jsonpickle.encode(self.__dict__, unpicklable=False, indent=2)
