// Automatic cadence, shared warm/spread counter, and partial reload lifecycle.
uint64_t weaponInterval(inout Runtime s, Weapon w, uint who, uint64_t when)
{
    uint64_t rate = w.rateMin;
    if (w.mode == 2) rate = f64Add(rate,f64Div(f64Mul(f64Add(w.rateMax,rate ^ F64_SIGN),smaller(s.warm[who],w.warmLimit)),w.warmLimit));
    uint64_t speed = larger(uint64_t(0x3f847ae1) << 32 | 0x47ae147b,f64Add(ONE,f64Div(readStat(s,who,S_attack_speed_pct,when),HUNDRED))); // .01
    if (w.mode == 0 && w.rawRate == 0 && f64Equal(speed,ONE)) return w.interval;
    return f64Div(ONE,f64Mul(rate,speed));
}
void coolWeapon(inout Runtime s, Weapon w, uint who, uint64_t when)
{
    if (w.mode != 2 || f64Zero(s.warm[who])) return;
    uint64_t idle = f64Add(when,s.lastFire[who] ^ F64_SIGN);
    uint64_t interval = !f64Zero(s.lastInterval[who]) ? s.lastInterval[who] : weaponInterval(s,w,who,when);
    if (!f64Less(f64Mul(interval,uint64_t(0x3ff80000) << 32),idle)) return; // 1.5
    s.warm[who] = larger(0,f64Add(s.warm[who],f64Mul(f64Div(w.warmLimit,w.coolTime),idle) ^ F64_SIGN)); s.lastFire[who] = when;
}
void advanceWarmup(inout Runtime s, Weapon w, uint who, uint64_t when, uint64_t interval)
{
    uint64_t cap = larger(w.warmLimit,s.spreadShots[who]);
    if ((w.mode == 2 || !f64Zero(s.spreadShots[who])) && f64Less(s.warm[who],cap))
        s.warm[who] = smaller(cap,f64Add(s.warm[who],larger(0,f64Add(ONE,f64Div(readStat(s,who,S_mg_warmup_speed_pct,when),HUNDRED)))));
    if (w.mode == 2) { s.lastFire[who] = when; s.lastInterval[who] = interval; }
}
uint64_t reloadDuration(inout Runtime s, Weapon w, uint who, uint64_t when)
{
    return f64Mul(w.reloadTime,larger(0,f64Add(ONE,f64Div(readStat(s,who,S_reload_speed_pct,when),HUNDRED) ^ F64_SIGN)));
}
void beginReload(inout Runtime s, Weapon w, uint who, uint64_t when)
{
    s.reloadUntil[who] = f64Add(when,reloadDuration(s,w,who,when)); s.charging[who] = 0; WORLD_CONTROL_RELOAD(s,who)
}
bool completeReload(inout Runtime s, Weapon w, uint who, uint64_t when, uint output)
{
    uint rawCapacity = s.modeIndex[who] < 0 ? s.capacity[who] : commands[s.inputBase+P_MODE_BASE+uint(s.modeIndex[who])*P_MODE_WORDS+1];
    w.capacity = fullCapacity(s,who,rawCapacity,w.ammoBuffs != 0,when);
    if (s.error != 0) return false;
    if (s.modeIndex[who] >= 0) { s.modeMagazine[who] = w.capacity; s.modeCapacityEpoch[who] = s.modeEpoch[who]; }
    uint64_t fraction = ONE;
    if (s.modeIndex[who] < 0)
        fraction = smaller(ONE,f64Mul(f64Div(ONE,f64FromI64(s.clipCount[who])),larger(0,f64Add(ONE,f64Div(readStat(s,who,S_reload_ratio_pct,when),HUNDRED)))));
    if (f64Less(fraction,ONE))
    {
        uint status; uint64_t gain = f64ToI64(f64Add(f64Mul(f64FromI64(w.capacity),fraction),uint64_t(0x3fe00000) << 32),2,status);
        if (status != 0 || gain > 0x7fffffff) { s.error = 2; return false; }
        s.ammo[who] = int(min(int64_t(w.capacity),int64_t(s.ammo[who])+int64_t(max(1,uint(gain)))));
        if (s.ammo[who] < int(w.capacity)) { beginReload(s,w,who,when); return false; }
    }
    else s.ammo[who] = w.capacity;
    s.reloadUntil[who] = F64_SIGN | ONE; dispatch(s,0,19,who,0,when,output); s.nextShot[who] = when;
    if (s.modeIndex[who] < 0 && !f64Zero(s.postReloadDelay[who])) s.postReloadUntil[who] = f64Add(when,s.postReloadDelay[who]);
    return s.error == 0;
}
