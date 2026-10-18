"""One-time v22 source preparation after the completed v21 checkpoint."""
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
archive=ROOT/'research/ports/v21';archive.mkdir(exist_ok=True)
for name in ('app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py'):
 dst=archive/Path(name).name
 if not dst.exists():shutil.copyfile(ROOT/name,dst)
def replace(s,a,b):assert a in s,a[:100];return s.replace(a,b)
p=ROOT/'app/detail_gpu.py';s=(archive/p.name).read_text(encoding='utf-8');s=s.replace('detail_random_v20','detail_shields_v22').replace('detail_state_bytes_v20','detail_state_bytes_v22')
s=replace(s,"EVENT['event:ally_burst_cast']=42", "EVENT['event:ally_burst_cast']=42\nEVENT['event:shield_consumed']=43")
s=replace(s,"allowed={'source',", "allowed={'end_on_shield_consumed','source',")
s=replace(s,"   q[201]=int(eff.get('event_scope')", "   if 'end_on_shield_consumed' in eff and (kind!='buff' or stat not in ('shield_from_max_hp_pct','shared_shield_from_max_hp_pct') or type(eff['end_on_shield_consumed']) is not bool):raise UnsupportedDetail('invalid shield consumption lifetime')\n   q[260]=int(eff.get('end_on_shield_consumed',False))\n   q[201]=int(eff.get('event_scope')")
s=replace(s,"   elif kind=='instant' and stat=='debuff_cleanse':q[1]=26", "   elif kind=='instant' and stat=='debuff_cleanse':q[1]=26\n   elif kind=='instant' and stat=='shield_heal_pct':q[1]=27\n   elif kind=='buff' and stat=='next_shield_hp_pct':q[1]=4;q[261]=1\n   elif kind=='buff' and stat=='shared_shield_from_max_hp_pct':q[1]=0;q[2]=45\n   elif kind=='buff' and stat=='shield_invincible':q[1]=4;q[213]=4")
s=replace(s,'if q[1] in (6,7,8) and q[4]==4:', 'if q[1] in (6,7,8,27) and q[4]==4:')
s=replace(s,"if kind=='instant' and stat=='heal_hp_pct' and scaling=='max_hp'", "if kind=='instant' and stat in ('heal_hp_pct','shield_heal_pct') and scaling=='max_hp'")
s=replace(s,"stat in ('cover_heal_pct','heal_hp_pct') and scaling=='max_hp'", "stat in ('cover_heal_pct','heal_hp_pct','shield_heal_pct') and scaling=='max_hp'")
s=replace(s,"   if scaling and not (kind=='instant'", "   if kind=='instant' and stat=='shield_heal_pct' and scaling not in (None,'max_hp'):raise UnsupportedDetail('unsupported shield healing scale')\n   if scaling and not (kind=='instant'")
s=replace(s,'row[1] not in (0,1,2,3,4,5)', 'row[1] not in (0,1,2,3,4,5,6)')
s=replace(s," if any(b[0]<a[0]", " if any(row[1]==6 and (row[2] not in (0,1,2) or int(row[2])!=row[2] or row[6]<0 or row[7] not in (0,1)) for row in script):raise ValueError('Invalid authored shield operation')\n if any(row[1]==2 and row[2]==111 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid shield state query')\n if any(b[0]<a[0]")
p.write_text(s,encoding='utf-8')
p=ROOT/'app/detail_effects.cu';s=(archive/p.name).read_text(encoding='utf-8');s=s.replace('detail_random_v20','detail_shields_v22').replace('detail_state_bytes_v20','detail_state_bytes_v22')
s=replace(s,' int shield_mask[NS],hits[5],', ' int shield_present[NS];double shield_current[NS][5],shield_capacity[NS][5],last_shield_result;\n int shield_mask[NS],hits[5],')
s=replace(s,'s->shield_mask[j]=0;', 's->shield_mask[j]=0;s->shield_present[j]=0;for(int p=0;p<5;p++)s->shield_current[j][p]=s->shield_capacity[j][p]=0;')
s=replace(s,'State* s=workspace+id;s->random_special_present=', 'State* s=workspace+id;s->last_shield_result=0;s->random_special_present=')
marker='__device__ void start_reload(const double*,const double*,int,State*,int,int,double);'
s=replace(s,marker,marker+'\n'+(ROOT/'research/ports/shield_quantities.cu.inc').read_text(encoding='utf-8'))
s=replace(s,'s->shield_mask[r]=max_hp(c,e,ne,s,owner,full)*value(e,ne,s,r)>0?s->masks[r]&31:0;invalidate(s);', 'build_shield(c,e,ne,s,r,full);')
s=replace(s,'  int mask=0,registration=q[59]>0&&event!=28;', '  int mask=0,registration=q[59]>0&&event!=28;\n  if(kind==27&&!registration&&q[6]==0)continue;')
s=replace(s,'  if(kind==24){add_burst', '''  if(kind==27){
   for(Order recipients=activation_order;recipients;recipients>>=3){int recipient=(recipients&7)-1;if(recipient<0||recipient>=5)continue;
    double base=q[50]>0?max_hp(c,e,ne,s,owner,full):shield_total(e,s,recipient,1);heal_shield(e,s,recipient,base*q[6]/100.0,t);
   }continue;
  }
  if(kind==24){add_burst''')
s=replace(s,'  if(op==5)status[id]|=flush_lands(c,e,ne,s,env,t,full);', '''  if(op==5)status[id]|=flush_lands(c,e,ne,s,env,t,full);
  if(op==6){
   if(ev==0)status[id]|=absorb_shield(c,e,ne,s,env,who,cmd[6],t,(int)cmd[7],full);
   else if(ev==1)s->last_shield_result=heal_shield(e,s,who,cmd[6],t);
   else{status[id]|=tick_effects(c,e,ne,s,env,t,full);s->last_shield_result=0;}
  }''')
s=replace(s,'   if(ev==110){', '''   if(ev==111){
    for(int k=0;k<OW;k++)dst[k]=0;dst[0]=s->last_shield_result;FloatSum amounts[5],capacities[5];for(int p=0;p<5;p++){amounts[p]={0,0};capacities[p]={0,0};}
    for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&(arg<0||effect(e,s,j)[3]==arg)){
     const double* q=effect(e,s,j);if(q[1]==0&&q[2]==45||q[261]>0){dst[16]++;dst[17]=(int)dst[17]|s->masks[j];dst[18]+=s->stacks[j];dst[19]=(int)dst[19]|s->shield_present[j];}
     if(q[1]==0&&q[2]==45)for(int p=0;p<5;p++){add_sum(s,&amounts[p],s->shield_current[j][p]);add_sum(s,&capacities[p],s->shield_capacity[j][p]);if(s->shield_current[j][p]>0)dst[11+p]=1;}
    }
    for(int p=0;p<5;p++){dst[1+p]=finish_sum(amounts[p]);dst[6+p]=finish_sum(capacities[p]);}continue;
   }
   if(ev==110){''')
p.write_text(s,encoding='utf-8')
for name in ('scripts/build-combat.py','scripts/build-detail-native.py'):
 p=ROOT/name;s=(archive/p.name).read_text(encoding='utf-8');assert 'detail_random_v20' in s;p.write_text(s.replace('detail_random_v20','detail_shields_v22'),encoding='utf-8')
print('v22 shield sources prepared; GPU builds and independent parity pending.')
