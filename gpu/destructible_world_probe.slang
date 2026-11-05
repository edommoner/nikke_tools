#define PORTABLE_RESIDENT_RUNTIME
#include "binary64.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
struct Runtime { uint64_t steps; };
RWStructuredBuffer<Runtime> runtimeStates;
#include "world_schedule.slang"
#include "destructible_target_core.slang"
#include "destructible_world_runtime.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*5120,output=id.x*786432,base=output+16384,header=output+18200;
    for(uint i=0;i<20000;i++) results[output+i]=0;
    runtimeStates[id.x].steps=0;
    WorldSchedule w;w.input=input;w.output=output+16;w.count=commands[input+1];w.error=0;
    uint bindings=input+2328,count=commands[input+2320],steps=commands[input+3864];uint64_t through=wsLoad(input+6);
    if(commands[input]!=0x57533031U||commands[input+2]!=0||commands[input+3]!=0||commands[input+4]!=0||commands[input+5]!=0||!f64Finite(through)||f64Less(through,0)||f64Less(f64FromI64(180),through)||steps>32||!wsValidate(w)) w.error=64;
    for(uint i=8;i<16;i++) if(commands[input+i]!=0) w.error=64;
    for(uint i=2064;i<2320;i++) if(commands[input+i]!=0) w.error=64;
    for(uint i=2321;i<2328;i++) if(commands[input+i]!=0) w.error=64;
    for(uint i=3865;i<3872;i++) if(commands[input+i]!=0) w.error=64;
    if(w.error==0&&!dwValidate(w,bindings,count,base)) w.error=64;
    if(steps<=32) for(uint i=3872+steps*32;i<5120;i++) if(commands[input+i]!=0) w.error=64;
    for(uint step=0;step<steps&&w.error==0;step++)
    {
        uint at=input+3872+step*32,op=commands[at],answer=output+20000+step*2640;uint64_t when=wsLoad(at+5);
        results[answer]=op;
        for(uint i=12;i<32;i++) if(commands[at+i]!=0) w.error=64;
        if(!f64Finite(when)||f64Less(through,when)||op>3) w.error=64;
        if(op!=1) for(uint i=1;i<5;i++) if(commands[at+i]!=0) w.error=64;
        if(op!=1) for(uint i=7;i<11;i++) if(commands[at+i]!=0) w.error=64;
        if(op!=1&&op!=2&&commands[at+11]!=0) w.error=64;
        if(w.error!=0) break;
        if(op==3) dwFinish(w,bindings,count,base,header,when);
        else results[answer+2]=uint(dwBegin(w,bindings,count,base,header,when));
        if(w.error==0&&op==1)
        {
            DWReceipt r=dwLand(w,base,count,header,commands[at+1],commands[at+2],commands[at+3],commands[at+4],commands[at+11],wsLoad(at+7),wsLoad(at+9),when);
            results[answer+3]=r.delivered;results[answer+4]=r.broken;dtStore(answer+5,r.took);results[answer+7]=r.ownerKind;results[answer+8]=r.ownerId;results[answer+9]=r.ownerGeneration;
            results[answer+10]=r.kind;results[answer+11]=r.identity;results[answer+12]=r.generation;dtStore(answer+13,r.when);
        }
        if(w.error==0&&op==2) { uint status;dtSelect(base,count,commands[at+11],answer+16,status);w.error=status; }
        results[answer+1]=w.error;results[answer+20]=results[header+3];results[answer+21]=results[w.output+1];results[answer+22]=results[w.output+2];
        for(uint i=0;i<128*DT_WORDS;i++) results[answer+32+i]=results[base+i];
        for(uint i=0;i<32*24;i++) results[answer+1824+i]=results[w.output+16+i];
        runtimeStates[id.x].steps++;
    }
    results[output]=w.error==0?0:64;results[output+1]=steps;results[output+2]=w.error;results[output+3]=count;
}
