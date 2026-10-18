// This runs once per physical packet, after hit notifications and before
// last_bullet. Damage/pellet/muzzle callbacks never consume it independently.
[noinline]
void consumeBulletBuffs(inout Runtime s, uint who, uint64_t when, uint output)
{
    uint retired[P_CARRIERS], count = 0; bool changed = false;
#ifdef PORTABLE_BULLET_SCAN_REFERENCE
    uint visits = s.orderedCount;
#else
    uint visits = s.bulletCount, encoded = s.bulletHead;
#endif
    for (uint pass = 0; pass < visits && s.error == 0; pass++)
    {
#ifdef PORTABLE_BULLET_SCAN_REFERENCE
        uint row = s.orderedRows[pass];
#else
        uint row = encoded-1; encoded = s.bulletNext[row];
#endif
        Definition d = residentDefinition(s,row);
        if (d.bulletDuration == 0 || s.alive[row] == 0 || f64Equal(s.activated[row],when) && d.bulletBound == 0) continue;
        if (s.lazyPending[row] != 0) ensureLazyRecipients(s,row,when);
        if (s.error != 0) break;
        uint at = row*5+who;
        if (s.recipientBullets[at] != 0)
        {
            s.recipientBullets[at]--;
            if (s.recipientBullets[at] == 0)
            {
                s.activeRecipients[row] &= ~(1U << who); changed = true;
                uint remaining = 0; for (uint actor = 0; actor < 5; actor++) remaining |= s.recipientBullets[row*5+actor];
                if (remaining == 0) retired[count++] = row;
            }
        }
        else if (d.owner == who && s.bulletLeft[row] >= 0)
        {
            s.bulletLeft[row]--;
            if (s.bulletLeft[row] <= 0) { retired[count++] = row; changed = true; }
        }
    }
    // All removals precede callbacks. A later row's lazy rank still sees the
    // same active collection as the CPU loop until its removal phase starts.
    uint begin = s.removalCount;
    for (uint i = 0; i < count && s.error == 0; i++) queueCarrierEnd(s,retired[i]);
    if (s.error != 0) return;
    if (s.removalCount > begin) dispatch(s,9,0,0,int(begin),when,output);
    else if (changed)
    {
        syncHealth(s,when);
        if (s.hpWatchCount != 0) dispatch(s,7,0,0,0,when,output);
    }
}
