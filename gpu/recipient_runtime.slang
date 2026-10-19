bool validRecipientPlan(uint at, bool enemy = false)
{
    uint kind = commands[at], count = commands[at+1], mask = commands[at+2];
    if (enemy) return kind == 4 && count == 0 && mask == 0 && commands[at+3] == 0 && commands[at+4] == 0 && commands[at+5] == 0 && commands[at+6] < P_DEFINITIONS && (commands[at+7] & ~7U) == 0;
    if (kind > 21 || kind >= 17 && kind <= 20 || kind == 4 || kind == 14 || count > 5 || mask > 31 || commands[at+3] > (kind == 12 || kind == 13 ? 2 : 1)) return false;
    if ((kind == 5 || kind == 6 || kind == 7 || kind == 15 || kind == 16 || kind == 21) && count == 0) return false;
    uint order = commands[at+4], seen = 0; bool ended = false;
    if (order >> 15 != 0 || commands[at+6] >= P_DEFINITIONS || (commands[at+7] & 8) != 0 || (commands[at+7] >> 4) > P_DEFINITIONS) return false;
    for (uint i = 0; i < 5; i++)
    {
        uint encoded = (order >> (3*i)) & 7;
        if (encoded == 0) { ended = true; continue; }
        if (ended || encoded > 5 || (seen & (1U << (encoded-1))) != 0) return false;
        seen |= 1U << (encoded-1);
    }
    return order == 0 || kind == 8 && seen == mask;
}
// Shared ordered selection. Static metadata is compiled once; ranks and burst
// membership are resolved from this invocation's GPU state, never CPU traces.
[noinline]
uint selectRecipients(inout Runtime s, uint row, uint64_t when, out uint order)
{
    Definition d = readDefinition(s.inputBase,row);
    uint at = s.inputBase+P_RECIPIENT_BASE+row*8;
    uint kind = commands[at], count = commands[at+1], candidates = commands[at+2];
    uint exclude = commands[at+3], authoredOrder = commands[at+4];
    if (kind == 5 || kind == 6 || kind == 7 || kind == 15 || kind == 16) return rankedRecipients(s,row,when,order);
    if (kind == 21) return coverRecipients(s,count,order);
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
        if (kind == 12 || kind == 13)
        {
            for (uint who = 0; who < 5; who++)
            {
                bool present = stateMember(s,who,int(commands[at+5]),exclude);
                if (kind == 12 && !present || kind == 13 && present) pool &= ~(1U << who);
            }
        }
        else if (exclude != 0) pool &= ~(1U << d.owner);
        pool &= ~s.downMask;
        for (uint who = 0; who < 5; who++) if ((pool & (1U << who)) != 0) slots[size++] = who;
    }
    uint mask = 0, written = 0; order = 0;
    for (uint i = 0; i < size; i++) if ((s.downMask & (1U << slots[i])) == 0)
    { mask |= 1U << slots[i]; order |= (slots[i]+1) << (3*written++); }
    return mask;
}
