"""One-shot v26 assembly from verified v25; do not rerun after assembly."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']
texts={f:(ROOT/f).read_text(encoding='utf-8') for f in files}
assert "DETAIL_ABI='detail_optimal_range_v25'" in texts[files[0]]
archive=ROOT/'research/ports/v25';archive.mkdir(exist_ok=True)
for f in files+['app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','research/detail-normal-acceptance.json','research/detail-normal-acceptance.log']:
    dest=archive/Path(f).name;assert not dest.exists(),dest;dest.write_bytes((ROOT/f).read_bytes())
def rep(t,old,new):
    assert t.count(old)==1,(old[:100],t.count(old));return t.replace(old,new)
host=texts[files[0]].replace('detail_optimal_range_v25','detail_live_parts_v26').replace('detail_state_bytes_v25','detail_state_bytes_v26')
host=rep(host,"'optimal_range_max_pct':62}","'optimal_range_max_pct':62,'pierce_range':63,'explosion_range':64}")
host=rep(host,"from gpu_combat import STAT as COARSE_STAT","from gpu_combat import STAT as COARSE_STAT\nfrom detail_world import EN,read_parts,patterns_for,packed_enemy")
host=rep(host,"    if eff['hits_parts'] and c.get('_detail_has_parts',False):q[39]=int(q[39])|1024","    if eff['hits_parts']:\n     q[39]=int(q[39])|65536\n     if c.get('_detail_has_parts',False):q[39]=int(q[39])|1024")
host=rep(host,'not 0<=r[2]<63','not 0<=r[2]<65')
host=rep(host,"  if len(en)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in en):raise ValueError('Invalid detailed enemy')", "  if len(en) not in (2,EN) or not all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in en):raise ValueError('Invalid detailed enemy')\n  if len(en)==EN:\n   count=en[2]\n   if int(count)!=count or not 0<=count<=32 or en[67] not in (0,1):raise ValueError('Invalid detailed parts world')\n   if any(en[3+i*2]>1e15 or int(en[4+i*2])!=en[4+i*2] or not 1<=en[4+i*2]<=5 for i in range(int(count))):raise ValueError('Invalid detailed part target')")
host=rep(host,'row[1] not in (0,1,2,3,4,5,6)','row[1] not in (0,1,2,3,4,5,6,7)')
anchor=" if any(b[0]<a[0] for a,b in zip(script,script[1:])):"
host=rep(host,anchor," if any(row[1]==7 and (row[2] not in (0,1) or int(row[4])!=row[4] or not 0<=row[4]<=5 or row[6]<0 or int(row[7])!=row[7] or not -1<=row[7]<32) for row in script):raise ValueError('Invalid authored part stimulus')\n if any(row[1]==2 and row[2]==114 and (int(row[4])!=row[4] or not 0<=row[4]<32) for row in script):raise ValueError('Invalid part state query')\n"+anchor)
host=rep(host,"array.array('d',(v for enemy in enemies for v in enemy))","array.array('d',(v for enemy in enemies for v in list(enemy)+[0]*(EN-len(enemy))))")
anchor=" bs={c['name']:stats(c) for c in chars}"
host=rep(host,anchor," parts=read_parts(body.get('enemy',{}).get('parts',[]))\n if enemy.get('patterns',[])!=patterns_for(parts) or enemy.get('coord') is not None:raise UnsupportedDetail('Only authored fixed live parts are implemented; other boss patterns remain unsupported')\n"+anchor)
host=rep(host,"'enemy':[enemy['def'],enemy['core_px']], 'prepared':prepared", "'enemy':packed_enemy(enemy,parts),'parts':parts, 'prepared':prepared")
anchor=" result=run(device,[compiled['program']],script,"
host=rep(host,anchor," parts=compiled.get('parts',[])\n part_offset=sum(row[1]==2 for row in script)\n for i in range(len(parts)):script.append([duration,2,114,0,i,part_offset+i,0,0])\n"+anchor)
anchor=" payload['seed']=body.get('seed',0)"
host=rep(host,anchor," if parts:\n  payload['parts_state']=[dict(name=part['name'],damage=int(logs[part_offset+i][1]),hits=int(logs[part_offset+i][2]),destroyed=bool(logs[part_offset+i][0]),destroyed_at=round(logs[part_offset+i][3],6) if logs[part_offset+i][0] else None) for i,part in enumerate(parts)]\n"+anchor)
cu=texts[files[1]].replace('detail_optimal_range_v25','detail_live_parts_v26').replace('detail_state_bytes_v25','detail_state_bytes_v26')
cu=rep(cu,'#define EW 268','#define EW 268\n#define EN 68')
cu=rep(cu,'struct State {','struct State {\n double part_dealt[32],part_at[32],shot_part[5],land_part[1024],now_part[NE];\n int part_dead[32],part_hits[32],part_min,part_pending,shot_reach[5],land_reach[1024],now_reach[NE];')
cu=rep(cu,'if(s->valid[who]&(1ULL<<key))','if(key<63&&(s->valid[who]&(1ULL<<key)))')
cu=rep(cu,' s->cached[who][key]=out;s->valid[who]|=1ULL<<key;s->camera_lens=previous_lens;return out;',' if(key<63){s->cached[who][key]=out;s->valid[who]|=1ULL<<key;}s->camera_lens=previous_lens;return out;')
cu=rep(cu,' const double* a=c+who*CW;double b[ST];for(int k=0;k<ST;k++)b[k]=stat(c,e,ne,s,who,k,full);', ' if(env[2]>0&&!(flags&131072)){flags&=~1024;if((flags&65536)&&s->part_min==0&&env[67]>0)flags|=1024;}\n const double* a=c+who*CW;double b[ST];for(int k=0;k<ST;k++)b[k]=stat(c,e,ne,s,who,k,full);')
cu=rep(cu,'double core=(flags&16384)?1:', 'double core=(flags&131072)?0:(flags&16384)?1:')
anchor='// Explicit bounded DFS preserves synchronous nested stack-reach order.'
cu=rep(cu,anchor,(ROOT/'research/ports/reach_damage.cu.inc').read_text(encoding='utf-8')+'\n'+anchor)
cu=rep(cu,'s->land_owner[k]=owner;s->land_damage[k]=hit;', 's->land_owner[k]=owner;s->land_damage[k]=hit;ReachHit part=reach_sample(c,e,ne,s,env,owner,full,v,(int(q[39])&256)?1:0,(int)q[39]);s->land_reach[k]=part.reach;s->land_part[k]=part.damage;')
# Snapshot the part component before shot notifications mutate buffs/weapon modes.
auto='(skill?32768:0)|(stat(c,e,ne,s,who,36,full)>0?64:0)|(stat(c,e,ne,s,who,52,full)>0?512:0)'
charge='(is_full?32:0)|(skill?32768:0)|((int)a[26]?8:0)|(stat(c,e,ne,s,who,36,full)>0?64:0)|(stat(c,e,ne,s,who,52,full)>0?512:0)'
for expression,coeff in [(auto,'coeff'),(charge,'coeff/split')]:
    old=f' double one=damage(c,e,ne,s,env,who,full,{coeff},!skill,{expression});'
    new=f' int flags={expression};double one=damage(c,e,ne,s,env,who,full,{coeff},!skill,flags);ReachHit part=reach_sample(c,e,ne,s,env,who,full,{coeff},!skill,flags);s->shot_reach[who]=part.reach;s->shot_part[who]=part.damage;'
    cu=rep(cu,old,new)
anchor='__device__ int flush_lands('
cu=rep(cu,anchor,(ROOT/'research/ports/live_parts.cu.inc').read_text(encoding='utf-8')+'\n'+anchor)
cu=rep(cu,'for(int k=0;k<s->land_count;k++)code|=heal_landed(c,e,ne,s,env,t,full,s->land_owner[k],s->land_damage[k]);', 'for(int k=0;k<s->land_count;k++){int who=s->land_owner[k];code|=heal_landed(c,e,ne,s,env,t,full,who,s->land_damage[k]);code|=parts_land(c,e,ne,s,env,t,full,who,s->land_reach[k],s->land_part[k]);}')
cu=rep(cu,' int code=tick_effects(c,e,ne,s,env,t,*full);',' int part_events=parts_refresh(env,s);int code=tick_effects(c,e,ne,s,env,t,*full);code|=parts_events(c,e,ne,s,env,t,*full,part_events);')
cu=rep(cu,'double hit=damage(c,e,ne,s,env,(int)q[0],1,coeff,0,0);', 'double hit=damage(c,e,ne,s,env,(int)q[0],1,coeff,(int(q[39])&256)?1:0,(int)q[39]);')
cu=rep(cu,'s->now_damage[s->now_count++]=hit;', 's->now_damage[s->now_count]=hit;ReachHit part=reach_sample(c,e,ne,s,env,(int)q[0],1,coeff,(int(q[39])&256)?1:0,(int)q[39]);s->now_reach[s->now_count]=part.reach;s->now_part[s->now_count++]=part.damage;')
cu=rep(cu,'for(int k=0;k<s->now_count;k++)code|=heal_landed(c,e,ne,s,env,t,1,s->now_owner[k],s->now_damage[k]);', 'for(int k=0;k<s->now_count;k++){int who=s->now_owner[k];code|=heal_landed(c,e,ne,s,env,t,1,who,s->now_damage[k]);code|=parts_land(c,e,ne,s,env,t,1,who,s->now_reach[k],s->now_part[k]);}')
cu=rep(cu,'for(int k=0;k<s->hits[i];k++)code|=heal_landed(c,e,ne,s,env,t,*full,i,s->hit_unit[i]);', 'for(int k=0;k<s->hits[i];k++){code|=heal_landed(c,e,ne,s,env,t,*full,i,s->hit_unit[i]);code|=parts_land(c,e,ne,s,env,t,*full,i,s->shot_reach[i],s->shot_part[i]);}')
cu=rep(cu,'const double* env=enemy+id*2;', 'const double* env=enemy+id*EN;')
cu=rep(cu,' status[id]=0;',' s->part_pending=0;for(int p=0;p<32;p++){s->part_dead[p]=s->part_hits[p]=0;s->part_dealt[p]=0;s->part_at[p]=-1;}parts_refresh(env,s);\n status[id]=0;')
cu=rep(cu,'if(!s->squad_mode)status[id]|=tick_effects', 'if(!s->squad_mode&&op!=7)status[id]|=tick_effects')
anchor='  if(op==2){'
cu=rep(cu,anchor,'  if(op==7){if(ev==0)status[id]|=parts_land(c,e,ne,s,env,t,full,who,arg,cmd[6],(int)cmd[7]);else{int count=parts_refresh(env,s);status[id]|=tick_effects(c,e,ne,s,env,t,full);status[id]|=parts_events(c,e,ne,s,env,t,full,count);}}\n'+anchor)
cu=rep(cu,'   if(ev==113){', '   if(ev==114){dst[0]=s->part_dead[arg];dst[1]=s->part_dealt[arg];dst[2]=s->part_hits[arg];dst[3]=s->part_at[arg];dst[4]=s->part_min;dst[5]=s->part_pending;continue;}\n   if(ev==113){')
for f,t in [(files[0],host),(files[1],cu)]+[(f,texts[f].replace('detail_optimal_range_v25','detail_live_parts_v26')) for f in files[2:]]:(ROOT/f).write_text(t,encoding='utf-8')
progress=json.loads((ROOT/'research/detail-expansion-next.json').read_text(encoding='utf-8'));progress['current_work']=dict(feature='v26 live reach parts, pierce/explosion range, real destruction and next-frame notifications',status='source assembled; builds and verification pending',objective_complete=False)
(ROOT/'research/detail-expansion-next.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared v26 live reach parts; no GPU verification claim yet')
