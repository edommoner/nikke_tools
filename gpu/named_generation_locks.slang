// Provider order is not a distance policy. Actor pool handles never alias body.
static const uint GL_MAGIC=0x474c3031U;
bool initializeGenerationLocks(inout Runtime s)
{
    s.locks.count=0;s.locks.revision=0;s.locks.configured=0;s.locks.who=0;s.locks.name=0;
    for(uint i=0;i<128;i++){s.locks.slots[i]=0;s.locks.generations[i]=0;}
    if(!actorPoolsEnabled(s))return false;
    // Snapshot destinations are immutable and may not be used by pool writers.
    uint destinations=0;
    for(uint step=0;step<commands[s.inputBase+2];step++)
    {
        uint at=s.inputBase+P_COMMAND_BASE+step*8;
        if(commands[at]!=46)continue;
        uint index=commands[at+3];if(index>=32||(destinations&(1U<<index))!=0)return false;
        destinations|=1U<<index;
    }
    for(uint step=0;step<commands[s.inputBase+2];step++)
    {
        uint at=s.inputBase+P_COMMAND_BASE+step*8,op=commands[at],index=32;
        if(op==35)index=commands[at+4];else if(op==36)index=commands[at+4];else if(op==38)index=commands[at+3];
        if(index<32&&(destinations&(1U<<index))!=0)return false;
    }
    return true;
}
uint generationLockPrune(inout Runtime s)
{
    uint kept=0,removed=0;
    for(uint i=0;i<s.locks.count;i++)
    {
        uint slot=s.locks.slots[i],gen=s.locks.generations[i],p=actorPoolAt(s,slot);
        if(results[p+1]==0||results[p]!=gen){removed++;continue;}
        s.locks.slots[kept]=slot;s.locks.generations[kept]=gen;kept++;
    }
    s.locks.count=kept;return removed;
}
bool generationLockCommand(inout Runtime s,uint at,uint64_t when)
{
    if(commands[at]==45)
    {
        uint who=commands[at+3],name=commands[at+4],base=commands[at+5],limit=commands[at+6],packed=commands[at+7];
        uint candidate=packed&255U,receipt=packed>>8;
        if(who>=5||name>=P_DEFINITIONS||limit==0||limit>128||base>limit||candidate>=32||receipt>=P_COMMANDS)return false;
        if(s.locks.configured!=0&&(s.locks.who!=who||s.locks.name!=name))return false;
        uint source=actorPoolSet(s,candidate);if(results[source+5]!=1||results[source]>128)return false;
        uint capacity;uint64_t total;
        if(!namedTargetCountValue(s,who,name,base,limit,when,capacity,total))return false;
        // Validate the entire frozen provider list before changing membership.
        uint seen[4];for(uint i=0;i<4;i++)seen[i]=0;
        for(uint i=0;i<results[source];i++)
        {
            uint e=source+8+i*4,slot=results[e];if(slot>=actorPoolCount(s))return false;
            uint b=actorBinding(s,slot);
            if(commands[b]!=results[e+2]||commands[b+1]!=results[e+3]||results[e+1]==0||results[e+1]>=0x80000000U||(seen[slot/32]&(1U<<(slot%32)))!=0)return false;
            seen[slot/32]|=1U<<(slot%32);
        }
        s.locks.configured=1;s.locks.who=who;s.locks.name=name;
        uint removed=generationLockPrune(s),selected=0xffffffffU,gen=0;
        if(s.locks.count<capacity)for(uint i=0;i<results[source];i++)
        {
            uint e=source+8+i*4,slot=results[e],g=results[e+1],p=actorPoolAt(s,slot);
            if(results[p+1]==0||results[p]!=g)continue;
            bool locked=false;for(uint j=0;j<s.locks.count;j++)if(s.locks.slots[j]==slot&&s.locks.generations[j]==g)locked=true;
            if(locked)continue;
            selected=slot;gen=g;s.locks.slots[s.locks.count]=slot;s.locks.generations[s.locks.count]=g;s.locks.count++;break;
        }
        if(removed!=0||selected!=0xffffffffU){if(s.locks.revision==0x7fffffffU)return false;s.locks.revision++;}
        uint dst=s.resourceOutput+P_WORLD_ACTOR_RECEIPT_BASE+receipt*8;
        results[dst]=capacity;results[dst+1]=s.locks.count;results[dst+2]=s.locks.revision;
        results[dst+3]=selected==0xffffffffU?selected:commands[actorBinding(s,selected)];
        results[dst+4]=selected==0xffffffffU?0:commands[actorBinding(s,selected)+1];results[dst+5]=gen;results[dst+6]=removed;results[dst+7]=GL_MAGIC;
        return true;
    }
    uint index=commands[at+3],reason=commands[at+4];
    if(index>=32||reason>2||commands[at+5]!=0||commands[at+6]!=0||commands[at+7]!=0)return false;
    uint removed=generationLockPrune(s);if(removed!=0){if(s.locks.revision==0x7fffffffU)return false;s.locks.revision++;}
    if(reason!=0&&s.locks.revision==0x7fffffffU)return false;
    uint dst=actorPoolSet(s,index);if(results[dst+5]!=0||results[dst+6]!=0)return false;
    for(uint i=0;i<P_WORLD_ACTOR_SET_WORDS;i++)results[dst+i]=0;
    results[dst]=s.locks.count;results[dst+6]=GL_MAGIC;results[dst+7]=s.locks.revision;
    for(uint i=0;i<s.locks.count;i++)
    {
        uint slot=s.locks.slots[i],e=dst+8+i*4,b=actorBinding(s,slot);
        results[dst+1+slot/32]|=1U<<(slot%32);results[e]=slot;results[e+1]=s.locks.generations[i];results[e+2]=commands[b];results[e+3]=commands[b+1];
    }
    if(reason!=0){s.locks.count=0;s.locks.revision++;}
    return true;
}
