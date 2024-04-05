# import resource # unix
import sys
import locale
import time

from pathlib import Path
import os.path

from utils import *


def compile_articles(
    src_path: Path,
    glob: GlobalConfig,
    article_template: str
) -> list[ArticleCategory]:
    print_div()
    print('compiling articles...\n')
    t_start_articles = time.time()

    # remove the previous output directory
    path_remove(glob.root_path / 'articles')

    # keep track of the categories
    categories = []

    # keep track of the category IDs
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
            print(
                f'  - {article.title} ({article.id}) (...)',
                end='',
                flush=True
            )
            t_start_article = time.time()

            # article ID must be unique
            if article.id in article_ids:
                raise Exception(f'article ID "{article.id}" is not unique')
            else:
                article_ids.add(article.id)

            # output path
            article.out_path = \
                glob.root_path / 'articles' / category.id \
                / (article.id + '.html')
            article.out_path.parent.mkdir(parents=True, exist_ok=True)

            # add the article to the category
            category.articles.append(article)

            # open the output file
            with open(article.out_path, mode='w', encoding='utf8') as out_file:
                # start with the template
                out_data = article_template

                # resolve variables
                n_resolved = 0
                while (True):
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
                            'article_author': article.author,
                            'article_date': article.date,
                            'article_date_alt': article.date_alt,
                            'article_contents': article.contents
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

                    out_data, n_replaced = str_resolve_load_src(
                        out_data,
                        src_path
                    )
                    n_total_replaced += n_replaced

                    if (n_total_replaced < 1):
                        break
                    n_resolved += 1
                    if n_resolved > MAX_VAR_RES:
                        raise Exception(ERR_MAX_VAR_RES)

                # write
                out_file.write(out_data)

            print(
                f'\r  - {article.title} ({article.id}) '
                f'({elapsed_since(t_start_article)})'
            )
        print('')

        # add the category to the list
        categories.append(category)

    n_articles = sum(len(category.articles) for category in categories)
    print(
        f'{n_articles} articles compiled in {elapsed_since(t_start_articles)}\n'
    )

    return categories


def compile_index(
    src_path: Path,
    glob: GlobalConfig,
    index_template: str,
    categories: list[ArticleCategory]
):
    print(f'> index (...)', end='', flush=True)
    t_start_index = time.time()

    # output path
    out_path = glob.root_path / 'index.html'

    # remove the previous output file
    path_remove(out_path)

    # load the config
    index = IndexPage.from_path(src_path / 'index.toml', glob)

    # open the output file
    with open(out_path, mode='w', encoding='utf8') as out_file:
        # generate the article category list
        article_list = ''
        for category in categories:
            category_content = index.category_content_start

            for article in category.articles:
                article_path_rel = Path(
                    os.path.relpath(article.out_path, out_path.parent)
                ).as_posix()
                article_link_content, _ = str_resolve_vars(
                    index.article_link_content,
                    {
                        'article_id': article.id,
                        'article_title': article.title,
                        'article_author': article.author,
                        'article_date': article.date,
                        'article_date_alt': article.date_alt,
                        'article_contents': article.contents,
                        'article_path': article_path_rel
                    },
                    False
                )
                category_content += article_link_content

            category_content, _ = str_resolve_vars(
                category_content,
                {
                    'category_id': category.id,
                    'category_name': category.name,
                    'category_desc': category.desc
                },
                False
            )

            category_content += index.category_content_end
            article_list += category_content

        # start with the template
        out_data = index_template

        # resolve variables
        n_resolved = 0
        while (True):
            n_total_replaced = 0

            root_path_rel = '.'
            out_data, n_replaced = str_resolve_vars(
                out_data,
                {
                    'root_path': root_path_rel,
                    'article_list': article_list
                },
                False
            )
            n_total_replaced += n_replaced

            out_data, n_replaced = str_resolve_vars(
                out_data,
                index.vars,
                True
            )
            n_total_replaced += n_replaced

            out_data, n_replaced = str_resolve_vars(
                out_data,
                glob.vars,
                True
            )
            n_total_replaced += n_replaced

            out_data, n_replaced = str_resolve_load_src(out_data, src_path)
            n_total_replaced += n_replaced

            if (n_total_replaced < 1):
                break
            n_resolved += 1
            if n_resolved > MAX_VAR_RES:
                raise Exception(ERR_MAX_VAR_RES)

        # write
        out_file.write(out_data)

    print(f'\r> index ({elapsed_since(t_start_index)})')


def compile_pages(
    src_path: Path,
    glob: GlobalConfig,
    index_template: str,
    categories: list[ArticleCategory]
):
    print_div()
    print('compiling pages...\n')
    t_start_pages = time.time()

    compile_index(
        src_path,
        glob,
        index_template,
        categories
    )

    print(f'\nall pages compiled in {elapsed_since(t_start_pages)}\n')


def generate_site():
    # increase max stack size and recursion depth
    # resource.setrlimit(resource.RLIMIT_STACK, (2**31, -1)) # unix
    sys.setrecursionlimit(1_000_000)

    # set locale
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

    # work in the source directory
    src_path = Path('./src').resolve()
    os.chdir(src_path)

    t_start = time.time()

    glob = GlobalConfig.from_path('global.toml')

    if not glob.root_path.exists():
        glob.root_path.mkdir(parents=True, exist_ok=True)

    path_remove(glob.root_path / 'assets')
    path_copy(
        src_path / 'assets',
        glob.root_path / 'assets'
    )

    index_template = read_file(src_path / 'templates' / 'index.html')
    article_template = read_file(src_path / 'templates' / 'article.html')

    categories = compile_articles(
        src_path,
        glob,
        article_template
    )
    compile_pages(
        src_path,
        glob,
        index_template,
        categories
    )

    print_div()
    print(f'finished in {elapsed_since(t_start)}')


generate_site()
