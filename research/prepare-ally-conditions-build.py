"""One-shot v26 to v27 source transition; retain the verified v26 artifacts."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']
texts={f:(ROOT/f).read_text(encoding='utf-8') for f in files}
assert "DETAIL_ABI='detail_live_parts_v26'" in texts[files[0]]
archive=ROOT/'research/ports/v26';archive.mkdir(exist_ok=True)
for f in files+['app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','research/detail-normal-acceptance.json','research/detail-owned-acceptance.json','research/detail-owned-current-summary.json']:
    dest=archive/Path(f).name
    if dest.exists():assert dest.read_bytes()==(ROOT/f).read_bytes(),dest
    else:dest.write_bytes((ROOT/f).read_bytes())

def rep(text,old,new):
    assert text.count(old)==1,(old[:80],text.count(old))
    return text.replace(old,new)

host=texts[files[0]].replace('detail_live_parts_v26','detail_ally_conditions_v27').replace('detail_state_bytes_v26','detail_state_bytes_v27')
host=rep(host,"    elif condition=='self_hp_max':typ=11", "    elif condition.startswith('ally_hp_below:'):\n     typ=34;arg=float(condition.split(':')[1])\n     if not math.isfinite(arg):raise UnsupportedDetail('invalid ally HP threshold')\n    elif condition=='self_hp_max':typ=11")
host=rep(host,"    elif condition=='squad_ally_exists':", "    elif condition in ('has_defender_ally','no_defender_ally'):\n     from calculator.buff_manager import _NIKKE\n     has=any(n!=caster and _NIKKE.get(n,{}).get('class')=='방어형' for n in names)\n     typ=25;arg=int(has==(condition=='has_defender_ally'))\n    elif condition=='squad_ally_exists':")
cu=texts[files[1]].replace('detail_live_parts_v26','detail_ally_conditions_v27').replace('detail_state_bytes_v26','detail_state_bytes_v27')
cu=rep(cu,'int first=0,int limit=3);','int first=0,int limit=3,int query=-1);')
cu=rep(cu,'int first,int limit){','int first,int limit,int query){')
cu=rep(cu,'&&type!=29&&type!=30)))continue;','&&type!=29&&type!=30&&type!=34)))continue;')
anchor='  if(type==29&&!s->charging[owner]'
assert cu.count(anchor)==1
cu=cu.replace(anchor,'''  if(type==34){
   if(runtime){int recipient=query>=0?query:owner;if(slot>=0&&!(s->masks[slot]&(1<<recipient)))recipient=5;if((recipient<5?s->hppct[recipient]:100.0)>arg)return 0;}
   else{double lowest=100;for(int k=0;k<5;k++)lowest=mn(lowest,s->hppct[k]);if(lowest>arg)return 0;}
  }
'''+anchor)
# All recipient stat readers explicitly identify the actual queried ally.
assert cu.count('full,1,j)')==9
cu=cu.replace('full,1,j)','full,1,j,0,0,0,3,who)')
cu=rep(cu,'!condition(c,e,ne,s,q,full,1,j,0,0,0,3,who)','!base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who)')
cu=rep(cu,'condition(c,e,ne,s,effect(e,s,k),full,1,k)','base_condition(c,e,ne,s,effect(e,s,k),full,1,k,0,0,0,3,who)')
cu=rep(cu,'base_condition(c,e,ne,s,m,full,1,k)','base_condition(c,e,ne,s,m,full,1,k,0,0,0,3,owner)')
for f,t in [(files[0],host),(files[1],cu)]+[(f,texts[f].replace('detail_live_parts_v26','detail_ally_conditions_v27')) for f in files[2:]]:
    (ROOT/f).write_text(t,encoding='utf-8')
progress=json.loads((ROOT/'research/detail-expansion-next.json').read_text(encoding='utf-8'))
progress['current_work']=dict(feature='v27 ally HP activation versus recipient runtime predicates and defender ally branches',status='source assembled; builds and CPU/GPU verification pending',objective_complete=False)
(ROOT/'research/detail-expansion-next.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared v27 ally conditions; GPU verification pending')
