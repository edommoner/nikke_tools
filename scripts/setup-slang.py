"""Workspace-only pinned Slang compiler; leaves the existing CUDA toolchain intact."""
import argparse,hashlib,json,platform,shutil,subprocess,tarfile,tempfile,urllib.request,zipfile
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
VERSION='2026.20'
ASSETS={
    ('Windows','AMD64'):('windows-x86_64.zip','e6dd32bbddf1720ebb4e679d55e9635ce792865a5bd84f3d2cd9af28647c0174'),
    ('Darwin','arm64'):('macos-aarch64.tar.gz','07fa8833fdbb343c3674c84fdd885910f495f3daaaa0c732b32980151e8b58c4'),
    ('Darwin','x86_64'):('macos-x86_64.tar.gz','b4f01f615dc625f60c593d7d0a4bbd38e05dfa2a34bfd3973017c309d866feaa'),
}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path);args=ap.parse_args()
    key=(platform.system(),platform.machine())
    if key not in ASSETS:ap.error(f'No pinned compiler package for {key}')
    suffix,digest=ASSETS[key]
    base=(ROOT/'.tools').resolve();base.mkdir(exist_ok=True);target=base/f'slang-{VERSION}-{key[0]}-{key[1]}'
    executable=target/'bin'/('slangc.exe' if key[0]=='Windows' else 'slangc')
    if not executable.is_file():
        if target.exists():raise RuntimeError(f'Incomplete compiler directory: {target}')
        with tempfile.TemporaryDirectory(prefix='slang-',dir=base) as directory:
            stage=Path(directory).resolve();assert stage.is_relative_to(base)
            archive=stage/('package.zip' if suffix.endswith('.zip') else 'package.tar.gz')
            if args.archive:shutil.copyfile(args.archive,archive)
            else:
                url=f'https://github.com/shader-slang/slang/releases/download/v{VERSION}/slang-{VERSION}-{suffix}'
                with urllib.request.urlopen(url,timeout=60) as source,archive.open('wb') as output:shutil.copyfileobj(source,output)
            if hashlib.sha256(archive.read_bytes()).hexdigest()!=digest:raise ValueError('Slang archive digest mismatch')
            unpack=stage/'unpack';unpack.mkdir()
            if suffix.endswith('.zip'):
                with zipfile.ZipFile(archive) as package:
                    for entry in package.infolist():
                        p=PurePosixPath(entry.filename)
                        if p.is_absolute() or '..' in p.parts or '\\' in entry.filename:raise ValueError('Unexpected compiler archive path')
                    package.extractall(unpack)
            else:
                with tarfile.open(archive) as package:package.extractall(unpack,filter='data')
            if not (unpack/'bin'/executable.name).is_file():raise ValueError('Compiler package has an unexpected layout')
            assert unpack.resolve().is_relative_to(base) and target.resolve().is_relative_to(base)
            unpack.rename(target)
    result=subprocess.run([str(executable),'-version'],capture_output=True,text=True,check=True)
    print(json.dumps(dict(compiler=str(executable),version=(result.stdout+result.stderr).strip(),archive_sha256=digest)))


if __name__=='__main__':main()
