#!/usr/bin/env python3
"""Losslessly archive legacy timing buffers; restore before using raw readers."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
import portable_benchmark_storage as storage


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('inventory','migrate','status','restore'))
    p.add_argument('--storage',type=Path,required=True)
    p.add_argument('--repository',type=Path,default=ROOT)
    p.add_argument('--remove-original',action='store_true')
    p.add_argument('--workload',help='Limit pilot migration to one capture directory name')
    p.add_argument('--path',help='Repository-relative raw path to restore')
    p.add_argument('--verify',action='store_true',help='Fully decompress archives and hash retained raw')
    p.add_argument('--folder',help='Inventory one completed folder name under research/portable-build')
    p.add_argument('--report',help='Matching completed report filename under research')
    a=p.parse_args()
    with storage.locked(a.storage.resolve()):
        if a.command=='inventory':
            if bool(a.folder)!=bool(a.report):p.error('--folder and --report are required together')
            options=dict(targets=[(a.folder,a.report)]) if a.folder else {}
            m=storage.inventory(a.repository,a.storage,**options)
            result=dict(files=len(m['files']),selected=sum(r['selected'] for r in m['files']),gpu_calls=0)
        elif a.command=='migrate':result=storage.migrate(a.storage,repository=a.repository,remove_original=a.remove_original,workload=a.workload)
        elif a.command=='status':result=storage.status(a.storage,repository=a.repository,verify=a.verify)
        else:
            if not a.path:p.error('restore requires --path')
            result=storage.restore(a.storage,a.path,repository=a.repository)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
