// Shared cartridge capacity and immediate refill/removal. Integer arithmetic
// is signed and widened before addition; Python flat removal may go negative.
uint ammoInstantCapacity(inout Runtime s, uint who, uint64_t when)
{
    int mode = s.modeIndex[who];
    if (mode < 0) return fullCapacity(s,who,s.capacity[who],true,when);
    if (s.modeCapacityEpoch[who] == s.modeEpoch[who]) return s.modeMagazine[who];
    uint at = s.inputBase+P_MODE_BASE+uint(mode)*P_MODE_WORDS;
    uint capacity = fullCapacity(s,who,commands[at+1],commands[at+23] != 0,when);
    s.modeMagazine[who] = capacity; s.modeCapacityEpoch[who] = s.modeEpoch[who];
    return capacity;
}
[noinline]
void applyAmmoInstant(inout Runtime s, Definition d, uint mask, uint64_t when)
{
    if (mask == 0) return;
    uint status; int64_t flat = 0;
    uint64_t fraction = 0;
    if (d.kind == 13) fraction = f64Div(d.value,HUNDRED);
    else
    {
        flat = int64_t(f64ToI64(d.value,1,status));
        if (status != 0)
        {
            if (!f64Less(0,d.value)) { s.error = 16; return; }
            flat = int64_t(0x7fffffffffffffff);
        }
    }
    for (uint who = 0; who < 5 && s.error == 0; who++) if ((mask & (1U << who)) != 0)
    {
        uint capacity = ammoInstantCapacity(s,who,when);
        int64_t change = flat;
        if (d.kind == 13)
        {
            // Preserve max_ammo * (value/100), followed by ties-to-even round.
            uint64_t amount = f64Mul(f64FromI64(capacity),fraction);
            if (!f64Finite(amount)) { s.error = 16; return; }
            change = int64_t(f64ToI64(amount,0,status));
            if (status != 0) change = f64Less(amount,0) ? int64_t(uint64_t(1) << 63) : int64_t(0x7fffffffffffffff);
        }
        // Saturate before addition so an accepted i64 delta cannot overflow.
        int64_t current = int64_t(s.ammo[who]), result;
        if (change >= int64_t(capacity)-current) result = capacity;
        else if (d.kind == 13 && change <= -current) result = 0;
        else
        {
            if (change < int64_t(-2147483647)-1-current) { s.error = 16; return; }
            result = current+change;
        }
        s.ammo[who] = int(result);
        if (s.reloadCancelOnFull[who] != 0 && f64Less(0,s.reloadUntil[who]) && result >= int64_t(capacity))
        {
            // Cancellation does not complete a reload or issue full_reload.
            s.reloadUntil[who] = F64_SIGN | ONE;
        }
    }
}
