#define PORTABLE_RESIDENT_RUNTIME
#include "binary64.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
struct Runtime { uint64_t steps; };
RWStructuredBuffer<Runtime> runtimeStates;
#include "destructible_target_core.slang"
uint64_t dtInput(uint at) { return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32); }
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*2048,output=id.x*786432,base=output+16,status=0,count=commands[input],steps=commands[input+1];
    runtimeStates[id.x].steps=0;
    if(count==0||count>128||steps>32) { results[output]=64;results[output+2]=64;return; }
    for(uint i=2+steps*32;i<2048;i++) if(commands[input+i]!=0) { results[output]=64;results[output+2]=64;return; }
    for(uint i=0;i<128*DT_WORDS;i++) results[base+i]=0;
    uint64_t previous=0;
    for(uint step=0;step<steps&&status==0;step++)
    {
        uint at=input+2+step*32,op=commands[at],slot=commands[at+1],kind=commands[at+2],identity=commands[at+3],generation=commands[at+4];
        uint answer=output+2048+step*1824;results[answer]=op;
        for(uint word=15;word<32;word++) if(commands[at+word]!=0) status=64;
        if(status!=0) break;
        uint64_t when=dtInput(at+5);dtAdvance(base,count,when,previous,status);if(status!=0) break;previous=when;
        if(op==0) dtSpawn(base,count,slot,kind,identity,generation,dtInput(at+7),dtInput(at+9),commands[at+11],commands[at+12],commands[at+13],when,status);
        else if(op==1)
        { bool delivered,broken;uint64_t took=dtHit(base,count,slot,kind,identity,generation,commands[at+14],dtInput(at+7),dtInput(at+9),delivered,broken,status);results[answer+2]=uint(delivered);results[answer+3]=uint(broken);dtStore(answer+4,took); }
        else if(op==2) results[answer+2]=uint(dtRetire(base,count,slot,kind,identity,generation,status));
        else if(op==3) dtSelect(base,count,commands[at+14],answer+8,status);
        else status=64;
        results[answer+1]=status;
        for(uint i=0;i<count*DT_WORDS;i++) results[answer+32+i]=results[base+i];
        runtimeStates[id.x].steps++;
    }
    results[output]=status==0?0:64;results[output+1]=steps;results[output+2]=status;
}
