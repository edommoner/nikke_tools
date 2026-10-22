#include "binary64.slang"
static const uint64_t HUNDRED=uint64_t(0x40590000)<<32;
#include "damage_factors.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint at=1+id.x*18,out=id.x*786432;
    uint64_t factors[9];
    for(uint i=0;i<9;i++)factors[i]=uint64_t(commands[at+2*i])|(uint64_t(commands[at+2*i+1])<<32);
    uint64_t main=damageFactorProduct(factors,false),part=damageFactorProduct(factors,true);
    results[out]=0;
    results[out+1]=uint(main);results[out+2]=uint(main>>32);
    results[out+3]=uint(part);results[out+4]=uint(part>>32);
}
