import pytomlpp
from pathlib import Path
import os.path
import shutil
import errno


def copy_any(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc:
        if exc.errno in (errno.ENOTDIR, errno.EINVAL):
            shutil.copy(src, dst)
        else:
            raise


def load_cfg(path) -> dict:
    return pytomlpp.loads(open(path, encoding='utf8').read())


def check_var_names(cfg: dict):
    for key in cfg['vars'].keys():
        if key.startswith('_') or key.startswith('-'):
            raise Exception(
                'user-defined variable name can\'t start with _ or -'
            )


def resolve_internal(cfg: dict) -> dict:
    for key, val in cfg['vars'].items():
        for key2 in cfg['vars'].keys():
            cfg['vars'][key2] = cfg['vars'][key2].replace(
                f'$-{key}-$',
                val
            )


src_path = Path('./src').resolve()
os.chdir(src_path)

global_cfg = load_cfg('global.toml')
root_path = Path(global_cfg['root_path']).resolve()

shutil.rmtree(root_path / 'assets')
copy_any(
    src_path / 'assets',
    root_path / 'assets'
)

check_var_names(global_cfg)
resolve_internal(global_cfg)

print(global_cfg)
