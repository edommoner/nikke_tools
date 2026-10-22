// Shared weapon-frame phases; math, callback order and snapshots are unchanged.
[noinline]
void prepareWeaponFrame(inout Runtime s,uint who,uint64_t when,uint output,out uint target,out Weapon w,out bool ready)
{
    ready=false;
    if (s.weaponEnabled[who] == 0 || (s.downMask & (1U << who)) != 0 || statusStunned(s,who)) return;
    target = aimedTarget(s,who); if (target == 0xffffffff) return;
    s.target = target; selectWeapon(s,who,when,w);
    if (s.error != 0) return; WORLD_MANUAL_SWAP(s,w,who,when) WORLD_CONTROL_TICK(s,who,when,output)
    if(advanceModeEntry(s,w,who,when)) return;
    if(s.modeIndex[who]>=0 && w.sentinelMode==0 && w.shotLimit>=0 && uint(w.shotLimit)==commands[s.inputBase+P_MODE_BASE+uint(s.modeIndex[who])*P_MODE_WORDS+1]) w.shotLimit=int(w.capacity);
    if (!WORLD_MANUAL_ENABLED(s,who) && s.modeIndex[who] < 0 && f64Less(0,s.reloadUntil[who]) && hasInfiniteAmmo(s,who,when))
    { s.reloadUntil[who] = F64_SIGN | ONE; s.nextShot[who] = larger(s.nextShot[who],when); }
    if (!WORLD_MANUAL_ENABLED(s,who) && s.modeIndex[who] < 0 && f64Less(s.reloadUntil[who],0)) s.ammo[who] = min(s.ammo[who],int(w.capacity));
    if (WORLD_RELOAD_ACTIVE(s,who,!f64Less(s.reloadUntil[who],0)) && (s.modeIndex[who] < 0 || w.reloadAllowed != 0))
    {
        if (f64Less(when,s.reloadUntil[who])) return;
        if (!completeReload(s,w,who,when,output)) return; WORLD_RELOAD_AFTER_COMPLETE(s,who)
        selectWeapon(s,who,when,w); // A completion callback may change the mode.
    }
    if (s.modeIndex[who] < 0 && !f64Less(s.postReloadUntil[who],0))
    {
        if (f64Less(when,s.postReloadUntil[who])) return;
        s.postReloadUntil[who] = F64_SIGN | ONE; s.nextShot[who] = when;
    }
    s.frameAmmoActive[who] = 1;
    s.physicalGaugeOwner=who+1;s.physicalGaugeGain=w.gain;
    s.frameAmmoBase[who] = s.modeIndex[who] < 0 ? s.capacity[who] : w.sentinelMode != 0 ? 999999 : commands[s.inputBase+P_MODE_BASE+uint(s.modeIndex[who])*P_MODE_WORDS+1];
    WORLD_PAUSE_WEAPON(s,w,who,when) coolWeapon(s,w,who,when);
    ready=true;
}

[noinline]
void advanceWeaponCharge(inout Runtime s,inout Weapon w,uint who,uint64_t when,uint output,uint epoch,int mode,out bool ready)
{
    ready=false;
    if (f64Less(when,s.nextShot[who])) return;
    if (s.pendingAutoReload[who] != 0)
    {
        // Eligibility was sampled before hit callbacks. Complete at the first
        // post-delay frame even if the speed effect expired in the meantime.
        s.pendingAutoReload[who] = 0;
        s.modeCapacityEpoch[who] = 0;
        s.ammo[who] = ammoInstantCapacity(s,who,when);
        dispatch(s,0,19,who,0,when,output);
        if (s.error != 0 || changedWeaponSession(s,who,epoch,mode)) return;
        // Automatic completion bypasses partial clips and post-reload delay.
    }
    w.infinite = uint(hasInfiniteAmmo(s,who,when));
    if (w.infinite == 0 && s.ammo[who] <= 0 && (w.mode != 1 || s.charging[who] == 0))
    {
        beginReload(s,w,who,when);
        // Native checks all-ammo completion after its zero-ammo reload attempt.
        // Infinite ammo bypasses this branch and may still fire before ending.
        if (s.error == 0 && mode >= 0 && w.shotLimit == 0 && modeCapacityReference(s,uint(mode)) != 0)
        {
            uint name=definition_name(s.inputBase,uint(mode));s.frameAmmoActive[who]=0;s.physicalGaugeOwner=0;
            clearMode(s,who,when);dispatch(s,0,29,who,int(name),when,output);
        }
        return;
    }
    if (w.mode == 1)
    {
        if (s.charging[who] == 0)
        {
            WORLD_CONTROL_WAIT(s,who,w.chargeTime,when) WORLD_CHARGE_START(s,who) WORLD_CONTROL_START(s,who,w.chargeTime,when) s.charging[who] = 1; s.chargeStartedAt[who] = when;
            w.infinite = uint(hasInfiniteAmmo(s,who,when));
            if (w.infinite == 0 && s.ammo[who] == 1) dispatch(s,0,21,who,0,when,output);
            if (changedWeaponSession(s,who,epoch,mode)) return;
        }
        s.chargeUntil[who] = f64Add(s.chargeStartedAt[who],effectiveCharge(s,who,w.chargeTime,when));
        WORLD_CHARGE_HOLD(s,w,who,when) if (s.error != 0 || f64Less(when,s.chargeUntil[who])) return;
        dispatch(s,0,10,who,0,when,output);
        w.infinite = uint(hasInfiniteAmmo(s,who,when));
        if (changedWeaponSession(s,who,epoch,mode)) return;
    }
    ready=true;
}

[noinline]
void captureWeaponShot(inout Runtime s,inout Weapon w,uint who,uint64_t when,uint output,uint target,uint modeShots,int mode,uint epoch,inout uint64_t landedAmount,inout uint landedCount,inout uint landedTarget,out uint completedShots,out bool scheduleAutoReload,out uint64_t shotInterval,out bool last,out bool ready)
{
    ready=false;
#ifdef PORTABLE_CHARGE_COLLECT_REFERENCE
    scheduleAutoReload = w.mode == 1 && w.delayCover != 0 && !f64Less(readStat(s,who,S_reload_speed_pct,when),HUNDRED);
#else
    // Reload speed is an ordinary ordered scalar: no damage/quantity collector
    // is needed just to latch this boolean before hit callbacks.
    scheduleAutoReload = w.mode == 1 && w.delayCover != 0 && (s.quantityMask & 64) != 0 && !f64Less(plainQuantity(s,who,S_reload_speed_pct,when),HUNDRED);
#endif
    shotInterval = w.mode != 1 ? weaponInterval(s,w,who,when) : w.interval;
    last = w.infinite == 0 && s.ammo[who] == 1;
    if (last && w.mode != 1) dispatch(s,0,21,who,0,when,output);
    if (w.mode != 1) advanceWarmup(s,w,who,when,shotInterval);
    if (w.mode != 1 && w.infinite == 0) { if (!changedWeaponSession(s,who,epoch,mode)) s.ammo[who]--; dispatch(s,0,26,who,0,when,output); }
    WORLD_PROJECTILE_SAMPLE(s,w,who,when) WORLD_SAMPLE_SHOT_KIND(s,who,mode,w.pellets*w.muzzles) uint64_t coefficient = mode >= 0 && modeShots == 0 && !f64Less(w.firstCoefficient,0) ? w.firstCoefficient : w.coefficient;
    uint64_t amount = COUNTER_DAMAGE(s,who,w,coefficient,when,damageValue(s,who,f64Div(coefficient,f64FromI64(w.pellets)),when,WORLD_PACKET_NORMAL(s,who),w.coreBonus,WORLD_PACKET_FLAGS(s,who,(w.mode == 1 ? H_CHARGE | ((s.attackContext[who] & 4) != 0 ? H_EXPLOSION : 0) : 0)),w.fullChargeMult,w.optimal != 0,true));
    COUNTER_SHOT(s,who,w,coefficient,when) WORLD_PROJECTILE_RECORD(s,w,who,when,amount) if (s.error != 0) return;
    uint count = w.pellets*w.muzzles;
    landedAmount=amount;landedCount=count;landedTarget=target;
    completedShots = s.shots[who]+1;
    ready=true;
}

[noinline]
void landWeaponPellets(inout Runtime s,inout Weapon w,uint who,uint64_t when,uint output,uint target,uint64_t amount,uint count,uint completedShots)
{
    // Capture the packet once. Child buffs and mode switches do not resample
    // later pellets, consume extra ammunition, or redirect this physical shot.
    for (uint hit = 0; hit < count && s.error == 0; hit++)
    {
        if (s.landingPolicy==0) land(s,who,WORLD_POOL_PHYSICAL_TARGET(s,who,target),amount);
        if (w.mode != 1 || count > 1) dispatch(s,0,20,who,0,when,output); WORLD_TEAM_PELLET(s,w,who,when,output) WORLD_FRACTION_AUTO(s,w,who,when,output)
    }
    s.shots[who] = completedShots;
}

[noinline]
void finishWeaponShot(inout Runtime s,inout Weapon w,uint who,uint64_t when,uint output,uint count,uint epoch,int mode,bool scheduleAutoReload,uint64_t shotInterval,bool last)
{
    if(w.mode!=1) notifyPelletInShot(s,who,count,when,output);
    bool burstSpeed=(s.quantityMask & 128)!=0;
    if(burstSpeed && w.mode!=1 && WORLD_PACKET_NORMAL(s,who)) s.normalLandedMask|=1U<<who;
    if(!burstSpeed || w.mode!=1) WORLD_PHYSICAL_GAUGE(s) addBurstGauge(s,burstHitGain(s,who,w.gain,count,w.gaugeMultiplier,when));
    if (w.mode == 1 && w.infinite == 0) { if (!changedWeaponSession(s,who,epoch,mode)) s.ammo[who]--; dispatch(s,0,26,who,0,when,output); }
    dispatch(s,0,7,who,0,when,output);
    if (w.mode == 1) dispatch(s,0,11,who,0,when,output);
    for (uint muzzle = 0; muzzle < w.muzzles && s.error == 0; muzzle++) dispatch(s,0,8,who,0,when,output);
    if (w.mode == 1) for (uint muzzle = 0; muzzle < w.muzzles && s.error == 0; muzzle++) dispatch(s,0,12,who,0,when,output);
    if(burstSpeed && w.mode==1)
    { if(WORLD_PACKET_NORMAL(s,who)) s.normalLandedMask|=1U<<who;WORLD_PHYSICAL_GAUGE(s) addBurstGauge(s,burstHitGain(s,who,w.gain,count,w.gaugeMultiplier,when)); }
    WORLD_TEAM_CHARGE(s,w,who,count,when,output) if (s.bulletCount != 0) WORLD_NORMAL_ONLY(s,who) consumeBulletBuffs(s,who,when,output);
    WORLD_FRACTION_CHARGE(s,w,who,count,when,output) if (last) for (uint muzzle = 0; muzzle < w.muzzles && s.error == 0; muzzle++) dispatch(s,0,14,who,0,when,output);
    WORLD_CHARGE_FINISH(s,w,who) if (changedWeaponSession(s,who,epoch,mode)) return; // Preserve a callback's new session.
    if (mode >= 0)
    {
        s.modeShots[who]++;
        if (w.shotLimit >= 0 && s.modeShots[who] >= uint(w.shotLimit))
        { uint name = definition_name(s.inputBase,mode); s.frameAmmoActive[who] = 0;s.physicalGaugeOwner=0; clearMode(s,who,when); dispatch(s,0,29,who,int(name),when,output); return; }
    }
    if (w.mode == 1)
    { s.pendingAutoReload[who] = uint(scheduleAutoReload); s.charging[who] = 0; s.nextShot[who] = larger(f64Add(when,WORLD_FRACTION_POST_DELAY(s,who,mode,f64Add(w.interval,w.chargeTime ^ F64_SIGN))),f64Add(s.chargeStartedAt[who],w.minCycle)); }
    else s.nextShot[who] = larger(when,f64Add(s.nextShot[who],shotInterval));
}
