"""Isolate the next port from the sealed v38 production implementation."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];checkpoint=ROOT/'research/detail-decoy-healing-checkpoint.json'
c=json.loads(checkpoint.read_text(encoding='utf-8'))
assert c['passed'] and c['abi']=='detail_decoy_healing_v38'
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in c['source_sha256'].items())
dest=ROOT/'research/staging/v39';assert not dest.exists(),'Never overwrite a port.'
for name in ['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']:
    s=(ROOT/name).read_text(encoding='utf-8').replace('detail_decoy_healing_v38','detail_outgoing_healing_v39').replace('detail_state_bytes_v38','detail_state_bytes_v39').replace('detail_boss_shape_v38','detail_boss_shape_v39')
    if name.endswith('detail_gpu.py'):
        s=s.replace('cover_disabled=71,decoy=72)','cover_disabled=71,decoy=72,outgoing_heal_pct=73)').replace('0<=r[2]<73','0<=r[2]<74')
    if name.endswith('.cu'):
        start=s.index('// The CPU healing query resolves only heal_received_pct carriers.')
        end=s.index('__device__ void add_burst',start)
        s=s[:start]+'''// Body healing has separate recipient/source multipliers. Resolve only the
// queried carrier stat; do not trigger unrelated lazy target selection.
__device__ void resolve_live_slot(const double*,const double*,int,State*,int,int);
__device__ double healing_stat_multiplier(const double* c,const double* e,int ne,State* s,int who,int full,int key){
 double pct=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(q[1]!=0||q[2]!=key||!s->alive[j]||s->end[j]<=s->when)continue;
  resolve_live_slot(c,e,ne,s,j,full);
  if(s->masks[j]>=0&&(s->masks[j]&(1<<who))&&base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))pct+=recipient_value(e,ne,s,j,who);
 }
 return mx(0,1+pct/100);
}
__device__ double heal_multiplier(const double* c,const double* e,int ne,State* s,int who,int full,int source){
 double received=healing_stat_multiplier(c,e,ne,s,who,full,42);
 double outgoing=healing_stat_multiplier(c,e,ne,s,source,full,73);
 return received*outgoing;
}
'''+s[end:]
        s=s.replace('heal_multiplier(c,e,ne,s,recipient,full)','heal_multiplier(c,e,ne,s,recipient,full,source)').replace('heal_multiplier(c,e,ne,s,who,full)','heal_multiplier(c,e,ne,s,who,full,who)')
    out=dest/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(s,encoding='utf-8')
(dest/'stage-base.json').write_text(json.dumps(dict(base_abi=c['abi'],base_checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),objective_complete=False,stage_verified=False),indent=2)+'\n',encoding='utf-8')
print('Isolated v39 outgoing healing; production remains v38.')
