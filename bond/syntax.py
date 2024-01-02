import copy
import jsonpickle

import tokens
import log


class Node:
    type: str
    pos: tokens.TokenPos

    def __init__(self, type: str, pos: tokens.TokenPos):
        self.type = type
        self.pos = copy.deepcopy(pos)


class VarNode(Node):
    name: str

    def __init__(self, pos: tokens.TokenPos, name: str):
        super().__init__(type(self).__name__, pos)
        self.name = name


class AssignmentNode(Node):
    left: VarNode
    right: Node

    def __init__(self, pos: tokens.TokenPos, left: VarNode, right: Node):
        super().__init__(type(self).__name__, pos)


class FunctionCallNode(Node):
    name: str
    args: list = []

    def __init__(self, pos: tokens.TokenPos, name: str, args: list = []):
        super().__init__(type(self).__name__, pos)
        self.name = name
        self.args = args


class StringLiteralNode(Node):
    value: str

    def __init__(self, pos: tokens.TokenPos, value: str):
        super().__init__(type(self).__name__, pos)
        self.value = value


class SyntaxTree:
    ok: bool
    nodes: list

    def __init__(self):
        self.ok = False
        self.nodes = []

    def __str__(self) -> str:
        return jsonpickle.encode(self.__dict__, unpicklable=False, indent=2)


def build(tokenization_result: tokens.TokenizationResult) -> SyntaxTree:
    log.info('building syntax tree')

    result = SyntaxTree()

    if not tokenization_result.ok:
        log.error('tokenization result was not ok')
        return result

    tokens: list = tokenization_result.tokens

    # TODO build syntax tree
