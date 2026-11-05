// A standalone numeric probe must not depend on unrelated battle source/cache keys.
#include "binary64.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "packet_integer_sum.slang"
#include "packet_integer_ratio.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*8,output=id.x*8;for(uint i=0;i<8;i++)results[output+i]=0;
    uint divisor=commands[input+6];
    if(commands[input]!=0x50525631U||commands[input+1]!=1||commands[input+7]!=0){results[output]=64;return;}
    PacketIntegerSum n;n.low=uint64_t(commands[input+2])|(uint64_t(commands[input+3])<<32);n.high=uint64_t(commands[input+4])|(uint64_t(commands[input+5])<<32);
    uint status;uint64_t value=packetIntegerRatio(n,divisor,status);
    if(status!=0){results[output]=64;return;}
    results[output+1]=0x50525631U;results[output+2]=divisor;results[output+4]=uint(value);results[output+5]=uint(value>>32);
}
