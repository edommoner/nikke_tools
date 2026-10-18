from pathlib import Path
p=Path(__file__).resolve().parents[1]/'app/detail_effects.cu'
s=p.read_text(encoding='utf-8')
changes={
'timer_active[NE],timer_seq[NE],entry_seq[NS],timer_clock,entry_clock':'timer_active[NE],entry_seq[NS],entry_clock',
'int instant_next[NE],instant_head,instant_tail;':'int timer_next[NE],timer_head[2],timer_tail[2];',
's->timer_seq[j]=s->entry_seq[j]=0;':'s->entry_seq[j]=0;',
's->timer_clock=s->entry_clock=0':'s->entry_clock=0',
's->instant_next[j]=-2;':'s->timer_next[j]=-2;',
's->instant_head=s->instant_tail=-1;':'for(int family=0;family<2;family++)s->timer_head[family]=s->timer_tail[family]=-1;',
'if(!was){s->timer_seq[j]=++s->timer_clock;if(kind!=3){int code=index_instant_timer(s,j);if(code)return code;}}':'if(!was){int code=index_timer(s,j,kind==3?0:1);if(code)return code;}',
}
for old,new in changes.items():
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
start=s.index('__device__ int index_instant_timer(');end=s.index('// Capture once before children',start)
s=s[:start]+'''__device__ int index_timer(State* s,int row,int family){
 if(row==s->timer_tail[family])return 0;
 if(s->timer_next[row]!=-2){
  int before=-1,at=s->timer_head[family],steps=0;
  while(at>=0&&at!=row&&steps++<NE){before=at;at=s->timer_next[at];}
  if(at!=row)return 8;
  if(before<0)s->timer_head[family]=s->timer_next[row];else s->timer_next[before]=s->timer_next[row];
 }
 if(s->timer_tail[family]<0)s->timer_head[family]=row;else s->timer_next[s->timer_tail[family]]=row;
 s->timer_next[row]=-1;s->timer_tail[family]=row;return 0;
}
struct TimerSnapshot {int count,row[NE],epoch[NE];};
// Registration order is maintained once. Both families snapshot through the
// same index; unrelated definitions and repeated minimum selection are absent.
__device__ void capture_timers(const double* e,State* s,int ne,int damage,TimerSnapshot* out){
 out->count=0;int family=damage?0:1;
 for(int j=s->timer_head[family];j>=0;j=s->timer_next[j])if(s->timer_active[j]){
  int at=out->count++;out->row[at]=j;out->epoch[at]=s->timer_epoch[j];
 }
}
__device__ int timer_owned(State* s,int row,int epoch){return s->timer_active[row]&&s->timer_epoch[row]==epoch;}
__device__ void advance_timer(State* s,int row,int epoch,double interval){if(timer_owned(s,row,epoch))s->timer_at[row]+=interval;}
''' +s[end:]
assert 'instant_next' not in s and 'timer_seq' not in s and 'timer_clock' not in s
p.write_text(s,encoding='utf-8')
