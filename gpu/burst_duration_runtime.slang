[noinline]
bool validateDurationGroups(inout Runtime s)
{
    if (s.durationEnabled == 0) return true;
    for (uint row = 0; row < s.count; row++) if (s.defs[row].durationGroup != 0)
    {
        Definition d = s.defs[row];
#ifdef PORTABLE_DURATION_SCAN_REFERENCE
        for (uint prior = 0; prior < row; prior++) if (d.durationGroup == s.defs[prior].durationGroup &&
            (d.owner != s.defs[prior].owner || d.name != s.defs[prior].name)) return false;
#else
        uint encoded = s.durationGroupFirst[d.durationGroup-1];
        if (encoded == 0) s.durationGroupFirst[d.durationGroup-1] = row+1;
        else if (d.owner != s.defs[encoded-1].owner || d.name != s.defs[encoded-1].name) return false;
#endif
    }
    return true;
}

// The controller consumes active carriers directly, not buff-query values.
// Do not resolve lazy recipients, recheck runtime predicates or multiply stacks.
bool durationEligible(inout Runtime s, uint row, uint64_t when)
{
    Definition d = residentDefinition(s,row);
    if (d.kind != 0 || d.stat != S_fullburst_duration || s.alive[row] == 0 || !f64Less(when,s.end[row])) return false;
    return d.durationCast == 0 || d.owner == s.lastB3Caster && !f64Less(s.activated[row],f64Add(s.lastB3Time,BURST_EPS ^ F64_SIGN));
}
[noinline]
uint64_t fullBurstLength(inout Runtime s, uint64_t when)
{
    if (s.durationEnabled == 0) return TEN;
    uint seen[P_MASK_WORDS]; for (uint word = 0; word < P_MASK_WORDS; word++) seen[word] = 0;
    uint64_t extension = 0;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = residentDefinition(s,row);
        if (!durationEligible(s,row,when)) continue;
#ifdef PORTABLE_DURATION_SCAN_REFERENCE
        bool duplicate = false;
        for (uint previous = 0; previous < pass; previous++)
        {
            uint prior = s.orderedRows[previous];
            if (residentDefinition(s,prior).durationGroup == d.durationGroup && durationEligible(s,prior,when)) { duplicate = true; break; }
        }
        if (duplicate) continue;
#else
        uint group = d.durationGroup-1, bit = 1U << (group%32);
        if ((seen[group/32] & bit) != 0) continue;
        seen[group/32] |= bit;
#endif
        extension = f64Add(extension,d.value);
        if (!f64Finite(extension)) { s.error = 16; return 0; }
    }
    uint64_t duration = larger(ONE,f64Add(TEN,extension));
    if (!f64Finite(duration)) s.error = 16;
    return duration;
}
