// Allied body state and healing. All arithmetic uses shared software binary64.
bool liveHealthRecipient(inout Runtime s,uint row,uint who,uint64_t when)
{
    return s.alive[row]!=0 && f64Less(when,s.end[row]) && (s.activeRecipients[row]&(1U<<who))!=0 &&
           ((residentDefinition(s,row).flags&256U)!=0 || basicConditions(s,row,when,true,who));
}
[noinline]
uint64_t effectiveMaxHP(inout Runtime s, uint who, uint64_t when)
{
#ifndef PORTABLE_HEALTH_SCAN_REFERENCE
    if ((s.healthMask & 1) == 0) return s.baseHP[who];
#endif
    uint64_t percent = 0, flat = 0;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = residentDefinition(s,row);
        if (d.kind != 0 || !liveHealthRecipient(s,row,who,when)) continue;
        uint64_t value = scalarValue(s,row,who);
        if (d.stat == S_max_hp_pct || d.stat == S_max_hp_only_pct) percent = f64Add(percent,value);
        else if (d.stat == S_hp_caster_based_pct || d.stat == S_hp_only_caster_based_pct)
            flat = f64Add(flat,f64Div(f64Mul(s.baseHP[d.owner],value),HUNDRED));
        else if (d.stat == S_max_hp_from_max_hp_pct) flat = f64Add(flat,s.hpSnapshot[row]);
    }
    uint64_t maximum = f64Add(f64Mul(s.baseHP[who],f64Add(ONE,f64Div(percent,HUNDRED))),flat);
    if (!f64Finite(maximum) || !f64Less(0,maximum)) s.error = 16;
    return maximum;
}
[noinline]
uint64_t effectiveDefense(inout Runtime s, uint who, uint64_t when)
{
#ifndef PORTABLE_HEALTH_SCAN_REFERENCE
    if ((s.healthMask & 2) == 0) return s.baseDefense[who];
#endif
    uint64_t percent = 0, flat = 0;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = residentDefinition(s,row);
        if (d.kind != 0 || !liveHealthRecipient(s,row,who,when)) continue;
        uint64_t value = scalarValue(s,row,who);
        if ((d.alliedFlags & 1) != 0) percent = f64Add(percent,value);
        else if (d.stat == S_def_caster_based_pct) flat = f64Add(flat,f64Mul(s.baseDefense[d.owner],f64Div(value,HUNDRED)));
    }
    uint64_t result = f64Add(f64Mul(s.baseDefense[who],f64Add(ONE,f64Div(percent,HUNDRED))),flat);
    if (!f64Finite(result)) s.error = 16;
    return result;
}
[noinline]
void syncHealthActor(inout Runtime s, uint who, uint64_t when)
{
    if ((s.downMask & (1U << who)) != 0) { s.hp[who] = 0; s.hpPct[who] = 0; return; }
    uint64_t previous = s.hpPct[who], maximum = effectiveMaxHP(s,who,when);
    if (s.error != 0) return;
    s.hp[who] = larger(0,commands[s.inputBase+P_HP_UNCLAMP_POLICY]!=0 ? s.hp[who] : smaller(maximum,s.hp[who]));
    s.hpPct[who] = f64Mul(f64Div(s.hp[who],maximum),HUNDRED);
    if (!f64Finite(s.hpPct[who])) { s.error = 16; return; }
    if (s.hpWatchCount != 0 && s.hpEdgeGuard == 0 && !f64Equal(previous,s.hpPct[who]))
    {
        if ((s.hpPendingMask & (1U << who)) != 0) { s.error = 64; return; }
        s.hpPrevious[who] = previous; s.hpNext[who] = s.hpPct[who]; s.hpPendingMask |= 1U << who;
    }
}
[noinline]
void syncHealth(inout Runtime s, uint64_t when)
{
    if (s.healthMask == 0 && s.hpWatchCount == 0) return;
    // With listeners, synchronize one actor at a time in the explicit event
    // stack. A crossing's children finish before the next actor is observed.
    if (s.hpWatchCount != 0) { s.hpDirtyMask |= 31; return; }
    for (uint who = 0; who < 5 && s.error == 0; who++) syncHealthActor(s,who,when);
}
[noinline]
uint64_t prepareHealthGrant(inout Runtime s, uint row, uint64_t when)
{
    Definition d = residentDefinition(s,row); uint64_t grant = 0;
    if (d.stat == S_max_hp_pct || d.stat == S_hp_caster_based_pct)
        {
            uint64_t unit=d.value;
            if (referenceScaleMode(s,s.carrierDefinition[row])!=0) unit=s.stacks[row]!=0 ? f64Div(scalarValue(s,row,d.owner),f64FromI64(s.stacks[row])) : 0;
            grant = f64Div(f64Mul(s.baseHP[d.owner],unit),HUNDRED);
        }
    if (d.stat == S_max_hp_from_max_hp_pct)
    {
        uint64_t previous = s.hpSnapshot[row]; s.hpSnapshot[row] = 0;
        s.hpSnapshot[row] = f64Div(f64Mul(effectiveMaxHP(s,d.owner,when),scalarValue(s,row,d.owner)),HUNDRED);
        grant = larger(0,f64Add(s.hpSnapshot[row],previous ^ F64_SIGN));
    }
    if (!f64Finite(grant)) s.error = 16;
    return grant;
}
[noinline]
void applyHealthBuff(inout Runtime s, uint row, uint64_t when)
{
    Definition d = residentDefinition(s,row);
#ifndef PORTABLE_HEALTH_SCAN_REFERENCE
    if (!(d.stat >= S_max_hp_pct && d.stat <= S_max_hp_only_pct || d.stat == S_max_hp_from_max_hp_pct)) return;
#endif
    uint64_t grant = prepareHealthGrant(s,row,when);
    if (s.error != 0) return;
    if (!f64Zero(grant)) for (uint who = 0; who < 5; who++) if ((s.activeRecipients[row] & (1U << who)) != 0)
        s.hp[who] = smaller(f64Add(s.hp[who],grant),effectiveMaxHP(s,who,when));
    syncHealth(s,when);
}
[noinline]
uint64_t healMultiplier(inout Runtime s, uint recipient, uint source, uint64_t when)
{
    uint64_t received = larger(0,f64Add(ONE,f64Div(plainQuantity(s,recipient,S_heal_received_pct,when),HUNDRED)));
    uint64_t outgoing = larger(0,f64Add(ONE,f64Div(plainQuantity(s,source,S_outgoing_heal_pct,when),HUNDRED)));
    return f64Mul(received,outgoing);
}
[noinline]
void writeHealth(inout Runtime s, uint64_t when, uint output)
{
    if (s.error != 0) return;
    for (uint who = 0; who < 5; who++)
    {
        uint at = output+who*10;
        storeNumber(at,s.hp[who]); storeNumber(at+2,effectiveMaxHP(s,who,when));
        storeNumber(at+4,s.hpPct[who]); storeNumber(at+6,effectiveDefense(s,who,when)); storeNumber(at+8,s.healing[who]);
    }
}
