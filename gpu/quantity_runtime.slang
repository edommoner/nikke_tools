// Shared source-group quantities. Never collapse distinct rounding groups.
bool liveRecipient(inout Runtime s, uint row, uint who, uint64_t when)
{
    return s.alive[row] != 0 && f64Less(when,s.end[row]) && (s.activeRecipients[row] & (1U << who)) != 0 && basicConditions(s,row,when,true,who);
}
uint64_t scalarValue(inout Runtime s, uint row, uint who)
{
    Definition d = s.defs[row]; uint64_t value = d.value;
    if (d.stat == S_charge_speed_caster_based_pct && d.kind == 0)
    {
        uint64_t caster = s.rawCharge[d.owner], target = f64Zero(s.rawCharge[who]) ? caster : s.rawCharge[who];
        if (f64Zero(caster) || f64Zero(target)) return 0;
        value = f64Mul(f64Div(f64Div(f64Mul(caster,value),HUNDRED),target),HUNDRED);
    }
    return f64Mul(value,f64FromI64(s.stacks[row]));
}
uint chargeFlags(inout Runtime s, uint who, uint64_t when)
{
    uint flags = 0;
    for (uint i = 0; i < s.orderedCount; i++)
    {
        uint row = s.orderedRows[i]; Definition d = s.defs[row];
        if (!liveRecipient(s,row,who,when)) continue;
        flags |= d.quantityFlags & 24;
        if (d.kind == 0 && d.stat == S_charge_time_fixed) flags |= 4;
    }
    return flags;
}
struct QuantityTotals { uint64_t percent, rounded; };
[noinline]
QuantityTotals quantityTotals(inout Runtime s, uint who, uint key, uint64_t when, uint64_t base, uint64_t step)
{
    QuantityTotals result = {}; uint required = key == S_max_ammo_pct ? 1 : 2;
    if ((s.quantityMask & required) == 0) return result;
    uint immunity = key == S_charge_speed_pct ? chargeFlags(s,who,when) : 0;
    if ((immunity & 4) != 0) return result;
    uint64_t values[32]; uint seen[32], order[32], flags[32], count = 0;
    for (uint i = 0; i < 32; i++) { values[i] = 0; seen[i] = 0; flags[i] = 0; }
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = s.defs[row];
        if (d.kind != 0 || (d.stat != key && !(key == S_charge_speed_pct && d.stat == S_charge_speed_caster_based_pct)) || !liveRecipient(s,row,who,when)) continue;
        // Missing caster metadata is an absent component, not a zero-valued
        // component that may change the first-seen group order.
        if (d.stat == S_charge_speed_caster_based_pct && f64Zero(s.rawCharge[d.owner])) continue;
        uint group = d.group;
#ifdef PORTABLE_QUANTITY_SCAN_REFERENCE
        if (seen[group] != 0) continue;
        seen[group] = 1; order[count++] = group;
        // Benchmark control: rediscover each group's resident members.
        for (uint member = 0; member < s.orderedCount; member++)
        {
            uint other = s.orderedRows[member]; Definition candidate = s.defs[other];
            if (candidate.group != group || candidate.kind != 0 ||
                (candidate.stat != key && !(key == S_charge_speed_pct && candidate.stat == S_charge_speed_caster_based_pct)) || !liveRecipient(s,other,who,when)) continue;
            if (candidate.stat == S_charge_speed_caster_based_pct && f64Zero(s.rawCharge[candidate.owner])) continue;
            values[group] = f64Add(values[group],scalarValue(s,other,who)); flags[group] |= candidate.exclusive | (candidate.quantityFlags & 32);
        }
#else
        if (seen[group] == 0) { seen[group] = 1; order[count++] = group; }
        values[group] = f64Add(values[group],scalarValue(s,row,who)); flags[group] |= d.exclusive | (d.quantityFlags & 32);
#endif
    }
    int best = -1; bool exclusive = false;
    if (key == S_max_ammo_pct) for (uint i = 0; i < count; i++)
    {
        uint group = order[i];
        if (!f64Less(values[group],0)) continue;
        if ((flags[group] & 1) != 0) exclusive = true;
        if (best < 0 || f64Less(values[group],values[best])) best = int(group);
    }
    Sum rounded = {}, filteredPercent = {}; bool removed = false;
    for (uint i = 0; i < count; i++)
    {
        uint group = order[i]; uint64_t value = values[group];
        bool blocked = key == S_charge_speed_pct && (flags[group] & 32) == 0 &&
            (f64Less(0,value) && (immunity & 8) != 0 || f64Less(value,0) && (immunity & 16) != 0);
        bool discard = exclusive && f64Less(value,0) && int(group) != best;
        if (blocked || discard) { removed = removed || blocked; continue; }
        result.percent = f64Add(result.percent,value); addSum(filteredPercent,value);
        uint64_t term = f64Mul(f64Integral(f64Add(f64Div(f64Mul(base,f64Div(value,HUNDRED)),step),uint64_t(0x3fe00000) << 32),2),step);
        if (!f64Finite(term)) { s.error = 16; return result; }
        addSum(rounded,term);
    }
    if (removed) result.percent = f64Add(filteredPercent.total,filteredPercent.correction);
    result.rounded = f64Add(rounded.total,rounded.correction); return result;
}
uint64_t plainQuantity(inout Runtime s, uint who, uint key, uint64_t when)
{
    uint64_t result = 0;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = s.defs[row];
        if (d.kind == 0 && d.stat == key && liveRecipient(s,row,who,when)) result = f64Add(result,scalarValue(s,row,who));
    }
    return result;
}
uint64_t chargeOverflow(inout Runtime s, uint who, uint64_t when)
{
    uint64_t result = 0;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass];
        if ((s.defs[row].quantityFlags & 64) != 0 && liveRecipient(s,row,who,when)) result = f64Add(result,scalarValue(s,row,who));
    }
    return result;
}
uint64_t checkedIntegerAdd(inout Runtime s, uint64_t a, uint64_t b)
{
    uint64_t result = a+b;
    if (((a ^ result) & (b ^ result) & F64_SIGN) != 0) s.error = 2;
    return result;
}
uint fullCapacity(inout Runtime s, uint who, uint base, bool applyBuffs, uint64_t when)
{
    if (!applyBuffs || base == 0 || (s.quantityMask & 17) == 0) return base;
    QuantityTotals quant = quantityTotals(s,who,S_max_ammo_pct,when,f64FromI64(base),ONE);
    uint qStatus,flatStatus;
    uint64_t quantity = f64ToI64(quant.rounded,1,qStatus), flat = f64ToI64(plainQuantity(s,who,S_max_ammo_flat,when),0,flatStatus);
    if (qStatus != 0 || flatStatus != 0) { s.error = 2; return 0; }
    uint64_t total = checkedIntegerAdd(s,checkedIntegerAdd(s,base,quantity),flat);
    if ((total & F64_SIGN) != 0 || total == 0) return 1;
    if (total > 0x7fffffff) { s.error = 2; return 0; }
    return uint(total);
}
uint64_t effectiveCharge(inout Runtime s, uint who, uint64_t base, uint64_t when)
{
    if ((s.quantityMask & 42) == 0) return base;
    if ((s.quantityMask & 8) != 0 && (chargeFlags(s,who,when) & 4) != 0)
    {
        int best = -1;
        for (uint row = 0; row < s.count; row++)
        {
            Definition d = s.defs[row];
            if (d.owner != who || d.stat != S_charge_time_fixed || d.kind != 0 || s.alive[row] == 0 || d.fixedLiteral == 0) continue;
            if (best < 0 || f64Less(s.activated[best],s.activated[row]) || f64Equal(s.activated[best],s.activated[row]) && s.entryOrder[row] > s.entryOrder[best]) best = int(row);
        }
        return best < 0 ? base : s.defs[best].fixedValue;
    }
    uint64_t step = uint64_t(0x3f847ae1) << 32 | 0x47ae147b; // .01 seconds
    QuantityTotals cut = quantityTotals(s,who,S_charge_speed_pct,when,base,step);
    return larger(0,f64Add(larger(0,f64Add(base,cut.rounded ^ F64_SIGN)),plainQuantity(s,who,S_charge_time_flat,when)));
}
