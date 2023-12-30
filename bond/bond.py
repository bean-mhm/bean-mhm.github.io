import os
import pathlib
import log
from classes import *


# returns (pos, eof, buf)
def read_char(f, pos: TokenPos) -> (TokenPos, bool, str):
    buf = f.read(1)
    if not buf:
        return (pos, True, '')
    else:
        if buf.endswith('\r'):
            buf += f.read(1)
            if buf.endswith('\r\n'):
                pos.line += 1
                pos.col = 1
            buf = buf[1:]
        elif buf.endswith('\n'):
            pos.line += 1
            pos.col = 1
        else:
            pos.col += 1

        return (pos, False, buf)


# returns (pos, eof, buf)
def append_char(f, pos, buf: TokenPos) -> (TokenPos, bool, str):
    new_pos, eof, new_buf = read_char(f, pos)
    return (new_pos, eof, buf + new_buf)


def parse_file(f) -> ParseResult:
    details = {'pos': TokenPos(1, 1)}
    result = ParseResult()

    while True:
        details['pos'], eof, buf = read_char(f, details['pos'])
        if eof:
            log.info('end of file', details)
            return result

        if buf.isspace():
            continue

        if buf == '#':
            while True:
                details['pos'], eof, buf = read_char(f, details['pos'])
                if eof:
                    log.info('end of file', details)
                    return result
                elif (buf == '\n'):
                    break

            continue

        if buf == '$':
            details['pos'], eof, buf = append_char(f, details['pos'], buf)
            if eof:
                log.error('unexpected end of file', details)
                return result
            elif not buf.startswith('$-'):
                log.error('expected \'-\' after \'$\'', details)
                return result

            while True:
                details['pos'], eof, buf = append_char(f, details['pos'], buf)
                if eof:
                    log.error('unexpected end of file', details)
                    return result
                elif (buf.endswith('-$')):
                    break

            var = VarToken(details['pos'], buf)
            log.verbose(f'read var name {buf}', details)

    return result


script_dir = os.path.dirname(os.path.realpath(__file__))
with open(f'{script_dir}/../src/articles/ray-tracing.ssc', 'r') as f:
    parse_file(f)
