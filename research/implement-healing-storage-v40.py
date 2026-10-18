"""Add an autonomous GPU overheal buffer; never feed CPU quantities to CUDA."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];stage=ROOT/'research/staging/v40/app'
p=stage/'detail_gpu.py';s=p.read_text(encoding='utf-8');assert 'heal_overcharge_store=74' not in s
s=s.replace('outgoing_heal_pct=73)','outgoing_heal_pct=73,heal_overcharge_store=74)').replace('0<=r[2]<74','0<=r[2]<75')
needle=" if any(row[1]==2 and row[2]==121 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid decoy state query')"
assert needle in s;s=s.replace(needle,needle+"\n if any(row[1]==2 and row[2]==122 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid healing-storage query')")
p.write_text(s,encoding='utf-8')
p=stage/'detail_effects.cu';s=p.read_text(encoding='utf-8');assert 'build_heal_storage' not in s
s=s.replace('struct State {','struct State {\n double heal_store_expiry[NS];',1)
needle='s->definition[j]=definition;s->alive[j]=0;';assert s.count(needle)==1;s=s.replace(needle,'s->heal_store_expiry[j]=-1;'+needle)
needle='for(int j=0;j<NS;j++){s->definition[j]=';assert s.count(needle)==1;s=s.replace(needle,'for(int j=0;j<NS;j++){s->heal_store_expiry[j]=-1;s->definition[j]=')
needle='__device__ double take_shield_amp';at=s.index(needle)
s=s[:at]+'''// Storage is a separate overheal reserve, not a max-HP modifier or shield.
__device__ void build_heal_storage(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);double cap=mx(0,max_hp(c,e,ne,s,(int)q[0],full)*recipient_value(e,ne,s,j,(int)q[0])/100);
 int preserve=s->when<s->heal_store_expiry[j];int previous=s->shield_present[j];s->shield_present[j]=s->masks[j]&31;
 for(int who=0;who<5;who++){
  double old=preserve&&(previous&(1<<who))?s->shield_current[j][who]:0;
  s->shield_capacity[j][who]=(s->shield_present[j]&(1<<who))?cap:0;
  s->shield_current[j][who]=mn(mx(0,old),s->shield_capacity[j][who]);
 }
 s->heal_store_expiry[j]=s->end[j];
}
__device__ int heal_storage_slots(const double* c,const double* e,int ne,State* s,int who,int full,int* order){
 if(s->down_mask&(1<<who))return 0;int count=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);if(q[1]!=0||q[2]!=74||!live_shield_recipient(c,e,ne,s,j,who,full))continue;
  if(!s->shield_present[j])build_heal_storage(c,e,ne,s,j,full);
  if(!(s->shield_present[j]&(1<<who)))continue;
  int at=count++;while(at>0&&s->activated[order[at-1]]<s->activated[j]){order[at]=order[at-1];at--;}order[at]=j;
 }
 return count;
}
__device__ void fill_heal_storage(const double* c,const double* e,int ne,State* s,int who,double amount,int full){
 if(amount<=0)return;int order[NS],count=heal_storage_slots(c,e,ne,s,who,full,order);
 for(int k=0;k<count;k++){int j=order[k];double put=mn(amount,mx(0,s->shield_capacity[j][who]-s->shield_current[j][who]));s->shield_current[j][who]+=put;amount-=put;}
}
__device__ double absorb_heal_storage(const double* c,const double* e,int ne,State* s,int who,double amount,int full){
 if(amount<=0)return mx(0,amount);int order[NS],count=heal_storage_slots(c,e,ne,s,who,full,order);
 for(int k=0;k<count;k++){int j=order[k];double take=mn(amount,s->shield_current[j][who]);s->shield_current[j][who]-=take;amount-=take;}return amount;
}
__device__ void apply_storage_body_heal(const double* c,const double* e,int ne,State* s,int who,double amount,int full){
 double maximum=max_hp(c,e,ne,s,who,full);if(amount>0)fill_heal_storage(c,e,ne,s,who,mx(0,s->hp[who]+amount-maximum),full);
 s->hp[who]=mn(s->hp[who]+amount,maximum);
}
'''+s[at:]
needle='if(phase==4&&q[1]==0&&q[2]==72&&!post_lazy[depth]&&post_rawmask[depth]){r=first_instance(e,s,s->definition[r]);if(r>=0)build_decoy(c,e,ne,s,r,full);}'
assert s.count(needle)==1;s=s.replace(needle,needle+'\n   if(phase==4&&q[1]==0&&q[2]==74&&!post_lazy[depth]&&post_rawmask[depth]){r=first_instance(e,s,s->definition[r]);if(r>=0)build_heal_storage(c,e,ne,s,r,full);}')
needle='s->hp[recipient]=mn(s->hp[recipient]+base*amount/100*heal_multiplier(c,e,ne,s,recipient,full,source),max_hp(c,e,ne,s,recipient,full));'
assert s.count(needle)==1;s=s.replace(needle,'apply_storage_body_heal(c,e,ne,s,recipient,base*amount/100*heal_multiplier(c,e,ne,s,recipient,full,source),full);')
needle='s->hp[who]=mn(s->hp[who]+hit*ls/100*heal_multiplier(c,e,ne,s,who,full,who),max_hp(c,e,ne,s,who,full));'
assert s.count(needle)==1;s=s.replace(needle,'apply_storage_body_heal(c,e,ne,s,who,hit*ls/100*heal_multiplier(c,e,ne,s,who,full,who),full);')
needle='s->hp[recipient]=mx(0,s->hp[recipient]*(1-reduce_amount[depth]/100));'
assert s.count(needle)==1;s=s.replace(needle,'double old=s->hp[recipient],after=mx(0,old*(1-reduce_amount[depth]/100));if(after<old){double amount=old-after,remaining=absorb_heal_storage(c,e,ne,s,recipient,amount,full);after+=amount-remaining;}s->hp[recipient]=after;')
needle='if(hp&&live_marker(c,e,ne,s,who,67,full))hp=0;';assert s.count(needle)==1;s=s.replace(needle,needle+'\n if(hp)hp=absorb_heal_storage(c,e,ne,s,who,hp,full);')
start=s.index('   if(ev==121){');end=s.index('   if(ev==110)',start)
query=s[start:end].replace('ev==121','ev==122').replace('effect(e,s,j)[2]==72','effect(e,s,j)[2]==74')
s=s[:end]+query+s[end:]
p.write_text(s,encoding='utf-8');print('Staged GPU storage lifecycle/body healing/damage/drain/query122 implemented; no GPU parity claim yet.')
