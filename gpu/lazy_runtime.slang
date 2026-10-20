// Bounded GPU-owned memo for (caster + raw selector group, activation time).
// Links protect old snapshots while a sibling has not consumed them yet.
void unlinkLazyCache(inout Runtime s, uint row)
{
    if (s.lazyLink[row] != 0)
    { uint entry = s.lazyLink[row]-1; s.cacheRefs[entry]--; s.lazyLink[row] = 0; }
}
void discardLazy(inout Runtime s, uint row)
{
    unlinkLazyCache(s,row);
    if (s.lazyPending[row] != 0) { s.lazyPending[row] = 0; s.lazyPendingCount--; s.lazyMappedPendingCount -= residentDefinition(s,row).queryResolve; }
}
void beginLazyRoot(inout Runtime s, uint64_t when)
{
    if (s.lazyEnabled == 0) return;
    if (f64Zero(s.cacheRootTime) && f64Zero(s.cacheFloor)) s.cacheFloor = f64Add(END_BEFORE,f64Add(END_EPS,END_EPS)) ^ F64_SIGN;
    if (f64Less(s.cacheRootTime,when))
    {
        // A last DOT tick can be observed just before expiry. Retain the
        // preceding root plus its nudge and two comparison-epsilon margins.
        s.cacheFloor = f64Add(s.cacheRootTime,f64Add(END_BEFORE,f64Add(END_EPS,END_EPS)) ^ F64_SIGN);
        s.cacheRootTime = when;
    }
}

[noinline]
void ensureLazyRecipients(inout Runtime s, uint row, uint64_t when)
{
    if (s.lazyPending[row] == 0) return;
    Definition d = residentDefinition(s,row); uint group = d.lazyGroup;
    uint64_t key = s.activated[row]; uint entry = P_LAZY_CACHE;
    if (s.lazyLink[row] != 0) entry = s.lazyLink[row]-1;
    else
    {
        bool scan = true;
#ifndef PORTABLE_LAZY_CACHE_SCAN_REFERENCE
        if (s.cacheSeen[group-1] != 0)
        {
            uint newest = s.cacheNewest[group-1];
            if (newest < s.cacheCount && s.cacheGroup[newest] == group && f64Equal(s.cacheTime[newest],key))
            { entry = newest; scan = false; }
            else if (f64Less(s.cacheNewestTime[group-1],key)) scan = false;
        }
        else scan = false;
#endif
        if (scan) for (uint i = 0; i < s.cacheCount; i++)
            if (s.cacheGroup[i] == group && f64Equal(s.cacheTime[i],key)) { entry = i; break; }
        if (entry == P_LAZY_CACHE)
        {
            if (s.cacheCount < P_LAZY_CACHE) entry = s.cacheCount++;
            else for (uint i = 0; i < P_LAZY_CACHE; i++)
            {
                uint candidate = (s.cacheCursor+i)%P_LAZY_CACHE;
                if (s.cacheRefs[candidate] == 0 && f64Less(s.cacheTime[candidate],s.cacheFloor))
                { entry = candidate; s.cacheCursor = (candidate+1)%P_LAZY_CACHE; s.cacheReuses++; break; }
            }
            if (entry == P_LAZY_CACHE) { s.error = 64; return; }
            s.cacheGroup[entry] = group; s.cacheTime[entry] = key;
            uint64_t order; s.cacheMask[entry] = rankedRecipients(s,s.carrierDefinition[row],when,order); s.cacheOrder[entry] = uint(order);
            s.cacheEvaluations++;
            if (s.cacheSeen[group-1] == 0 || !f64Less(key,s.cacheNewestTime[group-1]))
            { s.cacheSeen[group-1] = 1; s.cacheNewest[group-1] = entry; s.cacheNewestTime[group-1] = key; }
        }
        if (s.error != 0) return;
        // Do not resolve siblings here: an unresolved attack buff must stay
        // absent from another selector's rank until its own first consumption.
        for (uint i = 0; i < s.carrierCount; i++)
            if (s.alive[i] != 0 && s.lazyPending[i] != 0 && s.lazyLink[i] == 0 &&
                residentDefinition(s,i).lazyGroup == group && f64Equal(s.activated[i],key))
            { s.lazyLink[i] = entry+1; s.cacheRefs[entry]++; }
    }
    s.activeRecipients[row] = s.cacheMask[entry] & ~s.downMask; storeCarrierOrder(s,row,s.cacheOrder[entry]);
    resolveBulletTargets(s,row);
    unlinkLazyCache(s,row); s.lazyPending[row] = 0; s.lazyPendingCount--; s.lazyMappedPendingCount -= d.queryResolve;
}

bool needsBuffResolution(inout Runtime s)
{
#ifdef PORTABLE_LAZY_ALL_PENDING_REFERENCE
    return s.lazyPendingCount != 0;
#else
    return s.lazyMappedPendingCount != 0;
#endif
}

// A dictionary-style buff query resolves mapped stats in resident order and
// freezes each row's runtime eligibility before later rows resolve. Selective
// live-stat queries (healing/presence) resolve only the requested family.
[noinline]
bool beginBuffQuery(inout Runtime s, uint who, uint64_t when)
{
    if (s.queryActive != 0 || !needsBuffResolution(s)) return false;
    s.queryActive = 1; s.queryWho = who; s.queryWhen = when;
    for (uint pass = 0; pass < s.orderedCount && s.error == 0; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = residentDefinition(s,row); s.queryAllowed[row] = 0;
        if (excludedDamageBuff(s,row,who) || s.alive[row] == 0 || !f64Less(when,s.end[row])) continue;
        if (d.queryResolve != 0) ensureLazyRecipients(s,row,when);
        if ((s.activeRecipients[row] & (1U << who)) != 0 && WORLD_STATE_NUMERIC_CONDITION(s,row,who,when,basicConditions(s,row,when,true,who))) s.queryAllowed[row] = 1;
    }
    return true;
}
bool queryRecipient(inout Runtime s, uint row, uint who, uint64_t when)
{
    if (excludedDamageBuff(s,row,who) || s.alive[row] == 0 || !f64Less(when,s.end[row])) return false;
    if (s.queryActive != 0 && s.queryWho == who && f64Equal(s.queryWhen,when) && residentDefinition(s,row).queryResolve != 0) return s.queryAllowed[row] != 0;
    if (s.lazyPending[row] != 0) ensureLazyRecipients(s,row,when);
    return (s.activeRecipients[row] & (1U << who)) != 0 && WORLD_STATE_NUMERIC_CONDITION(s,row,who,when,basicConditions(s,row,when,true,who));
}
