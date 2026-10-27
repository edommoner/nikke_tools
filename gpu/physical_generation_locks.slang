// No new timer: acquisitions are called by the real periodic activation path.
uint physicalLockHead(inout Runtime s){return s.resourceOutput+P_WORLD_ACTOR_POOL_QUERY_BASE+63*16;}
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
            if(s.lockPulseRow!=P_DEFINITIONS||d.kind!=4||d.stat!=0||d.enemyBuff!=0||d.target!=0||d.conditionCount!=1||d.bulletDuration!=0||
                !f64Equal(definition_period(s.inputBase,row),f64Div(ONE,f64FromI64(5))))return false;
            uint cond=s.inputBase+P_CONDITION_BASE+row*P_CONDITION_WORDS;
            if(commands[cond]!=C_CHARGING||commands[cond+1]!=0||!f64Zero(loadNumber(cond+2)))return false;
            s.lockPulseRow=row;
        }
    }
    if(s.lockPulseRow==P_DEFINITIONS)return false;
    for(uint step=0;step<commands[s.inputBase+2];step++)
    {uint op=commands[s.inputBase+P_COMMAND_BASE+step*8];if((op>=34&&op<=38)||(op>=41&&op<=46))return false;}
    s.locks.configured=1;s.locks.who=owner;s.locks.name=name;
    for(uint i=0;i<64*16;i++)results[s.resourceOutput+P_WORLD_ACTOR_POOL_QUERY_BASE+i]=0;
    uint h=physicalLockHead(s);results[h]=0x504c3031U;results[h+4]=owner;results[h+5]=s.lockPulseRow;return true;
}
void physicalLockPulse(inout Runtime s,uint row,uint64_t when)
{
    if(row!=s.lockPulseRow)return;
    if(s.lockPulseCount>=63){s.error=64;return;}
    actorSetCapture(s,33,0);if(s.error!=0)return;
    uint index=s.lockPulseCount;
    if(!generationLockAcquire(s,s.locks.who,s.locks.name,5,128,index<<8,when)){s.error=64;return;}
    uint source=s.resourceOutput+P_WORLD_ACTOR_RECEIPT_BASE+index*8,dst=s.resourceOutput+P_WORLD_ACTOR_POOL_QUERY_BASE+index*16;
    for(uint i=0;i<8;i++)results[dst+i]=results[source+i];storeNumber(dst+8,when);
    results[actorPoolSet(s,0)+5]=0;results[actorPoolHead(s)+7]--;
    s.lockPulseCount++;results[physicalLockHead(s)+1]=s.lockPulseCount;
}
void physicalLockSnapshot(inout Runtime s,uint who,uint64_t when)
{
    if(who!=s.locks.who)return;
    if(s.lockShotCount>=31){s.error=64;return;}
    if(!generationLockSnapshot(s,s.lockShotCount+1,0)){s.error=64;return;}
    s.lockShotCount++;results[physicalLockHead(s)+2]=s.lockShotCount;
}
void physicalLockAttack(inout Runtime s,uint who,uint64_t when)
{
    if(who!=s.locks.who)return;
    if(s.locks.revision==0x7fffffffU){s.error=64;return;}
    s.locks.count=0;s.locks.revision++;s.lockClearCount++;results[physicalLockHead(s)+3]=s.lockClearCount;
}
