#include "physical_lock_layout.slang"
#ifdef PORTABLE_LOCK_PACKET_BINDINGS
#include "lock_packet_runtime.slang"
#endif
#ifndef PL_PULSE_CAPACITY
#define PL_PULSE_CAPACITY 63U
#endif
#ifndef PL_PULSE_AT
#define PL_PULSE_AT(s,index) ((s).resourceOutput+PL_PULSES+(index)*16)
#endif
// No new timer: acquisitions are called by the real periodic activation path.
uint physicalLockHead(inout Runtime s){return s.resourceOutput+PL_HEAD;}
bool initializePhysicalLocks(inout Runtime s)
{
    s.lockPulseCount=0;s.lockShotCount=0;s.lockClearCount=0;s.lockPulseRow=P_DEFINITIONS;
    uint owner=5,name=0;
    for(uint row=0;row<s.count;row++)if(definition_stat(s.inputBase,row)==TC_STAT)
    {owner=definition_owner(s.inputBase,row);name=uint(definition_targetName(s.inputBase,row));}
    if(owner>=5)return false;
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        if(d.name==name&&d.owner==owner)
        {
#ifdef PORTABLE_LOCK_ENEMY_CARRIER
            if(s.lockPulseRow!=P_DEFINITIONS||d.kind!=4||d.stat!=0||d.enemyBuff!=1||d.damageRoute!=6||d.damageCount!=1||d.conditionCount!=1||d.bulletDuration!=0||
#else
            if(s.lockPulseRow!=P_DEFINITIONS||d.kind!=4||d.stat!=0||d.enemyBuff!=0||d.target!=0||d.conditionCount!=1||d.bulletDuration!=0||
#endif
                !f64Equal(definition_period(s.inputBase,row),f64Div(ONE,f64FromI64(5))))return false;
            uint cond=s.inputBase+P_CONDITION_BASE+row*P_CONDITION_WORDS;
            if(commands[cond]!=C_CHARGING||commands[cond+1]!=0||!f64Zero(loadNumber(cond+2)))return false;
            s.lockPulseRow=row;
        }
    }
    if(s.lockPulseRow==P_DEFINITIONS)return false;
    for(uint step=0;step<commands[s.inputBase+2];step++)
    {uint op=commands[s.inputBase+P_COMMAND_BASE+step*8];
#ifdef PORTABLE_LOCK_ENEMY_CARRIER
     // Existing named-state readback is observational, not a lock command.
     if((op>=34&&op<=38)||(op>=42&&op<=46))return false;
#else
     if((op>=34&&op<=38)||(op>=41&&op<=46))return false;
#endif
    }
    s.locks.configured=1;s.locks.who=owner;s.locks.name=name;
    for(uint i=PL_BASE;i<PL_OUTPUT;i++)results[s.resourceOutput+i]=0;
    uint h=physicalLockHead(s);results[h]=0x504c3031U;results[h+4]=owner;results[h+5]=s.lockPulseRow;return true;
}
void physicalLockPulse(inout Runtime s,uint row,uint64_t when)
{
    if(row!=s.lockPulseRow)return;
    if(s.lockPulseCount>=PL_PULSE_CAPACITY){s.error=64;return;}
    uint source=s.resourceOutput+PL_CANDIDATE;for(uint i=0;i<P_WORLD_ACTOR_SET_WORDS;i++)results[source+i]=0;
    uint order[128],count=0;
    for(uint slot=0;slot<actorPoolCount(s);slot++)
    {uint kind=commands[actorBinding(s,slot)];if((kind==0||kind==5)&&results[actorPoolAt(s,slot)+1]!=0)order[count++]=slot;}
    actorSortSpawnOrder(s,order,count);results[source]=count;results[source+5]=1;
    for(uint i=0;i<count;i++)
    {uint slot=order[i],b=actorBinding(s,slot),e=source+8+i*4;results[source+1+slot/32]|=1U<<(slot%32);results[e]=slot;results[e+1]=results[actorPoolAt(s,slot)];results[e+2]=commands[b];results[e+3]=commands[b+1];}
    uint index=s.lockPulseCount,dst=PL_PULSE_AT(s,index);GenerationLockReceipt r;
    if(!generationLockAcquireSet(s,s.locks.who,s.locks.name,5,128,source,when,r)){s.error=64;return;}
    generationLockWriteReceipt(dst,r);storeNumber(dst+8,when);
    s.lockPulseCount++;results[physicalLockHead(s)+1]=s.lockPulseCount;
}
void physicalLockSnapshot(inout Runtime s,uint who,uint64_t when)
{
    if(who!=s.locks.who)return;
    if(s.lockShotCount>=31){s.error=64;return;}
    if(!generationLockSnapshotAt(s,s.resourceOutput+PL_SNAPSHOTS+s.lockShotCount*P_WORLD_ACTOR_SET_WORDS,0)){s.error=64;return;}
#ifdef PORTABLE_LOCK_PACKET_BINDINGS
    storeNumber(s.resourceOutput+LP_SHOT_TIMES+s.lockShotCount*2,when);
#endif
    s.lockShotCount++;results[physicalLockHead(s)+2]=s.lockShotCount;
}
void physicalLockAttack(inout Runtime s,uint who,uint64_t when)
{
    if(who!=s.locks.who)return;
    if(s.locks.revision==0x7fffffffU){s.error=64;return;}
    s.locks.count=0;s.locks.revision++;s.lockClearCount++;results[physicalLockHead(s)+3]=s.lockClearCount;
}

// Native final observation derives until_cleared after finish retires live adds.
// This is a final snapshot field, never a new close event or death notice.
void physicalLockFinalizeGraph(inout Runtime s)
{
    uint nodes=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];
    for(uint n=0;n<nodes;n++)
    {
        uint d=s.inputBase+P_WORLD_FRAME_INPUT_BASE+16+n*64,g=s.resourceOutput+P_WORLD_FRAME_OUTPUT_BASE+16+n*24;
        if(commands[s.inputBase+P_WORLD_ACTOR_NODE_BASE+n*4]!=2||(commands[d+1]&2)==0||results[g+1]==0)continue;
        bool live=false;for(uint slot=1;slot<actorPoolCount(s);slot++)
            if(commands[actorBinding(s,slot)]==5&&commands[actorBinding(s,slot)+3]==n&&results[actorPoolAt(s,slot)+1]!=0)live=true;
        results[g+6]=uint(!live);
    }
}
