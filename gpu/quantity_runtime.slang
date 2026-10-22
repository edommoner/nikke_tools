// Shared source-group quantities. Never collapse distinct rounding groups.
bool liveRecipient(inout Runtime s, uint row, uint who, uint64_t when)
{
    return s.alive[row] != 0 && f64Less(when,s.end[row]) && (s.activeRecipients[row] & (1U << who)) != 0 && basicConditions(s,row,when,true,who);
}
uint64_t stackedValue(inout Runtime s, uint row, uint who, uint stack)
{
    Definition d = residentDefinition(s,row); uint64_t value = d.value;
    // Native lost-HP scaling reads the caster at query time and bypasses stacks.
    if ((d.flags & 128U)!=0) return f64Mul(value,larger(0,f64Add(HUNDRED,s.hpPct[d.owner] ^ F64_SIGN)));
    if (d.stat == S_charge_speed_caster_based_pct && d.kind == 0)
    {
        uint64_t caster = s.rawCharge[d.owner], target = f64Zero(s.rawCharge[who]) ? caster : s.rawCharge[who];
        if (f64Zero(caster) || f64Zero(target)) return 0;
        value = f64Mul(f64Div(f64Div(f64Mul(caster,value),HUNDRED),target),HUNDRED);
    }
#ifndef PORTABLE_REFERENCE_SCALE_ALWAYS_LOOKUP
    if ((d.flags&4)==0) return f64Mul(value,f64FromI64(d.maxStack==1 ? 1 : stack));
#endif
    bool referenced; uint64_t count=scalarReferenceCount(s,row,referenced);
    return f64Mul(value,referenced ? count : f64FromI64(d.maxStack==1 ? 1 : stack));
}
uint64_t scalarValue(inout Runtime s, uint row, uint who) { return stackedValue(s,row,who,s.stacks[row]); }
uint64_t recipientValue(inout Runtime s, uint row, uint who)
{
    uint override = s.recipientStacks[row*5+who];
    return stackedValue(s,row,who,override != 0 ? override : s.stacks[row]);
}
uint chargeFlags(inout Runtime s, uint who, uint64_t when)
{
    uint flags = 0;
    for (uint i = 0; i < s.orderedCount; i++)
    {
        uint row = s.orderedRows[i]; Definition d = residentDefinition(s,row);
        if ((d.quantityFlags & 24) == 0 && !(d.kind == 0 && d.stat == S_charge_time_fixed)) continue;
        if (!queryRecipient(s,row,who,when)) continue;
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
    uint64_t values[P_DEFINITIONS]; uint seen[P_DEFINITIONS], order[P_DEFINITIONS], flags[P_DEFINITIONS], count = 0;
#ifdef PORTABLE_CAPACITY_SCAN_REFERENCE
    uint initializedGroups = P_DEFINITIONS;
#else
    // Compiler groups are dense and the GPU validates group < definition count.
    // Do not clear unused capacity for each quantity query on a small program.
    uint initializedGroups = s.count;
#endif
    for (uint i = 0; i < initializedGroups; i++) { values[i] = 0; seen[i] = 0; flags[i] = 0; }
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = residentDefinition(s,row);
        if (d.kind != 0 || (d.stat != key && !(key == S_charge_speed_pct && d.stat == S_charge_speed_caster_based_pct)) || !queryRecipient(s,row,who,when)) continue;
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
            uint other = s.orderedRows[member]; Definition candidate = residentDefinition(s,other);
            if (candidate.group != group || candidate.kind != 0 ||
                (candidate.stat != key && !(key == S_charge_speed_pct && candidate.stat == S_charge_speed_caster_based_pct)) || !queryRecipient(s,other,who,when)) continue;
            if (candidate.stat == S_charge_speed_caster_based_pct && f64Zero(s.rawCharge[candidate.owner])) continue;
            values[group] = f64Add(values[group],recipientValue(s,other,who)); flags[group] |= candidate.exclusive | (candidate.quantityFlags & 32);
        }
#else
        if (seen[group] == 0) { seen[group] = 1; order[count++] = group; }
        values[group] = f64Add(values[group],recipientValue(s,row,who)); flags[group] |= d.exclusive | (d.quantityFlags & 32);
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
[noinline]
uint64_t plainQuantity(inout Runtime s, uint who, uint key, uint64_t when)
{
    uint64_t result = 0;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = residentDefinition(s,row);
        if (d.kind == 0 && d.stat == key && queryRecipient(s,row,who,when)) result = f64Add(result,d.queryResolve != 0 && d.alliedFlags == 0 ? recipientValue(s,row,who) : scalarValue(s,row,who));
    }
    return result;
}
[noinline]
uint64_t periodicSkillInterval(inout Runtime s,uint definition,uint64_t base,uint64_t when)
{
    if((s.quantityMask&6144)==0) return base;
    uint who=definition_owner(s.inputBase,definition);Sum sum={};
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
        if(d.kind!=0 || d.stat!=S_skill_cooldown_pct || s.alive[row]==0 || !f64Less(when,s.end[row])) continue;
        // Native _by_stat reads the current container without querying buffs:
        // unresolved target_chars=None applies to every caster; runtime
        // predicates are not rechecked for this percentage operation.
        if(s.lazyPending[row]==0 && (s.activeRecipients[row]&(1U<<who))==0) continue;
        addSum(sum,scalarValue(s,row,who));
    }
    // Python3.12 float sum retains a finite Neumaier correction. An overflow
    // in the running total must not turn an infinite result into NaN merely
    // because the auxiliary correction became unordered.
    uint64_t percent=sum.total;
    if(f64Finite(sum.correction) && !f64Zero(sum.correction)) percent=f64Add(percent,sum.correction);
    uint64_t factor=larger(0,f64Add(ONE,f64Div(percent,HUNDRED)));
    uint64_t flat=0;
    if((s.quantityMask&4096)!=0)
    {
        Sum adjustment={};uint name=definition_name(s.inputBase,definition);
        // Native concatenates the two stat indices in this order, rather
        // than summing all interval operators in global activation order.
        for(uint kind=1;kind<=2;kind++) for(uint pass=0;pass<s.orderedCount;pass++)
        {
            uint row=s.orderedRows[pass],source=s.carrierDefinition[row];
            if(!namedSkillInterval(s,source) || s.alive[row]==0 || !f64Less(when,s.end[row])) continue;
            uint meta=skillIntervalMeta(s,source);
            if(commands[meta+1]!=kind || commands[meta+3]==0 || commands[meta+2]!=name ||
               s.lazyPending[row]==0 && (s.activeRecipients[row]&(1U<<who))==0 || !basicConditions(s,row,when,true,who)) continue;
            addSum(adjustment,scalarValue(s,row,who));
        }
        flat=adjustment.total;
        if(f64Finite(adjustment.correction) && !f64Zero(adjustment.correction)) flat=f64Add(flat,adjustment.correction);
    }
    return larger(f64Mul(larger(0,f64Add(base,flat)),factor),f64Mul(base,f64Div(f64FromI64(5),HUNDRED)));
}
uint64_t chargeOverflow(inout Runtime s, uint who, uint64_t when)
{
    uint64_t result = 0;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass];
        if ((residentDefinition(s,row).quantityFlags & 64) != 0 && queryRecipient(s,row,who,when)) result = f64Add(result,recipientValue(s,row,who));
    }
    return result;
}
uint64_t checkedIntegerAdd(inout Runtime s, uint64_t a, uint64_t b)
{
    uint64_t result = a+b;
    if (((a ^ result) & (b ^ result) & F64_SIGN) != 0) s.error = 2;
    return result;
}
uint rawFullCapacity(inout Runtime s, uint who, uint base, bool applyBuffs, uint64_t when)
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
[noinline]
uint64_t rawEffectiveCharge(inout Runtime s, uint who, uint64_t base, uint64_t when)
{
    if ((s.quantityMask & 42) == 0) return base;
    if ((s.quantityMask & 8) != 0 && (chargeFlags(s,who,when) & 4) != 0)
    {
        int best = -1;
        for (uint row = 0; row < s.carrierCount; row++)
        {
            Definition d = residentDefinition(s,row);
            if (d.owner != who || d.stat != S_charge_time_fixed || d.kind != 0 || s.alive[row] == 0 || d.fixedLiteral == 0) continue;
            if (best < 0 || f64Less(s.activated[best],s.activated[row]) || f64Equal(s.activated[best],s.activated[row]) && s.entryOrder[row] > s.entryOrder[best]) best = int(row);
        }
        return best < 0 ? base : residentDefinition(s,uint(best)).fixedValue;
    }
    uint64_t step = uint64_t(0x3f847ae1) << 32 | 0x47ae147b; // .01 seconds
    QuantityTotals cut = quantityTotals(s,who,S_charge_speed_pct,when,base,step);
    return larger(0,f64Add(larger(0,f64Add(base,cut.rounded ^ F64_SIGN)),plainQuantity(s,who,S_charge_time_flat,when)));
}

uint fullCapacity(inout Runtime s, uint who, uint base, bool applyBuffs, uint64_t when)
{
    WORLD_STATE_SCOPE_BEGIN(s,0) bool query = applyBuffs && needsBuffResolution(s) && beginBuffQuery(s,who,when);
    uint capacity = rawFullCapacity(s,who,base,applyBuffs,when);
    if (query) s.queryActive = 0; WORLD_STATE_SCOPE_END(s)
    return capacity;
}
uint64_t effectiveCharge(inout Runtime s, uint who, uint64_t base, uint64_t when)
{
    WORLD_STATE_SCOPE_BEGIN(s,0) bool query = needsBuffResolution(s) && beginBuffQuery(s,who,when);
    uint64_t charge = rawEffectiveCharge(s,who,base,when);
    if (query) s.queryActive = 0; WORLD_STATE_SCOPE_END(s)
    return charge;
}
