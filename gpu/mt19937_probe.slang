RWStructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "portable_mt19937.slang"
[shader("compute")]
[numthreads(1,1,1)]
void mtProbe(uint3 id:SV_DispatchThreadID)
{
    uint input=1+id.x*1032,output=id.x*4096;
    if(id.x>=commands[0]) return;
    for(uint i=0;i<4096;i++) results[output+i]=0;
    uint count=commands[input+3],rng=output+3072;
    if(commands[input]!=0x4d543031 || count>1024) { results[output]=64;return; }
    for(uint i=4;i<8;i++) if(commands[input+i]!=0) { results[output]=64;return; }
    for(uint i=0;i<count;i++)
    {
        uint op=commands[input+8+i],kind=op>>24,arg=op&0xffffff;
        if(kind==0 && arg>32 || kind==1 && (arg==0 || arg>5) || kind==2 && (arg>>8>5 || (arg&255)>(arg>>8)) || kind>2)
        { results[output]=64;return; }
    }
    mtSeed(rng,uint64_t(commands[input+1])|(uint64_t(commands[input+2])<<32));
    for(uint i=0;i<count;i++)
    {
        uint op=commands[input+8+i],kind=op>>24,arg=op&0xffffff,value,mask=0;
        if(kind==0) value=mtBits(rng,arg);
        else if(kind==1) value=mtBelow(rng,arg);
        else value=mtSampleFive(rng,arg>>8,arg&255,mask);
        results[output+4+i*2]=value;results[output+5+i*2]=mask;
    }
    results[output+1]=count;results[output+2]=results[rng+1];results[output+3]=results[rng+3];
}
