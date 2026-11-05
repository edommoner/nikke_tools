RWStructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
#include "packet_integer_sum.slang"
#include "coordinate_round_key.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;uint input=1+id.x*4,output=id.x*6;
    for(uint i=0;i<6;i++)results[output+i]=0;
    uint64_t value=uint64_t(commands[input])|(uint64_t(commands[input+1])<<32);uint status;
    uint64_t rounded=coordinateRoundSix(value,status);
    if(status!=0||commands[input+2]!=0||commands[input+3]!=0){results[output]=64;return;}
    uint64_t key=f64Zero(rounded)?uint64_t(0):rounded;
    results[output+1]=uint(rounded);results[output+2]=uint(rounded>>32);
    results[output+3]=uint(key);results[output+4]=uint(key>>32);results[output+5]=0x43523631U;
}
