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
struct Buff{int phase;bool burst;vector<std::pair<int,double>> amounts;vector<Rule> rules;};
struct Group{int phase;uint32_t flags;double unit,coeff,atk,def,core,corebonus,charge;vector<double> own;std::array<double,7> base,self;};
struct Dep{bool enabled,team;double ratio;};
struct Char{int stage,b3,squad,has_squad,weapon,klass,code;double cd,charge,casts,seconds[2];vector<Group> groups;vector<Buff> buffs;vector<Dep> deps;};
struct Table{int keys;double duration;bool compensated;vector<Char> chars;};
struct Reader{const double* p;size_t n; double next(){if(!n--)throw std::runtime_error("short table");return *p++;}int integer(){double x=next();if(!std::isfinite(x)||x<std::numeric_limits<int>::min()||x>std::numeric_limits<int>::max()||x!=std::trunc(x))throw std::runtime_error("integer");return int(x);}int count(){int x=integer();if(x<0||x>1000000)throw std::runtime_error("count");return x;}};
int sliced(int count,int limit){return limit<0?std::max(0,count+limit):std::min(count,limit);}
unsigned targets(const Rule&r,int src,const Char* const* c,const uint32_t* ids){
    unsigned mask=0;int pool[5],n=0;const Char& s=*c[src];
    switch(r.op){
    case 0:return 0;case 1:return 31;case 2:return 1u<<src;case 3:return 31^(1u<<src);
    case 4:for(int i=0;i<5;i++)if(ids[i]==unsigned(r.a))mask|=1u<<i;return mask;
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
void buckets(const Group&g,const double*v,double*f,bool compensated){
    auto h=[&](int i){return bool(g.flags&(1u<<i));};bool normal=h(0);
    f[0]=normal?g.coeff*(1+v[0]/100):g.coeff;
    double defense=h(1)?0.:std::max(g.def*(1+v[3]/100)+v[4],0.)*(1-v[5]/100);
    f[1]=std::max(g.atk*(1+v[1]/100)+v[2]-defense,0.);
    f[2]=1+std::min(1.,std::max(0.,v[normal?6:7]))*std::max(0.,.5+v[normal?8:9]/100)+.5*h(2);
    if(normal&&h(3))f[2]+=.3;
    if(normal||h(4)||h(5))f[2]+=g.core*(g.corebonus+v[10]/100);
    f[3]=h(6)?g.charge*(1+v[12]/100)+v[11]/100:1.;
    f[4]=1+v[13]/100;
    const int flags[]={7,10,1,11,12,13,14,15,16};const int keys[]={14,17,18,19,20,21,22,23,24};
    Sum sum(compensated);for(int i=0;i<9;i++)if(h(flags[i]))sum.add(v[keys[i]]/100);f[4]+=sum.value();
    if(h(7)){if(h(8))f[4]+=v[15]/100;if(h(9))f[4]+=v[16]/100;}
    f[5]=1+v[25]/100+(h(17)?v[26]/100:0);f[6]=v[28]?1.1+v[27]/100:1.;
}
void score(const Table&t,const uint32_t*ids,double&total,double*members){
    const Char*c[5];for(int i=0;i<5;i++)c[i]=&t.chars[ids[i]];
    int casts[5]={};double ready[5]={},fb=0,time=3.;int stage_mask=0;
    for(auto x:c)stage_mask|=x->stage;
    if(stage_mask==7)for(int iter=0;iter<32;iter++){
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
    vector<double> emission(10*t.keys,0.);vector<unsigned char> touched(10*t.keys,0);
    for(int src=0;src<5;src++)for(const Buff&b:c[src]->buffs){
        unsigned mask=0;for(const Rule&r:b.rules)mask|=targets(r,src,c,ids);mask&=~(1u<<src);
        if(!mask)continue;double scale=b.burst?casts[src]/c[src]->casts:1.;
        for(int dst=0;dst<5;dst++)if(mask&(1u<<dst)){
            int offset=(dst*2+b.phase)*t.keys;
            for(auto kv:b.amounts){emission[offset+kv.first]+=kv.second*scale;touched[offset+kv.first]=1;}
        }
    }
    double direct[5];vector<double> own(t.keys);
    for(int i=0;i<5;i++){
        double value=0.;for(const Group&g:c[i]->groups){
            int offset=(i*2+g.phase)*t.keys;
            for(int k=0;k<t.keys;k++)own[k]=touched[offset+k]?g.own[k]+emission[offset+k]:g.own[k];
            double exposure=g.phase?fb:t.duration-fb;double scale=exposure/c[i]->seconds[g.phase];if(g.flags&(1<<7))scale=casts[i]/c[i]->casts;
            double f[7];buckets(g,own.data(),f,t.compensated);double prod=1.;
            for(int k=0;k<7;k++){double combined=g.self[k]+(f[k]-g.base[k]);if(k==1)combined=std::max(0.,combined);prod*=combined;}
            value+=g.unit*prod*scale;
        }direct[i]=std::max(0.,value);
    }
    Sum sum(t.compensated);for(double d:direct)sum.add(d);double base=sum.value();Sum result(t.compensated);
    for(int i=0;i<5;i++){double value=direct[i];for(const Dep&d:c[i]->deps)if(d.enabled)value+=d.ratio*(d.team?base:direct[i]);if(members)members[i]=value;result.add(value);}
    total=std::max(result.value(),1.);
}
}
extern "C" void* l2_create(const double*words,size_t count){
    try{Reader r{words,count};if(r.integer()!=1)return nullptr;int n=r.count();Table t;t.keys=r.count();if(t.keys<29||t.keys>4096)return nullptr;t.duration=r.next();t.compensated=r.integer();t.chars.resize(n);
        for(Char&c:t.chars){c.stage=r.integer();c.b3=r.integer();c.cd=r.next();c.squad=r.integer();c.has_squad=r.integer();c.weapon=r.integer();c.klass=r.integer();c.code=r.integer();c.charge=r.next();c.casts=r.next();c.seconds[0]=r.next();c.seconds[1]=r.next();int ng=r.count(),nb=r.count(),nd=r.count();
            c.groups.resize(ng);c.buffs.resize(nb);c.deps.resize(nd);
            for(Group&g:c.groups){g.phase=r.integer();g.flags=r.integer();g.unit=r.next();g.coeff=r.next();g.atk=r.next();g.def=r.next();g.core=r.next();g.corebonus=r.next();g.charge=r.next();g.own.resize(t.keys);for(double&x:g.own)x=r.next();for(double&x:g.base)x=r.next();for(double&x:g.self)x=r.next();if(g.phase<0||g.phase>1)return nullptr;}
            for(Buff&b:c.buffs){b.phase=r.integer();b.burst=r.integer();int na=r.count(),nr=r.count();if(b.phase<0||b.phase>1)return nullptr;for(int j=0;j<na;j++){int k=r.integer();double v=r.next();if(k<0||k>=t.keys)return nullptr;b.amounts.emplace_back(k,v);}for(int j=0;j<nr;j++)b.rules.push_back({r.integer(),r.integer(),r.integer(),r.integer()});}
            for(Dep&d:c.deps){d.enabled=r.integer();d.team=r.integer();d.ratio=r.next();}
            const int source=int(&c-t.chars.data());
            c.buffs.erase(std::remove_if(c.buffs.begin(),c.buffs.end(),[&](const Buff&b){return std::all_of(b.rules.begin(),b.rules.end(),[&](const Rule&q){return q.op==0||q.op==2||(q.op==4&&q.a==source);});}),c.buffs.end());
        }if(r.n)return nullptr;return new Table(std::move(t));
    }catch(...){return nullptr;}
}
extern "C" void l2_destroy(void*t){delete static_cast<Table*>(t);}
extern "C" int l2_score_many(const void*ptr,const uint32_t*ids,size_t n,double*out,double*members){
    if(!ptr||(!ids&&n)||(!out&&n))return -1;const Table&t=*static_cast<const Table*>(ptr);
    for(size_t row=0;row<n;row++){const uint32_t*s=ids+row*5;for(int i=0;i<5;i++){if(s[i]>=t.chars.size())return -1;for(int j=0;j<i;j++)if(s[i]==s[j])return -1;}score(t,s,out[row],members?members+row*5:nullptr);}return 0;
}
extern "C" void* alloc(size_t n){return std::malloc(n);}
extern "C" void release(void*p){std::free(p);}
extern "C" uint32_t l2_generate(const void*ptr,uint32_t seed,uint32_t*ids,size_t n,int covered){
    const Table&t=*static_cast<const Table*>(ptr);if(!seed||t.chars.size()<5)return 0;
    auto next=[&](){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;};
    for(size_t row=0;row<n;){unsigned mask=0;for(int i=0;i<5;){uint32_t x=next()%t.chars.size();bool duplicate=false;for(int j=0;j<i;j++)if(ids[row*5+j]==x)duplicate=true;if(!duplicate){ids[row*5+i++]=x;mask|=t.chars[x].stage;}}if(!covered||mask==7)row++;}return seed;
}
