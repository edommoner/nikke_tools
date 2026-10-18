"""Require actual raw field modifiers in a normal squad, not compile-only rows."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts')]
from detail_coverage import a
from gpu_selector import Cuda
import detail_gpu as g
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'research/enemy-fields-api-fixture.json',ROOT/'scripts/detail_coverage.py',ROOT/'app/detail_effects.cu',ROOT/'app/detail_effects-sm86.cubin',ROOT/'app/detail_effects-sm86.json']
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
body=json.loads((ROOT/'research/enemy-fields-api-fixture.json').read_text(encoding='utf-8'));body['_debug_scalar_query']={'who':0,'key':12};compiled=a.evaluate({**body,'_compile_gpu_detail':True});device=Cuda()
try:result=g.evaluate_full(device,compiled,module_backend='native')
finally:device.close()
frames=result['_scalar_frames'];positive=[row for row in frames if row['value']>0]
assert positive and result['total_damage']>0
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=True,source_sha256=before,frames=len(frames),positive_frames=len(positive),first_positive=positive[0],max_modifier=max(r['value'] for r in positive),total_damage=result['total_damage'],members=result['members'],burst_timeline=result['burst_timeline'],backend='native',scope='Actual raw enemy received-damage modifier in a normal45s squad with weapon mode enabled; not summon admission.')
(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ('passed','positive_frames','max_modifier','total_damage')}))
