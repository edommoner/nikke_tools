// Native get_buffs runs HP-derived attack after ordinary stats and before
// caster-based attack. Its unresolved selectors are fresh,not lazy-cache reads.
bool lateAttackRecipient(inout Runtime s,uint row,uint who,uint64_t when)
{
    if(s.alive[row]==0 || !f64Less(when,s.end[row])) return false;
    uint recipients=s.activeRecipients[row];
    if(s.lazyPending[row]!=0)
    {
        uint64_t order;recipients=selectRecipients(s,s.carrierDefinition[row],when,order);
        // Do not freeze recipients,link a cache,or consume pending history.
    }
    return (recipients & (1U<<who))!=0 && basicConditions(s,row,when,true,who);
}

[noinline]
uint64_t nativeAttackMaxHP(inout Runtime s,uint who,uint64_t when)
{
    // This mirrors the pinned CPU effective_max_hp used by the attack pass:
    // active memberships after native tick expiry,without another runtime-condition query.
    // Displayed/health-sync maximum HP keeps its existing independent contract.
    uint64_t percent=0,flat=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
        if(d.kind!=0 || s.alive[row]==0 || !f64Less(when,s.end[row]) || (s.activeRecipients[row] & (1U<<who))==0) continue;
        if(d.stat==S_max_hp_pct || d.stat==S_max_hp_only_pct)
            percent=f64Add(percent,scalarValue(s,row,who));
        else if(d.stat==S_hp_caster_based_pct || d.stat==S_hp_only_caster_based_pct)
            flat=f64Add(flat,f64Div(f64Mul(s.baseHP[d.owner],scalarValue(s,row,who)),HUNDRED));
        else if(d.stat==S_max_hp_from_max_hp_pct) flat=f64Add(flat,s.hpSnapshot[row]);
        else if(d.stat==S_hp_copy) flat=f64Add(flat,baseCopyContribution(s,row,who));
    }
    return f64Add(f64Mul(s.baseHP[who],f64Add(ONE,f64Div(percent,HUNDRED))),flat);
}

[noinline]
void collectHPAttack(inout Runtime s,uint who,uint64_t when,inout uint64_t flat)
{
    for(uint family=0;family<2;family++)
        for(uint pass=0;pass<s.orderedCount;pass++)
        {
            uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
            if(d.kind!=0 || d.enemyBuff!=0 || d.stat!=(family==0 ? S_atk_from_hp_pct : S_atk_caster_based_pct) || !lateAttackRecipient(s,row,who,when)) continue;
            uint64_t value=family==0 ? recipientValue(s,row,who) : scalarValue(s,row,who);
            uint64_t basis=family==0 ? nativeAttackMaxHP(s,who,when) : s.baseAttack[d.owner];
            flat=f64Add(flat,f64Mul(basis,f64Div(value,HUNDRED)));
            if(!f64Finite(flat)) { s.error=16;return; }
        }
}
