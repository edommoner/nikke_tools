"""CPU-only storage budgeting and lossless raw maintenance."""
import argparse,json,stat,sys
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def safe_name(name):
    p = PurePosixPath(name)
    if not name or '\\' in name or ':' in name or p.is_absolute() or any(x in ('', '.', '..') for x in name.split('/')):
        raise ValueError('Unsafe artifact path')
    return name

def file_records(root, names):
    records = []
    for name in sorted(names):
        safe_name(name)
        p = root/name
        try:info=p.lstat()
        except OSError as error:raise ValueError('Expected regular artifact: '+name) from error
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('Expected regular artifact: '+name)
        from portable_capture_storage import file_digest
        records.append(dict(path=name, bytes=info.st_size, sha256=file_digest(p)))
    return records

def _check_records_fresh(root, records, *, parallel=False):
    names = [safe_name(r['path']) for r in records]
    if len(names) != len(set(names)):
        raise ValueError('Artifact bytes/SHA/size mismatch')
    if parallel and len(names)>=128:
        # Windows per-file open latency dominates immutable payload checks.
        # Read every byte again at every gate; no metadata or digest cache.
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as readers:
            actual=list(readers.map(lambda name:file_records(root,[name])[0],sorted(names)))
    else:actual=file_records(root,names)
    if actual != sorted(records, key=lambda r:r['path']):
        raise ValueError('Artifact bytes/SHA/size mismatch')

check_records=_check_records_fresh

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('storage-check');a.add_argument('--path',type=Path,default=ROOT);a.add_argument('--required-bytes',type=int,default=0);a.add_argument('--reserve-bytes',type=int,default=20*1024**3)
    a=sub.add_parser('sparsify-raw');a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--apply',action='store_true');a.add_argument('--block-size',type=int,choices=(4096,65536),default=65536)
    for name in ('archive-raw','restore-raw'):
        a=sub.add_parser(name);a.add_argument('--capture',type=Path,required=True);a.add_argument('--archive',type=Path,required=True)
        if name=='archive-raw':a.add_argument('--remove-original',action='store_true')
    a=p.parse_args()
    from portable_capture_storage import space_status,archive_raw,restore_raw
    if a.command=='storage-check':result=space_status(a.path,a.required_bytes,reserve=max(a.reserve_bytes,20*1024**3))
    elif a.command=='archive-raw':result=archive_raw(a.capture,a.archive,check_records,remove_original=a.remove_original)
    elif a.command=='restore-raw':result=restore_raw(a.capture,a.archive,check_records)
    else:
        from portable_sparse_raw import sparsify_raw
        result=sparsify_raw(a.capture,a.out,check_records,apply=a.apply,block_size=a.block_size)
    print(json.dumps(result,indent=2))
    if result.get('passed') is False:raise SystemExit(2)
if __name__=='__main__':main()
