// Damage selectors use live logical actors; predicates still use sampled world.
[noinline]
uint enemyDamageMask(inout Runtime s, Definition d, uint inherited, out uint packedOrder)
{
    WORLD_FIELDS_ENEMY_SELECT(s,d,inherited,packedOrder) packedOrder = 0;
    if (s.combat == 0) { packedOrder = 1; return 1; }
    if (d.damageRoute < 2)
    {
        uint target = d.damageRoute == 1 ? 0 : inherited;
        if (target < s.targetCount && s.targetAlive[target] != 0) { packedOrder = target+1; return 1U << target; }
        return 0;
    }
    if (d.damageRoute == 9) return enemyAttackMask(s,d.damageCount,packedOrder);
    uint order[8], count = 0; uint sequence = enemySpawnSequence(s);
    // Canonical ranked HP rules keep the body first for descending ranks and
    // last for lowest HP. Adds tie by stable input/spawn order.
    if ((d.damageRoute == 2 || d.damageRoute == 3 || d.damageRoute == 4 || d.damageRoute == 7) && s.targetAlive[0] != 0) order[count++] = 0;
    uint first = 0xffffffff;
    if (d.damageRoute == 6)
    {
        first = (s.automaticAddAim & (1U << d.owner)) != 0 ? automaticEnemyAim(s,sequence) : s.aim[d.owner];
        if (first == 0xffffffff || s.targetAlive[first] == 0)
        {
            first = 0xffffffff;
            for (uint rank = 1; rank < s.targetCount; rank++)
            {
                uint encoded = (sequence >> (4*rank)) & 15; if (encoded == 0) break;
                uint target = encoded-1;
                if (s.targetAlive[target] != 0) { first = target; break; }
            }
            if (first == 0xffffffff && s.targetAlive[0] != 0) first = 0;
        }
    }
    if (first != 0xffffffff) order[count++] = first;
    for (uint rank = 1; rank < s.targetCount; rank++)
    {
        uint encoded = (sequence >> (4*rank)) & 15; if (encoded == 0) break;
        uint target = encoded-1;
        if (s.targetAlive[target] == 0 || target == first) continue;
        uint at = count++;
        if (d.damageRoute == 3 || d.damageRoute == 4 || d.damageRoute == 5)
        {
            uint64_t key = d.damageRoute == 3 ? s.targetMaxHP[target] : s.targetHP[target];
            while (at > 0 && order[at-1] != 0)
            {
                uint prior = order[at-1]; uint64_t previous = d.damageRoute == 3 ? s.targetMaxHP[prior] : s.targetHP[prior];
                bool before = d.damageRoute == 5 ? f64Less(key,previous) : f64Less(previous,key);
                if (!before) break;
                order[at] = prior; at--;
            }
        }
        order[at] = target;
    }
    if ((d.damageRoute == 5 || d.damageRoute == 8 || d.damageRoute == 6 && first != 0) && s.targetAlive[0] != 0) order[count++] = 0;
    uint mask = 0;
    for (uint i = 0; i < min(count,d.damageCount); i++) { mask |= 1U << order[i]; packedOrder |= (order[i]+1) << (4*i); }
    return mask;
}
uint enemyMaskCount(uint mask)
{
    uint count = 0; for (uint i = 0; i < 8; i++) count += (mask >> i) & 1;
    return count;
}
[noinline]
void logDamagePacket(inout Runtime s, Definition d, uint row, uint mask, uint basis, uint hit,
                     uint64_t share, uint64_t weighted, uint packedOrder, uint64_t when, uint depth, uint output)
{
    if (s.traceTotal == 0x7fffffff) { s.error = 2; return; }
    s.traceTotal++;
    if (s.traceMode != 1) return;
    if (s.traceCount == P_TRACE) { s.error = 8; return; }
    uint index = s.traceCount++, at = output+P_TRACE_BASE+index*P_TRACE_WORDS;
    results[at] = row; storeNumber(at+1,when); results[at+3] = s.timerEpoch[row];
    results[at+4] = s.combat != 0 ? s.targetGeneration[basis] : s.generation;
    results[at+5] = depth; storeNumber(at+6,s.due[row]);
    at = output+P_DAMAGE_TRACE_BASE+index*10;
    results[at] = mask; results[at+1] = basis; results[at+2] = hit; results[at+3] = d.damageHits;
    storeNumber(at+4,share); results[at+6] = packedOrder; results[at+7] = enemyMaskCount(mask); storeNumber(at+8,weighted);
}
