// Immutable per-event definition masks are packed once from static descriptors.
// Validate against descriptors, including the zero padding beyond definition count.
[noinline]
bool validEventCandidates(inout Runtime s)
{
    for (uint word = 0; word < P_MASK_WORDS; word++)
    {
        uint expected[64]; for (uint event = 0; event < 64; event++) expected[event] = 0;
        for (uint row = word*32; row < min(s.count,(word+1)*32); row++)
            for (uint slot = 0; slot < s.defs[row].triggerCount; slot++)
            {
                uint event = commands[s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8];
                if (event >= 64) return false;
                expected[event] |= 1U << (row%32);
            }
        for (uint event = 0; event < 64; event++)
            if (commands[s.inputBase+P_EVENT_CANDIDATE_BASE+event*P_MASK_WORDS+word] != expected[event]) return false;
    }
    return true;
}
[noinline]
uint nextEventCandidate(inout Runtime s, uint event, uint cursor)
{
    if (event >= 64) return s.count;
    uint first = cursor/32;
    for (uint word = first; word < P_MASK_WORDS; word++)
    {
        uint mask = commands[s.inputBase+P_EVENT_CANDIDATE_BASE+event*P_MASK_WORDS+word];
        if (word == first) mask &= 0xffffffffU << (cursor%32);
        if (mask != 0) return word*32+uint(firstbitlow(mask));
    }
    return s.count;
}
