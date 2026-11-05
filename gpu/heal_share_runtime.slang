#include "heal_share_plan.slang"
#include "heal_share_trace.slang"
bool healShareFrameEnabled(inout Runtime s)
{
#ifdef PORTABLE_HEAL_SHARE_DIAGNOSTIC
    return true;
#else
    return (s.healthMask&128)!=0;
#endif
}
[noinline]
HealSharePlan sampleHealSharePlan(inout Runtime s,uint original,uint64_t when)
{
    HealShareLinks links={};
    for(uint pass=0;pass<s.orderedCount && s.error==0;pass++)
    {
        uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
        if(d.kind!=0 || d.stat!=S_heal_split || s.alive[row]==0 || !f64Less(when,s.end[row])) continue;
        uint mask=0;
        for(uint who=0;who<5 && s.error==0;who++)
        {
            if((s.downMask&(1U<<who))!=0) continue;
            if(s.lazyPending[row]!=0) ensureLazyRecipients(s,row,when);
            if((s.activeRecipients[row]&(1U<<who))!=0 && WORLD_STATE_NUMERIC_CONDITION(s,row,who,when,basicConditions(s,row,when,true,who))) mask|=1U<<who;
        }
        if(!addHealShareCarrier(links,mask)) s.error=64;
    }
    return finishHealSharePlan(links,original);
}
[noinline]
void beginHealShareFrame(inout Runtime s,inout Frame frame,uint64_t amount,uint source)
{
    HealSharePlan plan={};
    traceHealShare(s,1,frame.owner,frame.time,amount);
    if(f64Less(0,amount))
    {
        plan=sampleHealSharePlan(s,frame.owner,frame.time);
        traceHealShare(s,2,frame.owner,frame.time,0,plan.weights);
    }
    else { plan.weights=uint64_t(1)<<(frame.owner*10);plan.total=1;plan.members=1; }
    frame.mode=31;frame.event=0;frame.argument=int(source);frame.cursor=0;
    frame.value=plan.weights;frame.healthValue=amount;frame.repeatLeft=plan.total;frame.repeatPassive=plan.members;
}
#ifdef PORTABLE_RESIDENT_FRAME_STACK
[ForceInline]
void beginResourceHealShareFrame(inout Runtime s,inout DispatchFrameStack frames,int depth,uint64_t amount,uint source)
{
    Frame frame=loadDispatchFrame(frames,uint(depth));
    beginHealShareFrame(s,frame,amount,source);
    storeDispatchFrame(frames,uint(depth),frame);
}
#define BEGIN_DISPATCH_HEAL_SHARE(s,frames,depth,amount,source) beginResourceHealShareFrame(s,frames,depth,amount,source)
#else
#define BEGIN_DISPATCH_HEAL_SHARE(s,frames,depth,amount,source) beginHealShareFrame(s,frames[depth],amount,source)
#endif
[noinline]
void advanceHealShareFrame(inout Runtime s,inout DISPATCH_FRAMES(frames),inout int depth,Frame f)
{
    uint who=f.cursor;
    while(who<5 && uint((f.value>>(who*10))&1023)==0) who++;
    if(who==5)
    { traceHealShare(s,5,f.owner,f.time,f.healthValue);depth--;pushFrame(s,frames,depth,0,16,f.owner,f.argument,f.time);return; }
    frames[depth].cursor=who+1;
    HealSharePlan plan;plan.weights=f.value;plan.total=f.repeatLeft;plan.members=f.repeatPassive;
    uint64_t amount=healSharePortion(plan,who,f.healthValue),before=s.hp[who];
    traceHealShare(s,3,who,f.time,amount);
    s.hp[who]=storageBodyHeal(s,who,amount,f.time);
    traceHealShare(s,4,who,f.time,s.hp[who]);
    s.healing[who]=f64Add(s.healing[who],larger(0,f64Add(s.hp[who],before^F64_SIGN)));
    if(!f64Finite(s.healing[who])) { s.error=16;return; }
    syncHealthActor(s,who,f.time);
}
