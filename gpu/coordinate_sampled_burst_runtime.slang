// One exact binary64 amount per existing pending-entry/hit capacity.
void beginSampledPendingBatch(inout Runtime s,uint count,uint64_t when)
{
    if(count>CSB_ENTRIES){s.error=64;return;}
    uint h=s.resourceOutput+CSB_HEAD,previous=results[h];if(previous>CSB_ENTRIES){s.error=64;return;}
    for(uint i=0;i<previous*CSB_HITS*2;i++)results[s.resourceOutput+CSB_BASE+i]=0;
    results[h]=count;if(count!=0)storeNumber(h+1,when);results[h+3]=0;
}
uint64_t sampledPendingAmount(inout Runtime s,uint index,uint hit)
{
    if(index>=CSB_ENTRIES||hit>=CSB_HITS){s.error=64;return 0;}
    return actorNumber(s.resourceOutput+CSB_BASE+(index*CSB_HITS+hit)*2);
}
// First query stays beside its exclusion setter in the shared caller.
// Generated CUDA/MSL dropped that setter across the prior helper boundary.
void storeSampledPendingAmounts(inout Runtime s,uint index,Definition d,uint64_t amount)
{
    uint64_t part=0,interrupt=0,critical=0;
    for(uint hit=0;hit<s.pendingHits[index]&&s.error==0;hit++)
    {
        if(hit!=0)resampleSkillFrame(s,0,d._wireRow,amount,part,interrupt,critical);
        if(index>=CSB_ENTRIES||hit>=CSB_HITS){s.error=64;return;}
        storeNumber(s.resourceOutput+CSB_BASE+(index*CSB_HITS+hit)*2,amount);results[s.resourceOutput+CSB_HEAD+3]++;
    }
}
