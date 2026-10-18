"""Match special ATK target draws to complete per-recipient CPU buff queries."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'app/detail_gpu.py';s=p.read_text(encoding='utf-8')
a="q[207]=int(stat in _STAT_TO_BUFF or stat=='atk_caster_based_pct')"
b="q[207]=int(stat in _STAT_TO_BUFF or stat=='atk_caster_based_pct' and eff.get('target','self') not in tuple('allies_random:'+str(n) for n in range(6)))"
assert a in s;s=s.replace(a,b);p.write_text(s,encoding='utf-8')
p=ROOT/'app/detail_effects.cu';s=p.read_text(encoding='utf-8')
s=s.replace(' MTState rng;int random_error,',' int random_special_valid[5],random_special_mask[5][NS];\n MTState rng;int random_error,')
s=s.replace('s->valid[i]=0;s->query_camera_at[i]=-1;','s->valid[i]=0;s->random_special_valid[i]=0;s->query_camera_at[i]=-1;')
a='__device__ double stat(const double* c,const double* e,int ne,State* s,int who,int key,int full){'
b='''__device__ int random_target(const double*,State*,const double*,Order*);
__device__ void random_special_query(const double* e,State* s,int who){
 if(s->random_special_valid[who])return;
 for(int pass=0;pass<2;pass++)for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(!s->alive[j]||s->end[j]<=s->when||s->masks[j]>=0||q[4]!=19||!(pass==0?q[241]>0:q[1]==0&&q[2]==26))continue;
  s->random_special_mask[who][j]=random_target(e,s,q,0);
 }
 s->random_special_valid[who]=1;
}
'''+a
assert a in s;s=s.replace(a,b)
a=' camera_query(s,who);int previous_lens=s->camera_lens;'
b=' camera_query(s,who);random_special_query(e,s,who);int previous_lens=s->camera_lens;'
# Only stat() computes a complete buff query; quant() already calls stat() when needed.
assert a in s;s=s.replace(a,b,1)
a='if(!(special_target(c,e,ne,s,j,full)&(1<<who))||!base_condition'
b='if(!((s->masks[j]<0&&q[4]==19?s->random_special_mask[who][j]:special_target(c,e,ne,s,j,full))&(1<<who))||!base_condition'
assert a in s;s=s.replace(a,b)
p.write_text(s,encoding='utf-8');print('Per-query random special targets prepared; new builds/parity required.')
