"""One-shot v24 assembly from v23. Never overwrites an existing archive."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']
texts={f:(ROOT/f).read_text(encoding='utf-8') for f in files}
assert "DETAIL_ABI='detail_immunity_v23'" in texts['app/detail_gpu.py']
archive=ROOT/'research/ports/v23';archive.mkdir(exist_ok=True)
for f,t in texts.items():
    dest=archive/Path(f).name;assert not dest.exists(),dest;dest.write_text(t,encoding='utf-8')
for name in ['detail-normal-acceptance.json','detail-normal-acceptance.log']:
    (archive/name).write_bytes((ROOT/'research'/name).read_bytes())
def replace(t,old,new):
    assert t.count(old)==1,(old[:100],t.count(old));return t.replace(old,new)
host=texts['app/detail_gpu.py'].replace('detail_immunity_v23','detail_charge_immunity_v24').replace('detail_state_bytes_v23','detail_state_bytes_v24')
anchor="   elif kind=='buff' and stat=='debuff_immune_count':q[1]=4;q[262]=3"
host=replace(host,anchor,anchor+"\n   elif kind=='buff' and stat in ('charge_speed_buff_immune','charge_speed_debuff_immune'):q[1]=4;q[213]=8 if stat=='charge_speed_buff_immune' else 16\n   elif kind=='buff' and stat=='charge_speed_overflow_conversion_pct':q[1]=4;q[213]=64")
host=replace(host,"   group=(caster,eff.get('_source_tag'),eff.get('_quant_group') or len(rows))", "   if eff.get('_source_tag') in ('equipment','cube'):q[213]=int(q[213])|32\n   group=(caster,eff.get('_source_tag'),eff.get('_quant_group') or len(rows))")
anchor="   if r[4]==17:"
host=replace(host,anchor,"   if r[1]==0 and r[2] in (20,37) and (int(r[45])!=r[45] or not 0<=r[45]<NE):raise ValueError('Invalid charge quantization group')\n"+anchor)
cu=texts['app/detail_effects.cu'].replace('detail_immunity_v23','detail_charge_immunity_v24').replace('detail_state_bytes_v23','detail_state_bytes_v24')
cu=replace(cu,'__device__ double stat(', (ROOT/'research/ports/charge_immunity.cu.inc').read_text(encoding='utf-8')+'\n__device__ double stat(')
anchor=' double out=key==5||key==24?.15:0;'
cu=replace(cu,anchor,' if(key==20){double value=charge_speed_total(c,e,ne,s,who,full);s->cached[who][key]=value;s->valid[who]|=1ULL<<key;s->camera_lens=previous_lens;return value;}\n'+anchor)
anchor=' s->cached[who][key]=out;'
cu=replace(cu,anchor,' if(key==8){double conv=charge_overflow_coefficient(c,e,ne,s,who,full);if(conv>0){double overflow=mx(0,charge_speed_total(c,e,ne,s,who,full)-100);if(overflow>0)out+=overflow*conv/100;}}\n'+anchor)
anchor=' camera_query(s,who);int previous_lens=s->camera_lens;s->camera_lens=s->query_camera[who];\n for(int j=s->slot_head;'
cu=replace(cu,anchor,' camera_query(s,who);int previous_lens=s->camera_lens;s->camera_lens=s->query_camera[who];\n if(key==20){double values[NE];int blocked[NE],n=charge_groups(c,e,ne,s,who,full,values,blocked);for(int i=0;i<n;i++)if(!blocked[i])out+=floor(base*(values[i]/100)/step+.5)*step;s->camera_lens=previous_lens;return out;}\n for(int j=s->slot_head;')
(ROOT/'app/detail_gpu.py').write_text(host,encoding='utf-8');(ROOT/'app/detail_effects.cu').write_text(cu,encoding='utf-8')
for f in files[2:]:(ROOT/f).write_text(texts[f].replace('detail_immunity_v23','detail_charge_immunity_v24'),encoding='utf-8')
print('Prepared v24 charge immunity and overflow conversion source')
