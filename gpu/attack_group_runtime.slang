// GPU-owned actual-shot groups. Uses canonical Actor receipts and DFS dispatch.
// The explicit AGS1 policy counts BODY/ADD enemies, never pellets or damage.
#ifdef PORTABLE_COMPOSED_ARENA
#include "composed_arena_layout.slang"
#else
static const uint AG_HEADER=800000,AG_SLOTS=800032,AG_WORDS=536,AG_LOG=820000,AG_LOG_CAP=64,AG_PACKETS=860000;
#ifdef PORTABLE_COORDINATE_GROUPS
static const uint AG_COMPACT=1310720,AG_COMPACT_WORDS=186528;
#else
static const uint AG_COMPACT=AG_PACKETS+P_LANDINGS,AG_COMPACT_WORDS=1048576-AG_COMPACT;
#endif
#endif
uint agHead(inout Runtime s) { return s.resourceOutput+AG_HEADER; }
uint agAt(inout Runtime s,uint index) { return s.resourceOutput+AG_SLOTS+index*AG_WORDS; }
uint agKey(inout Runtime s,uint index) { return (results[agAt(s,index)+3]<<5)|index; }
uint agResolve(inout Runtime s,uint key)
{
    uint index=key&31U,at=agAt(s,index);
    if(key==0||results[at]==0||results[at+3]!=(key>>5)) { s.error=64;return 0xffffffffU; }
    return index;
}
void agRelease(inout Runtime s,uint key)
{
    uint index=agResolve(s,key);if(s.error!=0) return;uint at=agAt(s,index);
    if(results[at+6]==0) { s.error=64;return; }
    if(--results[at+6]==0) results[at]=0;
}
uint agRetainCurrent(inout Runtime s,uint row)
{
    uint key=results[agHead(s)+4];if(key==0||definition_damageRoute(s.inputBase,row)!=0) return 0;
    uint index=agResolve(s,key);if(s.error!=0) return 0;uint at=agAt(s,index);
    if(results[at]!=2||results[at+6]>=1024) { s.error=64;return 0; }
    results[at+6]++;return key;
}
// Materialize a temporary canonical Actor set from the owned frozen tuple.
// Fresh liveness/generation filtering prevents a same-label respawn retarget.
void agCapture(inout Runtime s,uint key,uint index)
{
    uint source=agResolve(s,key);if(s.error!=0) return;uint from=agAt(s,source),at=actorPoolSet(s,index);
    if(results[from]!=2||results[at+5]!=0) { s.error=64;return; }
    for(uint i=0;i<P_WORLD_ACTOR_SET_WORDS;i++) results[at+i]=0;
    ActorBits bits=actorBitsEmpty();uint count=0;
    for(uint i=0;i<results[from+4];i++)
    {
        uint packet=from+24+i*4,slot=results[packet],generation=results[packet+1];
        if(slot>=actorPoolCount(s)) { s.error=64;return; }
        if(results[actorPoolAt(s,slot)]!=generation||results[actorPoolAt(s,slot)+1]==0) continue;
        uint entry=at+8+count++*4;for(uint j=0;j<4;j++) results[entry+j]=results[packet+j];actorBitsAdd(bits,slot);
    }
    results[at]=count;for(uint i=0;i<4;i++) results[at+1+i]=bits.words[i];results[at+5]=1;results[actorPoolHead(s)+7]++;
}
// Canonical Boss.route(ev.to) counts vanished/stale requested labels as
// unrouted overkill. No receipt, hit, new-generation damage or owner score.
void agRejectedRouting(inout Runtime s,uint key,uint who,uint64_t amount)
{
    uint index=agResolve(s,key);if(s.error!=0) return;uint at=agAt(s,index),dead=0;
    for(uint i=0;i<results[at+4];i++)
    {
        uint entry=at+24+i*4,slot=results[entry];
        if(results[entry+2]!=5) continue;
        if(results[actorPoolAt(s,slot)]!=results[entry+1]||results[actorPoolAt(s,slot)+1]==0) dead++;
    }
    if(dead!=0) actorPoolAddOverkill(s,who,f64Mul(amount,f64FromI64(dead)),false);
}
bool initializeAttackGroups(inout Runtime s)
{
    uint input=s.inputBase+104400,head=agHead(s);
    for(uint i=0;i<32+32*AG_WORDS;i++) results[head+i]=0;
    for(uint i=0;i<AG_LOG_CAP*AG_WORDS;i++) results[s.resourceOutput+AG_LOG+i]=0;
    for(uint i=0;i<P_LANDINGS;i++) results[s.resourceOutput+AG_PACKETS+i]=0;
    if(commands[input]!=0x41475331U||(commands[input+1]!=1&&commands[input+1]!=2)
#ifndef PORTABLE_COMPOSED_ARENA
       ||commands[input+2]==0
#endif
       ||(commands[input+2]&~31U)!=0) return false;
    if(commands[input+3]>1) return false;
    for(uint i=4;i<8;i++) if(commands[input+i]!=0) return false;
    if(commands[input+3]!=0) for(uint i=0;i<AG_COMPACT_WORDS;i++) results[s.resourceOutput+AG_COMPACT+i]=0;
    if(!actorRecipientsEnabled(s)||s.combat==0||s.landingPolicy!=1||s.targetCount!=1||commands[s.inputBase+P_WORLD_TEAM_INPUT_BASE+3]!=0) return false;
    #ifdef PORTABLE_COMPOSED_ARENA
    for(uint slot=0;slot<actorPoolCount(s);slot++) if(commands[actorBinding(s,slot)]!=0&&commands[actorBinding(s,slot)]!=1&&commands[actorBinding(s,slot)]!=6
#ifdef PORTABLE_COORDINATE_GROUPS
       &&commands[actorBinding(s,slot)]!=5
#endif
       ) return false;
#else
    for(uint slot=0;slot<actorPoolCount(s);slot++) if(commands[actorBinding(s,slot)]!=0&&commands[actorBinding(s,slot)]!=5) return false;
#endif
    uint owners=0;
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        for(uint slot=0;slot<d.triggerCount;slot++)
        {
            uint at=s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8;if(commands[at]!=62) continue;
            uint threshold=commands[at+4];
            if(threshold<1||threshold>128||loadNumber(at+1)!=f64FromI64(threshold)||commands[at+3]!=0||commands[at+5]!=0||commands[at+6]!=0||commands[at+7]!=0||d.conditionCount!=0||d.kind!=0&&d.kind!=3||d.kind==3&&(d.damagePending!=0||d.damageRoute!=0||!f64Zero(d.interval)||(d.damageFlags&H_SPLIT)!=0)||d.damageRoute!=0&&d.target!=0) return false;
            owners|=1U<<d.owner;
        }
    }
    if(owners!=commands[input+2]) return false;
    results[head]=0x41475331U;results[head+8]=owners;results[head+9]=commands[input+1]-1;results[head+10]=commands[input+3];return true;
}
void agCollect(inout Runtime s,uint group,uint slot,uint generation)
{
    uint at=agAt(s,group),count=results[at+4];if(results[at]!=1) { s.error=64;return; }
    for(uint i=0;i<count;i++) if(results[at+24+i*4]==slot&&results[at+25+i*4]==generation) return;
    if(count>=128) { s.error=64;return; }
    uint to=at+24+count*4,b=actorBinding(s,slot);results[to]=slot;results[to+1]=generation;results[to+2]=commands[b];results[to+3]=commands[b+1];results[at+4]++;
}
bool deliverAttackGroupShot(inout Runtime s,uint who,uint64_t when,uint output,uint64_t amount,uint count)
{
    uint head=agHead(s);if(count==0||(results[head+8]&(1U<<who))==0) return false;
    if(s.error!=0) return true;
#ifdef PORTABLE_COMPOSED_ARENA
    if(actorPoolCount(s)!=1) { s.error=64;return true; } // Coordinate physical probability/parts routing is unconnected.
#endif
    if(!worldPhysicalNormal(s,who)||count>1024||results[head+3]!=0) { s.error=64;return true; }
#include "attack_group_open.slang"
    uint saved=s.target;
    for(uint hit=0;hit<count&&s.error==0;hit++)
    {
        uint setIndex=0;while(setIndex<P_WORLD_ACTOR_SETS&&results[actorPoolSet(s,setIndex)+5]!=0) setIndex++;
        if(setIndex==P_WORLD_ACTOR_SETS) { s.error=64;break; }
        // Native route samples the existing physical selector again after each
        // pellet's receipt/counter children. A destroyed ADD is never reused.
        actorSetCapture(s,33,setIndex,results[head+9]!=0 ? 0 : 2,128,0,who NAMED_ENEMY_ARGUMENT(0));uint set=actorPoolSet(s,setIndex),n=results[set];
        for(uint i=0;i<n&&s.error==0;i++)
        {
            uint entry=set+8+i*4,slot=results[entry],generation=results[entry+1];
            if(results[actorPoolAt(s,slot)]!=generation||results[actorPoolAt(s,slot)+1]==0) continue;
            storeNumber(actorPoolHead(s)+2,when);s.target=0;land(s,who,ACTOR_REF|slot,amount);
            uint receipt=actorPoolHead(s)+18;if(results[receipt]==0||s.error!=0) continue;
            // Receipt is collected before synchronous counter children run.
            agCollect(s,group,slot,generation);
            uint64_t credit=commands[actorBinding(s,slot)]==5?actorNumber(receipt+2):amount;
            counterPhysicalPacket(s,who,slot,generation,credit,results[receipt+1]!=0,when,output);
            if((s.healthMask&64)!=0&&s.error==0) dispatch(s,17,0,who,0,when,output,amount);
            if(damageAccumEnabled(s)&&slot==0&&s.error==0) dispatch(s,39,0,who,0,when,output,amount);
        }
        results[set+5]=0;results[actorPoolHead(s)+7]--;
    }
    s.target=saved;
#include "attack_group_seal.slang"

}

#ifdef PORTABLE_COORDINATE_GROUPS
bool beginCoordinatePhysicalGroup(inout Runtime s,uint who,uint64_t when,uint count)
{
    uint head=agHead(s);
    if(count==0||(results[head+8]&(1U<<who))==0||!worldPhysicalNormal(s,who))return false;
    if(s.error!=0)return true;
    uint maximum=131072;
#ifdef PORTABLE_COORDINATE_TYPED_WEAPONS
    if(coordinateTypedWeapons(s))maximum=262144;
#endif
    if(count>maximum||results[head+3]!=0){s.error=64;return true;}
#include "attack_group_open.slang"
    return true;
}
bool finishCoordinatePhysicalGroup(inout Runtime s,uint who,uint64_t when,uint output)
{
    if(s.error!=0)return true;
    uint head=agHead(s),pending=results[head+3];if(pending==0)return false;
    uint group=pending-1,at=agAt(s,group);
#include "attack_group_seal.slang"
}
#endif
