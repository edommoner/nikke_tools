// Typed kind9 reuses the common carrier/object pool. hpSnapshot is disjoint
// for stat74 and retains the prior storage expiry across a carrier refresh.
static const uint STORAGE_PENDING=262144;
bool healingStorageEnabled(inout Runtime s)
{ return (commands[s.inputBase+P_PROTECTION_META_BASE]&32U)!=0; }

[noinline]
void buildHealingStorage(inout Runtime s,uint slot,uint64_t when)
{
    Definition d=residentDefinition(s,slot);
    uint64_t capacity=larger(0,f64Div(f64Mul(effectiveMaxHP(s,d.owner,when),scalarValue(s,slot,d.owner)),HUNDRED));
    if(!f64Finite(capacity)) { s.error=16;return; }
    uint previous=protectionObject(s,slot),mask=s.activeRecipients[slot]&31;
    uint scratch=s.resourceOutput+P_PROTECTION_BUILD_BASE;
    for(uint who=0;who<5;who++)
    {
        uint64_t current=0;
        if(previous!=PROTECTION_NONE && f64Less(when,s.hpSnapshot[slot]))
        {
            uint at=protectionAddress(s,previous);
            if((results[at+23]&(1U<<who))!=0) current=protectionNumber(at+who*4);
        }
        storeNumber(scratch+who*2,(mask&(1U<<who))!=0 ? smaller(larger(0,current),capacity) : 0);
    }
    uint object=allocateProtection(s,slot,9U|(d.owner<<10));if(s.error!=0) return;
    uint at=protectionAddress(s,object);
    for(uint who=0;who<5;who++)
    {
        storeNumber(at+who*4,protectionNumber(scratch+who*2));
        storeNumber(at+who*4+2,(mask&(1U<<who))!=0 ? capacity : 0);
        storeNumber(scratch+who*2,0);
    }
    results[at+23]=mask;s.hpSnapshot[slot]=s.end[slot];
}

[noinline]
uint64_t transferHealingStorage(inout Runtime s,uint who,uint64_t amount,uint64_t when,bool fill)
{
    uint64_t remaining=larger(0,amount);
    if(!healingStorageEnabled(s) || (s.downMask&(1U<<who))!=0) return remaining;
    bool query=needsBuffResolution(s)&&beginBuffQuery(s,who,when);
    // Native slots() resolves/snapshots every live object before transfer, even
    // with zero excess or when an earlier object can consume the whole amount.
    for(uint pass=0;pass<s.orderedCount && s.error==0;pass++)
    {
        uint slot=s.orderedRows[pass];
        if(definition_stat(s.inputBase,s.carrierDefinition[slot])!=S_heal_overcharge_store || !queryRecipient(s,slot,who,when)) continue;
        uint object=protectionObject(s,slot);
        if(object==PROTECTION_NONE || (results[protectionAddress(s,object)+22]&STORAGE_PENDING)!=0) buildHealingStorage(s,slot,when);
    }
    uint64_t ceiling=F64_INF;uint lowerOrder=0;
    for(uint iteration=0;iteration<P_CARRIERS && s.error==0;iteration++)
    {
        uint selected=PROTECTION_NONE,bestOrder=0;uint64_t latest=0;
        for(uint pass=0;pass<s.orderedCount;pass++)
        {
            uint slot=s.orderedRows[pass],object=protectionObject(s,slot);
            if(object==PROTECTION_NONE || definition_stat(s.inputBase,s.carrierDefinition[slot])!=S_heal_overcharge_store || !queryRecipient(s,slot,who,when)) continue;
            uint at=protectionAddress(s,object);if((results[at+22]&255)!=9 || (results[at+23]&(1U<<who))==0) continue;
            uint order=s.entryOrder[slot];uint64_t time=s.activated[slot];
            if(f64Less(ceiling,time) || f64Equal(time,ceiling)&&order<=lowerOrder) continue;
            if(selected==PROTECTION_NONE || f64Less(latest,time) || f64Equal(latest,time)&&order<bestOrder)
            { selected=object;latest=time;bestOrder=order; }
        }
        if(selected==PROTECTION_NONE) break;
        ceiling=latest;lowerOrder=bestOrder;uint at=protectionAddress(s,selected)+who*4;
        uint64_t current=protectionNumber(at),available=fill ? larger(0,f64Add(protectionNumber(at+2),current^F64_SIGN)) : current;
        uint64_t transferred=smaller(remaining,available);
        storeNumber(at,fill ? f64Add(current,transferred) : f64Add(current,transferred^F64_SIGN));
        remaining=f64Add(remaining,transferred^F64_SIGN);
    }
    if(query) s.queryActive=0;
    return remaining;
}

[noinline]
uint64_t storageBodyHeal(inout Runtime s,uint who,uint64_t amount,uint64_t when)
{
    uint64_t maximum=effectiveMaxHP(s,who,when),next=f64Add(s.hp[who],amount);
    if(f64Less(0,amount)) transferHealingStorage(s,who,larger(0,f64Add(next,maximum^F64_SIGN)),when,true);
    return smaller(next,maximum);
}

[noinline]
uint64_t storageBodyReduce(inout Runtime s,uint who,uint64_t value,uint64_t when)
{
    uint64_t old=s.hp[who],after=larger(0,f64Mul(old,f64Add(ONE,f64Div(value,HUNDRED)^F64_SIGN)));
    if(!healingStorageEnabled(s) || !f64Less(after,old)) return after;
    uint64_t amount=f64Add(old,after^F64_SIGN),remaining=transferHealingStorage(s,who,amount,when,false);
    return f64Add(after,f64Add(amount,remaining^F64_SIGN));
}
