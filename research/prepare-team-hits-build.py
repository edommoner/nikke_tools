"""Initial v28 assembly; do not rerun. Final identity/binding fixes are in app sources.

The initial failed source is retained in research/ports/v28-initial.
Final v28 uses EW270, distinct instance/shared-budget keys and source_rows.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_world.py','scripts/build-combat.py','scripts/build-detail-native.py']
texts={f:(ROOT/f).read_text(encoding='utf-8') for f in files}
assert "DETAIL_ABI='detail_ally_conditions_v27'" in texts[files[0]]
archive=ROOT/'research/ports/v27';archive.mkdir(exist_ok=True)
for f in files+['app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','research/detail-normal-acceptance.json']:
    dest=archive/Path(f).name
    if dest.exists():assert dest.read_bytes()==(ROOT/f).read_bytes(),dest
    else:dest.write_bytes((ROOT/f).read_bytes())
def rep(t,old,new):
    assert t.count(old)==1,(old[:100],t.count(old))
    return t.replace(old,new)
host=texts[files[0]].replace('detail_ally_conditions_v27','detail_team_hits_v28').replace('detail_state_bytes_v27','detail_state_bytes_v28')
host=rep(host,'import array,ctypes as C,math,re,time,sys','import array,copy,ctypes as C,math,re,time,sys')
host=rep(host,'NE,EW,CW,OW=128,268,168,48','NE,EW,CW,OW=128,269,168,48')
host=rep(host," rows=[];compiled=[];problems=[];groups={};equipment_states={};target_plans=[];target_keys={}",""" rows=[];compiled=[];problems=[];groups={};equipment_states={};target_plans=[];target_keys={}
 # Each team listener has one immutable activation definition per attacker.
 # All five see the common event count; only the actual attacker activates.
 # This retains attacker-based levels/targets and source-owner conditions.
 team_origins={};team_budgets={};expanded=[]
 for index,(eff,caster) in enumerate(effects):
  timings=eff.get('trigger',{}).get('timing',[])
  team=[t.startswith(('part_hit_count:','body_hit_count:')) for t in timings]
  if any(team):
   if not all(team) or eff.get('type') not in ('buff','instant','damage') or eff.get('tick_interval') is not None:
    raise UnsupportedDetail([{'character':caster,'effect':eff.get('name','?'),'reason':'mixed, periodic or weapon-change team listener remains unsupported'}])
   if any(not t.split(':',1)[1].isdigit() or int(t.split(':',1)[1])<=0 for t in timings):
    raise UnsupportedDetail('team hit threshold must be a positive integer literal')
   for attacker in names:
    clone=copy.deepcopy(eff);team_origins[id(clone)]=(caster,id(eff));expanded.append((clone,attacker))
  else:expanded.append((eff,caster))
 effects=expanded""")
anchor="   if not isinstance(q[57],int)"
assert host.count(anchor)==1
host=host.replace(anchor,"""   team_origin=team_origins.get(id(eff))
   if team_origin:
    q[268]=names.index(team_origin[0])+1
    if team_origin[1] not in team_budgets:team_budgets[team_origin[1]]=len(rows)
    q[58]=team_budgets[team_origin[1]]
"""+anchor)
host=rep(host,"    elif timing.startswith('pellet_hit_in_shot:')", "    elif timing.startswith(('part_hit_count:','body_hit_count:')):\n     key,threshold=timing.split(':');code=44 if key=='part_hit_count' else 45;arg=int(threshold);q[46]=1\n    elif timing.startswith('pellet_hit_in_shot:')")
host=rep(host,"   for j,condition in enumerate(cond):", "   activation_context=(caster,owner,c,lv)\n   if team_origin:\n    caster=team_origin[0];owner=names.index(caster);c=chars[owner];lv=str(c.get('skill_levels',{}).get(eff.get('source','')[-1:],c.get('skill_level',10)))\n   for j,condition in enumerate(cond):")
host=rep(host,"   if kind=='weapon_change':\n    from calculator.timeline", "   caster,owner,c,lv=activation_context\n   if kind=='weapon_change':\n    from calculator.timeline")
cu=texts[files[1]].replace('detail_ally_conditions_v27','detail_team_hits_v28').replace('detail_state_bytes_v27','detail_state_bytes_v28')
cu=rep(cu,'#define EW 268','#define EW 269')
cu=rep(cu,'frac[5][2]','frac[5][4]')
cu=rep(cu,'struct State {','struct State {\n int team_interest;')
cu=rep(cu,'s->frac[i][0]=s->frac[i][1]=0;','s->frac[i][0]=s->frac[i][1]=s->frac[i][2]=s->frac[i][3]=0;')
cu=rep(cu,'int query=-1);','int query=-1,int eval_owner=-1);')
cu=rep(cu,'int query){','int query,int eval_owner){')
cu=rep(cu,'int owner=(int)q[0];double v=0;','int owner=eval_owner>=0?eval_owner:(int)q[0];double v=0;')
cu=rep(cu,'int slot=-1,double core_frac=0,int hit_crit=0){','int slot=-1,double core_frac=0,int hit_crit=0,int eval_owner=-1){')
cu=rep(cu,' if(runtime)return base_condition(c,e,ne,s,q,full,runtime,slot,core_frac,hit_crit);',' if(runtime)return base_condition(c,e,ne,s,q,full,runtime,slot,core_frac,hit_crit,0,3,-1,eval_owner);\n int owner=eval_owner>=0?eval_owner:(int)q[0];')
cu=rep(cu,'stat(c,e,ne,s,(int)q[0],(int)q[16+j*3],full)','stat(c,e,ne,s,owner,(int)q[16+j*3],full)')
cu=rep(cu,'optimal_range(c,e,ne,s,(int)q[0],full,0)','optimal_range(c,e,ne,s,owner,full,0)')
cu=rep(cu,'core_frac,hit_crit,j,1)','core_frac,hit_crit,j,1,-1,eval_owner)')
cu=rep(cu,'if(event!=26&&owner!=iwho[depth])continue;','if(event!=26&&event!=44&&event!=45&&owner!=iwho[depth])continue;')
cu=rep(cu,'  if(!matched)continue;','  if(!matched)continue;\n  if((event==44||event==45)&&owner!=iwho[depth])continue;')
cu=rep(cu,'depth==0?hit_crit:0);if(!cond_met','depth==0?hit_crit:0,(event==44||event==45)?(int)q[268]-1:-1);if(!cond_met')
cu=rep(cu,'int index=ev==22?0:1;', 'int index=ev==22?0:ev==23?1:ev==44?2:3;')
cu=rep(cu,' if(part<=0)return 0;if(part>=1)return notify',' if((ev==44||ev==45)&&!(s->team_interest&(1<<(ev-44))))return 0;\n if(part<=0)return 0;if(part>=1)return notify')
cu=rep(cu,' s->burst_amount=0;s->burst_charging=1;',' s->team_interest=0;for(int j=0;j<ne;j++)for(int k=0;k<(int)e[j*EW+144];k++){int code=(int)e[j*EW+TD+k*TS];if(code==44||code==45)s->team_interest|=1<<(code-44);}\n s->burst_amount=0;s->burst_charging=1;')
# Per-pellet non-core broadcasts use the original shot snapshot. Body/part
# classification is frame-wide and does not count extra reach damage twice.
anchor='__device__ double core_probability('
assert cu.count(anchor)==1
cu=cu.replace(anchor,'__device__ int team_hit_event(const double* env,State* s){return (env[67]>0||(env[2]>0&&s->part_min>0))?44:45;}\n'+anchor)
cu=rep(cu,'status|=notify(c,e,ne,s,env,t,20,who,0,full);status|=fractional', 'status|=notify(c,e,ne,s,env,t,20,who,0,full);status|=fractional(c,e,ne,s,env,t,who,full,team_hit_event(env,s),1-core);status|=fractional')
cu=rep(cu,' if(!skill)code|=consume_bullets(c,e,ne,s,env,t,who,full);\n for(int k=0;k<count;k++)code|=fractional', ' for(int k=0;k<count;k++)code|=fractional(c,e,ne,s,env,t,who,full,team_hit_event(env,s),1-core);\n if(!skill)code|=consume_bullets(c,e,ne,s,env,t,who,full);\n for(int k=0;k<count;k++)code|=fractional')
world=rep(texts[files[2]],"    if not parts:return [enemy['def'],enemy['core_px']]", "    if not parts and not enemy.get('has_parts',False):return [enemy['def'],enemy['core_px']]")
for f,t in [(files[0],host),(files[1],cu),(files[2],world)]+[(f,texts[f].replace('detail_ally_conditions_v27','detail_team_hits_v28')) for f in files[3:]]:
    (ROOT/f).write_text(t,encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';progress=json.loads(p.read_text(encoding='utf-8'))
progress['current_work']=dict(feature='v28 global team part/body hits, source-owner conditions and attacker attribution',status='source assembled; builds and verification pending',objective_complete=False)
p.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared v28 team hits; no GPU parity claim yet')
