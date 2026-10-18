from pathlib import Path
p=Path(__file__).resolve().parents[1]/'app/detail_effects.cu';s=p.read_text(encoding='utf-8')
schedule='s->incoming_queued=0;for(int i=0;i<s->boss_count;i++){const double* p=boss_pattern(s,i);if(p[0]!=6)continue;while(s->boss_active[i]&&s->incoming_shots[i]<p[87]&&t>=s->boss_start[i]+s->incoming_shots[i]*p[88]-1e-9){if(s->incoming_queued>=BQ)return 512;s->incoming_queue[s->incoming_queued++]=i;s->incoming_shots[i]++;}}'
assert s.count(schedule)==1;s=s.replace(schedule+'\n ','')
needle='__device__ int incoming_attacks(const double* c,const double* e,int ne,State* s,const double* env,double t,int full){\n int code=0;'
assert needle in s;s=s.replace(needle,needle+'\n '+schedule)
p.write_text(s,encoding='utf-8')
