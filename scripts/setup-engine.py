"""Install/upgrade pinned reference engines without discarding an existing tree."""
import argparse,hashlib,json,shutil,sys,tempfile,urllib.request,zipfile
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
import engine_revision as pins
REVISION='67835ca3033a95482749ea2db35a8ee2a0856a92'
HISTORICAL_REVISION=pins.HISTORICAL_REVISION
PREFIX=f'nikke-calc-{REVISION}'
REQUIRED=('runner/sim.py','data/parsed_nikke.json')
assert REVISION==pins.PINNED_REVISION


def validate_archive(archive,revision=REVISION):
    if archive.comment.decode('ascii')!=revision:raise ValueError('Engine revision verification failed')
    entries=archive.infolist();names=[entry.filename for entry in entries]
    prefix=PurePosixPath(names[0]).parts[0] if names and PurePosixPath(names[0]).parts else ''
    if prefix not in (f'nikke-calc-{revision}','nikke-calc-master'):raise ValueError('Unexpected engine archive root')
    approved=pins.REVISIONS[revision];seen=set();files=set()
    for entry in entries:
        path=PurePosixPath(entry.filename)
        if '\\' in entry.filename or path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!=prefix or (entry.external_attr>>16)&0o170000==0o120000 or entry.filename in seen:
            raise ValueError('Unexpected engine archive path')
        seen.add(entry.filename)
        if entry.is_dir():continue
        relative=path.relative_to(prefix).as_posix()
        if relative not in approved['files'] or hashlib.sha256(archive.read(entry)).hexdigest()!=approved['files'][relative]:
            raise ValueError('Pinned engine archive bytes differ: '+relative)
        files.add(relative)
    if not set((*REQUIRED,*approved['required']))<=files:raise ValueError('Incomplete engine archive')
    return prefix


def _install(root,revision,archive_path,destination):
    root=Path(root).resolve();base=root/'research/upstream';engine=base/destination
    if not base.resolve().is_relative_to(root):raise ValueError('Engine destination escapes checkout')
    old_revision=None;backup=None
    if engine.exists() or engine.is_symlink():
        old_revision=pins.identify(engine)
        if old_revision==revision:return dict(engine=str(engine),already_present=True,revision=revision)
        if destination!='nikke-calc-master':raise ValueError('Historical engine destination has a different revision; preserved without changes')
        backup=base/f'nikke-calc-{old_revision[:7]}'
        if backup.exists() or backup.is_symlink():raise ValueError('Preserved engine destination already exists; neither tree was changed: '+str(backup))
    base.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='setup-engine-',dir=base) as staging:
        stage=Path(staging);download=stage/'engine.zip'
        if archive_path is None:
            with urllib.request.urlopen(f'https://codeload.github.com/Jgaram/nikke-calc/zip/{revision}',timeout=60) as source,download.open('wb') as target:shutil.copyfileobj(source,target)
        else:shutil.copyfile(archive_path,download)
        # Verify the entire archive before touching the installed reference.
        with zipfile.ZipFile(download) as archive:
            archive_root=validate_archive(archive,revision);archive.extractall(stage)
        extracted=stage/archive_root
        pins.verify_tree(extracted,revision)
        if old_revision is not None:
            pins.verify_tree(engine,old_revision)
            if backup.exists() or backup.is_symlink():raise ValueError('Preserved engine destination appeared during setup')
            engine.rename(backup)
        try:
            if engine.exists() or engine.is_symlink():raise ValueError('Engine destination appeared during setup')
            extracted.rename(engine)
        except BaseException:
            # Restore the original path if publication failed and it is empty.
            # Never overwrite another tree or remove a preserved installation.
            if backup is not None and not engine.exists() and not engine.is_symlink():backup.rename(engine)
            raise
    result=dict(engine=str(engine),already_present=False,revision=revision)
    if backup is not None:result['preserved_engine']=str(backup)
    return result


def setup(root=ROOT,archive_path=None,*,historical=False,historical_archive_path=None):
    if historical_archive_path is not None and not historical:raise ValueError('--historical-archive requires --historical')
    result=_install(root,REVISION,archive_path,'nikke-calc-master')
    if historical:result['historical']=_install(root,HISTORICAL_REVISION,historical_archive_path,'nikke-calc-'+HISTORICAL_REVISION[:7])
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--archive',type=Path,help='Use a local pinned 67835ca3 ZIP')
    ap.add_argument('--historical',action='store_true',help='Also install preserved 23164e4 for historical tests')
    ap.add_argument('--historical-archive',type=Path,help='Use a local pinned 23164e4 ZIP (requires --historical)')
    args=ap.parse_args()
    if args.historical_archive is not None and not args.historical:ap.error('--historical-archive requires --historical')
    print(json.dumps(setup(archive_path=args.archive,historical=args.historical,historical_archive_path=args.historical_archive)))
