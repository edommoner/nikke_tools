"""Two fresh, complete byte checks; no compiler, reference or GPU admission."""
import argparse,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('package_byte_benchmark_cli',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)

def benchmark(package,out):
    package=Path(package).resolve();out=Path(out).resolve()
    if out==package or package in out.parents or out.exists():raise ValueError('Use a new output outside immutable package')
    raw=(package/'gpu-package.json').read_bytes();manifest=json.loads(raw)
    if manifest.get('schema')!=cli.SCHEMA or manifest.get('package_id')!=cli.package_id(manifest):raise ValueError('Invalid package header')
    rows=[]
    with cli.forbid_gpu():
        for workers in (1,4):
            started=time.perf_counter();cli.check_records(package,manifest['files'],parallel=workers==4)
            rows.append(dict(maximum_workers=workers,elapsed_seconds=time.perf_counter()-started,all_bytes_verified=True))
    if (package/'gpu-package.json').read_bytes()!=raw:raise ValueError('Package header changed during byte checks')
    result=dict(schema='package-byte-check-benchmark-v1',package_id=manifest['package_id'],manifest_sha256=hashlib.sha256(raw).hexdigest(),
                files=len(manifest['files']),bytes=sum(r['bytes'] for r in manifest['files']),measurements=rows,
                benchmark_source_sha256=cli.sha(Path(__file__).read_bytes()),controller_sha256=cli.sha((ROOT/'scripts/nikke_gpu.py').read_bytes()),
                checksum_cache_used=False,compiler_calls=0,gpu_calls=0,native_battle_calls=0,
                full_package_verified=False,calculation_verified=False,
                scope='Fresh full byte checks only; order fixed sequential then bounded parallel; OS cache and host load may affect timings')
    with out.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(benchmark(a.package,a.out)))
