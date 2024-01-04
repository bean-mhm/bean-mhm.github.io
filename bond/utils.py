from pathlib import Path


def resolve_path(path: str):
    return Path(path).resolve().absolute()


def resolve_path_str(path: str):
    return str(resolve_path(path))


def write_to_file(s: str, path: str):
    fpath = resolve_path(path)
    fpath.parent.mkdir(exist_ok=True, parents=True)
    with open(str(fpath), mode='w', encoding='utf8') as f:
        f.write(s)


digit_chars = '0123456789'
hex_chars = '0123456789ABCDEFabcdef'
valid_var_name_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_ '
valid_identifier_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'


def is_digit(s: str) -> bool:
    for char in s:
        if char not in digit_chars:
            return False
    return True


def is_hex(s: str) -> bool:
    for char in s:
        if char not in hex_chars:
            return False
    return True


def check_var_token_inner(s: str) -> bool:
    # can't be empty
    if s == '':
        return False

    # can't start or end with a space
    if s[0] == ' ' or s[-1] == ' ':
        return False

    # check if all else is valid
    for char in s:
        if char not in valid_var_name_chars:
            return False

    return True


def check_var_token(s: str) -> bool:
    # must be at least 5 chars long, example: $-a-$
    if len(s) < 5:
        return False

    # must start with $- and end with -$
    if not s.startswith('$-') or not s.endswith('-$'):
        return False

    # check the inner content
    if not check_var_token_inner(s[2:-2]):
        return False

    return True
