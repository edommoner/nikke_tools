// Body-layer attacks. Boss scheduling, target choice and protection layers
// will feed this same boundary; they are not synthesized by the CPU adapter.
bool liveMarker(inout Runtime s, uint who, uint stat, uint64_t when)
{
#ifndef PORTABLE_INCOMING_SCAN_REFERENCE
    uint bit = stat == S_invincible ? 1 : 2;
    if ((s.incomingMask & bit) == 0) return false;
#endif
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass];
        if (s.defs[row].kind == 0 && s.defs[row].stat == stat && liveRecipient(s,row,who,when)) return true;
    }
    return false;
}
[noinline]
uint64_t incomingBodyDamage(inout Runtime s, uint who, uint64_t attack, uint64_t coefficient, uint64_t when)
{
    uint64_t amount = larger(0,f64Add(attack,effectiveDefense(s,who,when) ^ F64_SIGN));
    amount = f64Div(f64Mul(amount,coefficient),HUNDRED);
    uint64_t received = 0;
#ifdef PORTABLE_INCOMING_SCAN_REFERENCE
    received = plainQuantity(s,who,S_received_dmg_pct,when);
#else
    if ((s.incomingMask & 4) != 0) received = plainQuantity(s,who,S_received_dmg_pct,when);
#endif
    amount = f64Mul(amount,larger(0,f64Add(ONE,f64Div(received,HUNDRED))));
    if (!f64Finite(amount)) { s.error = 16; return 0; }
    return larger(ONE,amount);
}
[noinline]
void knockDown(inout Runtime s, uint who, uint64_t when)
{
    uint bit = 1U << who; s.downMask |= bit; s.hp[who] = 0; s.hpPct[who] = 0;
    s.hpPendingMask &= ~bit; s.hpDirtyMask &= ~bit;
    for (uint row = 0; row < s.count; row++)
    {
        Definition d = s.defs[row];
        if ((d.kind == 0 || d.kind == 4) && s.alive[row] != 0)
        {
            s.activeRecipients[row] &= ~bit;
            if (s.activeRecipients[row] == 0) { s.alive[row] = 0; s.stacks[row] = 0; }
        }
        if (d.owner == who) for (uint slot = 0; slot < d.triggerCount; slot++)
        {
            uint event = commands[s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8];
            if (event != 26) s.counters[row*8+slot] = 0;
        }
    }
    s.modeIndex[who] = -1; s.modeEpoch[who]++; s.appliedEpoch[who] = s.modeEpoch[who];
    s.charging[who] = 0; s.reloadUntil[who] = F64_SIGN | ONE; s.postReloadUntil[who] = F64_SIGN | ONE; s.pendingAutoReload[who] = 0;
    syncHealth(s,when);
}
void writeIncoming(inout Runtime s, uint output)
{
    for (uint who = 0; who < 5; who++)
    {
        uint at = output+who*4; storeNumber(at,s.receivedDamage[who]);
        results[at+2] = s.receivedHits[who]; results[at+3] = uint((s.downMask & (1U << who)) != 0);
    }
}
