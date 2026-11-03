"""Archive-derived engine identities shared by installation and product startup."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PINNED_REVISION='67835ca3033a95482749ea2db35a8ee2a0856a92'
HISTORICAL_REVISION='23164e4a88fe46af609cc99b0de38a98313a5f4d'
MANIFEST_SHA256='8e8b32e8d9a77d0b6794dcad50ae89ec73a2d60ef05d56513b1220436bc02f17'
_raw=(ROOT/'data/engine-revisions.json').read_bytes()
if hashlib.sha256(_raw).hexdigest()!=MANIFEST_SHA256:
    raise ValueError('Pinned engine identity manifest changed')
REVISIONS=json.loads(_raw)['revisions']


def verify_runtime(engine,revision=PINNED_REVISION):
    """Hash every executable/data dependency before importing or evaluating it."""
    engine=Path(engine)
    if engine.is_symlink() or not engine.is_dir():
        raise ValueError('Pinned reference engine missing or unsafe: '+str(engine))
    record=REVISIONS[revision]
    for name in record['required']:
        path=engine/name
        # A linked parent could otherwise escape the checked installation.
        if path.is_symlink() or any((engine/p).is_symlink() for p in Path(name).parents):
            raise ValueError('Pinned reference engine contains a symbolic link: '+name)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=record['files'][name]:
            raise ValueError('Pinned reference engine revision mismatch: expected '+revision+'; missing or modified '+name+'; run scripts/setup-engine.py')
    return revision


def verify_tree(engine,revision):
    """Recognize full archives or frozen runtime subsets, rejecting local edits."""
    engine=Path(engine)
    verify_runtime(engine,revision)
    approved=REVISIONS[revision]['files']
    directories={str(parent) for name in approved for parent in Path(name).parents if str(parent)!='.'}
    for path in engine.rglob('*'):
        relative=path.relative_to(engine)
        if path.is_symlink():raise ValueError('Unknown or modified engine tree: symbolic link '+str(relative))
        if '__pycache__' in relative.parts:continue
        # Finder/Explorer metadata is not upstream source or executable data.
        if path.is_file() and (path.name in ('.DS_Store','Thumbs.db','desktop.ini') or path.name.startswith('._')):continue
        if path.is_dir():
            if relative.as_posix() not in directories:raise ValueError('Unknown engine directory: '+str(relative))
        elif not path.is_file() or relative.as_posix() not in approved or hashlib.sha256(path.read_bytes()).hexdigest()!=approved[relative.as_posix()]:
            raise ValueError('Unknown or modified engine file: '+str(relative))
    return revision


def identify(engine):
    failures=[]
    for revision in (PINNED_REVISION,HISTORICAL_REVISION):
        try:return verify_tree(engine,revision)
        except (ValueError,OSError) as error:failures.append(str(error))
    raise ValueError('Unknown or modified installed reference engine; preserved without changes. '+ '; '.join(failures))
