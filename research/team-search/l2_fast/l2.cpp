#include <atomic>
#include "l2.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <vector>
using std::vector;
namespace {
struct Sum { double s=0,c=0;bool compensated; explicit Sum(bool b):compensated(b){} void add(double x){double t=s+x;if(compensated){if(std::abs(s)>=std::abs(x))c+=(s-t)+x;else c+=(x-t)+s;}s=t;} double value()const{return c && std::isfinite(c)?s+c:s;} };
struct Rule{int op,a,b,limit;};
struct Buff{int phase;bool burst;bool needs_shield=false;unsigned char prerequisite=0;int condition=0;bool own_observed=false,has_caps=false,can_supply=true,correctable=false,phase_scaled=false,capped=false;vector<std::pair<int,double>> amounts;vector<double> caps;vector<size_t> rank_amounts;vector<Rule> rules,dynamic_rules;vector<unsigned char> candidates;bool all_candidates=false;};
struct Group{int phase;uint32_t flags;double unit,coeff,atk,def,core,corebonus,charge,action_rate=1,context_unit=0;bool cast_scaled=false,cast_scaled_s22=false,action_eligible=true;vector<double> own;std::array<double,7> base,self;int offset=0,merge_class=0;bool use_cast=false,use_action=false;double selected_unit=0,action_divisor=1;std::array<unsigned char,9> bonus_keys{};unsigned char bonus_count=0;vector<int> read_keys;uint64_t read_mask=0,bucket_reads[7]={};std::array<double,7> idle_f{};double idle_product=1,idle_action=1;};
struct Dep{bool enabled,team;double ratio;};
struct Mechanic{int kind,event,condition,threshold;double value;int scope,limit;};
struct ActiveMechanic{const Mechanic* rule;int source,used;};
struct Char{bool shield_provider=false,stage_uncertain=false;int stage,b3,b1=0,squad,has_squad,weapon,klass,code;double cd,charge,casts,seconds[2],phase_raw[2]={};double atk=0,hp=0,def=0,rank_pct=0,rank_flat=0,rate=1,charge_base=0,delay=0,clips=1,ammo=1,reload=0,mincycle=0;bool charged=false;int cycle_conditions=0;uint32_t cycle_classes[4]={};vector<Mechanic> mechanics;vector<size_t> stage_rules,extension_rules,event_rules[7];vector<Group> groups;vector<Buff> buffs;vector<size_t> rank_buffs;vector<Dep> deps;};
struct Table{int keys;double duration;bool compensated;int switches=0,v3=0,v4=0;int action_keys[7];size_t max_mechanics=0;vector<Char> chars;};
// One bounded workspace per native thread / standalone WASM instance.
// Capacity is prepared once per batch or enumeration, never per squad.
struct CycleResult{uint32_t key[5]={};int casts[5]={};double fb=0;bool valid=false;};
struct Scratch {
    std::array<CycleResult,2048> cycles;
    vector<double> emission,own;
    vector<unsigned char> touched;
    vector<ActiveMechanic> active;
    void prepare(const Table&t){
        emission.resize(10*t.keys);touched.resize(10*t.keys);own.resize(t.keys);
        active.resize(5*t.max_mechanics);
        for(auto&x:cycles)x.valid=false;
    }
    void clear(){std::fill(emission.begin(),emission.end(),0.);std::fill(touched.begin(),touched.end(),0);}
};
Scratch& scratch_for(const Table&t){
#ifdef __EMSCRIPTEN__
    static Scratch scratch;
#else
    static thread_local Scratch scratch;
#endif
    scratch.prepare(t);return scratch;
}
struct Reader{const double* p;size_t n; double next(){if(!n--)throw std::runtime_error("short table");return *p++;}int integer(){double x=next();if(!std::isfinite(x)||x<std::numeric_limits<int>::min()||x>std::numeric_limits<int>::max()||x!=std::trunc(x))throw std::runtime_error("integer");return int(x);}int count(){int x=integer();if(x<0||x>1000000)throw std::runtime_error("count");return x;}};
int sliced(int count,int limit){return limit<0?std::max(0,count+limit):std::min(count,limit);}
unsigned targets(const Rule&r,int src,const Char* const* c,const uint32_t* ids,const double (*stats)[4]=nullptr){
    unsigned mask=0;int pool[5],n=0;const Char& s=*c[src];
    switch(r.op){
    case 0:return 0;case 1:return 31;case 2:return 1u<<src;case 3:return 31^(1u<<src);
    case 4:for(int i=0;i<5;i++)if(ids[i]==unsigned(r.a))mask|=1u<<i;return mask;
    case 18:case 19:case 20:case 21:case 22:case 23:case 24:case 25:{
        if(!stats)return 0;
        for(int i=0;i<5;i++)if(!((r.op==19||r.op==22)&&i==src)&&(r.op!=20||c[i]->weapon==r.a)&&(r.op!=25||stats[i][3]<stats[src][3]))pool[n++]=i;
        int key=(r.op==21||r.op==22)?1:(r.op==23?2:(r.op==24?3:0));
        if(r.op!=25)std::stable_sort(pool,pool+n,[&](int a,int b){return key==1?stats[a][key]<stats[b][key]:stats[a][key]>stats[b][key];});
        int limit=r.op==25?n:sliced(n,r.limit);for(int i=0;i<limit;i++)mask|=1u<<pool[i];return mask;
    }
    case 8:if(src)pool[n++]=src-1;if(src<4)pool[n++]=src+1;mask=1u<<src;break;
    case 9:{// Python slice [src+1:src+1+limit], including negative stop.
        int stop=src+1+r.limit;if(stop<0)stop=std::max(0,5+stop);stop=std::min(5,stop);
        for(int i=src+1;i<stop;i++)mask|=1u<<i;return mask;}
    default:
        for(int i=0;i<5;i++){
            const Char& d=*c[i];bool yes=false;
            switch(r.op){case 5:yes=d.b3;break;case 6:yes=i==src||(s.has_squad&&d.squad==s.squad);break;case 7:yes=true;break;
            case 10:case 11:yes=d.weapon==r.a&&(r.op!=11||i!=src);break;
            case 12:yes=d.klass==r.a;break;case 13:case 14:yes=d.code==r.a&&(r.op!=14||i!=src);break;
            case 15:case 16:yes=d.code==r.a&&d.weapon==r.b;break;case 17:yes=d.charge>0;break;}
            if(yes)pool[n++]=i;
        }
        if(r.op==17)std::stable_sort(pool,pool+n,[&](int a,int b){return c[a]->charge>c[b]->charge;});
    }
    int limit=(r.op==7||r.op==8||r.op==12||r.op==16||r.op==17)?sliced(n,r.limit):n;
    for(int i=0;i<limit;i++)mask|=1u<<pool[i];return mask;
}
// Static leaf unions contain no floating-point operations. Sliced, positional
// and ranked leaves retain the original ordered evaluator.
unsigned buff_targets(const Buff&b,int src,const Char*const*c,const uint32_t*ids,const double (*stats)[4]=nullptr){
    unsigned mask=b.all_candidates?31:0;
    if(!b.candidates.empty())for(int i=0;i<5;i++)if(b.candidates[ids[i]])mask|=1u<<i;
    for(const Rule&r:b.dynamic_rules)mask|=targets(r,src,c,ids,stats);
    return mask&~(1u<<src);
}
bool condition(int code,int src,const Char*const*c){
    if(!code)return true;bool other=false;
    for(int i=0;i<5;i++)if(i!=src&&c[i]->b1)other=true;
    if(code==1||code==2)return other==(code==2);
    for(int i=0;i<5;i++)if(i!=src&&c[src]->has_squad&&c[src]->squad==c[i]->squad)return true;return false;
}
bool prerequisite_ok(int code,int src,const Char*const*c){
    // Runtime stages may differ from nominal B1. An uncertain other member
    // prevents this new absence proof; keep the observed supply unchanged.
    if(code==1||code==2)for(int i=0;i<5;i++)if(i!=src&&c[i]->stage_uncertain)return true;
    return condition(code,src,c);
}
void dynamic_cycle(const Table&t,const Char*const*c,int*casts,double&fb,Scratch&scratch){
    double ready[5]={};int stages[5];bool reentry[5]={};
    for(int i=0;i<5;i++){
        stages[i]=c[i]->stage;
        for(size_t j:c[i]->stage_rules){const auto&r=c[i]->mechanics[j];if(condition(r.condition,i,c)){
            if(r.kind==1)stages[i]=1<<(int(r.value)-1);if(r.kind==2)reentry[i]=true;
        }}
    }
    int mask=0;for(int x:stages)mask|=x;if(mask!=7)return;
    // Filter immutable event lists once per squad. Within each event, records
    // retain source order and the original mechanic order, so ready[] updates
    // and trigger-limit counters have exactly the same sequence as before.
    size_t offsets[8],count_active=0;
    for(int event=0;event<7;event++){
        offsets[event]=count_active;
        for(int src=0;src<5;src++)for(size_t j:c[src]->event_rules[event]){
            const auto&r=c[src]->mechanics[j];
            if(condition(r.condition,src,c))scratch.active[count_active++]={&r,src,0};
        }
    }
    offsets[7]=count_active;
    auto emit=[&](int event,double when,int count,int caster=-1){
        for(size_t j=offsets[event];j<offsets[event+1];j++){
            auto&a=scratch.active[j];const auto&r=*a.rule;
            if(event==1&&a.source!=caster)continue;
            if(count>=r.threshold&&(!r.limit||a.used<r.limit)){
                a.used++;for(int dst=0;dst<5;dst++)if(r.scope||dst==a.source)ready[dst]=std::max(when,ready[dst]-r.value);
            }
        }
    };
    double time=3.;int cycles=0;emit(0,0.,1);
    for(int iter=0;iter<32;iter++){
        int chosen=-1;
        for(int stage=0;stage<3;stage++){
            for(int slot=0;slot<2;slot++){
                chosen=-1;double earliest=std::numeric_limits<double>::infinity();
                for(int i=0;i<5;i++)if(stages[i]&(1<<stage)){if(chosen<0&&ready[i]<=time+1e-9)chosen=i;earliest=std::min(earliest,ready[i]);}
                if(chosen<0){time=std::max(time,earliest);for(int i=0;i<5;i++)if((stages[i]&(1<<stage))&&ready[i]<=time+1e-9){chosen=i;break;}}
                if(time>=t.duration)return;
                casts[chosen]++;ready[chosen]=time+c[chosen]->cd;emit(1,time,casts[chosen],chosen);emit(4+stage,time,cycles+1);
                if(slot==0&&reentry[chosen]){time+=.5;continue;}break;
            }
            time+=stage==2?.37:.1;
        }
        if(time>=t.duration)break;cycles++;emit(2,time,cycles);
        double extension=0.;for(size_t j:c[chosen]->extension_rules){const auto&r=c[chosen]->mechanics[j];if(condition(r.condition,chosen,c))extension+=r.value;}
        double length=std::max(1.,10.+extension);fb+=std::min(length,t.duration-time);time+=length;if(time>=t.duration)break;emit(3,time,cycles);time+=2.;if(time>=t.duration)break;
    }
}
double action_rate(const Table&t,const Char&c,const double*v){
    auto a=[&](int i){return t.action_keys[i]<0?0.:v[t.action_keys[i]];};
    // nearbyint implements Python's ties-to-even round under the default mode.
    double ammo=std::max(1.,c.ammo+std::floor(c.ammo*(a(0)/100.)+.5)+std::nearbyint(a(1)));
    double reload=c.reload*std::max(0.,1.-a(2)/100.);
    double refill=std::min(1.,(1./c.clips)*std::max(0.,1.+a(6)/100.));
    double gain=std::max(1.,std::floor(ammo*refill+.5));reload*=std::max(1.,std::ceil(ammo/gain));
    double interval;
    if(c.charged){double cut=std::floor((c.charge_base*(a(4)/100.))/.01+.5)*.01;double charge=std::max(0.,std::max(0.,c.charge_base-cut)+a(5));interval=std::max(std::max(c.mincycle,charge+c.delay),1./60.);}
    else interval=1./(c.rate*std::max(.01,1.+a(3)/100.));
    return 1./(interval+reload/ammo);
}
void buckets(const Group&g,const double*v,double*f,bool compensated,uint64_t dirty=0,bool initialize=true){
    auto h=[&](int i){return bool(g.flags&(1u<<i));};bool normal=h(0);
    if(initialize||(dirty&g.bucket_reads[0]))f[0]=normal?g.coeff*(1+v[0]/100):g.coeff;
    if(initialize||(dirty&g.bucket_reads[1])){double defense=h(1)?0.:std::max(g.def*(1+v[3]/100)+v[4],0.)*(1-v[5]/100);
    f[1]=std::max(g.atk*(1+v[1]/100)+v[2]-defense,0.);}
    if(initialize||(dirty&g.bucket_reads[2])){f[2]=1+std::min(1.,std::max(0.,v[normal?6:7]))*std::max(0.,.5+v[normal?8:9]/100)+.5*h(2);
    if(normal&&h(3))f[2]+=.3;
    if(normal||h(4)||h(5))f[2]+=g.core*(g.corebonus+v[10]/100);}
    if(initialize||(dirty&g.bucket_reads[3]))f[3]=h(6)?g.charge*(1+v[12]/100)+v[11]/100:1.;
    if(initialize||(dirty&g.bucket_reads[4])){f[4]=1+v[13]/100;
    Sum sum(compensated);for(int i=0;i<g.bonus_count;i++)sum.add(v[g.bonus_keys[i]]/100);f[4]+=sum.value();
    if(h(7)){if(h(8))f[4]+=v[15]/100;if(h(9))f[4]+=v[16]/100;}}
    if(initialize||(dirty&g.bucket_reads[5]))f[5]=1+v[25]/100+(h(17)?v[26]/100:0);
    if(initialize||(dirty&g.bucket_reads[6]))f[6]=v[28]?1.1+v[27]/100:1.;
}
double supply_scale(const Table&t,const Char&c,const Buff&b,int casts,double fb){
    if(!b.burst)return 1.;
    double scale=casts/c.casts;
    if(b.phase_scaled){double exposure=b.phase?fb:t.duration-fb;scale*=c.phase_raw[b.phase]/std::max(exposure,1e-9);}
    return scale;
}
double own_correction(const Table&t,const Buff&b,bool valid,double scale,bool blocked=false){
    if(!b.own_observed)return 0.;
    if(blocked||((t.v3&32)&&!valid))return -1.;
    return b.phase_scaled?scale-1.:0.;
}
double supplied_value(const Table&t,const Buff&b,size_t j,double scale){
    double value=b.amounts[j].second*scale;
    return b.capped&&b.caps[j]>0.?std::min(value,b.caps[j]):value;
}
double own_delta(const Table&t,const Buff&b,size_t j,bool valid,double scale,bool blocked=false){
    if(blocked||((t.v3&32)&&!valid))return -b.amounts[j].second;
    if(b.capped){double own_scale=b.phase_scaled?scale:1.;return supplied_value(t,b,j,own_scale)-b.amounts[j].second;}
    return b.amounts[j].second*own_correction(t,b,valid,scale,blocked);
}
template<bool Reuse=false,bool V4=true>
void score(const Table&t,const uint32_t*ids,double&total,double*members,Scratch&scratch){
    const Char*c[5];for(int i=0;i<5;i++)c[i]=&t.chars[ids[i]];
    bool shield_possible=true;
    if constexpr(V4)if(t.v4&1){shield_possible=false;for(auto x:c)shield_possible|=x->shield_provider;}
    int casts[5]={};double ready[5]={},fb=0,time=3.;int stage_mask=0;
    for(auto x:c)stage_mask|=x->stage;
    if(t.switches&2){
        uint32_t key[5],hash=2166136261u;
        for(int i=0;i<5;i++){
            int context=0;
            if(c[i]->cycle_conditions)for(int j=0;j<5;j++)if(i!=j){
                if((c[i]->cycle_conditions&1)&&c[j]->b1)context|=1;
                if((c[i]->cycle_conditions&2)&&c[i]->has_squad&&c[i]->squad==c[j]->squad)context|=2;
            }
            key[i]=c[i]->cycle_classes[context];hash=(hash^key[i])*16777619u;
        }
        auto&cached=scratch.cycles[hash% scratch.cycles.size()];
        if(cached.valid&&std::equal(key,key+5,cached.key)){
            std::copy(cached.casts,cached.casts+5,casts);fb=cached.fb;
        }else{
            dynamic_cycle(t,c,casts,fb,scratch);
            std::copy(key,key+5,cached.key);std::copy(casts,casts+5,cached.casts);cached.fb=fb;cached.valid=true;
        }
    }
    else if(stage_mask==7)for(int iter=0;iter<32;iter++){
        bool stop=false;
        for(int stage=0;stage<3;stage++){
            int chosen=-1;double earliest=std::numeric_limits<double>::infinity();
            for(int i=0;i<5;i++)if(c[i]->stage&(1<<stage)){if(chosen<0&&ready[i]<=time+1e-9)chosen=i;earliest=std::min(earliest,ready[i]);}
            if(chosen<0){time=std::max(time,earliest);for(int i=0;i<5;i++)if((c[i]->stage&(1<<stage))&&ready[i]<=time+1e-9){chosen=i;break;}}
            if(time>=t.duration){stop=true;break;}
            casts[chosen]++;ready[chosen]=time+c[chosen]->cd;time+=stage==2?.37:.1;
        }
        if(stop||time>=t.duration)break;fb+=std::min(10.,t.duration-time);time+=12.;if(time>=t.duration)break;
    }
    // Small dense accumulator. Presence matters: an absent key must not add +0
    // to an own input. Source/buff/amount sequence is never reassociated.
    scratch.clear();auto&emission=scratch.emission;auto&touched=scratch.touched;
    uint64_t dirty[10]={};double stats[5][4]={};
    if(t.switches&4){
        for(int src=0;src<5;src++)for(size_t bi:c[src]->rank_buffs){
            const Buff&b=c[src]->buffs[bi];
            bool blocked=false;if constexpr(V4)blocked=((t.v4&1)&&b.needs_shield&&!shield_possible)||((t.v4&4)&&b.prerequisite&&!prerequisite_ok(b.prerequisite,src,c));
        bool valid=(!(t.switches&2)||condition(b.condition,src,c))&&!blocked;
            unsigned mask=0;if(valid&&b.can_supply)mask=buff_targets(b,src,c,ids);
            if(!mask&&!b.correctable)continue;
            double scale=supply_scale(t,*c[src],b,casts[src],fb);
            for(int dst=0;dst<5;dst++)if(mask&(1u<<dst))for(size_t j:b.rank_amounts){int off=(dst*2+1)*t.keys+b.amounts[j].first;emission[off]+=supplied_value(t,b,j,scale);touched[off]=1;}
            double correction=own_correction(t,b,valid,scale,blocked);
            if(correction||(b.capped&&b.own_observed))for(size_t j:b.rank_amounts){int off=(src*2+1)*t.keys+b.amounts[j].first;emission[off]+=own_delta(t,b,j,valid,scale,blocked);touched[off]=1;}
        }
        for(int i=0;i<5;i++){int off=(i*2+1)*t.keys;double pct=touched[off+1]?c[i]->rank_pct+emission[off+1]:c[i]->rank_pct;double flat=touched[off+2]?c[i]->rank_flat+emission[off+2]:c[i]->rank_flat;stats[i][0]=c[i]->atk*(1.+pct/100.)+flat;stats[i][1]=100.;stats[i][2]=c[i]->hp;stats[i][3]=c[i]->def;}
        std::fill(emission.begin(),emission.end(),0.);std::fill(touched.begin(),touched.end(),0);
    }
    for(int src=0;src<5;src++)for(const Buff&b:c[src]->buffs){
        bool blocked=false;if constexpr(V4)blocked=((t.v4&1)&&b.needs_shield&&!shield_possible)||((t.v4&4)&&b.prerequisite&&!prerequisite_ok(b.prerequisite,src,c));
        bool valid=(!(t.switches&2)||condition(b.condition,src,c))&&!blocked;
        unsigned mask=0;if(valid&&b.can_supply)mask=buff_targets(b,src,c,ids,(t.switches&4)?stats:nullptr);
        if(!mask&&!b.correctable)continue;
        double scale=supply_scale(t,*c[src],b,casts[src],fb);
        if constexpr(Reuse){
            // Each destination is an independent accumulator. Keep source,
            // buff and amount order within every accumulator, sharing only
            // the identical supplied scalar across destinations.
            for(size_t j=0;j<b.amounts.size();j++){
                int k=b.amounts[j].first;double value=supplied_value(t,b,j,scale);uint64_t bit=uint64_t(1)<<(k%64);
                for(unsigned remaining=mask;remaining;remaining&=remaining-1){
                    int dst=__builtin_ctz(remaining),phase=dst*2+b.phase,offset=phase*t.keys+k;
                    emission[offset]+=value;touched[offset]=1;dirty[phase]|=bit;
                }
            }
        }else{
        for(int dst=0;dst<5;dst++)if(mask&(1u<<dst)){
            int offset=(dst*2+b.phase)*t.keys;
            for(size_t j=0;j<b.amounts.size();j++){int k=b.amounts[j].first;emission[offset+k]+=supplied_value(t,b,j,scale);touched[offset+k]=1;dirty[dst*2+b.phase]|=uint64_t(1)<<(k%64);}
        }
        }
        double correction=own_correction(t,b,valid,scale,blocked);
        if(correction||(b.capped&&b.own_observed))for(size_t j=0;j<b.amounts.size();j++){int off=(src*2+b.phase)*t.keys+b.amounts[j].first;emission[off]+=own_delta(t,b,j,valid,scale,blocked);touched[off]=1;dirty[src*2+b.phase]|=uint64_t(1)<<(b.amounts[j].first%64);}
    }
    double direct[5];auto&own=scratch.own;
    for(int i=0;i<5;i++){
        double value=0.,merged_action=0.;int merged=-1,action_merged=-1;for(const Group&g:c[i]->groups){
            int offset=i*2*t.keys+g.offset;
            bool changed=bool(dirty[i*2+g.phase]&g.read_mask);
            if(changed&&merged!=g.merge_class){for(int k=0;k<t.keys;k++)own[k]=touched[offset+k]?g.own[k]+emission[offset+k]:g.own[k];merged=g.merge_class;}
            double exposure=g.phase?fb:t.duration-fb;double scale=exposure/c[i]->seconds[g.phase];if(g.use_cast)scale=casts[i]/c[i]->casts;
            if(g.use_action){if(changed&&action_merged!=g.merge_class){merged_action=action_rate(t,*c[i],own.data());action_merged=g.merge_class;}scale*=(changed?merged_action:g.idle_action)/g.action_divisor;}
            double prod=g.idle_product;if(changed){double f[7];std::copy(g.idle_f.begin(),g.idle_f.end(),f);buckets(g,own.data(),f,t.compensated,dirty[i*2+g.phase],false);prod=1.;
            for(int k=0;k<7;k++){double combined=g.self[k]+(f[k]-g.base[k]);if(k==1)combined=std::max(0.,combined);prod*=combined;}}
            value+=g.selected_unit*prod*scale;
        }direct[i]=std::max(0.,value);
    }
    Sum sum(t.compensated);for(double d:direct)sum.add(d);double base=sum.value();Sum result(t.compensated);
    for(int i=0;i<5;i++){double value=direct[i];for(const Dep&d:c[i]->deps)if(d.enabled)value+=d.ratio*(d.team?base:direct[i]);if(members)members[i]=value;result.add(value);}
    total=std::max(result.value(),1.);
}
}
extern "C" void* l2_create(const double*words,size_t count){
    try{Reader r{words,count};int version=r.integer();if(version!=1&&version!=2&&version!=3&&version!=4)return nullptr;int n=r.count();Table t;t.keys=r.count();if(t.keys<29||t.keys>4096)return nullptr;t.duration=r.next();t.compensated=r.integer();t.chars.resize(n);
        for(Char&c:t.chars){c.stage=r.integer();c.b3=r.integer();c.cd=r.next();c.squad=r.integer();c.has_squad=r.integer();c.weapon=r.integer();c.klass=r.integer();c.code=r.integer();c.charge=r.next();c.casts=r.next();c.seconds[0]=r.next();c.seconds[1]=r.next();int ng=r.count(),nb=r.count(),nd=r.count();
            c.groups.resize(ng);c.buffs.resize(nb);c.deps.resize(nd);
            for(Group&g:c.groups){g.phase=r.integer();g.flags=r.integer();g.unit=r.next();g.coeff=r.next();g.atk=r.next();g.def=r.next();g.core=r.next();g.corebonus=r.next();g.charge=r.next();g.own.resize(t.keys);for(double&x:g.own)x=r.next();for(double&x:g.base)x=r.next();for(double&x:g.self)x=r.next();if(g.phase<0||g.phase>1)return nullptr;}
            for(Buff&b:c.buffs){b.phase=r.integer();b.burst=r.integer();int na=r.count(),nr=r.count();if(b.phase<0||b.phase>1)return nullptr;for(int j=0;j<na;j++){int k=r.integer();double v=r.next();if(k<0||k>=t.keys)return nullptr;b.amounts.emplace_back(k,v);}for(int j=0;j<nr;j++)b.rules.push_back({r.integer(),r.integer(),r.integer(),r.integer()});}
            for(Dep&d:c.deps){d.enabled=r.integer();d.team=r.integer();d.ratio=r.next();}
        }
        if(version>=2){
            t.switches=r.integer();for(int&k:t.action_keys){k=r.integer();if(k<-1||k>=t.keys)return nullptr;}
            for(Char&c:t.chars){c.atk=r.next();c.hp=r.next();c.def=r.next();c.rank_pct=r.next();c.rank_flat=r.next();c.rate=r.next();c.charge_base=r.next();c.delay=r.next();c.clips=r.next();c.ammo=r.next();c.reload=r.next();c.mincycle=r.next();c.charged=r.integer();c.b1=r.integer();
                for(Group&g:c.groups){g.action_rate=r.next();g.context_unit=r.next();g.cast_scaled=r.integer();g.action_eligible=r.integer();}
                for(Buff&b:c.buffs)b.condition=r.integer();
                int nm=r.count();for(int j=0;j<nm;j++)c.mechanics.push_back({r.integer(),r.integer(),r.integer(),r.integer(),r.next(),r.integer(),r.integer()});
            }
        }
        if(version>=3){t.v3=r.integer();for(Char&c:t.chars){for(double&v:c.phase_raw)v=r.next();for(Group&g:c.groups)g.cast_scaled_s22=r.integer();for(Buff&b:c.buffs)b.own_observed=r.integer();}}
        for(Char&c:t.chars)for(Buff&b:c.buffs)b.caps.resize(b.amounts.size(),0.);
        if(version>=3&&r.n){if(r.integer()!=128)return nullptr;for(Char&c:t.chars)for(Buff&b:c.buffs)for(double&v:b.caps){v=r.next();if(!std::isfinite(v)||v<0.)return nullptr;b.has_caps|=v>0.;}}
        if(version==4){if(r.integer()!=256)return nullptr;t.v4=r.integer();if(t.v4&~7)return nullptr;for(Char&c:t.chars){c.shield_provider=r.integer();for(Buff&b:c.buffs)b.needs_shield=r.integer();}
            if(r.n){if(r.integer()!=512)return nullptr;for(Char&c:t.chars){c.stage_uncertain=r.integer();for(Buff&b:c.buffs){int v=r.integer();if(v<0||v>3)return nullptr;b.prerequisite=v;}}}
            else if(t.v4&4)return nullptr;
        }
        for(Char&c:t.chars){t.max_mechanics=std::max(t.max_mechanics,c.mechanics.size());const int source=int(&c-t.chars.data());
            // Preserve group order and every floating-point operation chain;
            // only table-constant choices and the ordered bonus-key list move.
            for(Group&g:c.groups){
                g.merge_class=int(&g-c.groups.data());
                for(const Group&prior:c.groups){
                    if(&prior==&g)break;
                    if(prior.phase==g.phase&&std::memcmp(prior.own.data(),g.own.data(),t.keys*sizeof(double))==0){g.merge_class=prior.merge_class;break;}
                }
                g.offset=g.phase*t.keys;
                g.use_cast=(g.flags&(1<<7))||((t.switches&2)&&g.cast_scaled)||((t.v3&64)&&g.cast_scaled_s22);
                g.use_action=(t.switches&1)&&g.action_eligible;
                g.selected_unit=(t.switches&8)?g.context_unit:g.unit;
                g.action_divisor=std::max(g.action_rate,1e-9);
                const int flags[]={7,10,1,11,12,13,14,15,16};const int keys[]={14,17,18,19,20,21,22,23,24};
                for(int i=0;i<9;i++)if(g.flags&(1u<<flags[i]))g.bonus_keys[g.bonus_count++]=keys[i];
                int bucket=0;auto read=[&](int k){if(k>=0){g.read_keys.push_back(k);if(bucket<7)g.bucket_reads[bucket]|=uint64_t(1)<<(k%64);}};
                auto h=[&](int k){return bool(g.flags&(1u<<k));};
                if(h(0))read(0);bucket=1;read(1);read(2);
                if(!h(1)){read(3);read(4);read(5);}
                bucket=2;read(h(0)?6:7);read(h(0)?8:9);
                if(h(0)||h(4)||h(5))read(10);
                bucket=3;if(h(6)){read(11);read(12);}
                bucket=4;read(13);for(int k=0;k<g.bonus_count;k++)read(g.bonus_keys[k]);
                if(h(7)){if(h(8))read(15);if(h(9))read(16);}
                bucket=5;read(25);if(h(17))read(26);bucket=6;read(27);read(28);bucket=7;
                if(g.use_action)for(int k:t.action_keys)read(k);
                std::sort(g.read_keys.begin(),g.read_keys.end());
                g.read_keys.erase(std::unique(g.read_keys.begin(),g.read_keys.end()),g.read_keys.end());
                for(int k:g.read_keys)g.read_mask|=uint64_t(1)<<(k%64);
                double f[7];buckets(g,g.own.data(),f,t.compensated);std::copy(f,f+7,g.idle_f.begin());
                for(int k=0;k<7;k++){double combined=g.self[k]+(f[k]-g.base[k]);if(k==1)combined=std::max(0.,combined);g.idle_product*=combined;}
                if(g.use_action)g.idle_action=action_rate(t,c,g.own.data());
            }
            for(size_t j=0;j<c.mechanics.size();j++){
                const auto&r=c.mechanics[j];
                if(r.kind==1||r.kind==2)c.stage_rules.push_back(j);
                if(r.kind==3)c.extension_rules.push_back(j);
                if(r.kind==0&&r.event>=0&&r.event<7)c.event_rules[r.event].push_back(j);
            }
            // These predicates depend only on the immutable table. Self-only
            // buffs may still correct observed own supply in v3, but never need
            // recipient selection. Keep their arithmetic and source order.
            for(Buff&b:c.buffs){
                b.can_supply=!std::all_of(b.rules.begin(),b.rules.end(),[&](const Rule&q){return q.op==0||q.op==2||(q.op==4&&q.a==source);});
                b.phase_scaled=(t.v3&16)&&b.burst;
                b.capped=(t.v3&128)&&b.has_caps;
                b.correctable=b.own_observed&&((t.v3&32)||b.phase_scaled||b.capped||((t.v4&1)&&b.needs_shield)||((t.v4&4)&&b.prerequisite));
                for(const Rule&q:b.rules){
                    if(q.op==1||q.op==3){b.all_candidates=true;continue;}
                    if(q.op==0||q.op==2)continue;
                    if(q.op==4||q.op==5||q.op==6||q.op==10||q.op==11||q.op==13||q.op==14||q.op==15){
                        if(b.candidates.empty())b.candidates.resize(t.chars.size());
                        for(size_t i=0;i<t.chars.size();i++){
                            const Char&d=t.chars[i];bool yes=false;
                            switch(q.op){case 4:yes=i==unsigned(q.a);break;case 5:yes=d.b3;break;
                            case 6:yes=c.has_squad&&d.squad==c.squad;break;
                            case 10:case 11:yes=d.weapon==q.a;break;
                            case 13:case 14:yes=d.code==q.a;break;
                            case 15:yes=d.code==q.a&&d.weapon==q.b;break;}
                            b.candidates[i]|=yes;
                        }
                    }else b.dynamic_rules.push_back(q);
                }
                if(b.all_candidates){b.candidates.clear();b.dynamic_rules.clear();}
            }
            c.buffs.erase(std::remove_if(c.buffs.begin(),c.buffs.end(),[&](const Buff&b){return !b.can_supply&&!b.correctable;}),c.buffs.end());
            // Ranking reads only phase-1 ATK percent/flat. Preserve the original
            // buff/amount subsequence for those keys; all other rank emission
            // used to be cleared without being read.
            for(size_t i=0;i<c.buffs.size();i++){
                Buff&b=c.buffs[i];
                for(size_t j=0;j<b.amounts.size();j++)if(b.amounts[j].first==1||b.amounts[j].first==2)b.rank_amounts.push_back(j);
                if(b.phase==1&&!b.rank_amounts.empty())c.rank_buffs.push_back(i);
            }
        }
        // Intern exact cycle behavior for the four possible structural contexts.
        // Byte keys retain signed zero and every rule's original order.
        vector<vector<uint64_t>> classes;
        for(Char&c:t.chars){
            for(const auto&q:c.mechanics)if(q.condition)c.cycle_conditions|=(q.condition==1||q.condition==2)?1:2;
            for(int context=0;context<4;context++){
                vector<uint64_t> key;auto bits=[&](double x){uint64_t v;std::memcpy(&v,&x,8);key.push_back(v);};
                key.push_back(c.stage);bits(c.cd);
                for(const auto&q:c.mechanics){
                    bool valid=!q.condition||((q.condition==1||q.condition==2)?bool(context&1)==(q.condition==2):bool(context&2));
                    if(!valid)continue;
                    key.push_back(q.kind);key.push_back(q.event);key.push_back(q.threshold);bits(q.value);key.push_back(q.scope);key.push_back(q.limit);
                }
                auto it=std::find(classes.begin(),classes.end(),key);
                c.cycle_classes[context]=uint32_t(it-classes.begin());
                if(it==classes.end())classes.push_back(std::move(key));
            }
        }
        if(r.n)return nullptr;return new Table(std::move(t));
    }catch(...){return nullptr;}
}
extern "C" void l2_destroy(void*t){delete static_cast<Table*>(t);}
extern "C" int l2_score_many(const void*ptr,const uint32_t*ids,size_t n,double*out,double*members){
    if(!ptr||(!ids&&n)||(!out&&n))return -1;const Table&t=*static_cast<const Table*>(ptr);
    Scratch&scratch=scratch_for(t);
    for(size_t row=0;row<n;row++){const uint32_t*s=ids+row*5;for(int i=0;i<5;i++){if(s[i]>=t.chars.size())return -1;for(int j=0;j<i;j++)if(s[i]==s[j])return -1;}
#ifdef __EMSCRIPTEN__
        score(t,s,out[row],members?members+row*5:nullptr,scratch);
#else
        if(t.v4)score<false,true>(t,s,out[row],members?members+row*5:nullptr,scratch);
        else score<false,false>(t,s,out[row],members?members+row*5:nullptr,scratch);
#endif
    }return 0;
}
extern "C" void* alloc(size_t n){return std::malloc(n);}
extern "C" void release(void*p){std::free(p);}
extern "C" uint32_t l2_generate(const void*ptr,uint32_t seed,uint32_t*ids,size_t n,int covered){
    const Table&t=*static_cast<const Table*>(ptr);if(!seed||t.chars.size()<5)return 0;
    auto next=[&](){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;};
    for(size_t row=0;row<n;){unsigned mask=0;for(int i=0;i<5;){uint32_t x=next()%t.chars.size();bool duplicate=false;for(int j=0;j<i;j++)if(ids[row*5+j]==x)duplicate=true;if(!duplicate){ids[row*5+i++]=x;mask|=t.chars[x].stage;}}if(!covered||mask==7)row++;}return seed;
}

#include <chrono>
#include <queue>
#ifndef __EMSCRIPTEN__
#include <thread>
#endif
namespace {
bool better(const L2Entry&a,const L2Entry&b){
    if(a.score!=b.score)return a.score>b.score;
    return std::lexicographical_compare(a.ids,a.ids+5,b.ids,b.ids+5);
}
struct Better { bool operator()(const L2Entry&a,const L2Entry&b)const{return better(a,b);} };
using Heap=std::priority_queue<L2Entry,vector<L2Entry>,Better>;
void retain(Heap&heap,const L2Entry&e,size_t k){
    if(heap.size()<k)heap.push(e);
    else if(better(e,heap.top())){heap.pop();heap.push(e);}
}
void finish(Heap&heap,L2Entry*out,size_t*count){
    *count=heap.size();for(size_t i=*count;i>0;i--){out[i-1]=heap.top();heap.pop();}
}
uint64_t choose(size_t n,unsigned k){uint64_t v=1;if(n<k)return 0;for(unsigned j=1;j<=k;j++)v=v*(n-j+1)/j;return v;}
bool covered(const Table&t,const uint32_t*ids){
    const Char*c[5];for(int i=0;i<5;i++)c[i]=&t.chars[ids[i]];
    int mask=0;
    for(int i=0;i<5;i++){
        int stage=c[i]->stage;
        if(t.switches&2)for(const auto&r:c[i]->mechanics)
            if(r.kind==1&&condition(r.condition,i,c))stage=1<<(int(r.value)-1);
        mask|=stage;
    }return mask==7;
}
}
static int enumerate_impl(const void*ptr,const uint32_t*roster,size_t n,size_t k,
    uint32_t part,uint32_t parts,uint32_t stride,L2Entry*out,size_t*out_n,L2Counts*counts,bool balanced,std::atomic<uint32_t>*next=nullptr){
    if(!ptr||!roster||!out||!out_n||!counts||n<5||n>1000||!k||!parts||part>=parts||!stride)return -1;
    const Table&t=*static_cast<const Table*>(ptr);
    vector<uint32_t> r(roster,roster+n);std::sort(r.begin(),r.end());
    for(size_t i=0;i<n;i++)if(r[i]>=t.chars.size()||(i&&r[i]==r[i-1]))return -1;
    Scratch&scratch=scratch_for(t);
    auto start=std::chrono::steady_clock::now();*counts={};Heap heap;
    uint64_t pair=0,task=next?next->fetch_add(1):0;
    for(size_t a=balanced?0:part;a+4<n;a+=balanced?1:parts){
        // Global lexicographic rank, independent of partition count.
        uint64_t rank=choose(n,5)-choose(n-a,5);
        for(size_t b=a+1;b+3<n;b++,pair++){
        if(balanced){
            if(next?pair!=task:pair%parts!=part)continue;
            rank=choose(n,5)-choose(n-a,5)+choose(n-a-1,4)-choose(n-b,4);
        }
        for(size_t c=b+1;c+2<n;c++)
        for(size_t d=c+1;d+1<n;d++)for(size_t e=d+1;e<n;e++,rank++){
            counts->visited++;if(rank%stride)continue;
            L2Entry entry{{r[a],r[b],r[c],r[d],r[e]},0.};
            if(!covered(t,entry.ids))continue;counts->covered++;
#ifdef __EMSCRIPTEN__
            // Keep one shared WASM scorer. The enum-only specialization caused
            // a measured runtime regression; the original emission path is exact.
            score(t,entry.ids,entry.score,nullptr,scratch);
#else
            if(t.v4)score<true,true>(t,entry.ids,entry.score,nullptr,scratch);
            else score<true,false>(t,entry.ids,entry.score,nullptr,scratch);
#endif
            counts->scored++;retain(heap,entry,k);
        }
        if(next)task=next->fetch_add(1);
        }
    }
    finish(heap,out,out_n);counts->seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();return 0;
}
// Preserve the public first-index partition contract for saved replays.
extern "C" int l2_enumerate(const void*t,const uint32_t*r,size_t n,size_t k,
    uint32_t part,uint32_t parts,uint32_t stride,L2Entry*out,size_t*out_n,L2Counts*counts){
    return enumerate_impl(t,r,n,k,part,parts,stride,out,out_n,counts,false);
}
// Round-robin canonical (first,second) prefixes spread the heavy early first
// indices over workers. Each worker keeps one scratch and one local top-K.
extern "C" int l2_enumerate_balanced(const void*t,const uint32_t*r,size_t n,size_t k,
    uint32_t part,uint32_t parts,uint32_t stride,L2Entry*out,size_t*out_n,L2Counts*counts){
    return enumerate_impl(t,r,n,k,part,parts,stride,out,out_n,counts,true);
}
extern "C" int l2_enumerate_threads(const void*t,const uint32_t*r,size_t n,size_t k,
    uint32_t threads,uint32_t stride,L2Entry*out,size_t*out_n,L2Counts*counts){
    if(!threads||threads>256||!k||!out||!out_n||!counts)return -1;
#ifdef __EMSCRIPTEN__
    if(threads!=1)return -1;
    return l2_enumerate(t,r,n,k,0,1,stride,out,out_n,counts);
#else
    auto start=std::chrono::steady_clock::now();
    vector<vector<L2Entry>> results(threads,vector<L2Entry>(k));vector<size_t> sizes(threads);
    vector<L2Counts> stats(threads);vector<int> rc(threads);vector<std::thread> workers;
    std::atomic<uint32_t> next{0};
    for(uint32_t i=0;i<threads;i++)workers.emplace_back([&,i](){rc[i]=enumerate_impl(t,r,n,k,i,threads,stride,results[i].data(),&sizes[i],&stats[i],true,&next);});
    for(auto&w:workers)w.join();*counts={};Heap heap;
    for(uint32_t i=0;i<threads;i++){
        if(rc[i])return rc[i];counts->visited+=stats[i].visited;counts->covered+=stats[i].covered;counts->scored+=stats[i].scored;
        for(size_t j=0;j<sizes[i];j++)retain(heap,results[i][j],k);
    }finish(heap,out,out_n);counts->seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();return 0;
#endif
}
