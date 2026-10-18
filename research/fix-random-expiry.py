from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'app/detail_effects.cu';s=p.read_text(encoding='utf-8')
start=s.index('  if(q[4]==19){\n   for(int k=0;k<s->random_cache_count;')
end=s.index('else for(int k=s->slot_head;',start)
old=s[start:end]
helper='''__device__ int cached_random_target(const double* e,State* s,const double* q,double activated,Order* ordered){
 for(int k=0;k<s->random_cache_count;k++)if(s->random_owner[k]==(int)q[0]&&s->random_key[k]==(int)q[257]&&s->random_time[k]==activated){*ordered=s->random_order[k];return s->random_mask[k];}
 if(s->random_cache_count>=RC){s->random_error=32;*ordered=0;return 0;}
 int k=s->random_cache_count++;s->random_owner[k]=(int)q[0];s->random_key[k]=(int)q[257];s->random_time[k]=activated;
 int mask=random_target(e,s,q,ordered);s->random_mask[k]=mask;s->random_order[k]=*ordered;return mask;
}
'''
s=s[:start]+'  if(q[4]==19)found=cached_random_target(e,s,q,s->activated[j],&s->target_order[j]);'+s[end:]
pos=s.index('__device__ int ranked_target(');s=s[:pos]+helper+s[pos:]
a='''  int j=removed[step],mask=masks[step];
  if(effect(e,s,j)[35]>0)code|=notify(c,e,ne,s,env,t,29,(int)effect(e,s,j)[0],(int)effect(e,s,j)[3],full);'''
b='''  int j=removed[step],mask=masks[step];const double* expired=effect(e,s,j);double activated=s->activated[j];
  if(expired[35]>0){
   code|=notify(c,e,ne,s,env,t,29,(int)expired[0],(int)expired[3],full);
   // Verbose CPU logs resolve an unread expired carrier after end callbacks.
   // Resolve its old key without overwriting a newly activated slot.
   if(mask<0&&expired[4]==19){Order discarded=0;mask=cached_random_target(e,s,expired,activated,&discarded);}
  }'''
assert a in s;s=s.replace(a,b)
a='''  code|=log_burst(s,t,4,-1);
 }'''
b='''  code|=log_burst(s,t,4,-1);
  // Match the CPU verbose snapshot's raw resolution once per squad recipient.
  // This intentionally does not resolve/cache the active carrier itself.
  for(int who=0;who<5;who++)for(int j=s->slot_head;j>=0;j=s->slot_next[j])if(s->alive[j]&&s->masks[j]<0&&effect(e,s,j)[4]==19)random_target(e,s,effect(e,s,j));
 }'''
assert a in s;s=s.replace(a,b)
p.write_text(s,encoding='utf-8');print('Expiration logging and full-burst snapshot RNG consumption ported.')
