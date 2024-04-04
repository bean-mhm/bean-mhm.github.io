# import resource # unix
import sys
import copy
import time

import pytomlpp

from pathlib import Path
import os.path
import shutil
import errno


err_max_var_res = \
    'too many continuous variable resolutions, maybe a circular reference or ' \
    'repeated variable names in different configs?'


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


def _cfg_verify_vars(data: dict):
    if not data['vars']:
        data['vars'] = {}

    if not isinstance(data['vars'], dict):
        raise Exception('vars must be a dict')

    for key in data['vars'].keys():
        if key.startswith('-'):
            raise Exception(
                'variable name can\'t start with "-"'
            )


# returns the number of replacements
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


# use key-value pairs from vars to modify values recursively in data
def _cfg_resolve_vars(data: dict, vars: dict, user_defined: bool):
    var_fmt = get_var_format(user_defined)
    n_resolved = 0
    while (True):
        if n_resolved > 10:
            raise Exception(err_max_var_res)
        n_replaced = 0
        for vname, vval in vars.items():
            n_replaced += replace_recursive(data, var_fmt.format(vname), vval)
        if (n_replaced < 1):
            break
        n_resolved += 1


# use key-value pairs from vars to modify values in s
# returns tuple with the result and the number of replacements
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
        self.contents = str(data_copy['article_contents'])
        self.vars = data_copy['vars']
        self.out_path = Path()

        _cfg_resolve_vars(
            self.vars,
            {
                'article_id': self.id,
                'article_title': self.title,
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
            'article_contents': self.contents,
            'vars': self.vars
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
            'category_desc': self.desc
        })


# increase max stack size and recursion depth
# resource.setrlimit(resource.RLIMIT_STACK, (2**31, -1)) # unix
sys.setrecursionlimit(1_000_000)

t_start = time.time()

# work in the source directory
src_path = Path('./src').resolve()
os.chdir(src_path)

# load the global config
glob = GlobalConfig.from_path('global.toml')

# copy assets
path_remove(glob.root_path / 'assets')
path_copy(
    src_path / 'assets',
    glob.root_path / 'assets'
)

# remove the articles output directory before rewriting it
path_remove(glob.root_path / 'articles')

# HTML template files
index_template = read_file(src_path / 'templates' / 'index.html')
footer_template = read_file(src_path / 'templates' / 'footer.html')
article_template = read_file(src_path / 'templates' / 'article.html')

# keep track of the article categories
categories = []

# keep track of all the article category IDs
category_ids = set()

# articles source directory
articles_path = src_path / 'articles'
if not articles_path.is_dir():
    raise Exception('articles directory "{articles_path}" doesn\'t exist')

# iterate through the articles source directory
for p in articles_path.iterdir():
    # find a category
    if not p.is_dir():
        continue
    category_path = p / 'category.toml'
    if not category_path.exists():
        continue
    category = ArticleCategory.from_path(category_path)
    print(f'> {category.name} ({category.id})')

    # category ID must be unique
    if category.id in category_ids:
        raise Exception(f'category ID "{category.id}" is not unique')
    else:
        category_ids.add(category.id)

    # keep track of all the article IDs in the current category
    article_ids = set()

    # iterate through the articles in the category
    for p2 in p.iterdir():
        # find an article
        if p2.is_dir():
            continue
        if p2.suffix != '.toml':
            continue
        if p2.stem.lower() == 'category':
            continue
        article = Article.from_path(p2, glob)
        print(f'  - {article.title} ({article.id}) (...)', end='', flush=True)
        t_start_article = time.time()

        # article ID must be unique
        if article.id in article_ids:
            raise Exception(f'article ID "{article.id}" is not unique')
        else:
            article_ids.add(article.id)

        # output path
        article.out_path = \
            glob.root_path / 'articles' / category.id / (article.id + '.html')
        article.out_path.parent.mkdir(parents=True, exist_ok=True)

        # add the article to the category
        category.articles.append(article)

        # open the output file
        with open(article.out_path, mode='w', encoding='utf8') as out_file:
            # start with the template
            out_data = article_template

            # resolve the variables
            n_resolved = 0
            while (True):
                if n_resolved > 10:
                    raise Exception(err_max_var_res)
                n_total_replaced = 0

                root_path_rel = Path(
                    os.path.relpath(glob.root_path, article.out_path.parent)
                ).as_posix()
                out_data, n_replaced = str_resolve_vars(
                    out_data,
                    {
                        'root_path': root_path_rel,
                        'article_id': article.id,
                        'article_title': article.title,
                        'article_contents': article.contents,
                        'footer': footer_template
                    },
                    False
                )
                n_total_replaced += n_replaced

                out_data, n_replaced = str_resolve_vars(
                    out_data,
                    article.vars,
                    True
                )
                n_total_replaced += n_replaced

                out_data, n_replaced = str_resolve_vars(
                    out_data,
                    glob.vars,
                    True
                )
                n_total_replaced += n_replaced

                if (n_total_replaced < 1):
                    break
                n_resolved += 1

            # write
            out_file.write(out_data)

        print(
            f'\r  - {article.title} ({article.id}) '
            f'({elapsed_since(t_start_article)})'
        )
    print('')

    # add the category to the list
    categories.append(category)

print(f'finished in {elapsed_since(t_start)}')
