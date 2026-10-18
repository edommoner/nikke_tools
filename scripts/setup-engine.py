"""Install the pinned reference engine on Windows, macOS or Linux (stdlib only)."""
import argparse,json,shutil,tempfile,urllib.request,zipfile
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
REVISION='23164e4a88fe46af609cc99b0de38a98313a5f4d'
PREFIX=f'nikke-calc-{REVISION}'
REQUIRED=('runner/sim.py','data/parsed_nikke.json')


def validate_archive(archive):
    if archive.comment.decode('ascii')!=REVISION:raise ValueError('Engine revision verification failed')
    names=set(archive.namelist())
    prefix=PurePosixPath(archive.namelist()[0]).parts[0] if names else ''
    if prefix not in (PREFIX,'nikke-calc-master'):raise ValueError('Unexpected engine archive root')
    for entry in archive.infolist():
        path=PurePosixPath(entry.filename)
        if '\\' in entry.filename or path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!=prefix or (entry.external_attr>>16)&0o170000==0o120000:
            raise ValueError('Unexpected engine archive path')
    if not all(f'{prefix}/{p}' in names for p in REQUIRED):raise ValueError('Incomplete engine archive')
    return prefix


def setup(root=ROOT,archive_path=None):
    base=(Path(root)/'research/upstream').resolve();engine=base/'nikke-calc-master'
    if all((engine/p).is_file() for p in REQUIRED):return dict(engine=str(engine),already_present=True,revision=REVISION)
    if engine.exists():raise ValueError('Existing engine directory is incomplete; preserve it and inspect before reinstalling')
    base.mkdir(parents=True,exist_ok=True)
    # Own a temporary directory inside the checked destination. No existing
    # engine or user data is recursively removed or overwritten.
    with tempfile.TemporaryDirectory(prefix='setup-engine-',dir=base) as staging:
        stage=Path(staging).resolve();assert stage.is_relative_to(base)
        download=stage/'engine.zip'
        if archive_path is None:
            with urllib.request.urlopen(f'https://codeload.github.com/Jgaram/nikke-calc/zip/{REVISION}',timeout=60) as source,download.open('wb') as target:shutil.copyfileobj(source,target)
        else:shutil.copyfile(archive_path,download)
        with zipfile.ZipFile(download) as archive:
            archive_root=validate_archive(archive);archive.extractall(stage)
        extracted=(stage/archive_root).resolve();assert extracted.is_relative_to(base) and engine.resolve().is_relative_to(base)
        extracted.rename(engine)
    return dict(engine=str(engine),already_present=False,revision=REVISION)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,help='Use a previously downloaded pinned codeload ZIP');args=ap.parse_args()
    print(json.dumps(setup(archive_path=args.archive)))
