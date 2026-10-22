// Shared squad-frame state machine. Includes no native floating-point math.
// Automatic weapon mechanics; manual/cover policies remain separate work.
static const uint64_t BURST_EPS = uint64_t(0x3e112e0b) << 32 | 0xe826d695; // 1e-9
static const uint64_t STAGE_DELAY = uint64_t(0x3fb99999) << 32 | 0x9999999a; // .1
static const uint64_t FULL_DELAY = uint64_t(0x3fd7ae14) << 32 | 0x7ae147ae; // .37
static const uint64_t TEN = uint64_t(0x40240000) << 32;

#include "ammo_instant_runtime.slang"

[noinline]
void initializeCombat(inout Runtime s, uint input)
{
#ifdef PORTABLE_ENTRY_RELOAD_DIAGNOSTIC
    for(uint j=0;j<488;j++) results[s.resourceOutput+P_MODE_ENTRY_STATE_BASE+10+j]=0;
#endif
    s.automaticAddAim = commands[input+P_AIM_POLICY_BASE];
    if (s.automaticAddAim > 31) { s.error = 64; return; }
    s.enemyEpoch = 1; for (uint target = 0; target < 8; target++) s.enemyBirth[target] = 1;
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
        if (s.attackContext[who] > 7) { s.error = 64; return; }
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
        s.lastFire[who] = f64FromI64(uint64_t(-999)); s.postReloadUntil[who] = F64_SIGN | ONE; s.modeEntryUntil[who] = F64_SIGN | ONE; s.modeEntryPhase[who] = 0;

    }
    for (uint j = 0; j < s.targetCount; j++)
    {
        uint at = input+P_TARGET_BASE+j*P_TARGET_WORDS;
        s.targetGeneration[j] = commands[at+2]; s.targetAlive[j] = commands[at+3];
        s.targetHP[j] = loadNumber(at+4); s.targetMaxHP[j] = s.targetHP[j]; s.targetDefense[j] = loadNumber(at+6);
    }
    if (!initializeEnemyAttackOrder(s)) { s.error = 64; return; }
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
[noinline]
void selectWeapon(inout Runtime s,uint who,uint64_t when,out Weapon w)
{
    w.mode=0;
    w.capacity=0;
    w.pellets=0;
    w.muzzles=0;
    w.infinite=0;
    w.sentinelMode=0;
    w.reloadAllowed=0;
    w.optimal=0;
    w.rawRate=0;
    w.ammoBuffs=0;
    w.delayCover=0;
    w.shotLimit=0;
    w.coefficient=0;
    w.interval=0;
    w.reloadTime=0;
    w.chargeTime=0;
    w.gain=0;
    w.coreBonus=0;
    w.firstCoefficient=0;
    w.fullChargeMult=0;
    w.minCycle=0;
    w.gaugeMultiplier=0;
    w.rateMin=0;
    w.rateMax=0;
    w.warmLimit=0;
    w.coolTime=0;
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
    WORLD_MODE_GAUGE(s,w,who,index) WORLD_CONTROL_GAIN(s,w,who) if (w.pellets == 0 || w.pellets > 64 || w.muzzles == 0 || w.muzzles > 8) { s.error = 64; return; }
    if (index < 0 && s.physicalModeIndex[who] == -2)
    {
        s.physicalModeIndex[who] = -1; WORLD_CONTROL_CANCEL(s,who)
        s.nextShot[who] = when;
    }
    if (s.appliedEpoch[who] != s.modeEpoch[who])
    {
        s.appliedEpoch[who] = s.modeEpoch[who]; s.physicalModeIndex[who] = index; s.modeShots[who] = 0; s.pendingAutoReload[who] = 0;
        // CharState resets its pre-entry capacity memo when the mode is entered.
        s.modeCapacityEpoch[who] = 0;
        bool hasEntry=index>=0 && commands[s.inputBase+P_MODE_BASE+uint(index)*P_MODE_WORDS+30]!=0;
        s.modeEntryUntil[who]=F64_SIGN | ONE; s.modeEntryPhase[who]=hasEntry ? 1 : 0;
        if(!hasEntry)
        {
            w.capacity = w.sentinelMode != 0 ? 999999 : ammoInstantCapacity(s,who,when); s.modeMagazine[who] = w.capacity;
            s.ammo[who] = w.capacity;
        }
        WORLD_MODE_CHARGE_CANCEL(s,who) s.nextShot[who] = when; s.charging[who] = 0; s.reloadUntil[who] = F64_SIGN | ONE; s.postReloadUntil[who] = F64_SIGN | ONE;
    }
    if (index >= 0) w.capacity = s.modeMagazine[who];
    else w.capacity = fullCapacity(s,who,s.capacity[who],true,when);
    if (s.weaponInitialized[who] == 0) { s.weaponInitialized[who] = 1; s.ammo[who] = w.capacity; }
    return;
}
#include "weapon_runtime.slang"
#include "mode_entry_runtime.slang"
#ifdef PORTABLE_WORLD_RELOAD
#include "world_reload_runtime.slang"
#endif
#ifdef PORTABLE_WORLD_OVERLAYS
#include "world_overlay_weapon.slang"
#endif
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
        logBurst(s,6,0xffffffff,when,output); WORLD_CONTROL_CYCLE(s) enterStage(s,1,when,output);
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
        for (uint who = 0; who < 5; who++) if (stages[who] == s.phase || stages[who] == 4)
        {
            candidates |= 1U << who; earliest = smaller(earliest,s.ready[who]);
            if ((s.downMask&(1U<<who))==0 && !statusStunned(s,who) && reached(when,s.ready[who])) { picked = who; break; }
            // Default automatic B1/B2 reserves the first candidate; reentry and B3 scan alternatives.
            if (s.phase < 3 && s.reentrySlot == 0) break;
        }
        if (picked == 5) { s.action = larger(s.action,earliest); s.cooldownWaitMask = candidates; }
        if (picked < 5)
        {
            uint stage = s.phase; s.castMask |= 1U << picked; s.casts[picked]++; WORLD_CONTROL_CAST(s,stage,picked)
            setBurstReady(s,picked,when);
            if (s.error != 0) return;
            uint target = s.target; s.target = 0;
            dispatch(s,0,3,picked,0,when,output);
            // Native ally-burst broadcast includes the caster in squad order.
            // No subscribers means no additional dispatch/state synchronization.
            if (nextEventCandidate(s,42,0) < s.count)
                for (uint who = 0; who < 5 && s.error == 0; who++) dispatch(s,0,42,who,0,when,output);
            s.target = target;
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
#include "pellet_shot_runtime.slang"
#include "weapon_frame_phases.slang"
[noinline]
void weaponFrameBody(inout Runtime s, uint who, uint64_t when, uint output, out uint64_t landedAmount, out uint landedCount, out uint landedTarget)
{
    landedAmount=0;landedCount=0;landedTarget=0;
    uint target;Weapon w;bool ready;
    prepareWeaponFrame(s,who,when,output,target,w,ready);if(!ready) return;
    uint epoch = s.modeEpoch[who], modeShots = s.modeShots[who]; int mode = s.modeIndex[who];
    advanceWeaponCharge(s,w,who,when,output,epoch,mode,ready);if(!ready) return;
    uint completedShots;bool scheduleAutoReload,last;uint64_t shotInterval;
    captureWeaponShot(s,w,who,when,output,target,modeShots,mode,epoch,landedAmount,landedCount,landedTarget,completedShots,scheduleAutoReload,shotInterval,last,ready);if(!ready) return;
    landWeaponPellets(s,w,who,when,output,target,landedAmount,landedCount,completedShots);
    finishWeaponShot(s,w,who,when,output,landedCount,epoch,mode,scheduleAutoReload,shotInterval,last);
}

void weaponFrame(inout Runtime s, uint who, uint64_t when, uint output)
{
    s.frameAmmoActive[who] = 0;s.physicalGaugeOwner=0;
    uint64_t landedAmount;uint landedCount,landedTarget;
    weaponFrameBody(s,who,when,output,landedAmount,landedCount,landedTarget);
    s.frameAmmoActive[who] = 0;s.physicalGaugeOwner=0;
    if (s.landingPolicy!=0 || (s.healthMask&64)!=0) for (uint hit=0;hit<landedCount && s.error==0;hit++)
    {
        COUNTER_CAPTURE(s,who,landedTarget) WORLD_PHYSICAL_BEGIN(s,who,landedTarget,landedAmount) if (s.landingPolicy!=0) land(s,who,COUNTER_TARGET(s,WORLD_POOL_PHYSICAL_TARGET(s,who,landedTarget)),landedAmount);
        COUNTER_IMPACT(s,who,landedAmount,when,output) if ((s.healthMask&64)!=0 && s.error==0) dispatch(s,17,0,who,0,when,output,landedAmount); COUNTER_PARTS(s,who,when,output) WORLD_GATE_END
    }
}
[noinline]
void squadFrame(inout Runtime s, uint64_t when, uint output)
{
    drainLandings(s,when,output);
    if (s.error!=0) return;
    burstFrame(s,when,output); WORLD_CONTROL_ARBITRATE(s,when,output)
    captureFocusAims(s,when);
    for (uint who = 0; who < 5 && s.error == 0; who++) weaponFrame(s,who,when,output);
}
// Fixed clock generation belongs to the GPU, not to an authored shot schedule.
[noinline]
void advanceCombat(inout Runtime s, uint64_t through, uint output)
{
    sampleWorld(s);
    if (s.combatStarted == 0)
    { worldFrameBegin(s,0);if(s.error!=0) return;s.combatStarted = 1; teamNotify(s,0,0,output); WORLD_INITIAL_SPAWN_START(s,0,output) initializeMagazines(s,0); }
    for (uint work = 0; work <= 10800 && s.error == 0; work++)
    {
        if (s.nextFrame > 10800) return;
        uint64_t when = s.clockMode != 0 ? s.frameTime : f64Div(f64FromI64(s.nextFrame),uint64_t(0x404e0000) << 32); // 60
        if (f64Less(through,when)) return;
        s.nextFrame++; s.frameCount++; beginLazyRoot(s,when); sampleWorld(s);
        worldFrameBegin(s,when);if(s.error!=0) return;
        tick(s,when,output);
        if(s.error==0) worldFrameDeliver(s,when,output);
        if (s.error == 0) squadFrame(s,when,output);
        if (s.clockMode != 0) s.frameTime = f64Add(when,uint64_t(0x3f911111) << 32 | 0x11111111);
    }
}

[noinline]
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
