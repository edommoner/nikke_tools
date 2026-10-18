// Definition counters/timers keep their immutable row. Resident slots own only
// target membership, stack, activation time, expiry and captured HP quantities.
[noinline]
uint findCarrier(inout Runtime s, uint definition, uint recipients, uint64_t when)
{
    Definition incoming = s.defs[definition];
#ifndef PORTABLE_CARRIER_SCAN_REFERENCE
    // Most real definitions have one carrier and no compatible name aliases.
    // Avoid a growing resident scan on first activation and ordinary refresh.
    if (s.multiCarrier[definition] == 0)
    {
        bool primaryLive = s.alive[definition] != 0 && f64Less(when,s.end[definition]);
        if (primaryLive && s.activeRecipients[definition] == recipients) return definition;
        if (!primaryLive && (incoming.mergeEligible & 2) == 0) return definition;
    }
#endif
    uint merged = P_CARRIERS;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint slot = s.orderedRows[pass]; Definition prior = residentDefinition(s,slot);
        if (s.alive[slot] == 0 || !f64Less(when,s.end[slot]) || s.activeRecipients[slot] != recipients) continue;
        if (s.carrierDefinition[slot] == definition) return slot;
        if (merged == P_CARRIERS && (incoming.mergeEligible & 1) != 0 && (prior.mergeEligible & 1) != 0 && incoming.name == prior.name &&
            incoming.owner == prior.owner && incoming.kind == prior.kind && incoming.statKey == prior.statKey && incoming.maxStack == prior.maxStack) merged = slot;
    }
    if (merged != P_CARRIERS) return merged;
    if (s.alive[definition] == 0 || !f64Less(when,s.end[definition])) return definition;
    for (uint slot = s.count; slot < s.carrierCount; slot++)
        if (s.alive[slot] == 0 || !f64Less(when,s.end[slot]))
        { s.carrierDefinition[slot] = definition; s.multiCarrier[definition] = 1; return slot; }
    if (s.carrierCount == P_CARRIERS) { s.error = 64; return definition; }
    uint slot = s.carrierCount++; s.carrierDefinition[slot] = definition; s.multiCarrier[definition] = 1; return slot;
}

void queueCarrierEnd(inout Runtime s, uint slot)
{
    Definition d = residentDefinition(s,slot);
    s.alive[slot] = 0; s.stacks[slot] = 0;
    if (s.removalCount == P_CARRIERS) { s.error = 64; return; }
    // Capture the notification payload before callbacks can recycle this slot.
    s.removalQueue[s.removalCount++] = d.owner | (d.name << 3);
}
