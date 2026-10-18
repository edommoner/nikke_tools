"""First v34 runtime edit. Revival FSM is still pending; no verified GPU claim."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];stage=ROOT/'research/staging/v34'
def edit(path,changes):
 p=stage/path;s=p.read_text(encoding='utf-8')
 for old,new in changes:
  assert old in s,(path,old[:100]);s=s.replace(old,new)
 p.write_text(s,encoding='utf-8')
edit('app/detail_gpu.py',[
 ("allowed={'end_on_shield_consumed'","allowed={'persist_on_revive','end_on_shield_consumed'"),
 ("q[260]=int(eff.get('end_on_shield_consumed',False))","q[260]=int(eff.get('end_on_shield_consumed',False))\n   if 'persist_on_revive' in eff and type(eff['persist_on_revive']) is not bool:raise UnsupportedDetail('invalid revival persistence flag')\n   q[245]=int(eff.get('persist_on_revive',False))"),
 ("payload['_incoming_state']={n:dict(hp=state[i],cover_hp=state[5+i],cover_max_hp=state[10+i]) for i,n in enumerate(names)}","payload['_incoming_state']={n:dict(hp=state[i],cover_hp=state[5+i],cover_max_hp=state[10+i]) for i,n in enumerate(names)}\n  payload['_down_mask']=int(state[15])"),
 ("if incoming_times:payload['_incoming_frames']=[dict(time=at,state={n:dict(hp=r[i],cover_hp=r[5+i],cover_max_hp=r[10+i]) for i,n in enumerate(names)}) for at,r in zip(incoming_times,logs[incoming_frames_offset:incoming_frames_offset+len(incoming_times)])]","if incoming_times:\n   payload['_incoming_frames']=[dict(time=at,state={n:dict(hp=r[i],cover_hp=r[5+i],cover_max_hp=r[10+i]) for i,n in enumerate(names)}) for at,r in zip(incoming_times,logs[incoming_frames_offset:incoming_frames_offset+len(incoming_times)])]\n   payload['_down_frames']=[dict(time=at,mask=int(r[15])) for at,r in zip(incoming_times,logs[incoming_frames_offset:incoming_frames_offset+len(incoming_times)])]")])
edit('app/detail_effects.cu',[
 ('struct State {','struct State {\n int down_mask,lost_count[5],lost_definitions[5][NS];'),
 ('s->incoming_count=s->incoming_queued=0;','s->down_mask=0;for(int who=0;who<5;who++)s->lost_count[who]=0;s->incoming_count=s->incoming_queued=0;'),
 ('if(kind==1)return (1<<n)-1;','if(kind==1)return ((1<<n)-1)&~s->down_mask;'),
 ('if(!(mask&(1<<who))&&s->cover_hp[who]>0','if(!(s->down_mask&(1<<who))&&!(mask&(1<<who))&&s->cover_hp[who]>0'),
 ('if(q[4]==19){if(who!=(int)q[0])pool[n++]=who;}','if(s->down_mask&(1<<who))continue;\n  if(q[4]==19){if(who!=(int)q[0])pool[n++]=who;}'),
 ('if(rank_def(c,e,ne,s,who)<limit)','if(!(s->down_mask&(1<<who))&&rank_def(c,e,ne,s,who)<limit)'),
 ('if(mask&(1<<who)||q[49]>0','if(s->down_mask&(1<<who)||mask&(1<<who)||q[49]>0'),
 ('mask|=bits;while(child)', 'bits&=~s->down_mask;child=filter_order(child,bits);mask|=bits;while(child)'),
 ('if(ordered)*ordered=mask<0?0:recipient_order(c,e,ne,s,q,mask,full);return mask;','if(mask>=0)mask&=~s->down_mask;\n if(ordered)*ordered=mask<0?0:recipient_order(c,e,ne,s,q,mask,full);return mask;'),
 ('if(k!=owner&&s->burst_stage[k]==1)','if(k!=owner&&!(s->down_mask&(1<<k))&&s->burst_stage[k]==1)'),
 ('if(q[69]<=0||!condition(c,e,ne,s,q,full,0))continue;','if(q[69]<=0||(s->down_mask&(1<<(int)q[0]))||!condition(c,e,ne,s,q,full,0))continue;'),
 ('if(stat(c,e,ne,s,who,28,full)>0)return 0;\n if(!s->started[who])','if(s->down_mask&(1<<who))return 0;\n if(stat(c,e,ne,s,who,28,full)>0)return 0;\n if(!s->started[who])'),
 ('if(rule==1)return 22737;', 'if(rule==1){for(int who=0;who<5;who++)if(!(s->down_mask&(1<<who))){order|=Order(who+1)<<shift;shift+=3;}return order;}'),
 ('if(available&(1<<who)){taunt','if((available&(1<<who))&&!(s->down_mask&(1<<who))){taunt'),
 ('if(!(taunt&(1<<who))){order','if(!(s->down_mask&(1<<who))&&!(taunt&(1<<who))){order'),
 ('rest=31^taunt','rest=(31^taunt)&~s->down_mask'),
 ('Order out=who+1;int shift=3,mask=1<<who;','if(s->down_mask&(1<<who))return 0;Order out=who+1;int shift=3,mask=1<<who;'),
 ('if(!(mask&(1<<member))&&live_shield_recipient','if(!(s->down_mask&(1<<member))&&!(mask&(1<<member))&&live_shield_recipient'),
 ('const double* p=boss_pattern(s,pattern);int pierce=', 'if(s->down_mask&(1<<who))return 0;const double* p=boss_pattern(s,pattern);int pierce='),
 ('// Down/revive is the next runtime dependency. Reject the entire battle until\n // that state transition is implemented; never label a partial result as CUDA.\n if(hp&&s->hp[who]-hp<=0)return code|1024;\n if(hp){s->hp[who]=mx(0,s->hp[who]-hp);sync_hp(c,e,ne,s,who,full);}', '// Revive definitions are still rejected by the staged compiler until its FSM is implemented.\n int fell=hp&&s->hp[who]-hp<=0;\n if(hp){s->hp[who]=mx(0,s->hp[who]-hp);if(!fell)sync_hp(c,e,ne,s,who,full);}'),
 ('if(s->incoming_count>=ILOG)return code|512;','fell=fell&&!(s->down_mask&(1<<who));if(fell)s->hp[who]=0;\n if(s->incoming_count>=ILOG)return code|512;'),
 ('row[10]=0;row[11]=0;return code;', 'row[10]=fell;row[11]=0;\n if(fell){knock_down(e,ne,s,who);code|=notify(c,e,ne,s,env,t,38,who,0,full);int living=31&~s->down_mask;for(int other=0;other<5;other++)if(living&(1<<other))code|=notify(c,e,ne,s,env,t,46,other,0,full);}\n return code;'),
 ('s->burst_stage[i]=override_stage?override_stage:(int)c[i*CW+20];candidate_stage[i]=s->burst_stage[i];','s->burst_stage[i]=override_stage?override_stage:(int)c[i*CW+20];candidate_stage[i]=(s->down_mask&(1<<i))?0:s->burst_stage[i];'),
 ('if(s->phase>=1&&s->phase<=3&&t>=s->action-1e-9){','if(s->phase>=1&&s->phase<=3&&s->action>=1e29){for(int who=0;who<5;who++)if(candidate_stage[who]==s->phase||candidate_stage[who]==4){s->action=t;break;}}\n if(s->phase>=1&&s->phase<=3&&t>=s->action-1e-9){'),
 ('dst[10+who]=s->cover_max[who];}continue;', 'dst[10+who]=s->cover_max[who];}dst[15]=s->down_mask;continue;')])
print('Staged down masks, target filtering and incoming death transition; helper/notify/revival work still pending.')
