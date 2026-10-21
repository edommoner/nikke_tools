// A landed packet heals its attacker. The receipt phase decides when to call.
// Same operation order as the installed native _apply_lifesteal, in binary64.
[noinline]
bool applyLifestealState(inout Runtime s, uint who, uint64_t damage, uint64_t when)
{
    if ((s.downMask & (1U << who)) != 0) return false;
    uint64_t rate=plainQuantity(s,who,S_lifesteal_pct,when);
    if (!f64Finite(rate)) { s.error=16;return false; }
    if (!f64Less(0,rate)) return false;
    uint64_t amount=f64Mul(f64Div(f64Mul(damage,rate),HUNDRED),healMultiplier(s,who,who,when));
    if (!f64Finite(amount)) { s.error=16;return false; }
    uint64_t before=s.hp[who];s.hp[who]=storageBodyHeal(s,who,amount,when);
    s.healing[who]=f64Add(s.healing[who],larger(0,f64Add(s.hp[who],before ^ F64_SIGN)));
    if (!f64Finite(s.healing[who])) { s.error=16;return false; }
    syncHealthActor(s,who,when);
    return true; // Positive rate notifies even when capped or zero-potency.
}
