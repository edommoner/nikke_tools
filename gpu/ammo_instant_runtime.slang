#include "ammo_instant_numeric.slang"
// Presence flags do not read numeric value/stack magnitude.
[noinline]
bool hasInfiniteAmmo(inout Runtime s, uint who, uint64_t when)
{
    ensureNativeNumeric(s,who,when);
#ifdef PORTABLE_INFINITE_SCAN_REFERENCE
    uint count = s.orderedCount;
#else
    uint count = s.infiniteRowCount;
#endif
    for (uint i = 0; i < count; i++)
    {
#ifdef PORTABLE_INFINITE_SCAN_REFERENCE
        uint row = s.orderedRows[i];
#else
        uint row = s.infiniteRows[i];
#endif
        Definition d = residentDefinition(s,row);
        if (d.kind == 0 && d.stat == S_infinite_ammo && queryRecipient(s,row,who,when)) return true;
    }
    return false;
}

// Shared cartridge capacity and immediate refill/removal. Integer arithmetic
// is signed and widened before addition; Python flat removal may go negative.
[noinline]
uint ammoInstantCapacity(inout Runtime s, uint who, uint64_t when)
{
    int mode = s.modeIndex[who];
    uint base = s.frameAmmoActive[who] != 0 ? s.frameAmmoBase[who] : s.capacity[who];
    if (mode < 0) return fullCapacity(s,who,base,true,when);
    if (commands[s.inputBase+P_MODE_BASE+uint(mode)*P_MODE_WORDS+21] != 0) return fullCapacity(s,who,base,true,when);
    if (s.modeCapacityEpoch[who] == s.modeEpoch[who]) return s.modeMagazine[who];
    uint at = s.inputBase+P_MODE_BASE+uint(mode)*P_MODE_WORDS;
    uint capacity = modeCapacityReference(s,uint(mode)) != 0 ? referencedModeCapacity(s,who,uint(mode),when) : fullCapacity(s,who,commands[at+1],commands[at+23] != 0,when);
    if (s.error != 0) return 0;
    s.modeMagazine[who] = capacity; s.modeCapacityEpoch[who] = s.modeEpoch[who];
    return capacity;
}
[noinline]
void applyAmmoInstant(inout Runtime s, Definition d, uint mask, uint64_t when)
{
    if (mask == 0) return;
    int64_t flat;uint64_t fraction;
    if(!prepareAmmoInstant(d.kind,d.value,flat,fraction)){s.error=16;return;}
    for (uint who = 0; who < 5 && s.error == 0; who++) if ((mask & (1U << who)) != 0)
    {
        uint capacity = ammoInstantCapacity(s,who,when);
        int result;
        if(!ammoInstantResult(d.kind,capacity,s.ammo[who],flat,fraction,result)){s.error=16;return;}
        s.ammo[who] = result;
        if (s.reloadCancelOnFull[who] != 0 && f64Less(0,s.reloadUntil[who]) && result >= int64_t(capacity))
        {
            // Cancellation does not complete a reload or issue full_reload.
            s.reloadUntil[who] = F64_SIGN | ONE;
        }
    }
}
