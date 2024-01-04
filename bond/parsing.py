from collections import namedtuple
import jsonpickle

import lexing
import log

Assignment = namedtuple('Assignment', ['left', 'right'])
BinOp = namedtuple('BinOp', ['left', 'op', 'right'])
UnaryOp = namedtuple('UnaryOp', ['op', 'right'])
String = namedtuple('String', ['value'])
Integer = namedtuple('Integer', ['value'])
FnCall = namedtuple('FnCall', ['name', 'args'])
Var = namedtuple('Var', ['name'])


# Builds an abstract syntax tree using tokens from a Lexer instance.
class Parser:
    ok: bool
    nodes: list
    tokens: list
    head: int

    def __init__(self, lexer: lexing.Lexer):
        self.ok = True
        self.nodes = []
        self.tokens = []
        self.head = 0

        if not lexer.ok:
            self._error('lexer was not ok')
            return

        self.tokens = lexer.tokens
        self._parse()

    def __str__(self) -> str:
        d: dict = {'ok': self.ok, 'nodes': []}

        for node in self.nodes:
            d['nodes'].append(node_to_dict(node))

        return jsonpickle.encode(d, unpicklable=False, indent=2)

    def _consume(self, *types) -> tuple[bool, lexing.Token]:
        if self.head >= len(self.tokens):
            return (False, self.tokens[-1])

        token = self.tokens[self.head]

        for type in types:
            if token.type == type:
                self.head += 1
                return (True, token)

        return (False, token)

    def _info(self, message: str, extra: list = []):
        log.info(message, ['Parser'] + extra)

    def _error(self, message: str, extra: list = []):
        log.error(message, ['Parser'] + extra)
        self.ok = False

    def _error_at_head(self, message: str):
        log.error(message, ['Parser', self.tokens[self.head].pos])
        self.ok = False

    def _parse(self):
        self.nodes = []

        if not self.ok:
            return

        self._info('parsing')

        while self.head < len(self.tokens) - 1:
            self.nodes.append(self._statement())

    def _statement(self):
        found, var = self._consume('Var')
        if found:
            found, equal_sign = self._consume('EqualSign')
            if not found:
                self._error_at_head('expected \'=\' after variable token')
                return None

            right = self._expression()
            return Assignment(left=Var(name=var.data), right=right)
        else:
            return self._expression()

    def _expression(self):
        return self._term()

    def _term(self):
        left = self._factor()
        while True:
            found, op = self._consume('Plus', 'Minus')
            if not found:
                break
            right = self._factor()
            left = BinOp(left, op.type, right)
        return left

    def _factor(self):
        left = self._exponent()
        while True:
            found, op = self._consume('Asterisk', 'Slash', 'Percent')
            if not found:
                break
            right = self._exponent()
            left = BinOp(left, op.type, right)
        return left

    def _exponent(self):
        left = self._unary()
        while True:
            found, op = self._consume('Caret')
            if not found:
                break
            right = self._exponent()
            left = BinOp(left, op.type, right)
        return left

    def _unary(self):
        found, op = self._consume('Plus', 'Minus', 'Bang')
        if found:
            right = self._unary()
            return UnaryOp(op.type, right)
        else:
            return self._primary()

    def _primary(self):
        found, string = self._consume('String')
        if found:
            return String(value=string.data)

        found, integer = self._consume('Integer')
        if found:
            return Integer(value=integer.data)

        found, fn_name = self._consume('Identifier')
        if found:
            found, left_paren = self._consume('LeftParen')
            if not found:
                self._error_at_head('expected opening parenthesis after function name')
                return None

            args: list = []
            while True:
                found, right_paren = self._consume('RightParen')
                if found:
                    break

                args.append(self._expression())

                found, right_paren = self._consume('RightParen')
                if found:
                    break

                found, comma = self._consume('Comma')
                if not found:
                    self._error_at_head('expected \',\' or \')\' after function argument')
                    return None

            return FnCall(name=fn_name.data, args=args)

        found, left_paren = self._consume('LeftParen')
        if found:
            expr = self._expression()

            found, right_paren = self._consume('RightParen')
            if not found:
                self._error_at_head('expected \')\' after parenthesized expression')
                return None

            return expr

        found, var = self._consume('Var')
        if found:
            return Var(name=var.data)

        self._error_at_head('expected expression')
        return None


def isinstance_namedtuple(obj) -> bool:
    return (
        isinstance(obj, tuple) and
        hasattr(obj, '_asdict') and
        hasattr(obj, '_fields')
    )


def node_to_dict(node: namedtuple) -> dict:
    d = {'type': type(node).__name__}
    for field in node._fields:
        key = field
        val = getattr(node, key)

        if isinstance_namedtuple(val):
            val = node_to_dict(val)

        d[key] = val
    return d
