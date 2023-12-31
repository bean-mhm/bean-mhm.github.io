valid_id_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_ '
digit_chars = '0123456789'
hex_chars = '0123456789ABCDEFabcdef'


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


def is_valid_id(s: str) -> bool:
    # can't be empty
    if s == '':
        return False

    # can't start with a digit
    if s[0] in digit_chars:
        return False

    # can't start or end with a space
    if s[0] == ' ' or s[-1] == ' ':
        return False

    # check if all else is valid
    for char in s:
        if char not in valid_id_chars:
            return False

    return True


def is_valid_var_name(s: str) -> bool:
    # must be at least 5 chars long, example: $-a-$
    if len(s) < 5:
        return False

    # must start with $- and end with -$
    if not s.startswith('$-') or not s.endswith('-$'):
        return False

    # check the inner content
    if not is_valid_id(s[2:-2]):
        return False

    return True
