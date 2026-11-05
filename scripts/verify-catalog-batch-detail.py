"""Current accepted catalog: independent whole battles, with GPU batch execution.

Each GPU input is an owned profile, effects and a common authored frame schedule.
CPU event histories and simulation states are never replayed into the kernel.
"""
import argparse,copy,hashlib,json,random,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for,coverage
import detail_gpu



if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx','both'],default='both');p.add_argument('--batch-size',type=int,default=8)
    p.add_argument('--duration',type=int,default=30);p.add_argument('--seed',type=int,default=12345);p.add_argument('--mode',choices=['fixed','accumulate'],default='fixed')
    p.add_argument('--shooting-policy',choices=['auto','character'],default='auto');p.add_argument('--character');p.add_argument('--limit',type=int);p.add_argument('--output',default='research/detail-catalog-batch-verification.json');args=p.parse_args()
    if not 1<=args.batch_size<=32 or not 1<=args.duration<=180:p.error('batch size 1..32 and duration 1..180 required')
    report=main(args);(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
