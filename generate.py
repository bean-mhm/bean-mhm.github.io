import collections
import pytomlpp
from pathlib import Path
import os.path
import shutil
import errno
# import resource # unix
import sys


def _cfg_resolve_path(data: dict, key: str) -> Path:
    p = Path(data[key]).resolve()
    data[key] = str(p)
    return p


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


def _cfg_resolve_vars(data: dict, vars: dict, var_format: str):
    n_replaced = 0
    for vname, vval in vars.items():
        n_replaced += replace_recursive(data, var_format.format(vname), vval)
    n_resolved = 1
    while (n_replaced > 0):
        if n_resolved > 10:
            raise Exception(
                'too many continuous variable resolutions, maybe a circular '
                'reference?'
            )
        n_replaced = 0
        for vname, vval in vars.items():
            n_replaced += replace_recursive(data, var_format.format(vname), vval)
        n_resolved += 1


class GlobalConfig:
    data: dict
    root_path: Path

    def __init__(self, data: dict):
        self.data = data

        self.root_path = _cfg_resolve_path(self.data, 'root_path')

        _cfg_verify_vars(self.data)
        _cfg_resolve_vars(self.data, self.data['vars'], '$-{}-$')

    def from_str(s):
        return GlobalConfig(pytomlpp.loads(s))

    def from_path(p):
        return GlobalConfig(pytomlpp.loads(open(p, encoding='utf8').read()))

    def __str__(self) -> str:
        return pytomlpp.dumps(self.data)


class Article:
    glob: GlobalConfig
    data: dict
    src_path: Path
    out_path: Path

    def __init__(self, data: dict, glob: GlobalConfig):
        self.glob = glob
        self.data = data

        self.src_path = _cfg_resolve_path(self.data, 'src_path')
        self.out_path = _cfg_resolve_path(self.data, 'out_path')

        _cfg_verify_vars(self.data)
        _cfg_resolve_vars(self.data, self.data['vars'], '$-{}-$')
        _cfg_resolve_vars(self.data, self.glob.data['vars'], '$-{}-$')

    def from_str(s, glob: GlobalConfig):
        return Article(pytomlpp.loads(s), glob)

    def from_path(p, glob: GlobalConfig):
        return Article(pytomlpp.loads(open(p, encoding='utf8').read()), glob)

    def __str__(self) -> str:
        return pytomlpp.dumps(self.data)


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


# increase max stack size and recursion depth
# resource.setrlimit(resource.RLIMIT_STACK, (2**31, -1)) # unix
sys.setrecursionlimit(1_000_000)


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

print(glob)
