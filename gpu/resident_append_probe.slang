// Real shared functions and Runtime; no battle or duplicate append executor.
#define PORTABLE_RESIDENT_APPEND_PROBE
#define PORTABLE_RESIDENT_RUNTIME
#include "event_runtime.slang"

[noinline]
void residentAppendProbe(inout Runtime s,uint input,uint output)
{
    initializeRuntime(s);s.inputBase=input;s.resourceOutput=output;
    uint op=commands[input],prefill=commands[input+2],refresh=commands[input+3];
    s.count=commands[input+1];s.carrierCount=512;s.entryClock=prefill;
    s.hpDirtyMask=0x53a09b7eU;s.hpPendingMask=0x6409ae12U;s.enemyCaptureGeneration[0]=0xa5a5a5a5U;
    for(uint i=0;i<512;i++)
    { s.enemyBuffRows[i]=0xffffffffU;s.infiniteRows[i]=0xffffffffU;s.orderedRows[i]=0xffffffffU; }
    for(uint i=0;i<2048;i++)s.hpWatchSlots[i]=0xffffffffU;
    if(op==1||op==2)
    {
        s.orderedCount=prefill;
        if(op==1)s.enemyBuffCount=prefill;else s.infiniteRowCount=prefill;
        for(uint i=0;i<prefill;i++)
        {
            uint row=refresh!=0?0:i+1;s.orderedRows[i]=row;
            if(op==1)s.enemyBuffRows[i]=row;else s.infiniteRows[i]=row;
        }
        markEntry(s,0);
    }
    if(op==3||op==4)initializeHPWatches(s);
    for(uint i=0;i<32;i++)results[output+i]=0;
    results[output]=s.error;results[output+1]=0x41505031U;
    results[output+2]=s.enemyBuffCount;results[output+3]=s.infiniteRowCount;
    results[output+4]=s.hpWatchCount;results[output+5]=s.orderedCount;results[output+6]=s.entryClock;
    results[output+7]=s.hpDirtyMask;results[output+8]=s.hpPendingMask;results[output+9]=s.enemyCaptureGeneration[0];
    for(uint i=0;i<512;i++)
    { results[output+32+i]=s.enemyBuffRows[i];results[output+544+i]=s.infiniteRows[i];results[output+1056+i]=s.orderedRows[i]; }
    for(uint i=0;i<2048;i++)results[output+1568+i]=s.hpWatchSlots[i];
}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    residentAppendProbe(runtimeStates[id.x],1+id.x*115680,id.x*3616);
}
