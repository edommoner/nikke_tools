// Immutable watcher identities use the existing compiler's event key IDs.
uint hpWatchAddress(inout Runtime s, uint watch)
{
    uint slot = s.hpWatchSlots[watch];
    return s.inputBase+P_EVENT_BASE+(slot/8)*P_EVENT_WORDS+(slot%8)*8;
}
[noinline]
void initializeHPWatches(inout Runtime s)
{
    // Observer order, then first descriptor occurrence (including numeric
    // spellings such as 50 and 50.0 as distinct named keys).
    for (uint owner = 0; owner < 5; owner++) for (uint row = 0; row < s.count; row++)
    {
        if (s.defs[row].owner != owner) continue;
        for (uint slot = 0; slot < s.defs[row].triggerCount; slot++)
        {
            uint at = s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8;
            int stage = int(commands[at+7]);
            if (stage < -14 || stage > -11) continue;
            bool seen = false;
#ifndef PORTABLE_HP_WATCH_SCAN_REFERENCE
            for (uint i = 0; i < s.hpWatchCount; i++)
            {
                uint prior = hpWatchAddress(s,i);
                if (s.defs[s.hpWatchSlots[i]/8].owner == owner && commands[prior] == commands[at] && commands[prior+4] == commands[at+4]) seen = true;
            }
#endif
            if (!seen) s.hpWatchSlots[s.hpWatchCount++] = row*8+slot;
        }
    }
}
bool hpEdgeMatches(uint changed, uint observer, int stage, uint phase,
                   uint64_t previous, uint64_t next, uint64_t threshold)
{
    uint64_t epsilon = uint64_t(0x3eb0c6f7) << 32 | 0xa0b5ed8d; // 1e-6
    if (phase == 2)
        return stage == -14 && observer != changed && (observer+1 == changed || changed+1 == observer) &&
            f64Less(previous,f64Add(HUNDRED,epsilon ^ F64_SIGN)) && !f64Less(next,f64Add(HUNDRED,epsilon ^ F64_SIGN));
    if (phase == 0 && !(stage == -11 && observer == changed || stage == -12)) return false;
    if (phase == 1 && !(stage == -13 && observer != changed && (observer+1 == changed || changed+1 == observer))) return false;
    uint64_t boundary = f64Add(threshold,epsilon);
    return f64Less(boundary,previous) && !f64Less(boundary,next);
}
