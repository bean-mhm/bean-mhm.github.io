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

    # remove the previous output directory
    t_start_remove_old_outputs = time.time()
    path_remove(glob.root_path / 'articles')
    s_elapsed = elapsed_since(t_start_remove_old_outputs)
    print(f'removed the old output files in {s_elapsed}\n')

    # keep track of the categories and the articles inside them
    categories = []

    # keep track of the category IDs
    category_ids = set()

    # articles source directory
    articles_path = src_path / 'articles'
    if not articles_path.is_dir():
        raise Exception('articles directory "{articles_path}" doesn\'t exist')

    t_start_analyze = time.time()

    # iterate through the articles source directory
    for p in iterdir_sorted(articles_path):
        # find a category
        if not p.is_dir():
            continue
        category_path = p / 'category.toml'
        if not category_path.exists():
            continue
        category = ArticleCategory.from_path(category_path)

        # category ID must be unique
        if category.id in category_ids:
            raise Exception(f'category ID "{category.id}" is not unique')
        else:
            category_ids.add(category.id)

        # keep track of all the article IDs in the current category
        article_ids = set()

        # iterate through the articles in the category
        for p2 in iterdir_sorted(p):
            # find an article
            if p2.is_dir():
                continue
            if p2.suffix != '.toml':
                continue
            if p2.stem.lower() == 'category':
                continue
            article = Article.from_path(p2, glob)

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

        # add the category to the list
        categories.append(category)

    n_articles = sum(len(category.articles) for category in categories)
    s_elapsed = elapsed_since(t_start_analyze)
    print(f'found {n_articles} articles in {s_elapsed}\n')

    t_start_compile = time.time()

    # write the output files
    for category in categories:
        print(f'> {category.name} ({category.id})')

        for i in range(len(category.articles)):
            article = category.articles[i]
            print(
                f'  - {article.title} ({article.id}) (...)',
                end='',
                flush=True
            )
            t_start_article = time.time()

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

                    out_data, n_replaced = str_resolve_load(
                        out_data,
                        'load_src',
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

            s_elapsed = elapsed_since(t_start_article)
            print(f'\r  - {article.title} ({article.id}) ({s_elapsed})')

        print('')

    s_elapsed = elapsed_since(t_start_compile)
    print(f'all {n_articles} articles compiled in {s_elapsed}\n')

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
            if not category.visible:
                continue

            category_content = index.category_content_start

            n_visible_articles = 0
            for article in category.articles:
                if article.visible:
                    n_visible_articles += 1
                else:
                    continue

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

            if n_visible_articles == 0:
                category_content += index.category_empty_content

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

            out_data, n_replaced = str_resolve_load(
                out_data,
                'load_src',
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

    print_div()
    t_start = time.time()

    t_start_load_glob = time.time()
    glob = GlobalConfig.from_path('global.toml')
    s_elapsed = elapsed_since(t_start_load_glob)
    print(f'loaded the global config in {s_elapsed}')

    if not glob.root_path.exists():
        glob.root_path.mkdir(parents=True, exist_ok=True)

    t_start_remove_assets = time.time()
    path_remove(glob.root_path / 'assets')
    s_elapsed = elapsed_since(t_start_remove_assets)
    print(f'removed the old assets output directory in {s_elapsed}')

    t_start_copy_assets = time.time()
    path_copy(
        src_path / 'assets',
        glob.root_path / 'assets'
    )
    s_elapsed = elapsed_since(t_start_copy_assets)
    print(f'copied assets in {s_elapsed}\n')

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
