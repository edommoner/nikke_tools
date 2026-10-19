// Active bullet-lifetime carriers keep resident order without scanning ordinary
// equipment/passive rows on every physical shot. Encoded links use zero as nil.
void unlinkBulletCarrier(inout Runtime s, uint row)
{
    if (s.bulletLinked[row] == 0) return;
    uint previous = s.bulletPrev[row], next = s.bulletNext[row];
    if (previous != 0) s.bulletNext[previous-1] = next; else s.bulletHead = next;
    if (next != 0) s.bulletPrev[next-1] = previous; else s.bulletTail = previous;
    s.bulletPrev[row] = 0; s.bulletNext[row] = 0; s.bulletLinked[row] = 0; s.bulletCount--;
}
void resetBulletCarrier(inout Runtime s, uint row)
{
    unlinkBulletCarrier(s,row);
    if (s.bulletInitialized[row] == 0) return;
    for (uint who = 0; who < 5; who++) { s.recipientBullets[row*5+who] = 0; s.recipientStacks[row*5+who] = 0; }
    s.bulletLeft[row] = 0; s.bulletInitialized[row] = 0;
}
void prepareBulletActivation(inout Runtime s, uint row, uint mask, bool wasLive, bool lazy, uint previousStack)
{
    Definition d = residentDefinition(s,row); s.bulletInitialized[row] = 1;
    if (lazy) s.bulletLeft[row] = int(d.bulletDuration);
    else
    {
        for (uint who = 0; who < 5; who++)
        {
            uint at = row*5+who;
            bool had = wasLive && s.recipientBullets[at] != 0;
            uint stack = s.recipientStacks[at] != 0 ? s.recipientStacks[at] : previousStack;
            s.recipientBullets[at] = (mask & (1U << who)) != 0 ? d.bulletDuration : 0;
            s.recipientStacks[at] = (mask & (1U << who)) != 0 && d.maxStack != 1 ? (had ? checkedStackIncrement(stack,d.maxStack,s.error) : 1) : 0;
            if (s.error!=0) return;
        }
        s.bulletLeft[row] = -1;
    }
    if (s.bulletLinked[row] == 0)
    {
        s.bulletPrev[row] = s.bulletTail; s.bulletNext[row] = 0;
        if (s.bulletTail != 0) s.bulletNext[s.bulletTail-1] = row+1; else s.bulletHead = row+1;
        s.bulletTail = row+1; s.bulletLinked[row] = 1; s.bulletCount++;
    }
}
void resolveBulletTargets(inout Runtime s, uint row)
{
    if (residentDefinition(s,row).bulletDuration == 0 || s.bulletLeft[row] < 0) return;
    for (uint who = 0; who < 5; who++) s.recipientBullets[row*5+who] = (s.activeRecipients[row] & (1U << who)) != 0 ? uint(s.bulletLeft[row]) : 0;
    s.bulletLeft[row] = -1;
}
