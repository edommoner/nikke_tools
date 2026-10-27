#include "packet_fates_layout.slang"
// These are native's queued BODY proposals after their typed delivery. They
// retain the common queue's order/time/quantity, but never enter Actor land.
bool initializePacketFates(inout Runtime s)
{
    if(s.traceMode!=1||s.landingPolicy!=1)return false;
    for(uint i=PF_HEAD;i<PF_END;i++)results[s.resourceOutput+i]=0;
    results[s.resourceOutput+PF_HEAD]=PF_MAGIC;return true;
}
void compositionPushSkillHit(inout Runtime s,inout DISPATCH_FRAMES(frames),inout int depth,Definition d,uint64_t fraction,uint64_t when)
{
    if(d._wireRow!=commands[DF_DESCRIPTOR(s)]||s.target!=0){s.error=64;return;}
    uint scratch=DF_SCRATCH(s.resourceOutput,depth),h=s.resourceOutput+PF_HEAD;
    if(results[h+2]>=PF_CAPACITY){s.error=64;return;}
    enqueueLanding(s,d._wireRow,0,0xffffffffU,0,dtNumber(scratch+534),when,1,1,uint(depth+1),s.enemyEpoch);
    if(s.error!=0)return;
    results[h+2]++;
    // Called only from the existing typed continuation, after target-counter
    // children and before ordinary named-hit children, like native append().
    pushSkillHit(s,frames,depth,d,fraction,when);
}
bool compositionSuppressedReceipt(inout Runtime s,LandingReceipt r,uint index,uint64_t when)
{
    if(r.row!=commands[DF_DESCRIPTOR(s)])return false;
    uint h=s.resourceOutput+PF_HEAD,trace=results[worldSkillHead(s)+1];
    if(r.hit!=1||r.hits!=1||r.lockSnapshot!=0||!f64Zero(r.partAmount)||!f64Zero(r.interruptAmount)||trace>=PF_CAPACITY||results[h+3]>=results[h+2]){s.error=64;return true;}
    uint set=actorPoolSet(s,index);
    if(results[set+5]!=0){s.error=64;return true;}
    for(uint i=0;i<P_WORLD_ACTOR_SET_WORDS;i++)results[set+i]=0;
    results[set]=1;results[set+1]=1;results[set+5]=1;
    results[set+8]=0;results[set+9]=results[actorPoolAt(s,0)];results[set+10]=commands[actorBinding(s,0)];results[set+11]=commands[actorBinding(s,0)+1];
    results[actorPoolHead(s)+7]++;
    logWorldSkill(s,r,set,r.amount,when);
    results[set+5]=0;results[actorPoolHead(s)+7]--;
    if(s.error!=0)return true;
    results[s.resourceOutput+PF_FLAGS+trace]=1;results[h+1]++;results[h+3]++;
    return true; // No land(), counter(), heal(), or BODY damage.
}
