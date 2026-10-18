"""One-off checked migration of the common GPU landing boundary."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from impact_specs import BEGIN,END,render_cuda
p=ROOT/'app/detail_effects.cu';source=p.read_text(encoding='utf-8')
def replace(old,new,n=1):
    global source
    assert source.count(old)==n,(old[:100],source.count(old),n)
    source=source.replace(old,new)
replace('#define RC 1024',BEGIN+render_cuda()+END+'\n#define RC 1024')
replace('struct State {','struct State {\n int impact_enabled;double impact_summary[OW];\n int land_family[1024];')
replace('detail_resource_limits_v52','detail_typed_impacts_v53')
replace('s->land_owner[k]=owner;s->land_damage[k]=sequence->hit;',
        's->land_owner[k]=owner;s->land_family[k]=(int(q[39])&128)?HIT_DOT:HIT_SKILL;s->land_damage[k]=sequence->hit;')
replace('s->land_owner[k]=owner;s->land_damage[k]=hit;',
        's->land_owner[k]=owner;s->land_family[k]=(int(q[39])&128)?HIT_DOT:HIT_SKILL;s->land_damage[k]=hit;',2)
old='''__device__ int land_damage(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,int who,double hit){
 int code=heal_landed(c,e,ne,s,env,t,full,who,hit);
 return code|collect_damage_accum(c,e,ne,s,env,t,full,who,hit);
}'''
new='''// One typed boundary for every supported body/part landing. Credit is not
// weighted by non-core probability, damage, pellets-per-ammo or resource spend.
__device__ void record_impact(State* s,const Impact& p,double t){
 if(!s->impact_enabled)return;
 double* r=s->impact_summary;r[0]++;r[1+p.kind*4+p.family]++;r[25]+=p.credit;r[26]+=p.damage;r[40+p.outcome]++;
 r[27]=p.kind;r[28]=p.identity;r[29]=p.generation;r[30]=p.family;r[31]=p.outcome;r[32]=p.attacker;
 r[33]=p.damage;r[34]=p.credit;r[35]=p.attack_id;r[36]=t;
}
__device__ int land_impact(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,const Impact& p){
 record_impact(s,p,t);
 if(p.outcome!=OUTCOME_DAMAGING)return 0;
 int code=heal_landed(c,e,ne,s,env,t,full,p.attacker,p.damage);
 return code|collect_damage_accum(c,e,ne,s,env,t,full,p.attacker,p.damage);
}
__device__ int land_damage(const double* c,const double* e,int ne,State* s,const double* env,double t,int full,int who,double hit,int family=HIT_WEAPON,int kind=ACTOR_BODY,int identity=0){
 Impact p={who,kind,identity,1,family,OUTCOME_DAMAGING,0,hit,1};
 return land_impact(c,e,ne,s,env,t,full,p);
}'''
replace(old,new)
replace('double hit,int aimed=-1){','double hit,int aimed=-1,int family=HIT_WEAPON){')
replace('code|=land_damage(c,e,ne,s,env,t,full,who,hit);}return code;',
        'code|=land_damage(c,e,ne,s,env,t,full,who,hit,family,ACTOR_PART,p);}return code;')
replace('s->land_damage[k]);code|=parts_land(c,e,ne,s,env,t,full,who,s->land_reach[k],s->land_part[k]);',
        's->land_damage[k],s->land_family[k]);code|=parts_land(c,e,ne,s,env,t,full,who,s->land_reach[k],s->land_part[k],-1,s->land_family[k]);')
replace('s->now_damage[k]);code|=parts_land(c,e,ne,s,env,t,1,who,s->now_reach[k],s->now_part[k]);',
        's->now_damage[k],HIT_SKILL);code|=parts_land(c,e,ne,s,env,t,1,who,s->now_reach[k],s->now_part[k],-1,HIT_SKILL);')
replace('s->land_damage[k]);code|=parts_land(c,e,ne,s,env,t,1,who,s->land_reach[k],s->land_part[k]);',
        's->land_damage[k],s->land_family[k]);code|=parts_land(c,e,ne,s,env,t,1,who,s->land_reach[k],s->land_part[k],-1,s->land_family[k]);')
replace('s->land_owner[dst]=s->land_owner[src];','s->land_owner[dst]=s->land_owner[src];s->land_family[dst]=s->land_family[src];')
replace('s->hp_log_enabled=s->hp_log_count=0;',
        's->impact_enabled=0;for(int k=0;k<OW;k++)s->impact_summary[k]=0;s->impact_summary[27]=s->impact_summary[28]=-1;for(int j=0;j<steps;j++)if(script[j*8+1]==2&&script[j*8+2]==126)s->impact_enabled=1;\n s->hp_log_enabled=s->hp_log_count=0;')
replace('land_damage(c,e,ne,s,env,t,full,who,cmd[6])','land_damage(c,e,ne,s,env,t,full,who,cmd[6],HIT_EXTERNAL)')
replace('parts_land(c,e,ne,s,env,t,full,who,arg,cmd[6],(int)cmd[7])',
        'parts_land(c,e,ne,s,env,t,full,who,arg,cmd[6],(int)cmd[7],HIT_EXTERNAL)')
replace('  if(op==2){\n   double* dst=',
        '  if(op==8){Impact p={who,arg%8,arg/8,(int)cmd[5],ev%4,(ev/4)%4,ev/16,cmd[6],cmd[7]};record_impact(s,p,t);}\n  if(op==2){\n   double* dst=')
replace('   if(ev==112){','   if(ev==126){for(int k=0;k<OW;k++)dst[k]=s->impact_summary[k];continue;}\n   if(ev==112){')
p.write_text(source,encoding='utf-8')
