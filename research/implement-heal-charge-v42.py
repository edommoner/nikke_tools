"""Autonomous v42 received-healing pool, named release and read-only witnesses."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];stage=ROOT/'research/staging/v42/app'
p=stage/'detail_gpu.py';s=p.read_text(encoding='utf-8')
assert 'heal_overcharge_store_atk_pct=76' not in s
def sub(old,new):
    global s
    assert s.count(old)==1,(old[:90],s.count(old));s=s.replace(old,new)
sub('heal_split=75)','heal_split=75,heal_overcharge_store_atk_pct=76,accumulate_max_scale_pct=77)')
sub("   elif kind=='instant' and stat=='decoy_heal_pct':q[1]=31", """   elif kind=='instant' and stat=='decoy_heal_pct':q[1]=31
   elif kind=='instant' and stat=='heal_overcharge_discharge':
    if not isinstance(eff.get('target_effect'),str) or not eff['target_effect']:raise UnsupportedDetail('healing discharge requires a named target_effect')
    q[1]=32;q[36]=state(eff['target_effect'])
   elif kind=='buff' and stat=='accumulate_max_scale_pct':
    if 'target_effect' in eff and (not isinstance(eff['target_effect'],str) or not eff['target_effect']):raise UnsupportedDetail('invalid healing capacity target_effect')
    q[1]=0;q[2]=77;q[212]=int('target_effect' in eff);q[36]=state(eff.get('target_effect',''))""")
sub('0<=r[2]<76','0<=r[2]<78')
sub("   if r[1]==31 and (r[258]!=1 or r[4]==4):raise ValueError('Invalid decoy healing instruction')", """   if r[1]==31 and (r[258]!=1 or r[4]==4):raise ValueError('Invalid decoy healing instruction')
   if r[1]==32 and (r[258]!=1 or r[4]==4 or int(r[36])!=r[36] or not 0<=r[36]<NE):raise ValueError('Invalid healing discharge instruction')
   if r[1]==0 and r[2]==77 and (r[212] not in (0,1) or int(r[36])!=r[36] or not 0<=r[36]<NE):raise ValueError('Invalid healing capacity reference')""")
sub(" if any(row[1]==2 and row[2]==122 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid healing-storage query')", """ if any(row[1]==2 and row[2]==122 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid healing-storage query')
 if any(row[1]==2 and row[2]==123 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid healing-charge query')""")
sub('storage_times=[]\n for i in range(5):script.append([0,0,0,i,0,-1,0,0])', '''storage_times=[]
 if '_debug_charge_frames' in body and type(body['_debug_charge_frames']) is not bool:raise ValueError('Invalid charge frame witness')
 charge_keys=sorted({int(q[3]) for q in compiled['program']['effects'] if q[1]==0 and q[2]==76}) if body.get('_debug_charge_frames') else []
 charge_offset=storage_offset+(len(frame_times)*(1+len(storage_keys)) if body.get('_debug_storage_frames') else 0);charge_times=[]
 for i in range(5):script.append([0,0,0,i,0,-1,0,0])''')
sub(' # Log readback is data produced by GPU, not CPU-selected burst times.', '''  if body.get('_debug_charge_frames'):
   for key in [-1]+charge_keys:script.append([t,2,123,0,key,charge_offset+len(charge_times),0,0]);charge_times.append((t,key))
 # Log readback is data produced by GPU, not CPU-selected burst times.''')
sub(" if body.get('_debug_hp_events'):\n  count=int(logs[hp_offset][3])", """ if charge_times:payload['_charge_frames']=[dict(time=at,key=key,current={n:row[1+i] for i,n in enumerate(names)},base_capacity={n:row[6+i] for i,n in enumerate(names)},carriers=int(row[16])) for (at,key),row in zip(charge_times,logs[charge_offset:charge_offset+len(charge_times)])]
 if body.get('_debug_hp_events'):
  count=int(logs[hp_offset][3])""")
p.write_text(s,encoding='utf-8')
p=stage/'detail_effects.cu';s=p.read_text(encoding='utf-8')
sub(' int shield_present[NS];',' double heal_charge_last[5][NE];\n int shield_present[NS];')
code='''// Independent received-healing pool: full allocated healing, not excess HP.
// shield_present is disjoint for stat76: 0 uninitialized/retired, 1 open, 2 taken.
__device__ void build_heal_charge(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);int owner=(int)q[0];
 s->shield_capacity[j][0]=mx(0,rank_atk(c,e,ne,s,owner,full)*value(e,ne,s,j)/100);s->shield_current[j][0]=0;s->shield_present[j]=1;
}
__device__ double heal_charge_capacity(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);int owner=(int)q[0],name=(int)q[3];double bonus=0;
 for(int k=s->slot_head;k>=0;k=s->slot_next[k]){const double* b=effect(e,s,k);if(b[1]!=0||b[2]!=77||(b[212]>0&&b[36]!=name)||!live_shield_recipient(c,e,ne,s,k,owner,full))continue;bonus+=recipient_value(e,ne,s,k,owner);}
 return mx(0,s->shield_capacity[j][0]*(1+bonus/100));
}
__device__ void collect_heal_charge(const double* c,const double* e,int ne,State* s,int who,double amount,int full){
 if(amount<=0||(s->down_mask&(1<<who)))return;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){const double* q=effect(e,s,j);if(q[1]!=0||q[2]!=76||s->shield_present[j]!=1||!live_shield_recipient(c,e,ne,s,j,who,full))continue;
  double room=mx(0,heal_charge_capacity(c,e,ne,s,j,full)-s->shield_current[j][0]);s->shield_current[j][0]+=mn(amount,room);
 }
}
__device__ void retire_heal_charge(const double* e,State* s,int j){
 const double* q=effect(e,s,j);if(q[1]!=0||q[2]!=76)return;int owner=(int)q[0],name=(int)q[3];
 if(s->shield_present[j]==1&&q[35]>0&&!(s->down_mask&(1<<owner)))s->heal_charge_last[owner][name]+=s->shield_current[j][0];
 s->shield_current[j][0]=0;s->shield_present[j]=0;
}
__device__ double take_heal_charge(const double* e,State* s,int owner,int name){
 if(s->down_mask&(1<<owner))return 0;double amount=s->heal_charge_last[owner][name];s->heal_charge_last[owner][name]=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){const double* q=effect(e,s,j);if(!s->alive[j]||q[1]!=0||q[2]!=76||q[0]!=owner||q[3]!=name||s->shield_present[j]!=1)continue;
  amount+=s->shield_current[j][0];s->shield_current[j][0]=0;s->shield_present[j]=2;
 }return amount;
}
'''
sub('__device__ void apply_storage_body_heal(',code+'__device__ void apply_storage_body_heal(')
sub(' double maximum=max_hp(c,e,ne,s,who,full);if(amount>0)fill_heal_storage', ' collect_heal_charge(c,e,ne,s,who,amount,full);double maximum=max_hp(c,e,ne,s,who,full);if(amount>0)fill_heal_storage')
sub('removed[n]=j;masks[n++]=s->masks[j];s->alive[j]=0;', 'removed[n]=j;masks[n++]=s->masks[j];retire_heal_charge(e,s,j);s->alive[j]=0;')
sub('int hit_crit,double healing_pool){\n unsigned short', '''int hit_crit,double healing_pool){
 if(ev==29)for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(!s->alive[j]&&effect(e,s,j)[0]==who&&effect(e,s,j)[3]==arg)retire_heal_charge(e,s,j);
 unsigned short''')
sub('double share_pool[32];share_pool[0]=healing_pool;', 'double share_pool[32],release_pool[32];share_pool[0]=healing_pool;')
old='double base=heal[50]>0?max_hp(c,e,ne,s,source,full):c[recipient*CW+28];pool=base*amount/100*heal_multiplier(c,e,ne,s,recipient,full,source);event=54;'
sub(old,'double base=heal[50]>0?max_hp(c,e,ne,s,source,full):c[recipient*CW+28];pool=(heal[1]==32?release_pool[depth]:base*amount/100)*heal_multiplier(c,e,ne,s,recipient,full,source);event=54;')
sub('  if(kind==6){queue[depth]=activation_order;', '''  if(kind==32){release_pool[depth]=take_heal_charge(e,s,owner,(int)q[36]);queue[depth]=activation_order;queue_event[depth]=16;queue_arg[depth]=-1;healrow[depth]=j;continue;}
  if(kind==6){queue[depth]=activation_order;''')
sub('   if(phase==4&&q[1]==0&&q[2]==74', '''   if(phase==4&&q[1]==0&&q[2]==76){r=first_instance(e,s,s->definition[r]);if(r>=0)build_heal_charge(c,e,ne,s,r,full);}
   if(phase==4&&q[1]==0&&q[2]==74''')
sub('    s->alive[k]=0;s->stacks[k]=0;s->dot_present[k]=0;if(first_instance', '    retire_heal_charge(e,s,k);s->alive[k]=0;s->stacks[k]=0;s->dot_present[k]=0;if(first_instance')
sub('if(!s->masks[k]){s->alive[k]=0;s->stacks[k]=0;s->dot_present[k]=0;}', 'if(!s->masks[k]){if(effect(e,s,k)[1]==0&&effect(e,s,k)[2]==76){s->shield_present[k]=0;s->shield_current[k][0]=0;}s->alive[k]=0;s->stacks[k]=0;s->dot_present[k]=0;}')
sub(' // Mark down before ending the mode.', ''' for(int key=0;key<NE;key++)s->heal_charge_last[who][key]=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(!s->alive[j]&&effect(e,s,j)[0]==who&&effect(e,s,j)[1]==0&&effect(e,s,j)[2]==76){s->shield_present[j]=0;s->shield_current[j][0]=0;}
 // Mark down before ending the mode.''')
sub('s->hold_fired[k][j]=0;s->gauges[k][j]=0;', 's->hold_fired[k][j]=0;s->heal_charge_last[k][j]=0;s->gauges[k][j]=0;')
code='''   if(ev==123){
    for(int k=0;k<OW;k++)dst[k]=0;double amounts[5]={0,0,0,0,0},capacities[5]={0,0,0,0,0};
    for(int owner=0;owner<5;owner++)for(int key=0;key<NE;key++)if(arg<0||key==arg)amounts[owner]+=s->heal_charge_last[owner][key];
    for(int j=s->slot_head;j>=0;j=s->slot_next[j]){const double* q=effect(e,s,j);if(!s->alive[j]||q[1]!=0||q[2]!=76||s->shield_present[j]==0||(arg>=0&&q[3]!=arg))continue;int owner=(int)q[0];dst[16]++;amounts[owner]+=s->shield_current[j][0];capacities[owner]+=s->shield_capacity[j][0];}
    for(int owner=0;owner<5;owner++){dst[1+owner]=amounts[owner];dst[6+owner]=capacities[owner];}continue;
   }
'''
sub('   if(ev==122){',code+'   if(ev==122){')
p.write_text(s,encoding='utf-8');print('v42 GPU source implemented; binaries and parity not yet verified.')
