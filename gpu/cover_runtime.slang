// Cover is a separate health layer. Boss routing feeds the explicit layer
// boundary; a hit absorbed here never spills into allied body HP.
[noinline]
uint64_t effectiveCoverHP(inout Runtime s, uint who, uint64_t when)
{
#ifndef PORTABLE_COVER_SCAN_REFERENCE
    if ((s.coverMask & 1) == 0) return s.baseCoverHP[who];
#endif
    uint64_t percent = 0, flat = 0;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = residentDefinition(s,row);
        if (d.kind != 0 || d.stat != S_cover_hp_pct || !liveRecipient(s,row,who,when)) continue;
        uint64_t value = scalarValue(s,row,who);
        if (d.healthScaling != 0)
            flat = f64Add(flat,f64Div(f64Mul(effectiveMaxHP(s,d.owner,when),value),HUNDRED));
        else percent = f64Add(percent,value);
    }
    uint64_t maximum = f64Add(f64Mul(s.baseCoverHP[who],f64Add(ONE,f64Div(percent,HUNDRED))),flat);
    if (!f64Finite(maximum) || f64Less(maximum,0)) s.error = 16;
    return maximum;
}
[noinline]
void syncCovers(inout Runtime s, uint64_t when)
{
    if (s.coverSync == 0 || s.error != 0) return;
#ifndef PORTABLE_COVER_SCAN_REFERENCE
    if ((s.coverMask & 1) == 0) return;
#endif
    for (uint who = 0; who < 5; who++)
    {
        uint64_t maximum = effectiveCoverHP(s,who,when), previous = s.coverMaxHP[who];
        if (f64Equal(maximum,previous)) continue;
        if (!f64Zero(s.coverHP[who])) s.coverHP[who] = smaller(f64Add(s.coverHP[who],larger(0,f64Add(maximum,previous ^ F64_SIGN))),maximum);
        s.coverMaxHP[who] = maximum;
    }
}
[noinline]
uint coverRecipients(inout Runtime s, uint count, out uint64_t order)
{
    uint pool[5], size = 0;
    uint64_t ratios[5];
    for (uint who = 0; who < 5; who++) if ((s.downMask & (1U << who)) == 0 && f64Less(0,s.coverHP[who]) && f64Less(0,s.coverMaxHP[who]))
    {
        uint64_t ratio = f64Div(s.coverHP[who],s.coverMaxHP[who]); uint at = size++;
        while (at > 0 && f64Less(ratio,ratios[at-1])) { pool[at] = pool[at-1]; ratios[at] = ratios[at-1]; at--; }
        pool[at] = who; ratios[at] = ratio;
    }
    uint mask = 0; order = 0;
    for (uint i = 0; i < min(size,count); i++) { mask |= 1U << pool[i]; order |= uint64_t(pool[i]+1) << (3*i); }
    return mask;
}
[noinline]
void writeCovers(inout Runtime s, uint64_t when, uint output)
{
    if (s.error != 0) return;
    for (uint who = 0; who < 5; who++)
    {
        uint at = output+who*8;
        storeNumber(at,s.coverHP[who]); storeNumber(at+2,s.coverMaxHP[who]);
        storeNumber(at+4,effectiveCoverHP(s,who,when)); storeNumber(at+6,s.coverDamage[who]);
    }
}
