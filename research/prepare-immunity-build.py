"""One-shot v23 assembly. Archives v22; never run again over a newer version."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']
archive=ROOT/'research/ports/v22';archive.mkdir(exist_ok=True)
texts={f:(ROOT/f).read_text(encoding='utf-8') for f in files}
assert "DETAIL_ABI='detail_shields_v22'" in texts['app/detail_gpu.py'],'Not the v22 baseline'
for f,t in texts.items():
    dest=archive/Path(f).name
    assert not dest.exists(),'Archive already exists; do not overwrite'
    dest.write_text(t,encoding='utf-8')
def replace(t,old,new):
    assert t.count(old)==1,(old[:100],t.count(old))
    return t.replace(old,new)
host=texts['app/detail_gpu.py'].replace('detail_shields_v22','detail_immunity_v23').replace('detail_state_bytes_v22','detail_state_bytes_v23')
anchor="   elif kind=='buff' and stat=='shield_invincible':q[1]=4;q[213]=4"
host=replace(host,anchor,anchor+"\n   elif kind=='buff' and stat=='debuff_immune':q[1]=4;q[262]=1\n   elif kind=='buff' and isinstance(stat,str) and stat.startswith('debuff_immune:'):q[1]=4;q[262]=2;q[263]=state(stat.split(':',1)[1])\n   elif kind=='buff' and stat=='debuff_immune_count':q[1]=4;q[262]=3")
anchor=" if any(row[1]==2 and row[2]==111 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid shield state query')"
host=replace(host,anchor,anchor+"\n if any(row[1]==2 and row[2]==112 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid immunity pool query')")
cu=texts['app/detail_effects.cu'].replace('detail_shields_v22','detail_immunity_v23').replace('detail_state_bytes_v22','detail_state_bytes_v23')
cu=replace(cu,'struct State {','struct State {\n double immune_used[6][NE];')
cu=replace(cu,'__device__ int end_shield(', (ROOT/'research/ports/debuff_immunity.cu.inc').read_text(encoding='utf-8')+'\n__device__ int end_shield(')
cu=replace(cu,'int post_row[32],post_phase[32]','int post_immune_name[32],post_immune_mask[32];int post_row[32],post_phase[32]')
cu=replace(cu,'  int rawmask=mask;Order raworder=activation_order;',
    '  if(q[209]==2&&mask>=0){mask=filter_harmful(e,ne,s,q,&activation_order);if(!mask)continue;}\n  int rawmask=mask;Order raworder=activation_order;')
cu=replace(cu,'  post_row[depth]=j;post_phase[depth]=0;',
    '  post_immune_name[depth]=q[262]==3?(int)q[3]:-1;post_immune_mask[depth]=rawmask;\n  post_row[depth]=j;post_phase[depth]=0;')
cu=replace(cu,'   if(phase>=5){r=first_instance',
    '   if(phase>=5&&post_immune_name[depth]>=0&&post_immune_mask[depth]>0){for(int who=0;who<6;who++)if(post_immune_mask[depth]&(1<<who))s->immune_used[who][post_immune_name[depth]]=0;}\n   if(phase>=5){r=first_instance')
cu=replace(cu,' status[id]=0;', ' for(int who=0;who<6;who++)for(int key=0;key<NE;key++)s->immune_used[who][key]=0;\n status[id]=0;')
cu=replace(cu,'   if(ev==111){',
    '   if(ev==112){for(int k=0;k<OW;k++)dst[k]=0;for(int who=0;who<6;who++){if(arg>=0)dst[who]=s->immune_used[who][arg];else for(int key=0;key<NE;key++)dst[who]+=s->immune_used[who][key];}continue;}\n   if(ev==111){')
(ROOT/'app/detail_gpu.py').write_text(host,encoding='utf-8')
(ROOT/'app/detail_effects.cu').write_text(cu,encoding='utf-8')
for f in files[2:]:(ROOT/f).write_text(texts[f].replace('detail_shields_v22','detail_immunity_v23'),encoding='utf-8')
print('Prepared v23 immunity source; build PTX then native sequentially')
