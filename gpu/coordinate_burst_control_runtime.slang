#define PORTABLE_BURST_CONTROL_SHARED_BINARY64
#include "burst_control_policy.slang"
static const uint CBC_INPUT=109792U,CBC_BASE=1769838U;
bool burstControls(inout Runtime s){return commands[s.inputBase+CBC_INPUT+2]==1;}
uint burstControlHead(inout Runtime s){return s.resourceOutput+CBC_BASE;}
BurstControlPolicy loadBurstControlPolicy(inout Runtime s)
{BurstControlPolicy p;for(uint i=0;i<176;i++)p.words[i]=commands[s.inputBase+CBC_INPUT+i];return p;}
bool initializeBurstControls(inout Runtime s)
{
    BurstControlPolicy p=loadBurstControlPolicy(s);
    if(!burstControls(s))
    {
        for(uint i=0;i<176;i++)
        {uint expected=i==0?0x42435631U:i==1?1U:i==4?5U:i==5?24U:i==6?16U:0U;if(p.words[i]!=expected)return false;}
        return true;
    }
    if(!burstControlValid(p)||!manualControls(s))return false;
    uint h=burstControlHead(s);for(uint i=0;i<18;i++)results[h+i]=0;
    results[h]=0x42435631U;storeNumber(h+2,ONE|F64_SIGN);s.action=BC_INF;
    storeNumber(h+10,uint64_t(0xcbf29ce484222325));storeNumber(h+12,uint64_t(0x84222325cbf29ce4));return true;
}
BurstControlState loadBurstControlState(inout Runtime s,uint64_t when)
{
    BurstControlState b;uint h=burstControlHead(s);b.stage=s.phase;b.cycle=results[h+1];b.reentry=s.reentrySlot;b.unavailable=s.downMask;b.explicitStage=0;
    b.when=when;b.opened=actorNumber(h+2);b.action=s.action;
    for(uint who=0;who<5;who++)
    {b.ready[who]=s.ready[who];b.stages[who]=results[h+4+who];if(statusStunned(s,who))b.unavailable|=1U<<who;if((commands[s.inputBase+P_WEAPON_BASE+who*P_WEAPON_WORDS+3]&1024U)!=0)b.explicitStage|=1U<<who;}
    return b;
}
void cacheBurstControlStages(inout Runtime s,uint stages[5])
{if(burstControls(s))for(uint who=0;who<5;who++)results[burstControlHead(s)+4+who]=stages[who];}
void openBurstControlStage(inout Runtime s,uint64_t when)
{if(burstControls(s))storeNumber(burstControlHead(s)+2,when);}
void finishBurstControlCycle(inout Runtime s)
{if(burstControls(s))results[burstControlHead(s)+1]++;}
void chooseBurstControl(inout Runtime s,uint64_t when,out uint picked)
{
    BurstControlPolicy p=loadBurstControlPolicy(s);BurstControlState b=loadBurstControlState(s,when);
    BurstControlCandidates c=burstControlCandidates(p,b,s.phase,true);BurstControlDecision d=burstControlChoose(p,b,c);
    picked=d.owner;s.action=d.action;s.cooldownWaitMask=d.waitMask;
}
void predictBurstControl(inout Runtime s,uint64_t when)
{storeNumber(ciHead(s)+12,burstControlPredict(loadBurstControlPolicy(s),loadBurstControlState(s,when)));}
void captureBurstControl(inout Runtime s,uint64_t when)
{
    if(!burstControls(s))return;uint h=burstControlHead(s),words[25];
    words[0]=uint(when);words[1]=uint(when>>32);words[2]=s.phase;words[3]=s.reentrySlot;words[4]=uint(s.action);words[5]=uint(s.action>>32);
    words[6]=results[h+2];words[7]=results[h+3];words[8]=results[h+1];
    for(uint who=0;who<5;who++){words[9+who]=results[h+4+who];words[15+who*2]=uint(s.ready[who]);words[16+who*2]=uint(s.ready[who]>>32);}
    words[14]=s.cooldownWaitMask;uint64_t a=actorNumber(h+10),b=actorNumber(h+12);
    for(uint i=0;i<25;i++){uint64_t w=words[i];a=(a^w)*uint64_t(0x100000001b3);b=((b<<7)|(b>>57))^w*uint64_t(0x9e3779b185ebca87);}
    storeNumber(h+10,a);storeNumber(h+12,b);results[h+14]++;
}
