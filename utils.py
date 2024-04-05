import copy
import time
from datetime import datetime

from pathlib import Path
import shutil
import errno
import re

import pytomlpp


MAX_VAR_RES = 10
ERR_MAX_VAR_RES = \
    'too many continuous variable resolutions, maybe a circular reference or ' \
    'repeated variable names in different configs?'


class GlobalConfig:
    root_path: Path
    vars: dict

    def __init__(self, data: dict):
        data_copy = copy.deepcopy(data)

        _cfg_verify_vars(data_copy)
        _cfg_resolve_vars(data_copy, data_copy['vars'], True)
        self.vars = data_copy['vars']

        self.root_path = Path(data_copy['root_path']).resolve()

    def from_str(s):
        return GlobalConfig(load_toml_str(s))

    def from_path(p):
        return GlobalConfig(load_toml_file(p))

    def __str__(self) -> str:
        return pytomlpp.dumps({
            'root_path': str(self.root_path),
            'vars': self.vars
        })


class Article:
    glob: GlobalConfig
    id: str
    title: str
    author: str
    date: str
    contents: str
    vars: dict
    out_path: Path

    def __init__(self, data: dict, glob: GlobalConfig):
        self.glob = glob

        data_copy = copy.deepcopy(data)

        _cfg_verify_vars(data_copy)
        _cfg_resolve_vars(data_copy, data_copy['vars'], True)
        _cfg_resolve_vars(data_copy, glob.vars, True)

        self.id = str(data_copy['article_id']).strip().lower()
        self.title = str(data_copy['article_title']).strip()
        self.author = str(data_copy['article_author']).strip()

        self.date = str(data_copy['article_date']).strip()
        dt = datetime.strptime(self.date, '%Y-%m-%d')
        self.date_alt = f'{dt.strftime("%b")} {dt.day}, {dt.year}'

        self.contents = str(data_copy['article_contents'])
        self.vars = data_copy['vars']
        self.out_path = Path()

        _cfg_resolve_vars(
            self.vars,
            {
                'article_id': self.id,
                'article_title': self.title,
                'article_author': self.author,
                'article_date': self.date,
                'article_date_alt': self.date_alt,
                'article_contents': self.contents
            },
            False
        )

    def from_str(s, glob: GlobalConfig):
        return Article(load_toml_str(s), glob)

    def from_path(p, glob: GlobalConfig):
        return Article(load_toml_file(p), glob)

    def __str__(self) -> str:
        return pytomlpp.dumps({
            'article_id': self.id,
            'article_title': self.title,
            'article_author': self.author,
            'article_date': self.date,
            'article_date_alt': self.date_alt,
            'article_contents': self.contents,
            'vars': self.vars,
            'out_path': str(self.out_path)
        })


class ArticleCategory:
    id: str
    name: str
    desc: str
    articles: list[Article]

    def __init__(self, data: dict):
        self.id = str(data['category_id']).strip().lower()
        self.name = str(data['category_name']).strip()
        self.desc = str(data['category_desc']).strip()
        self.articles = []

    def from_str(s):
        return ArticleCategory(load_toml_str(s))

    def from_path(p):
        return ArticleCategory(load_toml_file(p))

    def __str__(self) -> str:
        return pytomlpp.dumps({
            'category_id': self.id,
            'category_name': self.name,
            'category_desc': self.desc,
            'articles': [article.id for article in self.articles]
        })


class IndexPage:
    glob: GlobalConfig
    category_content_start: str
    article_link_content: str
    category_content_end: str
    vars: dict

    def __init__(self, data: dict, glob: GlobalConfig):
        self.glob = glob

        data_copy = copy.deepcopy(data)

        _cfg_verify_vars(data_copy)
        _cfg_resolve_vars(data_copy, data_copy['vars'], True)
        _cfg_resolve_vars(data_copy, glob.vars, True)

        self.category_content_start = str(data_copy['category_content_start'])
        self.article_link_content = str(data_copy['article_link_content'])
        self.category_content_end = str(data_copy['category_content_end'])
        self.vars = data_copy['vars']

        _cfg_resolve_vars(
            self.vars,
            {
                'category_content_start': self.category_content_start,
                'article_link_content': self.article_link_content,
                'category_content_end': self.category_content_end
            },
            False
        )

    def from_str(s, glob: GlobalConfig):
        return IndexPage(load_toml_str(s), glob)

    def from_path(p, glob: GlobalConfig):
        return IndexPage(load_toml_file(p), glob)

    def __str__(self) -> str:
        return pytomlpp.dumps({
            'category_content_start': self.category_content_start,
            'article_link_content': self.article_link_content,
            'category_content_end': self.category_content_end,
            'vars': self.vars
        })


def print_div():
    print('--------------------------------------------------\n')


def elapsed_since(t_start):
    elapsed = time.time() - t_start
    return f'{elapsed:.3f} s'


def path_remove(p: Path):
    if not p.exists():
        return
    if (p.is_dir()):
        shutil.rmtree(p)
    else:
        p.unlink()


def path_copy(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc:
        if exc.errno in (errno.ENOTDIR, errno.EINVAL):
            shutil.copy(src, dst)
        else:
            raise


def read_file(p) -> str:
    return open(p, encoding='utf8').read()


def load_toml_str(s) -> dict:
    return pytomlpp.loads(s)


def load_toml_file(p) -> dict:
    return pytomlpp.loads(read_file(p))


# * returns the number of replacements
def replace_recursive(data: dict, replace_what: str, replace_with: str) -> int:
    n_replaced = 0
    for k, v in data.items():
        if isinstance(v, dict):
            replace_recursive(v, replace_what, replace_with)
        elif type(v) is list:
            replace_recursive(
                {i: v for i, v in enumerate(v)},
                replace_what,
                replace_with
            )
        elif type(v) is str:
            if replace_what in v:
                data[k] = data[k].replace(replace_what, replace_with)
                n_replaced += 1
    return n_replaced


def get_var_format(user_defined: bool) -> str:
    if user_defined:
        return '$-{}-$'
    return '$--{}--$'


def _cfg_verify_vars(data: dict):
    if 'vars' not in data:
        data['vars'] = {}

    if not isinstance(data['vars'], dict):
        raise Exception('vars must be a dict')

    for key in data['vars'].keys():
        if key.startswith('-'):
            raise Exception(
                'variable name can\'t start with "-"'
            )


# use key-value pairs from vars to modify values recursively in data
def _cfg_resolve_vars(data: dict, vars: dict, user_defined: bool):
    var_fmt = get_var_format(user_defined)
    n_resolved = 0
    while (True):
        if n_resolved > MAX_VAR_RES:
            raise Exception(ERR_MAX_VAR_RES)
        n_replaced = 0
        for vname, vval in vars.items():
            n_replaced += replace_recursive(data, var_fmt.format(vname), vval)
        if (n_replaced < 1):
            break
        n_resolved += 1


# use key-value pairs from vars to modify values in s
# * returns tuple with the result and the number of replacements
def str_resolve_vars(
    s: str,
    vars: dict,
    user_defined: bool
) -> tuple[str, int]:
    var_fmt = get_var_format(user_defined)
    n_replaced = 0
    for vname, vval in vars.items():
        replace_what = var_fmt.format(vname)
        if replace_what in s:
            s = s.replace(replace_what, vval)
            n_replaced += 1
    return s, n_replaced


# find places in s where we need to load text from a source file
# * the paths referenced must be relative to the source directory and they
#   shouldn't start with a slash
# * example: $--load_src--$("templates/item.html")
# * returns tuple with the result and the number of replacements
def str_resolve_load_src(s: str, src_path: Path) -> tuple[str, int]:
    start_trigger = get_var_format(False).format('load_src') + '("'
    end_trigger = '")'
    start_pos = 0
    n_replaced = 0
    while True:
        trigger_pos = s.find(start_trigger, start_pos)
        if trigger_pos == -1:
            break

        path_start_pos = trigger_pos + len(start_trigger)
        path_end_pos = s.find(end_trigger, path_start_pos)
        if path_end_pos == -1:
            raise Exception('unclosed path')

        path = src_path / Path(
            s[path_start_pos:path_end_pos]
        )
        content = read_file(path)

        s = \
            s[:trigger_pos] \
            + content \
            + s[path_end_pos + len(end_trigger):]
        n_replaced += 1

        start_pos = path_end_pos + len(end_trigger)

    return s, n_replaced


# https://stackoverflow.com/a/5967539
def try_str_to_int(s):
    return int(s) if s.isdigit() else s


# https://stackoverflow.com/a/5967539
def natural_keys(s):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [try_str_to_int(c) for c in re.split(r'(\d+)', s)]


def natural_keys_for_iterdir(item):
    return natural_keys(str(item.parts[-1]))


def iterdir_sorted(p: Path) -> list[Path]:
    items = list(p.iterdir())
    items.sort(key=natural_keys_for_iterdir)
    return items
