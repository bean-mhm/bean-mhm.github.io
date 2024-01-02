import os

import tokens
import syntax


def process(path: str):
    with open(path, mode='r', encoding="utf8") as f:
        tokenization_result = tokens.tokenize(f)
        print(tokenization_result)

        syntax_tree = syntax.build(tokenization_result)
        print(syntax_tree)

        # TODO Compile


script_dir = os.path.dirname(os.path.realpath(__file__))
process(f'{script_dir}/../src/articles/ray-tracing.ssc')
