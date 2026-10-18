"""Apply the autonomous link plan and bounded synchronous delivery to v41."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];stage=ROOT/'research/staging/v41/app'
p=stage/'detail_gpu.py';s=p.read_text(encoding='utf-8')
assert 'heal_split=75' not in s
s=s.replace('heal_overcharge_store=74)','heal_overcharge_store=74,heal_split=75)').replace('0<=r[2]<75','0<=r[2]<76').replace('row[2] in (52,53)','row[2] in (52,53,54)')
p.write_text(s,encoding='utf-8')
p=stage/'detail_effects.cu';s=p.read_text(encoding='utf-8')
def replace(old,new):
    global s
    assert s.count(old)==1,(old[:100],s.count(old));s=s.replace(old,new)
replace('double=0,int=0);','double=0,int=0,double=0);')
anchor='__device__ double take_shield_amp('
assert s.count(anchor)==1
code='''// One link per distinct live member per carrier. Plans are frozen before
// delivery and never use CPU-generated HP, weights or traces.
__device__ Order heal_share_plan(const double* c,const double* e,int ne,State* s,int who,int full,int* weights,int* total){
 for(int n=0;n<5;n++)weights[n]=0;*total=0;
 if(s->down_mask&(1<<who)){weights[who]=1;*total=1;return who+1;}
 int masks[NS],count=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);if(q[1]!=0||q[2]!=75)continue;int mask=0;
  for(int n=0;n<5;n++)if(!(s->down_mask&(1<<n))&&live_shield_recipient(c,e,ne,s,j,n,full))mask|=1<<n;
  if(mask)masks[count++]=mask;
 }
 int connected=1<<who;for(;;){int next=connected;for(int k=0;k<count;k++)if(masks[k]&connected)next|=masks[k];if(next==connected)break;connected=next;}
 for(int k=0;k<count;k++)if(masks[k]&connected)for(int n=0;n<5;n++)if(masks[k]&(1<<n)){weights[n]++;(*total)++;}
 if(!*total){weights[who]=1;*total=1;return who+1;}
 Order order=0;int shift=0;for(int n=0;n<5;n++)if(weights[n]){order|=Order(n+1)<<shift;shift+=3;}return order;
}
'''
s=s.replace(anchor,code+anchor)
replace('int hit_crit){\n unsigned short','int hit_crit,double healing_pool){\n unsigned short')
replace(' int hp_changed[32],hp_owner[32]', ' Order share_queue[32];int share_weight[32][5],share_total[32];double share_pool[32];share_pool[0]=healing_pool;\n int hp_changed[32],hp_owner[32]')
anchor='  if(cursor[depth]==0){revival_queue[depth]=0;'
assert s.count(anchor)==1
code='''  // Private continuation: finish all allocated body heals and synchronous
  // HP edges, then emit exactly the original heal_received notification.
  if(iev[depth]==54){
   if(cursor[depth]==0){
    if(share_pool[depth]>0)share_queue[depth]=heal_share_plan(c,e,ne,s,iwho[depth],full,share_weight[depth],&share_total[depth]);
    else{share_queue[depth]=iwho[depth]+1;share_total[depth]=1;for(int n=0;n<5;n++)share_weight[depth][n]=n==iwho[depth];}
    cursor[depth]=1;
   }
   if(share_queue[depth]){
    int recipient=(share_queue[depth]&7)-1;share_queue[depth]>>=3;
    int weight=share_weight[depth][recipient];double amount=weight==share_total[depth]?share_pool[depth]:share_pool[depth]*weight/share_total[depth];
    apply_storage_body_heal(c,e,ne,s,recipient,amount,full);sync_hp(c,e,ne,s,recipient,full);continue;
   }
   iev[depth]=16;cursor[depth]=0;
  }
'''
s=s.replace(anchor,code+anchor)
replace('if(healrow[depth]>=0){const double* heal=effect(e,s,healrow[depth]);source=(int)heal[0];double amount=heal[6];if(heal[10]>=0)amount*=ref(e,ne,s,source,(int)heal[10]);double base=heal[50]>0?max_hp(c,e,ne,s,source,full):c[recipient*CW+28];apply_storage_body_heal(c,e,ne,s,recipient,base*amount/100*heal_multiplier(c,e,ne,s,recipient,full,source),full);sync_hp(c,e,ne,s,recipient,full);}',
'''double pool=0;if(healrow[depth]>=0){const double* heal=effect(e,s,healrow[depth]);source=(int)heal[0];double amount=heal[6];if(heal[10]>=0)amount*=ref(e,ne,s,source,(int)heal[10]);double base=heal[50]>0?max_hp(c,e,ne,s,source,full):c[recipient*CW+28];pool=base*amount/100*heal_multiplier(c,e,ne,s,recipient,full,source);event=54;}''')
replace('depth++;iev[depth]=event;iwho[depth]=recipient;', 'depth++;share_pool[depth]=pool;iev[depth]=event;iwho[depth]=recipient;')
replace(' apply_storage_body_heal(c,e,ne,s,who,hit*ls/100*heal_multiplier(c,e,ne,s,who,full,who),full);sync_hp(c,e,ne,s,who,full);\n return notify(c,e,ne,s,env,t,16,who,who,full);',
''' double amount=hit*ls/100*heal_multiplier(c,e,ne,s,who,full,who);
 return notify(c,e,ne,s,env,t,54,who,who,full,0,0,amount);''')
p.write_text(s,encoding='utf-8')
print('v41 autonomous sharing source implemented; not built or verified.')
