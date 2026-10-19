// B3 plain bonus damage captures its coefficient at activation, then calculates
// every queued packet after full-burst buffs and before any queued landing.
bool validPendingDefinition(inout Runtime s, uint row)
{
    Definition d = s.defs[row];
    if (d.damagePending != 0)
    {
        bool cast = false;
        for (uint slot = 0; slot < d.triggerCount; slot++)
            if (commands[s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8] == 3) cast = true;
        if (d.kind != 3 || !cast) return false;
    }
    uint at = s.inputBase+P_PENDING_EXCLUDE_BASE+row*P_MASK_WORDS;
    for (uint word = 0; word < P_MASK_WORDS; word++)
    {
        uint bits = commands[at+word];
        if (bits == 0) continue;
        if (d.damagePending == 0 && bits != 0) return false;
        for (uint bit = 0; bit < 32; bit++) if ((bits & (1U << bit)) != 0)
        {
            uint target = word*32+bit;
            if (target >= s.count) return false;
            if (s.defs[target].owner != d.owner || s.defs[target].kind != 0 && s.defs[target].kind != 4) return false;
        }
    }
    return true;
}
void enqueuePendingBurst(inout Runtime s, uint row, uint64_t when)
{
    Definition d = s.defs[row];
    uint64_t coefficient = d.value; // plain bonus coefficient is not a DoT stack multiplier
    if (f64Zero(coefficient)) return;
    if (!f64Finite(coefficient)) { s.error = 16; return; }
    if (s.pendingCount == P_PENDING) { s.error = 64; return; }
    if (s.pendingEnqueued == 0x7fffffff) { s.error = 2; return; }
    uint index = s.pendingCount++;
    s.pendingEnqueued++;
    s.pendingRow[index] = row; s.pendingCoefficient[index] = coefficient;
    s.pendingCastTime[index] = when; s.pendingHits[index] = d.pendingHits;
    s.pendingAmount[index] = 0;
}
[noinline]
void firePendingBursts(inout Runtime s, uint64_t when, uint output)
{
    uint count = s.pendingCount;
    // Capture all amounts before routing/landing can change target state.
    for (uint index = 0; index < count && s.error == 0; index++)
    {
        uint row = s.pendingRow[index]; Definition d = s.defs[row];
#ifndef PORTABLE_PENDING_RECALCULATE_REFERENCE
        // No event is dispatched during this calculation phase. Repeated
        // adjacent definitions with the same captured coefficient share it.
        if (index != 0 && row == s.pendingRow[index-1] && f64Equal(s.pendingCoefficient[index],s.pendingCoefficient[index-1]))
        { s.pendingAmount[index] = s.pendingAmount[index-1]; continue; }
#endif
        uint target = s.target; s.target = 0; s.damageExclusion = row+1;
        s.pendingAmount[index] = damageValue(s,d.owner,s.pendingCoefficient[index],when,false,s.coreBonus);
        s.damageExclusion = 0; s.target = target;
    }
    for (uint index = 0; index < count && s.error == 0; index++)
    {
        uint row = s.pendingRow[index]; Definition d = s.defs[row]; d.damageHits = s.pendingHits[index];
        for (uint hit = 0; hit < d.damageHits && s.error == 0; hit++)
        {
            uint packedOrder; uint inherited = aimedTarget(s,d.owner);
            uint mask = enemyDamageMask(s,d,inherited,packedOrder);
            if (mask == 0) break;
            for (uint pass = 0; pass < 8; pass++)
            { uint encoded = (packedOrder >> (pass*4)) & 15; if (encoded == 0) break; land(s,d.owner,encoded-1,s.pendingAmount[index]); }
            uint trace = s.traceCount;
            logDamagePacket(s,d,row,mask,0,hit+1,s.pendingAmount[index],s.pendingAmount[index],packedOrder,when,1,output);
            if (s.error == 0 && s.traceMode == 1)
            { uint at = output+P_PENDING_TRACE_BASE+trace*4; results[at] = 1; storeNumber(at+1,s.pendingCastTime[index]); }
        }
        if (s.pendingFired == 0x7fffffff) { s.error = 2; break; }
        s.pendingFired++;
    }
    s.damageExclusion = 0;
    if (s.error == 0) s.pendingCount = 0;
}
void writePendingBurst(inout Runtime s, uint output, bool entries)
{
    results[output] = s.pendingCount; results[output+1] = s.pendingEnqueued; results[output+2] = s.pendingFired;
    if (entries) for (uint index = 0; index < s.pendingCount; index++)
    {
        uint at = output+4+index*8; results[at] = s.pendingRow[index];
        storeNumber(at+1,s.pendingCastTime[index]); storeNumber(at+3,s.pendingCoefficient[index]);
        results[at+5] = s.pendingHits[index]; storeNumber(at+6,s.pendingAmount[index]);
    }
}
