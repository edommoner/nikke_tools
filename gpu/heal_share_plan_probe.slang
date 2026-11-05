#include "binary64.slang"
#include "heal_share_plan.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*520,output=id.x*786432;
    uint count=commands[input],original=commands[input+1];
    if(count>513 || original>=5) { results[output]=64;return; }
    uint64_t amount=uint64_t(commands[input+2])|(uint64_t(commands[input+3])<<32);
    HealShareLinks links={};
    for(uint row=0;row<count;row++) if(!addHealShareCarrier(links,commands[input+4+row]))
    { results[output]=64;return; }
    HealSharePlan outer=finishHealSharePlan(links,original);
    // An independent nested plan cannot overwrite the saved outer value.
    HealShareLinks nested={};addHealShareCarrier(nested,1U<<((original+1)%5));
    HealSharePlan child=finishHealSharePlan(nested,(original+1)%5);
    results[output]=0;results[output+1]=outer.total;results[output+2]=outer.members;
    results[output+3]=uint(outer.weights);results[output+4]=uint(outer.weights>>32);
    for(uint who=0;who<5;who++)
    {
        uint weight=healShareWeight(outer,who);results[output+5+who]=weight;
        uint64_t part=weight!=0 ? healSharePortion(outer,who,amount) : 0;
        results[output+10+who*2]=uint(part);results[output+11+who*2]=uint(part>>32);
    }
    results[output+20]=child.total;results[output+21]=child.members;
}
