#include "binary64.slang"
#include "stack_numeric.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
[shader("compute")]
[numthreads(1,1,1)]
void stackNumericProbe(uint3 thread : SV_DispatchThreadID)
{
    uint id=thread.x;if(id>=commands[0]) return;
    uint at=1+id*8,status;
    uint64_t current=uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);
    uint64_t value=uint64_t(commands[at+2])|(uint64_t(commands[at+3])<<32);
    uint result;
    if(commands[at+7]==0) result=checkedStackChange(current,value,commands[at+4],commands[at+5],commands[at+6],status);
    else
    {
        uint conversion;uint64_t integer=f64ToI64(current,1,conversion);
        if(conversion!=0 || integer>0xffffffff || !f64Equal(current,f64FromI64(integer))) { result=0;status=64; }
        else result=checkedStackIncrement(uint(integer),commands[at+4],status);
    }
    results[id*2]=result;results[id*2+1]=status;
}
