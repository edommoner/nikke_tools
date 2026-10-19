// Shared squad-frame state machine. Includes no native floating-point math.
// Automatic weapon mechanics; manual/cover policies remain separate work.
static const uint64_t BURST_EPS = uint64_t(0x3e112e0b) << 32 | 0xe826d695; // 1e-9
static const uint64_t STAGE_DELAY = uint64_t(0x3fb99999) << 32 | 0x9999999a; // .1
static const uint64_t FULL_DELAY = uint64_t(0x3fd7ae14) << 32 | 0x7ae147ae; // .37
static const uint64_t TEN = uint64_t(0x40240000) << 32;

#include "ammo_instant_runtime.slang"

void initializeCombat(inout Runtime s, uint input)
{
    s.lastB3Caster = 0xffffffff; s.lastB3Time = F64_SIGN | ONE; s.lastFullStart = F64_SIGN | ONE;
    s.gaugeCharging = 1; s.clockMode = commands[input+6];
    if (s.clockMode > 1) { s.error = 64; return; }
    s.targetCount = commands[input+4]; s.gauge = loadNumber(input+28); s.reentryDelay = loadNumber(input+30);
    if (s.combat != 1 || s.targetCount == 0 || s.targetCount > 8) { s.error = 64; return; }
    for (uint who = 0; who < 5; who++)
    {
        uint at = input+P_WEAPON_BASE+who*P_WEAPON_WORDS;
        s.modeIndex[who] = -1;
        s.fullChargeMult[who] = f64Div(loadNumber(input+P_WEAPON_EXTRA_BASE+who*4+2),HUNDRED); s.attackContext[who] = commands[input+P_ATTACK_CONTEXT_BASE+who];
        s.pellets[who] = commands[input+P_WEAPON_EXTRA_BASE+who*4]; s.muzzles[who] = commands[input+P_WEAPON_EXTRA_BASE+who*4+1];
        s.weaponEnabled[who] = commands[at]; s.weaponMode[who] = commands[at+1];
        s.capacity[who] = commands[at+2]; s.ammo[who] = s.capacity[who]; s.stage[who] = commands[at+3]; s.currentStage[who] = s.stage[who]; s.physicalModeIndex[who] = -1;
        s.coefficient[who] = loadNumber(at+4); s.interval[who] = loadNumber(at+6);
        s.reloadTime[who] = loadNumber(at+8); s.chargeTime[who] = loadNumber(at+10);
        s.gain[who] = loadNumber(at+12); s.cooldown[who] = loadNumber(at+14);
        s.reloadUntil[who] = F64_SIGN | ONE;
        uint extra = input+P_WEAPON_MECHANICS_BASE+who*P_WEAPON_MECHANICS_WORDS;
        s.rateMin[who] = loadNumber(extra); s.rateMax[who] = loadNumber(extra+2); s.warmLimit[who] = loadNumber(extra+4); s.coolTime[who] = loadNumber(extra+6);
        s.spreadStart[who] = loadNumber(extra+8); s.spreadEnd[who] = loadNumber(extra+10); s.spreadShots[who] = loadNumber(extra+12); s.coreDiameter[who] = loadNumber(extra+14);
        s.rawRate[who] = commands[extra+20]; s.clipCount[who] = commands[extra+16]; s.geometry[who] = commands[extra+17]; s.postReloadDelay[who] = loadNumber(extra+18);
        s.rawCharge[who] = loadNumber(input+P_WEAPON_QUANTITY_BASE+who*P_WEAPON_QUANTITY_WORDS);
        s.delayCover[who] = commands[input+P_WEAPON_QUANTITY_BASE+who*P_WEAPON_QUANTITY_WORDS+2];
        s.reloadCancelOnFull[who] = commands[input+P_WEAPON_QUANTITY_BASE+who*P_WEAPON_QUANTITY_WORDS+3];
        if (s.reloadCancelOnFull[who] > 1) { s.error = 64; return; }
        s.minCycle[who] = loadNumber(extra+22); s.gaugeMultiplier[who] = f64Div(loadNumber(extra+24),HUNDRED);
        uint64_t coreMult = loadNumber(extra+26);
        s.coreDamageBonus[who] = f64Less(coreMult,0) ? s.coreBonus : f64Div(f64Add(coreMult,HUNDRED ^ F64_SIGN),HUNDRED);
        s.lastFire[who] = f64FromI64(uint64_t(-999)); s.postReloadUntil[who] = F64_SIGN | ONE;

    }
    for (uint j = 0; j < s.targetCount; j++)
    {
        uint at = input+P_TARGET_BASE+j*P_TARGET_WORDS;
        s.targetGeneration[j] = commands[at+2]; s.targetAlive[j] = commands[at+3];
        s.targetHP[j] = loadNumber(at+4); s.targetMaxHP[j] = s.targetHP[j]; s.targetDefense[j] = loadNumber(at+6);
    }
}
bool reached(uint64_t time, uint64_t due) { return !f64Less(time,f64Add(due,BURST_EPS ^ F64_SIGN)); }
void teamNotify(inout Runtime s, uint event, uint64_t when, uint output)
{
    // Resource/burst notifications have body context; a previous impact cannot
    // silently redirect them to an add. Restore the enclosing context afterwards.
    uint target = s.target; s.target = 0;
    for (uint who = 0; who < 5 && s.error == 0; who++) dispatch(s,0,event,who,0,when,output);
    s.target = target;
}
struct Weapon
{
    uint mode, capacity, pellets, muzzles, infinite, sentinelMode, reloadAllowed, optimal, rawRate, ammoBuffs, delayCover;
    int shotLimit;
    uint64_t coefficient, interval, reloadTime, chargeTime, gain, coreBonus, firstCoefficient, fullChargeMult, minCycle, gaugeMultiplier, rateMin, rateMax, warmLimit, coolTime;
};
Weapon selectWeapon(inout Runtime s, uint who, uint64_t when)
{
    Weapon w = {};
    w.delayCover = s.delayCover[who]; w.ammoBuffs = 1; w.rawRate = s.rawRate[who]; w.rateMin = s.rateMin[who]; w.rateMax = s.rateMax[who]; w.warmLimit = s.warmLimit[who]; w.coolTime = s.coolTime[who];
    w.minCycle = s.minCycle[who]; w.gaugeMultiplier = s.gaugeMultiplier[who]; w.fullChargeMult = s.fullChargeMult[who]; w.optimal = s.attackContext[who] & 1;
    w.mode = s.weaponMode[who]; w.capacity = s.capacity[who]; w.pellets = s.pellets[who]; w.muzzles = s.muzzles[who];
    w.coefficient = s.coefficient[who]; w.interval = s.interval[who]; w.reloadTime = s.reloadTime[who];
    w.chargeTime = s.chargeTime[who]; w.gain = s.gain[who]; w.coreBonus = s.coreDamageBonus[who];
    w.firstCoefficient = F64_SIGN | ONE; w.shotLimit = -1; w.reloadAllowed = 1;
    int index = s.modeIndex[who];
    if (index >= 0)
    {
        uint at = s.inputBase+P_MODE_BASE+uint(index)*P_MODE_WORDS;
        w.mode = commands[at]; w.capacity = commands[at+1]; w.pellets = commands[at+2]; w.muzzles = commands[at+3];
        w.coefficient = loadNumber(at+4); w.reloadTime = loadNumber(at+8); w.chargeTime = loadNumber(at+10);
        w.interval = w.mode != 1 ? f64Div(ONE,loadNumber(at+6)) : f64Add(w.chargeTime,loadNumber(at+18));
        w.gain = loadNumber(at+12); w.coreBonus = f64Div(f64Add(loadNumber(at+14),HUNDRED ^ F64_SIGN),HUNDRED);
        w.firstCoefficient = loadNumber(at+16); w.shotLimit = int(commands[at+20]);
        w.fullChargeMult = f64Div(loadNumber(at+24),HUNDRED); w.minCycle = 0; w.gaugeMultiplier = ONE; w.optimal = commands[at+26];
        w.delayCover = commands[at+27]; w.ammoBuffs = commands[at+23]; w.sentinelMode = commands[at+21]; w.reloadAllowed = commands[at+22];
        w.rawRate = 1; uint timing = s.inputBase+P_MODE_TIMING_BASE+uint(index)*P_MODE_TIMING_WORDS;
        w.rateMin = loadNumber(timing); w.rateMax = loadNumber(timing+2); w.warmLimit = loadNumber(timing+4); w.coolTime = loadNumber(timing+6);
    }
    if (w.pellets == 0 || w.pellets > 64 || w.muzzles == 0 || w.muzzles > 8) { s.error = 64; return w; }
    if (s.appliedEpoch[who] != s.modeEpoch[who])
    {
        s.appliedEpoch[who] = s.modeEpoch[who]; s.physicalModeIndex[who] = index; s.modeShots[who] = 0; s.pendingAutoReload[who] = 0;
        // CharState resets its pre-entry capacity memo when the mode is entered.
        s.modeCapacityEpoch[who] = 0;
        w.capacity = w.sentinelMode != 0 ? 999999 : ammoInstantCapacity(s,who,when); s.modeMagazine[who] = w.capacity;
        s.ammo[who] = w.capacity; s.nextShot[who] = when; s.charging[who] = 0; s.reloadUntil[who] = F64_SIGN | ONE; s.postReloadUntil[who] = F64_SIGN | ONE;
    }
    if (index >= 0) w.capacity = s.modeMagazine[who];
    else w.capacity = fullCapacity(s,who,s.capacity[who],true,when);
    if (index >= 0 && w.sentinelMode == 0 && w.shotLimit >= 0 && uint(w.shotLimit) == commands[s.inputBase+P_MODE_BASE+uint(index)*P_MODE_WORDS+1]) w.shotLimit = int(w.capacity);
    if (s.weaponInitialized[who] == 0) { s.weaponInitialized[who] = 1; s.ammo[who] = w.capacity; }
    return w;
}
#include "weapon_runtime.slang"
void initializeMagazines(inout Runtime s, uint64_t when)
{
    for (uint who = 0; who < 5 && s.error == 0; who++)
    { s.ammo[who] = ammoInstantCapacity(s,who,when); s.weaponInitialized[who] = 1; }
}


void logBurst(inout Runtime s, uint event, uint who, uint64_t when, uint output)
{
    s.burstTraceTotal++;
    if (s.traceMode == 0) return;
    if (s.burstTraceCount == P_BURST_TRACE) { s.error = 8; return; }
    uint at = output+P_BURST_TRACE_BASE+s.burstTraceCount++*8;
    storeNumber(at,when); results[at+2] = event; results[at+3] = who+1;
}
void enterStage(inout Runtime s, uint stage, uint64_t when, uint output)
{
    for (uint who = 0; who < 5 && s.error == 0; who++) dispatch(s,0,4,who,int(stage),when,output);
}
uint effectiveStage(inout Runtime s, uint who, uint64_t when)
{
    uint stage = s.stage[who], order = 0;
    for (uint row = 0; row < s.carrierCount; row++)
        if (residentDefinition(s,row).owner == who && residentDefinition(s,row).stageOverride != 0 && s.alive[row] != 0 && f64Less(when,s.end[row]) && basicConditions(s,row,when,true) && s.entryOrder[row] >= order)
        { order = s.entryOrder[row]; stage = residentDefinition(s,row).stageOverride; }
    return stage;
}
#include "burst_duration_runtime.slang"
[noinline]
void burstFrame(inout Runtime s, uint64_t when, uint output)
{
    uint stages[5]; for (uint who = 0; who < 5; who++) { stages[who] = effectiveStage(s,who,when); s.currentStage[who] = stages[who]; }
    if (s.phase == 5 && reached(when,s.fullEnd))
    { s.phase = 0; teamNotify(s,2,when,output); s.castMask = 0; logBurst(s,5,0xffffffff,when,output); }
    if (s.phase == 0 && reached(s.gauge,HUNDRED))
    {
        s.gauge = 0; s.phase = 1; s.action = when; s.reentryDone = 0; s.reentrySlot = 0;
        logBurst(s,6,0xffffffff,when,output); enterStage(s,1,when,output);
    }
    if (s.cooldownWaitMask != 0)
    {
        uint64_t earliest = FOREVER;
        for (uint who = 0; who < 5; who++) if ((s.cooldownWaitMask & (1U << who)) != 0) earliest = smaller(earliest,s.ready[who]);
        s.action = smaller(s.action,larger(when,earliest));
    }
    if (s.phase >= 1 && s.phase <= 3 && reached(when,s.action))
    {
        uint picked = 5, candidates = 0; uint64_t earliest = FOREVER; s.cooldownWaitMask = 0;
        if (s.reentrySlot != 0) enterStage(s,s.phase,when,output);
        for (uint who = 0; who < 5; who++) if ((s.downMask & (1U << who)) == 0 && (stages[who] == s.phase || stages[who] == 4))
        {
            candidates |= 1U << who; earliest = smaller(earliest,s.ready[who]);
            if (reached(when,s.ready[who])) { picked = who; break; }
            // Default automatic B1/B2 reserves the first candidate; reentry and B3 scan alternatives.
            if (s.phase < 3 && s.reentrySlot == 0) break;
        }
        if (picked == 5) { s.action = larger(s.action,earliest); s.cooldownWaitMask = candidates; }
        if (picked < 5)
        {
            uint stage = s.phase; s.castMask |= 1U << picked; s.casts[picked]++;
            setBurstReady(s,picked,when);
            if (s.error != 0) return;
            uint target = s.target; s.target = 0;
            dispatch(s,0,3,picked,0,when,output); s.target = target;
            if (stage == 3) { s.lastB3Caster = picked; s.lastB3Time = when; }
            logBurst(s,stage+(s.reentrySlot != 0 ? 6 : 0),picked,when,output);
            bool reentry = s.pendingReentry[picked] != 0; s.pendingReentry[picked] = 0;
            for (uint row = 0; row < s.carrierCount; row++)
                if (residentDefinition(s,row).owner == picked && residentDefinition(s,row).reentry != 0 && s.alive[row] != 0 && f64Less(when,s.end[row]) && basicConditions(s,row,when,true)) reentry = true;
            if (reentry && (s.reentryDone & (1U << stage)) == 0)
            { s.reentryDone |= 1U << stage; s.reentrySlot = 1; s.action = f64Add(when,s.reentryDelay); }
            else
            {
                s.reentrySlot = 0; s.phase++;
                s.action = f64Add(when,s.phase == 4 ? FULL_DELAY : STAGE_DELAY);
                if (s.phase < 4) enterStage(s,s.phase,when,output);
            }
        }
    }
    if (s.phase == 4 && reached(when,s.action))
    { s.phase = 5; s.lastFullStart = when; s.fullEnd = f64Add(when,fullBurstLength(s,when));
      if (s.error != 0) return;
      teamNotify(s,1,when,output); reconcileBurstCooldowns(s,when); firePendingBursts(s,when,output); logBurst(s,4,0xffffffff,when,output); }
    s.gaugeCharging = uint(s.phase == 0);
}
[noinline]
bool changedWeaponSession(inout Runtime s, uint who, uint epoch, int originalMode)
{
    if (s.modeEpoch[who] == epoch) return false;
    // A temporary logical entry/cancel during a base-gun callback did not replace
    // its physical shot, so its consumption and scheduling still finish.
    return !(originalMode < 0 && s.modeIndex[who] < 0 && s.physicalModeIndex[who] < 0);
}
void weaponFrameBody(inout Runtime s, uint who, uint64_t when, uint output)
{
    if (s.weaponEnabled[who] == 0 || (s.downMask & (1U << who)) != 0) return;
    uint target = aimedTarget(s,who); if (target == 0xffffffff) return;
    s.target = target; Weapon w = selectWeapon(s,who,when);
    if (s.error != 0) return;
    if (s.modeIndex[who] < 0 && f64Less(0,s.reloadUntil[who]) && hasInfiniteAmmo(s,who,when))
    { s.reloadUntil[who] = F64_SIGN | ONE; s.nextShot[who] = larger(s.nextShot[who],when); }
    if (s.modeIndex[who] < 0 && f64Less(s.reloadUntil[who],0)) s.ammo[who] = min(s.ammo[who],int(w.capacity));
    if (!f64Less(s.reloadUntil[who],0) && (s.modeIndex[who] < 0 || w.reloadAllowed != 0))
    {
        if (f64Less(when,s.reloadUntil[who])) return;
        if (!completeReload(s,w,who,when,output)) return;
        w = selectWeapon(s,who,when); // A completion callback may change the mode.
    }
    if (s.modeIndex[who] < 0 && !f64Less(s.postReloadUntil[who],0))
    {
        if (f64Less(when,s.postReloadUntil[who])) return;
        s.postReloadUntil[who] = F64_SIGN | ONE; s.nextShot[who] = when;
    }
    s.frameAmmoActive[who] = 1;
    s.frameAmmoBase[who] = s.modeIndex[who] < 0 ? s.capacity[who] : w.sentinelMode != 0 ? 999999 : commands[s.inputBase+P_MODE_BASE+uint(s.modeIndex[who])*P_MODE_WORDS+1];
    coolWeapon(s,w,who,when);
    uint epoch = s.modeEpoch[who], modeShots = s.modeShots[who]; int mode = s.modeIndex[who];
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
    { beginReload(s,w,who,when); return; }
    if (w.mode == 1)
    {
        if (s.charging[who] == 0)
        {
            s.charging[who] = 1; s.chargeStartedAt[who] = when;
            w.infinite = uint(hasInfiniteAmmo(s,who,when));
            if (w.infinite == 0 && s.ammo[who] == 1) dispatch(s,0,21,who,0,when,output);
            if (changedWeaponSession(s,who,epoch,mode)) return;
        }
        s.chargeUntil[who] = f64Add(s.chargeStartedAt[who],effectiveCharge(s,who,w.chargeTime,when));
        if (s.error != 0 || f64Less(when,s.chargeUntil[who])) return;
        dispatch(s,0,10,who,0,when,output);
        w.infinite = uint(hasInfiniteAmmo(s,who,when));
        if (changedWeaponSession(s,who,epoch,mode)) return;
    }
#ifdef PORTABLE_CHARGE_COLLECT_REFERENCE
    bool scheduleAutoReload = w.mode == 1 && w.delayCover != 0 && !f64Less(readStat(s,who,S_reload_speed_pct,when),HUNDRED);
#else
    // Reload speed is an ordinary ordered scalar: no damage/quantity collector
    // is needed just to latch this boolean before hit callbacks.
    bool scheduleAutoReload = w.mode == 1 && w.delayCover != 0 && (s.quantityMask & 64) != 0 && !f64Less(plainQuantity(s,who,S_reload_speed_pct,when),HUNDRED);
#endif
    uint64_t shotInterval = w.mode != 1 ? weaponInterval(s,w,who,when) : w.interval;
    bool last = w.infinite == 0 && s.ammo[who] == 1;
    if (last && w.mode != 1) dispatch(s,0,21,who,0,when,output);
    if (w.mode != 1) advanceWarmup(s,w,who,when,shotInterval);
    if (w.mode != 1 && w.infinite == 0) { if (!changedWeaponSession(s,who,epoch,mode)) s.ammo[who]--; dispatch(s,0,26,who,0,when,output); }
    uint64_t coefficient = mode >= 0 && modeShots == 0 && !f64Less(w.firstCoefficient,0) ? w.firstCoefficient : w.coefficient;
    uint64_t amount = damageValue(s,who,f64Div(coefficient,f64FromI64(w.pellets)),when,true,w.coreBonus,w.mode == 1 ? H_CHARGE : 0,w.fullChargeMult,w.optimal != 0);
    if (s.error != 0) return;
    uint count = w.pellets*w.muzzles;
    uint completedShots = s.shots[who]+1;
    // Capture the packet once. Child buffs and mode switches do not resample
    // later pellets, consume extra ammunition, or redirect this physical shot.
    for (uint hit = 0; hit < count && s.error == 0; hit++)
    {
        land(s,who,target,amount);
        if (w.mode != 1 || count > 1) dispatch(s,0,20,who,0,when,output);
    }
    s.shots[who] = completedShots;
    addBurstGauge(s,f64Mul(f64Mul(w.gain,f64FromI64(count)),w.gaugeMultiplier));
    if (w.mode == 1 && w.infinite == 0) { if (!changedWeaponSession(s,who,epoch,mode)) s.ammo[who]--; dispatch(s,0,26,who,0,when,output); }
    dispatch(s,0,7,who,0,when,output);
    if (w.mode == 1) dispatch(s,0,11,who,0,when,output);
    for (uint muzzle = 0; muzzle < w.muzzles && s.error == 0; muzzle++) dispatch(s,0,8,who,0,when,output);
    if (w.mode == 1) for (uint muzzle = 0; muzzle < w.muzzles && s.error == 0; muzzle++) dispatch(s,0,12,who,0,when,output);
    if (s.bulletCount != 0) consumeBulletBuffs(s,who,when,output);
    if (last) for (uint muzzle = 0; muzzle < w.muzzles && s.error == 0; muzzle++) dispatch(s,0,14,who,0,when,output);
    if (changedWeaponSession(s,who,epoch,mode)) return; // Preserve a callback's new session.
    if (mode >= 0)
    {
        s.modeShots[who]++;
        if (w.shotLimit >= 0 && s.modeShots[who] >= uint(w.shotLimit))
        { uint name = s.defs[mode].name; s.frameAmmoActive[who] = 0; clearMode(s,who,when); dispatch(s,0,29,who,int(name),when,output); return; }
    }
    if (w.mode == 1)
    { s.pendingAutoReload[who] = uint(scheduleAutoReload); s.charging[who] = 0; s.nextShot[who] = larger(f64Add(when,f64Add(w.interval,w.chargeTime ^ F64_SIGN)),f64Add(s.chargeStartedAt[who],w.minCycle)); }
    else s.nextShot[who] = larger(when,f64Add(s.nextShot[who],shotInterval));
}
void weaponFrame(inout Runtime s, uint who, uint64_t when, uint output)
{
    s.frameAmmoActive[who] = 0;
    weaponFrameBody(s,who,when,output);
    s.frameAmmoActive[who] = 0;
}
[noinline]
void squadFrame(inout Runtime s, uint64_t when, uint output)
{
    burstFrame(s,when,output);
    for (uint who = 0; who < 5 && s.error == 0; who++) weaponFrame(s,who,when,output);
}
// Fixed clock generation belongs to the GPU, not to an authored shot schedule.
[noinline]
void advanceCombat(inout Runtime s, uint64_t through, uint output)
{
    sampleWorld(s);
    if (s.combatStarted == 0)
    { s.combatStarted = 1; teamNotify(s,0,0,output); initializeMagazines(s,0); }
    for (uint work = 0; work <= 10800 && s.error == 0; work++)
    {
        if (s.nextFrame > 10800) return;
        uint64_t when = s.clockMode != 0 ? s.frameTime : f64Div(f64FromI64(s.nextFrame),uint64_t(0x404e0000) << 32); // 60
        if (f64Less(through,when)) return;
        s.nextFrame++; s.frameCount++; beginLazyRoot(s,when); sampleWorld(s);
        tick(s,when,output);
        if (s.error == 0) squadFrame(s,when,output);
        if (s.clockMode != 0) s.frameTime = f64Add(when,uint64_t(0x3f911111) << 32 | 0x11111111);
    }
}

void writeCombatQuery(inout Runtime s, uint output, uint states)
{
    for (uint who = 0; who < 5; who++)
    {
        uint at = output+6*who; results[at] = s.ammo[who]; results[at+1] = s.shots[who];
        storeNumber(at+2,s.nextShot[who]); storeNumber(at+4,s.reloadUntil[who]);
    }
    results[output+30] = s.phase; results[output+31] = s.castMask;
    storeNumber(output+32,s.gauge); storeNumber(output+34,s.action); storeNumber(output+36,s.fullEnd);
    results[states+111] = s.lastB3Caster+1; storeNumber(states+124,s.lastB3Time); storeNumber(states+126,s.lastFullStart);
    results[output+38] = s.target; results[output+39] = s.clockMode;
    for (uint j = 0; j < s.targetCount; j++)
    {
        uint at = states+j*8; results[at] = s.targetGeneration[j]; results[at+1] = s.targetAlive[j];
        storeNumber(at+2,s.targetHP[j]); storeNumber(at+4,s.targetDamage[j]); results[at+6] = s.targetHits[j];
    }
    for (uint who = 0; who < 5; who++)
    {
        uint at = states+64+who*8; storeNumber(at,s.ready[who]); storeNumber(at+2,s.chargeUntil[who]);
        results[at+4] = s.charging[who]; results[at+5] = s.aim[who];
        results[at+6] = uint(s.modeIndex[who]+1); results[at+7] = s.modeShots[who];
    }
    for (uint who = 0; who < 5; who++) storeNumber(states+112+who*2,s.cooldownApplied[who]);
    results[states+122] = s.cooldownWaitMask; results[states+123] = s.gaugeCharging;
    results[states+104] = s.reentrySlot; results[states+105] = s.reentryDone;
    for (uint who = 0; who < 5; who++) results[states+106+who] = s.casts[who];
}
