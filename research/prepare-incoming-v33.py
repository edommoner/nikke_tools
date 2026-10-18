"""One-shot, exact substitutions from archived v32 into the next ABI."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def edit(path,changes):
 p=ROOT/path;s=p.read_text(encoding='utf-8')
 for old,new in changes:
  assert old in s,(path,old[:90]);s=s.replace(old,new)
 p.write_text(s,encoding='utf-8')
for path in ['app/detail_gpu.py','scripts/build-combat.py','scripts/build-detail-native.py']:
 edit(path,[('detail_boss_buffs_v32','detail_incoming_v33')])
edit('app/detail_gpu.py',[
 ('BH,BLOG,BQ,WEAPONS','BH,BLOG,BQ,ILOG,WEAPONS'),
 ("# These named states", "EXTRA.update(stealth=65,taunt=66,invincible=67,undying=68,received_dmg_split_even=69,cover_hp_pct=70,cover_disabled=71,decoy=72)\n# These named states"),
 ('not 0<=r[2]<65','not 0<=r[2]<73'),
 ("b'detail_state_bytes_v32'","b'detail_state_bytes_v33'"),
 ("b'detail_boss_shape_v32'","b'detail_boss_shape_v33'"),
 ("stat in ('heal_hp_pct','shield_heal_pct') and scaling=='max_hp'","stat in ('cover_heal_pct','heal_hp_pct','shield_heal_pct') and scaling=='max_hp'"),
 ("program=compile_effects(chars,effects)","program=compile_effects(chars,effects)\n program['cover_base_hp']=float(config.get('cover_hp',2000000))\n if any(p.get('kind')=='attack' for p in body.get('enemy',{}).get('patterns',[])):\n  gaps=[{'character':owner,'effect':eff.get('name','?'),'reason':'Incoming model gap: '+eff.get('stat','')} for eff,owner in bm._effects if eff.get('stat') in ('damage_reduction_pct','force_move','cover_def_pct')]\n  if gaps:raise UnsupportedDetail(gaps)"),
 ("if any(status):raise RuntimeError('GPU detail capacity or target cache exceeded; result rejected: '+str(list(status)))","if any(v&1024 for v in status):raise UnsupportedDetail('A lethal incoming hit requires down/revive handling that is still being ported; GPU result rejected')\n  if any(status):raise RuntimeError('GPU detail capacity or target cache exceeded; result rejected: '+str(list(status)))"),
 ("for seed in seeds for v in random.Random(seed).getstate()[1]","for seed in seeds for rng_seed in (seed,0) for v in random.Random(rng_seed).getstate()[1]")])
edit('app/detail_effects.cu',[
 ('#define BW 80','#define BW 96'),('#define WB (8+NE)','#define WB (16+NE)'),
 ('#define BQ 1024','#define BQ 1024\n#define ILOG 4096'),
 ('detail_state_bytes_v32','detail_state_bytes_v33'),('detail_boss_shape_v32','detail_boss_shape_v33'),('detail_boss_buffs_v32','detail_incoming_v33'),
 ('struct State {','struct State {\n MTState boss_rng;double cover_hp[5],cover_max[5],cover_base;int incoming_count,incoming_shots[BP],incoming_queue[BQ],incoming_queued;double incoming_log[ILOG][12];'),
 ('s->rng.words[k]=initial_rng[id*625+k]','s->rng.words[k]=initial_rng[id*1250+k]'),
 ('s->rng.index=(int)initial_rng[id*625+624];','s->rng.index=(int)initial_rng[id*1250+624];for(int k=0;k<624;k++)s->boss_rng.words[k]=initial_rng[id*1250+625+k];s->boss_rng.index=(int)initial_rng[id*1250+1249];s->incoming_count=s->incoming_queued=0;for(int k=0;k<BP;k++)s->incoming_shots[k]=0;s->cover_base=worlds[id*WP+267]>0?worlds[id*WP+264]:2000000;for(int k=0;k<5;k++)s->cover_hp[k]=s->cover_max[k]=s->cover_base;'),
 ('s->boss_active[i]=1;s->boss_start[i]=t;','s->boss_active[i]=1;s->boss_start[i]=t;s->incoming_shots[i]=0;'),
 ('double defense=s->boss_base_def;','s->incoming_queued=0;for(int i=0;i<s->boss_count;i++){const double* p=boss_pattern(s,i);if(p[0]!=6)continue;while(s->boss_active[i]&&s->incoming_shots[i]<p[87]&&t>=s->boss_start[i]+s->incoming_shots[i]*p[88]-1e-9){if(s->incoming_queued>=BQ)return 512;s->incoming_queue[s->incoming_queued++]=i;s->incoming_shots[i]++;}}\n double defense=s->boss_base_def;'),
 ('if(stimulus&&stimulus[2]==1)', 'if(s->boss_count){sync_cover(c,e,ne,s,*full);code|=incoming_attacks(c,e,ne,s,env,t,*full);if(code)return code;}\n if(stimulus&&stimulus[2]==1)'),
 ('if(kind==7){if(q[6]!=0){queue[depth]=activation_order;queue_event[depth]=17;queue_arg[depth]=-1;healrow[depth]=-1;}continue;}', 'if(kind==7){if(q[6]!=0){Order kept=0;int shift=0;for(Order raw=activation_order;raw;raw>>=3){int who=(raw&7)-1;if(s->cover_hp[who]<=0)continue;double base=q[50]>0?max_hp(c,e,ne,s,owner,full):s->cover_max[who];s->cover_hp[who]=mn(s->cover_max[who],s->cover_hp[who]+base*q[6]/100);kept|=Order(who+1)<<shift;shift+=3;}queue[depth]=kept;queue_event[depth]=17;queue_arg[depth]=-1;healrow[depth]=-1;}continue;}'),
 ('if(phase==4&&q[1]==0&&q[2]==45', 'if(phase==4&&q[1]==0&&q[2]==72&&!post_lazy[depth]&&post_rawmask[depth]){r=first_instance(e,s,s->definition[r]);if(r>=0)build_decoy(c,e,ne,s,r,full);}\n   if(phase==4&&q[1]==0&&q[2]==45'),
 ('if(ev==116){','if(ev==117){for(int k=0;k<OW;k++)dst[k]=0;dst[12]=s->incoming_count;if(arg<s->incoming_count)for(int k=0;k<12;k++)dst[k]=s->incoming_log[arg][k];continue;}\n   if(ev==118){for(int k=0;k<OW;k++){int word=arg*OW+k;dst[k]=word<624?s->boss_rng.words[word]:word==624?s->boss_rng.index:0;}continue;}\n   if(ev==119){for(int k=0;k<OW;k++)dst[k]=0;for(int who=0;who<5;who++){dst[who]=s->hp[who];dst[5+who]=s->cover_hp[who];dst[10+who]=s->cover_max[who];}continue;}\n   if(ev==116){')])
print('v33 ABI and incoming scheduling scaffold prepared; device runtime still to be added before build.')
