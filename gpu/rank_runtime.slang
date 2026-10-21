// Ranking observes already-resolved carriers. In particular it never resolves
// the pending buff whose own recipient is being selected, or another pending
// attack modifier. This also avoids recursive shader calls.
[noinline]
uint64_t recipientAttack(inout Runtime s, uint who, uint64_t when)
{
    uint64_t percent = 0, flat = 0;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = residentDefinition(s,row);
        if (d.kind != 0 || s.alive[row] == 0 || (s.activeRecipients[row] & (1U << who)) == 0) continue;
        // Native ranking uses the representative scalar, including references
        // and max_stack=1 semantics; it does not use per-recipient overrides.
        if(d.stat!=S_atk_pct && d.stat!=S_atk_flat && d.stat!=S_atk_caster_based_pct) continue;
        uint64_t value = scalarValue(s,row,who);
        if (d.stat == S_atk_pct) percent = f64Add(percent,value);
        else if (d.stat == S_atk_flat) flat = f64Add(flat,value);
        else if (d.stat == S_atk_caster_based_pct) flat = f64Add(flat,f64Mul(s.baseAttack[d.owner],f64Div(value,HUNDRED)));
    }
    return f64Add(f64Mul(s.baseAttack[who],f64Add(ONE,f64Div(percent,HUNDRED))),flat);
}

[noinline]
uint rankedRecipientsAt(inout Runtime s, uint definition, uint at, uint64_t when, out uint64_t order)
{
    uint kind = commands[at], count = commands[at+1], owner = definition_owner(s.inputBase,definition);
    uint pool = kind == 15 || kind == 16 ? commands[at+2] : 31;
    if (commands[at+3] != 0) pool &= ~(1U << owner);
    if(kind==22) pool &= s.downMask & ~(1U<<owner);else pool &= ~s.downMask;
    uint slots[5], size = 0; uint64_t keys[5];
    for (uint who = 0; who < 5; who++) if ((pool & (1U << who)) != 0)
    {
        uint64_t key = kind == 7 ? s.hpPct[who] : kind == 6 ? s.baseDefense[who] : recipientAttack(s,who,when);
        if (!f64Finite(key)) { s.error = 16; order = 0; return 0; }
        uint pos = size;
        while (pos > 0 && (kind == 7 || kind == 16 ? f64Less(key,keys[pos-1]) : f64Less(keys[pos-1],key)))
        { slots[pos] = slots[pos-1]; keys[pos] = keys[pos-1]; pos--; }
        slots[pos] = who; keys[pos] = key; size++;
    }
    uint mask = 0; order = 0;
    for (uint i = 0; i < min(size,count); i++)
    { mask |= 1U << slots[i]; order |= uint64_t(slots[i]+1) << (3*i); }
    return mask;
}

uint rankedRecipients(inout Runtime s,uint definition,uint64_t when,out uint64_t order)
{ return rankedRecipientsAt(s,definition,s.inputBase+P_RECIPIENT_BASE+definition*8,when,order); }
