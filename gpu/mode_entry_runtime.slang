// Same reload arithmetic and carriers as normal reload, using the restored base gun.
// Each actual mode tick queries the duration; only its first tick latches the wait.
[noinline]
bool advanceModeEntry(inout Runtime s,inout Weapon w,uint who,uint64_t when)
{
    int index=s.modeIndex[who];if(index<0) return false;
    uint at=s.inputBase+P_MODE_BASE+uint(index)*P_MODE_WORDS,policy=commands[at+30];
    uint64_t delay=loadNumber(at+28);
    if(policy==2)
    {
        Weapon baseWeapon=w;baseWeapon.reloadTime=s.reloadTime[who];
        delay=reloadDuration(s,baseWeapon,who,when);
#ifdef PORTABLE_ENTRY_RELOAD_DIAGNOSTIC
        uint head=s.resourceOutput+P_MODE_ENTRY_STATE_BASE+10,count=results[head];
        if(count>=96) { s.error=64;return true; }
        results[head]=count+1;uint record=head+8+count*5;
        results[record]=who;storeNumber(record+1,when);storeNumber(record+3,delay);
#endif
    }
    if(s.error!=0) return true;
    if(s.modeEntryPhase[who]==1)
    { s.modeEntryUntil[who]=f64Add(when,delay);s.modeEntryPhase[who]=2; }
    if(s.modeEntryPhase[who]!=2) return false;
    if(!f64Less(s.modeEntryUntil[who],0))
    {
        if(f64Less(when,s.modeEntryUntil[who])) return true;
        s.modeEntryUntil[who]=F64_SIGN|ONE;
    }
    // A negative fixed duration is not clamped; its negative until stays observable.
    s.modeEntryPhase[who]=0;
    w.capacity=w.sentinelMode!=0 ? 999999 : ammoInstantCapacity(s,who,when);
    s.modeMagazine[who]=w.capacity;s.ammo[who]=w.capacity;
    if(w.mode!=1) s.nextShot[who]=when;
    s.charging[who]=0;s.chargeStartedAt[who]=when;
    return false;
}
