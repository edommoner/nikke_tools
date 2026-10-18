bool validRecipientPlan(uint at)
{
    uint kind = commands[at], count = commands[at+1], mask = commands[at+2];
    if (kind > 16 || kind == 4 || kind == 12 || kind == 13 || kind == 14 || count > 5 || mask > 31 || commands[at+3] > 1) return false;
    if ((kind == 5 || kind == 6 || kind == 7 || kind == 15 || kind == 16) && count == 0) return false;
    uint order = commands[at+4], seen = 0; bool ended = false;
    if (order >> 15 != 0) return false;
    for (uint i = 0; i < 5; i++)
    {
        uint encoded = (order >> (3*i)) & 7;
        if (encoded == 0) { ended = true; continue; }
        if (ended || encoded > 5 || (seen & (1U << (encoded-1))) != 0) return false;
        seen |= 1U << (encoded-1);
    }
    return order == 0 || kind == 8 && seen == mask;
}
// Keep the damage/quantity collector out of the static-selector stack frame.
[noinline]
uint64_t recipientAttack(inout Runtime s, uint who, uint64_t when)
{
    uint64_t percent = 0, flat = 0;
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass]; Definition d = s.defs[row];
        if (d.kind != 0 || !liveRecipient(s,row,who,when)) continue;
        if (d.stat == S_atk_pct) percent = f64Add(percent,scalarValue(s,row,who));
        else if (d.stat == S_atk_flat) flat = f64Add(flat,scalarValue(s,row,who));
        else if (d.stat == S_atk_caster_based_pct)
            flat = f64Add(flat,f64Mul(s.baseAttack[d.owner],f64Div(scalarValue(s,row,who),HUNDRED)));
    }
    return f64Add(f64Mul(s.baseAttack[who],f64Add(ONE,f64Div(percent,HUNDRED))),flat);
}
// Shared ordered selection. Static metadata is compiled once; ranks and burst
// membership are resolved from this invocation's GPU state, never CPU traces.
[noinline]
uint selectRecipients(inout Runtime s, uint row, uint64_t when, out uint order)
{
    Definition d = s.defs[row];
    uint at = s.inputBase+P_RECIPIENT_BASE+row*8;
    uint kind = commands[at], count = commands[at+1], candidates = commands[at+2];
    uint exclude = commands[at+3], authoredOrder = commands[at+4];
    if (kind == 0)
    {
        uint mask = (1U << d.owner) & ~s.downMask;
        order = mask != 0 ? d.owner+1 : 0; return mask;
    }
    uint slots[5]; uint size = 0;
    if (kind == 2)
    { for (uint who = d.owner+1; who < 5 && size < count; who++) slots[size++] = who; }
    else if (kind == 3)
    {
        slots[size++] = d.owner;
        if (d.owner > 0 && count > 0) slots[size++] = d.owner-1;
        if (d.owner < 4 && size <= count) slots[size++] = d.owner+1;
    }
    else if (kind == 8 && authoredOrder != 0)
    {
        for (uint i = 0; i < 5; i++)
        { uint encoded = (authoredOrder >> (3*i)) & 7; if (encoded != 0) slots[size++] = encoded-1; }
    }
    else
    {
        uint pool = kind == 8 || kind == 15 || kind == 16 ? candidates : 31;
        if (kind == 9 || kind == 11) pool &= s.castMask;
        if (kind == 10) pool &= ~s.castMask;
        if (kind == 11) pool &= candidates;
        if (exclude != 0) pool &= ~(1U << d.owner);
        pool &= ~s.downMask;
        uint64_t keys[5];
        bool ranked = kind == 5 || kind == 6 || kind == 7 || kind == 15 || kind == 16;
        for (uint who = 0; who < 5; who++) if ((pool & (1U << who)) != 0)
        {
            uint64_t key = 0;
            if (kind == 7) key = s.hpPct[who];
            // CPU top_def intentionally ranks base defense, not buffed defense.
            else if (kind == 6) key = s.baseDefense[who];
            else if (ranked)
            {
                key = recipientAttack(s,who,when);
            }
            if (!f64Finite(key)) { s.error = 16; order = 0; return 0; }
            uint pos = size;
            // Stable insertion preserves squad order for equal ranks.
            while (pos > 0 && (kind == 7 || kind == 16 ? f64Less(key,keys[pos-1]) : f64Less(keys[pos-1],key)))
            { slots[pos] = slots[pos-1]; keys[pos] = keys[pos-1]; pos--; }
            slots[pos] = who; keys[pos] = key; size++;
        }
        if (ranked) size = min(size,count);
    }
    uint mask = 0, written = 0; order = 0;
    for (uint i = 0; i < size; i++) if ((s.downMask & (1U << slots[i])) == 0)
    { mask |= 1U << slots[i]; order |= (slots[i]+1) << (3*written++); }
    return mask;
}
