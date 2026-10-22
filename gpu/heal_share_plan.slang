// Shared plan algebra. Callers sample each distinct live carrier exactly once
// in native order, then retain the resulting value through nested HP callbacks.
struct HealShareLinks
{
    uint adjacent[5];
    uint weights[5];
    uint carriers;
};
struct HealSharePlan
{
    uint64_t weights;
    uint total;
    uint members;
};
bool addHealShareCarrier(inout HealShareLinks links,uint mask)
{
    if(mask>31 || links.carriers>=512) return false;
    if(mask==0) return true;
    links.carriers++;
    for(uint who=0;who<5;who++) if((mask&(1U<<who))!=0)
    { links.adjacent[who]|=mask;links.weights[who]++; }
    return true;
}
HealSharePlan finishHealSharePlan(HealShareLinks links,uint original)
{
    HealSharePlan plan={};uint connected=1U<<original;
    for(uint pass=0;pass<5;pass++)
    {
        uint expanded=connected;
        for(uint who=0;who<5;who++) if((connected&(1U<<who))!=0) expanded|=links.adjacent[who];
        if(expanded==connected) break;
        connected=expanded;
    }
    for(uint who=0;who<5;who++) if((connected&(1U<<who))!=0 && links.weights[who]!=0)
    { plan.weights|=uint64_t(links.weights[who])<<(who*10);plan.total+=links.weights[who];plan.members++; }
    if(plan.members==0) { plan.weights=uint64_t(1)<<(original*10);plan.total=1;plan.members=1; }
    return plan;
}
uint healShareWeight(HealSharePlan plan,uint who)
{ return uint((plan.weights>>(who*10))&1023); }
uint64_t healSharePortion(HealSharePlan plan,uint who,uint64_t amount)
{
    if(plan.members==1) return amount;
    return f64Div(f64Mul(amount,f64FromI64(healShareWeight(plan,who))),f64FromI64(plan.total));
}
