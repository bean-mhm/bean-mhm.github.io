# import resource # unix
import sys
import time

from pathlib import Path
import os.path

from utils import *


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

# start compiling articles
print_div()
print('compiling articles...\n')
t_start_articles = time.time()

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

# done compiling articles
n_articles = sum(len(category.articles) for category in categories)
print(f'{n_articles} articles compiled in {elapsed_since(t_start_articles)}\n')

# start compiling pages
print_div()
print('compiling pages...\n')
t_start_pages = time.time()

# index

# remove the previous output file
path_remove(glob.root_path / 'index.html')

print(f'> index (...)', end='', flush=True)
t_start_index = time.time()
index = IndexPage.from_path(src_path / 'index.toml', glob)

# TODO compile index

print(f'\r> index ({elapsed_since(t_start_article)})')

# done compiling pages
print(f'\nall pages compiled in {elapsed_since(t_start_pages)}\n')

# all done
print_div()
print(f'finished in {elapsed_since(t_start)}')
