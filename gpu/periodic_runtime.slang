// Definition-clock ownership is separate from the captured recipient set.
// Same-name single-stack DoT aliases refresh one live clock and union recipients.
[noinline]
uint periodicDamageMask(inout Runtime s, uint row, out uint packed)
{
    uint order = s.periodicOrder[row], count = 0, mask = 0; packed = 0;
    for (uint i = 0; i < 8; i++)
    {
        uint encoded = (order >> (4*i)) & 15; if (encoded == 0) break;
        uint target = encoded-1;
        if (targetLive(s,target,s.periodicGeneration[row*8+target]))
        { mask |= 1U << target; packed |= encoded << (4*count); count++; }
    }
    return mask;
}
[noinline]
void capturePeriodicTargets(inout Runtime s, uint row, uint source, bool append)
{
    uint packed = 0, count = 0, mask = 0;
    if (append) { mask = periodicDamageMask(s,row,packed); count = enemyMaskCount(mask); }
    Definition selector = s.defs[source];
    // Native damage carrier registration resolves target by logical aim.
    // Legacy single-recipient clocks retain their separate captured context.
    if (selector.damageRoute == 0) selector.damageRoute = 6;
    uint incoming; enemyDamageMask(s,selector,s.target,incoming);
    for (uint i = 0; i < 8; i++)
    {
        uint encoded = (incoming >> (4*i)) & 15; if (encoded == 0) break;
        uint target = encoded-1, bit = 1U << target;
        if ((mask & bit) != 0) continue;
        mask |= bit; packed |= encoded << (4*count); count++;
        s.periodicGeneration[row*8+target] = s.targetGeneration[target];
    }
    s.periodicOrder[row] = packed;
}
[noinline]
uint periodicClockOwner(inout Runtime s, uint source)
{
    uint group = s.defs[source].periodicGroup;
    if (group == 0) return source;
#ifdef PORTABLE_PERIODIC_OWNER_SCAN_REFERENCE
    uint selected = source, first = 0xffffffff;
    for (uint row = 0; row < s.count; row++)
        if (s.defs[row].periodicGroup == group && s.timerActive[row] != 0 && s.alive[row] != 0 && s.timerOrder[row] < first)
        { selected = row; first = s.timerOrder[row]; }
    return selected;
#else
    uint encoded = s.periodicOwner[group-1];
    if (encoded != 0 && s.timerActive[encoded-1] != 0 && s.alive[encoded-1] != 0) return encoded-1;
    s.periodicOwner[group-1] = source+1;
    return source;
#endif
}
[noinline]
void registerTimer(inout Runtime s, uint source, uint64_t when)
{
    uint row = periodicClockOwner(s,source); Definition d = s.defs[row], grant = s.defs[source];
    bool was = s.timerActive[row] != 0;
    bool staged=s.stagedEnabled!=0 && isStaged(s,row);
    bool resident = s.alive[row] != 0 && (staged || f64Less(when,s.end[row]));
    uint target = d.target != 0 ? 0 : s.target;
    bool retained = (d.periodicFlags & 1) != 0;
    bool sameTarget = retained || s.combat == 0 || (s.timerTarget[row] == target && s.timerGeneration[row] == s.targetGeneration[target]);
    bool preserve = d.kind == 3 && d.preserve != 0 && was && sameTarget && !staged;
    if (!preserve)
    {
        if (s.timerEpoch[row] == 0x7fffffff) { s.error = 2; return; }
        s.timerEpoch[row]++;
        s.due[row] = f64Add(when,d.kind == 3 && d.immediate != 0 ? 0 : d.interval);
        s.timerTarget[row] = retained ? 0 : target;
        s.timerGeneration[row] = s.combat != 0 ? s.targetGeneration[s.timerTarget[row]] : s.generation;
    }
    if (!was)
    {
        if (s.timerClock == 0x7fffffff) { s.error = 2; return; }
        s.timerOrder[row] = ++s.timerClock;
    }
    if (retained && (!resident || source != row)) capturePeriodicTargets(s,row,source,resident);
    s.timerActive[row] = 1;
    s.expiry[row] = f64Less(grant.duration,0) ? FOREVER : f64Add(when,grant.duration);
    if (d.kind == 3)
    {
        if (s.alive[row] == 0) markEntry(s,row);
        s.activated[row] = when;
        if (!registerDotReference(s,row,resident)) s.stacks[row] = min(s.stacks[row]+1,d.maxStack);
        s.end[row] = s.expiry[row]; s.alive[row] = 1;
    }
}
[noinline]
bool validatePeriodicDefinitions(inout Runtime s)
{
    for (uint row = 0; row < s.count; row++)
    {
        Definition d = s.defs[row]; bool damageClock = d.kind == 3 && !f64Zero(d.interval);
        if (d.periodicFlags > 7 || d.periodicGroup > s.count) return false;
        bool retained = damageClock && (d.damageRoute >= 2 || d.periodicGroup != 0);
        if ((d.periodicFlags & 1) != uint(retained) || retained && s.combat == 0) return false;
        if ((d.periodicFlags & 2) != 0 && (!damageClock || d.preserve != 1)) return false;
        if ((d.periodicFlags & 4) != 0 && !damageClock) return false;
        if (d.periodicGroup != 0 && (!damageClock || d.preserve != 1 || d.maxStack != 1 || (d.periodicFlags & 4) == 0)) return false;
        uint members = 0;
        for (uint other = 0; other < s.count; other++)
        {
            Definition b = s.defs[other];
            if (d.periodicGroup != 0 && b.periodicGroup == d.periodicGroup)
            { if (b.owner != d.owner || b.name != d.name) return false; members++; }
            if (row != other && (d.periodicFlags & 4) != 0 && (b.periodicFlags & 4) != 0 && d.name == b.name && d.owner == b.owner)
                if (d.periodicGroup == 0 || d.periodicGroup != b.periodicGroup) return false;
        }
        if (d.periodicGroup != 0 && members < 2) return false;
    }
    return true;
}
