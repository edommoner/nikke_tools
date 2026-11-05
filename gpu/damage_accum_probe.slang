#define PORTABLE_RESIDENT_RUNTIME
#include "binary64.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
// The state-operation probe owns only its monotonic activation sequence here.
// Production Runtime remains unchanged; pool storage is the24-word arena.
struct Runtime { uint64_t nextOrder; };
RWStructuredBuffer<Runtime> runtimeStates;
uint nextProbeOrder(uint id)
{
    uint64_t next=runtimeStates[id].nextOrder+1;
    runtimeStates[id].nextOrder=next;return uint(next);
}
#include "damage_accum_core.slang"
uint64_t probeNumber(uint at) { return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32); }
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*512,output=id.x*786432,base=output+16,header=output+8,status=0;
    runtimeStates[id.x].nextOrder=0;
    uint capacity=commands[input],count=commands[input+1];
    if(capacity==0 || capacity>32 || count>24) { results[output]=64;return; }
    results[header]=0;results[header+1]=0;
    for(uint i=0;i<32*24;i++) results[base+i]=0;
    for(uint step=0;step<count && status==0;step++)
    {
        uint at=input+2+step*20,op=commands[at],logical=commands[at+1],object=DA_NONE;
        uint answer=output+1024+step*32;results[answer]=op;
        for(uint i=0;i<capacity;i++) { uint p=daAt(base,i),flags=results[p+22];if((flags&DA_ACTIVE)!=0 && results[p+6]==logical) { object=i;break; } }
        if(op==0 || op==1)
        {
            if(object==DA_NONE) object=daFree(base,capacity);
            if(object==DA_NONE) { status=64;break; }
            uint p=daAt(base,object);
            if(op==0) daInitializePool(base,capacity,header,object,commands[at+3],commands[at+4],commands[at+2],nextProbeOrder(id.x),logical,probeNumber(at+5),status);
            else
            {
                daInitializeRate(base,capacity,header,object,commands[at+3],commands[at+4],nextProbeOrder(id.x),commands[at+2],probeNumber(at+5),commands[at+7],probeNumber(at+9),status);
            }
            results[p+6]=logical;
        }
        else if(op==2)
        {
            uint queue=output+3072,full=daCollect(base,capacity,header,logical,probeNumber(at+5),queue,8,status);
            results[answer+5]=full;
            for(uint i=0;i<full;i++) { results[answer+6+i*2]=results[queue+i*2];results[answer+7+i*2]=results[queue+i*2+1]; }
            uint done=0;for(uint i=0;i<capacity;i++) { uint p=daAt(base,i);if(daPool(results[p+22]) && (results[p+22]&DA_DONE)!=0) done|=1U<<results[p+6]; }
            results[answer+22]=done;
        }
        else if(op==3)
        {
            uint64_t amount=daTake(base,capacity,header,commands[at+3],status);daStore(answer+2,amount);
            bool emit;uint convert;uint64_t integer=daEmission(amount,probeNumber(at+5),emit,convert);
            if(status==0) status=convert;results[answer+4]=uint(emit);daStore(answer+24,integer);
        }
        else if(op==4) { if(object==DA_NONE) status=64;else daRetire(base,header,object); }
        else if(op==5)
        {
            if(object==DA_NONE) status=64;
            else { uint64_t rate=daRate(base,capacity,header,object,status);daStore(answer+2,rate); }
        }
        else if(op==6) daUpdateOwnerHP(base,capacity,logical,probeNumber(at+5),status);
        else status=64;
        results[answer+1]=status;
    }
    // Standard CLI rejection header; retain the exact core error separately.
    results[output]=status==0 ? 0 : 64;results[output+1]=count;results[output+2]=status;
}
