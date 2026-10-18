"""Apply only after all readers of the initial staged binaries have exited."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
archive=ROOT/'research/ports/v34-before-heal-resolution-fix'
assert not archive.exists()
base=ROOT/'research/staging/v34'
files=list(base.rglob('*'))
archive.mkdir(parents=True)
for p in files:
    if p.is_file() and '__pycache__' not in p.parts:
        out=archive/'stage'/p.relative_to(base);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
for name in ('detail-staged-survival-initial-quick.json','detail-staged-survival-initial-full.json','detail-staged-survival-initial-ptx.json','detail-staged-survival-initial-regression.json','detail-staged-survival-heal-before.json','detail-staged-survival-heal-cpu-witness.json'):
    src=ROOT/'research'/name
    assert src.exists(),name
    shutil.copy2(src,archive/name)
path=base/'app/detail_effects.cu'
old=path.read_text(encoding='utf-8')
start=old.index('// Healing uses recipient-only live buffs')
end=old.index('__device__ void health_activation',start)
new='''// The CPU healing query resolves only heal_received_pct carriers. These are
// outside the generic damage-stat resolver and must resolve at first heal query.
__device__ void resolve_live_slot(const double*,const double*,int,State*,int,int);
__device__ double heal_multiplier(const double* c,const double* e,int ne,State* s,int who,int full){
 double pct=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(q[1]!=0||q[2]!=42||!s->alive[j]||s->end[j]<=s->when)continue;
  resolve_live_slot(c,e,ne,s,j,full);
  if(s->masks[j]>=0&&(s->masks[j]&(1<<who))&&base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))pct+=recipient_value(e,ne,s,j,who);
 }
 return mx(0,1+pct/100);
}
'''
path.write_text(old[:start]+new+old[end:],encoding='utf-8')
manifest={str(p.relative_to(archive)):hashlib.sha256(p.read_bytes()).hexdigest() for p in archive.rglob('*') if p.is_file()}
(archive/'manifest.json').write_text(json.dumps(dict(objective_complete=False,files=manifest),indent=2)+'\n',encoding='utf-8')
print('Archived initial stage and patched staged heal-stat resolution; rebuild required.')
