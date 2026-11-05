StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
#include "incoming_weighted_allocation.slang"
uint64_t weightedNumber(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
void weightedStore(uint at,uint64_t value){results[at]=uint(value);results[at+1]=uint(value>>32);}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint at=1+id.x*16,outAt=id.x*20;
    for(uint i=0;i<20;i++)results[outAt+i]=0;
    uint mask=commands[at+2],caster=commands[at+3],cover=commands[at+12];
    uint64_t amount=weightedNumber(at+4),selfWeight=weightedNumber(at+6),otherWeight=weightedNumber(at+8),coverWeight=weightedNumber(at+10);
    bool valid=commands[at]==0x57414c31U&&commands[at+1]==1&&mask>0&&mask<=31&&caster<5&&cover<=1;
    valid=valid&&commands[at+13]==0&&commands[at+14]==0&&commands[at+15]==0;
    valid=valid&&(cover==0||((mask&(1U<<caster))!=0));
    valid=valid&&f64Finite(amount)&&!f64Less(amount,0);
    valid=valid&&f64Finite(selfWeight)&&f64Less(0,selfWeight)&&f64Finite(otherWeight)&&f64Less(0,otherWeight)&&f64Finite(coverWeight)&&f64Less(0,coverWeight);
    if(!valid){results[outAt]=64;return;}
    uint activeMask;uint64_t total,shares[6];
    uint status=incomingWeightedAllocation(mask,caster,cover!=0,amount,selfWeight,otherWeight,coverWeight,activeMask,total,shares);
    results[outAt+1]=0x57414c31U;results[outAt+2]=status;results[outAt+3]=activeMask;
    if(status!=0)return;
    weightedStore(outAt+4,total);
    for(uint who=0;who<6;who++)weightedStore(outAt+6+2*who,shares[who]);
}
