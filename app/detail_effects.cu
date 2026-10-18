// Detailed effect-state interpreter. Never skips an unsupported source construct.
// Event input is a stimulus program, not a CPU-computed buff/damage replay.
#define NE 256
#define MASK_WORDS ((NE+31)/32)
#define B3_MASK 270
#define REDUCER_MASK 278
#define NS 512
#define EW 344
#define RAMP_STEPS 64
#define AG 32
#define AT 128
#define PS 64
#define SS 32
#define EXTEND_MASK 286
#define EN 68
#define BP 32
#define BL 8
#define BW 96
#define BH 512
#define BLOG 4096
#define BQ 1024
#define ILOG 4096
#define WB (16+NE)
#define WA (WB+BP*BW)
#define WORLD_ACTORS 128
#define ACTOR_WORDS 8
#define WP (WA+1+WORLD_ACTORS*ACTOR_WORDS)
#define CW 169
#define ST 32
#define OW 48
#define EVS 8
#define EVENT_KINDS 128
#define INTEREST_DAMAGE_ACCUM 4
#define INTEREST_EXCLUSIVE_AMMO 8
#define INTEREST_TARGET_COUNTER 16
#define INTEREST_TARGET_CONTEXT 32
#define INTEREST_ENEMY_FIELDS 64
#define TD 145
#define TS 7
__device__ double mx(double a,double b){return a>b?a:b;}
__device__ double mn(double a,double b){return a<b?a:b;}
// BEGIN GENERATED WORLD CONDITIONS
// Generated from world_condition_specs.py; do not hand-edit.
#define WORLD_COUNT_ABOVE 40
#define WORLD_COUNT_BELOW 41
#define WORLD_TARGET_BOSS 42
#define WORLD_TARGET_ADD 43
struct TargetRef {int kind,identity,generation;};
__device__ int world_count_condition(int type,int count,double threshold){
 return type==WORLD_COUNT_ABOVE?count>=threshold:count<=threshold;
}
__device__ int world_target_condition(int type,TargetRef target){
 return type==WORLD_TARGET_ADD?target.kind==5:(target.kind==0||target.kind==1);
}
__device__ int inherits_event_target(int event){return event==8||event==58||event==47||event==55||event==56||event==57||event==61;}
// END GENERATED WORLD CONDITIONS
// BEGIN GENERATED ENEMY RECIPIENTS
// Generated from enemy_recipient_specs.py; do not hand-edit.
#define ENEMY_SELECT_LEGACY_BODY 0
#define ENEMY_SELECT_CURRENT 1
#define ENEMY_SELECT_BOSS 2
#define ENEMY_SELECT_ALL 3
#define ENEMY_SELECT_OTHER 4
__device__ TargetRef logical_enemy_ref(TargetRef a){return a.kind==1?TargetRef{0,0,1}:a;}
__device__ int enemy_wire(TargetRef a){a=logical_enemy_ref(a);return a.kind+8*a.identity;}
__device__ int same_enemy_ref(TargetRef a,TargetRef b){a=logical_enemy_ref(a);b=logical_enemy_ref(b);return enemy_wire(a)==enemy_wire(b)&&a.generation==b.generation;}
// END GENERATED ENEMY RECIPIENTS
struct EnemyFieldRef {int wire,generation;};
typedef unsigned long long Order;
struct MTState { unsigned int words[624]; int index; };
__device__ unsigned int mt_next(MTState* s) {
 if(s->index>=624){
  for(int i=0;i<624;i++){
   unsigned int y=(s->words[i]&0x80000000u)|(s->words[(i+1)%624]&0x7fffffffu);
   s->words[i]=s->words[(i+397)%624]^(y>>1)^((y&1u)?0x9908b0dfu:0u);
  }
  s->index=0;
 }
 unsigned int y=s->words[s->index++];
 y^=y>>11;y^=(y<<7)&0x9d2c5680u;y^=(y<<15)&0xefc60000u;y^=y>>18;
 return y;
}
__device__ unsigned int mt_bits(MTState* s,int bits){return bits?mt_next(s)>>(32-bits):0u;}
__device__ unsigned int mt_below(MTState* s,unsigned int n){
 int bits=0;for(unsigned int v=n;v;v>>=1)bits++;
 unsigned int r;do{r=mt_bits(s,bits);}while(r>=n);return r;
}

// BEGIN GENERATED IMPACT
// Generated from impact_specs.py; do not hand-edit.
#define ACTOR_BODY 0
#define ACTOR_PART 1
#define ACTOR_PROJECTILE 2
#define ACTOR_HP_SHIELD 3
#define ACTOR_HIT_SHIELD 4
#define ACTOR_ADD 5
#define HIT_WEAPON 0
#define HIT_SKILL 1
#define HIT_DOT 2
#define HIT_EXTERNAL 3
#define OUTCOME_MISS 0
#define OUTCOME_BLOCKED 1
#define OUTCOME_DAMAGING 2
struct Impact { int attacker,kind,identity,generation,family,outcome,attack_id; double damage,credit; };
// END GENERATED IMPACT

#define RC 1024
struct State {
 double add_dealt[WORLD_ACTORS],add_total[5],add_overkill,add_last_took;
 int add_hits[WORLD_ACTORS],add_gone[WORLD_ACTORS],add_order[BP],add_clock,add_pending_deaths,add_live_snapshot;
 int ag_active[AG],ag_owner[AG],ag_id[AG],ag_epoch[AG],ag_mask[AG],ag_count[AG],ag_n,ag_clock;
 int ag_kind[AG][AT],ag_identity[AG][AT],ag_generation[AG][AT];
 int ag_plan_count[5],ag_plan[5][AT];
 double ag_open[AG];
 int ramp_heap_n,ramp_heap[NE],ramp_heap_pos[NE];
 int ramp_active,ramp_clock,ramp_on[NE],ramp_count[NE],ramp_index[NE],ramp_epoch[NE],ramp_uid[NE],ramp_seq[NE];double ramp_start[NE];
 int source_count,source_owner_count,source_owner_order[5],source_owner[PS],source_name[PS],source_slots[PS],source_epoch[PS],source_legacy[PS];
 double source_expiry[PS][SS],source_next[PS],source_base[PS],source_step[PS];
 unsigned char source_index[5][NE];
 unsigned short event_offsets[EVENT_KINDS+1],event_definitions[NE*EVS];
 int counter_uid[NS],counter_epoch[NS],counter_done[NS],counter_clock,counter_completed,counter_error;
 double counter_credit[NS],counter_end[NS],counter_last[10];
 int dead_count,dead_kind[NS],dead_identity[NS],dead_generation[NS];
 int impact_enabled;double impact_summary[OW];
 int land_family[1024];
 double damage_accum_last[NE];
 double named_skill_crit[5][NE];
 int named_hit_interest[NE];
 double heal_store_expiry[NS];
 int hp_interest,hp_pending,in_hp_edge,hp_edge_error;double hp_edge_prev,hp_edge_new;
 int hp_log_enabled,hp_log_count;double hp_log[1024][3];
 int down_mask,reviving_mask,lost_count[5],lost_definitions[5][NS];double reviving_pct[5];
 MTState boss_rng;double cover_hp[5],cover_max[5],cover_base;int incoming_count,incoming_shots[BP],incoming_queue[BQ],incoming_queued;double incoming_log[ILOG][12];
 unsigned int boss_release,boss_apply;int boss_dispelled[BP];double boss_base_def;
 const double* boss_program;double world[EN],boss_base_core,boss_distance,boss_start[BP],boss_end_at[BP+1][BH],boss_log_at[BLOG];
 int boss_count,boss_weapon_mask,boss_active[BP],boss_opens[BP],boss_after[BP][BL],boss_until[BP][BL],boss_end_n[BP+1],boss_end_kind[BP+1][BH],boss_log_n,boss_log_node[BLOG],boss_log_kind[BLOG],boss_event_n,boss_event_code[BQ],boss_event_arg[BQ];
 int event_interest;
 double part_dealt[32],part_at[32],shot_part[5],land_part[1024],now_part[NE];
 int part_dead[32],part_hits[32],part_min,part_pending,shot_reach[5],land_reach[1024],now_reach[NE];
 double immune_used[6][NE];
 int random_special_present,random_special_valid[5],random_special_mask[5][NS];double random_special_time[5];
 MTState rng;int random_error,random_cache_count,random_owner[RC],random_key[RC],random_mask[RC];double random_time[RC];Order random_order[RC];
 int burst_damage_count,burst_damage_rows[NE],burst_damage_hits[NE];
 double burst_damage_mag[NE];
 int burst_stage[5],burst_pending[5],burst_pending_present[5],reenter_slot,reenter_done;
 double burst_amount;int burst_charging;
 int camera_lens,query_camera[5],ctrl_preempt[5],normal_landed_mask;double query_camera_at[5];
 int charging[5],hold_fired[5][NE],ctrl_owner,camera_mask,ctrl_prev[5],ctrl_prio[5],ctrl_seq[5],hold_close[5],hold_kind[5],tap[5],force_full[5],cycle_users[3];
 double charge_full[5],hold_release[5],hold_anchor[5],hold_reentry[5],hold_start[5],last_full[5],tap_hold[5],tap_charge[5],tap_release[5],tap_post[5];
 int mode_shots[5],mode_restored[5],reload_in_mode[5];double mode_ammo[5],charge_post[5];
 int weapon_context[5],mode_started[5];double mode_ready[5];int gauge_present[5][NE];double gauges[5][NE],gauge_cap[5][NE];
 double when,timer_at[NE],timer_end[NE];int timer_active[NE],timer_seq[NE],entry_seq[NS],timer_clock,entry_clock,dot_present[NS],bullets[NS][6],bullet_stacks[NS][6],bullet_left[NS];
 double heal_charge_last[5][NE];
 int shield_present[NS];double shield_current[NS][5],shield_capacity[NS][5],last_shield_result;
 int shield_mask[NS],hits[5],activations[NE];double hit_unit[5],frac[5][4];int cast_mask,heal_source,ammo_query_mask,auto_reload[5],lazy_dirty,squad_mode,land_count,now_count,land_owner[1024],now_owner[NE];double land_damage[1024],now_damage[NE];double cached[5][63];double hp[5],hppct[5],hit[5];int pending[NE];unsigned int excluded[MASK_WORDS];unsigned long long valid[5];int cached_full;
 double chance_acc[NE],noncore_acc[NE];double stacks[NS],end[NS],capture[NS],period_at[NE],period_prev[NE],activated[NS];int period_initialized[NE];int masks[NS],count[NE][EVS];Order target_order[NS];
 int mags_initialized,compensated_sums;int definition[NS],slots,slot_next[NS],slot_head,slot_tail,alive[NS],bullet_initialized[NS],runtime_cond[NS];
 unsigned short event_slots[32][NS];int event_stacks[32][NS];
 int mode[5],prev_mode[5],started[5],shots[5],charge_phase[5]; double charge_start[5],ready[5],cd_applied[5]; int phase,cycle,fb_caster,wait_mask,log_count,log_who[256],log_event[256]; double action,opened,gauge,fb_end,fb_cast_t,log_t[256]; double mode_end[5],total[5],warm[5],last[5],inter[5],next[5],ammo[5],reload[5],post[5];
 double boss_frame_at;
 TargetRef condition_target;
 TargetRef enemy_recipient[NS];
 EnemyFieldRef field_targets[32][WORLD_ACTORS];
 int timer_epoch[NE];TargetRef control_aim[5];int control_aim_mask;
 int instant_next[NE],instant_head,instant_tail;
};
// Export the compiler layout; the host never guesses CUDA struct padding.
__device__ int actor_dead(State*,int,int,int);
__device__ int enemy_field_matches(State*,int);
extern "C" __device__ __constant__ unsigned int detail_state_bytes_v42=sizeof(State);
extern "C" __device__ __constant__ unsigned int detail_boss_shape_v42[8]={BP,BL,BW,BH,BLOG,BQ,WB,WP};
extern "C" __device__ __constant__ unsigned int detail_event_shape_v55[5]={EVENT_KINDS,NE,EVS,TD,TS};
extern "C" __device__ __constant__ unsigned int detail_source_shape_v57[4]={PS,SS,EW,NE};
static_assert(PS<256,"Periodic source handles must fit the direct index");
__device__ int source_find(State* s,int owner,int name){
 if(!s->source_count||owner<0||owner>=5||name<0||name>=NE)return -1;
 return (int)s->source_index[owner][name]-1;
}
__device__ int source_population(State* s,int at,double t){int count=0;for(int k=0;k<s->source_slots[at];k++)count+=s->source_expiry[at][k]>t;return count;}
__device__ double source_interval(State* s,int at,int count){return s->source_base[at]*(1-s->source_step[at]/100*(count-1));}
__device__ int source_refresh(State* s,const double* q,double t){
 int owner=(int)q[0],name=(int)q[304],at=source_find(s,owner,name);
 if(at<0){if(s->source_count>=PS)return 4096;
  // No-source squads never touch this table. First allocation resets it once;
  // expired resources keep their identity, so a present zero stays present.
  if(!s->source_count)for(int who=0;who<5;who++)for(int key=0;key<NE;key++)s->source_index[who][key]=0;
  at=s->source_count++;s->source_owner[at]=owner;s->source_name[at]=name;s->source_epoch[at]=0;s->source_index[owner][name]=at+1;
  int found=0;for(int k=0;k<s->source_owner_count;k++)if(s->source_owner_order[k]==owner)found=1;
  if(!found)s->source_owner_order[s->source_owner_count++]=owner;
 }
 s->source_epoch[at]++;s->source_slots[at]=(int)q[305];s->source_base[at]=q[306];s->source_step[at]=q[307];s->source_legacy[at]=(int)q[137];
 for(int k=0;k<s->source_slots[at];k++)s->source_expiry[at][k]=q[308+k]<0?1e30:t+q[308+k];
 s->source_next[at]=t+source_interval(s,at,s->source_slots[at]);return 0;
}
__device__ int earlier_trigger_event(const double* q,int at){
 for(int prior=0;prior<at;prior++)if(q[TD+prior*TS]==q[TD+at*TS])return 1;
 return 0;
}
__device__ void build_event_index(const double* e,int ne,State* s){
 int cursor[EVENT_KINDS];for(int event=0;event<EVENT_KINDS;event++)cursor[event]=0;
 for(int j=0;j<ne;j++){const double* q=e+j*EW;for(int at=0;at<(int)q[144];at++)if(!earlier_trigger_event(q,at))cursor[(int)q[TD+at*TS]]++;}
 s->event_offsets[0]=0;
 for(int event=0;event<EVENT_KINDS;event++){s->event_offsets[event+1]=s->event_offsets[event]+cursor[event];cursor[event]=s->event_offsets[event];}
 for(int j=0;j<ne;j++){const double* q=e+j*EW;for(int at=0;at<(int)q[144];at++)if(!earlier_trigger_event(q,at))s->event_definitions[cursor[(int)q[TD+at*TS]]++]=j;}
}
// Neumaier summation for Python 3.12+ builtin sum() over floating values.
// Other stats still follow the upstream's explicit sequential += operations.
struct FloatSum {double total,correction;};
__device__ void add_sum(State* s,FloatSum* acc,double term){
 double combined=acc->total+term;
 if(s->compensated_sums)acc->correction+=fabs(acc->total)>=fabs(term)?(acc->total-combined)+term:(term-combined)+acc->total;
 acc->total=combined;
}
__device__ double finish_sum(FloatSum acc){return acc.correction!=0&&isfinite(acc.correction)?acc.total+acc.correction:acc.total;}
// Active slots refer to immutable definitions. Listener counters, trigger budgets
// and periodic clocks remain definition keyed; lifetime state is slot keyed.
__device__ const double* effect(const double* e,State* s,int slot){return e+s->definition[slot]*EW;}
__device__ void new_entry(State* s,int slot){
 s->enemy_recipient[slot]={ACTOR_BODY,0,1};
 s->entry_seq[slot]=++s->entry_clock;s->alive[slot]=1;
 if(slot==s->slot_tail)return;
 int before=-1;for(int k=s->slot_head;k>=0;k=s->slot_next[k]){if(k==slot)break;before=k;}
 if(before<0)s->slot_head=s->slot_next[slot];else s->slot_next[before]=s->slot_next[slot];
 s->slot_next[s->slot_tail]=slot;s->slot_next[slot]=-1;s->slot_tail=slot;
}
__device__ int first_instance(const double* e,State* s,int definition){
 for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[58]==e[definition*EW+58])return k;
 return -1;
}
__device__ int fresh_slot(State* s,int ne,int definition){
 int j=definition;
 if(s->alive[j]){
  j=-1;for(int k=ne;k<s->slots;k++)if(!s->alive[k]&&s->definition[k]==definition){j=k;break;}
  if(j<0){if(s->slots>=NS)return -1;j=s->slots++;s->slot_next[s->slot_tail]=j;s->slot_next[j]=-1;s->slot_tail=j;}
 }
 s->heal_store_expiry[j]=-1;s->definition[j]=definition;s->alive[j]=0;s->stacks[j]=0;s->end[j]=-1;s->capture[j]=-1;s->shield_mask[j]=0;s->shield_present[j]=0;for(int p=0;p<5;p++)s->shield_current[j][p]=s->shield_capacity[j][p]=0;s->masks[j]=0;s->target_order[j]=0;s->dot_present[j]=0;s->bullet_left[j]=-1;s->bullet_initialized[j]=0;s->runtime_cond[j]=0;
 for(int k=0;k<6;k++)s->bullets[j][k]=s->bullet_stacks[j][k]=0;
 return j;
}
__device__ int stack_immune_ref(const double* e,State* s,int who,TargetRef target){
 for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[211]>0&&s->masks[k]>=0&&(s->masks[k]&(1<<who))&&(who<5||!(s->event_interest&INTEREST_ENEMY_FIELDS)||same_enemy_ref(s->enemy_recipient[k],target)))return 1;
 return 0;
}
__device__ int stack_immune(const double* e,State* s,int who){return stack_immune_ref(e,s,who,s->condition_target);}
__device__ void invalidate(State* s){for(int i=0;i<5;i++){s->valid[i]=0;s->random_special_valid[i]=0;s->query_camera_at[i]=-1;}}
__device__ void set_condition_target(State* s,TargetRef target){
 TargetRef old=s->condition_target;
 if(old.kind!=target.kind||old.identity!=target.identity||old.generation!=target.generation){s->condition_target=target;invalidate(s);}
}
struct TargetScope {
 State* state;TargetRef previous;int active;
 __device__ TargetScope(State* s,int track):state(s),active(track){if(active)previous=s->condition_target;}
 __device__ ~TargetScope(){if(active)set_condition_target(state,previous);}
};
// get_buffs() caches a complete dictionary for one query time/generation.
// Camera ownership does not invalidate it in CPU; preserve that query snapshot
// even when only some of the GPU's scalar stat keys have been evaluated yet.
__device__ void camera_query(State* s,int who){if(s->query_camera_at[who]!=s->when){if(s->query_camera[who]!=s->camera_mask)s->valid[who]=0;s->query_camera[who]=s->camera_mask;s->query_camera_at[who]=s->when;}}
__device__ int lazy_target(const double* q){return q[4]>=5&&q[4]<=7||q[4]==14||q[4]==15||q[4]==16||q[4]==19;}
__device__ int marker_recipient(const double* e,State* s,int who,int flag){
 for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&((int)effect(e,s,k)[213]&flag)&&s->masks[k]>=0&&(s->masks[k]&(1<<who))&&(who<5||enemy_field_matches(s,k)))return 1;
 return 0;
}
__device__ int raw_stunned(const double* e,State* s,int who){
 if(marker_recipient(e,s,who,2))return 0;
 for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[1]==0&&effect(e,s,k)[2]==28&&s->masks[k]>=0&&(s->masks[k]&(1<<who))&&(who<5||enemy_field_matches(s,k)))return 1;
 return 0;
}
// State membership is a snapshot of already resolved active recipients. Zero
// stacks and entries awaiting this frame's expiry pass still count as CPU does.
__device__ int state_recipient(const double* e,State* s,int who,int name,int flags){
 for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[3]==name&&s->masks[k]>=0&&(s->masks[k]&(1<<who))&&(who<5||enemy_field_matches(s,k)))return 1;
 if(who>=5)return 0;
 int mode=s->mode[who];if(flags==1)return mode>=0;
 if(mode>=0)return effect(e,s,mode)[3]==name;
 return flags==2;
}
__device__ int target_basic(const double* e,const double* q,int n,State* s){
 int c=(int)q[0],kind=(int)q[4],arg=(int)q[5],mask=0;
 if(kind==0)return 1<<c;
 if(kind==21){for(int pick=0;pick<arg;pick++){int best=-1;double fraction=0;for(int who=0;who<n;who++)if(!(s->down_mask&(1<<who))&&!(mask&(1<<who))&&s->cover_hp[who]>0&&s->cover_max[who]>0){double v=s->cover_hp[who]/s->cover_max[who];if(best<0||v<fraction){best=who;fraction=v;}}if(best<0)break;mask|=1<<best;}return mask;}
 if(kind==1)return ((1<<n)-1)&~s->down_mask;
 if(kind==11)return s->cast_mask&(int)q[48];
 if(kind==18){for(int j=0;j<n;j++)if(((int)q[48]&(1<<j))&&marker_recipient(e,s,j,1))mask|=1<<j;return mask;}
 if(kind==12||kind==13){for(int j=0;j<n;j++)if(state_recipient(e,s,j,arg,(int)q[223])==(kind==12))mask|=1<<j;return mask;}
 if(kind==9)return s->cast_mask;
 if(kind==10)return ((1<<n)-1)^s->cast_mask;
 if(kind==2){for(int j=c+1;j<n&&j<=c+arg;j++)mask|=1<<j;return mask;}
 if(kind==3){mask=1<<c;int used=0;if(c>0&&used<arg){mask|=1<<(c-1);used++;}if(c+1<n&&used<arg)mask|=1<<(c+1);return mask;}
 if(kind==24){int used=0;if(q[141]>0){for(Order raw=(Order)q[140];raw&&used<arg;raw>>=3){int who=(raw&7)-1;if(who>=0&&who<n&&((int)q[48]&(1<<who))&&!(s->down_mask&(1<<who))){mask|=1<<who;used++;}}}else for(int who=0;who<n&&used<arg;who++)if(((int)q[48]&(1<<who))&&!(s->down_mask&(1<<who))){mask|=1<<who;used++;}return mask;}
 if(lazy_target(q)||kind==20||kind==22||kind==23||kind==25)return -1;
 if(kind==8)return (int)q[48];
 if(kind==4)return 1<<5; // Single enemy sentinel.
 return 0;
}
__device__ double ref(const double* e,int ne,State* s,int owner,int name){
 if(name>=0&&name<NE&&s->gauge_present[owner][name])return (long long)s->gauges[owner][name];
 int source=source_find(s,owner,name);if(source>=0)return source_population(s,source,s->when);
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if((int)effect(e,s,j)[0]==owner&&(int)effect(e,s,j)[3]==name&&(s->alive[j]))return s->stacks[j];
 return 0;
}
__device__ int ref_present(const double* e,State* s,int owner,int name){
 if(s->gauge_present[owner][name]||source_find(s,owner,name)>=0)return 1;
 for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[0]==owner&&effect(e,s,k)[3]==name)return 1;return 0;
}
// Bounded indexed heap: one current node per immutable staged definition.
__device__ __noinline__ int ramp_before(const double* e,State* s,int a,int b){
 double x=s->ramp_start[a]+(s->ramp_index[a]+1)*e[a*EW+340],y=s->ramp_start[b]+(s->ramp_index[b]+1)*e[b*EW+340];
 return x<y||x==y&&s->ramp_seq[a]<s->ramp_seq[b];
}
__device__ void ramp_swap(State* s,int a,int b){int x=s->ramp_heap[a],y=s->ramp_heap[b];s->ramp_heap[a]=y;s->ramp_heap[b]=x;s->ramp_heap_pos[x]=b;s->ramp_heap_pos[y]=a;}
__device__ __noinline__ void ramp_up(const double* e,State* s,int p){while(p>0){int parent=(p-1)/2;if(!ramp_before(e,s,s->ramp_heap[p],s->ramp_heap[parent]))break;ramp_swap(s,p,parent);p=parent;}}
__device__ __noinline__ void ramp_down(const double* e,State* s,int p){while(2*p+1<s->ramp_heap_n){int child=2*p+1;if(child+1<s->ramp_heap_n&&ramp_before(e,s,s->ramp_heap[child+1],s->ramp_heap[child]))child++;if(!ramp_before(e,s,s->ramp_heap[child],s->ramp_heap[p]))break;ramp_swap(s,p,child);p=child;}}
__device__ __noinline__ void ramp_remove(const double* e,State* s,int row){
 int p=s->ramp_heap_pos[row];if(p<0)return;s->ramp_heap_pos[row]=-1;int last=s->ramp_heap[--s->ramp_heap_n];
 if(p==s->ramp_heap_n)return;s->ramp_heap[p]=last;s->ramp_heap_pos[last]=p;
 if(p>0&&ramp_before(e,s,last,s->ramp_heap[(p-1)/2]))ramp_up(e,s,p);else ramp_down(e,s,p);
}
__device__ __noinline__ int ramp_insert(const double* e,State* s,int row){
 if(s->ramp_heap_n>=NE||s->ramp_heap_pos[row]>=0)return 8;int p=s->ramp_heap_n++;s->ramp_heap[p]=row;s->ramp_heap_pos[row]=p;ramp_up(e,s,p);return 0;
}
// Immutable configured identity; live presence comes from its source pool.
// Ownership never decides which actors a simultaneous-target clause counts.
__device__ int world_actor_index(State* s,int kind,int identity){
 const double* table=s->boss_program+WA;int count=(int)table[0];
 // The validated canonical prefix is body0, then contiguous fixed parts.
 // This avoids scanning a configured table for every body/part landing.
 int index=kind==ACTOR_BODY&&identity==0?0:kind==ACTOR_PART&&identity>=0?identity+1:-1;
 if(kind==ACTOR_ADD)index=s->boss_program[266]>0&&identity>=0?(int)s->boss_program[266]+identity:-1;
 if(index<0||index>=count)return -1;
 const double* row=table+1+index*ACTOR_WORDS;return row[0]==kind&&row[1]==identity?index:-1;
}
__device__ int world_actor(State* s,int kind,int identity,int* generation,int* alive,int* parent_kind,int* parent_id){
 int index=world_actor_index(s,kind,identity);if(index<0)return 0;
 const double* row=s->boss_program+WA+1+index*ACTOR_WORDS;
 *parent_kind=(int)row[5];*parent_id=(int)row[6];
 if(row[2]==0){*generation=1;*alive=1;return 1;}
 if(row[2]==1){int p=(int)row[4];if(p>=(int)s->world[2])return 0;*generation=1;*alive=!s->part_dead[p];return 1;}
 if(row[2]==2){int run=(int)row[3];*generation=s->boss_opens[run];*alive=s->boss_active[run]&&!s->add_gone[index];return *generation>0;}
 return 0;
}
// Periodic instants sample explicit control input at fire time. A dead/stale
// aim falls back to the body; it never silently binds the next actor generation.
__device__ TargetRef sample_control_aim(State* s,int owner){
 TargetRef body={ACTOR_BODY,0,1};
 if(owner<0||owner>=5||!(s->control_aim_mask&(1<<owner)))return body;
 TargetRef aim=s->control_aim[owner];if(aim.kind==ACTOR_BODY&&aim.identity==0&&aim.generation==1)return body;
 int generation=0,alive=0,parent_kind=-1,parent_id=-1;
 if(world_actor(s,aim.kind,aim.identity,&generation,&alive,&parent_kind,&parent_id)&&alive&&generation==aim.generation)return aim;
 return TargetRef{ACTOR_BODY,0,1};
}
// Keep source registration order once; inactive nodes can be reused safely.
__device__ int index_instant_timer(State* s,int row){
 if(row==s->instant_tail)return 0;
 if(s->instant_next[row]!=-2){
  int before=-1,at=s->instant_head,steps=0;
  while(at>=0&&at!=row&&steps++<NE){before=at;at=s->instant_next[at];}
  if(at!=row)return 8;
  if(before<0)s->instant_head=s->instant_next[row];else s->instant_next[before]=s->instant_next[row];
 }
 if(s->instant_tail<0)s->instant_head=row;else s->instant_next[s->instant_tail]=row;
 s->instant_next[row]=-1;s->instant_tail=row;return 0;
}
struct TimerSnapshot {int count,row[NE],epoch[NE];};
// Capture every registration before callbacks. A callback can replace a later
// registration without letting its old snapshot execute or advance the new one.
__device__ void capture_timers(const double* e,State* s,int ne,int damage,TimerSnapshot* out){
 out->count=0;
 if(!damage){
  for(int j=s->instant_head;j>=0;j=s->instant_next[j])if(s->timer_active[j]){int at=out->count++;out->row[at]=j;out->epoch[at]=s->timer_epoch[j];}
  return;
 }
 for(int j=0;j<ne;j++)if(s->timer_active[j]&&effect(e,s,j)[1]==3){
  int at=out->count++;while(at>0&&s->timer_seq[j]<s->timer_seq[out->row[at-1]]){out->row[at]=out->row[at-1];out->epoch[at]=out->epoch[at-1];at--;}
  out->row[at]=j;out->epoch[at]=s->timer_epoch[j];
 }
}
__device__ int timer_owned(State* s,int row,int epoch){return s->timer_active[row]&&s->timer_epoch[row]==epoch;}
__device__ void advance_timer(State* s,int row,int epoch,double interval){if(timer_owned(s,row,epoch))s->timer_at[row]+=interval;}
// Capture once before children run; later waves can differ from configuration order.
__device__ int capture_enemy_receivers(State* s,int depth){
 const double* table=s->boss_program+WA;int count=0,order[WORLD_ACTORS];
 for(int i=0;i<(int)table[0];i++){const double* row=table+1+i*ACTOR_WORDS;int kind=(int)row[0],identity=(int)row[1];if(kind!=ACTOR_BODY&&kind!=ACTOR_ADD)continue;
  int generation=0,alive=0,parent_kind=-1,parent_id=-1;
  if(!world_actor(s,kind,identity,&generation,&alive,&parent_kind,&parent_id)||!alive)continue;
  if(count==WORLD_ACTORS)return -8;
  int key=kind==ACTOR_BODY?0:s->add_order[(int)row[3]]+(int)row[4]+1,at=count++;
  while(at>0&&order[at-1]>key){order[at]=order[at-1];s->field_targets[depth][at]=s->field_targets[depth][at-1];at--;}
  order[at]=key;s->field_targets[depth][at]={kind+8*identity,generation};
 }
 return count;
}
__device__ TargetRef captured_field_target(State* s,int depth,int pos){EnemyFieldRef ref=s->field_targets[depth][pos];return TargetRef{ref.wire%8,ref.wire/8,ref.generation};}
__device__ int enemy_field_matches(State* s,int slot){
 if(!(s->event_interest&INTEREST_ENEMY_FIELDS))return 1;
 TargetRef target=logical_enemy_ref(s->condition_target);
 if(!same_enemy_ref(s->enemy_recipient[slot],target))return 0;
 if(target.kind==ACTOR_BODY)return 1;
 int generation,alive,parent_kind,parent_id;
 return world_actor(s,target.kind,target.identity,&generation,&alive,&parent_kind,&parent_id)&&generation==target.generation&&alive;
}
// Shared recipient projection for targeted removal, extension and mutation.
// Global name removal deliberately bypasses this current-world projection.
__device__ int selected_field_mask(State* s,int slot,const double* operation,int mask){
 int selected=s->masks[slot]<0?0:s->masks[slot]&mask;
 if(!(selected&32)||!(s->event_interest&INTEREST_ENEMY_FIELDS))return selected;
 TargetRef receiver=s->enemy_recipient[slot];int policy=(int)operation[48];
 if(!(policy==ENEMY_SELECT_ALL||policy==ENEMY_SELECT_CURRENT&&same_enemy_ref(receiver,s->condition_target)||policy==ENEMY_SELECT_BOSS&&receiver.kind==ACTOR_BODY))return selected&~32;
 int generation=0,alive=0,parent_kind=-1,parent_id=-1;
 return world_actor(s,receiver.kind,receiver.identity,&generation,&alive,&parent_kind,&parent_id)&&alive&&generation==receiver.generation?selected:selected&~32;
}
// Explicit attack groups: zero is the legacy ungrouped impact identity.
// Slot states: free=0, collecting=1, sealed=2, dispatching=3.
__device__ int group_find(State* s,int owner,int identity){for(int k=0;k<AG;k++)if(s->ag_active[k]==1&&s->ag_owner[k]==owner&&s->ag_id[k]==identity)return k;return -1;}
__device__ int group_sealed(State* s,int owner,int identity,int epoch){for(int k=0;k<AG;k++)if(s->ag_active[k]>=2&&s->ag_owner[k]==owner&&s->ag_id[k]==identity&&s->ag_epoch[k]==epoch)return k;return -1;}
__device__ int group_seal(State* s,int owner,int identity,int epoch,double t){
 int k=group_find(s,owner,identity);if(k<0||s->ag_epoch[k]!=epoch||t<s->ag_open[k])return -1;
 s->ag_active[k]=2;s->ag_n--;s->ag_open[k]=t;return k;
}
__device__ __noinline__ int group_begin(State* s,int owner,int identity,int mask,int expected,double t){
 if(s->ag_n>=AG||group_find(s,owner,identity)>=0||s->ag_clock>=2147483647)return 8;
 if(expected&&expected!=s->ag_clock+1)return 8;
 for(int k=0;k<AG;k++)if(!s->ag_active[k]){s->ag_active[k]=1;s->ag_owner[k]=owner;s->ag_id[k]=identity;s->ag_epoch[k]=++s->ag_clock;s->ag_mask[k]=mask;s->ag_count[k]=0;s->ag_open[k]=t;s->ag_n++;return 0;}return 8;
}
__device__ __noinline__ int group_collect(State* s,const Impact* p,double t){
 if(!s->ag_n||!p->attack_id||p->outcome==OUTCOME_MISS||p->credit<=0)return 0;
 int k=group_find(s,p->attacker,p->attack_id);if(k<0||!(s->ag_mask[k]&(1<<p->kind)))return 0;if(t<s->ag_open[k])return 8;
 for(int n=0;n<s->ag_count[k];n++)if(s->ag_kind[k][n]==p->kind&&s->ag_identity[k][n]==p->identity&&s->ag_generation[k][n]==p->generation)return 0;
 int n=s->ag_count[k];if(n>=AT)return 8;s->ag_kind[k][n]=p->kind;s->ag_identity[k][n]=p->identity;s->ag_generation[k][n]=p->generation;s->ag_count[k]++;return 0;
}
__device__ double captured_ref(const double* e,int ne,State* s,int owner,int name){
 if(s->gauge_present[owner][name])return ref(e,ne,s,owner,name);
 for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[0]==owner&&effect(e,s,k)[3]==name)return s->stacks[k];
 return -1;
}
// A normal buff samples duration scaling before refreshing its lifetime.
__device__ double expires_at(const double* e,int ne,State* s,const double* q,double t){
 if(q[7]<0)return 1e30;
 double duration=q[7];if(q[218]>0)duration*=(q[219]<0?0:ref(e,ne,s,(int)q[0],(int)q[219]));
 return t+duration;
}
__device__ double value(const double* e,int ne,State* s,int j){
 const double* q=effect(e,s,j);double v=q[6];
 // The CPU lost-HP branch returns before stack/per-recipient overrides and
 // always observes the original caster, including down/revival transitions.
 if(q[10]==-3){int owner=(int)q[0];double pct=s->hppct[owner];if(pct<0&&s->reviving_pct[owner]>0)pct=s->reviving_pct[owner];return v*mx(0,100-pct);}
 if(q[10]>=0)v*=s->capture[j]>=0?s->capture[j]:ref(e,ne,s,(int)q[0],(int)q[10]);
 else if((int)q[9]!=1)v*=s->stacks[j];
 return v;
}
// Counter reductions use original fixed values, once per live instance, in CPU order.
// Runtime gates, recipients and stack count intentionally do not filter this scan.
__device__ int reduced_count(const double* e,State* s,const double* listener,int n){
 bool any_reducer=false;for(int k=0;k<MASK_WORDS;k++)if(listener[REDUCER_MASK+k]!=0){any_reducer=true;break;}
 if(!any_reducer)return n<1?1:n;
 double reduction=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* r=effect(e,s,j);int id=s->definition[j];
  if(!s->alive[j]||s->end[j]<=s->when||r[244]==0||r[0]!=listener[0])continue;
  if(((unsigned int)listener[REDUCER_MASK+id/32])&(1u<<(id%32)))reduction+=r[243];
 }
 double result=(double)n-trunc(reduction);return result<1?1:result>2147483647?2147483647:(int)result;
}
__device__ __noinline__ double full_ammo(const double*,const double*,int,State*,int,int);
__device__ __noinline__ double recipient_value(const double* c,const double* e,int ne,State* s,int j,int who,int full){
 const double* q=effect(e,s,j);double v=value(e,ne,s,j);
 if(s->bullet_initialized[j]&&q[62]>=0&&q[9]!=1&&q[10]<0&&q[10]!=-3&&!lazy_target(q)&&s->alive[j])v=q[6]*s->bullet_stacks[j][who];
 if(q[10]==-4){if(who>=5||s->ammo_query_mask&(1<<who))return 0;s->ammo_query_mask|=1<<who;double capacity=full_ammo(c,e,ne,s,who,full);s->ammo_query_mask&=~(1<<who);v*=capacity;}
 return v;
}
// Keep shared predicate code out of every stat/weapon/healing caller.
__device__ __noinline__ int base_condition(const double* c,const double* e,int ne,State* s,const double* q,int full,int runtime,int slot=-1,double core_frac=0,int hit_crit=0,int first=0,int limit=3,int query=-1,int eval_owner=-1);
__device__ void resolve_all(const double* c,const double* e,int ne,State* s,int full,int consume=0);
__device__ double max_hp(const double*,const double*,int,State*,int,int,int=0);
__device__ int special_target(const double*,const double*,int,State*,int,int);
__device__ int live_marker(const double*,const double*,int,State*,int,int,int);
__device__ __noinline__ int exclusive_ammo_total(const double*,const double*,int,State*,int,int,double,double,int,double*);
// Boolean charge lock lookup avoids a recursive stat() call and its large stack frame.
__device__ int charge_locked(const double* c,const double* e,int ne,State* s,int who,int full){
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){const double* q=effect(e,s,j);if(q[1]!=0||q[2]!=53||!s->alive[j]||s->end[j]<=s->when||(s->excluded[s->definition[j]/32]&(1u<<(s->definition[j]%32))))continue;
  if((s->masks[j]&((1<<who)|(1<<5)))&&base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))return 1;
 }return 0;
}
__device__ int random_target(const double*,State*,const double*,Order*);
__device__ void random_special_query(const double* e,State* s,int who){
 if(!s->random_special_present||s->random_special_valid[who]&&s->random_special_time[who]==s->when)return;
 for(int pass=0;pass<2;pass++)for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(!s->alive[j]||s->end[j]<=s->when||s->masks[j]>=0||q[4]!=19||!(pass==0?q[241]>0:q[1]==0&&q[2]==26))continue;
  s->random_special_mask[who][j]=random_target(e,s,q,0);
 }
 s->random_special_valid[who]=1;s->random_special_time[who]=s->when;s->valid[who]&=~(1ULL<<1);
}
__device__ int charge_immunity_flags(const double* c,const double* e,int ne,State* s,int who,int full){
 int flags=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);int bits=(int)q[213]&24;
  if(!bits||!s->alive[j]||s->end[j]<=s->when||(s->excluded[s->definition[j]/32]&(1u<<(s->definition[j]%32))))continue;
  if((s->masks[j]&((1<<who)|(1<<5)))&&base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))flags|=bits;
 }
 return flags;
}
// Aggregate before testing the sign: CPU immunity operates on the rounded-stat
// source groups, not on individual active carriers. Equipment/cube are exempt.
__device__ int charge_groups(const double* c,const double* e,int ne,State* s,int who,int full,double* values,int* blocked){
 double totals[NE]={0};int seen[NE]={0},exempt[NE]={0},order[NE],n=0;
 int flags=charge_immunity_flags(c,e,ne,s,who,full);
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);int key=(int)q[2];
  if(q[1]!=0||(key!=20&&key!=37)||!s->alive[j]||s->end[j]<=s->when||(s->excluded[s->definition[j]/32]&(1u<<(s->definition[j]%32))))continue;
  if(!(s->masks[j]&((1<<who)|(1<<5)))||!base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))continue;
  double v=recipient_value(c,e,ne,s,j,who,full);
  if(key==37){double caster=c[(int)q[0]*CW+29],raw=c[who*CW+29]>0?c[who*CW+29]:caster;if(caster<=0||raw<=0)continue;v=caster*v/100/raw*100;}
  int group=(int)q[45];if(!seen[group]){seen[group]=1;order[n++]=group;exempt[group]=((int)q[213]&32)!=0;}
  totals[group]+=v;
 }
 for(int i=0;i<n;i++){int group=order[i];double v=totals[group];values[i]=v;blocked[i]=!exempt[group]&&(v>0&&(flags&8)||v<0&&(flags&16));}
 return n;
}
__device__ double charge_speed_total(const double* c,const double* e,int ne,State* s,int who,int full){
 if(charge_locked(c,e,ne,s,who,full))return 0;
 double values[NE],total=0;int blocked[NE],removed=0,n=charge_groups(c,e,ne,s,who,full,values,blocked);
 for(int i=0;i<n;i++){total+=values[i];removed|=blocked[i];}
 // Preserve the original sequential sum if no group was removed. When CPU
 // filters a group it recomputes with Python's compensated builtin sum().
 if(!removed)return total;FloatSum kept={0,0};for(int i=0;i<n;i++)if(!blocked[i])add_sum(s,&kept,values[i]);return finish_sum(kept);
}
__device__ double charge_overflow_coefficient(const double* c,const double* e,int ne,State* s,int who,int full){
 double out=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(!((int)q[213]&64)||!s->alive[j]||s->end[j]<=s->when||(s->excluded[s->definition[j]/32]&(1u<<(s->definition[j]%32))))continue;
  if((s->masks[j]&((1<<who)|(1<<5)))&&base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))out+=recipient_value(c,e,ne,s,j,who,full);
 }
 return out;
}

__device__ int live_named_modifier(const double* e,State* s,int j,int key,int name=-1){
 const double* q=effect(e,s,j);
 return q[1]==0&&q[2]==key&&(name<0||q[36]==name)&&s->alive[j]&&s->end[j]>s->when&&!(s->excluded[s->definition[j]/32]&(1u<<(s->definition[j]%32)));
}
// Shared named-effect lookup. Damage factors multiply per instance and are
// owner-scoped; ATK and received-damage magnitudes add and are recipient-scoped.
// Conditions intentionally follow each declared CPU model, not a new rule.
__device__ double named_magnitude(const double* c,const double* e,int ne,State* s,int key,int name,int owner,int recipient,int full){
 double result=1;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(!live_named_modifier(e,s,j,key,name))continue;
  if(key==78){if(q[0]!=owner)continue;result*=1+recipient_value(c,e,ne,s,j,owner,full)/100;continue;}
  int mask=s->masks[j]<0?special_target(c,e,ne,s,j,full):s->masks[j];
  if(!(mask&(1<<recipient)))continue;
  if(key==80&&!base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,owner))continue;
  result+=recipient_value(c,e,ne,s,j,(int)q[0],full)/100;
 }
 return result;
}
__device__ __noinline__ double stat(const double* c,const double* e,int ne,State* s,int who,int key,int full){
 if(key==28)return raw_stunned(e,s,who);
 resolve_all(c,e,ne,s,full);
 if(s->cached_full!=full){invalidate(s);s->cached_full=full;}
 camera_query(s,who);random_special_query(e,s,who);int previous_lens=s->camera_lens;s->camera_lens=s->query_camera[who];
 if(key<63&&(s->valid[who]&(1ULL<<key))){s->camera_lens=previous_lens;return s->cached[who][key];}
 if(key==18&&(s->event_interest&INTEREST_EXCLUSIVE_AMMO)){double amount=0;if(exclusive_ammo_total(c,e,ne,s,who,full,0,0,1,&amount)){s->cached[who][key]=amount;s->valid[who]|=1ULL<<key;s->camera_lens=previous_lens;return amount;}}
 if(key==20&&charge_locked(c,e,ne,s,who,full)){s->camera_lens=previous_lens;return 0;}
 if(key==20){double value=charge_speed_total(c,e,ne,s,who,full);s->cached[who][key]=value;s->valid[who]|=1ULL<<key;s->camera_lens=previous_lens;return value;}
 double out=key==5||key==24?.15:0;int critical=key==5||key==6||key==24||key==25;FloatSum critical_sum={out,0};
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);if((int)q[1]!=0||!s->alive[j]||s->end[j]<=s->when||(s->excluded[s->definition[j]/32]&(1u<<(s->definition[j]%32))))continue;
  int k=(int)q[2];int want=key;
  if(key==24&&k==22||key==25&&k==23)continue;
  if(key==24)want=5;if(key==25)want=6;
  int matches=(k==want)||(key==5&&k==22)||(key==6&&k==23)||(key==20&&k==37)||(key==3&&k==46)||(key==1&&k==85);
  if(!matches)continue;
  int mask=s->masks[j];if(!(mask&(1<<who))&&!(mask&(1<<5)))continue;
  // Pinned CPU applies most enemy-target stats through its generic attacker/target route.
  if(mask&(1<<5)){if(k==27||k==26||k==28)continue;}
  else if(k==12||k==2||k==3||k==46)continue;
  if(!base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))continue;
  if(key==28||key==36||key==52||key==53||key==59){out=1;continue;}
  double v=recipient_value(c,e,ne,s,j,who,full);
  if(k==85)v=s->shield_capacity[j][0]*v/100;
  if(k==60)v=c[(int)q[0]*CW+((s->normal_landed_mask&(1<<(int)q[0]))?46:47)]*v/100;
  if(k==46)v=c[(int)q[0]*CW+30]*v/100;
  if(k==37){double raw=c[who*CW+29]>0?c[who*CW+29]:c[(int)q[0]*CW+29];v=raw>0?c[(int)q[0]*CW+29]*v/100/raw*100:0;}
  if(key==5||key==24)v/=100;
  if(critical)add_sum(s,&critical_sum,v);else out+=v;
 }
 if(critical)out=finish_sum(critical_sum);if(key==5||key==24)out=mx(0,mn(1,out));
 // Enemy received-damage amplification appends increments after the base sum,
 // in modifier-major / base-minor order (including different source owners).
 if(key==12)for(int m=s->slot_head;m>=0;m=s->slot_next[m]){
  const double* mag=effect(e,s,m);if(!live_named_modifier(e,s,m,80)||!(s->masks[m]&(1<<5))||!base_condition(c,e,ne,s,mag,full,1,m,0,0,0,3,who))continue;
  double magnitude=recipient_value(c,e,ne,s,m,(int)mag[0],full)/100;
  for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
   const double* q=effect(e,s,j);if(q[1]!=0||q[2]!=12||q[3]!=mag[36]||!s->alive[j]||s->end[j]<=s->when||(s->excluded[s->definition[j]/32]&(1u<<(s->definition[j]%32)))||!(s->masks[j]&(1<<5))||!base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))continue;
   out+=recipient_value(c,e,ne,s,j,5,full)*magnitude;
  }
 }
 // CPU appends HP conversion, then caster-based ATK, after generic flat ATK.
 // These special passes resolve a still-lazy target afresh without caching it.
 if(key==1)for(int pass=0;pass<2;pass++)for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);if(!s->alive[j]||s->end[j]<=s->when||!(pass==0?q[241]>0:q[1]==0&&q[2]==26))continue;
  if(!((s->masks[j]<0&&q[4]==19?s->random_special_mask[who][j]:special_target(c,e,ne,s,j,full))&(1<<who))||!base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))continue;
  double v=recipient_value(c,e,ne,s,j,pass==0?who:(int)q[0],full);out+=pass==0?max_hp(c,e,ne,s,who,full)*(v/100):c[(int)q[0]*CW]*(v/100)*(q[35]>0?named_magnitude(c,e,ne,s,79,(int)q[3],(int)q[0],who,full):1);
 }
 if(key==8){double conv=charge_overflow_coefficient(c,e,ne,s,who,full);if(conv>0){double overflow=mx(0,charge_speed_total(c,e,ne,s,who,full)-100);if(overflow>0)out+=overflow*conv/100;}}
 if(key<63){s->cached[who][key]=out;s->valid[who]|=1ULL<<key;}s->camera_lens=previous_lens;return out;
}
// Authoritative CPU interval semantics, evaluated from live range buffs.
// Predicate uses the innate weapon; outgoing shots use their weapon context.
__device__ int optimal_range(const double* c,const double* e,int ne,State* s,int who,int full,int use_mode){
 const double* a=c+who*CW;
 const double* mode=use_mode&&s->weapon_context[who]&&s->mode[who]>=0?effect(e,s,s->mode[who]):0;
 if(s->boss_count&&s->boss_distance<0){int kind=(int)s->boss_program[mode?8+s->mode[who]:3+who];return (s->boss_weapon_mask&(1<<kind))!=0;}
 if(!s->boss_count&&a[167]<2)return (mode?mode[30]:a[14])>.5;
 double lo=mode?mode[264]:a[164],hi=mode?mode[265]:a[165],d=s->boss_count?s->boss_distance:a[166];
 hi*=1+stat(c,e,ne,s,who,62,full)/100;
 lo=mx(0,lo*(1-stat(c,e,ne,s,who,61,full)/100));
 return lo-1e-9<=d&&d<=hi+1e-9;
}
__device__ __noinline__ int base_condition(const double* c,const double* e,int ne,State* s,const double* q,int full,int runtime,int slot,double core_frac,int hit_crit,int first,int limit,int query,int eval_owner){
 if(runtime&&slot>=0&&(s->masks[slot]&32)&&!enemy_field_matches(s,slot))return 0;
 for(int j=first;j<(int)q[14]&&j<first+limit;j++){
  int type=(int)q[15+j*3],name=(int)q[16+j*3];double arg=q[17+j*3];int owner=eval_owner>=0?eval_owner:(int)q[0];double v=0;
  // Finite effects latch activation; persistent predicates read current state.
  if(runtime && ((slot>=0?!s->runtime_cond[slot]:(q[7]>=0||q[62]>=0)) || (type!=1&&type!=2&&type!=3&&type!=4&&type!=5&&type!=9&&type!=10&&type!=11&&type!=12&&type!=14&&type!=15&&type!=16&&type!=17&&type!=18&&type!=19&&type!=22&&type!=29&&type!=30&&type!=34&&type!=36&&type!=37&&type!=WORLD_COUNT_ABOVE&&type!=WORLD_COUNT_BELOW)))continue;
  if((type==WORLD_COUNT_ABOVE||type==WORLD_COUNT_BELOW)&&!world_count_condition(type,s->add_live_snapshot,arg))return 0;
  if((type==WORLD_TARGET_BOSS||type==WORLD_TARGET_ADD)&&!world_target_condition(type,s->condition_target))return 0;
  if(type==34){
   if(runtime){int recipient=query>=0?query:owner;if(slot>=0&&!(s->masks[slot]&(1<<recipient)))recipient=5;if((recipient<5?s->hppct[recipient]:100.0)>arg)return 0;}
   else{double lowest=100;for(int k=0;k<5;k++)lowest=mn(lowest,s->hppct[k]);if(lowest>arg)return 0;}
  }
  if(type==29&&!s->charging[owner]||type==30&&!((runtime&&s->camera_lens>=0?s->camera_lens:s->camera_mask)&(1<<owner)))return 0;
  if(type==26||type==27){int definition=q[269]>0?(int)q[269]-1:(int)q[58];double* acc=type==26?&s->chance_acc[definition]:&s->noncore_acc[definition];*acc+=type==26?arg:1.0-core_frac;if(*acc<1.0)return 0;*acc-=1.0;}
  if(type==35&&s->world[1]<1)return 0;
  if(type==36&&s->cover_hp[owner]<=0||type==37&&s->cover_hp[owner]>0)return 0;
  if(type==38&&!live_marker(c,e,ne,s,owner,68,full))return 0;
  if(type==39){for(int who=0;who<5;who++)if(!(s->down_mask&(1<<who))&&s->cover_hp[who]<=0)return 0;}
  if(type==28&&!hit_crit)return 0;
  if((type==22||type==25)&&arg==0)return 0;
  if(type==23&&!raw_stunned(e,s,5))return 0;
  if(type==24&&!marker_recipient(e,s,owner,2))return 0;
  if(type==1&&!full || type==2&&full)return 0;
  if(type>=18&&type<=21){v=s->gauges[owner][name];if(type==18&&v<arg||type==19&&v>=arg||type==20&&v!=arg)return 0;if(type==21){long long iv=(long long)v,m=(long long)arg;long long rem=((iv%m)+m)%m;if(rem!=(long long)q[66+j])return 0;}}
  if(type==3||type==4)v=state_recipient(e,s,owner,name,(int)arg);
  if(type==5){
   for(int k=s->slot_head;k>=0;k=s->slot_next[k])if((int)effect(e,s,k)[3]==name&&(s->alive[k])&&s->masks[k]>=0){int mask=s->masks[k];if(type==5?(effect(e,s,k)[0]==owner&&(mask&((1<<owner)|(1<<5)))):(mask&(1<<owner))){v=type==5?s->stacks[k]:1;break;}}
   if(s->mode[owner]>=0&&(int)effect(e,s,s->mode[owner])[3]==name)v=1;
  }
  if(type==16||type==17){int found=0;for(int k=s->slot_head;k>=0;k=s->slot_next[k])if((int)effect(e,s,k)[3]==name&&(s->alive[k])&&s->masks[k]>=0&&(s->masks[k]&(1<<5))&&enemy_field_matches(s,k)){found=1;break;}if(type==16&&!found||type==17&&found)return 0;}
  if(type==3&&v<=0 || type==4&&v>0 || type==5&&v<arg)return 0;
  
  if(type==12){int shield=0;for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(effect(e,s,k)[2]==45&&s->alive[k]&&(s->shield_mask[k]&(1<<owner))){shield=1;break;}if(!shield)return 0;}
  if(type==13&&s->heal_source==owner)return 0;
  if(type==14&&!(s->cast_mask&(1<<owner))||type==15&&(s->cast_mask&(1<<owner)))return 0;
  if(type==31||type==32){int has=0;for(int k=0;k<5;k++)if(k!=owner&&s->burst_stage[k]==1)has=1;if(type==31&&!has||type==32&&has)return 0;}
  if(type==6&&owner!=0&&owner!=2&&owner!=4)return 0;
  if(type==7&&owner!=1&&owner!=3)return 0;
  if(type==9&&s->hppct[owner]<arg||type==10&&s->hppct[owner]>arg||type==11&&s->hppct[owner]<100)return 0;
 }
 return 1;
}
__device__ int condition(const double* c,const double* e,int ne,State* s,const double* q,int full,int runtime,int slot=-1,double core_frac=0,int hit_crit=0,int eval_owner=-1){
 if(runtime)return base_condition(c,e,ne,s,q,full,runtime,slot,core_frac,hit_crit,0,3,-1,eval_owner);
 int owner=eval_owner>=0?eval_owner:(int)q[0];
 for(int j=0;j<(int)q[14];j++){
  if((int)q[15+j*3]==8){if(stat(c,e,ne,s,owner,(int)q[16+j*3],full)<=q[17+j*3])return 0;}
  else if((int)q[15+j*3]==33){if(!optimal_range(c,e,ne,s,owner,full,0))return 0;}
  else if(!base_condition(c,e,ne,s,q,full,0,slot,core_frac,hit_crit,j,1,-1,eval_owner))return 0;
 }
 return 1;
}
// Rank targets are resolved lazily once, using the same activation group as CPU.
__device__ double rank_atk(const double* c,const double* e,int ne,State* s,int who,int full){
 double pct=0,flat=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);if(q[1]!=0||!s->alive[j]||s->masks[j]<0||!(s->masks[j]&(1<<who)))continue;
  double v=recipient_value(c,e,ne,s,j,q[2]==26?(int)q[0]:who,full);if(q[2]==0)pct+=v;if(q[2]==1)flat+=v;if(q[2]==26)flat+=c[(int)q[0]*CW]*(v/100);
 }
 return c[who*CW]*(1+pct/100)+flat;
}
__device__ double rank_def(const double* c,const double* e,int ne,State* s,int who,int full){
 double pct=0,flat=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){const double* q=effect(e,s,j);if(q[1]!=0||!s->alive[j]||s->masks[j]<0||!(s->masks[j]&(1<<who)))continue;
  if(q[2]==2)pct+=recipient_value(c,e,ne,s,j,who,full);if(q[2]==46)flat+=c[(int)q[0]*CW+30]*(recipient_value(c,e,ne,s,j,(int)q[0],full)/100);
 }
 return c[who*CW+30]*(1+pct/100)+flat;
}
__device__ int random_target(const double* e,State* s,const double* q,Order* ordered=0){
 int pool[5],n=0,mask=0;Order order=0;
 for(int who=0;who<5;who++){
  if(q[4]==23){if((s->down_mask&(1<<who))&&((int)q[48]&(1<<who)))pool[n++]=who;continue;}
  if(s->down_mask&(1<<who))continue;
  if(q[4]==25){if(s->cover_hp[who]<=0)pool[n++]=who;continue;}
  if(q[4]==19){if(who!=(int)q[0])pool[n++]=who;}
  else{int harmful=0;for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[259]>0&&s->masks[k]>=0&&(s->masks[k]&(1<<who))){harmful=1;break;}if(harmful)pool[n++]=who;}
 }
 int count=(int)mn(q[5],n);
 for(int k=0;k<count;k++){int at=(int)mt_below(&s->rng,n-k),who=pool[at];pool[at]=pool[n-k-1];mask|=1<<who;order|=Order(who+1)<<(3*k);}
 if(ordered)*ordered=order;return mask;
}
__device__ int cached_random_target(const double* e,State* s,const double* q,double activated,Order* ordered){
 for(int k=0;k<s->random_cache_count;k++)if(s->random_owner[k]==(int)q[0]&&s->random_key[k]==(int)q[257]&&s->random_time[k]==activated){*ordered=s->random_order[k];return s->random_mask[k];}
 if(s->random_cache_count>=RC){s->random_error=32;*ordered=0;return 0;}
 int k=s->random_cache_count++;s->random_owner[k]=(int)q[0];s->random_key[k]=(int)q[257];s->random_time[k]=activated;
 int mask=random_target(e,s,q,ordered);s->random_mask[k]=mask;s->random_order[k]=*ordered;return mask;
}
__device__ int ranked_target(const double* c,const double* e,int ne,State* s,const double* q,int full,Order* ordered=0){
 if(q[4]==19||q[4]==20||q[4]==23||q[4]==25)return random_target(e,s,q,ordered);
 int mask=0,owner=(int)q[0],kind=(int)q[4];Order order=0;
 if(kind==14){double limit=rank_def(c,e,ne,s,owner,full);int shift=0;for(int who=0;who<5;who++)if(!(s->down_mask&(1<<who))&&rank_def(c,e,ne,s,who,full)<limit){mask|=1<<who;order|=Order(who+1)<<shift;shift+=3;}if(ordered)*ordered=order;return mask;}
 for(int pick=0;pick<(int)q[5];pick++){
  int best=-1;double bestv=0;
  for(int who=0;who<5;who++){
   if((kind==22?!(s->down_mask&(1<<who))||who==owner:bool(s->down_mask&(1<<who)))||mask&(1<<who)||q[49]>0&&who==owner||(kind==15||kind==16)&&!((int)q[48]&(1<<who)))continue;
   double v=kind==5||kind==15||kind==22?rank_atk(c,e,ne,s,who,full):kind==16?-rank_atk(c,e,ne,s,who,full):kind==6?c[who*CW+30]:-s->hppct[who];
   if(best<0||v>bestv){best=who;bestv=v;}
  }
  if(best<0)break;mask|=1<<best;order|=Order(best+1)<<(pick*3);
 }
 if(ordered)*ordered=order;return mask;
}
__device__ Order filter_order(Order raw,int mask){Order order=0;int shift=0;while(raw){int who=(raw&7)-1;raw>>=3;if(who>=0&&(mask&(1<<who))){order|=Order(who+1)<<shift;shift+=3;}}return order;}
__device__ int list_target(const double* c,const double* e,int ne,State* s,const double* q,int full,Order* ordered);
__device__ Order unique_order(Order raw){Order out=0;int seen=0,shift=0;while(raw){int v=raw&7;raw>>=3;if(!(seen&(1<<v))){seen|=1<<v;out|=Order(v)<<shift;shift+=3;}}return out;}
// Pack ordered recipients in three-bit slots (one-based indices).
__device__ Order recipient_order(const double* c,const double* e,int ne,State* s,const double* q,int mask,int full){
 Order order=0;int shift=0,kind=(int)q[4],owner=(int)q[0];
 if(kind==17){Order raw=0;list_target(c,e,ne,s,q,full,&raw);return filter_order(raw,mask);}
 if(q[141]>0){int raw=(int)q[140];while(raw){int who=(raw&7)-1;raw>>=3;if(who>=0&&(mask&(1<<who))){order|=Order(who+1)<<shift;shift+=3;}}return order;}
 if(kind==3){int list[3]={owner,owner-1,owner+1};for(int k=0;k<3;k++){int who=list[k];if(who>=0&&who<5&&(mask&(1<<who))){order|=Order(who+1)<<shift;shift+=3;}}return order;}
 while(mask&31){int best=-1;double bestv=0;
  for(int who=0;who<5;who++)if(mask&(1<<who)){double v=kind==5||kind==15||kind==22?rank_atk(c,e,ne,s,who,full):kind==16?-rank_atk(c,e,ne,s,who,full):kind==6?c[who*CW+30]:kind==7?-s->hppct[who]:kind==21?-s->cover_hp[who]/s->cover_max[who]:0;if(best<0||v>bestv){best=who;bestv=v;}}
  mask&=~(1<<best);order|=Order(best+1)<<shift;shift+=3;
 }return order;
}
// Lists are eager concatenations, even when individual children normally rank
// lazily. Definitions are inert rows and never become active effects.
__device__ int list_target(const double* c,const double* e,int ne,State* s,const double* q,int full,Order* ordered){
 int mask=0,shift=0;Order order=0;
 for(int i=0;i<(int)q[48];i++){
  const double* node=e+((int)q[5]+i)*EW;Order child=0;int bits=target_basic(e,node,5,s);
  if(bits<0)bits=ranked_target(c,e,ne,s,node,full,&child);else child=recipient_order(c,e,ne,s,node,bits,full);
  bits&=~s->down_mask;child=filter_order(child,bits);mask|=bits;while(child){order|=(child&7)<<shift;child>>=3;shift+=3;}
 }
 if(ordered)*ordered=order;return mask;
}
__device__ int target(const double* c,const double* e,int ne,const double* q,int n,State* s,int full,Order* ordered=0,int eager=0){
 if(q[4]==17)return list_target(c,e,ne,s,q,full,ordered);
 int mask=target_basic(e,q,n,s);
 if(mask<0&&(eager||q[4]==20||q[4]==22||q[4]==23||q[4]==25))return ranked_target(c,e,ne,s,q,full,ordered);
 if(mask>=0)mask&=~s->down_mask;
 if(ordered)*ordered=mask<0?0:recipient_order(c,e,ne,s,q,mask,full);return mask;
}
__device__ int special_target(const double* c,const double* e,int ne,State* s,int slot,int full){return s->masks[slot]>=0?s->masks[slot]:ranked_target(c,e,ne,s,effect(e,s,slot),full);}
__device__ void resolve_all(const double* c,const double* e,int ne,State* s,int full,int consume){
 if(!s->lazy_dirty&&!consume)return;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&s->masks[j]<0&&(effect(e,s,j)[207]>0||consume&&effect(e,s,j)[62]>=0)){
  const double* q=effect(e,s,j);int found=-1;
  if(q[4]==19)found=cached_random_target(e,s,q,s->activated[j],&s->target_order[j]);else for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(k!=j&&s->masks[k]>=0&&s->activated[k]==s->activated[j]&&effect(e,s,k)[0]==q[0]&&effect(e,s,k)[4]==q[4]&&effect(e,s,k)[5]==q[5]&&effect(e,s,k)[48]==q[48]&&effect(e,s,k)[49]==q[49]){found=s->masks[k];s->target_order[j]=s->target_order[k];break;}
  s->masks[j]=found>=0?found:ranked_target(c,e,ne,s,q,full,&s->target_order[j]);if(q[62]>=0&&s->bullet_left[j]>=0){for(int k=0;k<6;k++)s->bullets[j][k]=(s->masks[j]&(1<<k))?s->bullet_left[j]:0;s->bullet_left[j]=-1;}invalidate(s);
 }
 s->lazy_dirty=0;
}
__device__ double max_hp(const double* c,const double* e,int ne,State* s,int who,int full,int attack_scope){
 double pct=0,flat=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);if(q[1]!=0||!s->alive[j]||s->masks[j]<0||!(s->masks[j]&(1<<who)))continue;
  if(attack_scope&&(s->excluded[s->definition[j]/32]&(1u<<(s->definition[j]%32))))continue;
  if(q[2]==84){flat+=s->shield_capacity[j][0];continue;}
  if(q[2]==86){flat+=s->shield_capacity[j][0]*recipient_value(c,e,ne,s,j,who,full)/100;continue;}
  double v=recipient_value(c,e,ne,s,j,who,full);
  if(q[2]==38||q[2]==41)pct+=v;if(q[2]==39||q[2]==40)flat+=c[(int)q[0]*CW+28]*v/100;
 }
 return c[who*CW+28]*(1+pct/100)+flat;
}
// Typed snapshot storage: code 84 never shares shield quantity semantics.
// Exclude this instance's previous gift before measuring the source, so a
// refresh targeting the source cannot compound its own previous snapshot.
__device__ void build_max_hp_snapshot(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);double previous=s->shield_capacity[j][0];
 s->shield_capacity[j][0]=0;
 s->shield_capacity[j][0]=max_hp(c,e,ne,s,(int)q[0],full)*value(e,ne,s,j)/100;
 s->shield_current[j][0]=s->shield_capacity[j][0]-previous;invalidate(s);
}
// Copy selection is by immutable assembled base stats, before named callbacks.
// Selected basis stays attached to this instance until its next activation.
__device__ void prepare_base_copy(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);int axis=q[2]==85?0:28,source=-1;double best=0;
 for(int who=0;who<5;who++)if(!(s->down_mask&(1<<who))&&(source<0||c[who*CW+axis]>best)){source=who;best=c[who*CW+axis];}
 s->shield_capacity[j][0]=best;s->shield_capacity[j][1]=source;invalidate(s);
}
__device__ void build_base_copy(const double* c,const double* e,int ne,State* s,int j,int full){
 if(effect(e,s,j)[2]!=86)return;
 double amount=s->shield_capacity[j][0]*value(e,ne,s,j)/100;
 s->shield_current[j][1]=amount-s->shield_current[j][0];s->shield_current[j][0]=amount;
}
// Capture the transition at the write. The notify FSM drains it synchronously
// before the caller's next action; it never replays CPU-computed HP events.
__device__ void sync_hp(const double* c,const double* e,int ne,State* s,int who,int full){
 if(s->reviving_mask&(1<<who))return;double m=max_hp(c,e,ne,s,who,full);
 if(m>0){double prev=s->hppct[who],now=s->hp[who]/m*100;s->hppct[who]=now;invalidate(s);
  if(s->hp_interest&&!s->in_hp_edge&&prev>=0&&(now<prev||prev<100-1e-6&&now>=100-1e-6)){
   if(s->hp_pending){s->hp_edge_error=1;return;}
   s->hp_pending=who+1;s->hp_edge_prev=prev;s->hp_edge_new=now;
  }
 }
}
// Body healing has separate recipient/source multipliers. Resolve only the
// queried carrier stat; do not trigger unrelated lazy target selection.
__device__ void resolve_live_slot(const double*,const double*,int,State*,int,int);
__device__ double healing_stat_multiplier(const double* c,const double* e,int ne,State* s,int who,int full,int key){
 double pct=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(q[1]!=0||q[2]!=key||!s->alive[j]||s->end[j]<=s->when)continue;
  resolve_live_slot(c,e,ne,s,j,full);
  if(s->masks[j]>=0&&(s->masks[j]&(1<<who))&&base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))pct+=recipient_value(c,e,ne,s,j,who,full);
 }
 return mx(0,1+pct/100);
}
__device__ double heal_multiplier(const double* c,const double* e,int ne,State* s,int who,int full,int source){
 double received=healing_stat_multiplier(c,e,ne,s,who,full,42);
 double outgoing=healing_stat_multiplier(c,e,ne,s,source,full,73);
 return received*outgoing;
}
__device__ void add_burst(State* s,double amount){if(amount>0&&s->burst_charging)s->burst_amount=mn(100,s->burst_amount+amount);}
__device__ double burst_gain(const double* c,const double* e,int ne,State* s,int who,int mode,int hits,int charge,int full,double exception=-1){
 double energy=exception>=0?exception:mode>=0?effect(e,s,mode)[249]:c[who*CW+45];
 double gain=energy*hits;if(charge)gain*=(mode>=0?effect(e,s,mode)[226]:c[who*CW+19])/100;
 return gain+hits*stat(c,e,ne,s,who,60,full);
}
__device__ int boss_dispel(State*,double,int);
__device__ __noinline__ int notify(const double*,const double*,int,State*,const double*,double,int,int,int,int,double=0,int=0,double=0,int=-1,double=0,TargetRef={-1,0,0});
__device__ __noinline__ double full_ammo(const double*,const double*,int,State*,int,int);
__device__ double reload_duration(const double*,const double*,int,State*,int,int);
__device__ void start_reload(const double*,const double*,int,State*,int,int,double);
// Shield quantity lifecycle. All inputs are effects, initial stats and authored
// operations; CPU-calculated shield amounts never enter the interpreter.
__device__ void resolve_live_slot(const double* c,const double* e,int ne,State* s,int j,int full){
 if(s->masks[j]>=0)return;const double* q=effect(e,s,j);int found=-1;
 if(q[4]==19)found=cached_random_target(e,s,q,s->activated[j],&s->target_order[j]);
 else for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(k!=j&&s->masks[k]>=0&&s->activated[k]==s->activated[j]&&effect(e,s,k)[0]==q[0]&&effect(e,s,k)[4]==q[4]&&effect(e,s,k)[5]==q[5]&&effect(e,s,k)[48]==q[48]&&effect(e,s,k)[49]==q[49]){found=s->masks[k];s->target_order[j]=s->target_order[k];break;}
 s->masks[j]=found>=0?found:ranked_target(c,e,ne,s,q,full,&s->target_order[j]);
 if(q[62]>=0&&s->bullet_left[j]>=0){for(int k=0;k<6;k++)s->bullets[j][k]=(s->masks[j]&(1<<k))?s->bullet_left[j]:0;s->bullet_left[j]=-1;}
 invalidate(s);
}
__device__ int live_shield_recipient(const double* c,const double* e,int ne,State* s,int j,int who,int full){
 if(!s->alive[j]||s->when>=s->end[j])return 0;
 resolve_live_slot(c,e,ne,s,j,full);
 return (s->masks[j]&(1<<who))&&base_condition(c,e,ne,s,effect(e,s,j),full,1,j,0,0,0,3,who);
}
// Marker queries use the CPU's _live semantics: resolve only the queried
// carrier, check the exact lifetime, then apply recipient runtime conditions.
__device__ int live_marker(const double* c,const double* e,int ne,State* s,int who,int key,int full){
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(effect(e,s,j)[1]==0&&effect(e,s,j)[2]==key&&live_shield_recipient(c,e,ne,s,j,who,full))return 1;
 return 0;
}
__device__ double live_amount(const double* c,const double* e,int ne,State* s,int who,int key,int full){
 double total=0;for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(effect(e,s,j)[1]==0&&effect(e,s,j)[2]==key&&live_shield_recipient(c,e,ne,s,j,who,full))total+=recipient_value(c,e,ne,s,j,who,full);return total;
}
// CPU cover_max_hp queries each live carrier directly: ordinary percentages
// use cover base, max_hp scaling uses the original caster's live maximum.
// _get_value does not use the damage resolver's per-recipient bullet override.
__device__ double cover_capacity(const double* c,const double* e,int ne,State* s,int who,int full){
 double pct=0,flat=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);if(q[1]!=0||q[2]!=70||!live_shield_recipient(c,e,ne,s,j,who,full))continue;
  double v=value(e,ne,s,j);
  if(q[50]>0)flat+=max_hp(c,e,ne,s,(int)q[0],full)*v/100;else pct+=v;
 }
 return s->cover_base*(1+pct/100)+flat;
}
__device__ void sync_cover(const double* c,const double* e,int ne,State* s,int full){
 for(int who=0;who<5;who++){
  double amount=cover_capacity(c,e,ne,s,who,full),previous=s->cover_max[who];
  if(amount!=previous){if(s->cover_hp[who]>0)s->cover_hp[who]=mn(s->cover_hp[who]+mx(amount-previous,0),amount);s->cover_max[who]=amount;}
 }
}
__device__ void build_decoy(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);double amount=max_hp(c,e,ne,s,(int)q[0],full)*recipient_value(c,e,ne,s,j,(int)q[0],full)/100;
 s->shield_present[j]=s->masks[j]&31;for(int who=0;who<5;who++)s->shield_current[j][who]=s->shield_capacity[j][who]=(s->masks[j]&(1<<who))?amount:0;
}
// Storage is a separate overheal reserve, not a max-HP modifier or shield.
__device__ void build_heal_storage(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);double cap=mx(0,max_hp(c,e,ne,s,(int)q[0],full)*recipient_value(c,e,ne,s,j,(int)q[0],full)/100);
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
// Independent received-healing pool: full allocated healing, not excess HP.
// shield_present is disjoint for stat76: 0 uninitialized/retired, 1 open, 2 taken.
__device__ void build_heal_charge(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);int owner=(int)q[0];
 s->shield_capacity[j][0]=mx(0,rank_atk(c,e,ne,s,owner,full)*value(e,ne,s,j)/100);s->shield_current[j][0]=0;s->shield_present[j]=1;
}
__device__ double heal_charge_capacity(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);int owner=(int)q[0],name=(int)q[3];double bonus=0;
 for(int k=s->slot_head;k>=0;k=s->slot_next[k]){const double* b=effect(e,s,k);if(b[1]!=0||b[2]!=77||(b[212]>0&&b[36]!=name)||!live_shield_recipient(c,e,ne,s,k,owner,full))continue;bonus+=recipient_value(c,e,ne,s,k,owner,full);}
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
// Damage pools use the same typed carrier storage as other resource families.
// Only stats 81/82 read these scalar fields: 1 collecting, 2 closed/taken.
__device__ void build_damage_accum(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);int owner=(int)q[0];
 s->shield_capacity[j][0]=(c[owner*CW]*(1+stat(c,e,ne,s,owner,0,full)/100)+stat(c,e,ne,s,owner,1,full))*recipient_value(c,e,ne,s,j,owner,full)/100;
 s->shield_current[j][0]=0;s->shield_present[j]=1;
 if(q[35]>0)s->damage_accum_last[(int)q[3]]=0;
}
__device__ double take_damage_accum(const double* e,State* s,int name){
 double amount=s->damage_accum_last[name];
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){const double* q=effect(e,s,j);
  if(s->alive[j]&&q[1]==0&&(q[2]==81||q[2]==82)&&q[3]==name){amount=s->shield_current[j][0];s->shield_current[j][0]=0;s->shield_present[j]=2;break;}
 }
 s->damage_accum_last[name]=0;return amount;
}
__device__ double damage_accum_rate(const double* c,const double* e,int ne,State* s,int owner,int name,int full){
 int found=0;double base=0,extra=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){const double* q=effect(e,s,j);
  if(!s->alive[j]||q[1]!=0||q[2]!=83||q[0]!=owner||!q[139])continue;
  double amount=recipient_value(c,e,ne,s,j,owner,full);
  if(!q[212]){base+=amount;found=1;}else if(q[36]==name)extra+=amount;
 }
 return (found?base:100)+extra;
}
__device__ void prepare_target_counter(const double* c,const double* e,int ne,State* s,int r,int full){
 const double* q=effect(e,s,r);double t=s->activated[r];
 double credit=q[301]>0&&s->counter_uid[r]==s->entry_seq[r]&&!s->counter_done[r]&&s->counter_end[r]>t?s->counter_credit[r]:0;
 if(s->counter_clock>=2147483646){s->counter_error=8;return;}
 s->counter_uid[r]=s->entry_seq[r];s->counter_epoch[r]=++s->counter_clock;s->counter_done[r]=0;
 s->counter_credit[r]=credit;s->counter_end[r]=s->end[r];
}
// BEGIN GENERATED LIFECYCLE
// Generated from lifecycle_specs.py; do not hand-edit.
__device__ int lifecycle_init_hp(const double* q){return q[1]==0&&(q[2]==86);}
__device__ int lifecycle_instance(const double* e,State* s,int r,int uid){
 if(r<0)return -1;const double* q=effect(e,s,r);
 if(q[1]==0&&(q[2]==72))return s->alive[r]&&s->entry_seq[r]==uid?r:-1;
 if(q[1]==0&&(q[2]==45))return s->alive[r]&&s->entry_seq[r]==uid?r:-1;
 if(q[1]==0&&(q[2]==74))return s->alive[r]&&s->entry_seq[r]==uid?r:-1;
 if(q[1]==0&&(q[2]==76))return s->alive[r]&&s->entry_seq[r]==uid?r:-1;
 if(q[1]==0&&(q[2]==81||q[2]==82))return s->alive[r]&&s->entry_seq[r]==uid?r:-1;
 if(q[1]==0&&(q[2]==84))return s->alive[r]&&s->entry_seq[r]==uid?r:-1;
 if(q[1]==0&&(q[2]==85||q[2]==86))return s->alive[r]&&s->entry_seq[r]==uid?r:-1;
 if(q[1]==0&&(q[2]==87))return s->alive[r]&&s->entry_seq[r]==uid?r:-1;
 return first_instance(e,s,s->definition[r]);
}
__device__ void prepare_base_copy(const double*,const double*,int,State*,int,int);
__device__ void prepare_target_counter(const double*,const double*,int,State*,int,int);
__device__ void lifecycle_prepare(const double* c,const double* e,int ne,State* s,int r,int full){
 const double* q=effect(e,s,r);
 if(q[1]==0&&(q[2]==85||q[2]==86))prepare_base_copy(c,e,ne,s,r,full);
 if(q[1]==0&&(q[2]==87))prepare_target_counter(c,e,ne,s,r,full);
}
__device__ void build_decoy(const double*,const double*,int,State*,int,int);
__device__ void build_shield(const double*,const double*,int,State*,int,int);
__device__ void build_heal_storage(const double*,const double*,int,State*,int,int);
__device__ void build_heal_charge(const double*,const double*,int,State*,int,int);
__device__ void build_damage_accum(const double*,const double*,int,State*,int,int);
__device__ void build_max_hp_snapshot(const double*,const double*,int,State*,int,int);
__device__ void build_base_copy(const double*,const double*,int,State*,int,int);
__device__ int lifecycle_activate(const double* c,const double* e,int ne,State* s,int r,int full,const double* q,int uid,int lazy,int mask,int* emitted,Order* targets,int* stop){
 *emitted=-1;*stop=0;
 if(q[1]==0&&q[2]==72&&!lazy&&mask){r=lifecycle_instance(e,s,r,uid);if(r>=0)build_decoy(c,e,ne,s,r,full);}
 if(q[1]==0&&q[2]==45&&!lazy&&mask){r=lifecycle_instance(e,s,r,uid);*stop=1;if(r>=0){build_shield(c,e,ne,s,r,full);*emitted=18;*targets=unique_order(s->target_order[r]);}}
 if(q[1]==0&&q[2]==74&&!lazy&&mask){r=lifecycle_instance(e,s,r,uid);if(r>=0)build_heal_storage(c,e,ne,s,r,full);}
 if(q[1]==0&&q[2]==76){r=lifecycle_instance(e,s,r,uid);if(r>=0)build_heal_charge(c,e,ne,s,r,full);}
 if(q[1]==0&&(q[2]==81||q[2]==82)){r=lifecycle_instance(e,s,r,uid);if(r>=0)build_damage_accum(c,e,ne,s,r,full);}
 if(q[1]==0&&q[2]==84&&!lazy&&mask){r=lifecycle_instance(e,s,r,uid);if(r>=0)build_max_hp_snapshot(c,e,ne,s,r,full);}
 if(q[1]==0&&(q[2]==85||q[2]==86)){r=lifecycle_instance(e,s,r,uid);if(r>=0)build_base_copy(c,e,ne,s,r,full);}
 return r;
}
__device__ void lifecycle_retire(const double* e,State* s,int j){
 retire_heal_charge(e,s,j);
}
__device__ void lifecycle_before_body_heal(const double* c,const double* e,int ne,State* s,int who,double amount,int full){
 collect_heal_charge(c,e,ne,s,who,amount,full);
}
// END GENERATED LIFECYCLE
__device__ void apply_storage_body_heal(const double* c,const double* e,int ne,State* s,int who,double amount,int full){
 lifecycle_before_body_heal(c,e,ne,s,who,amount,full);double maximum=max_hp(c,e,ne,s,who,full);if(amount>0)fill_heal_storage(c,e,ne,s,who,mx(0,s->hp[who]+amount-maximum),full);
 s->hp[who]=mn(s->hp[who]+amount,maximum);
}
// One link per distinct live member per carrier. Plans are frozen before
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
__device__ double take_shield_amp(const double* c,const double* e,int ne,State* s,int who,int full){
 int used[NS],n=0;FloatSum sum={0,0};
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(effect(e,s,j)[261]>0&&live_shield_recipient(c,e,ne,s,j,who,full)){used[n++]=j;add_sum(s,&sum,recipient_value(c,e,ne,s,j,who,full));}
 if(!n)return 0;
 for(int i=0;i<n;i++){int j=used[i];s->masks[j]&=~(1<<who);s->target_order[j]=filter_order(s->target_order[j],s->masks[j]);if(!s->masks[j])s->alive[j]=0;}
 // Consumed next-shield buffs emit log expiry, not state-end callbacks.
 invalidate(s);return finish_sum(sum);
}
__device__ void build_shield(const double* c,const double* e,int ne,State* s,int j,int full){
 const double* q=effect(e,s,j);int owner=(int)q[0];
 double amount=max_hp(c,e,ne,s,owner,full)*value(e,ne,s,j)/100.0;
 double built[5]={0,0,0,0,0};
 for(Order targets=unique_order(s->target_order[j]);targets;targets>>=3){int who=(targets&7)-1;if(who<0||who>=5)continue;
  double result=amount*(1.0+take_shield_amp(c,e,ne,s,who,full)/100.0);
  built[who]=result;
 }
 // Python assigns the completed comprehension only after all amplifiers have
 // queried the old shield maps. Keep old positivity visible until this commit.
 s->shield_present[j]=s->masks[j]&31;s->shield_mask[j]=0;
 for(int who=0;who<5;who++){s->shield_current[j][who]=s->shield_capacity[j][who]=built[who];if(built[who]>0)s->shield_mask[j]|=1<<who;}
 invalidate(s);
}
__device__ double shield_total(const double* e,State* s,int who,int capacity){
 FloatSum sum={0,0};for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&effect(e,s,j)[1]==0&&effect(e,s,j)[2]==45)add_sum(s,&sum,capacity?s->shield_capacity[j][who]:s->shield_current[j][who]);return finish_sum(sum);
}
__device__ int shield_protected(const double* c,const double* e,int ne,State* s,int maker,int full){
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(((int)effect(e,s,j)[213]&4)&&live_shield_recipient(c,e,ne,s,j,maker,full))return 1;
 return 0;
}
// Presence-based immunity deliberately does not resolve lazy masks or evaluate
// runtime conditions: pinned _has_immune and _consume_immune_charge do not.
__device__ int harmful_blocked(const double* c,const double* e,int ne,State* s,int who,const double* incoming,int full){
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(!s->alive[j]||s->masks[j]<0||!(s->masks[j]&(1<<who)))continue;
  if(q[262]==1||q[262]==2&&incoming[35]>0&&q[263]==incoming[3])return 1;
 }
 // Same-named carriers share the maximum capacity, never the sum. Ordered
 // groups spend in the order of their first active carrier, per recipient.
 double caps[NE]={0};int seen[NE]={0},keys[NE],n=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(!s->alive[j]||q[262]!=3||s->masks[j]<0||!(s->masks[j]&(1<<who)))continue;
  int key=(int)q[3];if(!seen[key]){seen[key]=1;keys[n++]=key;}
  caps[key]=mx(caps[key],recipient_value(c,e,ne,s,j,who,full));
 }
 for(int i=0;i<n;i++){int key=keys[i];if(s->immune_used[who][key]<caps[key]){s->immune_used[who][key]+=1.0;return 1;}}
 return 0;
}
__device__ int filter_harmful(const double* c,const double* e,int ne,State* s,const double* q,int original_mask,Order* ordered,int full){
 Order kept=0;int mask=0,shift=0;
 for(Order raw=*ordered;raw;raw>>=3){int who=(raw&7)-1;if(who<0||harmful_blocked(c,e,ne,s,who,q,full))continue;
  kept|=Order(who+1)<<shift;shift+=3;mask|=1<<who;
 }
 // The interpreter's ordered notification list contains allies only. The
 // enemy sentinel is still a real application recipient and must not vanish.
 if((original_mask&(1<<5))&&!harmful_blocked(c,e,ne,s,5,q,full))mask|=1<<5;
 *ordered=kept;return mask;
}

__device__ int end_shield(const double* c,const double* e,int ne,State* s,const double* env,int j,int uid,double t,int full){
 if(!s->alive[j]||s->entry_seq[j]!=uid)return 0;const double* q=effect(e,s,j);int def=s->definition[j];
 s->alive[j]=0;s->stacks[j]=0;s->dot_present[j]=0;if(first_instance(e,s,def)<0)s->timer_active[def]=0;invalidate(s);
 return q[35]>0?notify(c,e,ne,s,env,t,29,(int)q[0],(int)q[3],full):0;
}
__device__ __noinline__ int absorb_shield(const double* c,const double* e,int ne,State* s,const double* env,int who,double amount,double t,int pierce,int full){
 int slots[NS],uids[NS],definitions[NS],ended[NS],ended_uid[NS],n=0,nended=0,code=0;double old_left[NS];
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&effect(e,s,j)[1]==0&&effect(e,s,j)[2]==45&&s->shield_current[j][who]>0&&t<s->end[j]){
  int at=n++;while(at>0&&s->activated[slots[at-1]]<=s->activated[j]){slots[at]=slots[at-1];at--;}
  slots[at]=j;
 }
 if(!pierce&&n>1)n=1;
 for(int k=0;k<n;k++){int j=slots[k];uids[k]=s->entry_seq[j];definitions[k]=s->definition[j];old_left[k]=s->shield_current[j][who];}
 double total=0;
 for(int k=0;k<n;k++){
  int j=slots[k],same=s->entry_seq[j]==uids[k];const double* q=e+definitions[k]*EW;
  if(shield_protected(c,e,ne,s,(int)q[0],full)){total+=amount;continue;}
  double left=same?s->shield_current[j][who]:old_left[k],taken=mn(left,amount);total+=taken;
  if(same)s->shield_current[j][who]=left-taken;
  if(left-taken<=0){
   if(same){s->shield_current[j][who]=0;s->shield_mask[j]&=~(1<<who);}
   invalidate(s);
   if(same&&q[260]>0){int any=0;for(int p=0;p<5;p++)if(s->shield_current[j][p]>0)any=1;if(!any){ended[nended]=j;ended_uid[nended++]=uids[k];}}
   code|=notify(c,e,ne,s,env,t,43,who,0,full);
  }
 }
 for(int k=0;k<nended;k++)code|=end_shield(c,e,ne,s,env,ended[k],ended_uid[k],t,full);
 s->last_shield_result=total;return code;
}
__device__ double heal_shield(const double* e,State* s,int who,double amount,double t){
 if(amount<=0)return 0;int slots[NS],n=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&effect(e,s,j)[1]==0&&effect(e,s,j)[2]==45&&(s->shield_present[j]&(1<<who))&&t<s->end[j]){
  int at=n++;while(at>0&&s->activated[slots[at-1]]<s->activated[j]){slots[at]=slots[at-1];at--;}slots[at]=j;
 }
 double left=amount,total=0;
 for(int k=0;k<n;k++){int j=slots[k];double room=s->shield_capacity[j][who]-s->shield_current[j][who];if(room<=0)continue;
  double put=mn(room,left);s->shield_current[j][who]+=put;total+=put;left-=put;if(s->shield_current[j][who]>0)s->shield_mask[j]|=1<<who;if(left<=0)break;
 }
 if(total>0)invalidate(s);return total;
}
__device__ double decoy_capacity(const double* e,State* s,int who){
 FloatSum total={0,0};for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&effect(e,s,j)[1]==0&&effect(e,s,j)[2]==72)add_sum(s,&total,s->shield_capacity[j][who]);return finish_sum(total);
}
// Snapshot capacities of resident decoy carriers, newest activation first.
// Strict < preserves original resident order for equal timestamps (not UID).
// An empty recipient can heal while another recipient keeps the carrier alive.
__device__ double heal_decoy(const double* e,State* s,int who,double amount,double t){
 if(amount<=0)return 0;int slots[NS],n=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&effect(e,s,j)[1]==0&&effect(e,s,j)[2]==72&&(s->shield_present[j]&(1<<who))&&t<s->end[j]){
  int at=n++;while(at>0&&s->activated[slots[at-1]]<s->activated[j]){slots[at]=slots[at-1];at--;}slots[at]=j;
 }
 double left=amount,total=0;
 for(int k=0;k<n;k++){int j=slots[k];double room=s->shield_capacity[j][who]-s->shield_current[j][who];if(room<=0)continue;
  double put=mn(room,left);s->shield_current[j][who]+=put;total+=put;left-=put;if(left<=0)break;
 }
 if(total>0)invalidate(s);return total;
}

__device__ int expire(const double* c,const double* e,State* s,int ne,const double* env,double t,int full){
 int removed[NS],masks[NS],n=0,code=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->end[j]<=t&&(s->alive[j])){removed[n]=j;masks[n++]=s->masks[j];lifecycle_retire(e,s,j);s->alive[j]=0;s->stacks[j]=0;s->dot_present[j]=0;invalidate(s);}
 for(int k=1;k<n;k++){int j=removed[k],mask=masks[k],at=k;while(at>0&&s->entry_seq[j]<s->entry_seq[removed[at-1]]){removed[at]=removed[at-1];masks[at]=masks[at-1];at--;}removed[at]=j;masks[at]=mask;}
 for(int step=0;step<n;step++){
  int j=removed[step],mask=masks[step];const double* expired=effect(e,s,j);double activated=s->activated[j];
  if(expired[35]>0){
   code|=notify(c,e,ne,s,env,t,29,(int)expired[0],(int)expired[3],full);
   // Verbose CPU logs resolve an unread expired carrier after end callbacks.
   // Resolve its old key without overwriting a newly activated slot.
   if(mask<0&&expired[4]==19){Order discarded=0;mask=cached_random_target(e,s,expired,activated,&discarded);}
  }
  if(effect(e,s,j)[2]==39||effect(e,s,j)[2]==40||effect(e,s,j)[2]==84||effect(e,s,j)[2]==86)for(int who=0;who<5;who++)if(mask>=0&&(mask&(1<<who))){s->hp[who]=mn(s->hp[who],max_hp(c,e,ne,s,who,full));sync_hp(c,e,ne,s,who,full);code|=notify(c,e,ne,s,env,t,52,who,0,full);}
 }
 for(int i=0;i<5;i++)if(s->mode_end[i]<=t&&s->mode[i]>=0){int j=s->mode[i];s->mode[i]=-1;invalidate(s);if(effect(e,s,j)[35]>0)code|=notify(c,e,ne,s,env,t,29,i,(int)effect(e,s,j)[3],full);}
 return code;
}
__device__ __noinline__ double damage(const double* c,const double* e,int ne,State* s,const double* env,int who,int full,double coeff,int normal,int flags,int basis=0,double hp_pct=0){
 if(env[2]>0&&!(flags&131072)){flags&=~1024;if((flags&65536)&&s->part_min==0&&env[67]>0)flags|=1024;}
 const double* a=c+who*CW;double b[ST];for(int k=0;k<ST;k++)b[k]=stat(c,e,ne,s,who,k,full);
 double defense=(flags&512)?0:mx(env[0]*(1+b[2]/100)+b[3],0)*(1-b[4]/100);double attack=mx(a[0]*(1+b[0]/100)+b[1]-defense,0);
 if(basis){double converted=max_hp(c,e,ne,s,who,full,1)*hp_pct/100;attack=mx((basis==2?converted:a[0]*(1+b[0]/100)+(b[1]+converted))-defense,0);}
 double crit=mn(normal?b[5]:b[24],1)*mx(.5+(normal?b[6]:b[25])/100,0);
 double spread=a[13];
 if(s->started[who])spread=a[10]>0?a[9]+(a[13]-a[9])*mn(s->warm[who],a[10])/a[10]:a[9];
 const double* mode=s->weapon_context[who]&&s->mode[who]>=0?effect(e,s,s->mode[who]):0;
 double core=(flags&131072)?0:(flags&16384)?1:(flags&256)?(env[1]>0?1:0):(normal||(flags&32768))&&env[1]>0?mn(1,pow(env[1]/mx(spread*(1-.00908*b[21]),1),2.55)):0;
 double bonus=1+crit+(full?.5:0)+(normal&&optimal_range(c,e,ne,s,who,full,1)?.3:0)+core*((mode?mode[228]:a[12])-100+b[7])/100;
 double f5=1+b[10]/100;
 if(flags&1){f5+=b[13]/100;if(flags&4096)f5+=stat(c,e,ne,s,who,56,full)/100;if(flags&8192)f5+=stat(c,e,ne,s,who,57,full)/100;}
 if(flags&64)f5+=stat(c,e,ne,s,who,35,full)/100;if(flags&512)f5+=stat(c,e,ne,s,who,51,full)/100;if(flags&128)f5+=stat(c,e,ne,s,who,50,full)/100;
 if(flags&8)f5+=b[16]/100;if(flags&4)f5+=b[15]/100;if(flags&2)f5+=b[14]/100;if(flags&1024)f5+=stat(c,e,ne,s,who,54,full)/100;if(flags&2048)f5+=stat(c,e,ne,s,who,55,full)/100;
 double f6=1+b[12]/100;if(flags&16)f6+=b[27]/100;
 double charge=(flags&32)?(mode?mode[226]:a[19])/100*(1+b[9]/100)+b[8]/100:1;
 double d=(coeff*(normal?1+b[11]/100:1)/100)*attack*bonus*charge*f5*f6*(a[15]>.5?1.1+b[17]/100:1);
 return mx((double)__double2ll_rn(d),1);
}
struct ReachHit {int reach;double damage;};
__device__ __noinline__ ReachHit reach_sample(const double* c,const double* e,int ne,State* s,const double* env,int who,int full,double coeff,int normal,int flags,int basis=0,double hp_pct=0){
 ReachHit out={0,0};if(env[2]<=0||s->part_min<=0)return out;
 int reach=(flags&65536)?5:(flags&8)?(stat(c,e,ne,s,who,64,full)>=100-1e-9?4:3):(flags&64)?(stat(c,e,ne,s,who,63,full)>=100-1e-9?2:1):0;
 if(reach<s->part_min)return out;
 out.reach=reach;out.damage=damage(c,e,ne,s,env,who,full,coeff,normal,(flags&~(256|16384))|1024|131072,basis,hp_pct);return out;
}

struct FieldResult {int code,row,phase,uid,is_new,changed,stack,mask,rawmask,lazy,immune_name,immune_mask;Order order,raworder;};
__device__ FieldResult apply_field(const double* c,const double* e,int ne,State* s,int j,int mask,Order activation_order,double expires,double t,int full,TargetRef recipient){
 FieldResult result={};const double* q=effect(e,s,j);
  int rawmask=mask;Order raworder=activation_order;int owner=(int)q[0];
  if(q[43]>=0){j=(int)q[43];q=effect(e,s,j);}
  int definition=s->definition[j],existing=-1;
  int lazy=lazy_target(q);
  for(int k=s->slot_head;k>=0;k=s->slot_next[k]){
   if(!s->alive[k]||effect(e,s,k)[58]!=q[58]||(rawmask&32)&&!same_enemy_ref(s->enemy_recipient[k],recipient))continue;
   if(lazy||q[62]>=0||s->masks[k]==rawmask&&s->target_order[k]==raworder){existing=k;break;}
  }
  if(existing<0&&q[205]>0&&q[35]>0){
   for(int k=s->slot_head;k>=0;k=s->slot_next[k]){const double* other=effect(e,s,k);if(!s->alive[k]||s->end[k]<=t||other[58]==q[58]||other[205]<=0||s->runtime_cond[k]||other[0]!=q[0]||other[3]!=q[3]||other[206]!=q[206]||other[9]!=q[9])continue;
    int same=rawmask<0?(other[4]==q[4]&&other[5]==q[5]&&other[48]==q[48]&&other[49]==q[49]):(s->masks[k]==rawmask&&s->target_order[k]==raworder);
    if(same&&(!(rawmask&32)||same_enemy_ref(s->enemy_recipient[k],recipient))){existing=k;break;}
   }
  }
  if(existing>=0){j=existing;q=effect(e,s,j);}
  else{j=fresh_slot(s,ne,definition);if(j<0){result.code=16;return result;}q=effect(e,s,j);}
  invalidate(s);int was_alive=s->alive[j];double previous=s->stacks[j];double initial_capture=q[10]>=0&&q[208]>=0?captured_ref(e,ne,s,owner,(int)q[10]):-1;Order order=raworder;if(mask<0&&was_alive&&s->masks[j]>=0){mask=s->masks[j];order=s->target_order[j];}
  if(!s->alive[j]){s->runtime_cond[j]=q[7]<0&&q[217]>0;new_entry(s,j);s->stacks[j]=1;}else if(q[9]!=1)s->stacks[j]=q[9]<0?s->stacks[j]+1:mn(s->stacks[j]+1,q[9]);
  s->activated[j]=t;s->masks[j]=mask;s->target_order[j]=order;if(mask&32)s->enemy_recipient[j]=recipient;if(mask<0)s->lazy_dirty=1;s->end[j]=expires;if(!was_alive)s->capture[j]=initial_capture;
  if(q[62]>=0){
   s->bullet_initialized[j]=1;int lazy=lazy_target(q);
   if(!lazy){for(int k=0;k<6;k++){int had=was_alive&&s->bullets[j][k]>0;if(mask>=0&&(mask&(1<<k))){s->bullets[j][k]=(int)q[62];s->bullet_stacks[j][k]=had?(q[9]<0?s->bullet_stacks[j][k]+1:(int)mn(s->bullet_stacks[j][k]+1,q[9])):1;}else{s->bullets[j][k]=0;s->bullet_stacks[j][k]=0;}}s->bullet_left[j]=-1;}
   else{if(!was_alive)for(int k=0;k<6;k++)s->bullets[j][k]=0;s->bullet_left[j]=(int)q[62];}
  }
  lifecycle_prepare(c,e,ne,s,j,full);

 result.row=j;result.uid=s->entry_seq[j];result.is_new=!was_alive;result.immune_mask=rawmask;result.changed=previous!=s->stacks[j];result.stack=(int)s->stacks[j];result.mask=mask;result.rawmask=rawmask;result.order=order;result.raworder=raworder;result.lazy=lazy_target(q);result.immune_name=q[262]==3?(int)q[3]:-1;return result;
}

struct SkillSequence {int row,left,count,reach;double hit,part,crit;};
// Explicit bounded DFS preserves synchronous nested stack-reach order.
__device__ __noinline__ int notify(const double* c,const double* e,int ne,State* s,const double* env,double t,int ev,int who,int arg,int full,double core_frac,int hit_crit,double healing_pool,int resumed_hits,double parent_dealt,TargetRef event_target){
 int track_target=s->event_interest&INTEREST_TARGET_CONTEXT;
 TargetScope target_scope(s,track_target);TargetRef targets[32];int context_depth=0;
 TargetRef body={ACTOR_BODY,0,1};
 if(track_target){TargetRef root=event_target.kind>=0?event_target:inherits_event_target(ev)?s->condition_target:body;targets[0]=root;set_condition_target(s,root);}
 if(ev==29)for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(!s->alive[j]&&effect(e,s,j)[0]==who&&effect(e,s,j)[3]==arg)lifecycle_retire(e,s,j);
 unsigned short (*ended)[NS]=s->event_slots;int (*ending_stack)[NS]=s->event_stacks;int ended_count[32],ended_pos[32];for(int j=0;j<32;j++)ended_count[j]=ended_pos[j]=0;
 int gauge_id[32],gauge_owner[32],ammo_left[32],ammo_owner[32],named_event[32];double gauge_cursor[32],gauge_end[32];
 FieldResult post[32];int queue_arg[32];for(int i=0;i<32;i++){post[i].row=-1;queue_arg[i]=-1;}
 int field_row[32],field_mask[32],field_pos[32]={0},field_count[32]={0};Order field_order[32];double field_end[32];
 int repeat_row[32],repeat_left[32],repeat_passive[32];for(int i=0;i<32;i++)repeat_left[i]=0;
 Order queue[32];int iev[32],iwho[32],iarg[32],icount[32],cursor[32],queue_event[32],healrow[32];for(int j=0;j<32;j++){queue[j]=0;healrow[j]=-1;gauge_id[j]=-1;ammo_left[j]=0;named_event[j]=-1;}Order revival_queue[32];int revival_actor[32],revival_cursor[32];double revival_pct[32];int depth=0;iev[0]=ev;iwho[0]=who;iarg[0]=arg;icount[0]=ev==9?(int)ref(e,ne,s,who,arg):0;cursor[0]=0;
 Order health_queue[32],reduce_queue[32];double health_amount[32],reduce_amount[32];int health_add[32];
 Order share_queue[32];int share_weight[32][5],share_total[32];double share_pool[32],release_pool[32];share_pool[0]=healing_pool;
 int hp_changed[32],hp_owner[32],hp_cursor[32],hp_phase[32];double hp_prev[32],hp_new[32];
 SkillSequence skill_sequence[32];int forced_row[32],forced_cursor[32],forced_crit[32];double forced_core[32];
 while(depth>=0){
  if(s->hp_edge_error)return 1;
  if(track_target){
   if(depth>context_depth)targets[depth]=inherits_event_target(iev[depth])?targets[depth-1]:body;
   context_depth=depth;set_condition_target(s,targets[depth]);
  }
  if(s->hp_pending){
   if(depth==31)return 1;depth++;iev[depth]=53;iwho[depth]=0;iarg[depth]=0;cursor[depth]=0;
   hp_changed[depth]=s->hp_pending-1;hp_prev[depth]=s->hp_edge_prev;hp_new[depth]=s->hp_edge_new;hp_phase[depth]=0;hp_owner[depth]=0;hp_cursor[depth]=0;
   s->hp_pending=0;s->in_hp_edge=1;
   // Restore a returned parent before pushing a fresh HP continuation at a
   // reused depth; the previous child's target must not survive that reuse.
   if(track_target){targets[depth]=body;context_depth=depth;set_condition_target(s,body);}
  }
  if(iev[depth]==53){
   int pushed=0,changed=hp_changed[depth];
   while(!pushed&&hp_phase[depth]<2){
    while(!pushed&&hp_owner[depth]<5){
     int owner=hp_owner[depth];
     while(hp_cursor[depth]<ne*EVS){
      int at=hp_cursor[depth]++,j=at/EVS,a=at%EVS;const double* q=e+j*EW;if((int)q[0]!=owner||a>=(int)q[144])continue;
      const double* d=q+TD+a*TS;int kind=-(int)d[6],tag=(int)d[3];
      if((d[0]!=31&&d[0]!=48)||kind<11||kind>14)continue;
      int downward=hp_new[depth]<hp_prev[depth];
      if(downward){
       if(hp_phase[depth]==0){if(kind!=12&&!(kind==11&&owner==changed))continue;}
       else if(kind!=13||abs(owner-changed)!=1||(s->down_mask&(1<<changed)))continue;
       if(!(hp_prev[depth]>d[4]+1e-6&&hp_new[depth]<=d[4]+1e-6))continue;
      }else if(hp_phase[depth]!=0||kind!=14||abs(owner-changed)!=1||(s->down_mask&(1<<changed)))continue;
      // Python's notify index visits each event key once in registration order,
      // even when multiple definitions or timing descriptors share the key.
      int seen=0;for(int p=0;p<at&&!seen;p++){const double* older=e+(p/EVS)*EW;if(older[0]!=owner||p%EVS>=(int)older[144])continue;const double* prior=older+TD+(p%EVS)*TS;if(prior[0]==d[0]&&prior[3]==tag)seen=1;}
      if(seen)continue;
      if(s->hp_log_enabled){if(s->hp_log_count>=1024)return 1;double* log=s->hp_log[s->hp_log_count++];log[0]=t;log[1]=owner;log[2]=tag;}
      int event_code=(int)d[0];if(depth==31)return 1;depth++;iev[depth]=event_code;iwho[depth]=owner;iarg[depth]=tag;icount[depth]=0;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post[depth].row=-1;queue_arg[depth]=-1;ended_count[depth]=ended_pos[depth]=0;pushed=1;break;
     }
     if(!pushed){hp_owner[depth]++;hp_cursor[depth]=0;}
    }
    if(!pushed){hp_phase[depth]++;hp_owner[depth]=0;hp_cursor[depth]=0;}
   }
   if(!pushed){s->in_hp_edge=0;depth--;}
   continue;
  }
  // A parent skill freezes its damage/critical chance before the hit loop.
  // Child hit notifications finish synchronously before the next parent hit.
  if(iev[depth]==55){
   s->heal_source=iev[depth-1]==16?iarg[depth-1]:-1;
   SkillSequence* sequence=skill_sequence+depth;const double* q=effect(e,s,sequence->row);int owner=(int)q[0],name=(int)q[3];
   if(sequence->left<=0){add_burst(s,burst_gain(c,e,ne,s,owner,s->weapon_context[owner]?s->prev_mode[owner]:-1,sequence->count,0,full,q[251]>0?q[250]:-1));depth--;continue;}
   sequence->left--;s->total[owner]+=sequence->hit;
   if(s->squad_mode||s->impact_enabled||(s->event_interest&(INTEREST_DAMAGE_ACCUM|INTEREST_TARGET_COUNTER))){if(s->land_count>=1024)return 4;int k=s->land_count++;s->land_owner[k]=owner;s->land_family[k]=(int(q[39])&128)?HIT_DOT:HIT_SKILL;s->land_damage[k]=sequence->hit;s->land_reach[k]=sequence->reach;s->land_part[k]=sequence->part;}
   int critical=sequence->crit>=1;
   if(sequence->crit>0&&sequence->crit<1){double* fraction=&s->named_skill_crit[owner][name];*fraction+=sequence->crit;if(*fraction>=1){*fraction-=1;critical=1;}}
   if(depth==31)return 1;depth++;iev[depth]=49;iwho[depth]=owner;iarg[depth]=name;icount[depth]=critical;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post[depth].row=-1;queue_arg[depth]=-1;ended_count[depth]=ended_pos[depth]=0;continue;
  }
  // Forced use activates the selected slot once without touching event counts
  // or resetting the slot's periodic grid. Selection is compiled data.
  if(iev[depth]==56){
   s->heal_source=iev[depth-1]==16?iarg[depth-1]:-1;
   const double* forced=effect(e,s,forced_row[depth]);int selected=-1;
   while(forced_cursor[depth]<ne){int j=forced_cursor[depth]++;if(!((unsigned int)forced[B3_MASK+j/32]&(1u<<(j%32))))continue;
    const double* q=effect(e,s,j);if(!condition(c,e,ne,s,q,full,0,-1,forced_core[depth],forced_crit[depth]))continue;selected=j;break;}
   if(selected<0){depth--;continue;}
   int owner=(int)effect(e,s,selected)[0],critical=forced_crit[depth];double core=forced_core[depth];
   if(depth==31)return 1;depth++;iev[depth]=47;iwho[depth]=owner;iarg[depth]=selected;icount[depth]=critical;forced_core[depth]=core;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post[depth].row=-1;queue_arg[depth]=-1;ended_count[depth]=ended_pos[depth]=0;continue;
  }
  // Private continuation: finish all allocated body heals and synchronous
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
  if(cursor[depth]==0){revival_queue[depth]=0;revival_actor[depth]=-1;revival_cursor[depth]=0;revival_pct[depth]=0;health_queue[depth]=reduce_queue[depth]=0;}
  if(health_queue[depth]){
   int recipient=(health_queue[depth]&7)-1;health_queue[depth]>>=3;
   if(health_add[depth])s->hp[recipient]=mn(s->hp[recipient]+health_amount[depth],max_hp(c,e,ne,s,recipient,full));
   sync_hp(c,e,ne,s,recipient,full);continue;
  }
  if(reduce_queue[depth]){int recipient=(reduce_queue[depth]&7)-1;reduce_queue[depth]>>=3;double old=s->hp[recipient],after=mx(0,old*(1-reduce_amount[depth]/100));if(after<old){double amount=old-after,remaining=absorb_heal_storage(c,e,ne,s,recipient,amount,full);after+=amount-remaining;}s->hp[recipient]=after;sync_hp(c,e,ne,s,recipient,full);continue;}
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
    depth++;iev[depth]=47;iwho[depth]=caster;iarg[depth]=definition;icount[depth]=0;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post[depth].row=-1;queue_arg[depth]=-1;ended_count[depth]=ended_pos[depth]=0;pushed=1;break;
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
  // Personal notifications stop at their entry boundary while down. Existing
  // DOT/instant timers (28), self_down (38), and shared counters keep their
  // distinct CPU paths. Apply this to nested FSM frames as well as the root.
  if(cursor[depth]==0&&repeat_left[depth]<=0&&post[depth].row<0&&iev[depth]!=28&&iev[depth]!=57&&iev[depth]!=38&&iev[depth]!=26&&iev[depth]!=44&&iev[depth]!=45&&(s->down_mask&(1<<iwho[depth]))){depth--;continue;}
  if(ended_pos[depth]<ended_count[depth]){
   if(depth==31)return 1;int at=ended_pos[depth]++,k=ended[depth][at],stack=ending_stack[depth][at];depth++;iev[depth]=stack<0?29:9;iwho[depth]=(int)effect(e,s,k)[0];iarg[depth]=(int)effect(e,s,k)[3];icount[depth]=stack<0?0:stack;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post[depth].row=-1;queue_arg[depth]=-1;ended_count[depth]=ended_pos[depth]=0;continue;
  }
  if(gauge_id[depth]>=0){
   int gid=gauge_id[depth],gowner=gauge_owner[depth];double next=1e30;
   for(int k=0;k<ne;k++){const double* r=effect(e,s,k);if((int)r[0]!=gowner)continue;
    for(int a=0;a<(int)r[144];a++){const double* d=r+TD+a*TS;if(d[0]!=30||d[3]!=gid)continue;double step=d[1];double boundary=(floor(gauge_cursor[depth]/step)+1)*step;if(boundary<=gauge_end[depth]&&boundary<next)next=boundary;}
   }
   if(next<1e30){if(depth==31||next>2147483647||next<-2147483647)return 8;gauge_cursor[depth]=next;depth++;iev[depth]=30;iwho[depth]=gowner;iarg[depth]=gid;icount[depth]=(int)next;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post[depth].row=-1;queue_arg[depth]=-1;ended_count[depth]=ended_pos[depth]=0;continue;}
   gauge_id[depth]=-1;
  }
  if(ammo_left[depth]>0){
   // No listener can observe these notices, including nested resource notices.
   if(s->event_offsets[26]==s->event_offsets[27]){ammo_left[depth]=0;continue;}
   if(depth==31)return 1;int attacker=ammo_owner[depth];ammo_left[depth]--;depth++;iev[depth]=26;iwho[depth]=attacker;iarg[depth]=0;icount[depth]=0;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post[depth].row=-1;queue_arg[depth]=-1;ended_count[depth]=ended_pos[depth]=0;continue;
  }
  if(named_event[depth]>=0){
   if(depth==31)return 1;int name=named_event[depth],caster=ammo_owner[depth];named_event[depth]=-1;depth++;iev[depth]=31;iwho[depth]=caster;iarg[depth]=name;icount[depth]=0;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post[depth].row=-1;queue_arg[depth]=-1;ended_count[depth]=ended_pos[depth]=0;continue;
  }
  if(queue[depth]){
   if(depth==31)return 1;int recipient=(queue[depth]&7)-1,event=queue_event[depth],source=queue_arg[depth];queue[depth]>>=3;
   double pool=0;if(healrow[depth]>=0){const double* heal=effect(e,s,healrow[depth]);source=(int)heal[0];double amount=heal[6];if(heal[10]>=0)amount*=ref(e,ne,s,source,(int)heal[10]);double base=heal[50]>0?max_hp(c,e,ne,s,source,full):c[recipient*CW+28];pool=(heal[1]==32?release_pool[depth]:base*amount/100)*heal_multiplier(c,e,ne,s,recipient,full,source);event=54;}
   depth++;share_pool[depth]=pool;iev[depth]=event;iwho[depth]=recipient;iarg[depth]=source;icount[depth]=0;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post[depth].row=-1;queue_arg[depth]=-1;continue;
  }
  if(post[depth].row>=0){
   int r=post[depth].row,owner=(int)effect(e,s,r)[0];const double* q=effect(e,s,r);
   int phase=post[depth].phase++;
   if(phase==0&&!post[depth].is_new&&q[9]!=1&&post[depth].changed&&q[35]>0||phase==2&&post[depth].is_new&&q[35]>0){
    if(depth==31)return 1;int stack=phase==2?1:post[depth].stack;depth++;iev[depth]=9;iwho[depth]=owner;iarg[depth]=(int)q[3];icount[depth]=stack;cursor[depth]=0;queue[depth]=0;healrow[depth]=-1;gauge_id[depth]=-1;ammo_left[depth]=0;named_event[depth]=-1;repeat_left[depth]=0;post[depth].row=-1;queue_arg[depth]=-1;ended_count[depth]=ended_pos[depth]=0;continue;
   }
   if(phase==1&&(post[depth].is_new||q[9]!=1)&&q[202]>0){
    int mask=post[depth].mask;Order order=post[depth].order;if(!post[depth].is_new&&s->entry_seq[r]==post[depth].uid){mask=s->masks[r];order=s->target_order[r];}
    queue[depth]=q[201]>0?(mask<0?owner+1:filter_order(order,mask)):22737;queue_event[depth]=(int)q[202]-1;queue_arg[depth]=(int)q[203];healrow[depth]=-1;continue;
   }
   if(phase==3){
    if(!post[depth].is_new&&s->entry_seq[r]==post[depth].uid&&s->alive[r]){s->capture[r]=q[10]>=0&&q[208]>=0?captured_ref(e,ne,s,owner,(int)q[10]):-1;invalidate(s);}
    if(q[204]>=0&&!post[depth].lazy){queue[depth]=post[depth].raworder;queue_event[depth]=31;queue_arg[depth]=(int)q[204];healrow[depth]=-1;continue;}
   }
   if(phase==4){int emitted=-1,stop=0;Order targets=0;
    r=lifecycle_activate(c,e,ne,s,r,full,q,post[depth].uid,post[depth].lazy,post[depth].rawmask,&emitted,&targets,&stop);
    if(stop){if(emitted>=0){queue[depth]=targets;queue_event[depth]=emitted;queue_arg[depth]=-1;healrow[depth]=-1;}continue;}
   }
   if(phase>=5&&post[depth].immune_name>=0&&post[depth].immune_mask>0){for(int who=0;who<6;who++)if(post[depth].immune_mask&(1<<who))s->immune_used[who][post[depth].immune_name]=0;}
   if(phase>=5){r=lifecycle_instance(e,s,r,post[depth].uid);if(!post[depth].lazy&&r>=0){const double* health=effect(e,s,r);int mask=post[depth].rawmask;if(mask>=0&&health[1]==0&&!lazy_target(health)){
    if(health[2]>=38&&health[2]<=41){health_queue[depth]=filter_order(post[depth].raworder,mask);health_amount[depth]=c[(int)health[0]*CW+28]*(s->stacks[r]>0?value(e,ne,s,r)/s->stacks[r]:0)/100;health_add[depth]=health[2]==38||health[2]==39;}
    if(health[2]==84||health[2]==86){health_queue[depth]=filter_order(s->target_order[r],s->masks[r]);health_amount[depth]=s->shield_current[r][health[2]==86?1:0];health_add[depth]=health_amount[depth]>0;}
   }}post[depth].row=-1;continue;}
   continue;
  }
  if(field_pos[depth]<field_count[depth]){
   post[depth]=apply_field(c,e,ne,s,field_row[depth],field_mask[depth],field_order[depth],field_end[depth],t,full,captured_field_target(s,depth,field_pos[depth]++));if(post[depth].code)return post[depth].code;continue;
  }
  s->heal_source=iev[depth]==16?iarg[depth]:-1;
  int event=iev[depth],direct=event==28||event==47||event==57||event==61;
  int available=direct?(iarg[depth]>=0&&iarg[depth]<ne):(event>=0&&event<EVENT_KINDS?s->event_offsets[event+1]-s->event_offsets[event]:0);
  if(cursor[depth]>=available&&repeat_left[depth]<=0){depth--;continue;}
  int repeated=repeat_left[depth]>0;
  int j=repeated?repeat_row[depth]:direct?iarg[depth]:s->event_definitions[s->event_offsets[event]+cursor[depth]];
  if(repeated)repeat_left[depth]--;else cursor[depth]++;
  const double* q=effect(e,s,j);int owner=(int)q[0];
  if(event==28||event==47||event==57||event==61){if(j!=iarg[depth])continue;}else{
  if(event!=26&&event!=44&&event!=45&&owner!=iwho[depth])continue;
  int matched=repeated,passive=repeated?repeat_passive[depth]:0,multiplicity=0;
  // CPU indexes each timing separately, including duplicate event keys. Count
  // once per notification, then replay each indexed activation synchronously.
  if(!repeated)for(int a=0;a<(int)q[144];a++){
   const double* d=q+TD+a*TS;if((int)d[0]!=event)continue;
   int threshold=(int)d[1],mode=(int)d[2];if(d[6]==1&&event!=4)threshold=reduced_count(e,s,q,threshold);
   if((event==4||event==41)&&iarg[depth]!=(int)d[6])continue;
   if(event==6&&iarg[depth]!=j)continue;
   if((event==9||event==29||event==30||event==31||event==39||event==48||event==49||event==50||event==58||event==59)&&(int)d[3]!=iarg[depth])continue;
   if(event==9&&icount[depth]!=(int)d[4])continue;
   if(event==27&&iarg[depth]!=threshold)continue;
   if(event==62&&iarg[depth]!=threshold)continue;
   multiplicity++;int ok=1;
   if(event==7||event==8||mode>0){s->count[j][a]++;int ct=s->count[j][a];ok=mode==2?ct>=threshold:mode==3?ct==threshold:ct%threshold==0;}
   if(d[6]==2&&event!=4&&event!=41)ok=0;
   if(event==30&&icount[depth]%threshold!=0)ok=0;
   if(ok&&!matched){matched=1;passive=(int)d[5];}
  }
  if(!matched)continue;
  if((event==44||event==45)&&owner!=iwho[depth])continue;
  // Shared counts advance even while the listener's source is down. Its
  // activation is suppressed only after those counters have been updated.
  if((event==26||event==44||event==45)&&((s->down_mask&(1<<owner))||q[268]>0&&(s->down_mask&(1<<((int)q[268]-1)))))continue;
  if(!repeated&&event!=6&&multiplicity>1){repeat_row[depth]=j;repeat_left[depth]=multiplicity-1;repeat_passive[depth]=passive;}
  int cond_met=condition(c,e,ne,s,q,full,0,-1,depth==0?core_frac:0,depth==0?hit_crit:event==49?icount[depth]:0,(event==44||event==45)?(int)q[268]-1:-1);if(!cond_met&&!(event==0&&q[7]<0&&passive))continue;
  if(q[56]>0&&s->cast_mask!=(int)q[56]-1)continue;
  }
  int kind=(int)q[1],budget=q[269]>0?(int)q[269]-1:(int)q[58];Order activation_order=0;
  if(kind==0&&q[2]==87&&actor_dead(s,(int)q[296],(int)q[297],(int)q[298]))continue;
  if(event!=57&&event!=61&&(event!=28||q[69]>0)){
   if(q[57]>=0&&s->activations[budget]>=q[57])continue;
   if(q[57]>=0&&q[256]>0&&!lazy_target(q)&&!target(c,e,ne,q,5,s,full,0,1))continue;
   s->activations[budget]++;
  }
  // Periodic instants resolve on ticks, direct damage and weapon changes do
  // not resolve recipients. Their optional budget probe above is independent.
  int mask=0,registration=q[59]>0&&event!=28&&event!=61;
  if((kind==27||kind==31)&&!registration&&q[6]==0)continue;
  if(!(q[258]==1&&registration)&&kind!=2&&kind!=33&&!((kind==3||kind==34)&&!registration))mask=target(c,e,ne,q,5,s,full,&activation_order,q[258]==1||kind==19);
  if(q[59]>0&&event!=28&&event!=61){
   int staged_count=0;if(q[340]>0){double raw=q[342]<4096?q[342]:(ref_present(e,s,owner,(int)q[342]-4096)?ref(e,ne,s,owner,(int)q[342]-4096):1);if(raw<0||raw>RAMP_STEPS)return 8;staged_count=(int)raw;if(!staged_count)continue;}
   double expires=q[7]<0?1e30:t+q[7];int original=j;
   if(kind==3&&(int(q[39])&128)&&q[9]==1)for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(k!=j&&effect(e,s,k)[0]==owner&&effect(e,s,k)[3]==q[3]&&(int(effect(e,s,k)[39])&128)&&effect(e,s,k)[9]==1&&s->dot_present[k]&&s->timer_active[k]){j=k;q=effect(e,s,j);break;}
   int was=s->timer_active[j],preserve=kind==3&&(int(q[39])&128)&&was&&q[340]<=0;
   if(!preserve){if(s->timer_epoch[j]==2147483647)return 8;s->timer_epoch[j]++;}
   if(!was){s->timer_seq[j]=++s->timer_clock;if(kind!=3){int code=index_instant_timer(s,j);if(code)return code;}}
   if(!(kind==3&&(int(q[39])&128)&&was))s->timer_at[j]=t+(kind==3&&q[60]>0?0:q[59]);
   s->timer_active[j]=1;s->timer_end[j]=expires;
   if(kind==3){
    int had=s->dot_present[j];if(!had){s->runtime_cond[j]=q[7]<0&&q[217]>0;new_entry(s,j);s->activated[j]=t;}
    double stack=1;if(q[10]>=0){if(s->gauge_present[owner][(int)q[10]])stack=ref(e,ne,s,owner,(int)q[10]);else for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(effect(e,s,k)[0]==owner&&effect(e,s,k)[3]==q[10]&&(s->alive[k])){stack=s->stacks[k];break;}}
    if(q[10]>=0)s->stacks[j]=stack;else if(!had)s->stacks[j]=1;else s->stacks[j]=q[9]<0?s->stacks[j]+1:mn(s->stacks[j]+1,q[9]);
    s->dot_present[j]=1;s->end[j]=expires;s->masks[j]=mask;s->capture[j]=-1;if(mask<0)s->lazy_dirty=1;invalidate(s);
    if(q[340]>0){ramp_remove(e,s,j);if(!had)s->ramp_epoch[j]=0;if(!s->ramp_on[j])s->ramp_active++;s->ramp_on[j]=1;s->ramp_count[j]=staged_count;s->ramp_index[j]=0;s->ramp_epoch[j]++;s->ramp_uid[j]=s->entry_seq[j];s->ramp_seq[j]=++s->ramp_clock;s->ramp_start[j]=t;s->stacks[j]=0;double last=t+staged_count*q[340];s->timer_at[j]=last+q[343];s->timer_end[j]=s->end[j]=q[7]<0?1e30:last+q[7];if(ramp_insert(e,s,j))return 8;}
   }
   continue;
  }
  if(kind==37){ammo_left[depth]=(int)mx(0,(int)q[6]-1);ammo_owner[depth]=owner;continue;}
  if(kind==35){int error=source_refresh(s,q,t);if(error)return error;invalidate(s);continue;}
  if(kind==36){
   // A nested notification starts with no parent damage; returning restores the root scope.
   double amount=(depth==0?parent_dealt:0)*q[6]/100;if(amount<=0)continue;
   double hit=(double)__double2ll_rz(amount);s->total[owner]+=hit;
   if(s->land_count>=1024)return 4;int k=s->land_count++;s->land_owner[k]=owner;s->land_family[k]=HIT_SKILL;s->land_damage[k]=hit;s->land_reach[k]=0;s->land_part[k]=0;continue;
  }
  if(kind==34){
   double pool=take_damage_accum(e,s,(int)q[36]);if(pool<=0)continue;
   double hit=(double)__double2ll_rz(pool*(1+stat(c,e,ne,s,owner,27,full)/100));s->total[owner]+=hit;
   if(s->land_count>=1024)return 4;int k=s->land_count++;s->land_owner[k]=owner;s->land_family[k]=(int(q[39])&128)?HIT_DOT:HIT_SKILL;s->land_damage[k]=hit;s->land_reach[k]=0;s->land_part[k]=0;continue;
  }
  if(kind==33){
   int critical=depth==0?hit_crit:(event==49||event==47)?icount[depth]:0;
   double core=depth==0?core_frac:event==47?forced_core[depth]:0;
   if(depth==31)return 1;depth++;iev[depth]=56;forced_row[depth]=j;forced_cursor[depth]=0;forced_crit[depth]=critical;forced_core[depth]=core;continue;
  }
  if(kind>=9&&kind<=11){
   int gid=(int)q[64];if(q[65]>=0)s->gauge_cap[owner][gid]=q[65];double old=s->gauges[owner][gid],now,consumed=q[6]==-1?old:mn(q[6],old);
   if(kind==9){double cap=s->gauge_cap[owner][gid];for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(effect(e,s,k)[0]==owner&&effect(e,s,k)[1]==12&&effect(e,s,k)[64]==gid&&s->alive[k])cap+=effect(e,s,k)[70];now=mn(old+q[6],cap);}
   else{
    double floor=q[294],available=mx(0,old-floor);
    now=q[6]==-1?floor:mx(floor,old-q[6]);
    // Preserve requested/available precision, never invert the remainder.
    consumed=q[6]==-1?available:mx(0,mn(q[6],available));
   }
   s->gauges[owner][gid]=now;s->gauge_present[owner][gid]=1;invalidate(s);
   if(kind==9&&now>old){gauge_id[depth]=gid;gauge_owner[depth]=owner;gauge_cursor[depth]=old;gauge_end[depth]=now;}
   if(kind==11&&consumed>0){if(consumed>2147483647)return 8;ammo_left[depth]=(int)consumed;ammo_owner[depth]=owner;}
   continue;
  }
  if(kind==27){
   for(Order recipients=activation_order;recipients;recipients>>=3){int recipient=(recipients&7)-1;if(recipient<0||recipient>=5)continue;
    double base=q[50]>0?max_hp(c,e,ne,s,owner,full):shield_total(e,s,recipient,1);heal_shield(e,s,recipient,base*q[6]/100.0,t);
   }continue;
  }
  if(kind==31){
   for(Order recipients=activation_order;recipients;recipients>>=3){int recipient=(recipients&7)-1;if(recipient<0||recipient>=5)continue;
    double base=q[50]>0?max_hp(c,e,ne,s,owner,full):decoy_capacity(e,s,recipient);heal_decoy(e,s,recipient,base*q[6]/100.0,t);
   }continue;
  }
  if(kind==24){add_burst(s,q[6]);continue;}
  if(kind==25){s->burst_pending[owner]=(int)q[254];s->burst_pending_present[owner]=1;continue;}
  if(kind==28){if(mask&32){int limit=q[6]==0?1:q[6]<=0?0:q[6]>=BP?BP:(int)q[6];int code=boss_dispel(s,t,limit);if(code)return code;}continue;}
  if(kind==26){
   // CPU strips oldest harmful entries independently per recipient, atomically.
   // A fractional positive limit still selects its first entry; zero means all.
   int limit=q[6]>0?(q[6]>=NS?NS:(int)mx(1,(int)q[6])):NS,taken[5]={0,0,0,0,0},enemy_taken[WORLD_ACTORS]={0};
   for(int k=s->slot_head;k>=0;k=s->slot_next[k]){
    if(!s->alive[k]||effect(e,s,k)[209]!=2||s->masks[k]<0)continue;
    int selected=selected_field_mask(s,k,q,mask),stripped=0;
    for(int recipient=0;recipient<5;recipient++)if((selected&(1<<recipient))&&taken[recipient]<limit){stripped|=1<<recipient;taken[recipient]++;}
    if(selected&32){TargetRef receiver=s->enemy_recipient[k];int index=world_actor_index(s,receiver.kind,receiver.identity);if(index>=0&&enemy_taken[index]<limit){stripped|=32;enemy_taken[index]++;}}
    if(!stripped)continue;
    s->masks[k]&=~stripped;s->target_order[k]=filter_order(s->target_order[k],s->masks[k]);
    for(int f=0;f<=depth;f++)if(post[f].row==k&&post[f].uid==s->entry_seq[k]){post[f].mask=s->masks[k];post[f].order=s->target_order[k];}
    if(!s->masks[k]){if(effect(e,s,k)[1]==0&&effect(e,s,k)[2]==76){s->shield_present[k]=0;s->shield_current[k][0]=0;}s->alive[k]=0;s->stacks[k]=0;s->dot_present[k]=0;}
   }
   // Unlike named removal, cleanse emits no end events and retains timers and
   // the surviving entry's independent shield/bullet maps.
   invalidate(s);continue;
  }
  if(kind==23){
   for(Order recipients=activation_order;recipients;recipients>>=3){int recipient=(recipients&7)-1;if(recipient>=5||s->reload[recipient]>0)continue;
    s->ammo[recipient]=0;start_reload(c,e,ne,s,recipient,full,t);
   }continue;
  }
  if(kind==13||kind==14){
   for(Order recipients=activation_order;recipients;recipients>>=3){int recipient=(recipients&7)-1;
    double maximum=full_ammo(c,e,ne,s,recipient,full);
    double v=q[6];double add=kind==13?(double)__double2ll_rn(maximum*(v/100)):(double)(long long)v;
    s->ammo[recipient]=kind==13?mx(0,mn(s->ammo[recipient]+add,maximum)):mn(s->ammo[recipient]+add,maximum);
   }
   if(kind==13&&q[202]>0){queue[depth]=owner+1;queue_event[depth]=(int)q[202]-1;queue_arg[depth]=(int)q[203];healrow[depth]=-1;}continue;
  }
  if(kind==29){revival_queue[depth]=activation_order;revival_pct[depth]=q[6];continue;}
  // Cover resurrection is distinct from healing: broken living recipients
  // only, their stored maximum, no cover_healed notification and no cap to100%.
  if(kind==30){double pct=q[6];for(Order recipients=activation_order;recipients;recipients>>=3){int recipient=(recipients&7)-1;if(s->cover_hp[recipient]>0)continue;s->cover_hp[recipient]=mx(0,s->cover_max[recipient]*pct/100);invalidate(s);}continue;}
  if(kind==8){reduce_queue[depth]=activation_order;reduce_amount[depth]=q[6];continue;}
  if(kind==7){if(q[6]!=0){Order kept=0;int shift=0;for(Order raw=activation_order;raw;raw>>=3){int who=(raw&7)-1;if(s->cover_hp[who]<=0)continue;double base=q[50]>0?max_hp(c,e,ne,s,owner,full):s->cover_max[who];s->cover_hp[who]=mn(s->cover_max[who],s->cover_hp[who]+base*q[6]/100);kept|=Order(who+1)<<shift;shift+=3;}queue[depth]=kept;queue_event[depth]=17;queue_arg[depth]=-1;healrow[depth]=-1;}continue;}
  if(kind==32){release_pool[depth]=take_heal_charge(e,s,owner,(int)q[36]);queue[depth]=activation_order;queue_event[depth]=16;queue_arg[depth]=-1;healrow[depth]=j;continue;}
  if(kind==6){queue[depth]=activation_order;queue_event[depth]=16;queue_arg[depth]=-1;healrow[depth]=j;continue;}
  if(kind==5){for(Order recipients=activation_order;recipients;recipients>>=3){int k=(recipients&7)-1;s->ready[k]=mx(t,s->ready[k]-q[6]);}continue;}
  if(kind==22){
   if(q[6]!=0){double factor=mx(0,1-q[6]/100);for(int k=0;k<ne;k++)if(effect(e,s,k)[44]>0&&s->period_initialized[k]&&(mask&(1<<(int)effect(e,s,k)[0])))s->period_at[k]=t+mx(0,s->period_at[k]-t)*factor;}
   continue;
  }
  if(kind==18){
   int already=0;for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[3]==q[36]&&s->masks[k]>=0&&(s->masks[k]&(1<<owner))){already=1;break;}
   double raw=q[6]==0?1:q[6];if(fabs(raw)>2147483647)return 8;int count=(int)raw,definition=(int)q[215];
   if(already||count<=0||q[212]<=0||definition<0)continue;
   const double* source=e+definition*EW;Order source_order=0;int targets=target(c,e,ne,source,5,s,full,&source_order);
   int r=fresh_slot(s,ne,definition);if(r<0)return 16;
   double capture=source[10]>=0&&source[208]>=0?captured_ref(e,ne,s,owner,(int)source[10]):-1;
   s->runtime_cond[r]=source[208]<0&&source[217]>0;new_entry(s,r);s->stacks[r]=source[9]<0?count:mn(count,source[9]);s->activated[r]=t;s->end[r]=source[208]<0?1e30:t+source[208];s->masks[r]=targets;s->target_order[r]=source_order;s->capture[r]=capture;if(targets<0)s->lazy_dirty=1;invalidate(s);lifecycle_prepare(c,e,ne,s,r,full);
   if(lifecycle_init_hp(source)&&targets>=0){health_queue[depth]=filter_order(source_order,targets);health_amount[depth]=0;health_add[depth]=0;}
   continue;
  }
  if(kind==16||kind==17||kind==19||kind==20||kind==21){
   double raw=kind==19?q[6]:(q[6]==0?1:q[6]);
   if((kind==20||kind==21)&&q[10]>=0){int found=s->gauge_present[owner][(int)q[10]];for(int k=s->slot_head;k>=0&&!found;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[0]==owner&&effect(e,s,k)[3]==q[10])found=1;if(found)raw=ref(e,ne,s,owner,(int)q[10]);}
   if(fabs(raw)>2147483647)return 8;int delta=(int)raw;if(kind==17||kind==21)delta=-delta;
   if(kind==19&&delta<=0)continue;
   int recipients=mask;for(int who=0;who<5;who++)if(stack_immune(e,s,who))recipients&=~(1<<who);recipients&=kind==19?31:63;
   ended_count[depth]=ended_pos[depth]=0;
   for(int k=s->slot_head;k>=0;k=s->slot_next[k]){
    if(!s->alive[k])continue;const double* source=effect(e,s,k);int targets=s->masks[k];
    if(kind==19){
     if(source[210]<=0||source[209]!=1||source[9]==1)continue;
     if(targets<0)targets=ranked_target(c,e,ne,s,source,full);
     if(!(targets&recipients)||(targets&~recipients))continue;
    }else if(kind==16||kind==17){if(source[3]!=q[36]||targets<0||!(targets&(1<<owner))||stack_immune(e,s,owner))continue;}
    else{if(q[212]>0?source[3]!=q[36]:(source[209]!=2||source[9]<=1))continue;if(targets<0||!selected_field_mask(s,k,q,recipients))continue;if((targets&32)&&stack_immune_ref(e,s,5,s->enemy_recipient[k]))continue;}
    double previous=s->stacks[k],cap=source[9]<0?previous+delta:source[9];
    s->stacks[k]=(kind==20||kind==21)&&q[212]>0?mx(0,mn(previous+delta,cap)):kind==19?mn(previous+delta,cap):mx(1,mn(previous+delta,cap));
    if(kind==19&&s->bullet_initialized[k]&&source[62]>=0&&source[9]!=1&&!lazy_target(source))for(int who=0;who<6;who++)if(s->bullet_stacks[k][who]>0)s->bullet_stacks[k][who]=source[9]<0?s->bullet_stacks[k][who]+delta:(int)mn(s->bullet_stacks[k][who]+delta,source[9]);
    invalidate(s);int changed=previous!=s->stacks[k];
    if((kind==16||kind==17)&&delta>0||kind==19&&changed){if(s->end[k]<1e30&&source[208]>0){s->activated[k]=t;s->end[k]=t+source[208];}}
    if((kind==16||kind==17||kind==19)&&delta>0&&changed&&source[35]>0){
     if(s->stacks[k]>2147483647||s->stacks[k]<0)return 8;int at=ended_count[depth]++;ended[depth][at]=(unsigned short)k;ending_stack[depth][at]=(int)s->stacks[k];
    }
   }continue;
  }
  if(kind==1){
   invalidate(s);ended_count[depth]=ended_pos[depth]=0;
   for(int k=s->slot_head;k>=0;k=s->slot_next[k])if((int)effect(e,s,k)[3]==(int)q[36]&&(s->alive[k])){
    // Match CPU target-list removal: lazy states stay unresolved, shield/bullet maps persist while the instance survives.
    if(q[142]>0){int stripped=selected_field_mask(s,k,q,mask);if(!stripped)continue;s->masks[k]&=~stripped;s->target_order[k]=filter_order(s->target_order[k],s->masks[k]);for(int f=0;f<=depth;f++)if(post[f].row==k&&post[f].uid==s->entry_seq[k]){post[f].mask=s->masks[k];post[f].order=s->target_order[k];}if(s->masks[k])continue;}
    lifecycle_retire(e,s,k);s->alive[k]=0;s->stacks[k]=0;s->dot_present[k]=0;if(first_instance(e,s,s->definition[k])<0)s->timer_active[s->definition[k]]=0;if(q[142]<=0&&effect(e,s,k)[35]<=0)continue;int at=ended_count[depth]++;
    while(at>0&&s->entry_seq[k]<s->entry_seq[ended[depth][at-1]]){ended[depth][at]=ended[depth][at-1];ending_stack[depth][at]=ending_stack[depth][at-1];at--;}ended[depth][at]=(unsigned short)k;ending_stack[depth][at]=-1;
   }continue;
  }
  if(kind==15){
   for(int k=s->slot_head;k>=0;k=s->slot_next[k])if((s->alive[k])&&s->end[k]<1e30&&s->masks[k]>=0){
    int name=(int)effect(e,s,k)[3],slot=EXTEND_MASK+name/32;
    if(((unsigned int)q[slot]&(1u<<(name%32)))&&selected_field_mask(s,k,q,mask)){s->end[k]+=q[6];if(s->dot_present[k]&&s->timer_active[k])s->timer_end[k]=s->end[k];invalidate(s);}
   }continue;
  }
  if(kind==2){
   int prior=s->mode[owner];invalidate(s);
   if(((int)q[213]&128)&&prior>=0&&effect(e,s,prior)[3]==q[3]){
    s->mode[owner]=-1;s->mode_end[owner]=-1;queue[depth]=owner+1;queue_event[depth]=29;queue_arg[depth]=(int)q[3];healrow[depth]=-1;continue;
   }
   s->mode[owner]=j;s->mode_end[owner]=q[7]<0?1e30:t+q[7];if(q[202]>0){queue[depth]=22737;queue_event[depth]=(int)q[202]-1;queue_arg[depth]=(int)q[203];healrow[depth]=-1;}continue;
  }
  if(kind==3){
   if(q[6]==0)continue;
   // Deferred B3 bonus damage has its own hit-count rule in the CPU handler:
   // Named target references repeat the referenced attack's literal hit count.
   // Coefficient scaling remains independent; ordinary targets still hit once.
   // The coefficient reference is read when full burst starts, not at enqueue.
   if(q[51]==1){if(s->burst_damage_count>=NE)return 4;int at=s->burst_damage_count++;s->burst_damage_rows[at]=j;s->burst_damage_hits[at]=(int)mx(1,q[52]);s->burst_damage_mag[at]=q[35]>0?named_magnitude(c,e,ne,s,78,(int)q[3],owner,owner,full):1;continue;}
   double v=q[6];if((int(q[39])&128)&&(q[10]>=0||q[10]==-2)){
    double scale=0;int found=0;
    if(event==61){scale=q[341]>=0?q[341]:s->stacks[j];found=1;}
    for(int k=found?-1:s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[0]==owner&&effect(e,s,k)[3]==q[3]){scale=s->stacks[k];found=1;break;}
    if(!found)scale=ref(e,ne,s,owner,(int)q[255]);v*=scale;
   }
   int count=(int)q[61];if(q[136]>=0&&event!=57){int name=(int)q[136],found=s->gauge_present[owner][name];if(q[137]==2)count=found?(int)s->gauges[owner][name]:0;else{found|=source_find(s,owner,name)>=0;for(int k=s->slot_head;k>=0&&!found;k=s->slot_next[k])if(effect(e,s,k)[0]==owner&&effect(e,s,k)[3]==name&&(s->alive[k]))found=1;count=found?(int)ref(e,ne,s,owner,name):1;}}
   if(event==57)count=resumed_hits;
   if(q[35]>0)v*=named_magnitude(c,e,ne,s,78,(int)q[3],owner,owner,full);
   if(v==0)continue;
   if(q[51]==2&&event!=57){
    // Activation gates/budget were already checked. Only the stat count is
    // captured here; magnitude and damage buffs are sampled at landing.
    double raw_count=q[52]<4096?q[52]:ref(e,ne,s,owner,(int)q[52]-4096);
    if(raw_count>4096||raw_count<-2147483647)return 8;int latched=(int)raw_count;
    if(latched>4096||s->burst_damage_count>=NE)return 8;
    int at=s->burst_damage_count++;s->burst_damage_rows[at]=j;s->burst_damage_hits[at]=latched;s->burst_damage_mag[at]=1;continue;
   }
   if(count>4096)return 8;
   if(count>0&&q[35]>0&&(event==57||(s->named_hit_interest[(int)q[3]]&(1<<owner)))){
    SkillSequence frozen;frozen.row=j;frozen.left=frozen.count=count;
    frozen.hit=damage(c,e,ne,s,env,owner,full,v,(int(q[39])&256)?1:0,(int)q[39],(int)q[53],q[54]);
    frozen.crit=stat(c,e,ne,s,owner,(int(q[39])&256)?5:24,full);
    ReachHit part=reach_sample(c,e,ne,s,env,owner,full,v,(int(q[39])&256)?1:0,(int)q[39],(int)q[53],q[54]);frozen.reach=part.reach;frozen.part=part.damage;
    // The parent's exclusion list scopes its frozen damage only. Nested
    // named-hit handlers observe the ordinary live buffs, as on the CPU.
    if(event==57){for(int k=0;k<MASK_WORDS;k++)s->excluded[k]=0;invalidate(s);}
    if(depth==31)return 1;depth++;iev[depth]=55;skill_sequence[depth]=frozen;continue;
   }
   for(int hitno=0;hitno<count;hitno++){
    double hit=damage(c,e,ne,s,env,owner,full,v,(int(q[39])&256)?1:0,(int)q[39],(int)q[53],q[54]);s->total[owner]+=hit;
    if(s->squad_mode||s->impact_enabled||(s->event_interest&(INTEREST_DAMAGE_ACCUM|INTEREST_TARGET_COUNTER))){if(s->land_count>=1024)return 4;int k=s->land_count++;s->land_owner[k]=owner;s->land_family[k]=(int(q[39])&128)?HIT_DOT:HIT_SKILL;s->land_damage[k]=hit;ReachHit part=reach_sample(c,e,ne,s,env,owner,full,v,(int(q[39])&256)?1:0,(int)q[39],(int)q[53],q[54]);s->land_reach[k]=part.reach;s->land_part[k]=part.damage;}
   }add_burst(s,burst_gain(c,e,ne,s,owner,s->weapon_context[owner]?s->prev_mode[owner]:-1,count,0,full,q[251]>0?q[250]:-1));continue;
  }
  if(q[209]==2&&mask>=0){mask=filter_harmful(c,e,ne,s,q,mask,&activation_order,full);if(!mask)continue;}
  if((mask&32)&&q[4]==4&&q[48]==ENEMY_SELECT_ALL){
   field_row[depth]=j;field_mask[depth]=mask;field_order[depth]=activation_order;field_end[depth]=expires_at(e,ne,s,q,t);field_pos[depth]=0;
   field_count[depth]=capture_enemy_receivers(s,depth);if(field_count[depth]<0)return -field_count[depth];
  }else{
   // The common single-carrier path needs no batch snapshot or continuation.
   TargetRef recipient=(mask&32)&&q[4]==4&&q[48]==ENEMY_SELECT_CURRENT?logical_enemy_ref(s->condition_target):TargetRef{ACTOR_BODY,0,1};
   post[depth]=apply_field(c,e,ne,s,j,mask,activation_order,expires_at(e,ne,s,q,t),t,full,recipient);if(post[depth].code)return post[depth].code;
  }

 }
 return 0;
}
// The pinned CPU sums percentage modifiers without runtime gating, but
// gates both named flat groups and concatenates interval before cooldown.
__device__ double every_interval(const double* c,const double* e,int ne,State* s,const double* q,int full,double base){
 int owner=(int)q[0];FloatSum percentage={0,0},flat_amount={0,0};
 for(int k=s->slot_head;k>=0;k=s->slot_next[k]){const double* m=effect(e,s,k);if(s->alive[k]&&m[1]==0&&m[2]==58&&(s->masks[k]<0||(s->masks[k]&(1<<owner))))add_sum(s,&percentage,value(e,ne,s,k));}
 if(q[35]>0)for(int group=1;group<=2;group++)for(int k=s->slot_head;k>=0;k=s->slot_next[k]){const double* m=effect(e,s,k);if(s->alive[k]&&m[220]==group&&m[222]>0&&m[221]==q[3]&&(s->masks[k]<0||(s->masks[k]&(1<<owner)))&&base_condition(c,e,ne,s,m,full,1,k,0,0,0,3,owner))add_sum(s,&flat_amount,value(e,ne,s,k));}
 double interval=mx(0,base+finish_sum(flat_amount))*mx(0,1+finish_sum(percentage)/100);
 return mx(interval,base*.05);
}
// All clocks are authored input times. Timers select their own due times and
// preserve dictionary insertion order, without CPU event traces.
// Listener definitions are immutable during a kernel invocation. Build their
// per-owner registration order once rather than rescan/deduplicate every seal.
__device__ __noinline__ int build_group_plans(const double* e,State* s){
 for(int owner=0;owner<5;owner++)s->ag_plan_count[owner]=0;
 for(int at=s->event_offsets[62];at<s->event_offsets[63];at++){
  int row=s->event_definitions[at];const double* q=e+row*EW;int owner=(int)q[0];if(owner>=5)continue;
  for(int a=0;a<(int)q[144];a++){const double* d=q+TD+a*TS;if(d[0]!=62)continue;int threshold=(int)d[1],seen=0,n=s->ag_plan_count[owner];
   for(int p=0;p<n;p++)if(s->ag_plan[owner][p]==threshold)seen=1;
   if(!seen){if(n>=AT)return 8;s->ag_plan[owner][n]=threshold;s->ag_plan_count[owner]++;}
  }
 }return 0;
}
__device__ __noinline__ int group_dispatch(const double* c,const double* e,int ne,State* s,const double* env,int k,double t,int full){
 if(k<0||s->ag_active[k]!=2||t<s->ag_open[k])return 8;
 int owner=s->ag_owner[k];
 s->ag_active[k]=3;
 int targets=s->ag_count[k],used=s->ag_plan_count[owner];
 int code=0;
 for(int p=0;p<used;p++){int threshold=s->ag_plan[owner][p];if(targets>=threshold)code|=notify(c,e,ne,s,env,t,62,owner,threshold,full);}
 s->ag_active[k]=0;
 return code;
}
__device__ __noinline__ int tick_staged(const double* c,const double* e,int ne,State* s,const double* env,double t,int full){
 if(!s->ramp_heap_n)return 0;int code=0,steps=0;s->when=t;
 while(s->ramp_heap_n){
  int j=s->ramp_heap[0];const double* q=e+j*EW;
  if(!s->alive[j]||!s->timer_active[j]||s->ramp_uid[j]!=s->entry_seq[j]){ramp_remove(e,s,j);s->ramp_on[j]=0;s->ramp_active--;continue;}
  double due=s->ramp_start[j]+(s->ramp_index[j]+1)*q[340];if(due>t)break;
  if(++steps>4096)return code|8;ramp_remove(e,s,j);s->ramp_index[j]++;
  s->stacks[j]=q[9]<0?s->ramp_index[j]:mn(s->ramp_index[j],q[9]);
  if(s->ramp_index[j]>=s->ramp_count[j]){s->ramp_on[j]=0;s->ramp_active--;}else{int error=ramp_insert(e,s,j);if(error)return code|error;}
  // Commit the next node before children; a refresh removes/replaces it by row.
  invalidate(s);code|=notify(c,e,ne,s,env,t,61,(int)q[0],j,full);
 }
 return code;
}
__device__ __noinline__ int tick_effects(const double* c,const double* e,int ne,State* s,const double* env,double t,int full){
 int code=tick_staged(c,e,ne,s,env,t,full),touched=0;TimerSnapshot timers;capture_timers(e,s,ne,1,&timers);
 for(int pass=0;pass<timers.count;pass++){
  int j=timers.row[pass],epoch=timers.epoch[pass];if(!timer_owned(s,j,epoch))continue;const double* q=effect(e,s,j);
  double end=s->timer_end[j],limit=q[60]>0?end-1e-6:end+1e-6;
  if(s->timer_at[j]>limit){s->timer_active[j]=0;continue;}
  if(t<s->timer_at[j])continue;
  double when=t>=end?end-1e-4:t;s->when=when;touched=1;invalidate(s);
  advance_timer(s,j,epoch,q[59]);
  code|=notify(c,e,ne,s,env,when,28,(int)q[0],j,full);
 }
 s->when=t;if(touched)invalidate(s);
 // Source clocks run after damage timers and before carrier expiry. Snapshot
 // owner/channel bounds; children may refresh or append without re-entering.
 int sources=s->source_count,owners=s->source_owner_count;
 for(int p=0;p<owners;p++)for(int at=0;at<sources;at++){
  if(s->source_owner[at]!=s->source_owner_order[p]||s->source_next[at]<0||t<s->source_next[at])continue;
  int population=source_population(s,at,t);if(!population){s->source_next[at]=-1;continue;}
  int epoch=s->source_epoch[at];double next=s->source_next[at]+source_interval(s,at,population);
  code|=notify(c,e,ne,s,env,t,s->source_legacy[at]?60:59,s->source_owner[at],s->source_name[at],full);
  if(s->source_epoch[at]==epoch)s->source_next[at]=next;
 }
 code|=expire(c,e,s,ne,env,t,full);
 for(int j=0;j<ne;j++){const double* q=effect(e,s,j);if(q[69]<=0||(s->down_mask&(1<<(int)q[0]))||!condition(c,e,ne,s,q,full,0))continue;
  int instance=first_instance(e,s,j);if(instance<0)code|=notify(c,e,ne,s,env,t,28,(int)q[0],j,full);
  else{double old=s->end[instance];s->end[instance]=mx(old,expires_at(e,ne,s,q,t));if(old<=t&&s->end[instance]>t)invalidate(s);}
 }
 for(int j=0;j<ne;j++){const double* q=effect(e,s,j);if(q[44]<=0)continue;
  // Each every timing is visited in source order and shares the definition clock.
  for(int a=0;a<(int)q[144];a++){const double* d=q+TD+a*TS;if(d[0]!=6)continue;
   double interval=every_interval(c,e,ne,s,q,full,d[1]);double next=s->period_initialized[j]?s->period_at[j]:interval;
   if(s->period_initialized[j]&&interval!=s->period_prev[j])next=t+mx(0,next-t)*(interval/s->period_prev[j]);
   s->period_initialized[j]=1;s->period_at[j]=next;s->period_prev[j]=interval;
   if(t>=next){code|=notify(c,e,ne,s,env,t,6,(int)q[0],j,full);s->period_at[j]=next+interval;s->period_prev[j]=interval;}
  }
 }
 capture_timers(e,s,ne,0,&timers);
 for(int pass=0;pass<timers.count;pass++){
  int j=timers.row[pass],epoch=timers.epoch[pass];if(!timer_owned(s,j,epoch))continue;const double* q=effect(e,s,j);
  if(t>=s->timer_end[j]){s->timer_active[j]=0;continue;}
  if(t<s->timer_at[j])continue;
  TargetRef observed=sample_control_aim(s,(int)q[0]);TargetScope scope(s,s->event_interest&INTEREST_TARGET_CONTEXT);if(scope.active)set_condition_target(s,observed);
  advance_timer(s,j,epoch,q[59]);
  if(q[60]!=2||base_condition(c,e,ne,s,q,full,1))code|=notify(c,e,ne,s,env,t,28,(int)q[0],j,full,0,0,0,-1,0,observed);
  // Children see the next deadline; cancellation or rescheduling remains final.
 }
 return code;
}
__device__ __noinline__ int consume_bullets(const double* c,const double* e,int ne,State* s,const double* env,double t,int who,int full){
 resolve_all(c,e,ne,s,full,1);int removed[NS],n=0,code=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);if(q[62]<0||!s->alive[j]||s->activated[j]==t&&q[63]==0)continue;
  if(s->bullets[j][who]>0){
   s->bullets[j][who]--;if(s->bullets[j][who]==0){s->masks[j]&=~(1<<who);invalidate(s);int left=0;for(int k=0;k<6;k++)if(s->bullets[j][k]>0)left=1;if(!left){s->alive[j]=0;s->stacks[j]=0;removed[n++]=j;}}
  }else if(q[0]==who&&s->bullet_left[j]>=0){s->bullet_left[j]--;if(s->bullet_left[j]<=0){s->alive[j]=0;s->stacks[j]=0;removed[n++]=j;invalidate(s);}}
 }
 for(int k=1;k<n;k++){int j=removed[k],at=k;while(at>0&&s->entry_seq[j]<s->entry_seq[removed[at-1]]){removed[at]=removed[at-1];at--;}removed[at]=j;}
 for(int pass=0;pass<n;pass++){int j=removed[pass];if(effect(e,s,j)[35]>0)code|=notify(c,e,ne,s,env,t,29,(int)effect(e,s,j)[0],(int)effect(e,s,j)[3],full);}
 return code;
}
// Exclusive reductions compare source-group percentages before rounding.
// This path is enabled only when such an instruction exists in the program;
// ordinary programs preserve their previous aggregation and arithmetic order.
__device__ __noinline__ int exclusive_ammo_total(const double* c,const double* e,int ne,State* s,int who,int full,double base,double step,int excluded,double* result){
 double values[NE];int present[NE],exclusive[NE],order[NE],n=0;
 for(int k=0;k<NE;k++){values[k]=0;present[k]=exclusive[k]=0;}
 camera_query(s,who);int lens=s->camera_lens;s->camera_lens=s->query_camera[who];
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(q[1]!=0||q[2]!=18||!s->alive[j]||s->end[j]<=s->when||!(s->masks[j]&(1<<who))||(excluded&&(s->excluded[s->definition[j]/32]&(1u<<(s->definition[j]%32))))||!base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))continue;
  int group=(int)q[45];if(!present[group]){present[group]=1;order[n++]=group;}
  values[group]+=recipient_value(c,e,ne,s,j,who,full);exclusive[group]|=q[55]>0;
 }
 int enabled=0,best=-1;
 for(int i=0;i<n;i++){int group=order[i];if(values[group]<0){if(exclusive[group])enabled=1;if(best<0||values[group]<values[best])best=group;}}
 if(enabled){double total=0;for(int i=0;i<n;i++){int group=order[i];if(values[group]<0&&group!=best)continue;total+=step>0?floor(base*(values[group]/100)/step+.5)*step:values[group];}*result=total;}
 s->camera_lens=lens;return enabled;
}
// Equipment entries with equal source/type/level are one rounding group.
__device__ double quant(const double* c,const double* e,int ne,State* s,int who,int key,int full,double base,double step){
 resolve_all(c,e,ne,s,full);if(key==20&&stat(c,e,ne,s,who,53,full)>0)return 0;double out=0;
 if(key==18&&(s->event_interest&INTEREST_EXCLUSIVE_AMMO)&&exclusive_ammo_total(c,e,ne,s,who,full,base,step,0,&out))return out;
 camera_query(s,who);int previous_lens=s->camera_lens;s->camera_lens=s->query_camera[who];
 if(key==20){double values[NE];int blocked[NE],n=charge_groups(c,e,ne,s,who,full,values,blocked);for(int i=0;i<n;i++)if(!blocked[i])out+=floor(base*(values[i]/100)/step+.5)*step;s->camera_lens=previous_lens;return out;}
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);if((int)q[1]!=0||((int)q[2]!=key&&!(key==20&&q[2]==37))||!s->alive[j]||s->end[j]<=s->when||!(s->masks[j]&(1<<who))||!base_condition(c,e,ne,s,q,full,1,j,0,0,0,3,who))continue;
  int seen=0;double v=0;
  for(int k=s->slot_head;k>=0;k=s->slot_next[k])if((int)effect(e,s,k)[1]==0&&((int)effect(e,s,k)[2]==key||(key==20&&effect(e,s,k)[2]==37))&&effect(e,s,k)[45]==q[45]&&s->alive[k]&&s->end[k]>s->when&&(s->masks[k]&(1<<who))&&base_condition(c,e,ne,s,effect(e,s,k),full,1,k,0,0,0,3,who)){if(s->entry_seq[k]<s->entry_seq[j])seen=1;double part=recipient_value(c,e,ne,s,k,who,full);if(effect(e,s,k)[2]==37){double raw=c[who*CW+29]>0?c[who*CW+29]:c[(int)effect(e,s,k)[0]*CW+29];part=raw>0?c[(int)effect(e,s,k)[0]*CW+29]*part/100/raw*100:0;}v+=part;}
  if(!seen)out+=floor(base*(v/100)/step+.5)*step;
 }
 s->camera_lens=previous_lens;return out;
}
__device__ __noinline__ double full_ammo(const double* c,const double* e,int ne,State* s,int who,int full){
 int mode=s->mode[who];const double* q=mode>=0?effect(e,s,mode):0;
 if(q&&q[27]!=-1){
  if(q[234]<0&&q[233]==0)return q[27];
  if(s->mode_ammo[who]<0){double base=q[27];
   if(q[234]>=0){double count=captured_ref(e,ne,s,who,(int)q[234]);s->mode_ammo[who]=base*(count<0?1:(int)count);}
   else s->mode_ammo[who]=q[233]>0?mx(1,base+quant(c,e,ne,s,who,18,full,base,1)+(double)__double2ll_rn(stat(c,e,ne,s,who,33,full))):base;
  }return s->mode_ammo[who];
 }
 double base=s->weapon_context[who]&&q?999999:c[who*CW+2];return mx(1,base+quant(c,e,ne,s,who,18,full,base,1)+(double)__double2ll_rn(stat(c,e,ne,s,who,33,full)));
}
__device__ double charge_duration(const double* c,const double* e,int ne,State* s,int who,int full){
 const double* a=c+who*CW;double base=s->weapon_context[who]&&s->mode[who]>=0?effect(e,s,s->mode[who])[225]:a[16];double cut=quant(c,e,ne,s,who,20,full,base,.01);
 double charge=mx(0,mx(0,base-cut)+stat(c,e,ne,s,who,34,full));
 if(stat(c,e,ne,s,who,53,full)>0){int best=-1;charge=base;for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(effect(e,s,k)[0]==who&&effect(e,s,k)[2]==53&&s->alive[k]&&effect(e,s,k)[139]>0){if(best<0||s->activated[k]>s->activated[best]||s->activated[k]==s->activated[best]&&s->entry_seq[k]>s->entry_seq[best])best=k;}if(best>=0)charge=effect(e,s,best)[138];}
 return charge;
}
// CPU folds identical pellet probabilities into one muzzle-level mean using
// builtin sum(); keep its floating-point summation and division order.
__device__ double bullet_core(State* s,double core,int pellets){FloatSum acc={0,0};for(int k=0;k<pellets;k++)add_sum(s,&acc,core);return finish_sum(acc)/pellets;}
// Per-pellet events use deterministic fractional accumulators in expected mode.
__device__ int fractional(const double* c,const double* e,int ne,State* s,const double* env,double t,int who,int full,int ev,double part){
 if((ev==44||ev==45)&&!(s->event_interest&(1<<(ev-44))))return 0;
 if(part<=0)return 0;if(part>=1)return notify(c,e,ne,s,env,t,ev,who,0,full);
 int index=ev==22?0:ev==23?1:ev==44?2:3; s->frac[who][index]+=part;int code=0;
 while(s->frac[who][index]>=1){s->frac[who][index]-=1;code|=notify(c,e,ne,s,env,t,ev,who,0,full);}return code;
}
__device__ int team_hit_event(const double* env,State* s){return (env[67]>0||(env[2]>0&&s->part_min>0))?44:45;}
__device__ double core_probability(const double* c,const double* e,int ne,State* s,const double* env,int who,int full){
 const double* a=c+who*CW;double spread=a[13];if(s->started[who])spread=a[10]>0?a[9]+(a[13]-a[9])*mn(s->warm[who],a[10])/a[10]:a[9];
 return env[1]>0?mn(1,pow(env[1]/mx(spread*(1-.00908*stat(c,e,ne,s,who,21,full)),1),2.55)):0;
}
__device__ int pellets(const double* c,const double* e,int ne,State* s,int who,int full){
 double fixed=stat(c,e,ne,s,who,48,full);return fixed>0?(int)mx(1,(double)__double2ll_rn(fixed)):(int)mx(1,(s->weapon_context[who]&&s->mode[who]>=0?effect(e,s,s->mode[who])[25]:c[who*CW+32])+(double)__double2ll_rn(stat(c,e,ne,s,who,47,full)));
}
__device__ double reload_duration(const double* c,const double* e,int ne,State* s,int who,int full){
 int found=0;double fixed=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&effect(e,s,j)[242]>0&&s->masks[j]>=0&&(s->masks[j]&(1<<who))){double v=value(e,ne,s,j);fixed=found?mx(fixed,v):v;found=1;}
 if(found)return fixed;
 return (s->weapon_context[who]&&s->mode[who]>=0?effect(e,s,s->mode[who])[237]:c[who*CW+3])*mx(0,1-stat(c,e,ne,s,who,19,full)/100);
}
__device__ void start_reload(const double* c,const double* e,int ne,State* s,int who,int full,double t){
 s->reload[who]=t+reload_duration(c,e,ne,s,who,full);s->reload_in_mode[who]=s->mode[who]>=0;
 int fire=s->weapon_context[who]&&s->mode[who]>=0?(int)effect(e,s,s->mode[who])[224]:(int)c[who*CW+8];if(fire==3)s->charge_phase[who]=0;
 s->charge_full[who]=-1;s->hold_release[who]=-1;s->hold_close[who]=-1;s->charging[who]=0;invalidate(s);
}
__device__ int control_open(const double* row,State* s,int who,int full){
 if(row[9]>0&&!(s->cycle_users[(int)row[9]-1]&(int)row[10]))return 0;
 int window=(int)row[1];return window==0?1:window==1?s->phase==0:window==2?s->phase!=0&&!full:full&&(s->cast_mask&(1<<who));
}
__device__ int control_entry(const double* c,State* s,int who,int full,int group){
 const double* a=c+who*CW;for(int j=0;j<(int)a[40];j++){const double* row=a+48+j*12;int mode=(int)row[0];if((group==0||group==1&&mode!=4||group==2&&mode>=2)&&control_open(row,s,who,full))return j;}return -1;
}
__device__ int control_owns(const double* c,State* s,int who){return c[43]!=0||s->ctrl_owner==who;}
__device__ void release_control(State* s,int who,double t){
 if(s->hold_release[who]>t){s->hold_release[who]=-1;s->hold_close[who]=-1;
  if(s->hold_kind[who]&&s->hold_reentry[who]!=s->hold_anchor[who]){s->hold_reentry[who]=s->hold_anchor[who];s->hold_anchor[who]=-1;}s->hold_kind[who]=0;
 }
}
__device__ int arbitrate_control(const double* c,State* s,double t,int full){
 int prio[5],edge[5],count=0,mode=(int)c[43];
 for(int who=0;who<5;who++){
  const double* a=c+who*CW;prio[who]=-1;int seq=s->ctrl_seq[who];
  if(seq<(int)a[41]&&t>=a[144+seq*2])prio[who]=99;
  else if(s->hold_release[who]>t&&(s->hold_close[who]<0||control_open(a+48+s->hold_close[who]*12,s,who,full)))prio[who]=s->ctrl_prio[who];
  else {int j=control_entry(c,s,who,full,0);if(j>=0&&a[48+j*12]!=0)prio[who]=(int)a[50+j*12];}
  edge[who]=prio[who]>=0&&!s->ctrl_prev[who];s->ctrl_prev[who]=prio[who]>=0;if(prio[who]>=0)count++;
 }
 if(mode){if(mode==2&&count>1)return 16;s->camera_mask=(int)c[42];return 0;}
 int owner=s->ctrl_owner;if(owner>=0&&prio[owner]<0){if(s->hold_close[owner]>=0)release_control(s,owner,t);owner=-1;}
 int pick=-1;
 for(int who=0;who<5;who++)if(prio[who]>=0&&(owner<0||who!=owner&&(prio[who]>prio[owner]||prio[who]==prio[owner]&&edge[who]))){
  if(pick<0||prio[who]>prio[pick]||prio[who]==prio[pick]&&edge[who]>edge[pick])pick=who;
 }
 if(pick>=0){if(owner>=0){release_control(s,owner,t);s->ctrl_preempt[owner]++;}owner=pick;}
 s->camera_mask=owner>=0?1<<owner:(int)c[42];s->ctrl_owner=owner;return 0;
}
__device__ double hold_threshold(const double* e,int ne,int who){double largest=-1;for(int j=0;j<ne;j++){const double* q=e+j*EW;if(q[0]!=who)continue;for(int a=0;a<(int)q[144];a++){const double* d=q+TD+a*TS;if(d[0]==39)largest=mx(largest,d[4]);}}return largest;}
__device__ void update_controls(const double* c,const double* e,int ne,State* s,double t,int who,int full){
 const double* a=c+who*CW;
 if(s->hold_close[who]>=0&&!control_open(a+48+s->hold_close[who]*12,s,who,full)){s->hold_close[who]=-1;s->hold_release[who]=-1;s->hold_kind[who]=0;}
 if(!control_owns(c,s,who))return;
 if(a[8]==3){int j=control_entry(c,s,who,full,2);if(j>=0){const double* row=a+48+j*12;int mode=(int)row[0];
   if(mode==3){s->hold_close[who]=j;s->hold_release[who]=1e30;s->ctrl_prio[who]=(int)row[2];}
   else if(s->fb_end>0&&s->hold_anchor[who]!=s->fb_end){s->hold_anchor[who]=s->fb_end;s->hold_kind[who]=1;s->ctrl_prio[who]=(int)row[2];
    if(mode==2)s->hold_release[who]=s->fb_end-row[3];
    else{double need=hold_threshold(e,ne,who);if(need>=0)s->hold_start[who]=s->fb_end+row[3]-charge_duration(c,e,ne,s,who,full)-need;}
   }
  }}
 while(s->ctrl_seq[who]<(int)a[41]&&t>=a[144+s->ctrl_seq[who]*2]){int j=s->ctrl_seq[who]++;if(a[8]==3){s->hold_close[who]=-1;s->hold_release[who]=a[145+j*2];s->ctrl_prio[who]=99;}}
}
// A clip fills a rounded fraction of the current full magazine; only its final
// completion emits full_reload. Even a zero-duration next clip waits a frame.
__device__ int finish_clip(const double* c,const double* e,int ne,State* s,int who,int full,double t){
 s->mode_ammo[who]=-1;double fullmag=full_ammo(c,e,ne,s,who,full),ratio=mn(1,mx(0,1+stat(c,e,ne,s,who,49,full)/100)/c[who*CW+34]);
 if(ratio<1){s->ammo[who]=mn(fullmag,s->ammo[who]+mx(1,floor(fullmag*ratio+.5)));if(s->ammo[who]<fullmag){start_reload(c,e,ne,s,who,full,t);return 0;}}
 else s->ammo[who]=fullmag;
 s->reload[who]=-1;s->reload_in_mode[who]=0;return 1;
}
__device__ int auto_frame(const double* c,const double* e,int ne,State* s,const double* env,double t,int who,int full){
 const double* a=c+who*CW;int mode=s->mode[who],prior=s->prev_mode[who];int status=0;
 if(stat(c,e,ne,s,who,28,full)>0)return status;
 if(!s->started[who]){s->started[who]=1;if(!s->squad_mode)s->ammo[who]=full_ammo(c,e,ne,s,who,full);}
 if(mode<0){
  if(s->reload[who]<=0)s->ammo[who]=mn(s->ammo[who],full_ammo(c,e,ne,s,who,full));
  if(s->post[who]>0){if(t<s->post[who])return status;s->post[who]=-1;s->next[who]=t;}
 }
 double rate=mode>=0?effect(e,s,mode)[28]:a[4],maxrate=mode>=0?effect(e,s,mode)[24]:a[5];
 double warmcap=mode>=0?effect(e,s,mode)[40]:a[6],cool=mode>=0?effect(e,s,mode)[41]:a[11];
 int warm_mode=mode>=0?effect(e,s,mode)[224]==2:a[8]==2;
 if(warm_mode && s->warm[who]>0){double idle=t-s->last[who];double inter=s->inter[who]>0?s->inter[who]:1/mx(rate,.01);if(idle>inter*1.5){s->warm[who]=mx(0,s->warm[who]-warmcap/cool*idle);s->last[who]=t;}}
 if(t<s->next[who])return status;
 if(s->ammo[who]<=0&&stat(c,e,ne,s,who,59,full)==0){start_reload(c,e,ne,s,who,full,t);return status;}
 double fr=warm_mode?rate+(maxrate-rate)*mn(s->warm[who],warmcap)/warmcap:rate;
 fr*=mx(.01,1+stat(c,e,ne,s,who,30,full)/100);
 int infinite=stat(c,e,ne,s,who,59,full)>0;int is_last=s->ammo[who]==1&&!infinite;if(is_last)status|=notify(c,e,ne,s,env,t,21,who,0,full);
 double cap=mx(warmcap,a[10]);if((warm_mode||a[10]>0)&&s->warm[who]<cap)s->warm[who]=mn(cap,s->warm[who]+mx(0,1+stat(c,e,ne,s,who,31,full)/100));
 if(!infinite){s->ammo[who]--;status|=notify(c,e,ne,s,env,t,26,who,0,full);}
 int split=pellets(c,e,ne,s,who,full),muzzles=(int)(mode>=0?effect(e,s,mode)[29]:a[33]),count=split*muzzles;if(count>512)return 8;
 const double* q=mode>=0?effect(e,s,mode):0;int skill=q&&q[235]>0;
 double coeff=(q?(s->mode_shots[who]==0&&q[236]>=0?q[236]:q[26]):a[1])/split;
 int flags=(skill?32768:0)|(stat(c,e,ne,s,who,36,full)>0?64:0)|(stat(c,e,ne,s,who,52,full)>0?512:0);double one=damage(c,e,ne,s,env,who,full,coeff,!skill,flags);ReachHit part=reach_sample(c,e,ne,s,env,who,full,coeff,!skill,flags);s->shot_reach[who]=part.reach;s->shot_part[who]=part.damage;
 double crit=mn(stat(c,e,ne,s,who,skill?24:5,full),1),core=core_probability(c,e,ne,s,env,who,full);
 s->hit_unit[who]=one;s->hits[who]=count;s->hit[who]=one*count;s->total[who]+=s->hit[who];s->shots[who]++;
 for(int hit=0;hit<count;hit++){status|=notify(c,e,ne,s,env,t,20,who,0,full);status|=fractional(c,e,ne,s,env,t,who,full,team_hit_event(env,s),1-core);status|=fractional(c,e,ne,s,env,t,who,full,22,crit);status|=fractional(c,e,ne,s,env,t,who,full,23,core);}
 int previous_threshold=0;
 for(int pass=0;pass<NE*EVS;pass++){
  int threshold=2147483647;
  for(int j=0;j<ne;j++){const double* q=effect(e,s,j);if((int)q[0]!=who)continue;for(int a=0;a<(int)q[144];a++){const double* d=q+TD+a*TS;if(d[0]==27&&d[1]>previous_threshold&&d[1]<=count&&d[1]<threshold)threshold=(int)d[1];}}
  if(threshold==2147483647)break;status|=notify(c,e,ne,s,env,t,27,who,threshold,full);previous_threshold=threshold;
 }
 if(!skill&&!(s->normal_landed_mask&(1<<who))){s->normal_landed_mask|=1<<who;invalidate(s);}
 add_burst(s,burst_gain(c,e,ne,s,who,mode,count,0,full));
 status|=notify(c,e,ne,s,env,t,7,who,0,full);for(int k=0;k<muzzles;k++)status|=notify(c,e,ne,s,env,t,8,who,0,full,bullet_core(s,core,split));
 if(!skill)status|=consume_bullets(c,e,ne,s,env,t,who,full);
 if(is_last)for(int k=0;k<muzzles;k++)status|=notify(c,e,ne,s,env,t,14,who,0,full);
 s->next[who]+=1/fr;
 if(warm_mode){s->last[who]=t;s->inter[who]=1/fr;}
 if(s->next[who]<=t)s->next[who]=t;
 return status;
}
__device__ int charge_frame(const double* c,const double* e,int ne,State* s,const double* env,double t,int who,int full){
 const double* a=c+who*CW;int code=0,mode=s->mode[who];const double* q=mode>=0?effect(e,s,mode):0;int skill=q&&q[235]>0;if(stat(c,e,ne,s,who,28,full)>0)return code;
 if(!s->started[who]){s->started[who]=1;if(!s->squad_mode)s->ammo[who]=full_ammo(c,e,ne,s,who,full);}
 s->ammo[who]=mn(s->ammo[who],full_ammo(c,e,ne,s,who,full));
 if(mode<0&&s->post[who]>0){if(t<s->post[who])return code;s->post[who]=-1;}
 if(s->charge_phase[who]==2){if(t<s->charge_post[who])return code;if(s->auto_reload[who]){s->auto_reload[who]=0;s->mode_ammo[who]=-1;s->ammo[who]=full_ammo(c,e,ne,s,who,full);code|=notify(c,e,ne,s,env,t,19,who,0,full);}s->charge_phase[who]=0;}
 if(s->charge_phase[who]==0){
  if(s->ammo[who]<=0&&stat(c,e,ne,s,who,59,full)==0){start_reload(c,e,ne,s,who,full,t);return code;}
  if(s->hold_start[who]>0&&t<s->hold_start[who]&&s->hold_start[who]-t<=charge_duration(c,e,ne,s,who,full)+.4)return code;
  s->charge_start[who]=t;s->charge_phase[who]=1;
  s->charge_full[who]=-1;for(int j=0;j<NE;j++)s->hold_fired[who][j]=0;
  int entry=control_owns(c,s,who)?control_entry(c,s,who,full,1):-1;const double* input=entry>=0?a+48+entry*12:0;
  s->tap[who]=input&&input[0]==1;s->force_full[who]=s->tap[who]&&input[8]>0&&t-s->last_full[who]>=input[8];
  if(s->tap[who]){s->tap_hold[who]=input[4];s->tap_charge[who]=input[5];s->tap_release[who]=input[6];s->tap_post[who]=input[7];}
  if(s->hold_start[who]>0&&t>=s->hold_start[who]){s->hold_release[who]=t+charge_duration(c,e,ne,s,who,full)+hold_threshold(e,ne,who)+1.0/60;s->hold_start[who]=-1;s->force_full[who]=1;}
  s->charging[who]=1;invalidate(s);
  if(s->ammo[who]==1&&stat(c,e,ne,s,who,59,full)==0)code|=notify(c,e,ne,s,env,t,21,who,0,full);
 }
 if(s->charge_phase[who]!=1)return code;
 double charge=charge_duration(c,e,ne,s,who,full);
 int is_full=1;
 if(s->tap[who]&&!s->force_full[who]){if(t<s->charge_start[who]+s->tap_hold[who])return code;is_full=s->tap_charge[who]>=charge;}
 else{
  if(s->charge_full[who]<0){if(t<s->charge_start[who]+charge)return code;s->charge_full[who]=t;}
  int phase=s->charge_phase[who];double reload=s->reload[who],held=t-s->charge_full[who];
  for(int pass=0;pass<NE*EVS;pass++){int tag=-1;double earliest=1e30;
   for(int j=0;j<ne;j++){const double* def=e+j*EW;if(def[0]!=who)continue;for(int k=0;k<(int)def[144];k++){const double* d=def+TD+k*TS;if(d[0]==39&&!s->hold_fired[who][(int)d[3]]&&d[4]<=held&&d[4]<earliest){tag=(int)d[3];earliest=d[4];}}}
   if(tag<0)break;s->hold_fired[who][tag]=1;code|=notify(c,e,ne,s,env,t,39,who,tag,full);
  }
  if(s->charge_phase[who]!=phase||s->reload[who]!=reload)return code;
  if(s->hold_release[who]>=0&&t<s->hold_release[who])return code;
 }
 if(is_full){s->last_full[who]=t;s->force_full[who]=0;code|=notify(c,e,ne,s,env,t,10,who,0,full);}
 int infinite=stat(c,e,ne,s,who,59,full)>0;
 int auto_reload=(q?q[231]:a[31])>0&&stat(c,e,ne,s,who,19,full)>=100;
 int split=pellets(c,e,ne,s,who,full),muzzles=(int)(q?q[29]:a[33]),count=split*muzzles;if(count>512)return 8;
 double coeff=q?(s->mode_shots[who]==0&&q[236]>=0?q[236]:q[26]):a[1];
 int flags=(is_full?32:0)|(skill?32768:0)|((int)a[26]?8:0)|(stat(c,e,ne,s,who,36,full)>0?64:0)|(stat(c,e,ne,s,who,52,full)>0?512:0);double one=damage(c,e,ne,s,env,who,full,coeff/split,!skill,flags);ReachHit part=reach_sample(c,e,ne,s,env,who,full,coeff/split,!skill,flags);s->shot_reach[who]=part.reach;s->shot_part[who]=part.damage;
 double crit=mn(stat(c,e,ne,s,who,skill?24:5,full),1),core=core_probability(c,e,ne,s,env,who,full);
 s->hit_unit[who]=one;s->hits[who]=count;s->hit[who]=one*count;s->total[who]+=s->hit[who];s->shots[who]++;
 if(count>1)for(int k=0;k<count;k++)code|=notify(c,e,ne,s,env,t,20,who,0,full);
 int is_last=s->ammo[who]==1&&!infinite;if(!infinite){s->ammo[who]--;code|=notify(c,e,ne,s,env,t,26,who,0,full);}
 code|=notify(c,e,ne,s,env,t,7,who,0,full);code|=notify(c,e,ne,s,env,t,is_full?11:40,who,0,full);
 for(int k=0;k<muzzles;k++)code|=notify(c,e,ne,s,env,t,8,who,0,full,bullet_core(s,core,split));
 if(is_full)for(int k=0;k<muzzles;k++)code|=notify(c,e,ne,s,env,t,12,who,0,full,0,0,0,-1,one*count/muzzles);
 if(!skill&&!(s->normal_landed_mask&(1<<who))){s->normal_landed_mask|=1<<who;invalidate(s);}
 add_burst(s,burst_gain(c,e,ne,s,who,mode,count,is_full&&(s->camera_mask&(1<<who)),full));
 for(int k=0;k<count;k++)code|=fractional(c,e,ne,s,env,t,who,full,team_hit_event(env,s),1-core);
 if(!skill)code|=consume_bullets(c,e,ne,s,env,t,who,full);
 for(int k=0;k<count;k++)code|=fractional(c,e,ne,s,env,t,who,full,22,crit);
 for(int k=0;k<count;k++)code|=fractional(c,e,ne,s,env,t,who,full,23,core);
 if(is_last)for(int k=0;k<muzzles;k++)code|=notify(c,e,ne,s,env,t,14,who,0,full);
 s->charge_post[who]=s->tap[who]?t+s->tap_release[who]+s->tap_post[who]:mx(t+(q?q[227]:a[17]),s->charge_start[who]+(q?0:a[18]));if(!q)s->next[who]=s->charge_post[who];s->charge_phase[who]=2;if(!s->tap[who]&&auto_reload)s->auto_reload[who]=1;
 s->charge_full[who]=-1;s->hold_release[who]=-1;s->hold_close[who]=-1;s->charging[who]=0;invalidate(s);
 return code;
}
__device__ __noinline__ int manual_mode_ready(const double* c,const double* e,int ne,State* s,int who,int full){
 for(int at=s->event_offsets[19];at<s->event_offsets[20];at++){
  int j=s->event_definitions[at];
  const double* q=e+j*EW;if(q[0]!=who||q[1]!=2||q[14]<=0)continue;
  if(condition(c,e,ne,s,q,full,0))return 1;
 }return 0;
}
__device__ void begin_mode_frame(const double* c,const double* e,int ne,State* s,int who,int mode,int full,double t){
 const double* q=effect(e,s,mode);s->mode_ready[who]=t+(q[239]>0&&q[240]>0&&q[42]==0?reload_duration(c,e,ne,s,who,full):q[42]);s->mode_started[who]=0;s->mode_shots[who]=0;s->mode_ammo[who]=-1;s->mode_restored[who]=0;
}
__device__ int weapon_frame(const double* c,const double* e,int ne,State* s,const double* env,double t,int who,int full){
 if(s->down_mask&(1<<who))return 0;
 if(stat(c,e,ne,s,who,28,full)>0)return 0;
 if(!s->started[who]){s->started[who]=1;if(!s->squad_mode)s->ammo[who]=full_ammo(c,e,ne,s,who,full);}
 int mode=s->mode[who],prior=s->prev_mode[who];
 if(mode>=0&&prior<0)begin_mode_frame(c,e,ne,s,who,mode,full,t);
 s->prev_mode[who]=mode;
 int code=0;
 // BuffManager already invalidated when the mode ended. Restoring CharState
 // fields preserves the CPU buff query snapshot, including random recipients.
 if(mode<0&&prior>=0){if(!s->mode_restored[who]){s->ammo[who]=full_ammo(c,e,ne,s,who,full);s->mode_ammo[who]=-1;if(s->reload[who]>0&&s->reload_in_mode[who]){s->reload[who]=-1;s->reload_in_mode[who]=0;}}s->mode_restored[who]=0;s->next[who]=t;if(c[who*CW+8]==3)s->charge_phase[who]=0;s->charge_full[who]=-1;s->hold_release[who]=-1;s->charging[who]=0;}
 if(stat(c,e,ne,s,who,59,full)>0&&s->reload[who]>0){s->reload[who]=-1;s->reload_in_mode[who]=0;s->next[who]=mx(s->next[who],t);}
 if(c[who*CW+168]>0&&mode<0){
  if(s->reload[who]<=0)s->ammo[who]=mn(s->ammo[who],full_ammo(c,e,ne,s,who,full));
  if(s->reload[who]<=0&&s->post[who]<=0&&manual_mode_ready(c,e,ne,s,who,full)){start_reload(c,e,ne,s,who,full,t);return 0;}
 }
 update_controls(c,e,ne,s,t,who,full);
 // Reload completion can enter a mode. Resolve that transition before picking
 // a firing model, so the old weapon cannot fire once on the transition frame.
 if(mode<0&&s->reload[who]>0){
  if(t<s->reload[who])return code;if(!finish_clip(c,e,ne,s,who,full,t))return code;
  code|=notify(c,e,ne,s,env,t,19,who,0,full);s->post[who]=c[who*CW+7]>0?t+c[who*CW+7]:-1;if(s->post[who]<0)s->next[who]=t;
  mode=s->mode[who];if(mode>=0){begin_mode_frame(c,e,ne,s,who,mode,full,t);s->prev_mode[who]=mode;}
 }
 if(mode>=0){
  const double* q=effect(e,s,mode);
  if(q[238]>0&&s->reload_in_mode[who]&&s->reload[who]>0){if(t<s->reload[who])return 0;if(finish_clip(c,e,ne,s,who,full,t)){code|=notify(c,e,ne,s,env,t,19,who,0,full);if(c[who*CW+7]>0)s->post[who]=t+c[who*CW+7];else s->next[who]=t;}else return 0;}
  if(t<s->mode_ready[who])return code;
  if(!s->mode_started[who]){
   if(q[240]>0){s->charge_phase[who]=0;s->charge_start[who]=t;s->charge_full[who]=-1;}
   s->ammo[who]=q[27]==-1?999999:full_ammo(c,e,ne,s,who,full);
   if(q[224]!=3)s->next[who]=t;else if(s->charge_phase[who]!=0)s->charge_start[who]=t;
   s->mode_started[who]=1;
  }else if(q[224]==3&&s->charge_phase[who]==0)s->ammo[who]=q[27]==-1?999999:full_ammo(c,e,ne,s,who,full);
 }
 int before=s->shots[who];
 s->weapon_context[who]=mode>=0;
 code|=(mode>=0?effect(e,s,mode)[224]==3:c[who*CW+8]==3)?charge_frame(c,e,ne,s,env,t,who,full):auto_frame(c,e,ne,s,env,t,who,full);
 s->weapon_context[who]=0;
 if(mode>=0){const double* q=effect(e,s,mode);s->mode_shots[who]+=s->shots[who]-before;double limit=q[232];if(limit>=0&&q[27]!=-1&&limit==q[27])limit=full_ammo(c,e,ne,s,who,full);
  if(limit>=0&&s->mode_shots[who]>=limit){
   s->charge_phase[who]=0;s->mode_ready[who]=-1;s->reload[who]=-1;s->next[who]=t;
   double base=c[who*CW+2];s->ammo[who]=mx(1,base+quant(c,e,ne,s,who,18,full,base,1)+(double)__double2ll_rn(stat(c,e,ne,s,who,33,full)));
   s->mode_ammo[who]=-1;s->mode_restored[who]=1;s->mode[who]=-1;invalidate(s);
   if(q[35]>0)code|=notify(c,e,ne,s,env,t,29,who,(int)q[3],full);
  }
 }return code;
}
__device__ int log_burst(State* s,double t,int event,int who){
 if(s->log_count>=256)return 2;int j=s->log_count++;s->log_t[j]=t;s->log_event[j]=event;s->log_who[j]=who;return 0;
}
// Skill hits land at the next frame's dot-event drain, preserving HP-trigger timing.
__device__ int heal_landed(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,int who,double hit){
 if(hit<=0)return 0;double ls=stat(c,e,ne,s,who,44,full);if(ls<=0)return 0;
 double amount=hit*ls/100*heal_multiplier(c,e,ne,s,who,full,who);
 return notify(c,e,ne,s,env,t,54,who,who,full,0,0,amount);
}
// Collect every carrier before delivering any full notification. The order
// is dealt pools, then received pools, matching each family's entry order.
__device__ int collect_damage_accum(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,int attacker,double hit){
 if(!(s->event_interest&INTEREST_DAMAGE_ACCUM)||hit<=0)return 0;
 int names[NS],owners[NS],count=0;
 for(int kind=81;kind<=82;kind++)for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);if(!s->alive[j]||q[1]!=0||q[2]!=kind||s->shield_present[j]!=1||s->shield_capacity[j][0]<=0)continue;
  int owner=(int)q[0],name=(int)q[3];if(kind==81&&owner!=attacker)continue;
  double cap=s->shield_capacity[j][0];s->shield_current[j][0]=mn(s->shield_current[j][0]+hit*damage_accum_rate(c,e,ne,s,owner,name,full)/100,cap);
  if(q[35]>0)s->damage_accum_last[name]=s->shield_current[j][0];
  if(s->shield_current[j][0]>=cap-1e-9){s->shield_present[j]=2;if(q[35]>0){if(count>=NS)return 8;names[count]=name;owners[count++]=owner;}}
 }
 int code=0;for(int i=0;i<count;i++)code|=notify(c,e,ne,s,env,t,50,owners[i],names[i],full);return code;
}
// One typed boundary for every supported body/part landing. Credit is not
// weighted by non-core probability, damage, pellets-per-ammo or resource spend.
__device__ void record_impact(State* s,const Impact& p,double t){
 if(!s->impact_enabled)return;
 double* r=s->impact_summary;r[0]++;r[1+p.kind*4+p.family]++;r[25]+=p.credit;r[26]+=p.damage;r[40+p.outcome]++;
 r[27]=p.kind;r[28]=p.identity;r[29]=p.generation;r[30]=p.family;r[31]=p.outcome;r[32]=p.attacker;
 r[33]=p.damage;r[34]=p.credit;r[35]=p.attack_id;r[36]=t;
}
struct CounterReady {int slot,uid,epoch,owner,name,kind,identity,generation,emit;double credit;};
__device__ int actor_dead(State* s,int kind,int identity,int generation){
 for(int k=0;k<s->dead_count;k++)if(s->dead_kind[k]==kind&&s->dead_identity[k]==identity&&s->dead_generation[k]==generation)return 1;
 return 0;
}
__device__ __noinline__ int collect_target_counters(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,const Impact* packet,int kind=-1,int identity=0,int generation=0){
 if(!(s->event_interest&INTEREST_TARGET_COUNTER))return 0;
 if(packet){if(actor_dead(s,packet->kind,packet->identity,packet->generation))return 0;}
 else{
  if(actor_dead(s,kind,identity,generation))return 0;
  if(s->dead_count>=NS)return 8;
  int at=s->dead_count++;s->dead_kind[at]=kind;s->dead_identity[at]=identity;s->dead_generation[at]=generation;
 }
 CounterReady ready[NS];int count=0;
 // Snapshot and latch every ready sibling before any child notification.
 for(int r=s->slot_head;r>=0;r=s->slot_next[r]){
  const double* q=effect(e,s,r);
  if(!s->alive[r]||q[1]!=0||q[2]!=87||s->counter_uid[r]!=s->entry_seq[r]||s->counter_done[r]||s->counter_end[r]<=t)continue;
  if(packet){
   if(packet->kind!=q[296]||packet->identity!=q[297]||packet->generation!=q[298]||!((int)q[299]&(1<<packet->family))||!((int)q[300]&(1<<packet->outcome))||packet->credit<=0||q[303]>0&&packet->attacker!=(int)q[0])continue;
   s->counter_credit[r]=mn(q[295],s->counter_credit[r]+packet->credit);if(s->counter_credit[r]<q[295])continue;
  }else if(kind!=q[296]||identity!=q[297]||generation!=q[298])continue;
  s->counter_done[r]=1;
  ready[count++]={r,s->entry_seq[r],s->counter_epoch[r],(int)q[0],(int)q[3],(int)q[296],(int)q[297],(int)q[298],packet||q[302]>0,s->counter_credit[r]};
 }
 int code=0;
 for(int k=0;k<count;k++){
  CounterReady v=ready[k];if(v.emit){s->counter_completed++;
  double* last=s->counter_last;last[0]=v.uid;last[1]=v.epoch;last[2]=v.owner;last[3]=v.name;last[4]=v.kind;last[5]=v.identity;last[6]=v.generation;last[7]=v.credit;last[8]=packet?0:1;last[9]=t;
  TargetRef target={v.kind,v.identity,v.generation};code|=notify(c,e,ne,s,env,t,58,v.owner,v.name,full,0,0,0,-1,0,target);
  }
  // A nested reapplication can reuse the slot and UID but creates a new epoch.
  int r=v.slot;if(s->alive[r]&&s->entry_seq[r]==v.uid&&s->counter_epoch[r]==v.epoch){
   lifecycle_retire(e,s,r);s->alive[r]=0;s->stacks[r]=0;s->end[r]=-1;invalidate(s);
   code|=notify(c,e,ne,s,env,t,29,v.owner,v.name,full);
  }
 }
 return code|s->counter_error;
}
__device__ int publish_landing(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,const Impact& p,int dead=0){
 record_impact(s,p,t);
 int code=group_collect(s,&p,t);
 if(s->event_interest&INTEREST_TARGET_COUNTER){
  code|=collect_target_counters(c,e,ne,s,env,t,full,&p);
  if(dead)code|=collect_target_counters(c,e,ne,s,env,t,full,0,p.kind,p.identity,p.generation);
 }
 return code;
}
__device__ int land_impact(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,const Impact& p,int dead=0){
 int code=publish_landing(c,e,ne,s,env,t,full,p,dead);
 if(p.outcome!=OUTCOME_DAMAGING)return code;
 code|=heal_landed(c,e,ne,s,env,t,full,p.attacker,p.damage);
 return code|collect_damage_accum(c,e,ne,s,env,t,full,p.attacker,p.damage);
}
__device__ int add_land(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,const Impact& requested){
 int index=world_actor_index(s,ACTOR_ADD,requested.identity);if(index<0)return 8;
 const double* row=s->boss_program+WA+1+index*ACTOR_WORDS;int run=(int)row[3];
 if(!s->boss_opens[run]||requested.generation!=s->boss_opens[run])return 8;
 s->add_last_took=0;
 if(!s->boss_active[run]||s->add_gone[index]){s->add_overkill+=requested.damage;return 0;}
 const double* p=s->boss_program+WB+run*BW;
 int counting=p[92]>0&&(p[91]<0||t>=s->boss_start[run]+p[93]-1e-9),killed=0;double took;
 if(counting){s->add_hits[index]++;took=mn(requested.damage,1);killed=s->add_hits[index]>=p[92];}
 else{took=mn(requested.damage,p[91]-s->add_dealt[index]);killed=s->add_dealt[index]+took>=p[91];}
 s->add_dealt[index]+=took;s->add_total[requested.attacker]+=took;s->add_overkill+=requested.damage-took;s->add_last_took=took;
 if(killed){s->add_gone[index]=1;if(s->add_pending_deaths>=BQ)return 8;s->add_pending_deaths++;}
 Impact receipt=requested;receipt.damage=took;
 // Pool receipts are independent of requested damage used by other consumers.
 return publish_landing(c,e,ne,s,env,t,full,receipt,killed);
}
__device__ int land_damage(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,int who,double hit,int family=HIT_WEAPON,int kind=ACTOR_BODY,int identity=0,int dead=0){
 int generation=0,alive=0,parent_kind=-1,parent_id=-1;
 if(!world_actor(s,kind,identity,&generation,&alive,&parent_kind,&parent_id))return 8;
 Impact p={who,kind,identity,generation,family,OUTCOME_DAMAGING,0,hit,1};
 return land_impact(c,e,ne,s,env,t,full,p,dead);
}
// World presence is sampled at frame start. Destruction is immediate for later
// landings, but its notifications are delivered after the next frame's tick.
__device__ int parts_refresh(const double* env,State* s){
 s->part_min=0;for(int p=0;p<(int)env[2];p++)if(!s->part_dead[p]){int tier=(int)env[4+p*2];if(!s->part_min||tier<s->part_min)s->part_min=tier;}
 int count=s->part_pending;s->part_pending=0;return count;
}
__device__ __noinline__ int parts_land(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,int who,int reach,double hit,int aimed=-1,int family=HIT_WEAPON){
 if(!reach||hit<=0)return 0;unsigned int mask=0;
 for(int p=0;p<(int)env[2];p++){
  if(p==aimed||s->part_dead[p]||reach<env[4+p*2])continue;
  mask|=1u<<p;s->part_dealt[p]+=hit;s->part_hits[p]++;
  double hp=env[3+p*2];if(hp>0&&s->part_dealt[p]>=hp){s->part_dead[p]=1;s->part_at[p]=t;s->part_pending++;}
 }
 int code=0;for(int p=0;p<(int)env[2];p++)if(mask&(1u<<p)){s->total[who]+=hit;code|=land_damage(c,e,ne,s,env,t,full,who,hit,family,ACTOR_PART,p,s->part_dead[p]);}return code;
}
__device__ int parts_events(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,int count){
 int code=0;for(int j=0;j<count;j++)for(int i=0;i<5;i++)code|=notify(c,e,ne,s,env,t,34,i,0,full);return code;
}

__device__ int flush_lands(const double* c,const double* e,int ne,State* s,const double* env,double t,int full){
 int code=0;for(int k=0;k<s->land_count;k++){int who=s->land_owner[k];code|=land_damage(c,e,ne,s,env,t,full,who,s->land_damage[k],s->land_family[k]);code|=parts_land(c,e,ne,s,env,t,full,who,s->land_reach[k],s->land_part[k],-1,s->land_family[k]);}s->land_count=0;return code;
}
// Pattern transitions are evaluated here, never replayed from a CPU schedule.
__device__ const double* boss_pattern(State* s,int i){return s->boss_program+WB+i*BW;}
__device__ int boss_match_count(State* s,int node,int outcome){
 if(!outcome)return s->boss_end_n[node];int n=0;for(int k=0;k<s->boss_end_n[node];k++)if(s->boss_end_kind[node][k]==outcome)n++;return n;
}
__device__ double boss_match_time(State* s,int node,int outcome,int index){
 if(!outcome)return s->boss_end_at[node][index];int n=0;for(int k=0;k<s->boss_end_n[node];k++)if(s->boss_end_kind[node][k]==outcome){if(n==index)return s->boss_end_at[node][k];n++;}return 1e300;
}
__device__ int boss_log(State* s,double t,int i,int outcome){
 int at=s->boss_log_n;if(at>=BLOG)return 8;s->boss_log_at[at]=t;s->boss_log_node[at]=i;s->boss_log_kind[at]=outcome;s->boss_log_n++;return 0;
}
__device__ int boss_emit(State* s,const double* p,int end){
 int base=end?60:44,count=(int)p[end?11:10];
 for(int k=0;k<count;k++){int at=s->boss_event_n;if(at>=BQ)return 8;s->boss_event_code[at]=(int)p[base+k*2];s->boss_event_arg[at]=(int)p[base+k*2+1];s->boss_event_n++;}return 0;
}
__device__ int boss_close(State* s,int i,double t,int outcome){
 const double* p=boss_pattern(s,i);if(p[0]==7)for(int k=0;k<(int)p[90];k++){int at=(int)p[89]+k;if(!s->add_gone[at])s->add_gone[at]=2;}
 int n=s->boss_end_n[i+1];if(n>=BH)return 8;s->boss_active[i]=0;s->boss_end_at[i+1][n]=t;s->boss_end_kind[i+1][n]=outcome;s->boss_end_n[i+1]++;
 if(outcome!=4)s->boss_release|=1u<<i;
 int code=boss_log(s,t,i,outcome);if(outcome!=4)code|=boss_emit(s,boss_pattern(s,i),1);return code;
}
__device__ int gather_incoming(State* s,double t){
 // Queue identities now; recipient choice and damage still run after tick/events.
 // A source pattern owns one schedule, shared by its synchronously spawned actors.
 for(int i=0;i<s->boss_count;i++){
  const double* p=boss_pattern(s,i);if(!s->boss_active[i]||!(p[0]==6||p[0]==7&&p[80]>0))continue;
  int begin=s->incoming_shots[i];double first=s->boss_start[i]+(p[0]==7?p[76]:0);
  // Neither actor presence nor per-actor work can produce a shot before its
  // next shared deadline, or after this pattern's schedule is exhausted.
  if(begin>=p[87]||t<first+begin*p[88]-1e-9)continue;
  if(p[0]==7){int live=0;for(int slot=0;slot<(int)p[90];slot++)if(!s->add_gone[(int)p[89]+slot])live++;if(!live)continue;}
  int end=begin;
  while(end<p[87]&&t>=first+end*p[88]-1e-9){if(end-begin>=BQ)return 512;end++;}
  s->incoming_shots[i]=end;
  int actors=p[0]==7?(int)p[90]:1;
  for(int slot=0;slot<actors;slot++){
   int actor=p[0]==7?(int)p[89]+slot:-1;if(actor>=0&&s->add_gone[actor])continue;
   for(int shot=begin;shot<end;shot++){if(s->incoming_queued>=BQ)return 512;s->incoming_queue[s->incoming_queued++]=(actor+1)*BP+i;}
   if(actor>=0&&p[77]&&end>0&&end==p[87]){
    s->add_gone[actor]=3;if(s->boss_event_n>=BQ)return 8;int at=s->boss_event_n++;s->boss_event_code[at]=33;s->boss_event_arg[at]=0;
   }
  }
 }return 0;
}
__device__ int boss_frame(State* s,double t){
 if(!s->boss_count)return 0;
 if(s->boss_frame_at==t)return 0;s->boss_frame_at=t;
 for(int k=0;k<s->add_pending_deaths;k++){if(s->boss_event_n>=BQ)return 8;int at=s->boss_event_n++;s->boss_event_code[at]=33;s->boss_event_arg[at]=0;}s->add_pending_deaths=0;
 for(int i=0;i<s->boss_count;i++)if(s->boss_dispelled[i]==1){s->boss_dispelled[i]=2;s->boss_release|=1u<<i;}
 int due[BP];for(int i=0;i<BP;i++)due[i]=0;
 for(int i=0;i<s->boss_count;i++){const double* p=boss_pattern(s,i);if(!s->boss_active[i])continue;
  if(p[0]==7&&p[94]){int all=1;for(int k=0;k<(int)p[90];k++)if(!s->add_gone[(int)p[89]+k])all=0;if(all)due[i]=3;}
  if(!due[i]&&p[2]>0&&t>=s->boss_start[i]+p[2]-1e-9)due[i]=1;}
 for(int pass=0;pass<=BP;pass++){
  int grew=0;for(int i=0;i<s->boss_count;i++){
   if(!s->boss_active[i]||due[i]==2||due[i]==3)continue;const double* p=boss_pattern(s,i);
   for(int k=0;k<(int)p[5];k++){
    int node=(int)p[28+2*k],index=s->boss_until[i][k];double at;
    if(s->boss_end_n[node]>index)at=s->boss_end_at[node][index];else if(due[node-1])at=t;else continue;
    if(t>=at+p[29+2*k]-1e-9){due[i]=2;grew=1;break;}
   }
  }if(!grew)break;
 }
 int code=0;
 for(int i=0;i<s->boss_count;i++)if(due[i]){code|=boss_close(s,i,t,due[i]);if(code)return code;}
 for(int i=0;i<s->boss_count;i++){
  if(s->boss_active[i])continue;const double* p=boss_pattern(s,i);if(p[3]>0&&s->boss_opens[i]>=(int)p[3])continue;
  int ready=0;
  for(int k=0;k<(int)p[4];k++){
   int node=(int)p[12+2*k],outcome=(int)p[13+2*k],index=s->boss_after[i][k];
   if(boss_match_count(s,node,outcome)>index&&t>=boss_match_time(s,node,outcome,index)+p[1]-1e-9){ready=1;break;}
  }
  if(!ready)continue;s->boss_active[i]=1;s->boss_start[i]=t;s->incoming_shots[i]=0;s->boss_opens[i]++;s->boss_dispelled[i]=0;s->boss_apply|=1u<<i;
  for(int k=0;k<(int)p[4];k++)s->boss_after[i][k]=boss_match_count(s,(int)p[12+2*k],(int)p[13+2*k]);
  for(int k=0;k<(int)p[5];k++)s->boss_until[i][k]=s->boss_end_n[(int)p[28+2*k]];
  if(p[0]==7){
   int count=(int)p[90];if(s->add_clock>2147483647-count)return 8;s->add_order[i]=s->add_clock;s->add_clock+=count;
   for(int k=0;k<count;k++){int at=(int)p[89]+k;s->add_dealt[at]=0;s->add_hits[at]=s->add_gone[at]=0;
    if(s->boss_event_n>=BQ)return 8;int event=s->boss_event_n++;s->boss_event_code[event]=5;s->boss_event_arg[event]=0;}
  }
  code|=boss_log(s,t,i,0);code|=boss_emit(s,p,0);if(code)return code;
 }
 code|=gather_incoming(s,t);if(code)return code;
 double defense=s->boss_base_def;int order[BP],n=0;for(int i=0;i<s->boss_count;i++)if(s->boss_active[i]){int at=n++;while(at>0&&(s->boss_start[order[at-1]]>s->boss_start[i]||s->boss_start[order[at-1]]==s->boss_start[i]&&order[at-1]>i)){order[at]=order[at-1];at--;}order[at]=i;}
 for(int k=0;k<n;k++){int i=order[k];const double* p=boss_pattern(s,i);if(p[0]==5&&!s->boss_dispelled[i])defense=defense*p[76]+p[77];}
 double core=s->boss_base_core,distance=s->boss_program[1];int mask=(int)s->boss_program[2],last=-1;
 for(int i=0;i<s->boss_count;i++)if(s->boss_active[i]){
  const double* p=boss_pattern(s,i);if(p[0]==3)core=mx(core,p[6]);
  if(p[0]==4&&(last<0||s->boss_start[i]>s->boss_start[last]||s->boss_start[i]==s->boss_start[last]&&i>last))last=i;
 }
 if(last>=0){const double* p=boss_pattern(s,last);if(p[7]==1)distance=p[8];else mask=(int)p[9];}
 if(defense!=s->world[0]||core!=s->world[1]||distance!=s->boss_distance||mask!=s->boss_weapon_mask)invalidate(s);
 int living=1;for(int i=0;i<s->boss_count;i++)if(s->boss_active[i]){const double* p=boss_pattern(s,i);if(p[0]==7)for(int k=0;k<(int)p[90];k++)if(!s->add_gone[(int)p[89]+k])living++;}
 if(living!=s->add_live_snapshot)invalidate(s);s->add_live_snapshot=living;
 s->world[0]=defense;s->world[1]=core;s->boss_distance=distance;s->boss_weapon_mask=mask;return 0;
}
__device__ int boss_dispel(State* s,double t,int limit){
 for(int k=0;k<limit;k++){int last=-1;for(int i=0;i<s->boss_count;i++){
  const double* p=boss_pattern(s,i);if(!s->boss_active[i]||p[0]!=5||p[79]||s->boss_dispelled[i])continue;
  if(last<0||s->boss_start[i]>s->boss_start[last]||s->boss_start[i]==s->boss_start[last]&&i>last)last=i;
 }if(last<0)break;s->boss_dispelled[last]=1;int code=boss_log(s,t,last,5);if(code)return code;}return 0;
}
__device__ int boss_effect_state(const double* e,int ne,State* s,double t){
 for(int i=0;i<s->boss_count;i++)if(s->boss_release&(1u<<i)){
  int row=(int)boss_pattern(s,i)[78];if(row<0)continue;for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&s->definition[k]==row){s->alive[k]=0;s->stacks[k]=0;invalidate(s);}
 }
 for(int i=0;i<s->boss_count;i++)if(s->boss_apply&(1u<<i)){
  int row=(int)boss_pattern(s,i)[78];if(row<0)continue;int j=fresh_slot(s,ne,row);if(j<0)return 8;
  new_entry(s,j);s->stacks[j]=1;s->end[j]=1e30;s->masks[j]=32;s->target_order[j]=6;s->activated[j]=t;invalidate(s);
 }
 s->boss_release=s->boss_apply=0;return 0;
}
__device__ int boss_init(State* s,const double* w,int defer_frame=0){
 s->boss_frame_at=-1;
 s->add_clock=s->add_pending_deaths=0;s->add_live_snapshot=1;s->add_overkill=s->add_last_took=0;
 for(int i=0;i<WORLD_ACTORS;i++){s->add_dealt[i]=0;s->add_hits[i]=0;s->add_gone[i]=2;}for(int i=0;i<5;i++)s->add_total[i]=0;for(int i=0;i<BP;i++)s->add_order[i]=0;
 s->boss_release=s->boss_apply=0;s->boss_base_def=s->world[0];for(int i=0;i<BP;i++)s->boss_dispelled[i]=0;
 s->boss_program=w;s->boss_count=(int)w[0];s->boss_base_core=s->world[1];s->boss_distance=w[1];s->boss_weapon_mask=(int)w[2];s->boss_log_n=s->boss_event_n=0;
 for(int i=0;i<=BP;i++)s->boss_end_n[i]=0;
 for(int i=0;i<BP;i++){s->boss_active[i]=s->boss_opens[i]=0;s->boss_start[i]=0;for(int k=0;k<BL;k++)s->boss_after[i][k]=s->boss_until[i][k]=0;}
 s->boss_end_n[0]=1;s->boss_end_at[0][0]=0;s->boss_end_kind[0][0]=0;return defer_frame?0:boss_frame(s,0);
}
__device__ int boss_events(const double* c,const double* e,int ne,State* s,const double* env,double t,int full){
 int code=0;for(int k=0;k<s->boss_event_n;k++)for(int who=0;who<5;who++)code|=notify(c,e,ne,s,env,t,s->boss_event_code[k],who,s->boss_event_arg[k],full);s->boss_event_n=0;return code;
}
__device__ int boss_finish(State* s,double t){int code=0;for(int i=0;i<s->boss_count;i++)if(s->boss_active[i])code|=boss_close(s,i,t,4);return code;}

// Boss attacks run after expiration/cover synchronization and boss emissions,
// before outgoing delayed hits, bursts and character actions. No CPU trace is input.
__device__ Order incoming_targets(const double* c,const double* e,int ne,State* s,const double* p,int full){
 int rule=(int)p[82],seats=rule==1?5:(int)p[83],taunt=0;Order order=0;int shift=0;
 if(rule==1){for(int who=0;who<5;who++)if(!(s->down_mask&(1<<who))){order|=Order(who+1)<<shift;shift+=3;}return order;} // slots 0,1,2,3,4 in squad order
 if(!p[86]){
  int available=0;
  for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
   const double* q=effect(e,s,j);if(q[1]!=0||q[2]!=66||!s->alive[j]||s->end[j]<=s->when||s->masks[j]<0)continue;
   if(s->masks[j]&32)available|=1<<(int)q[0];
   else for(Order raw=s->target_order[j];raw;raw>>=3){int who=(raw&7)-1;if(live_shield_recipient(c,e,ne,s,j,who,full)){available|=1<<who;break;}}
  }
  for(int who=0;who<5&&shift<seats*3;who++)if((available&(1<<who))&&!(s->down_mask&(1<<who))){taunt|=1<<who;order|=Order(who+1)<<shift;shift+=3;}
 }
 if(rule==2){for(Order raw=(Order)p[84];raw&&shift<seats*3;raw>>=3){int who=(raw&7)-1;if(!(s->down_mask&(1<<who))&&!(taunt&(1<<who))){order|=Order(who+1)<<shift;shift+=3;}}return order;}
 int pool[5],n=0,rest=(31^taunt)&~s->down_mask,visible=0;
 for(int who=0;who<5;who++)if((rest&(1<<who))&&!live_marker(c,e,ne,s,who,65,full))visible|=1<<who;
 if(!visible)visible=rest;
 for(int who=0;who<5;who++)if(visible&(1<<who))pool[n++]=who;
 int need=(int)mn(seats-shift/3,n),picked=0;
 if(rule==3)for(int k=0;k<need;k++){int at=(int)mt_below(&s->boss_rng,n-k);picked|=1<<pool[at];pool[at]=pool[n-k-1];}
 else for(int k=0;k<need;k++){int best=-1;double value=0;for(int who=0;who<5;who++)if((visible&(1<<who))&&!(picked&(1<<who))){double at=rank_atk(c,e,ne,s,who,full);if(best<0||at>value){best=who;value=at;}}if(best>=0)picked|=1<<best;}
 for(int who=0;who<5;who++)if(picked&(1<<who)){order|=Order(who+1)<<shift;shift+=3;}return order;
}
__device__ Order incoming_group(const double* c,const double* e,int ne,State* s,int who,int full){
 if(s->down_mask&(1<<who))return 0;Order out=who+1;int shift=3,mask=1<<who;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(effect(e,s,j)[1]==0&&effect(e,s,j)[2]==69&&live_shield_recipient(c,e,ne,s,j,who,full)){
  for(Order raw=s->target_order[j];raw;raw>>=3){int member=(raw&7)-1;if(!(s->down_mask&(1<<member))&&!(mask&(1<<member))&&live_shield_recipient(c,e,ne,s,j,member,full)){mask|=1<<member;out|=Order(member+1)<<shift;shift+=3;}}
 }return out;
}
__device__ void knock_down(const double* e,int ne,State* s,int who){
 if(s->down_mask&(1<<who))return;
 s->down_mask|=1<<who;s->hp[who]=s->hppct[who]=0;s->lost_count[who]=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j]){
  const double* q=effect(e,s,j);
  if(!s->alive[j]||s->masks[j]<0||!(s->masks[j]&(1<<who))||q[245]>0)continue;
  if(s->end[j]>=1e30)s->lost_definitions[who][s->lost_count[who]++]=s->definition[j];
  s->masks[j]&=~(1<<who);s->target_order[j]=filter_order(s->target_order[j],s->masks[j]);
  s->bullets[j][who]=s->bullet_stacks[j][who]=0;
  // CPU removes current shields but retains capacity maps for shared carriers.
  // Decoy quantities use a distinct CPU map, not removed by knock_down().
  if(q[1]==0&&q[2]==45){s->shield_current[j][who]=0;s->shield_mask[j]&=~(1<<who);}
  if(!s->masks[j]){s->alive[j]=0;s->stacks[j]=0;}
 }
 for(int key=0;key<NE;key++)s->gauges[who][key]=0;
 for(int j=0;j<ne;j++)if(e[j*EW]==who)for(int a=0;a<(int)e[j*EW+144];a++){
  int code=(int)e[j*EW+TD+a*TS];if(code!=26&&code!=44&&code!=45)s->count[j][a]=0;
 }
 for(int key=0;key<NE;key++)s->heal_charge_last[who][key]=0;
 for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(!s->alive[j]&&effect(e,s,j)[0]==who&&effect(e,s,j)[1]==0&&effect(e,s,j)[2]==76){s->shield_present[j]=0;s->shield_current[j][0]=0;}
 // Mark down before ending the mode. CPU's state_end notification is suppressed
 // by the dead owner's personal-notification guard; no gameplay callback fires.
 s->mode[who]=-1;s->mode_end[who]=-1;invalidate(s);
 // CharState._reset_action leaves mode restoration/camera request history for
 // the next living tick. Do not clear pre-cast timers or shared trigger budgets.
 s->hold_release[who]=-1;
 s->reload[who]=s->post[who]=-1;s->charge_phase[who]=0;s->charge_full[who]=-1;s->charging[who]=0;
}
__device__ int incoming_land(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,int pattern,int who,double dmg,int hit_event,int source=-1){
 if(s->down_mask&(1<<who))return 0;const double* p=boss_pattern(s,pattern);int pierce=(int)p[85],covered=s->reload[who]>0&&s->cover_hp[who]>0&&!live_marker(c,e,ne,s,who,71,full);
 int code=absorb_shield(c,e,ne,s,env,who,dmg,t,pierce,full);double shield=s->last_shield_result,cover=0,decoy=0;
 if((pierce||shield<=0)&&covered){cover=mn(s->cover_hp[who],dmg);s->cover_hp[who]-=cover;if(s->cover_hp[who]<=0){s->cover_hp[who]=0;invalidate(s);}}
 double hp=pierce||(shield<=0&&cover<=0)?dmg:0;
 if(hp&&!covered){
  int latest=-1;for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&effect(e,s,j)[1]==0&&effect(e,s,j)[2]==72&&s->shield_current[j][who]>0&&t<s->end[j]&&(latest<0||s->activated[j]>s->activated[latest]||s->activated[j]==s->activated[latest]&&s->entry_seq[j]>s->entry_seq[latest]))latest=j;
  if(latest>=0){decoy=mn(s->shield_current[latest][who],hp);s->shield_current[latest][who]-=decoy;if(decoy>0)hp=0;
   if(s->shield_current[latest][who]<=0){invalidate(s);int any=0;for(int k=0;k<5;k++)if(s->shield_current[latest][k]>0)any=1;if(!any)code|=end_shield(c,e,ne,s,env,latest,s->entry_seq[latest],t,full);}
  }
 }
 if(hp&&live_marker(c,e,ne,s,who,67,full))hp=0;
 if(hp)hp=absorb_heal_storage(c,e,ne,s,who,hp,full);
 if(hp&&s->hp[who]-hp<=0&&live_marker(c,e,ne,s,who,68,full))hp=mx(s->hp[who]-1,0);
 if(hp&&s->hp[who]-hp<=0){code|=notify(c,e,ne,s,env,t,37,who,0,full);if(live_marker(c,e,ne,s,who,68,full))hp=mx(s->hp[who]-1,0);}
 // A lethal hit is logged before down cleanup and subsequent revival callbacks.
 int fell=hp&&s->hp[who]-hp<=0;
 if(hp){s->hp[who]=mx(0,s->hp[who]-hp);if(!fell){sync_hp(c,e,ne,s,who,full);code|=notify(c,e,ne,s,env,t,52,who,0,full);}}
 if(hit_event)code|=notify(c,e,ne,s,env,t,32,who,0,full);
 if(cover)code|=notify(c,e,ne,s,env,t,36,who,0,full);
 fell=fell&&!(s->down_mask&(1<<who));if(fell)s->hp[who]=0;
 if(s->incoming_count>=ILOG)return code|512;
 double* row=s->incoming_log[s->incoming_count++];row[0]=t;row[1]=pattern;row[2]=who;row[3]=dmg;row[4]=pierce;row[5]=decoy;row[6]=shield;row[7]=cover;row[8]=hp;row[9]=s->hp[who];row[10]=fell;row[11]=source+1;
 if(fell){knock_down(e,ne,s,who);code|=notify(c,e,ne,s,env,t,38,who,0,full);int living=31&~s->down_mask;for(int other=0;other<5;other++)if(living&(1<<other))code|=notify(c,e,ne,s,env,t,46,other,0,full);}
 return code;
}
__device__ int incoming_attacks(const double* c,const double* e,int ne,State* s,const double* env,double t,int full){
 int code=0;
 for(int k=0;k<s->incoming_queued;k++){
  int identity=s->incoming_queue[k],pattern=identity%BP,source=identity/BP-1;const double* p=boss_pattern(s,pattern);double flat=0;
  for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(effect(e,s,j)[1]==0&&effect(e,s,j)[2]==26&&s->alive[j]&&s->end[j]>t){resolve_live_slot(c,e,ne,s,j,full);if((s->masks[j]&32)&&base_condition(c,e,ne,s,effect(e,s,j),full,1,j,0,0,0,3,5))flat+=c[(int)effect(e,s,j)[0]*CW]*(recipient_value(c,e,ne,s,j,(int)effect(e,s,j)[0],full)/100);}
  double atk=mx(p[81]+flat,0);
  for(Order raw=incoming_targets(c,e,ne,s,p,full);raw;raw>>=3){int who=(raw&7)-1;double dmg=mx(mx(atk-rank_def(c,e,ne,s,who,full),0)*p[80]/100*mx(0,1+live_amount(c,e,ne,s,who,12,full)/100),1);
   Order group=incoming_group(c,e,ne,s,who,full);int count=0;for(Order g=group;g;g>>=3)count++;
   for(Order g=group;g;g>>=3){int member=(g&7)-1;code|=incoming_land(c,e,ne,s,env,t,full,pattern,member,dmg/count,member==who,source);if(code)return code;}
  }
 }s->incoming_queued=0;return code;
}

__device__ int squad_frame(const double* c,const double* e,int ne,State* s,const double* env,double t,int* full,const double* stimulus=0){
 // CPU fills all magazines after startup notifications and before its first tick.
 if(!s->mags_initialized){for(int who=0;who<5;who++)s->ammo[who]=full_ammo(c,e,ne,s,who,*full);s->mags_initialized=1;}
 int code=boss_frame(s,t);if(code)return code;code|=boss_effect_state(e,ne,s,t);if(code)return code;int part_events=parts_refresh(env,s);code|=tick_effects(c,e,ne,s,env,t,*full);if(s->boss_count)sync_cover(c,e,ne,s,*full);code|=parts_events(c,e,ne,s,env,t,*full,part_events);code|=boss_events(c,e,ne,s,env,t,*full);
 if(s->boss_count){code|=incoming_attacks(c,e,ne,s,env,t,*full);if(code)return code;}
 if(stimulus&&stimulus[2]==1)code|=absorb_shield(c,e,ne,s,env,(int)stimulus[3],stimulus[6],t,(int)stimulus[7],*full);
 code|=flush_lands(c,e,ne,s,env,t,*full);
 int candidate_stage[5];for(int i=0;i<5;i++){
  int override_stage=0;for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&(int)effect(e,s,j)[0]==i&&effect(e,s,j)[252]>0)override_stage=(int)effect(e,s,j)[252];
  s->burst_stage[i]=override_stage?override_stage:(int)c[i*CW+20];candidate_stage[i]=s->burst_stage[i];
  if(candidate_stage[i]==4&&c[i*CW+161]>0&&c[i*CW+160]==0&&!override_stage)candidate_stage[i]=3;
 }
 // CPU changes full_burst and invalidates before callbacks. Clearing the cast
 // flags afterwards retains any complete buff dictionaries queried by them.
 if(s->phase==5&&t>=s->fb_end-1e-9){
  s->phase=0;*full=0;invalidate(s);s->cached_full=0;code|=log_burst(s,t,5,-1);
  for(int i=0;i<5;i++)code|=notify(c,e,ne,s,env,t,2,i,0,0);
  double regen=0;for(int i=0;i<5;i++)regen=mx(regen,c[i*CW+25]);s->gauge=t+regen;s->cycle++;s->cast_mask=0;
 }
 if(s->phase==0&&(c[44]>0?s->burst_amount>=100-1e-9:t>=s->gauge-1e-9)){if(c[44]>0)code|=log_burst(s,t,6,-1);s->burst_amount=0;for(int j=0;j<3;j++)s->cycle_users[j]=0;s->reenter_done=0;s->reenter_slot=0;s->phase=1;s->action=t;s->opened=t;for(int i=0;i<5;i++)code|=notify(c,e,ne,s,env,t,4,i,1,0);}
 if(s->wait_mask){double at=1e30;for(int i=0;i<5;i++)if(s->wait_mask&(1<<i))at=mn(at,s->ready[i]);s->action=mx(s->opened,at);}
 // A stage with no candidates stays permanently blocked. Dead candidates
 // remain in the wait set, but cannot cast; revival needs no special restart.
 if(s->phase>=1&&s->phase<=3&&t>=s->action-1e-9){
  int stage=s->phase,picked=-1;double earliest=1e30;int stop=0,mask=0;s->wait_mask=0;
  if(s->reenter_slot)for(int i=0;i<5;i++)code|=notify(c,e,ne,s,env,t,4,i,stage,0);
  int first=-1,restricted=stage<3&&!s->reenter_slot;for(int i=0;i<5;i++)if(candidate_stage[i]==stage||candidate_stage[i]==4){if(first<0)first=i;if(c[i*CW+22]!=0||c[i*CW+160]>0)restricted=0;}
  for(int rank=0;rank<3&&!stop;rank++)for(int i=0;i<5;i++){
   const double* a=c+i*CW;if((candidate_stage[i]!=stage&&candidate_stage[i]!=4)||(restricted&&i!=first))continue;mask|=1<<i;
   int pr=1;
   if(a[22]>0)pr=s->cycle%(int)a[22]==0?0:2;
   else if(a[22]<0){int cycle=s->cycle-1;pr=cycle>=0&&cycle<160&&((unsigned int)a[35+cycle/32]&(1u<<(cycle%32)))?0:2;}
   if(pr!=rank)continue;
   earliest=mn(earliest,s->ready[i]);if(stat(c,e,ne,s,i,28,0)>0||(s->down_mask&(1<<i)))continue;
   if(t<s->ready[i]-1e-9){if(s->ready[i]-t<=a[23]+1e-9){s->action=s->ready[i];s->wait_mask=1<<i;stop=1;break;}continue;}
   double press=mx(s->opened,s->ready[i])+a[24];if(t<press-1e-9){s->action=press;stop=1;break;}
   picked=i;stop=1;break;
  }
  if(picked>=0){
   int i=picked;s->cycle_users[stage-1]|=1<<i;s->cast_mask|=1<<i;
   // CPU marks the caster before its cooldown query. Merely marking it does
   // not invalidate an already computed complete buff query at this time.
   for(int k=0;k<5;k++){s->valid[k]=0;s->query_camera_at[k]=-1;}
   s->cd_applied[i]=stat(c,e,ne,s,i,32,0);s->ready[i]=t+mx(0,c[i*CW+21]-s->cd_applied[i]);
   code|=notify(c,e,ne,s,env,t,3,i,0,0);code|=notify(c,e,ne,s,env,t,41,i,stage,0);for(int k=0;k<5;k++)code|=notify(c,e,ne,s,env,t,42,k,0,0);code|=log_burst(s,t,stage+(s->reenter_slot?6:0),i);
   if(stage==3){s->fb_caster=i;s->fb_cast_t=t;}
   int reentry=s->burst_pending_present[i];s->burst_pending_present[i]=0;
   if(!reentry)for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&(int)effect(e,s,j)[0]==i&&effect(e,s,j)[253]>0){reentry=1;break;}
   if(reentry&&!(s->reenter_done&(1<<stage))){s->reenter_done|=1<<stage;s->reenter_slot=1;s->opened=s->action=t+c[163];}
   else if(stage==3){s->reenter_slot=0;s->phase=4;s->action=t+.37;}
   else{s->reenter_slot=0;s->phase++;s->opened=t+.1;s->action=t+.1;for(int j=0;j<5;j++)code|=notify(c,e,ne,s,env,t,4,j,stage+1,0);}
  }else if(!stop){s->action=mx(s->action,earliest);s->wait_mask=mask;}
 }
 if(s->phase==4&&t>=s->action-1e-9){
  double ext=0;for(int j=s->slot_head;j>=0;j=s->slot_next[j])if((int)effect(e,s,j)[1]==0&&(int)effect(e,s,j)[2]==29&&s->alive[j]){if(((unsigned int)effect(e,s,j)[12]&(1u<<3))&&((int)effect(e,s,j)[0]!=s->fb_caster||s->activated[j]<s->fb_cast_t-1e-9))continue;ext+=effect(e,s,j)[6];}
  s->fb_end=t+mx(1,10+ext);s->phase=5;*full=1;
  for(int i=0;i<5;i++)code|=notify(c,e,ne,s,env,t,1,i,0,1);
  for(int i=0;i<5;i++){double extra=stat(c,e,ne,s,i,32,1)-s->cd_applied[i];if(s->ready[i]>t&&extra>0)s->ready[i]=mx(t,s->ready[i]-extra);s->cd_applied[i]=0;}
  // B3 bonus hits are evaluated after full-burst buffs, excluding later cast buffs.
  for(int at=0;at<s->burst_damage_count;at++){
   int j=s->burst_damage_rows[at];const double* q=effect(e,s,j);if(q[51]!=1)continue;for(int k=0;k<MASK_WORDS;k++)s->excluded[k]=(unsigned int)q[B3_MASK+k];invalidate(s);
   double coeff=q[6]*s->burst_damage_mag[at];if(q[10]>=0)coeff*=ref(e,ne,s,(int)q[0],(int)q[10]);if(coeff!=0)for(int h=0;h<s->burst_damage_hits[at];h++){double hit=damage(c,e,ne,s,env,(int)q[0],1,coeff,(int(q[39])&256)?1:0,(int)q[39],(int)q[53],q[54]);s->total[(int)q[0]]+=hit;if(s->now_count>=NE)return 4;s->now_owner[s->now_count]=(int)q[0];s->now_damage[s->now_count]=hit;ReachHit part=reach_sample(c,e,ne,s,env,(int)q[0],1,coeff,(int(q[39])&256)?1:0,(int)q[39],(int)q[53],q[54]);s->now_reach[s->now_count]=part.reach;s->now_part[s->now_count++]=part.damage;}
   for(int k=0;k<MASK_WORDS;k++)s->excluded[k]=0;invalidate(s);
  }
  // Resolve explicitly delayed attacks after legacy B3 bonus hits, using
  // the common damage handler without rechecking cast gates or budgets.
  int landing_begin=s->land_count;
  for(int at=0;at<s->burst_damage_count;at++){
   int j=s->burst_damage_rows[at];const double* q=effect(e,s,j);if(q[51]!=2)continue;
   for(int k=0;k<MASK_WORDS;k++)s->excluded[k]=(unsigned int)q[B3_MASK+k];invalidate(s);
   code|=notify(c,e,ne,s,env,t,57,(int)q[0],j,1,0,0,0,s->burst_damage_hits[at]);
   for(int k=0;k<MASK_WORDS;k++)s->excluded[k]=0;invalidate(s);
  }
  int landing_end=s->land_count;
  s->burst_damage_count=0;for(int k=0;k<s->now_count;k++){int who=s->now_owner[k];code|=land_damage(c,e,ne,s,env,t,1,who,s->now_damage[k],HIT_SKILL);code|=parts_land(c,e,ne,s,env,t,1,who,s->now_reach[k],s->now_part[k],-1,HIT_SKILL);}s->now_count=0;
  // These packets land in this frame, before weapons. Keep pre-existing
  // next-frame packets and newly emitted landing callbacks in their queue.
  for(int k=landing_begin;k<landing_end;k++){int who=s->land_owner[k];code|=land_damage(c,e,ne,s,env,t,1,who,s->land_damage[k],s->land_family[k]);code|=parts_land(c,e,ne,s,env,t,1,who,s->land_reach[k],s->land_part[k],-1,s->land_family[k]);}
  int landing_tail=s->land_count-landing_end;
  for(int k=0;k<landing_tail;k++){int src=landing_end+k,dst=landing_begin+k;s->land_owner[dst]=s->land_owner[src];s->land_family[dst]=s->land_family[src];s->land_damage[dst]=s->land_damage[src];s->land_reach[dst]=s->land_reach[src];s->land_part[dst]=s->land_part[src];}
  s->land_count=landing_begin+landing_tail;
  code|=log_burst(s,t,4,-1);
  // Match the CPU verbose snapshot's raw resolution once per squad recipient.
  // This intentionally does not resolve/cache the active carrier itself.
  for(int who=0;who<5;who++)for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&s->masks[j]<0&&effect(e,s,j)[4]==19)random_target(e,s,effect(e,s,j));
 }
 s->burst_charging=s->phase==0;
 code|=arbitrate_control(c,s,t,*full);
 for(int i=0;i<5;i++){
  s->hit[i]=0;s->hits[i]=0;code|=weapon_frame(c,e,ne,s,env,t,i,*full);
  for(int k=0;k<s->hits[i];k++){code|=land_damage(c,e,ne,s,env,t,*full,i,s->hit_unit[i]);code|=parts_land(c,e,ne,s,env,t,*full,i,s->shot_reach[i],s->shot_part[i]);}
 }
 return code;
}
extern "C" __global__ void detail_timer_registry_v81(const double* chars,const double* effects,const int* counts,const double* enemy,const double* worlds,const double* script,const unsigned int* initial_rng,int steps,int nq,int n,double* queries,double* totals,int* status,State* workspace,int compensated_sums){
 int id=blockIdx.x*blockDim.x+threadIdx.x;if(id>=n)return;
 const double* c=chars+id*5*CW;const double* e=effects+id*NE*EW;const double* original_env=enemy+id*EN;int ne=counts[id];
 State* s=workspace+id;s->ag_n=s->ag_clock=0;for(int k=0;k<AG;k++)s->ag_active[k]=0;s->source_count=s->source_owner_count=0;s->ramp_active=s->ramp_clock=s->ramp_heap_n=0;for(int k=0;k<NE;k++){s->ramp_on[k]=0;s->ramp_epoch[k]=0;s->ramp_heap_pos[k]=-1;}build_event_index(e,ne,s);status[id]|=build_group_plans(e,s);double* env=s->world;for(int k=0;k<EN;k++)env[k]=original_env[k];s->last_shield_result=0;s->random_special_present=0;for(int k=0;k<ne;k++)if(e[k*EW+4]==19&&(e[k*EW+241]>0||e[k*EW+1]==0&&e[k*EW+2]==26))s->random_special_present=1;s->random_error=0;s->random_cache_count=0;for(int k=0;k<624;k++)s->rng.words[k]=initial_rng[id*1250+k];s->rng.index=(int)initial_rng[id*1250+624];for(int k=0;k<624;k++)s->boss_rng.words[k]=initial_rng[id*1250+625+k];s->boss_rng.index=(int)initial_rng[id*1250+1249];s->down_mask=s->reviving_mask=0;for(int who=0;who<5;who++){s->lost_count[who]=0;s->reviving_pct[who]=0;}s->incoming_count=s->incoming_queued=0;for(int k=0;k<BP;k++)s->incoming_shots[k]=0;s->cover_base=worlds[id*WP+267]>0?worlds[id*WP+264]:2000000;for(int k=0;k<5;k++)s->cover_hp[k]=s->cover_max[k]=s->cover_base;s->compensated_sums=compensated_sums;s->mags_initialized=0;s->slots=ne;s->slot_head=ne?0:-1;s->slot_tail=ne-1;for(int j=0;j<NS;j++){s->heal_store_expiry[j]=-1;s->definition[j]=j<ne?j:-1;s->alive[j]=0;s->bullet_initialized[j]=0;s->runtime_cond[j]=0;s->slot_next[j]=j+1<ne?j+1:-1;s->entry_seq[j]=0;s->dot_present[j]=0;s->bullet_left[j]=-1;s->shield_mask[j]=0;s->shield_present[j]=0;for(int p=0;p<5;p++)s->shield_current[j][p]=s->shield_capacity[j][p]=0;s->alive[j]=0;s->stacks[j]=0;s->end[j]=-1;s->capture[j]=-1;s->masks[j]=0;s->target_order[j]=0;s->activated[j]=-1;for(int k=0;k<6;k++)s->bullets[j][k]=s->bullet_stacks[j][k]=0;}int full=0;s->when=0;s->timer_clock=s->entry_clock=0;s->cast_mask=0;s->heal_source=-1;s->ammo_query_mask=0;for(int i=0;i<5;i++)s->auto_reload[i]=0;s->lazy_dirty=0;s->land_count=0;s->now_count=0;s->squad_mode=0;for(int j=0;j<steps;j++)if(script[j*8+1]==4){s->squad_mode=1;break;}s->cached_full=0;invalidate(s);for(int j=0;j<MASK_WORDS;j++)s->excluded[j]=0;
 for(int j=0;j<NE;j++){for(int k=0;k<5;k++){s->hold_fired[k][j]=0;s->heal_charge_last[k][j]=0;s->gauges[k][j]=0;s->gauge_present[k][j]=0;s->gauge_cap[k][j]=1e30;}s->timer_active[j]=0;s->timer_epoch[j]=0;s->instant_next[j]=-2;s->timer_at[j]=s->timer_end[j]=-1;s->timer_seq[j]=s->entry_seq[j]=0;s->dot_present[j]=0;s->bullet_left[j]=-1;for(int k=0;k<6;k++)s->bullets[j][k]=s->bullet_stacks[j][k]=0;s->chance_acc[j]=s->noncore_acc[j]=0;s->activations[j]=0;s->shield_mask[j]=0;s->shield_present[j]=0;for(int p=0;p<5;p++)s->shield_current[j][p]=s->shield_capacity[j][p]=0;s->alive[j]=0;s->stacks[j]=0;s->end[j]=-1;s->capture[j]=-1;s->pending[j]=0;s->masks[j]=0;s->target_order[j]=0;for(int k=0;k<EVS;k++)s->count[j][k]=0;s->period_at[j]=e[j*EW+44];s->period_prev[j]=0;s->period_initialized[j]=0;s->activated[j]=-1;}
 s->instant_head=s->instant_tail=-1;s->control_aim_mask=0;for(int i=0;i<5;i++)s->control_aim[i]={ACTOR_BODY,0,1};
 for(int i=0;i<5;i++){s->ctrl_preempt[i]=0;s->query_camera[i]=(int)c[42];s->charging[i]=0;s->ctrl_prev[i]=0;s->ctrl_prio[i]=0;s->ctrl_seq[i]=0;s->hold_close[i]=-1;s->hold_kind[i]=0;s->tap[i]=0;s->force_full[i]=0;s->charge_full[i]=-1;s->hold_release[i]=-1;s->hold_anchor[i]=-1;s->hold_reentry[i]=-1;s->hold_start[i]=-1;s->last_full[i]=-1e9;s->tap_hold[i]=s->tap_charge[i]=s->tap_release[i]=s->tap_post[i]=0;s->mode_shots[i]=0;s->mode_restored[i]=0;s->reload_in_mode[i]=0;s->mode_ammo[i]=-1;s->charge_post[i]=0;s->weapon_context[i]=0;s->mode_started[i]=0;s->mode_ready[i]=-1;s->hits[i]=0;s->hit_unit[i]=0;s->frac[i][0]=s->frac[i][1]=s->frac[i][2]=s->frac[i][3]=0;s->hp[i]=c[i*CW+28];s->hppct[i]=100;s->hit[i]=0;s->mode[i]=-1;s->mode_end[i]=-1;s->total[i]=0;s->prev_mode[i]=-1;s->started[i]=0;s->shots[i]=0;s->warm[i]=0;s->last[i]=-999;s->inter[i]=0;s->next[i]=0;s->ammo[i]=c[i*CW+2];s->reload[i]=-1;s->post[i]=-1;s->charge_phase[i]=0;s->charge_start[i]=0;s->ready[i]=0;s->cd_applied[i]=0;}
 s->counter_clock=s->counter_completed=s->counter_error=s->dead_count=0;for(int r=0;r<NS;r++){s->counter_uid[r]=s->counter_epoch[r]=s->counter_done[r]=0;s->counter_credit[r]=0;s->counter_end[r]=-1;}for(int k=0;k<10;k++)s->counter_last[k]=0;
 s->hp_interest=s->hp_pending=s->in_hp_edge=s->hp_edge_error=0;s->hp_edge_prev=s->hp_edge_new=0;
 s->impact_enabled=0;for(int k=0;k<OW;k++)s->impact_summary[k]=0;s->impact_summary[27]=s->impact_summary[28]=-1;for(int j=0;j<steps;j++)if(script[j*8+1]==2&&script[j*8+2]==126)s->impact_enabled=1;
 s->hp_log_enabled=s->hp_log_count=0;for(int j=0;j<steps;j++)if(script[j*8+1]==2&&script[j*8+2]==120)s->hp_log_enabled=1;
 for(int name=0;name<NE;name++){s->damage_accum_last[name]=0;s->named_hit_interest[name]=0;for(int owner=0;owner<5;owner++)s->named_skill_crit[owner][name]=0;}
 s->event_interest=0;for(int j=0;j<ne;j++)if(e[j*EW+1]==0&&e[j*EW+2]==87)s->event_interest|=INTEREST_TARGET_COUNTER;for(int j=0;j<ne;j++)if(e[j*EW+55]>0)s->event_interest|=INTEREST_EXCLUSIVE_AMMO;for(int j=0;j<ne;j++)if(e[j*EW+1]==0&&(e[j*EW+2]==81||e[j*EW+2]==82))s->event_interest|=INTEREST_DAMAGE_ACCUM;for(int j=0;j<ne;j++)for(int k=0;k<(int)e[j*EW+144];k++){const double* d=e+j*EW+TD+k*TS;int code=(int)d[0];if(code==49)s->named_hit_interest[(int)d[3]]|=1<<(int)e[j*EW];if(code==44||code==45)s->event_interest|=1<<(code-44);if((code==31||code==48)&&d[6]<=-11)s->hp_interest=1;}
 for(int j=0;j<ne;j++)for(int k=0;k<(int)e[j*EW+14];k++){int type=(int)e[j*EW+15+k*3];if(type==WORLD_TARGET_BOSS||type==WORLD_TARGET_ADD)s->event_interest|=INTEREST_TARGET_CONTEXT;}
 for(int j=0;j<ne;j++)if(e[j*EW+4]==4&&e[j*EW+48]>0)s->event_interest|=INTEREST_ENEMY_FIELDS|INTEREST_TARGET_CONTEXT;
 s->burst_amount=0;s->burst_charging=1;
 s->burst_damage_count=0;s->reenter_done=0;s->reenter_slot=0;for(int i=0;i<5;i++){s->burst_stage[i]=(int)c[i*CW+162];s->burst_pending[i]=0;s->burst_pending_present[i]=0;}
 s->condition_target={ACTOR_BODY,0,1};
 s->normal_landed_mask=0;s->camera_lens=-1;s->ctrl_owner=-1;s->camera_mask=(int)c[42];for(int j=0;j<3;j++)s->cycle_users[j]=0;s->phase=0;s->cycle=1;s->action=0;s->opened=0;s->gauge=3;s->fb_end=-1;s->fb_caster=-1;s->fb_cast_t=-1;s->wait_mask=0;s->log_count=0;
 for(int who=0;who<6;who++)for(int key=0;key<NE;key++)s->immune_used[who][key]=0;
 s->part_pending=0;for(int p=0;p<32;p++){s->part_dead[p]=s->part_hits[p]=0;s->part_dealt[p]=0;s->part_at[p]=-1;}parts_refresh(env,s);
 int source_mode=0;for(int k=0;k<steps;k++)if(script[k*8+1]==15)source_mode=1;
 status[id]=boss_init(s,worlds+id*WP,source_mode);status[id]|=boss_effect_state(e,ne,s,0);
 for(int step=0;step<steps;step++){
  if(status[id])break;
  const double* cmd=script+step*8;double t=cmd[0];int op=(int)cmd[1],ev=(int)cmd[2],who=(int)cmd[3],arg=(int)cmd[4],out=(int)cmd[5];
  if(s->squad_mode&&op!=4&&s->when!=t)invalidate(s);s->when=t;
  if(op==2&&ev==128){
   double* dst=queries+(id*nq+out)*OW;for(int k=0;k<OW;k++)dst[k]=0;
   int begin=s->event_offsets[arg],end=s->event_offsets[arg+1],page=(int)cmd[6];dst[0]=begin;dst[1]=end;dst[2]=s->event_offsets[EVENT_KINDS];dst[3]=end-begin;
   for(int k=0;k<OW-4&&begin+page*(OW-4)+k<end;k++)dst[4+k]=s->event_definitions[begin+page*(OW-4)+k];continue;
  }
  if(!s->squad_mode&&op!=7&&op!=15)status[id]|=tick_effects(c,e,ne,s,env,t,full);
  if(op==0){if(ev==1)full=1;if(ev==2)full=0;status[id]|=notify(c,e,ne,s,env,t,ev,who,arg,full,cmd[6],(int)cmd[7]);}
  if(op==16){
   int generation=0,alive=0,parent_kind=-1,parent_id=-1;
   if(!world_actor(s,arg%8,arg/8,&generation,&alive,&parent_kind,&parent_id)||generation!=(int)cmd[5])status[id]|=8;
   else{if(ev==1)full=1;if(ev==2)full=0;TargetRef target={arg%8,arg/8,generation};status[id]|=notify(c,e,ne,s,env,t,ev,who,0,full,cmd[6],(int)cmd[7],0,-1,0,target);}
  }
  if(op==17){int generation=0,alive=0,parent_kind=-1,parent_id=-1;
   if(!world_actor(s,arg%8,arg/8,&generation,&alive,&parent_kind,&parent_id)||!alive||generation!=(int)cmd[5])status[id]|=8;
   else{s->control_aim[who]={arg%8,arg/8,generation};s->control_aim_mask|=1<<who;}
  }
  if(op==3)status[id]|=weapon_frame(c,e,ne,s,env,t,who,full);
  if(op==4)status[id]|=squad_frame(c,e,ne,s,env,t,&full,cmd);
  if(op==5){status[id]|=flush_lands(c,e,ne,s,env,t,full);status[id]|=boss_finish(s,t);}
  if(op==6){
   if(ev==0)status[id]|=absorb_shield(c,e,ne,s,env,who,cmd[6],t,(int)cmd[7],full);
   else if(ev==1)s->last_shield_result=heal_shield(e,s,who,cmd[6],t);
   else{status[id]|=tick_effects(c,e,ne,s,env,t,full);s->last_shield_result=0;}
  }
  if(op==7){if(ev==2){s->total[who]+=cmd[6];status[id]|=land_damage(c,e,ne,s,env,t,full,who,cmd[6],HIT_EXTERNAL);status[id]|=flush_lands(c,e,ne,s,env,t,full);}else if(ev==0)status[id]|=parts_land(c,e,ne,s,env,t,full,who,arg,cmd[6],(int)cmd[7],HIT_EXTERNAL);else{int count=parts_refresh(env,s);status[id]|=tick_effects(c,e,ne,s,env,t,full);status[id]|=parts_events(c,e,ne,s,env,t,full,count);}}
  if(op==8){Impact p={who,arg%8,arg/8,(int)cmd[5],ev%4,(ev/4)%4,ev/16,cmd[6],cmd[7]};record_impact(s,p,t);status[id]|=group_collect(s,&p,t);status[id]|=collect_target_counters(c,e,ne,s,env,t,full,&p);}
  if(op==10)status[id]|=group_begin(s,who,arg,ev,(int)cmd[6],t);
  if(op==11)status[id]|=group_dispatch(c,e,ne,s,env,group_seal(s,who,arg,(int)cmd[6],t),t,full);
  if(op==12&&group_seal(s,who,arg,(int)cmd[6],t)<0)status[id]|=8;
  if(op==13)status[id]|=group_dispatch(c,e,ne,s,env,group_sealed(s,who,arg,(int)cmd[6]),t,full);
  if(op==14){Impact p={who,arg%8,arg/8,(int)cmd[5],ev%4,(ev/4)%4,ev/16,cmd[6],cmd[7]};status[id]|=add_land(c,e,ne,s,env,t,full,p);}
  if(op==15){status[id]|=boss_frame(s,t);status[id]|=boss_effect_state(e,ne,s,t);status[id]|=tick_effects(c,e,ne,s,env,t,full);if(s->boss_count)sync_cover(c,e,ne,s,full);status[id]|=boss_events(c,e,ne,s,env,t,full);status[id]|=incoming_attacks(c,e,ne,s,env,t,full);}
  if(op==9)status[id]|=collect_target_counters(c,e,ne,s,env,t,full,0,ev,arg,(int)cmd[5]);
  if(op==2){
   double* dst=queries+(id*nq+out)*OW;
   if(ev==135){
    for(int k=0;k<OW;k++)dst[k]=0;int generation=0,alive=0,parent_kind=-1,parent_id=-1;
    if(world_actor(s,arg%8,arg/8,&generation,&alive,&parent_kind,&parent_id)&&generation==(int)cmd[7]&&alive){
     TargetScope scope(s,1);TargetRef target={arg%8,arg/8,generation};set_condition_target(s,target);dst[0]=stat(c,e,ne,s,who,(int)cmd[6],full);
     for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&s->end[j]>t&&(s->masks[j]&32)&&enemy_field_matches(s,j)){dst[1]++;dst[2]+=s->stacks[j];}
     dst[4]=arg%8;dst[5]=arg/8;dst[6]=generation;
    }continue;
   }
   if(ev==134){for(int j=0;j<OW;j++)dst[j]=0;int index=world_actor_index(s,ACTOR_ADD,arg);
    if(index>=0){const double* b=s->boss_program+WA+1+index*ACTOR_WORDS;int run=(int)b[3];dst[0]=1;dst[1]=arg;dst[2]=s->boss_opens[run];dst[3]=s->boss_opens[run]>0&&s->boss_active[run]&&!s->add_gone[index];dst[4]=s->add_gone[index];dst[5]=s->add_dealt[index];dst[6]=s->add_hits[index];dst[7]=s->boss_opens[run]?s->boss_start[run]:-1;dst[8]=run;dst[9]=b[4];dst[10]=s->boss_opens[run]?s->add_order[run]+b[4]+1:0;}
    dst[11]=s->add_live_snapshot;dst[12]=s->add_last_took;dst[13]=s->add_overkill;for(int k=0;k<5;k++)dst[14+k]=s->add_total[k];dst[19]=s->add_pending_deaths;continue;}
   if(ev==133){for(int j=0;j<OW;j++)dst[j]=0;int generation=0,alive=0,parent_kind=-1,parent_id=-1;
    int present=world_actor(s,arg%8,arg/8,&generation,&alive,&parent_kind,&parent_id);
    if(present&&(!cmd[6]||cmd[6]==generation)){dst[0]=1;dst[1]=arg%8;dst[2]=arg/8;dst[3]=generation;dst[4]=alive;dst[5]=parent_kind;dst[6]=parent_id;dst[7]=parent_kind>=0?1:0;}continue;}
   if(ev==131||ev==132){for(int j=0;j<OW;j++)dst[j]=0;int k=ev==132?group_sealed(s,who,arg,(int)cmd[6]):group_find(s,who,arg);dst[0]=k>=0;dst[4]=s->ag_n;dst[5]=s->ag_clock;
    if(k>=0){dst[1]=s->ag_epoch[k];dst[2]=s->ag_count[k];dst[3]=s->ag_mask[k];for(int j=0;j<14;j++){int n=(int)cmd[7]*14+j;if(n>=s->ag_count[k])break;dst[6+3*j]=s->ag_kind[k][n];dst[7+3*j]=s->ag_identity[k][n];dst[8+3*j]=s->ag_generation[k][n];}}continue;}
   if(ev==126){for(int k=0;k<OW;k++)dst[k]=s->impact_summary[k];continue;}
   if(ev==127){
    for(int k=0;k<OW;k++)dst[k]=0;
    for(int r=s->slot_head;r>=0;r=s->slot_next[r]){const double* q=effect(e,s,r);if(s->alive[r]&&q[1]==0&&q[2]==87&&q[0]==who&&(arg<0||q[3]==arg)&&s->counter_uid[r]==s->entry_seq[r]&&s->counter_end[r]>t){dst[0]++;dst[1]+=s->counter_credit[r];dst[3]+=s->counter_done[r];}}
    dst[2]=s->counter_completed;dst[4]=s->dead_count;dst[5]=s->counter_clock;for(int k=0;k<10;k++)dst[8+k]=s->counter_last[k];continue;
   }
   if(ev==112){for(int k=0;k<OW;k++)dst[k]=0;for(int who=0;who<6;who++){if(arg>=0)dst[who]=s->immune_used[who][arg];else for(int key=0;key<NE;key++)dst[who]+=s->immune_used[who][key];}continue;}
   if(ev==111){
    for(int k=0;k<OW;k++)dst[k]=0;dst[0]=s->last_shield_result;FloatSum amounts[5],capacities[5];for(int p=0;p<5;p++){amounts[p]={0,0};capacities[p]={0,0};}
    for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&(arg<0||effect(e,s,j)[3]==arg)){
     const double* q=effect(e,s,j);if(q[1]==0&&q[2]==45||q[261]>0){dst[16]++;dst[17]=(int)dst[17]|s->masks[j];dst[18]+=s->stacks[j];dst[19]=(int)dst[19]|s->shield_present[j];}
     if(q[1]==0&&q[2]==45)for(int p=0;p<5;p++){add_sum(s,&amounts[p],s->shield_current[j][p]);add_sum(s,&capacities[p],s->shield_capacity[j][p]);if(s->shield_current[j][p]>0)dst[11+p]=1;}
    }
    for(int p=0;p<5;p++){dst[1+p]=finish_sum(amounts[p]);dst[6+p]=finish_sum(capacities[p]);}continue;
   }
  if(ev==130){int j=arg;dst[0]=s->alive[j]&&s->dot_present[j]&&s->ramp_epoch[j]>0;
   if(dst[0]){dst[1]=s->stacks[j];dst[2]=s->ramp_count[j];dst[3]=s->ramp_index[j];dst[4]=s->ramp_epoch[j];dst[5]=s->ramp_on[j]?s->ramp_start[j]+(s->ramp_index[j]+1)*e[j*EW+340]:-1;dst[6]=s->timer_at[j];dst[7]=s->timer_end[j];dst[8]=s->timer_active[j];}continue;}
  if(ev==129){int at=source_find(s,who,arg);dst[0]=at>=0;dst[1]=at<0?0:source_population(s,at,t);dst[2]=at<0?-1:s->source_next[at];dst[3]=at<0?0:s->source_epoch[at];dst[4]=at<0?0:s->source_slots[at];dst[5]=s->source_count;for(int k=0;at>=0&&k<s->source_slots[at];k++)dst[6+k]=s->source_expiry[at][k];continue;}
   if(ev==121){
    for(int k=0;k<OW;k++)dst[k]=0;FloatSum amounts[5],capacities[5];for(int p=0;p<5;p++){amounts[p]={0,0};capacities[p]={0,0};}
    for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&effect(e,s,j)[1]==0&&effect(e,s,j)[2]==72&&(arg<0||effect(e,s,j)[3]==arg)){
     dst[16]++;for(int p=0;p<5;p++){add_sum(s,&amounts[p],s->shield_current[j][p]);add_sum(s,&capacities[p],s->shield_capacity[j][p]);}
    }
    for(int p=0;p<5;p++){dst[1+p]=finish_sum(amounts[p]);dst[6+p]=finish_sum(capacities[p]);}continue;
   }
   if(ev==125){
    for(int k=0;k<OW;k++)dst[k]=0;
    for(int j=s->slot_head;j>=0;j=s->slot_next[j]){const double* q=effect(e,s,j);
     if(!s->alive[j]||q[1]!=0||(q[2]!=85&&q[2]!=86)||(arg>=0&&q[3]!=arg))continue;
     int owner=(int)q[0];dst[1+owner]+=s->shield_capacity[j][0];dst[6+owner]+=s->shield_capacity[j][1]+1;dst[11+owner]+=s->shield_current[j][0];dst[16]++;
    }continue;
   }
   if(ev==124){
    for(int k=0;k<OW;k++)dst[k]=0;
    for(int name=0;name<NE;name++)if(arg<0||name==arg)dst[17]+=s->damage_accum_last[name];
    for(int j=s->slot_head;j>=0;j=s->slot_next[j]){const double* q=effect(e,s,j);
     if(!s->alive[j]||q[1]!=0||(q[2]!=81&&q[2]!=82)||(arg>=0&&q[3]!=arg))continue;
     int owner=(int)q[0];dst[1+owner]+=s->shield_current[j][0];dst[6+owner]+=s->shield_capacity[j][0];dst[11+owner]+=s->shield_present[j]==2;dst[16]++;
    }continue;
   }
   if(ev==123){
    for(int k=0;k<OW;k++)dst[k]=0;double amounts[5]={0,0,0,0,0},capacities[5]={0,0,0,0,0};
    for(int owner=0;owner<5;owner++)for(int key=0;key<NE;key++)if(arg<0||key==arg)amounts[owner]+=s->heal_charge_last[owner][key];
    for(int j=s->slot_head;j>=0;j=s->slot_next[j]){const double* q=effect(e,s,j);if(!s->alive[j]||q[1]!=0||q[2]!=76||s->shield_present[j]==0||(arg>=0&&q[3]!=arg))continue;int owner=(int)q[0];dst[16]++;amounts[owner]+=s->shield_current[j][0];capacities[owner]+=s->shield_capacity[j][0];}
    for(int owner=0;owner<5;owner++){dst[1+owner]=amounts[owner];dst[6+owner]=capacities[owner];}continue;
   }
   if(ev==122){
    for(int k=0;k<OW;k++)dst[k]=0;FloatSum amounts[5],capacities[5];for(int p=0;p<5;p++){amounts[p]={0,0};capacities[p]={0,0};}
    for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&effect(e,s,j)[1]==0&&effect(e,s,j)[2]==74&&(arg<0||effect(e,s,j)[3]==arg)){
     dst[16]++;for(int p=0;p<5;p++){add_sum(s,&amounts[p],s->shield_current[j][p]);add_sum(s,&capacities[p],s->shield_capacity[j][p]);}
    }
    for(int p=0;p<5;p++){dst[1+p]=finish_sum(amounts[p]);dst[6+p]=finish_sum(capacities[p]);}continue;
   }
   if(ev==110){for(int k=0;k<OW;k++){int word=arg*OW+k;dst[k]=word<624?s->rng.words[word]:word==624?s->rng.index:0;}continue;}
   if(ev==106){for(int k=0;k<OW;k++)dst[k]=0;dst[0]=s->chance_acc[arg];dst[1]=s->noncore_acc[arg];continue;}
   if(ev==105){dst[0]=damage(c,e,ne,s,env,who,full,cmd[6],(int)cmd[7],arg);continue;}
   if(ev==115){for(int k=0;k<OW;k++)dst[k]=0;dst[3]=s->boss_log_n;if(arg<s->boss_log_n){dst[0]=s->boss_log_at[arg];dst[1]=s->boss_log_node[arg];dst[2]=s->boss_log_kind[arg];}continue;}
   if(ev==117){for(int k=0;k<OW;k++)dst[k]=0;dst[12]=s->incoming_count;if(arg<s->incoming_count)for(int k=0;k<12;k++)dst[k]=s->incoming_log[arg][k];continue;}
   if(ev==118){for(int k=0;k<OW;k++){int word=arg*OW+k;dst[k]=word<624?s->boss_rng.words[word]:word==624?s->boss_rng.index:0;}continue;}
   if(ev==119){for(int k=0;k<OW;k++)dst[k]=0;for(int who=0;who<5;who++){dst[who]=s->hp[who];dst[5+who]=s->cover_hp[who];dst[10+who]=s->cover_max[who];}dst[15]=s->down_mask;continue;}
   if(ev==120){for(int k=0;k<OW;k++)dst[k]=0;dst[3]=s->hp_log_count;if(arg<s->hp_log_count)for(int k=0;k<3;k++)dst[k]=s->hp_log[arg][k];continue;}
   if(ev==116){for(int k=0;k<OW;k++)dst[k]=0;dst[0]=env[1];dst[1]=s->boss_distance;dst[2]=s->boss_weapon_mask;dst[3]=s->boss_log_n;unsigned int mask=0;for(int k=0;k<s->boss_count;k++){dst[5+k]=s->boss_opens[k];if(s->boss_active[k])mask|=1u<<k;}dst[4]=mask;dst[37]=env[0];unsigned int dispelled=0;for(int k=0;k<s->boss_count;k++)if(s->boss_dispelled[k])dispelled|=1u<<k;dst[38]=dispelled;continue;}
   if(ev==114){dst[0]=s->part_dead[arg];dst[1]=s->part_dealt[arg];dst[2]=s->part_hits[arg];dst[3]=s->part_at[arg];dst[4]=s->part_min;dst[5]=s->part_pending;continue;}
   if(ev==113){dst[0]=optimal_range(c,e,ne,s,who,full,arg);continue;}
   if(ev==103){dst[0]=stat(c,e,ne,s,who,arg,full);continue;}
   if(ev==104){dst[0]=charge_duration(c,e,ne,s,who,full);continue;}
   if(ev==109){dst[0]=s->burst_amount;dst[1]=s->burst_charging;continue;}
   if(ev==108){dst[0]=s->charging[who];dst[1]=s->charge_phase[who];dst[2]=s->charge_full[who];dst[3]=s->hold_release[who];dst[4]=s->ctrl_owner;dst[5]=s->camera_mask;dst[6]=s->shots[who];dst[7]=s->ctrl_seq[who];dst[8]=s->ctrl_preempt[who];dst[9]=!!(s->normal_landed_mask&(1<<who));dst[10]=s->ammo[who];dst[11]=s->reload[who];continue;}
   if(ev==107){dst[0]=reload_duration(c,e,ne,s,who,full);continue;}
   if(ev==102){dst[0]=s->gauges[who][arg];dst[1]=s->gauge_cap[who][arg];continue;}
   if(ev==101){dst[0]=s->hp[who];dst[1]=s->hppct[who];dst[2]=max_hp(c,e,ne,s,who,full);continue;}
   if(ev==100){dst[3]=s->log_count;if(arg<s->log_count){dst[0]=s->log_t[arg];dst[1]=s->log_event[arg];dst[2]=s->log_who[arg];}continue;}
   for(int k=0;k<ST;k++)dst[k]=stat(c,e,ne,s,who,k,full);
   int mode=s->mode[who];dst[32]=mode<0?c[who*CW+1]:effect(e,s,mode)[26];dst[33]=mode<0?c[who*CW+4]:effect(e,s,mode)[28];dst[34]=mode<0?c[who*CW+2]:effect(e,s,mode)[27];
   dst[35]=mode>=0;dst[36]=damage(c,e,ne,s,env,who,full,dst[32],1,0);dst[37]=arg>=0?ref(e,ne,s,who,arg):0;
   for(int i=0;i<5;i++)dst[38+i]=s->total[i];
   dst[43]=s->shots[who];dst[44]=s->ammo[who];dst[45]=s->warm[who];dst[46]=s->next[who];dst[47]=s->reload[who];
  }
 }
 if(s->squad_mode)status[id]|=flush_lands(c,e,ne,s,env,script[(steps-1)*8],full);
 status[id]|=s->random_error|s->counter_error;
 for(int i=0;i<5;i++)totals[id*5+i]=s->total[i];
}
