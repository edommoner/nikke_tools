"""Archive v31, then port ordered boss buffs and deferred enemy dispel."""
import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_boss.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py','scripts/build-combat.py','scripts/build-detail-native.py','scripts/verify-normal-detail.py','research/detail-normal-acceptance.json','research/detail-boss-clock-checkpoint.json','research/detail-all-effects-audit.json','web/app.js','web/index.html']
for f in files:
 p=ROOT/'research/ports/v31'/f;assert not p.exists(),p;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f,p)
def edit(f,old,new):
 p=ROOT/f;s=p.read_text(encoding='utf-8');assert old in s,(f,old);p.write_text(s.replace(old,new),encoding='utf-8')
for f in ['app/detail_gpu.py','scripts/build-combat.py','scripts/build-detail-native.py']:
 edit(f,'detail_boss_clock_v31','detail_boss_buffs_v32')
edit('app/detail_gpu.py','detail_state_bytes_v31','detail_state_bytes_v32')
edit('app/detail_gpu.py','detail_boss_shape_v31','detail_boss_shape_v32')
edit('app/detail_boss.py',"'move':4}","'move':4,'buff':5}")
edit('app/detail_boss.py','def compile_world(enemy,parts,body,program):','''def boss_effects(enemy,owner):
    """Immutable inactive definitions; GPU lifecycle activates/releases them."""
    effects=[];indices={}
    for p in validate_patterns(enemy.get('patterns',[])):
        if p.enemy_effect is not None:
            e={k:v for k,v in p.enemy_effect.items() if not k.startswith('_')}
            e.update(source='스킬1',target='target',trigger={'timing':['inactive'],'condition':[]})
            indices[p.id]=len(effects);effects.append((e,owner))
    return effects,indices

def compile_world(enemy,parts,body,program):''')
edit('app/detail_boss.py',"        q=[0.0]*BW;q[:12]", "        q=[0.0]*BW;q[76:80]=[p.def_mult,p.def_add,program.get('boss_effect_rows',{}).get(p.id,-1),int(p.irremovable)];q[:12]")
edit('app/detail_boss.py','integer(q[0],1,4)','integer(q[0],1,5)')
edit('app/detail_boss.py',"        for k in range(int(q[4])):","        if q[76]<0 or not integer(q[78],-1,NE-1) or not integer(q[79],0,1):raise ValueError('Invalid boss buff overlay')\n        for k in range(int(q[4])):")
edit('app/detail_gpu.py','WEAPONS,compile_world','WEAPONS,boss_effects,compile_world')
edit('app/detail_gpu.py',"   elif kind=='instant' and stat=='debuff_cleanse':q[1]=26", "   elif kind=='instant' and stat=='debuff_cleanse':q[1]=26\n   elif kind=='instant' and stat=='enemy_buff_cleanse':q[1]=28")
edit('app/detail_gpu.py',' program=compile_effects(chars,bm._effects)',""" extra,boss_indices=boss_effects(enemy,names[0])
 effects=list(bm._effects)+extra
 program=compile_effects(chars,effects)
 program['boss_effect_rows']={pid:program['source_rows'][len(bm._effects)+i][0] for pid,i in boss_indices.items()}""")
edit('app/detail_gpu.py',"event='start' if r[2]==0 else 'end'", "event='start' if r[2]==0 else 'dispel' if r[2]==5 else 'end'")
edit('app/detail_gpu.py',"opens=[int(v) for v in r[5:5+len(patterns)]])", "opens=[int(v) for v in r[5:5+len(patterns)]],defense=r[37],dispelled_mask=int(r[38]),enemy_received=r[39])")
edit('app/engine_worker.py',"e.event in ('start','end')", "e.event in ('start','end','dispel')")
edit('app/detail_effects.cu','detail_boss_clock_v31','detail_boss_buffs_v32')
edit('app/detail_effects.cu','detail_state_bytes_v31','detail_state_bytes_v32')
edit('app/detail_effects.cu','detail_boss_shape_v31','detail_boss_shape_v32')
edit('app/detail_effects.cu',' const double* boss_program;double world', ' unsigned int boss_release,boss_apply;int boss_dispelled[BP];double boss_base_def;\n const double* boss_program;double world')
edit('app/detail_effects.cu','__device__ __noinline__ int notify(const double*,', '__device__ int boss_dispel(State*,double,int);\n__device__ __noinline__ int notify(const double*,')
edit('app/detail_effects.cu','  if(kind==26){','  if(kind==28){if(mask&32){int limit=q[6]==0?1:q[6]<=0?0:q[6]>=BP?BP:(int)q[6];int code=boss_dispel(s,t,limit);if(code)return code;}continue;}\n  if(kind==26){')
edit('app/detail_effects.cu',' if(outcome!=4)code|=boss_emit', ' if(outcome!=4)code|=boss_emit') if False else None
edit('app/detail_effects.cu',' int code=boss_log(s,t,i,outcome);if(outcome!=4)', ' if(outcome!=4)s->boss_release|=1u<<i;\n int code=boss_log(s,t,i,outcome);if(outcome!=4)')
edit('app/detail_effects.cu',' if(!s->boss_count)return 0;int due[BP];', ' if(!s->boss_count)return 0;for(int i=0;i<s->boss_count;i++)if(s->boss_dispelled[i]==1){s->boss_dispelled[i]=2;s->boss_release|=1u<<i;}\n int due[BP];')
edit('app/detail_effects.cu','s->boss_start[i]=t;s->boss_opens[i]++;','s->boss_start[i]=t;s->boss_opens[i]++;s->boss_dispelled[i]=0;s->boss_apply|=1u<<i;')
edit('app/detail_effects.cu',' double core=s->boss_base_core,distance=', ' double defense=s->boss_base_def;int order[BP],n=0;for(int i=0;i<s->boss_count;i++)if(s->boss_active[i]){int at=n++;while(at>0&&(s->boss_start[order[at-1]]>s->boss_start[i]||s->boss_start[order[at-1]]==s->boss_start[i]&&order[at-1]>i)){order[at]=order[at-1];at--;}order[at]=i;}\n for(int k=0;k<n;k++){int i=order[k];const double* p=boss_pattern(s,i);if(p[0]==5&&!s->boss_dispelled[i])defense=defense*p[76]+p[77];}\n double core=s->boss_base_core,distance=')
edit('app/detail_effects.cu',' if(core!=s->world[1]||distance!=', ' if(defense!=s->world[0]||core!=s->world[1]||distance!=')
edit('app/detail_effects.cu',' s->world[1]=core;s->boss_distance=', ' s->world[0]=defense;s->world[1]=core;s->boss_distance=')
edit('app/detail_effects.cu',' s->boss_program=w;s->boss_count=', ' s->boss_release=s->boss_apply=0;s->boss_base_def=s->world[0];for(int i=0;i<BP;i++)s->boss_dispelled[i]=0;\n s->boss_program=w;s->boss_count=')
needle='__device__ int boss_init(State* s,const double* w){'
helpers='''__device__ int boss_dispel(State* s,double t,int limit){
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
'''
edit('app/detail_effects.cu',needle,helpers+needle)
edit('app/detail_effects.cu','int code=boss_frame(s,t);if(code)return code;int part_events=', 'int code=boss_frame(s,t);if(code)return code;code|=boss_effect_state(e,ne,s,t);if(code)return code;int part_events=')
edit('app/detail_effects.cu','status[id]=boss_init(s,worlds+id*WP);','status[id]=boss_init(s,worlds+id*WP);status[id]|=boss_effect_state(e,ne,s,0);')
edit('app/detail_effects.cu','dst[4]=mask;continue;}','dst[4]=mask;dst[37]=env[0];unsigned int dispelled=0;for(int k=0;k<s->boss_count;k++)if(s->boss_dispelled[k])dispelled|=1u<<k;dst[38]=dispelled;dst[39]=stat(c,e,ne,s,0,12,full);continue;}')
p=ROOT/'research/detail-expansion-next.json';r=json.loads(p.read_text(encoding='utf-8'));r['current_work']={'abi':'detail_boss_buffs_v32','status':'implementation_in_progress','feature':'Ordered boss defense/received damage buffs and deferred enemy cleanse','objective_complete':False};p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Archived v31; assembled v32')
