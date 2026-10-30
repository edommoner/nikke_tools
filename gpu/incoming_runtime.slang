// Body-layer attacks. Boss scheduling, target choice and protection layers
// will feed this same boundary; they are not synthesized by the CPU adapter.
bool liveMarker(inout Runtime s, uint who, uint stat, uint64_t when)
{
#ifndef PORTABLE_INCOMING_SCAN_REFERENCE
    uint bit = stat == S_invincible ? 1 : stat==S_focus_fire ? 64 : 2;
    if ((s.incomingMask & bit) == 0) return false;
#endif
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint row = s.orderedRows[pass];
        if (residentDefinition(s,row).kind == 0 && residentDefinition(s,row).stat == stat && queryRecipient(s,row,who,when)) return true;
    }
    return false;
}
[noinline]
uint64_t incomingBodyDamage(inout Runtime s, uint who, uint64_t attack, uint64_t coefficient, uint64_t when
#ifdef PORTABLE_COVER_DEFENSE
    ,out uint64_t receivedSnapshot
#endif
)
{
    uint64_t amount = larger(0,f64Add(attack,effectiveDefense(s,who,when) ^ F64_SIGN));
    amount = f64Div(f64Mul(amount,coefficient),HUNDRED);
    uint64_t received = 0;
#ifdef PORTABLE_INCOMING_SCAN_REFERENCE
    received = plainQuantity(s,who,S_received_dmg_pct,when);
#else
    if ((s.incomingMask & 4) != 0) received = plainQuantity(s,who,S_received_dmg_pct,when);
#endif
#ifdef PORTABLE_COVER_DEFENSE
    receivedSnapshot=received;
#endif
    amount = f64Mul(amount,larger(0,f64Add(ONE,f64Div(received,HUNDRED))));
    if (!f64Finite(amount)) { s.error = 16; return 0; }
    return larger(ONE,amount);
}
[noinline]
void knockDown(inout Runtime s, uint who, uint64_t when)
{
    for (uint key = 0; key < s.resourceCount; key++) setResourceValue(s,who*P_RESOURCE_KEYS+key,0);
    uint bit = 1U << who; s.downMask |= bit; s.hp[who] = 0; s.hpPct[who] = 0;
    s.hpPendingMask &= ~bit; s.hpDirtyMask &= ~bit;
    if(revivalEnabled(s)) results[revivalAt(s)+who]=0;
    for (uint pass = 0; pass < (revivalEnabled(s) ? s.orderedCount : s.carrierCount); pass++)
    {
        uint row=revivalEnabled(s) ? s.orderedRows[pass] : pass;
        Definition d = residentDefinition(s,row);
#ifdef PORTABLE_WEIGHTED_INCOMING
        // Independent cover carrier lifetime survives body-recipient removal.
        if(d.stat==WGT_COVER_STAT)continue;
#endif
        if ((d.kind == 0 || d.kind == 4) && s.alive[row] != 0 && s.lazyPending[row] == 0 && (d.flags&1024U)==0 && (!revivalEnabled(s) || (s.activeRecipients[row]&bit)!=0))
        {
            revivalRemember(s,who,row);
            s.activeRecipients[row] &= ~bit;
            if(revivalEnabled(s)) storeCarrierOrder(s,row,filterRemovalOrder(carrierOrder(s,row),s.activeRecipients[row]&31,3,21));
            if (d.bulletDuration != 0) { s.recipientBullets[row*5+who] = 0; s.recipientStacks[row*5+who] = 0; }
            if (s.activeRecipients[row] == 0) { unlinkBulletCarrier(s,row); s.alive[row] = 0; s.stacks[row] = 0; }
        }
    }
#ifdef PORTABLE_HEAL_CHARGE
    retireHealChargeDown(s,who);
#endif
    for (uint row = 0; row < s.count; row++)
    {
        Definition d = readDefinition(s.inputBase,row);
        if (d.owner == who) for (uint slot = 0; slot < d.triggerCount; slot++)
        {
            uint event = commands[s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8];
            if (event != 26) s.counters[row*8+slot] = 0;
        }
    }
    s.modeIndex[who] = -1; s.modeEpoch[who]++; s.appliedEpoch[who] = s.modeEpoch[who]; s.modeEntryUntil[who] = F64_SIGN | ONE; s.modeEntryPhase[who]=0;
    s.charging[who] = 0; s.reloadUntil[who] = F64_SIGN | ONE; s.postReloadUntil[who] = F64_SIGN | ONE; s.pendingAutoReload[who] = 0; WORLD_CONTROL_RELOAD(s,who)
#ifdef PORTABLE_COORDINATE_MANUAL_ACTIONS
    resetManualCover(s,who);
#endif
    syncHealth(s,when);
    revivalRecord(s,1,who,when,0);
}
void writeIncoming(inout Runtime s, uint output)
{
    for (uint who = 0; who < 5; who++)
    {
        uint at = output+who*4; storeNumber(at,f64Add(s.receivedDamage[who],s.receivedDamageCorrection[who]));
        results[at+2] = s.receivedHits[who]; results[at+3] = uint((s.downMask & (1U << who)) != 0);
    }
}
