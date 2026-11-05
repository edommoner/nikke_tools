// Native automatic add-bucket aim resolves the oldest currently live add.
// Explicit API slots retain their existing physical and logical fallback rules.
[noinline]
uint automaticEnemyAim(inout Runtime s, uint sequence)
{
    for (uint rank = 1; rank < s.targetCount; rank++)
    {
        uint encoded = (sequence >> (4*rank)) & 15;
        if (encoded == 0) break;
        uint target = encoded-1;
        if (s.targetAlive[target] != 0) return target;
    }
    return s.targetAlive[0] != 0 ? 0 : 0xffffffff;
}
