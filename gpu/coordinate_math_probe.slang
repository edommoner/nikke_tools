StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
#include "coordinate_math.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint at=1+id.x*8,outAt=id.x*8;for(uint i=0;i<8;i++)results[outAt+i]=0;
    if(commands[at]!=0x43484e31U||commands[at+1]!=1||commands[at+6]!=0||commands[at+7]!=0){results[outAt]=64;return;}
    uint64_t a=uint64_t(commands[at+2])|(uint64_t(commands[at+3])<<32),b=uint64_t(commands[at+4])|(uint64_t(commands[at+5])<<32);
    uint64_t value=coordinateHypot(a,b);results[outAt+1]=0x43484e31U;results[outAt+2]=uint(value);results[outAt+3]=uint(value>>32);
}
