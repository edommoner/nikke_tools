"""Bounded revival/passive restoration inside the GPU notification DFS."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'research/staging/v34/app/detail_effects.cu';s=p.read_text(encoding='utf-8')
def replace(old,new):
 global s
 assert old in s,old[:110];s=s.replace(old,new)
replace('int down_mask,lost_count[5],lost_definitions[5][NS];','int down_mask,reviving_mask,lost_count[5],lost_definitions[5][NS];double reviving_pct[5];')
replace('s->down_mask=0;for(int who=0;who<5;who++)s->lost_count[who]=0;','s->down_mask=s->reviving_mask=0;for(int who=0;who<5;who++){s->lost_count[who]=0;s->reviving_pct[who]=0;}')
replace('__device__ void sync_hp(const double* c,const double* e,int ne,State* s,int who,int full){double m=', '__device__ void sync_hp(const double* c,const double* e,int ne,State* s,int who,int full){if(s->reviving_mask&(1<<who))return;double m=')
replace('int depth=0;iev[0]=ev;', 'Order revival_queue[32];int revival_actor[32],revival_cursor[32];double revival_pct[32];int depth=0;iev[0]=ev;')
replace('while(depth>=0){\n  // Personal', '''while(depth>=0){
  if(cursor[depth]==0){revival_queue[depth]=0;revival_actor[depth]=-1;revival_cursor[depth]=0;revival_pct[depth]=0;}
  if(revival_actor[depth]>=0){
   int recipient=revival_actor[depth],pushed=0;
   while(revival_cursor[depth]<s->lost_count[recipient]){
    int definition=s->lost_definitions[recipient][revival_cursor[depth]++];const double* q=e+definition*EW;
    if(q[258]!=0||q[62]!=-1)continue;
    int startup=0,passive=0;for(int a=0;a<(int)q[144];a++){const double* d=q+TD+a*TS;if(d[0]==0){startup=1;passive|=(int)d[5];}}
    if(!startup)continue;
    int active=first_instance(e,s,definition);
    if(active>=0){
     if(s->masks[active]<0||(s->masks[active]&(1<<recipient))||lazy_target(q))continue;
     s->masks[active]|=1<<recipient;int shift=0;for(Order raw=s->target_order[active];raw;raw>>=3)shift+=3;
     s->target_order[active]|=Order(recipient+1)<<shift;invalidate(s);continue;
    }
    int caster=(int)q[0];if(s->down_mask&(1<<caster))continue;
    int ok=condition(c,e,ne,s,q,full,0);if(!ok&&(!passive||q[69]>0))continue;
    if(depth==31)return 1;
    // Private activation frame: no startup event counts are incremented. The
    // activation itself still observes target resolution and max_trigger.
    depth++;iev[depth]=47;iwho[depth]=caster;iarg[depth]=definition;icount[depth]=0;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post_row[depth]=-1;queue_arg[depth]=-1;ended_count[depth]=ended_pos[depth]=0;pushed=1;break;
   }
   if(pushed)continue;
   s->hp[recipient]=max_hp(c,e,ne,s,recipient,full)*revival_pct[depth]/100;
   s->reviving_mask&=~(1<<recipient);s->hppct[recipient]=-1;sync_hp(c,e,ne,s,recipient,full);invalidate(s);
   s->hold_release[recipient]=-1;s->reload[recipient]=s->post[recipient]=-1;s->charge_phase[recipient]=0;s->charge_full[recipient]=-1;s->charging[recipient]=0;
   s->ammo[recipient]=full_ammo(c,e,ne,s,recipient,full);s->next[recipient]=t;
   s->lost_count[recipient]=0;revival_actor[depth]=-1;continue;
  }
  if(revival_queue[depth]){
   int recipient=(revival_queue[depth]&7)-1;revival_queue[depth]>>=3;
   if(!(s->down_mask&(1<<recipient)))continue;
   s->down_mask&=~(1<<recipient);s->reviving_mask|=1<<recipient;s->reviving_pct[recipient]=revival_pct[depth];s->hppct[recipient]=revival_pct[depth];
   revival_actor[depth]=recipient;revival_cursor[depth]=0;continue;
  }
  // Personal''')
replace('if(event==28){if(j!=iarg[depth])continue;}else{','if(event==28||event==47){if(j!=iarg[depth])continue;}else{')
replace('if(kind==8){for(Order recipients=', 'if(kind==29){revival_queue[depth]=activation_order;revival_pct[depth]=q[6];continue;}\n  if(kind==8){for(Order recipients=')
replace('// Revive definitions are still rejected by the staged compiler until its FSM is implemented.', '// A lethal hit is logged before down cleanup and subsequent revival callbacks.')
p.write_text(s,encoding='utf-8')
print('Staged bounded revival DFS; not yet compiled or GPU-verified.')
