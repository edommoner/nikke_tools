// Body first, then stable add birth order. The sequence includes dormant slots;
// selection filters live actors and generation changes invalidate the cache.
[noinline]
uint buildEnemySpawnSequence(inout Runtime s)
{
    uint order[8], count = 0;
    for (uint target = 0; target < s.targetCount; target++)
    {
        uint at = count++;
        while (at > 0)
        {
            uint prior = order[at-1];
            if (prior == 0 || s.enemyBirth[target] >= s.enemyBirth[prior]) break;
            order[at] = prior; at--;
        }
        order[at] = target;
    }
    uint packed = 0;
    for (uint rank = 0; rank < count; rank++) packed |= (order[rank]+1) << (4*rank);
    return packed;
}
[noinline]
uint enemySpawnSequence(inout Runtime s)
{
#ifdef PORTABLE_SPAWN_ORDER_SCAN_REFERENCE
    return buildEnemySpawnSequence(s);
#else
    if (s.enemySpawnOrder == 0) s.enemySpawnOrder = buildEnemySpawnSequence(s);
    return s.enemySpawnOrder;
#endif
}
