// One candidate producer for real selection and the unobserved next-FB chain.
// No Runtime, command buffer or CPU-computed prediction is owned by this module.
#ifndef PORTABLE_BURST_CONTROL_SHARED_BINARY64
#include "binary64.slang"
#endif
static const uint64_t BC_INF=uint64_t(0x7ff00000)<<32;
static const uint64_t BC_EPS=(uint64_t(0x3e112e0b)<<32)|0xe826d695;
struct BurstControlPolicy { uint words[176]; };
struct BurstControlState
{
    uint stage,cycle,reentry,unavailable,explicitStage;
    uint stages[5];
    uint64_t when,opened,action,ready[5];
};
struct BurstControlCandidates {uint count;uint owners[5];};
struct BurstControlDecision {uint owner,waitMask;uint64_t action;};
uint64_t burstControlNumber(BurstControlPolicy p,uint at)
{return uint64_t(p.words[at])|(uint64_t(p.words[at+1])<<32);}
uint64_t burstControlMax(uint64_t a,uint64_t b){return f64Less(a,b)?b:a;}
uint64_t burstControlMin(uint64_t a,uint64_t b){return f64Less(b,a)?b:a;}
bool burstControlBound(uint64_t x,uint n)
{return f64Finite(x)&&!f64Less(x,0)&&!f64Less(f64FromI64(n),x);}
bool burstControlValid(BurstControlPolicy p)
{
    if(p.words[0]!=0x42435631U||p.words[1]!=1||p.words[2]!=1||p.words[3]>16||p.words[4]!=5||p.words[5]!=24||p.words[6]!=16||p.words[7]!=0)return false;
    for(uint who=0;who<5;who++)
    {
        uint at=8+who*24,kind=p.words[at+4];uint64_t wait=burstControlNumber(p,at+2);
        if(!burstControlBound(burstControlNumber(p,at),180)||!burstControlBound(wait,3)||!f64Zero(wait)&&f64Less(wait,uint64_t(0x3fe00000)<<32)||kind>2||p.words[at+22]>1||p.words[at+23]!=0)return false;
        if(kind==1?p.words[at+5]==0:p.words[at+5]!=0)return false;
        if(kind!=0&&p.words[at+22]!=1)return false;
        for(uint i=0;i<16;i++)if(kind!=2&&p.words[at+6+i]!=0)return false;
    }
    for(uint cycle=0;cycle<16;cycle++)for(uint stage=0;stage<3;stage++)
    {
        uint word=p.words[128+cycle*3+stage],mask=0;bool ended=false;
        if(cycle>=p.words[3]&&word!=0||word>>15!=0)return false;
        for(uint i=0;i<5;i++){uint v=(word>>(3*i))&7;if(v==0){ended=true;continue;}if(ended||v>5||(mask&(1U<<v))!=0)return false;mask|=1U<<v;}
    }
    return true;
}
uint burstControlRank(BurstControlPolicy p,uint who,uint cycle)
{
    uint at=8+who*24,kind=p.words[at+4];if(kind==0)return 1;
    bool due=kind==1?cycle%p.words[at+5]==0:cycle<=512&&(p.words[at+6+(cycle-1)/32]&(1U<<((cycle-1)%32)))!=0;
    return due?0:2;
}
BurstControlCandidates burstControlCandidates(BurstControlPolicy p,BurstControlState s,uint stage,bool actual)
{
    BurstControlCandidates c;c.count=0;for(uint i=0;i<5;i++)c.owners[i]=0;
    if(s.cycle<p.words[3])
    {uint word=p.words[128+s.cycle*3+stage-1];for(uint i=0;i<5;i++){uint v=(word>>(3*i))&7;if(v==0)break;c.owners[c.count++]=v-1;}return c;}
    bool explicitChoice=false;
    for(uint who=0;who<5;who++)if(s.stages[who]==stage||s.stages[who]==4)
    {c.owners[c.count++]=who;if(p.words[8+who*24+22]!=0||(s.explicitStage&(1U<<who))!=0)explicitChoice=true;}
    if(stage<3&&s.reentry==0&&!explicitChoice&&c.count>1)c.count=1;
    if(actual)for(uint i=1;i<c.count;i++)
    {uint who=c.owners[i],rank=burstControlRank(p,who,s.cycle+1),j=i;while(j>0&&burstControlRank(p,c.owners[j-1],s.cycle+1)>rank){c.owners[j]=c.owners[j-1];j--;}c.owners[j]=who;}
    return c;
}
BurstControlDecision burstControlChoose(BurstControlPolicy p,BurstControlState s,BurstControlCandidates c)
{
    BurstControlDecision d;d.owner=5;d.waitMask=0;d.action=s.action;
    if(c.count==0){d.action=BC_INF;return d;}
    for(uint i=0;i<c.count;i++)
    {
        uint who=c.owners[i];if((s.unavailable&(1U<<who))!=0)continue;
        uint64_t ready=s.ready[who];uint at=8+who*24;
        if(f64Less(s.when,f64Add(ready,BC_EPS^F64_SIGN)))
        {
            if(!f64Less(f64Add(burstControlNumber(p,at+2),BC_EPS),f64Add(ready,s.when^F64_SIGN)))
            {d.action=ready;d.waitMask=1U<<who;return d;}continue;
        }
        uint64_t delay=burstControlNumber(p,at);
        if(!f64Zero(delay))
        {uint64_t press=f64Add(burstControlMax(s.opened,ready),delay);if(f64Less(s.when,f64Add(press,BC_EPS^F64_SIGN))){d.action=press;return d;}}
        d.owner=who;return d;
    }
    uint64_t earliest=BC_INF;
    for(uint i=0;i<c.count;i++){uint who=c.owners[i];earliest=burstControlMin(earliest,s.ready[who]);d.waitMask|=1U<<who;}
    d.action=burstControlMax(s.action,earliest);return d;
}
// Called at full-burst end, after the completed-cycle counter increments.
// Candidate stages must be the snapshot made at tick entry, before end notices.
uint64_t burstControlPredict(BurstControlPolicy p,BurstControlState s)
{
    uint64_t at=s.when;s.reentry=0;
    for(uint stage=1;stage<=3;stage++)
    {
        BurstControlCandidates c=burstControlCandidates(p,s,stage,false);if(c.count==0)return (uint64_t(0x3ff00000)<<32)|F64_SIGN;
        uint64_t best=BC_INF;
        for(uint i=0;i<c.count;i++){uint who=c.owners[i];best=burstControlMin(best,f64Add(burstControlMax(at,s.ready[who]),burstControlNumber(p,8+who*24)));}
        at=f64Add(best,stage==3?((uint64_t(0x3fd7ae14)<<32)|0x7ae147ae):((uint64_t(0x3fb99999)<<32)|0x9999999a));
    }
    return at;
}
