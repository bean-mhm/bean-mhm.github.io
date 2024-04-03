import pytomlpp
from pathlib import Path
import os.path
import shutil
import errno


class Config:
    data: dict

    def __init__(self, data: dict):
        self.data = data

        # verify variable names
        for key in self.data['vars'].keys():
            if key.startswith('-'):
                raise Exception(
                    'variable name can\'t start with "-"'
                )

        # resolve variables internally
        for key, val in self.data['vars'].items():
            for key2 in self.data['vars'].keys():
                self.data['vars'][key2] = self.data['vars'][key2].replace(
                    f'$-{key}-$',
                    val
                )

    def from_str(s):
        return Config(pytomlpp.loads(s))

    def from_path(p):
        return Config(pytomlpp.loads(open(p, encoding='utf8').read()))

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


# work in the source directory
src_path = Path('./src').resolve()
os.chdir(src_path)

# load the global config
glob = Config.from_path('global.toml')
root_path = Path(glob.data['root_path']).resolve()
glob.data['root_path'] = str(root_path)

# copy assets
path_remove(root_path / 'assets')
path_copy(
    src_path / 'assets',
    root_path / 'assets'
)

print(glob)
