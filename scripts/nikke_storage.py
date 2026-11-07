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
    a=sub.add_parser('reclaim-project',help='Plan or reclaim zero blocks in old evidence-anchored raw buffers (Darwin)')
    a.add_argument('--repository',type=Path,default=ROOT)
    a.add_argument('--storage',type=Path,required=True,help='External receipt directory; use a fresh directory to apply a plan')
    a.add_argument('--apply',action='store_true',help='Reclaim allocation; default only scans and writes planning receipts')
    a.add_argument('--limit',type=int)
    for name in ('benchmark-inventory','archive-benchmarks','benchmark-status','restore-benchmark'):
        a=sub.add_parser(name,help={'benchmark-inventory':'Inventory completed timing captures',
            'archive-benchmarks':'Plan lossless timing archives; --apply writes bundles',
            'benchmark-status':'Check benchmark archives and preserved evidence',
            'restore-benchmark':'Restore an inventoried raw path without overwriting'}[name])
        a.add_argument('--storage',type=Path,required=True)
        a.add_argument('--repository',type=Path,default=ROOT)
        if name=='benchmark-inventory':
            a.add_argument('--folder',help='Completed folder under research/portable-build')
            a.add_argument('--report',help='Matching completed report filename under research')
        elif name=='archive-benchmarks':
            a.add_argument('--apply',action='store_true',help='Write archives and test restoration (default: read-only plan)')
            a.add_argument('--remove-original',action='store_true',help='With --apply, remove verified timing originals after a real restore test')
            a.add_argument('--workload',help='Limit to one capture directory name')
        elif name=='benchmark-status':a.add_argument('--verify',action='store_true',help='Fully decompress archives and hash retained raw')
        else:a.add_argument('--path',required=True,help='Repository-relative inventoried raw path')
    # Keep main's capacity floor and exit status; add optional archive integrity gates.
    budget=sub.choices['storage-check']
    budget.add_argument('--storage',type=Path)
    budget.add_argument('--verify',action='store_true')
    budget.add_argument('--require-archived',action='store_true')
    a=p.parse_args()
    if a.command=='reclaim-project' and a.limit is not None and a.limit<1:p.error('--limit must be positive')
    if a.command=='benchmark-inventory' and bool(a.folder)!=bool(a.report):p.error('--folder and --report are required together')
    if a.command=='archive-benchmarks' and a.remove_original and not a.apply:p.error('--remove-original requires --apply')
    from portable_capture_storage import space_status,archive_raw,restore_raw
    if a.command=='storage-check':
        from portable_benchmark_storage import storage_check
        result=storage_check(a.path,needed=a.required_bytes,reserve=max(a.reserve_bytes,20*1024**3),storage=a.storage,verify=a.verify,require_archived=a.require_archived)
    elif a.command=='reclaim-project':
        from portable_project_storage import sweep
        result=sweep(a.repository,a.storage,apply=a.apply,limit=a.limit)
    elif a.command in ('benchmark-inventory','archive-benchmarks','benchmark-status','restore-benchmark'):
        import portable_benchmark_storage as storage
        with storage.locked(a.storage.resolve()):
            if a.command=='benchmark-inventory':
                options=dict(targets=[(a.folder,a.report)]) if a.folder else {}
                manifest=storage.inventory(a.repository,a.storage,**options)
                result=dict(files=len(manifest['files']),selected=sum(r['selected'] for r in manifest['files']),gpu_calls=0)
            elif a.command=='archive-benchmarks':
                if a.apply:result=storage.migrate(a.storage,repository=a.repository,remove_original=a.remove_original,workload=a.workload)
                else:result=storage.plan(a.storage,repository=a.repository,workload=a.workload)
            elif a.command=='benchmark-status':result=storage.status(a.storage,repository=a.repository,verify=a.verify)
            else:result=storage.restore(a.storage,a.path,repository=a.repository)
    elif a.command=='archive-raw':result=archive_raw(a.capture,a.archive,check_records,remove_original=a.remove_original)
    elif a.command=='restore-raw':result=restore_raw(a.capture,a.archive,check_records)
    else:
        from portable_sparse_raw import sparsify_raw
        result=sparsify_raw(a.capture,a.out,check_records,apply=a.apply,block_size=a.block_size)
    print(json.dumps(result,indent=2))
    if result.get('passed') is False:raise SystemExit(2)
if __name__=='__main__':main()
