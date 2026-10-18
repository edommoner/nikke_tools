// Shared squad-frame state machine. Includes no native floating-point math.
// Fixed-rate, one physical hit per round; no warmup/pellet/mode/manual policy.
static const uint64_t BURST_EPS = uint64_t(0x3e112e0b) << 32 | 0xe826d695; // 1e-9
static const uint64_t STAGE_DELAY = uint64_t(0x3fb99999) << 32 | 0x9999999a; // .1
static const uint64_t FULL_DELAY = uint64_t(0x3fd7ae14) << 32 | 0x7ae147ae; // .37
static const uint64_t TEN = uint64_t(0x40240000) << 32;

void initializeCombat(inout Runtime s, uint input)
{
    s.targetCount = commands[input+4]; s.gauge = loadNumber(input+28);
    if (s.combat != 1 || s.targetCount == 0 || s.targetCount > 8) { s.error = 64; return; }
    for (uint who = 0; who < 5; who++)
    {
        uint at = input+P_WEAPON_BASE+who*P_WEAPON_WORDS;
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
void burstFrame(inout Runtime s, uint64_t when, uint output)
{
    if (s.phase == 5 && reached(when,s.fullEnd))
    {
        s.phase = 0; teamNotify(s,2,when,output); s.castMask = 0;
    }
    if (s.phase == 0 && reached(s.gauge,HUNDRED))
    { s.gauge = 0; s.phase = 1; s.action = when; }
    if (s.phase >= 1 && s.phase <= 3 && reached(when,s.action))
    {
        uint picked = 5;
        for (uint who = 0; who < 5; who++) if (s.stage[who] == s.phase)
        {
            if (reached(when,s.ready[who])) { picked = who; break; }
            if (s.phase < 3) { s.action = s.ready[who]; break; }
        }
        if (picked < 5)
        {
            s.castMask |= 1U << picked; s.ready[picked] = f64Add(when,s.cooldown[picked]);
            uint target = s.target; s.target = 0;
            dispatch(s,0,3,picked,0,when,output); s.target = target;
            s.phase++; s.action = f64Add(when,s.phase == 4 ? FULL_DELAY : STAGE_DELAY);
        }
    }
    if (s.phase == 4 && reached(when,s.action))
    { s.phase = 5; s.fullEnd = f64Add(when,TEN); teamNotify(s,1,when,output); }
}
void weaponFrame(inout Runtime s, uint who, uint64_t when, uint output)
{
    if (s.weaponEnabled[who] == 0) return;
    uint target = aimedTarget(s,who);
    if (target == 0xffffffff) return; // No ammunition/charge/gauge on absent world.
    s.target = target;
    if (!f64Less(s.reloadUntil[who],0))
    {
        if (f64Less(when,s.reloadUntil[who])) return;
        s.ammo[who] = s.capacity[who]; s.reloadUntil[who] = F64_SIGN | ONE;
        uint prior = s.target; s.target = 0; dispatch(s,0,19,who,0,when,output); s.target = prior;
        s.nextShot[who] = when;
    }
    if (f64Less(when,s.nextShot[who])) return;
    if (s.ammo[who] == 0)
    { s.reloadUntil[who] = f64Add(when,s.reloadTime[who]); return; }
    if (s.weaponMode[who] == 1)
    {
        if (s.charging[who] == 0)
        {
            s.charging[who] = 1; s.chargeUntil[who] = f64Add(when,s.chargeTime[who]);
            if (s.ammo[who] == 1) dispatch(s,0,21,who,0,when,output);
            return;
        }
        if (f64Less(when,s.chargeUntil[who])) return;
        dispatch(s,0,10,who,0,when,output);
    }
    bool last = s.ammo[who] == 1;
    if (last && s.weaponMode[who] == 0) dispatch(s,0,21,who,0,when,output);
    if (s.weaponMode[who] == 0) { s.ammo[who]--; dispatch(s,0,26,who,0,when,output); }
    uint64_t amount = damageValue(s,who,s.coefficient[who],when,true);
    if (s.error != 0) return;
    // Damage is calculated before synchronous on-attack / hit callbacks.
    land(s,who,target,amount); s.shots[who]++;
    if (s.phase == 0) s.gauge = smaller(HUNDRED,f64Add(s.gauge,s.gain[who]));
    if (s.weaponMode[who] == 1) { s.ammo[who]--; dispatch(s,0,26,who,0,when,output); }
    dispatch(s,0,7,who,0,when,output);
    if (s.weaponMode[who] == 1) dispatch(s,0,11,who,0,when,output);
    dispatch(s,0,8,who,0,when,output);
    if (s.weaponMode[who] == 1) dispatch(s,0,12,who,0,when,output);
    if (last) dispatch(s,0,14,who,0,when,output);
    if (s.weaponMode[who] == 1)
    {
        s.charging[who] = 0;
        s.nextShot[who] = f64Add(when,f64Add(s.interval[who],s.chargeTime[who] ^ F64_SIGN));
    }
    else s.nextShot[who] = larger(when,f64Add(s.nextShot[who],s.interval[who]));
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
    }
}
