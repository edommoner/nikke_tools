"""Run S22 acceptance with receipts and a process-group storage floor guard."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import truth_s22 as truth


def main(out,tag=''):
    root=truth.HERE.parents[1]
    env=dict(os.environ,PYTHONPATH=str(out.parent.parent/'pin-update-v1/validation-deps'),
        NIKKE_SLANG_ROOT=str(root.parents[1]/'.tools/slang-2026.20-Darwin-arm64'),
        PYTHONDONTWRITEBYTECODE='1')
    commands=[('focused',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_team_search_s22.py']),
              ('python',[sys.executable,'-m','unittest','discover','-s','tests']),
              ('node',['node','--test',*map(str,sorted((root/'tests').glob('*.test.mjs')))])]
    records=[]
    for label,command in commands:
        if (out/'STORAGE_STOP.json').exists():raise RuntimeError('Storage stop recorded')
        started=time.perf_counter();minimum=shutil.disk_usage(out).free
        with (out/f'validation-{tag}{label}.log').open('x') as log:
            proc=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            while proc.poll() is None:
                free=shutil.disk_usage(out).free;minimum=min(minimum,free)
                if free<truth.RESERVE:
                    os.killpg(proc.pid,signal.SIGTERM)
                    truth.save(out/'STORAGE_STOP.json',dict(free_bytes=free,job=label,time=time.time()))
                    proc.wait()
                    raise RuntimeError('Stopped acceptance process group below 20.5 GiB')
                time.sleep(1)
        records.append(dict(label=label,command=command,exit=proc.returncode,seconds=time.perf_counter()-started,
                            minimum_free_bytes=minimum,env={k:env[k] for k in ('PYTHONPATH','NIKKE_SLANG_ROOT','PYTHONDONTWRITEBYTECODE')}))
        truth.save(out/f'validation{("-"+tag.rstrip("-")) if tag else ""}.json',records);print(records[-1],flush=True)
        if label=='focused' and records[-1]['seconds']>30:raise RuntimeError('Focused tests exceeded 30 s')
    if any(r['exit'] for r in records):raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=truth.previous.DEFAULT/'s22')
    parser.add_argument('--tag',default='')
    args=parser.parse_args();main(args.out,args.tag)
