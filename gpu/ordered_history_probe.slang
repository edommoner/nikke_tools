StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "ordered_history_runtime.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*4,out=id.x*786432,prefix=out+8,head=out+2048;
    uint count=commands[input],seed=commands[input+1],enabled=commands[input+2],badKind=commands[input+3];
    if(count>OH_MAX || enabled>1 || badKind>1) { results[out]=64;return; }
    for(uint i=0;i<count;i++)
    {
        uint at=orderedHistoryRecordAt(prefix,head,i,enabled!=0);
        if(at==0xffffffffU) { results[out]=64;return; }
        for(uint j=0;j<8;j++) results[at+j]=seed^(i*0x9e3779b9U+j*0x85ebca6bU);
        results[at]=badKind!=0 ? 4 : 1+i%3;
        if(!orderedHistoryRecordDone(head,i,at)) { results[out]=64;return; }
    }
    if(!finishOrderedHistory(head,count)) results[out]=64;
}
