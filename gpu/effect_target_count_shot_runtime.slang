// Diagnostic trace owns ordinary unused query slots1..63, never query0.
#ifndef TCS_TRACE_CAPACITY
#define TCS_TRACE_CAPACITY 100U
#endif
#ifndef TCS_TRACE_AT
#define TCS_TRACE_AT(s,index) (tcsHead(s)+16+(index)*20)
#endif
static const uint TCS_CAPACITY=TCS_TRACE_CAPACITY;
uint tcsHead(inout Runtime s){return s.resourceOutput+P_QUERY_BASE+P_QUERY_WORDS;}
bool initializeTargetCountShotPlan(inout Runtime s)
{
    uint found=0,name=0;
    for(uint row=0;row<s.count;row++)if(definition_stat(s.inputBase,row)==TC_STAT)
    {found++;name=uint(definition_targetName(s.inputBase,row));}
    if(found!=1)return false;
    uint ordinary=0;
    for(uint step=0;step<commands[s.inputBase+2];step++)
    {
        uint at=s.inputBase+P_COMMAND_BASE+step*8;
        if(commands[at]==44)return false;
        if(commands[at]==2){ordinary++;if(commands[at+6]!=0)return false;}
    }
    if(ordinary!=1)return false;
    uint head=tcsHead(s);for(uint i=0;i<2016;i++)results[head+i]=0;
    results[head]=0x54435331U;results[head+1]=1;results[head+3]=name;results[head+4]=5;results[head+5]=128;return true;
}
struct TargetCountShotState
{uint capacity,remaining,skipped,present;uint64_t total,activated;};
TargetCountShotState targetCountShotState(inout Runtime s,uint who,uint64_t when)
{
    TargetCountShotState value={};uint name=results[tcsHead(s)+3];
    if(!namedTargetCountValue(s,who,name,5,128,when,value.capacity,value.total)){s.error=64;return value;}
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];Definition d=residentDefinition(s,slot);
        if(d.stat!=TC_STAT||s.alive[slot]==0)continue;
        if(value.present!=0){s.error=64;return value;}
        value.present=1;value.activated=s.activated[slot];
        if(s.recipientBullets[slot*5+who]!=0)value.remaining=s.recipientBullets[slot*5+who];
        else if(d.owner==who&&s.bulletLeft[slot]>=0)value.remaining=uint(s.bulletLeft[slot]);
        value.skipped=uint(value.remaining!=0&&f64Equal(when,value.activated)&&d.bulletBound==0);
    }
    return value;
}
void targetCountShotBefore(inout Runtime s,uint who,uint64_t when,out uint capacity,out uint remaining,out uint skipped,out uint present,out uint64_t total,out uint64_t activated)
{
    if(results[tcsHead(s)+2]>=TCS_CAPACITY)s.error=64;
    TargetCountShotState v=targetCountShotState(s,who,when);capacity=v.capacity;remaining=v.remaining;skipped=v.skipped;present=v.present;total=v.total;activated=v.activated;
}
void targetCountShotAfter(inout Runtime s,uint who,uint64_t when,uint capacity,uint remaining,uint skipped,uint present,uint64_t total,uint64_t activated)
{
    if(s.error!=0)return;uint head=tcsHead(s),count=results[head+2];
    if(count>=TCS_CAPACITY){s.error=64;return;}
    TargetCountShotState after=targetCountShotState(s,who,when);if(s.error!=0)return;
    uint at=TCS_TRACE_AT(s,count);results[head+2]=count+1;
    results[at]=who;results[at+1]=remaining;storeNumber(at+2,when);results[at+4]=capacity;results[at+5]=after.capacity;
    storeNumber(at+6,total);storeNumber(at+8,after.total);results[at+10]=after.remaining;results[at+11]=skipped;
    results[at+12]=present;results[at+13]=after.present;storeNumber(at+14,activated);results[at+16]=after.skipped;results[at+17]=0;storeNumber(at+18,after.activated);
}
