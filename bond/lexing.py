import copy
from collections import namedtuple
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


Token = namedtuple('Token', ['pos', 'type', 'data'])


# Extracts tokens in sequential order and with no tree-like or recursive structure.
class Lexer:
    ok: bool
    tokens: list
    f = None

    def __init__(self, f):
        self.ok = False
        self.tokens = []
        self.f = f

        self._tokenize()

    def __str__(self) -> str:
        d: dict = {'ok': self.ok, 'tokens': self.tokens}
        return jsonpickle.encode(d, unpicklable=False, indent=2)

    def _info(self, message: str, extra: list = []):
        log.info(message, ['Lexer'] + extra)

    def _error(self, message: str, extra: list = []):
        log.error(message, ['Lexer'] + extra)
        self.ok = False

    def _log_unexpected_eof(self, extra: list = []):
        self._error('unexpected end of file', extra)

    def _log_invalid_var_token(self, extra: list = []):
        self._error('invalid variable token', extra)

    def _tokenize(self):
        self._info('starting tokenization')

        pos = TokenPos()
        eof = False
        buf = ''
        skip_next_read = False
        while True:
            if skip_next_read:
                skip_next_read = False
            else:
                pos, eof, buf = read_char(self.f, pos)
                if eof:
                    self.tokens.append(Token(pos=copy.deepcopy(pos), type='EOF', data=buf))
                    break

            if buf.isspace():
                continue

            # comment
            if buf == '#':
                eof = False
                while True:
                    pos, eof, buf = read_char(self.f, pos)
                    if eof:
                        self.tokens.append(Token(pos=copy.deepcopy(pos), type='EOF', data=buf))
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

                pos, eof, buf = append_char(self.f, pos, buf)
                if eof:
                    self._log_unexpected_eof([pos])
                    return
                elif not buf.startswith('$-'):
                    self._error('expected \'-\' after \'$\'', [pos])
                    return

                while True:
                    pos, eof, buf = append_char(self.f, pos, buf)
                    if eof:
                        self._log_unexpected_eof([pos])
                        return
                    elif buf.endswith('-$'):
                        break

                if not utils.check_var_token(buf):
                    self._log_invalid_var_token([start_pos])
                    return

                self.tokens.append(Token(pos=start_pos, type='Var', data=buf))
                continue

            # equal sign
            elif buf == '=':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='EqualSign', data=buf))
                continue

            # comma
            elif buf == ',':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='Comma', data=buf))
                continue

            # left paren
            elif buf == '(':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='LeftParen', data=buf))
                continue

            # right paren
            elif buf == ')':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='RightParen', data=buf))
                continue

            # plus
            elif buf == '+':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='Plus', data=buf))
                continue

            # minus
            elif buf == '-':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='Minus', data=buf))
                continue

            # asterisk
            elif buf == '*':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='Asterisk', data=buf))
                continue

            # slash
            elif buf == '/':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='Slash', data=buf))
                continue

            # percent
            elif buf == '%':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='Percent', data=buf))
                continue

            # caret
            elif buf == '^':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='Caret', data=buf))
                continue

            # bang
            elif buf == '!':
                self.tokens.append(Token(pos=copy.deepcopy(pos), type='Bang', data=buf))
                continue

            # string literal
            elif buf == '"':
                start_pos = copy.deepcopy(pos)
                while True:
                    pos, eof, buf = append_char(self.f, pos, buf)
                    if eof:
                        self._log_unexpected_eof([pos])
                        return
                    elif buf[-1] == '\\':
                        pos, eof, buf = append_char(self.f, pos, buf)
                        if eof:
                            self._log_unexpected_eof([pos])
                            return
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
                        elif buf[-1] in 'xuU':
                            n_digits = 2
                            if buf[-1] == 'u':
                                n_digits = 4
                            elif buf[-1] == 'U':
                                n_digits = 8

                            hex_start_pos = copy.deepcopy(pos)
                            hex = ''
                            for _ in range(n_digits):
                                pos, eof, hex = append_char(self.f, pos, hex)
                                if eof:
                                    self._log_unexpected_eof([pos])
                                    return
                            if not utils.is_hex(hex):
                                self._error(
                                    f'expected {n_digits}-digit hex code after \'\\{buf[-1]}\'',
                                    [hex_start_pos]
                                )
                                return

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

                self.tokens.append(Token(pos=start_pos, type='String', data=s))

                continue

            # integer
            elif utils.is_digit(buf):
                start_pos = copy.deepcopy(pos)
                while True:
                    pos, eof, buf = append_char(self.f, pos, buf)
                    if eof:
                        self._log_unexpected_eof([pos])
                        return
                    elif not utils.is_digit(buf):
                        break

                s = buf[:-1]
                i = int(s)
                self.tokens.append(Token(pos=start_pos, type='Integer', data=i))

                # already read a non-integer char, so don't read another char
                skip_next_read = True
                buf = buf[-1]
                continue

            # identifier
            elif buf in utils.valid_identifier_chars and not utils.is_digit(buf):
                start_pos = copy.deepcopy(pos)
                while True:
                    pos, eof, buf = append_char(self.f, pos, buf)
                    if eof:
                        self._log_unexpected_eof([pos])
                        return
                    elif buf[-1] not in utils.valid_identifier_chars:
                        break

                s = buf[:-1]
                self.tokens.append(Token(pos=start_pos, type='Identifier', data=s))

                # already read an invalid char, so don't read another char
                skip_next_read = True
                buf = buf[-1]
                continue

            else:
                self._error(f'unrecognizable token', [pos])
                return

        # join adjacent string literals
        i = 0
        while (i < len(self.tokens) - 1):
            are_adjacent = self.tokens[i].type == 'String'\
                and self.tokens[i + 1].type == 'String'

            if are_adjacent:
                self.tokens[i].value += self.tokens[i + 1].data
                del self.tokens[i + 1]
            else:
                i += 1

        self.ok = True


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
