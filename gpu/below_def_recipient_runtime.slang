// Native _effective_def scans resolved residents only, without resolving pending
// fields or applying runtime predicates again. Preserve percent then flat order.
[noinline]
uint64_t recipientDefense(inout Runtime s,uint who)
{
    uint64_t percent=0,flat=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];Definition d=residentDefinition(s,slot);
        if(s.alive[slot]==0 || s.lazyPending[slot]!=0 || (s.activeRecipients[slot]&(1U<<who))==0) continue;
        if((d.alliedFlags&1U)!=0) percent=f64Add(percent,scalarValue(s,slot,who));
        else if(d.stat==S_def_caster_based_pct)
            flat=f64Add(flat,f64Mul(s.baseDefense[d.owner],f64Div(scalarValue(s,slot,d.owner),HUNDRED)));
    }
    uint64_t result=f64Add(f64Mul(s.baseDefense[who],f64Add(ONE,f64Div(percent,HUNDRED))),flat);
    if(!f64Finite(result)) s.error=16;
    return result;
}
[noinline]
uint selectBelowDefense(inout Runtime s,uint row,uint64_t when,out uint64_t order)
{
    uint owner=definition_owner(s.inputBase,row),mask=0,written=0;order=0;
    uint64_t threshold=recipientDefense(s,owner);
    for(uint who=0;who<5;who++)
    {
        uint64_t value=recipientDefense(s,who);
        if(f64Less(value,threshold) && (s.downMask&(1U<<who))==0)
        { mask|=1U<<who;order|=uint64_t(who+1)<<(3*written++); }
    }
    return mask;
}
