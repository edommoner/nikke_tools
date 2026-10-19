"""Exact production packed notice queue, shared CUDA/Metal capacity proof."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_backend import execute
from portable_specs import LIMITS as L
p=argparse.ArgumentParser();p.add_argument('--backend',choices=('metal','cuda'),default='metal');a=p.parse_args()
packed=struct.pack('<21I',5,*[v for i in range(5) for v in (i,0,0,0)])
raw,evidence=execute('gpu/removal_queue_probe.slang','removalQueueProbe',packed,4,L['OUTPUT_WORDS'],a.backend)
rows=[]
for mode in range(5):
 expected=[(i%256)*8+i%5 for i in range(512) for _ in range(8)] if mode<=1 else [2044,0] if mode==4 else []
 base=mode*L['OUTPUT_WORDS']*4;header=struct.unpack_from('<5I',raw,base)
 assert list(header)==[64 if mode in (1,3) else 0,len(expected),sum(expected),expected[0] if expected else 0,expected[-1] if expected else 0],(mode,header)
 at=base+L['REMOVAL_QUEUE_BASE']*4;contents=raw[at:at+L['REMOVALS']*2]
 canonical=struct.pack('<'+str(len(expected))+'H',*expected)+bytes((L['REMOVALS']-len(expected))*2)
 assert contents==canonical,mode
 rows.append(dict(mode=mode,passed=True,status=header[0],notices=header[1]))
report=dict(passed=True,scope='Production notice functions, 4096 capacity, 4097 atomic rejection, missing names, repeat bounds and both packed halves; not full event runtime certification',cases=rows,**evidence)
(ROOT/f'research/portable-removal-queue-{a.backend}.json').write_text(json.dumps(report,indent=2)+'\n');print('Production notice queue capacity/transport passed',a.backend,flush=True)
