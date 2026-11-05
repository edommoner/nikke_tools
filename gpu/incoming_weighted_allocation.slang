// Frozen recipient allocation only. Carrier selection and protection stay callers.
// Six receivers: five original bodies, then the caster's independent cover.
uint incomingWeightedAllocation(uint bodyMask,uint caster,bool coverActive,
    uint64_t amount,uint64_t casterWeight,uint64_t otherWeight,uint64_t coverWeight,
    out uint activeMask,out uint64_t total,out uint64_t shares[6])
{
    activeMask=bodyMask|(coverActive?32U:0U);total=0;
    for(uint who=0;who<6;who++)shares[who]=0;
    for(uint who=0;who<6;who++)
    {
        uint64_t weight=who==5?coverWeight:(who==caster?casterWeight:otherWeight);
        if((activeMask&(1U<<who))!=0)total=f64Add(total,weight);
    }
    if(!f64Finite(total))return 16;
    for(uint who=0;who<6;who++)
    {
        uint64_t weight=who==5?coverWeight:(who==caster?casterWeight:otherWeight);
        if((activeMask&(1U<<who))!=0)shares[who]=f64Mul(amount,f64Div(weight,total));
        if(!f64Finite(shares[who]))return 16;
    }
    return 0;
}
