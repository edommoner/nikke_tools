// Return a scalar value before carrierCount changes on either backend.
[noinline]
uint carrierCountBeforeAllocate(inout Runtime s)
{
    return s.carrierCount;
}

// Definition counters/timers keep their immutable row. Resident slots own only
// target membership, stack, activation time, expiry and captured HP quantities.
[noinline]
uint findCarrier(inout Runtime s, uint definition, uint recipients, uint64_t when,uint incomingGeneration,uint64_t incomingOrder)
{
    Definition incoming = readDefinition(s.inputBase,definition);
    bool ordered=(commands[s.inputBase+P_RECIPIENT_META_BASE]!=0 || commands[s.inputBase+P_RECIPIENT_META_BASE+1]!=0 || alliedRandomEnabled(s)) && incoming.enemyBuff==0 && incoming.lazyGroup==0 && incoming.bulletDuration==0;
#ifndef PORTABLE_CARRIER_SCAN_REFERENCE
    // Most real definitions have one carrier and no compatible name aliases.
    // Avoid a growing resident scan on first activation and ordinary refresh.
    if (incoming.enemyBuff == 0 && s.multiCarrier[definition] == 0)
    {
        bool primaryLive = s.alive[definition] != 0;
        if (primaryLive && (incoming.bulletDuration != 0 || incoming.lazyGroup != 0 || s.lazyPending[definition] == 0 && s.activeRecipients[definition] == recipients && (!ordered || visibleCarrierOrder(s,definition)==incomingOrder))) return definition;
        if (!primaryLive && s.lazyPending[definition]==0 && (incoming.mergeEligible & 2) == 0) return definition;
    }
#endif
    uint merged = P_CARRIERS;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint slot = s.orderedRows[pass]; Definition prior = residentDefinition(s,slot);
        if (s.alive[slot] == 0) continue;
        bool same = incoming.bulletDuration != 0 && s.carrierDefinition[slot] == definition ? true : incoming.lazyGroup != 0 ? prior.lazyGroup == incoming.lazyGroup : s.lazyPending[slot] == 0 && s.activeRecipients[slot] == recipients;
        if (incoming.enemyBuff != prior.enemyBuff || incoming.enemyBuff != 0 && !enemyCarrierSameLife(s,slot,recipients,incomingGeneration)) same = false;
        if(ordered && visibleCarrierOrder(s,slot)!=incomingOrder) same=false;
        if (!same) continue;
        if (s.carrierDefinition[slot] == definition) return slot;
        if (!f64Less(when,s.end[slot])) continue;
        if (merged == P_CARRIERS && (referenceCaptureFlags(s,slot)&4)==0 && (incoming.mergeEligible & 1) != 0 && (prior.mergeEligible & 1) != 0 && incoming.name == prior.name &&
            incoming.owner == prior.owner && incoming.kind == prior.kind && incoming.statKey == prior.statKey && incoming.maxStack == prior.maxStack) merged = slot;
    }
    if (merged != P_CARRIERS) return merged;
    if (s.alive[definition] == 0 && s.lazyPending[definition] == 0) return definition;
    for (uint slot = s.count; slot < s.carrierCount; slot++)
        if (s.alive[slot] == 0 && s.lazyPending[slot] == 0)
        { resetBulletCarrier(s,slot); discardLazy(s,slot); s.carrierDefinition[slot] = definition; s.multiCarrier[definition] = 1; return slot; }
    if (s.carrierCount == P_CARRIERS) { s.error = 64; return definition; }
    uint slot = carrierCountBeforeAllocate(s); s.carrierCount = slot+1; s.carrierDefinition[slot] = definition; s.multiCarrier[definition] = 1; return slot;
}

// One GPU-owned LIFO reservation pool for end/stack notices. Compact metadata
// retains its old two-per-word layout; a parallel uint plane snapshots stacks.
[noinline]
uint loadRemovalNotice(inout Runtime s,uint index)
{
    uint at=s.resourceOutput+P_REMOVAL_QUEUE_BASE+index/2;
    return (results[at]>>((index&1)*16))&65535;
}
[noinline]
uint loadStackNoticeValue(inout Runtime s,uint index)
{ return results[s.resourceOutput+P_STACK_NOTICE_VALUE_BASE+index]; }
[noinline]
void queueStackNotice(inout Runtime s,uint owner,uint name,uint stack)
{
    if(name>=P_DEFINITIONS) return;
    if(owner>=5 || stack>0x7fffffff || s.removalCount==P_REMOVALS) { s.error=64;return; }
    uint index=s.removalCount++,at=s.resourceOutput+P_REMOVAL_QUEUE_BASE+index/2,shift=(index&1)*16;
    results[at]=(results[at]&~(65535U<<shift))|((owner|(name<<3)|32768U)<<shift);
    results[s.resourceOutput+P_STACK_NOTICE_VALUE_BASE+index]=stack;
}
[noinline]
void queueRemovalNotice(inout Runtime s,uint owner,uint name,uint repeats=1)
{
    if(name>=P_DEFINITIONS || repeats==0) return;
    if(repeats>8 || s.removalCount>P_REMOVALS-repeats) { s.error=64;return; }
    for(uint i=0;i<repeats;i++)
    {
        uint index=s.removalCount++,at=s.resourceOutput+P_REMOVAL_QUEUE_BASE+index/2,shift=(index&1)*16;
        results[at]=(results[at]&~(65535U<<shift))|((owner|(name<<3))<<shift);
        results[s.resourceOutput+P_STACK_NOTICE_VALUE_BASE+index]=0;
    }
}
[noinline]
void queueCarrierEnd(inout Runtime s,uint slot,uint repeats=0,bool preserveLazy=false)
{
    uint definition=s.carrierDefinition[slot];
    if(repeats==0) repeats=WORLD_STATE_END_REPEATS(s,slot,definition_enemyBuff(s.inputBase,definition)!=0 && s.bulletInitialized[slot]!=2 ? countbits(s.activeRecipients[slot]>>5) : 1);
    invalidateFocusNumeric(s);
    unlinkBulletCarrier(s,slot);
    if(!preserveLazy) { discardLazy(s,slot);s.stacks[slot]=0; }
#ifdef PORTABLE_HEAL_CHARGE
    retainHealChargeEnd(s,slot);
#endif
    s.alive[slot]=0;
    queueRemovalNotice(s,definition_owner(s.inputBase,definition),definition_name(s.inputBase,definition),repeats);
}

// Native HP-copy expiration caps only after its state-end children finish.
void queueHealthCapNotice(inout Runtime s,uint mask)
{
    if(mask==0) return;
    if(s.removalCount==P_REMOVALS) { s.error=64;return; }
    uint index=s.removalCount++,at=s.resourceOutput+P_REMOVAL_QUEUE_BASE+index/2,shift=(index&1)*16;
    results[at]=(results[at]&~(65535U<<shift))|(16384U<<shift);
    results[s.resourceOutput+P_STACK_NOTICE_VALUE_BASE+index]=mask;
}
