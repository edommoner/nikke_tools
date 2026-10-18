"""One-shot integration; final source remains the build provenance authority."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def edit(name,changes):
    p=ROOT/name;t=p.read_text(encoding='utf-8')
    for old,new in changes:
        assert old in t,(name,old);t=t.replace(old,new)
    p.write_text(t,encoding='utf-8')
extra=(ROOT/'research/boss-clock-functions.txt').read_text(encoding='utf-8')
edit('app/detail_effects.cu',[
 ('#define EN 68','#define EN 68\n#define BP 32\n#define BL 8\n#define BW 80\n#define BH 512\n#define BLOG 1024\n#define BQ 1024\n#define WB (8+NE)\n#define WP (WB+BP*BW)'),
 ('struct State {','struct State {\n const double* boss_program;double world[EN],boss_base_core,boss_distance,boss_start[BP],boss_end_at[BP+1][BH],boss_log_at[BLOG];\n int boss_count,boss_weapon_mask,boss_active[BP],boss_opens[BP],boss_after[BP][BL],boss_until[BP][BL],boss_end_n[BP+1],boss_end_kind[BP+1][BH],boss_log_n,boss_log_node[BLOG],boss_log_kind[BLOG],boss_event_n,boss_event_code[BQ],boss_event_arg[BQ];'),
 ('detail_named_capacity_v30','detail_boss_clock_v31'),('detail_state_bytes_v30','detail_state_bytes_v31'),
 ('if(a[167]<2)return (mode?mode[30]:a[14])>.5;\n double lo=mode?mode[264]:a[164],hi=mode?mode[265]:a[165],d=a[166];',
  'if(s->boss_count&&s->boss_distance<0){int kind=(int)s->boss_program[mode?8+s->mode[who]:3+who];return (s->boss_weapon_mask&(1<<kind))!=0;}\n if(!s->boss_count&&a[167]<2)return (mode?mode[30]:a[14])>.5;\n double lo=mode?mode[264]:a[164],hi=mode?mode[265]:a[165],d=s->boss_count?s->boss_distance:a[166];'),
 ('if(type==28&&!hit_crit)return 0;','if(type==35&&s->world[1]<1)return 0;\n  if(type==28&&!hit_crit)return 0;'),
 ('__device__ int squad_frame(',extra+'__device__ int squad_frame('),
 ('int part_events=parts_refresh(env,s);int code=tick_effects(c,e,ne,s,env,t,*full);code|=parts_events(c,e,ne,s,env,t,*full,part_events);',
  'int code=boss_frame(s,t);if(code)return code;int part_events=parts_refresh(env,s);code|=tick_effects(c,e,ne,s,env,t,*full);code|=parts_events(c,e,ne,s,env,t,*full,part_events);code|=boss_events(c,e,ne,s,env,t,*full);'),
 ('const double* enemy,const double* script,const unsigned int* initial_rng','const double* enemy,const double* worlds,const double* script,const unsigned int* initial_rng'),
 ('const double* env=enemy+id*EN;int ne=counts[id];','const double* original_env=enemy+id*EN;int ne=counts[id];'),
 ('State* s=workspace+id;s->last_shield_result=0;','State* s=workspace+id;double* env=s->world;for(int k=0;k<EN;k++)env[k]=original_env[k];s->last_shield_result=0;'),
 ('status[id]=0;\n for(int step=0;step<steps;step++){','status[id]=boss_init(s,worlds+id*WP);\n for(int step=0;step<steps;step++){\n  if(status[id])break;'),
 ('if(op==5)status[id]|=flush_lands(c,e,ne,s,env,t,full);','if(op==5){status[id]|=flush_lands(c,e,ne,s,env,t,full);status[id]|=boss_finish(s,t);}'),
 ('if(ev==114){', 'if(ev==115){for(int k=0;k<OW;k++)dst[k]=0;dst[3]=s->boss_log_n;if(arg<s->boss_log_n){dst[0]=s->boss_log_at[arg];dst[1]=s->boss_log_node[arg];dst[2]=s->boss_log_kind[arg];}continue;}\n   if(ev==116){for(int k=0;k<OW;k++)dst[k]=0;dst[0]=env[1];dst[1]=s->boss_distance;dst[2]=s->boss_weapon_mask;dst[3]=s->boss_log_n;unsigned int mask=0;for(int k=0;k<s->boss_count;k++){dst[5+k]=s->boss_opens[k];if(s->boss_active[k])mask|=1u<<k;}dst[4]=mask;continue;}\n   if(ev==114){'),
])
edit('server.mjs',[(".update(readFileSync(path.join(root, 'app/detail_gpu.py')))",".update(readFileSync(path.join(root, 'app/detail_gpu.py'))).update(readFileSync(path.join(root, 'app/detail_world.py'))).update(readFileSync(path.join(root, 'app/detail_boss.py')))")])
print('GPU boss-clock source assembled')
