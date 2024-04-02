import lexing
import parsing
import log
import utils

script_dir = str(utils.resolve_path(__file__).parent)


def process(path: str):
    fpath = utils.resolve_path(path)
    path = str(fpath)
    parent_path = str(fpath.parent)
    filename = fpath.name
    filename_stem = fpath.stem

    with open(path, mode='r', encoding='utf8') as f:
        lexer = lexing.Lexer(f)
        utils.write_to_file(
            str(lexer),
            f'{parent_path}/.bond/{filename}.lexer.json'
        )

        if not lexer.ok:
            return False

        parser = parsing.Parser(lexer)
        utils.write_to_file(
            str(parser),
            f'{parent_path}/.bond/{filename}.parser.json'
        )

        if not parser.ok:
            return False

        # TODO Compile

        return True


process(f'{script_dir}/../src/test.ssc')
