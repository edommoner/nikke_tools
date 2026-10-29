StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
#include "incoming_damage_numeric.slang"
uint64_t coverProbeNumber(uint at) { return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32); }
void coverProbeStore(uint at,uint64_t x) { results[at]=uint(x);results[at+1]=uint(x>>32); }
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint at=1+id.x*16,outAt=id.x*12;
    for(uint i=0;i<12;i++)results[outAt+i]=0;
    uint64_t attack=coverProbeNumber(at+4),coefficient=coverProbeNumber(at+6),base=coverProbeNumber(at+8);
    uint64_t percent=coverProbeNumber(at+10),received=coverProbeNumber(at+12),body=coverProbeNumber(at+14);
    bool valid=commands[at]==0x43444631U&&commands[at+1]==1&&commands[at+2]==0&&commands[at+3]==0;
    valid=valid&&f64Finite(attack)&&f64Finite(coefficient)&&f64Finite(base)&&f64Finite(percent)&&f64Finite(received)&&f64Finite(body);
    valid=valid&&!f64Less(attack,0)&&!f64Less(coefficient,0)&&!f64Less(base,0);
    if(!valid){results[outAt]=64;return;}
    results[outAt+1]=0x43444631U;
    uint64_t effective=incomingDefensePercentage(base,percent);
    uint64_t covered=incomingDefendedQuantity(attack,coefficient,effective,received);
    uint64_t uncovered=incomingDefendedQuantity(attack,coefficient,body,received);
    if(!f64Finite(effective)||!f64Finite(covered)||!f64Finite(uncovered)){results[outAt+2]=16;return;}
    coverProbeStore(outAt+4,effective);coverProbeStore(outAt+6,covered);coverProbeStore(outAt+8,uncovered);
}
