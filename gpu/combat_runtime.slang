// Shared squad-frame state machine. Includes no native floating-point math.
// Fixed-rate, one physical hit per round; no warmup/pellet/mode/manual policy.
static const uint64_t BURST_EPS = uint64_t(0x3e112e0b) << 32 | 0xe826d695; // 1e-9
static const uint64_t STAGE_DELAY = uint64_t(0x3fb99999) << 32 | 0x9999999a; // .1
static const uint64_t FULL_DELAY = uint64_t(0x3fd7ae14) << 32 | 0x7ae147ae; // .37
static const uint64_t TEN = uint64_t(0x40240000) << 32;

void initializeCombat(inout Runtime s, uint input)
{
    s.targetCount = commands[input+4]; s.gauge = loadNumber(input+28); s.reentryDelay = loadNumber(input+30);
    if (s.combat != 1 || s.targetCount == 0 || s.targetCount > 8) { s.error = 64; return; }
    for (uint who = 0; who < 5; who++)
    {
        uint at = input+P_WEAPON_BASE+who*P_WEAPON_WORDS;
        s.modeIndex[who] = -1;
        s.pellets[who] = commands[input+P_WEAPON_EXTRA_BASE+who*4]; s.muzzles[who] = commands[input+P_WEAPON_EXTRA_BASE+who*4+1];
        s.weaponEnabled[who] = commands[at]; s.weaponMode[who] = commands[at+1];
        s.capacity[who] = commands[at+2]; s.ammo[who] = s.capacity[who]; s.stage[who] = commands[at+3];
        s.coefficient[who] = loadNumber(at+4); s.interval[who] = loadNumber(at+6);
        s.reloadTime[who] = loadNumber(at+8); s.chargeTime[who] = loadNumber(at+10);
        s.gain[who] = loadNumber(at+12); s.cooldown[who] = loadNumber(at+14);
        s.reloadUntil[who] = F64_SIGN | ONE;
    }
    for (uint j = 0; j < s.targetCount; j++)
    {
        uint at = input+P_TARGET_BASE+j*P_TARGET_WORDS;
        s.targetGeneration[j] = commands[at+2]; s.targetAlive[j] = commands[at+3];
        s.targetHP[j] = loadNumber(at+4); s.targetDefense[j] = loadNumber(at+6);
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
    uint mode, capacity, pellets, muzzles, infinite, reloadAllowed;
    int shotLimit;
    uint64_t coefficient, interval, reloadTime, chargeTime, gain, coreBonus, firstCoefficient;
};
Weapon selectWeapon(inout Runtime s, uint who, uint64_t when)
{
    Weapon w = {};
    w.mode = s.weaponMode[who]; w.capacity = s.capacity[who]; w.pellets = s.pellets[who]; w.muzzles = s.muzzles[who];
    w.coefficient = s.coefficient[who]; w.interval = s.interval[who]; w.reloadTime = s.reloadTime[who];
    w.chargeTime = s.chargeTime[who]; w.gain = s.gain[who]; w.coreBonus = s.coreBonus;
    w.firstCoefficient = F64_SIGN | ONE; w.shotLimit = -1; w.reloadAllowed = 1;
    int index = s.modeIndex[who];
    if (index >= 0)
    {
        uint at = s.inputBase+P_MODE_BASE+uint(index)*P_MODE_WORDS;
        w.mode = commands[at]; w.capacity = commands[at+1]; w.pellets = commands[at+2]; w.muzzles = commands[at+3];
        w.coefficient = loadNumber(at+4); w.reloadTime = loadNumber(at+8); w.chargeTime = loadNumber(at+10);
        w.interval = w.mode == 0 ? f64Div(ONE,loadNumber(at+6)) : f64Add(w.chargeTime,loadNumber(at+18));
        w.gain = loadNumber(at+12); w.coreBonus = f64Div(f64Add(loadNumber(at+14),HUNDRED ^ F64_SIGN),HUNDRED);
        w.firstCoefficient = loadNumber(at+16); w.shotLimit = int(commands[at+20]);
        w.infinite = commands[at+21]; w.reloadAllowed = commands[at+22];
    }
    if (w.pellets == 0 || w.pellets > 64 || w.muzzles == 0 || w.muzzles > 8) { s.error = 64; return w; }
    if (s.appliedEpoch[who] != s.modeEpoch[who])
    {
        s.appliedEpoch[who] = s.modeEpoch[who]; s.modeShots[who] = 0;
        s.ammo[who] = w.capacity; s.nextShot[who] = when; s.charging[who] = 0; s.reloadUntil[who] = F64_SIGN | ONE;
    }
    return w;
}
void logBurst(inout Runtime s, uint event, uint who, uint64_t when, uint output)
{
    if (s.burstTraceCount == 64) { s.error = 8; return; }
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
    for (uint row = 0; row < s.count; row++)
        if (s.defs[row].owner == who && s.defs[row].stageOverride != 0 && s.alive[row] != 0 && f64Less(when,s.end[row]) && s.entryOrder[row] >= order)
        { order = s.entryOrder[row]; stage = s.defs[row].stageOverride; }
    return stage;
}
void burstFrame(inout Runtime s, uint64_t when, uint output)
{
    uint stages[5]; for (uint who = 0; who < 5; who++) stages[who] = effectiveStage(s,who,when);
    if (s.phase == 5 && reached(when,s.fullEnd))
    { s.phase = 0; teamNotify(s,2,when,output); s.castMask = 0; logBurst(s,5,0xffffffff,when,output); }
    if (s.phase == 0 && reached(s.gauge,HUNDRED))
    {
        s.gauge = 0; s.phase = 1; s.action = when; s.reentryDone = 0; s.reentrySlot = 0;
        logBurst(s,6,0xffffffff,when,output); enterStage(s,1,when,output);
    }
    if (s.phase >= 1 && s.phase <= 3 && reached(when,s.action))
    {
        uint picked = 5; uint64_t earliest = FOREVER;
        if (s.reentrySlot != 0) enterStage(s,s.phase,when,output);
        for (uint who = 0; who < 5; who++) if (stages[who] == s.phase || stages[who] == 4)
        {
            earliest = smaller(earliest,s.ready[who]);
            if (reached(when,s.ready[who])) { picked = who; break; }
            if (s.phase < 3 && s.reentrySlot == 0) { s.action = s.ready[who]; break; }
        }
        if (picked == 5) s.action = larger(s.action,earliest);
        if (picked < 5)
        {
            uint stage = s.phase; s.castMask |= 1U << picked; s.casts[picked]++;
            s.ready[picked] = f64Add(when,s.cooldown[picked]);
            uint target = s.target; s.target = 0;
            dispatch(s,0,3,picked,0,when,output); s.target = target;
            logBurst(s,stage+(s.reentrySlot != 0 ? 6 : 0),picked,when,output);
            bool reentry = s.pendingReentry[picked] != 0; s.pendingReentry[picked] = 0;
            for (uint row = 0; row < s.count; row++)
                if (s.defs[row].owner == picked && s.defs[row].reentry != 0 && s.alive[row] != 0 && f64Less(when,s.end[row])) reentry = true;
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
    { s.phase = 5; s.fullEnd = f64Add(when,TEN); teamNotify(s,1,when,output); logBurst(s,4,0xffffffff,when,output); }
}
void weaponFrame(inout Runtime s, uint who, uint64_t when, uint output)
{
    if (s.weaponEnabled[who] == 0) return;
    uint target = aimedTarget(s,who); if (target == 0xffffffff) return;
    s.target = target; Weapon w = selectWeapon(s,who,when);
    if (s.error != 0) return;
    if (!f64Less(s.reloadUntil[who],0))
    {
        if (f64Less(when,s.reloadUntil[who])) return;
        s.ammo[who] = w.capacity; s.reloadUntil[who] = F64_SIGN | ONE;
        dispatch(s,0,19,who,0,when,output); s.nextShot[who] = when;
        w = selectWeapon(s,who,when); // A reload callback may select a new firing model.
    }
    uint epoch = s.modeEpoch[who], modeShots = s.modeShots[who]; int mode = s.modeIndex[who];
    if (f64Less(when,s.nextShot[who])) return;
    if (w.infinite == 0 && s.ammo[who] == 0)
    { if (w.reloadAllowed != 0) s.reloadUntil[who] = f64Add(when,w.reloadTime); return; }
    if (w.mode == 1)
    {
        if (s.charging[who] == 0)
        {
            s.charging[who] = 1; s.chargeUntil[who] = f64Add(when,w.chargeTime);
            if (w.infinite == 0 && s.ammo[who] == 1) dispatch(s,0,21,who,0,when,output);
            return;
        }
        if (f64Less(when,s.chargeUntil[who])) return;
        dispatch(s,0,10,who,0,when,output);
        if (s.modeEpoch[who] != epoch) return;
    }
    bool last = w.infinite == 0 && s.ammo[who] == 1;
    if (last && w.mode == 0) dispatch(s,0,21,who,0,when,output);
    if (w.mode == 0 && w.infinite == 0) { if (s.modeEpoch[who] == epoch) s.ammo[who]--; dispatch(s,0,26,who,0,when,output); }
    uint64_t coefficient = mode >= 0 && modeShots == 0 && !f64Less(w.firstCoefficient,0) ? w.firstCoefficient : w.coefficient;
    uint64_t amount = damageValue(s,who,f64Div(coefficient,f64FromI64(w.pellets)),when,true,w.coreBonus);
    if (s.error != 0) return;
    uint count = w.pellets*w.muzzles;
    // Capture the packet once. Child buffs and mode switches do not resample
    // later pellets, consume extra ammunition, or redirect this physical shot.
    for (uint hit = 0; hit < count && s.error == 0; hit++)
    {
        land(s,who,target,amount);
        if (w.mode == 0 || count > 1) dispatch(s,0,20,who,0,when,output);
    }
    s.shots[who]++;
    if (s.phase == 0) s.gauge = smaller(HUNDRED,f64Add(s.gauge,f64Mul(w.gain,f64FromI64(count))));
    if (w.mode == 1 && w.infinite == 0) { if (s.modeEpoch[who] == epoch) s.ammo[who]--; dispatch(s,0,26,who,0,when,output); }
    dispatch(s,0,7,who,0,when,output);
    if (w.mode == 1) dispatch(s,0,11,who,0,when,output);
    for (uint muzzle = 0; muzzle < w.muzzles && s.error == 0; muzzle++) dispatch(s,0,8,who,0,when,output);
    if (w.mode == 1) for (uint muzzle = 0; muzzle < w.muzzles && s.error == 0; muzzle++) dispatch(s,0,12,who,0,when,output);
    if (last) for (uint muzzle = 0; muzzle < w.muzzles && s.error == 0; muzzle++) dispatch(s,0,14,who,0,when,output);
    if (s.modeEpoch[who] != epoch) return; // Preserve a callback's new session.
    if (mode >= 0)
    {
        s.modeShots[who]++;
        if (w.shotLimit >= 0 && w.infinite == 0 && s.modeShots[who] >= uint(w.shotLimit))
        { uint name = s.defs[mode].name; clearMode(s,who,when); dispatch(s,0,29,who,int(name),when,output); return; }
    }
    if (w.mode == 1)
    { s.charging[who] = 0; s.nextShot[who] = f64Add(when,f64Add(w.interval,w.chargeTime ^ F64_SIGN)); }
    else s.nextShot[who] = larger(when,f64Add(s.nextShot[who],w.interval));
}
void squadFrame(inout Runtime s, uint64_t when, uint output)
{
    burstFrame(s,when,output);
    for (uint who = 0; who < 5 && s.error == 0; who++) weaponFrame(s,who,when,output);
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
    results[output+38] = s.target;
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
    results[states+104] = s.reentrySlot; results[states+105] = s.reentryDone;
    for (uint who = 0; who < 5; who++) results[states+106+who] = s.casts[who];
}
