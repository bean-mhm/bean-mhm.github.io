import copy
import jsonpickle

import log
import utils


class TokenPos:
    line: int
    col: int

    def __init__(self, line: int = 1, col: int = 0):
        self.line = line
        self.col = col

    def __str__(self) -> str:
        return f'{self.line}, {self.col}'


class Token:
    type: str
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


class CommaToken(Token):
    def __init__(self, pos: TokenPos):
        super().__init__(type(self).__name__, pos)


class StringLiteralToken(Token):
    value: str

    def __init__(self, pos: TokenPos, value: str):
        super().__init__(type(self).__name__, pos)
        self.value = value


class FunctionCallEndToken(Token):
    def __init__(self, pos: TokenPos):
        super().__init__(type(self).__name__, pos)


class FunctionCallStartToken(Token):
    name: str

    def __init__(self, pos: TokenPos, name: str):
        super().__init__(type(self).__name__, pos)
        self.name = name


class TokenizationResult:
    ok: bool
    tokens: list

    def __init__(self):
        self.ok = False
        self.tokens = []

    def __str__(self) -> str:
        return jsonpickle.encode(self.__dict__, unpicklable=False, indent=2)


# returns (pos, eof, buf)
def read_char(f, pos: TokenPos) -> (TokenPos, bool, str):
    buf = f.read(1)
    if not buf:
        return (pos, True, '')
    else:
        if buf[-1] == '\r':
            return read_char(f, pos)
        elif buf[-1] == '\n':
            pos.line += 1
            pos.col = 0
        else:
            pos.col += 1

        return (pos, False, buf)


# returns (pos, eof, buf)
def append_char(f, pos: TokenPos, buf: str) -> (TokenPos, bool, str):
    pos, eof, new_buf = read_char(f, pos)
    return (pos, eof, buf + new_buf)


def log_eof(extra: list = []):
    log.verbose('end of file', extra)


def log_unexpected_eof(extra: list = []):
    log.error('unexpected end of file', extra)


def log_invalid_id(extra: list = []):
    log.error('invalid identifier', extra)


def log_invalid_var_name(extra: list = []):
    log.error('invalid variable name', extra)


def log_invalid_function_name(extra: list = []):
    log.error('invalid function name', extra)


# Extract tokens in sequential order and with no tree-like or recursive structure
def tokenize(f) -> TokenizationResult:
    log.info('starting tokenization')

    pos = TokenPos()
    result = TokenizationResult()

    while True:
        pos, eof, buf = read_char(f, pos)
        if eof:
            log_eof([pos])
            break

        elif buf.isspace():
            continue

        # comment
        elif buf == '#':
            eof = False
            while True:
                pos, eof, buf = read_char(f, pos)
                if eof:
                    log_eof([pos])
                    break
                elif buf == '\n':
                    break

            if eof:
                break
            else:
                continue

        # variable
        elif buf == '$':
            start_pos = copy.deepcopy(pos)
            pos, eof, buf = append_char(f, pos, buf)
            if eof:
                log_unexpected_eof([pos])
                return result
            elif not buf.startswith('$-'):
                log.error('expected \'-\' after \'$\'', [pos])
                return result

            while True:
                pos, eof, buf = append_char(f, pos, buf)
                if eof:
                    log_unexpected_eof([pos])
                    return result
                elif buf.endswith('-$'):
                    break

            if not utils.is_valid_var_name(buf):
                log_invalid_var_name([start_pos])
                return result

            result.tokens.append(VarToken(start_pos, buf))
            continue

        # equal sign
        elif buf == '=':
            result.tokens.append(EqualSignToken(pos))
            continue

        # comma
        elif buf == ',':
            result.tokens.append(CommaToken(pos))
            continue

        # string literal
        elif buf == '"':
            start_pos = copy.deepcopy(pos)
            while True:
                pos, eof, buf = append_char(f, pos, buf)
                if eof:
                    log_unexpected_eof([pos])
                    return result
                elif buf[-1] == '\\':
                    pos, eof, buf = append_char(f, pos, buf)
                    if eof:
                        log_unexpected_eof([pos])
                        return result
                    elif buf[-1] == 'a':
                        buf = buf[:-2] + '\a'
                    elif buf[-1] == 'b':
                        buf = buf[:-2] + '\b'
                    elif buf[-1] == 'f':
                        buf = buf[:-2] + '\f'
                    elif buf[-1] == 'n':
                        buf = buf[:-2] + '\n'
                    elif buf[-1] == 'r':
                        buf = buf[:-2] + '\r'
                    elif buf[-1] == 't':
                        buf = buf[:-2] + '\t'
                    elif buf[-1] == 'v':
                        buf = buf[:-2] + '\v'
                    elif buf[-1].lower() == 'u':
                        n_digits = 4
                        if buf[-1] == 'U':
                            n_digits = 8

                        hex_start_pos = copy.deepcopy(pos)
                        hex = ''
                        for _ in range(n_digits):
                            pos, eof, hex = append_char(f, pos, hex)
                            if eof:
                                log_unexpected_eof([pos])
                                return result
                        if not utils.is_hex(hex):
                            log.error(
                                f'expected {n_digits}-digit hex code after \'\\u\'',
                                [hex_start_pos]
                            )
                            return result

                        actual_unicode_char = chr(int(hex, 16))
                        buf = buf[:-2] + actual_unicode_char
                    else:
                        buf = buf[:-2] + buf[-1]
                elif buf[-1] == '"':
                    break

            s = buf[1:-1]
            if s[0] == '\n':
                s = s[1:]
            if s[-1] == '\n':
                s = s[:-1]
            result.tokens.append(StringLiteralToken(start_pos, s))
            continue

        # function call end
        elif buf == ')':
            result.tokens.append(FunctionCallEndToken(pos))
            continue

        # function call start
        else:
            start_pos = copy.deepcopy(pos)
            while True:
                pos, eof, buf = append_char(f, pos, buf)
                if eof:
                    log_unexpected_eof([pos])
                    return result
                elif buf[-1] == '(':
                    break

            s = buf[:-1]
            if not utils.is_valid_function_name(s):
                log_invalid_function_name([start_pos])
                return result

            result.tokens.append(FunctionCallStartToken(start_pos, s))
            continue

    # join adjacent string literals
    i = 0
    while (i < len(result.tokens) - 1):
        are_adjacent = isinstance(result.tokens[i], StringLiteralToken)\
            and isinstance(result.tokens[i + 1], StringLiteralToken)

        if are_adjacent:
            result.tokens[i].value += result.tokens[i + 1].value
            del result.tokens[i + 1]
        else:
            i += 1

    result.ok = True
    return result
