#include "lock_packet_layout.slang"
#include "lock_delivery_policy.slang"
#ifndef LP_DIAGNOSTIC_CAPACITY
#define LP_DIAGNOSTIC_CAPACITY LP_TRACE_CAPACITY
#endif
#ifndef LP_TRACE_AT
#define LP_TRACE_AT(output,index) ((output)+LP_TRACE+(index)*16)
#endif
// A failed product composition retains the first packet failure in the existing
// 16-word projectile diagnostic bank. Success bytes and status semantics stay
// unchanged; both backends execute this same path before CPU fallback.
#ifdef PORTABLE_PRODUCT_COVER_LOCK
void failLockPacket(inout Runtime s,uint site,LandingReceipt r,uint packet,uint detail)
{
    if(s.error==0)
    {
        uint at=s.resourceOutput+786416U;
        results[at]=0x57504144U;results[at+1]=site;
        results[at+2]=r.row;results[at+3]=packet;
        results[at+4]=r.hit;results[at+5]=r.hits;results[at+6]=r.depth;results[at+7]=r.epoch;
        results[at+8]=r.lockSnapshot;results[at+9]=s.lockShotCount;
        storeNumber(at+10,r.when);
        uint h=landingHeader(s);results[at+12]=results[h];results[at+13]=results[h+1];
        results[at+14]=detail;results[at+15]=64U;
    }
    s.error=64;
}
#else
#define failLockPacket(s,site,r,packet,detail) s.error=64
#endif
bool lockPacketRow(inout Runtime s,uint row)
{return definition_kind(s.inputBase,row)==3&&(definition_damageFlags(s.inputBase,row)&H_SEQUENTIAL)!=0;}
bool initializeLockPackets(inout Runtime s)
{
    if(P_LANDINGS!=LP_QUEUE_CAPACITY)return false;
    for(uint row=0;row<s.count;row++)if(lockPacketRow(s,row))
    {
        Definition d=readDefinition(s.inputBase,row);uint e=s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS;
        if(d.kind!=3||d.owner!=s.locks.who||d.damageRoute!=11||d.damagePending!=0||d.periodicFlags!=0||!f64Zero(d.interval)||
            definition_triggerCount(s.inputBase,row)!=1||commands[e]!=11||d.conditionCount!=0||s.landingPolicy!=1||
            commands[namedEnemyDescriptor(s,row)+1]!=s.locks.name+1)return false;
    }
    for(uint i=LP_TOKENS;i<PL_OUTPUT;i++)results[s.resourceOutput+i]=0;
    results[s.resourceOutput+LP_HEAD]=LP_MAGIC;return true;
}
bool lockPacketTrace(inout Runtime s,LandingReceipt r,uint phase,uint packet)
{
    if(r.lockSnapshot==0||r.lockSnapshot>s.lockShotCount||r.lockSnapshot>31||r.hit<1||r.hit>r.hits||r.hits>256){failLockPacket(s,9001U,r,packet,0);return false;}
    uint token=r.lockSnapshot-1,snap=s.resourceOutput+PL_SNAPSHOTS+token*P_WORLD_ACTOR_SET_WORDS;
    if(!f64Equal(actorNumber(s.resourceOutput+LP_SHOT_TIMES+token*2),r.when)||results[snap+6]!=0x474c3031U||results[snap]>128){failLockPacket(s,9002U,r,packet,results[snap+6]);return false;}
    uint head=s.resourceOutput+LP_HEAD,index=results[head+1];if(index>=LP_DIAGNOSTIC_CAPACITY){failLockPacket(s,9003U,r,packet,index);return false;}
    uint at=LP_TRACE_AT(s.resourceOutput,index),ordinal=lockDeliveryIndex(r.hit,results[snap]),slot=0xffffffffU,gen=0,current=0,status=LD_EMPTY;
    if(ordinal!=0xffffffffU)
    {
        uint entry=snap+8+ordinal*4;slot=results[entry];gen=results[entry+1];bool present=slot<actorPoolCount(s),alive=false;
        if(present){current=results[actorPoolAt(s,slot)];alive=results[actorPoolAt(s,slot)+1]!=0;}
        status=lockDeliveryStatus(gen,present,current,alive);
    }
    results[at]=phase;results[at+1]=packet;results[at+2]=r.row;results[at+3]=r.hit;results[at+4]=r.hits;results[at+5]=r.lockSnapshot;
    results[at+6]=results[snap+7];results[at+7]=results[snap];storeNumber(at+8,r.when);
    results[at+10]=ordinal;results[at+11]=slot==0xffffffffU?0:slot+1;results[at+12]=gen;results[at+13]=current;results[at+14]=status;results[at+15]=LP_MAGIC;
    results[head+1]++;results[head+2+phase]++;return true;
}
void lockPacketStore(inout Runtime s,uint at,LandingReceipt r)
{
    uint packet=(at-s.resourceOutput-P_LANDING_STATE_BASE)/P_LANDING_WORDS;if(packet>=P_LANDINGS){failLockPacket(s,9004U,r,packet,at);return;}
    uint token=s.resourceOutput+LP_TOKENS+packet;
    if(results[token]!=0){failLockPacket(s,9005U,r,packet,results[token]);return;}
    if(!lockPacketRow(s,r.row))return;
    r.lockSnapshot=s.lockShotCount;
    if(lockPacketTrace(s,r,0,packet))results[token]=r.lockSnapshot;
}
// Materialize the scalar before clearing its RW slot. Slang's CUDA lowering
// otherwise keeps an address and returns the cleared value; Metal already
// materializes it. This is the same shared snapshot contract as actor scopes.
[noinline]
uint lockPacketTokenSnapshot(uint token)
{ return results[token]; }
uint lockPacketLoad(uint at)
{
    uint output=(at/P_OUTPUT_WORDS)*P_OUTPUT_WORDS,packet=(at-output-P_LANDING_STATE_BASE)/P_LANDING_WORDS;
    if(packet>=P_LANDINGS)return 0xffffffffU;
    uint token=output+LP_TOKENS+packet;uint value=lockPacketTokenSnapshot(token);results[token]=0;return value;
}
bool lockPacketObserveLoaded(inout Runtime s,LandingReceipt r)
{
    if(!lockPacketRow(s,r.row)){if(r.lockSnapshot!=0){failLockPacket(s,9006U,r,results[landingHeader(s)+1]-1,0);return false;}return true;}
    // The real drain increments its queue cursor before loading the receipt.
    uint packet=results[landingHeader(s)+1]-1;return lockPacketTrace(s,r,1,packet);
}
