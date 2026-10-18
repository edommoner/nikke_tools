"""Port seeded target selection; preserve the verified v19 source snapshot."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
archive=ROOT/'research/ports/v19';archive.mkdir(exist_ok=True)
paths=['app/detail_gpu.py','app/detail_effects.cu','app/engine_worker.py','scripts/build-combat.py','scripts/build-detail-native.py']
for name in paths:
 dst=archive/Path(name).name
 if not dst.exists():shutil.copyfile(ROOT/name,dst)
def edit(name,fn):
 p=ROOT/name;s=p.read_text(encoding='utf-8');p.write_text(fn(s),encoding='utf-8')
def replace(s,a,b):
 assert a in s,a[:100]
 return s.replace(a,b)
def host(s):
 s=replace(s,'NE,EW,CW,OW=128,256,168,48','NE,EW,CW,OW=128,264,168,48')
 s=s.replace('detail_cleanse_v19','detail_random_v20').replace('detail_state_bytes_v19','detail_state_bytes_v20')
 s=replace(s,'target_plans=[]','target_plans=[];target_keys={}')
 s=replace(s,"  c=chars[owner]\n  if isinstance(target,list):", "  c=chars[owner]\n  q[256]=int(isinstance(target,str))\n  if isinstance(target,str):\n   if target not in target_keys:target_keys[target]=len(target_keys)\n   q[257]=target_keys[target]\n  if isinstance(target,list):")
 s=replace(s,"  elif target=='self':q[4]=0", "  elif isinstance(target,str) and re.fullmatch(r'allies_random(?:_with_debuff)?:[0-5]',target):\n   q[4]=20 if '_with_debuff' in target else 19;q[5]=int(target.split(':')[1])\n  elif target=='self':q[4]=0")
 s=replace(s,'else int(row[48]).bit_count()', 'else min(count,4 if kind==19 else 5) if kind in (19,20) else int(row[48]).bit_count()')
 s=replace(s,"   allowed={'source'", "   q[258]={'buff':0,'instant':1,'damage':2,'weapon_change':3}.get(kind,-1)\n   allowed={'source'")
 s=replace(s,"module_backend='auto'):\n if not programs", "module_backend='auto',seeds=None):\n import random\n seeds=[0]*len(programs) if seeds is None else list(seeds)\n if len(seeds)!=len(programs) or any(type(seed) is not int or not 0<=seed<=4294967295 for seed in seeds):raise ValueError('Detailed GPU seed must be a uint32 integer')\n if not programs")
 s=replace(s,"array.array('d',(v for row in script for v in row))]", "array.array('d',(v for row in script for v in row)),array.array('I',(v for seed in seeds for v in random.Random(seed).getstate()[1]))]")
 s=replace(s,"if any(status):raise RuntimeError('GPU detail event or active-instance capacity exceeded; result rejected')", "if any(status):raise RuntimeError('GPU detail capacity or target cache exceeded; result rejected: '+str(list(status)))")
 s=replace(s,"script.append([duration,2,109,0,0,266,0,0])", "script.append([duration,2,109,0,0,266,0,0])\n if body.get('_debug_random_state'):\n  for page in range(14):script.append([duration,2,110,0,page,267+page,0,0])")
 s=replace(s,"module_backend=module_backend)\n totals=result", "module_backend=module_backend,seeds=[body.get('seed',0)])\n totals=result")
 s=replace(s," payload['burst_gauge_mode']=body.get('burst_gauge_mode','fixed')", " payload['seed']=body.get('seed',0)\n if body.get('_debug_random_state'):payload['_random_state']=[int(v) for page in logs[267:281] for v in page][:625]\n payload['burst_gauge_mode']=body.get('burst_gauge_mode','fixed')")
 return s
edit('app/detail_gpu.py',host)
for p in ('scripts/build-combat.py','scripts/build-detail-native.py'):edit(p,lambda s:s.replace('detail_cleanse_v19','detail_random_v20'))
def adapter(s):
 s=replace(s,"    req = {'squad': squad, 'sim': {'duration': duration, 'expected': True, 'burst_gauge_mode':gauge_mode}", "    seed=body.get('seed',0)\n    if type(seed) is not int or not 0<=seed<=4294967295:raise ValueError('乱数シードは0〜4294967295の整数です。')\n    req = {'squad': squad, 'sim': {'duration': duration, 'expected': True, 'seed':seed, 'burst_gauge_mode':gauge_mode}")
 return s
edit('app/engine_worker.py',adapter)
def cuda(s):
 s=s.replace('#define EW 256','#define EW 264').replace('detail_cleanse_v19','detail_random_v20').replace('detail_state_bytes_v19','detail_state_bytes_v20')
 primitive=(ROOT/'research/ports/detail_random.cu').read_text(encoding='utf-8')
 primitive=primitive[primitive.index('struct MTState'):primitive.index('extern "C" __global__')]
 s=replace(s,'struct State {',primitive+'\n#define RC 1024\nstruct State {\n MTState rng;int random_error,random_cache_count,random_owner[RC],random_key[RC],random_mask[RC];double random_time[RC];Order random_order[RC];')
 s=replace(s,'q[4]==15||q[4]==16;','q[4]==15||q[4]==16||q[4]==19;')
 # A draw produces both the mask and ordered sample exactly once.
 marker='__device__ int ranked_target('
 start=s.index(marker)
 s=s[:start]+'''__device__ int random_target(const double* e,State* s,const double* q,Order* ordered=0){
 int pool[5],n=0,mask=0;Order order=0;
 for(int who=0;who<5;who++){
  if(q[4]==19){if(who!=(int)q[0])pool[n++]=who;}
  else{int harmful=0;for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(s->alive[k]&&effect(e,s,k)[259]>0&&s->masks[k]>=0&&(s->masks[k]&(1<<who))){harmful=1;break;}if(harmful)pool[n++]=who;}
 }
 int count=(int)mn(q[5],n);
 for(int k=0;k<count;k++){int at=(int)mt_below(&s->rng,n-k),who=pool[at];pool[at]=pool[n-k-1];mask|=1<<who;order|=Order(who+1)<<(3*k);}
 if(ordered)*ordered=order;return mask;
}
''' +s[start:]
 s=replace(s,' int mask=0,owner=(int)q[0],kind=(int)q[4];Order order=0;', ' if(q[4]==19||q[4]==20)return random_target(e,s,q,ordered);\n int mask=0,owner=(int)q[0],kind=(int)q[4];Order order=0;')
 # kind20 must remain eager but use the common mask/order resolver.
 s=replace(s,' if(lazy_target(q))return -1;', ' if(lazy_target(q)||kind==20)return -1;')
 s=replace(s,'if(bits<0)bits=ranked_target(c,e,ne,s,node,full,&child);','if(bits<0)bits=ranked_target(c,e,ne,s,node,full,&child);')
 a='__device__ int target(const double* c,const double* e,int ne,const double* q,int n,State* s,int full){return q[4]==17?list_target(c,e,ne,s,q,full,0):target_basic(e,q,n,s);}'
 b='''__device__ int target(const double* c,const double* e,int ne,const double* q,int n,State* s,int full,Order* ordered=0,int eager=0){
 if(q[4]==17)return list_target(c,e,ne,s,q,full,ordered);
 int mask=target_basic(e,q,n,s);
 if(mask<0&&(eager||q[4]==20))return ranked_target(c,e,ne,s,q,full,ordered);
 if(ordered)*ordered=mask<0?0:recipient_order(c,e,ne,s,q,mask,full);return mask;
}'''
 s=replace(s,a,b)
 # Persistent lazy cache, including dead original carriers and empty samples.
 a='''  for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(k!=j&&s->masks[k]>=0&&s->activated[k]==s->activated[j]&&effect(e,s,k)[0]==q[0]&&effect(e,s,k)[4]==q[4]&&effect(e,s,k)[5]==q[5]&&effect(e,s,k)[48]==q[48]&&effect(e,s,k)[49]==q[49]){found=s->masks[k];s->target_order[j]=s->target_order[k];break;}
  s->masks[j]=found>=0?found:ranked_target(c,e,ne,s,q,full,&s->target_order[j]);'''
 b='''  if(q[4]==19){
   for(int k=0;k<s->random_cache_count;k++)if(s->random_owner[k]==(int)q[0]&&s->random_key[k]==(int)q[257]&&s->random_time[k]==s->activated[j]){found=s->random_mask[k];s->target_order[j]=s->random_order[k];break;}
   if(found<0){if(s->random_cache_count>=RC){s->random_error=32;return;}int k=s->random_cache_count++;s->random_owner[k]=(int)q[0];s->random_key[k]=(int)q[257];s->random_time[k]=s->activated[j];found=random_target(e,s,q,&s->target_order[j]);s->random_mask[k]=found;s->random_order[k]=s->target_order[j];}
  }else for(int k=s->slot_head;k>=0;k=s->slot_next[k])if(k!=j&&s->masks[k]>=0&&s->activated[k]==s->activated[j]&&effect(e,s,k)[0]==q[0]&&effect(e,s,k)[4]==q[4]&&effect(e,s,k)[5]==q[5]&&effect(e,s,k)[48]==q[48]&&effect(e,s,k)[49]==q[49]){found=s->masks[k];s->target_order[j]=s->target_order[k];break;}
  s->masks[j]=found>=0?found:ranked_target(c,e,ne,s,q,full,&s->target_order[j]);'''
 s=replace(s,a,b)
 a='''  int mask=target(c,e,ne,q,5,s,full),kind=(int)q[1];if(mask<0&&kind!=0&&kind!=4)mask=ranked_target(c,e,ne,s,q,full);if(!mask&&q[57]>=0)continue;
  int budget=(int)q[58];if(event!=28||q[69]>0){if(q[57]>=0&&s->activations[budget]>=q[57])continue;s->activations[budget]++;}'''
 b='''  int kind=(int)q[1],budget=(int)q[58];Order activation_order=0;
  if(event!=28||q[69]>0){
   if(q[57]>=0&&s->activations[budget]>=q[57])continue;
   if(q[57]>=0&&q[256]>0&&!lazy_target(q)&&!target(c,e,ne,q,5,s,full,0,1))continue;
   s->activations[budget]++;
  }
  // Periodic instants resolve on ticks, direct damage and weapon changes do
  // not resolve recipients. Their optional budget probe above is independent.
  int mask=0,registration=q[59]>0&&event!=28;
  if(!(q[258]==1&&registration)&&kind!=2&&!(kind==3&&!registration))mask=target(c,e,ne,q,5,s,full,&activation_order,q[258]==1||kind==19);'''
 s=replace(s,a,b)
 # Capture a single activation result for all synchronous downstream handlers.
 s=s.replace('recipient_order(c,e,ne,s,q,mask,full);recipients','activation_order;recipients')
 s=s.replace('queue[depth]=recipient_order(c,e,ne,s,q,mask,full);','queue[depth]=activation_order;')
 s=replace(s,'Order raworder=mask>=0?recipient_order(c,e,ne,s,q,mask,full):0;', 'Order raworder=activation_order;')
 s=replace(s,'int targets=target(c,e,ne,source,5,s,full);','Order source_order=0;int targets=target(c,e,ne,source,5,s,full,&source_order);')
 s=replace(s,'targets<0?0:recipient_order(c,e,ne,s,source,targets,full)','source_order')
 # Shared explicit MT input is data initialization, not a CPU oracle trace.
 s=replace(s,'const double* script,int steps,','const double* script,const unsigned int* initial_rng,int steps,')
 s=replace(s,'State* s=workspace+id;s->compensated_sums', 'State* s=workspace+id;s->random_error=0;s->random_cache_count=0;for(int k=0;k<624;k++)s->rng.words[k]=initial_rng[id*625+k];s->rng.index=(int)initial_rng[id*625+624];s->compensated_sums')
 s=replace(s,'   if(ev==106){','   if(ev==110){for(int k=0;k<OW;k++){int word=arg*OW+k;dst[k]=word<624?s->rng.words[word]:word==624?s->rng.index:0;}continue;}\n   if(ev==106){')
 s=replace(s,' for(int i=0;i<5;i++)totals[id*5+i]', ' status[id]|=s->random_error;\n for(int i=0;i<5;i++)totals[id*5+i]')
 return s
edit('app/detail_effects.cu',cuda)
edit('app/detail_gpu.py',lambda s:replace(s,"   q[258]={'buff'", "   q[259]=int(str(eff.get('polarity','')).startswith('harmful'))\n   q[258]={'buff'"))
edit('README.md',lambda s:replace(s,'v19の全回帰テスト114件は実行中です。','v19の全回帰テスト114件が通過しました。検証範囲とハッシュは `research/detail-cleanse-checkpoint.json` に保存しています。'))
print('Seeded target integration sources prepared; builds and battle parity pending.')
