// Capacity/transport proof for the exact production notice functions.
#include "event_runtime.slang"
[shader("compute")]
[numthreads(1,1,1)]
void removalQueueProbe(uint3 thread : SV_DispatchThreadID)
{
    uint id=thread.x;if(id>=commands[0]) return;
    uint mode=commands[1+id*4],output=id*P_OUTPUT_WORDS;
    Runtime s;s.resourceOutput=output;s.removalCount=0;s.error=0;
    for(uint i=0;i<P_REMOVALS/2;i++) results[output+P_REMOVAL_QUEUE_BASE+i]=0;
    if(mode<=1)
    {
        for(uint i=0;i<512;i++) queueRemovalNotice(s,i%5,i%256,8);
        if(mode==1) queueRemovalNotice(s,4,255,1);
    }
    else if(mode==2) queueRemovalNotice(s,4,0xffffffff,8);
    else if(mode==3) queueRemovalNotice(s,4,255,9);
    else { queueRemovalNotice(s,4,255,1);queueRemovalNotice(s,0,0,1); }
    uint sum=0;for(uint i=0;i<s.removalCount;i++) sum+=loadRemovalNotice(s,i);
    results[output]=s.error;results[output+1]=s.removalCount;results[output+2]=sum;
    results[output+3]=s.removalCount!=0 ? loadRemovalNotice(s,0) : 0;
    results[output+4]=s.removalCount!=0 ? loadRemovalNotice(s,s.removalCount-1) : 0;
}
