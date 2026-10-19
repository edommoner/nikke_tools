// Base attack is input data. The GPU derives rank per actor birth epoch;
// each selection still filters the live actor set before taking N recipients.
[noinline]
uint buildEnemyAttackOrder(inout Runtime s, bool livingOnly)
{
    uint order[8], count = 0; uint sequence = enemySpawnSequence(s);
    for (uint rank = 0; rank < s.targetCount; rank++)
    {
        uint encoded = (sequence >> (4*rank)) & 15; if (encoded == 0) break;
        uint target = encoded-1;
        if (livingOnly && s.targetAlive[target] == 0) continue;
        uint64_t attack = loadNumber(s.inputBase+P_TARGET_ATTACK_BASE+target*2);
        uint at = count++;
        while (at > 0)
        {
            uint prior = order[at-1];
            uint64_t previous = loadNumber(s.inputBase+P_TARGET_ATTACK_BASE+prior*2);
            if (!f64Less(previous,attack)) break;
            order[at] = prior; at--;
        }
        order[at] = target;
    }
    uint packed = 0;
    for (uint rank = 0; rank < count; rank++) packed |= (order[rank]+1) << (4*rank);
    return packed;
}
[noinline]
bool initializeEnemyAttackOrder(inout Runtime s)
{
    for (uint target = 0; target < 8; target++)
    {
        uint64_t value = loadNumber(s.inputBase+P_TARGET_ATTACK_BASE+target*2);
        if (target >= s.targetCount) { if (value != 0) return false; continue; }
        if (!f64Finite(value) || f64Less(value,0) ||
            f64Less((uint64_t(0x46293e59) << 32) | 0x39a08cea,value)) return false; // 1e30
    }
    return true;
}
[noinline]
uint enemyAttackMask(inout Runtime s, uint requested, out uint packedOrder)
{
#ifdef PORTABLE_ATTACK_RANK_SCAN_REFERENCE
    uint order = buildEnemyAttackOrder(s,true);
#else
    if (s.enemyAttackOrder == 0) s.enemyAttackOrder = buildEnemyAttackOrder(s,false);
    uint order = s.enemyAttackOrder;
#endif
    uint mask = 0, count = 0; packedOrder = 0;
    for (uint rank = 0; rank < s.targetCount && count < requested; rank++)
    {
        uint encoded = (order >> (4*rank)) & 15;
        if (encoded == 0) break;
        uint target = encoded-1;
        if (s.targetAlive[target] == 0) continue;
        mask |= 1U << target; packedOrder |= encoded << (4*count++);
    }
    return mask;
}
