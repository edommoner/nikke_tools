// Burst numeric updates are shared by every backend. Gauge eligibility is
// latched at the end of the controller tick, as in the pinned CPU state.
uint64_t burstHitGain(inout Runtime s,uint who,uint64_t coefficient,uint hits,uint64_t multiplier,uint64_t when)
{
    uint64_t gain=f64Mul(f64Mul(coefficient,f64FromI64(hits)),multiplier);
    if((s.quantityMask & 128)!=0)
        gain=f64Add(gain,f64Mul(f64FromI64(hits),readStat(s,who,S_burst_charge_speed_pct,when)));
    return gain;
}
void addBurstGauge(inout Runtime s, uint64_t amount)
{
    if (!f64Finite(amount)) { s.error = 16; return; }
    if (s.gaugeCharging == 0 || !f64Less(0,amount)) return;
    uint64_t next = f64Add(s.gauge,amount);
    if (!f64Finite(next)) { s.error = 16; return; }
    s.gauge = smaller(HUNDRED,next);
}
void reduceBurstReady(inout Runtime s, uint recipients, uint64_t amount, uint64_t when)
{
    if (!f64Finite(amount)) { s.error = 16; return; }
    for (uint who = 0; who < 5; who++) if ((recipients & (1U << who)) != 0)
    {
        uint64_t ready = f64Add(s.ready[who],amount ^ F64_SIGN);
        if (!f64Finite(ready)) { s.error = 16; return; }
        s.ready[who] = larger(when,ready);
    }
}
uint64_t burstCooldownReduction(inout Runtime s, uint who, uint64_t when)
{
#ifndef PORTABLE_BURST_SCAN_REFERENCE
    // A full buff query also resolves unrelated mapped lazy recipients.
    if ((s.burstModifierMask & 1) == 0 && s.lazyMappedPendingCount == 0) return 0;
#endif
    return readStat(s,who,S_burst_cooldown,when);
}
void setBurstReady(inout Runtime s, uint who, uint64_t when)
{
    uint64_t reduction = burstCooldownReduction(s,who,when);
    s.cooldownApplied[who] = reduction;
    uint64_t duration = f64Add(s.cooldown[who],reduction ^ F64_SIGN);
    s.ready[who] = f64Add(when,larger(0,duration));
    if (!f64Finite(reduction) || !f64Finite(duration) || !f64Finite(s.ready[who])) s.error = 16;
}
void reconcileBurstCooldowns(inout Runtime s, uint64_t when)
{
    for (uint who = 0; who < 5 && s.error == 0; who++)
    {
        uint64_t current = burstCooldownReduction(s,who,when);
        uint64_t extra = f64Add(current,s.cooldownApplied[who] ^ F64_SIGN);
        if (!f64Finite(current) || !f64Finite(extra)) { s.error = 16; return; }
        if (f64Less(when,s.ready[who]) && f64Less(0,extra)) reduceBurstReady(s,1U << who,extra,when);
        s.cooldownApplied[who] = 0;
    }
}
