StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
static const uint64_t HUNDRED=uint64_t(0x40590000)<<32;
#include "ammo_instant_numeric.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint at=1+id.x*16,outAt=id.x*8;
    for(uint i=0;i<8;i++)results[outAt+i]=0;
    uint kind=commands[at+2],capacity=commands[at+3];int current=int(commands[at+4]);
    uint64_t value=uint64_t(commands[at+6])|(uint64_t(commands[at+7])<<32);
    bool valid=commands[at]==0x414e5531U&&commands[at+1]==1&&(kind==13||kind==14)&&capacity>0&&capacity<=0x7fffffffU&&current<=int(capacity)&&commands[at+5]==0&&f64Finite(value);
    for(uint i=8;i<16;i++)valid=valid&&commands[at+i]==0;
    if(!valid){results[outAt]=64;return;}
    int64_t flat;uint64_t fraction;int result;
    results[outAt+1]=0x414e5531U;
    if(!prepareAmmoInstant(kind,value,flat,fraction)||!ammoInstantResult(kind,capacity,current,flat,fraction,result)){results[outAt+2]=16;return;}
    results[outAt+3]=uint(result);
}
