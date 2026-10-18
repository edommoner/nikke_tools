#include "binary64.slang"
#include "core_probability.slang"
#include "portable_schema.slang"

StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
static const uint64_t ONE = uint64_t(0x3ff00000) << 32;
static const uint64_t HUNDRED = uint64_t(0x40590000) << 32;
static const uint64_t FOREVER = uint64_t(0x46293e59) << 32 | 0x39a08cea;
static const uint64_t END_EPS = uint64_t(0x3eb0c6f7) << 32 | 0xa0b5ed8d;
static const uint64_t END_BEFORE = uint64_t(0x3f1a36e2) << 32 | 0xeb1c432d;

uint64_t loadNumber(uint at) { return uint64_t(commands[at]) | uint64_t(commands[at+1]) << 32; }
void storeNumber(uint at, uint64_t value) { results[at] = uint(value); results[at+1] = uint(value >> 32); }
uint64_t smaller(uint64_t a, uint64_t b) { return f64Less(a,b) ? a : b; }
uint64_t larger(uint64_t a, uint64_t b) { return f64Less(a,b) ? b : a; }

struct Definition
{
    uint owner, kind, stat, name, maxStack;
    int budget;
    uint64_t value, duration, interval;
    uint immediate, preserve, event, threshold, countMode;
    int eventName, targetName;
    uint recipients, target, stageArg, stageOverride, reentry, toggle, triggerCount, conditionCount, flags;
    uint64_t period;
    uint damageFlags, group, exclusive, quantityFlags, fixedLiteral, polarity;
    int alias;
    uint64_t fixedValue;
    uint bulletDuration, bulletBound;
    uint healthScaling, alliedFlags, mergeEligible, statKey, lazyGroup, queryResolve;
};
struct Frame
{
    uint mode, event, owner, cursor, target, value, repeatRow, repeatLeft, repeatPassive;
    int argument;
    uint64_t time, healthValue, healthPrevious, healthNext;
};
struct Runtime
{
    Definition defs[P_DEFINITIONS];
    uint bulletHead, bulletTail, bulletCount, bulletLinked[P_CARRIERS], bulletPrev[P_CARRIERS], bulletNext[P_CARRIERS], bulletInitialized[P_CARRIERS];
    int bulletLeft[P_CARRIERS]; uint recipientBullets[P_CARRIERS*5], recipientStacks[P_CARRIERS*5];
    uint carrierCount, carrierDefinition[P_CARRIERS], multiCarrier[P_DEFINITIONS], removalCount, removalQueue[P_CARRIERS];
    uint lazyPending[P_CARRIERS], lazyLink[P_CARRIERS], lazyPendingCount, lazyMappedPendingCount, lazyEnabled;
    uint cacheCount, cacheCursor, cacheEvaluations, cacheReuses;
    uint cacheGroup[P_LAZY_CACHE], cacheMask[P_LAZY_CACHE], cacheOrder[P_LAZY_CACHE], cacheRefs[P_LAZY_CACHE];
    uint cacheNewest[P_DEFINITIONS], cacheSeen[P_DEFINITIONS], lazyGroupDefinition[P_DEFINITIONS];
    uint64_t cacheTime[P_LAZY_CACHE], cacheNewestTime[P_DEFINITIONS], cacheRootTime, cacheFloor;
    uint queryActive, queryWho, queryAllowed[P_CARRIERS]; uint64_t queryWhen;
    uint incomingMask, downMask, activeRecipients[P_CARRIERS], receivedHits[5];
    uint64_t receivedDamage[5];
    uint hpWatchCount, hpWatchSlots[P_DEFINITIONS*P_TRIGGERS], hpDirtyMask, hpPendingMask, hpEdgeGuard;
    uint64_t hpPrevious[5], hpNext[5];
    uint healthMask; int healSource;
    uint64_t baseHP[5], hp[5], hpPct[5], baseDefense[5], hpSnapshot[P_CARRIERS], healing[5];
    uint quantityMask, weaponInitialized[5], modeMagazine[5], delayCover[5], pendingAutoReload[5];
    uint64_t rawCharge[5], activated[P_CARRIERS];
    uint rawRate[5], clipCount[5], geometry[5], probabilityValid[5], probabilityEvaluations[5];
    uint64_t chargeStartedAt[5], minCycle[5], gaugeMultiplier[5], coreDamageBonus[5];
    uint64_t warm[5], lastFire[5], lastInterval[5], postReloadUntil[5];
    uint64_t rateMin[5], rateMax[5], warmLimit[5], coolTime[5], postReloadDelay[5];
    uint64_t spreadStart[5], spreadEnd[5], spreadShots[5], coreDiameter[5], lastSpread[5], lastProbability[5], probabilityRatio[5];
    int modeIndex[5];
    uint currentStage[5], enemySnapshot, attackContext[5];
    uint64_t fullChargeMult[5];
    uint modeEpoch[5], appliedEpoch[5], modeShots[5], pendingReentry[5], reentrySlot, reentryDone, casts[5], burstTraceCount;
    uint pellets[5], muzzles[5], inputBase;
    uint64_t modeEnd[5], reentryDelay;
    uint combatStarted, combat, targetCount, target, aim[5], targetAlive[8], targetGeneration[8], targetHits[8];
    uint64_t targetHP[8], targetDamage[8], targetDefense[8];
    uint timerTarget[P_DEFINITIONS];
    uint weaponEnabled[5], weaponMode[5], capacity[5], ammo[5], shots[5], stage[5], charging[5];
    uint phase, castMask, traceMode, traceTotal, burstTraceTotal, nextFrame, frameCount;
    uint burstModifierMask, cooldownWaitMask, gaugeCharging; uint64_t cooldownApplied[5];
    uint64_t coefficient[5], interval[5], reloadTime[5], chargeTime[5], gain[5], cooldown[5];
    uint64_t nextShot[5], reloadUntil[5], ready[5], chargeUntil[5], gauge, action, fullEnd;
    uint count, error, timerClock, entryClock, traceCount, maxDepth, generation;
    uint orderedCount, orderedRows[P_CARRIERS];
    uint activations[P_DEFINITIONS], counters[P_DEFINITIONS*P_TRIGGERS], periodInitialized[P_DEFINITIONS], stacks[P_CARRIERS], alive[P_CARRIERS], entryOrder[P_CARRIERS];
    uint timerActive[P_DEFINITIONS], timerEpoch[P_DEFINITIONS], timerOrder[P_DEFINITIONS], timerGeneration[P_DEFINITIONS];
    uint64_t periodDue[P_DEFINITIONS], periodPrevious[P_DEFINITIONS];
    uint64_t due[P_DEFINITIONS], expiry[P_DEFINITIONS], end[P_CARRIERS], total[5], baseAttack[5];
    uint64_t defense, probability, coreBonus, baseCrit, baseCritDamage;
};
Definition residentDefinition(inout Runtime s, uint slot) { return s.defs[s.carrierDefinition[slot]]; }

struct Sum { uint64_t total; uint64_t correction; };
void addSum(inout Sum sum, uint64_t term)
{
    uint64_t combined = f64Add(sum.total,term);
    uint64_t correction = !f64Less(f64Abs(sum.total),f64Abs(term)) ?
        f64Add(f64Add(sum.total,combined ^ F64_SIGN),term) : f64Add(f64Add(term,combined ^ F64_SIGN),sum.total);
    sum.correction = f64Add(sum.correction,correction); sum.total = combined;
}
// Definition predicates use compiled IDs and exact binary64 operands.
// Runtime tests are deliberately distinct from activation-time gates.
bool stateMember(inout Runtime s, uint who, int name, uint flags)
{
    for (uint j = 0; j < s.carrierCount; j++)
        if (s.alive[j] != 0 && int(residentDefinition(s,j).name) == name && (s.activeRecipients[j] & (1U << who)) != 0) return true;
    if (s.combat == 0) return flags == 2;
    int mode = s.modeIndex[who];
    if (flags == 1) return mode >= 0;
    if (mode >= 0) return int(s.defs[mode].name) == name;
    return flags == 2;
}
[noinline]
bool basicConditions(inout Runtime s, uint row, uint64_t when, bool runtime, uint recipient = 0xffffffff)
{
    uint definition = s.carrierDefinition[row]; Definition d = s.defs[definition];
    if (runtime && (!f64Less(d.duration,0) || (d.flags & 2) == 0)) return true;
    for (uint i = 0; i < d.conditionCount; i++)
    {
        uint at = s.inputBase+P_CONDITION_BASE+definition*P_CONDITION_WORDS+i*4;
        uint kind = commands[at]; int name = int(commands[at+1]); uint64_t arg = loadNumber(at+2);
        if (runtime && kind != C_FULL && kind != C_NOT_FULL && kind != C_SELF_STATE && kind != C_NOT_SELF_STATE && kind != C_SELF_STACK && kind != C_CAST && kind != C_NOT_CAST && kind != C_CHARGING && kind != C_ENEMIES_ABOVE && kind != C_ENEMIES_BELOW && kind != C_HP_ABOVE && kind != C_HP_BELOW && kind != C_HP_MAX && kind != C_ALLY_HP_BELOW) continue;
        if (kind == C_FULL && s.phase != 5 || kind == C_NOT_FULL && s.phase == 5) return false;
        if (kind == C_SELF_STATE || kind == C_NOT_SELF_STATE)
        {
            uint flags = f64Equal(arg,ONE) ? 1 : f64Equal(arg,f64FromI64(2)) ? 2 : 0;
            bool present = stateMember(s,d.owner,name,flags);
            if (kind == C_SELF_STATE && !present || kind == C_NOT_SELF_STATE && present) return false;
        }
        if (kind == C_SELF_STACK)
        {
            uint count = 0;
            for (uint pass = 0; pass < s.orderedCount; pass++)
            {
                uint j = s.orderedRows[pass]; Definition carrier = residentDefinition(s,j);
                if (carrier.owner == d.owner && int(carrier.name) == name && s.alive[j] != 0 && (s.activeRecipients[j] & (1U << d.owner)) != 0) { count = s.stacks[j]; break; }
            }
            if (s.combat != 0 && s.modeIndex[d.owner] >= 0 && int(s.defs[s.modeIndex[d.owner]].name) == name) count = 1;
            if (f64Less(f64FromI64(count),arg)) return false;
        }
        if (kind == C_HP_ABOVE && f64Less(s.hpPct[d.owner],arg) || kind == C_HP_BELOW && f64Less(arg,s.hpPct[d.owner]) || kind == C_HP_MAX && f64Less(s.hpPct[d.owner],HUNDRED)) return false;
        if (kind == C_NOT_SELF_HEAL && (s.healSource < 0 || uint(s.healSource) == d.owner)) return false;
        if (kind == C_ALLY_HP_BELOW)
        {
            bool present = false;
            if (runtime && recipient < 5) present = !f64Less(arg,s.hpPct[recipient]);
            else for (uint who = 0; who < 5; who++) if (!f64Less(arg,s.hpPct[who])) present = true;
            if (!present) return false;
        }
        if (kind == C_BACK_ROW && d.owner != 1 && d.owner != 3) return false;
        if (kind == C_CAST && (s.castMask & (1U << d.owner)) == 0 || kind == C_NOT_CAST && (s.castMask & (1U << d.owner)) != 0) return false;
        if (kind == C_STATIC && f64Zero(arg) || kind == C_CHARGING && s.charging[d.owner] == 0) return false;
        if (kind == C_BURST1_ALLY || kind == C_NO_BURST1_ALLY)
        {
            bool has = false; for (uint who = 0; who < 5; who++) if (who != d.owner && s.currentStage[who] == 1) has = true;
            if (kind == C_BURST1_ALLY && !has || kind == C_NO_BURST1_ALLY && has) return false;
        }
        if (kind == C_ENEMIES_ABOVE && f64Less(f64FromI64(s.enemySnapshot),arg) || kind == C_ENEMIES_BELOW && f64Less(arg,f64FromI64(s.enemySnapshot))) return false;
        if (kind == C_TARGET_BOSS && s.target != 0 || kind == C_TARGET_ADD && s.target == 0) return false;
    }
    return true;
}

// Ordered resident slots are independent of immutable definition identities.
// New or recycled carriers enter at the end; refresh keeps insertion order.
void markEntry(inout Runtime s, uint row)
{
    uint at = 0;
    while (at < s.orderedCount && s.orderedRows[at] != row) at++;
    if (at == s.orderedCount)
    {
        if (s.orderedCount == P_CARRIERS) { s.error = 64; return; }
        s.orderedCount++;
    }
    for (uint i = at; i+1 < s.orderedCount; i++) s.orderedRows[i] = s.orderedRows[i+1];
    s.orderedRows[s.orderedCount-1] = row;
    if (s.entryClock == 0x7fffffff) { s.error = 2; return; }
    s.entryOrder[row] = ++s.entryClock;
}

#include "bullet_runtime.slang"
#include "rank_runtime.slang"
#include "lazy_runtime.slang"
#include "carrier_runtime.slang"
#include "quantity_runtime.slang"
#include "health_runtime.slang"
#include "hp_edge_runtime.slang"

// Collect in resident order once per query/hit. Four critical sums use the
// same compensated accumulation as the reference; other scalar sums are ordered.
[noinline]
void collectStats(inout Runtime s, uint who, uint64_t when, out uint64_t values[64])
{
    bool query = needsBuffResolution(s) && beginBuffQuery(s,who,when);
    for (uint k = 0; k < 64; k++) values[k] = 0;
    Sum rate = {}; rate.total = s.baseCrit; Sum skillRate = rate;
    Sum critical = {}; Sum skillCritical = {};
#ifdef PORTABLE_STAT_SCAN_REFERENCE
    // Reproducible benchmark control. Production uses the ordered branch.
    uint previous = 0;
    for (uint pass = 0; pass < s.carrierCount; pass++)
    {
        uint next = 0xffffffff, selected = s.carrierCount;
        for (uint j = 0; j < s.carrierCount; j++)
            if (s.entryOrder[j] > previous && s.entryOrder[j] < next) { next = s.entryOrder[j]; selected = j; }
        if (selected == s.carrierCount) break;
        previous = next; Definition d = residentDefinition(s,selected);
#else
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint selected = s.orderedRows[pass]; Definition d = residentDefinition(s,selected);
#endif
        if (d.alliedFlags != 0 || d.kind != 0 || d.stat >= 64 || s.alive[selected] == 0 || !f64Less(when,s.end[selected]) ||
            !queryRecipient(s,selected,who,when)) continue;
        uint64_t value = d.stat == S_atk_caster_based_pct ? scalarValue(s,selected,who) : recipientValue(s,selected,who);
        if (d.stat == S_crit_rate || d.stat == S_normal_atk_crit_rate)
        {
            value = f64Div(value,HUNDRED); addSum(rate,value);
            if (d.stat == S_crit_rate) addSum(skillRate,value);
        }
        else if (d.stat == S_crit_dmg || d.stat == S_normal_atk_crit_dmg)
        { addSum(critical,value); if (d.stat == S_crit_dmg) addSum(skillCritical,value); }
        else if (d.stat == S_atk_caster_based_pct) values[S_atk_flat] = f64Add(values[S_atk_flat],f64Mul(s.baseAttack[d.owner],f64Div(value,HUNDRED)));
        else values[d.stat] = f64Add(values[d.stat],value);
    }
    if ((s.quantityMask & 1) != 0) values[S_max_ammo_pct] = quantityTotals(s,who,S_max_ammo_pct,when,0,ONE).percent;
    if ((s.quantityMask & 2) != 0 || (s.quantityMask & 8) != 0) values[S_charge_speed_pct] = quantityTotals(s,who,S_charge_speed_pct,when,0,ONE).percent;
    if ((s.quantityMask & 4) != 0)
    {
        uint64_t conversion = chargeOverflow(s,who,when), overflow = larger(0,f64Add(values[S_charge_speed_pct],HUNDRED ^ F64_SIGN));
        if (f64Less(0,conversion) && f64Less(0,overflow)) values[S_charge_dmg_pct] = f64Add(values[S_charge_dmg_pct],f64Div(f64Mul(overflow,conversion),HUNDRED));
    }
    values[S_crit_rate] = larger(0,smaller(ONE,f64Add(rate.total,rate.correction)));
    values[S_crit_rate_skill] = larger(0,smaller(ONE,f64Add(skillRate.total,skillRate.correction)));
    values[S_crit_dmg] = f64Add(critical.total,critical.correction);
    values[S_crit_dmg_skill] = f64Add(skillCritical.total,skillCritical.correction);
    if (query) s.queryActive = 0;
}
#include "recipient_runtime.slang"

[noinline]
uint64_t readStat(inout Runtime s, uint who, uint key, uint64_t when)
{
    uint64_t values[64]; collectStats(s,who,when,values); return values[key];
}

[noinline]
bool activationConditions(inout Runtime s, uint row, uint64_t when)
{
    if (!basicConditions(s,row,when,false)) return false;
    for (uint i = 0; i < s.defs[row].conditionCount; i++)
    {
        uint at = s.inputBase+P_CONDITION_BASE+row*P_CONDITION_WORDS+i*4;
        if (commands[at] == C_STAT_ABOVE && !f64Less(loadNumber(at+2),readStat(s,s.defs[row].owner,commands[at+1],when))) return false;
    }
    return true;
}

void sampleWorld(inout Runtime s)
{
    s.enemySnapshot = s.combat == 0 ? 1 : 0;
    if (s.combat != 0) for (uint j = 0; j < s.targetCount; j++) if (s.targetAlive[j] != 0) s.enemySnapshot++;
}

bool targetLive(inout Runtime s, uint target, uint generation)
{
    return s.combat == 0 || (target < s.targetCount && s.targetAlive[target] != 0 && s.targetGeneration[target] == generation);
}
uint aimedTarget(inout Runtime s, uint who)
{
    uint t = s.aim[who];
    if (s.targetAlive[t] != 0) return t;
    for (uint j = 0; j < s.targetCount; j++) if (s.targetAlive[j] != 0) return j;
    return 0xffffffff;
}
void land(inout Runtime s, uint who, uint target, uint64_t amount)
{
    if (s.combat != 0 && s.targetHits[target] == 0x7fffffff) { s.error = 2; return; }
    s.total[who] = f64Add(s.total[who],amount);
    if (s.combat == 0) return;
    s.targetDamage[target] = f64Add(s.targetDamage[target],amount);
    s.targetHP[target] = larger(0,f64Add(s.targetHP[target],amount ^ F64_SIGN));
    s.targetHits[target]++;
    if (f64Zero(s.targetHP[target])) s.targetAlive[target] = 0;
}

// End the old session before callbacks. A child may install a new session.
void clearMode(inout Runtime s, uint who, uint64_t when)
{
    s.pendingAutoReload[who] = 0; s.modeIndex[who] = -1; s.modeEpoch[who]++; s.appliedEpoch[who] = s.modeEpoch[who];
    s.ammo[who] = fullCapacity(s,who,s.capacity[who],true,when); s.weaponInitialized[who] = 1; s.reloadUntil[who] = F64_SIGN | ONE;
    s.charging[who] = 0; s.nextShot[who] = when; s.modeShots[who] = 0; s.postReloadUntil[who] = F64_SIGN | ONE;
}

void pushFrame(inout Runtime s, inout Frame frames[32], inout int depth, uint mode, uint event, uint owner, int argument, uint64_t when, uint value = 0)
{
    if (depth == 31) { s.error = 1; return; }
    depth++;
    Frame f = {};
    if (mode == 9) { f.value = uint(argument); f.repeatLeft = s.removalCount-uint(argument); }
    f.mode = mode; f.event = event; f.owner = owner; f.argument = argument; f.time = when; f.value = mode == 9 ? uint(argument) : value;
    uint inherited = event < 32 ? P_TARGET_INHERIT_0 : P_TARGET_INHERIT_1;
    f.target = s.combat == 0 || mode != 0 || (event < 64 && (inherited & (1U << (event%32))) != 0) ? s.target : 0;
    frames[depth] = f; s.maxDepth = max(s.maxDepth,uint(depth+1));
}

void registerTimer(inout Runtime s, uint row, uint64_t when)
{
    Definition d = s.defs[row]; bool was = s.timerActive[row] != 0;
    uint target = d.target != 0 ? 0 : s.target;
    bool sameTarget = s.combat == 0 || (s.timerTarget[row] == target && s.timerGeneration[row] == s.targetGeneration[target]);
    bool preserve = d.kind == 3 && d.preserve != 0 && was && sameTarget;
    if (!preserve)
    {
        if (s.timerEpoch[row] == 0x7fffffff) { s.error = 2; return; }
        s.timerEpoch[row]++;
        s.due[row] = f64Add(when,d.kind == 3 && d.immediate != 0 ? 0 : d.interval);
        s.timerTarget[row] = d.target != 0 ? 0 : s.target;
        s.timerGeneration[row] = s.combat != 0 ? s.targetGeneration[s.timerTarget[row]] : s.generation;
    }
    if (!was)
    {
        if (s.timerClock == 0x7fffffff) { s.error = 2; return; }
        s.timerOrder[row] = ++s.timerClock;
    }
    s.timerActive[row] = 1;
    s.expiry[row] = f64Less(d.duration,0) ? FOREVER : f64Add(when,d.duration);
    if (d.kind == 3)
    {
        if (s.alive[row] == 0) markEntry(s,row);
        s.activated[row] = when;
        s.stacks[row] = min(s.stacks[row]+1,d.maxStack);
        s.end[row] = s.expiry[row]; s.alive[row] = 1;
    }
}

#include "damage_runtime.slang"
#include "incoming_runtime.slang"
#include "burst_runtime.slang"

[noinline]
void dispatch(inout Runtime s, uint mode, uint event, uint owner, int argument, uint64_t when, uint output)
{
    if (owner >= 5) { s.error = 64; return; }
    syncHealth(s,when);
    uint entryTarget = s.target;
    Frame frames[32]; int depth = -1;
    pushFrame(s,frames,depth,mode,event,owner,argument,when);
    uint work = 0;
    while (depth >= 0 && s.error == 0)
    {
        if (++work > 4096) { s.error = 4; break; }
        if (s.hpPendingMask != 0 && s.hpEdgeGuard == 0)
        {
            uint who = 0; while ((s.hpPendingMask & (1U << who)) == 0) who++;
            s.hpPendingMask &= ~(1U << who);
            uint64_t previous = s.hpPrevious[who], next = s.hpNext[who];
            pushFrame(s,frames,depth,4,f64Less(next,previous) ? 0 : 2,who,0,frames[depth].time);
            if (s.error != 0) break;
            frames[depth].healthPrevious = previous; frames[depth].healthNext = next; s.hpEdgeGuard = 1; continue;
        }
        if (s.hpDirtyMask != 0)
        {
            uint who = 0; while ((s.hpDirtyMask & (1U << who)) == 0) who++;
            s.hpDirtyMask &= ~(1U << who); syncHealthActor(s,who,frames[depth].time); continue;
        }
        Frame f = frames[depth]; s.target = f.target; s.healSource = f.event == 16 ? f.argument : -1; uint row = s.count, passive = 0;
        if (f.cursor == 0 && (f.mode == 0 || f.mode == 1 || f.mode == 2) &&
            (s.downMask & (1U << f.owner)) != 0 && f.event != 26 && f.event != 28 && f.event != 38)
        { depth--; continue; }
        if (f.mode == 9)
        {
            if (f.cursor == f.repeatLeft) { s.removalCount = f.value; depth--; continue; }
            uint payload = s.removalQueue[f.value+f.cursor]; frames[depth].cursor++;
            pushFrame(s,frames,depth,0,29,payload & 7,int(payload >> 3),f.time); continue;
        }
        if (f.mode == 8)
        {
            uint at = s.inputBase+P_COMMAND_BASE+uint(f.argument)*8;
            if (f.event == 0)
            {
                uint who = frames[depth].cursor, mask = commands[at+5] & ~s.downMask;
                while (who < 5 && (mask & (1U << who)) == 0) who++;
                if (who == 5) { depth--; continue; }
                frames[depth].cursor = who+1; frames[depth].owner = who;
                uint input = s.inputBase+P_INCOMING_BASE+uint(f.argument)*P_INCOMING_WORDS;
                frames[depth].healthValue = incomingBodyDamage(s,who,loadNumber(input),loadNumber(input+2),f.time);
                frames[depth].event = 1; continue;
            }
            if (f.event == 1)
            {
                uint64_t amount = liveMarker(s,f.owner,S_invincible,f.time) ? 0 : f.healthValue;
                if (!f64Zero(amount) && !f64Less(amount,s.hp[f.owner]) && liveMarker(s,f.owner,S_undying,f.time)) amount = larger(0,f64Add(s.hp[f.owner],ONE ^ F64_SIGN));
                frames[depth].healthValue = amount; frames[depth].event = 2;
                if (!f64Zero(amount) && !f64Less(amount,s.hp[f.owner])) pushFrame(s,frames,depth,0,37,f.owner,0,f.time);
                continue;
            }
            if (f.event == 2)
            {
                uint64_t amount = f.healthValue;
                if (!f64Zero(amount) && !f64Less(amount,s.hp[f.owner]) && liveMarker(s,f.owner,S_undying,f.time)) amount = larger(0,f64Add(s.hp[f.owner],ONE ^ F64_SIGN));
                bool fell = !f64Zero(amount) && !f64Less(amount,s.hp[f.owner]);
                s.receivedDamage[f.owner] = f64Add(s.receivedDamage[f.owner],amount);
                if (!f64Finite(s.receivedDamage[f.owner])) { s.error = 16; break; }
                if (s.receivedHits[f.owner] == 0x7fffffff) { s.error = 2; break; }
                s.receivedHits[f.owner]++;
                s.hp[f.owner] = larger(0,f64Add(s.hp[f.owner],amount ^ F64_SIGN));
                if (!fell) syncHealthActor(s,f.owner,f.time);
                frames[depth].value = uint(fell); frames[depth].event = 3;
                pushFrame(s,frames,depth,0,32,f.owner,0,f.time); continue;
            }
            frames[depth].event = 0;
            if (f.value != 0 && (s.downMask & (1U << f.owner)) == 0)
            {
                knockDown(s,f.owner,f.time);
                for (int observer = 4; observer >= 0; observer--) if ((s.downMask & (1U << observer)) == 0) pushFrame(s,frames,depth,0,46,uint(observer),0,f.time);
                pushFrame(s,frames,depth,0,38,f.owner,0,f.time);
            }
            continue;
        }
        if (f.mode == 7) { depth--; continue; }
        if (f.mode == 4)
        {
            bool delivered = false;
            while (frames[depth].cursor < s.hpWatchCount)
            {
                uint watch = frames[depth].cursor++, at = hpWatchAddress(s,watch);
                uint observer = s.defs[s.hpWatchSlots[watch]/8].owner;
#ifdef PORTABLE_HP_WATCH_SCAN_REFERENCE
                bool seen = false;
                for (uint i = 0; i < watch; i++)
                {
                    uint prior = hpWatchAddress(s,i);
                    if (s.defs[s.hpWatchSlots[i]/8].owner == observer && commands[prior] == commands[at] && commands[prior+4] == commands[at+4]) seen = true;
                }
                if (seen) continue;
#endif
                if (!hpEdgeMatches(f.owner,observer,int(commands[at+7]),f.event,f.healthPrevious,f.healthNext,loadNumber(at+5))) continue;
                pushFrame(s,frames,depth,0,commands[at],observer,int(commands[at+4]),f.time); delivered = true; break;
            }
            if (delivered) continue;
            if (f.event == 0) { frames[depth].event = 1; frames[depth].cursor = 0; continue; }
            s.hpEdgeGuard = 0; depth--; continue;
        }
        if (f.mode == 5 || f.mode == 6)
        {
            Definition health = residentDefinition(s,uint(f.argument));
            uint index = frames[depth].cursor;
            uint encoded = index < 5 ? (f.value >> (3*index)) & 7 : 0;
            if (encoded == 0) { depth--; continue; }
            frames[depth].cursor = index+1; uint who = encoded-1;
            if ((s.downMask & (1U << who)) != 0) continue;
            if (f.mode == 5) s.hp[who] = smaller(f64Add(s.hp[who],f.healthValue),effectiveMaxHP(s,who,f.time));
            else s.hp[who] = larger(0,f64Mul(s.hp[who],f64Add(ONE,f64Div(health.value,HUNDRED) ^ F64_SIGN)));
            syncHealthActor(s,who,f.time); continue;
        }
        if (f.mode == 3)
        {
            depth--; if ((s.downMask & (1U << f.owner)) != 0) continue;
            Definition heal = s.defs[uint(f.argument)];
            uint64_t base = heal.healthScaling != 0 ? effectiveMaxHP(s,heal.owner,f.time) : s.baseHP[f.owner];
            uint64_t amount = f64Mul(f64Div(f64Mul(base,heal.value),HUNDRED),healMultiplier(s,f.owner,heal.owner,f.time));
            if (!f64Finite(amount)) { s.error = 16; break; }
            uint64_t before = s.hp[f.owner];
            s.hp[f.owner] = smaller(f64Add(before,amount),effectiveMaxHP(s,f.owner,f.time));
            s.healing[f.owner] = f64Add(s.healing[f.owner],larger(0,f64Add(s.hp[f.owner],before ^ F64_SIGN)));
            syncHealthActor(s,f.owner,f.time);
            pushFrame(s,frames,depth,0,16,f.owner,int(heal.owner),f.time); continue;
        }
        if (f.mode == 1)
        {
            if (f.cursor == 0 && f.argument >= 0 && uint(f.argument) < s.count) row = uint(f.argument);
            frames[depth].cursor++;
        }
        else if (f.repeatLeft != 0)
        { row = f.repeatRow; passive = f.repeatPassive; frames[depth].repeatLeft--; }
        else
        {
            while (frames[depth].cursor < s.count)
            {
                uint j = frames[depth].cursor++; Definition d = s.defs[j];
                if (f.mode == 2)
                {
                    if ((commands[s.inputBase+P_FORCE_BASE+uint(f.argument)*P_MASK_WORDS+j/32] & (1U << (j%32))) != 0) { row = j; break; }
                    continue;
                }
                if (f.event != 26 && d.owner != f.owner) continue;
                uint multiplicity = 0; bool matched = false;
                for (uint slot = 0; slot < d.triggerCount; slot++)
                {
                    uint at = s.inputBase+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8;
                    uint event = commands[at], mode = commands[at+3]; int tag = int(commands[at+4]), stage = int(commands[at+7]);
                    if (event != f.event) continue;
                    if (event == 4 && stage != f.argument || event == 6 && int(j) != f.argument) continue;
                    if ((event == 9 || event == 29 || event == 31 || event == 48 || event == 49) && tag != f.argument) continue;
                    if (event == 9 && commands[at+5] != f.value) continue;
                    multiplicity++; bool ok = true;
                    if (mode != 0 || event == 7 || event == 8)
                    {
                        uint counter = j*8+slot, status;
                        uint64_t threshold64 = f64ToI64(loadNumber(at+1),1,status);
                        if (status != 0 || threshold64 == 0 || threshold64 > 0x7fffffff || s.counters[counter] == 0x7fffffff) { s.error = 2; break; }
                        uint count = ++s.counters[counter], threshold = uint(threshold64);
                        ok = mode == 2 ? count >= threshold : mode == 3 ? count == threshold : count % threshold == 0;
                    }
                    if (stage == 2 && event != 4) ok = false;
                    if (ok && !matched) { matched = true; passive = commands[at+6]; }
                }
                if (!matched) continue;
                row = j;
                if (f.event != 6 && multiplicity > 1)
                { frames[depth].repeatRow = j; frames[depth].repeatLeft = multiplicity-1; frames[depth].repeatPassive = passive; }
                break;
            }
        }
        if (row == s.count) { depth--; continue; }
        Definition d = s.defs[row];
        if (f.mode == 2)
        { pushFrame(s,frames,depth,1,47,d.owner,int(row),f.time); continue; }
        if (f.mode == 0 && !activationConditions(s,row,f.time) && !(f.event == 0 && f64Less(d.duration,0) && passive != 0)) continue;
        uint recipientOrder = 0, recipientMask = d.recipients;
        if (d.kind == 0 || d.kind == 4 || d.kind == 5 || d.kind == 6 || d.kind == 8 || d.kind == 24)
        {
            if (d.lazyGroup == 0) recipientMask = selectRecipients(s,row,f.time,recipientOrder);
            else recipientMask = 0;
            uint selector = commands[s.inputBase+P_RECIPIENT_BASE+row*8];
            bool lazy = selector == 5 || selector == 6 || selector == 7 || selector == 15 || selector == 16;
            if (d.budget >= 0 && recipientMask == 0 && !lazy) continue;
        }
        if (f.event != 28 || (d.flags & 1) != 0)
        {
            if (d.budget >= 0 && s.activations[row] >= uint(d.budget)) continue;
            if (s.activations[row] == 0x7fffffff) { s.error = 2; break; }
            s.activations[row]++;
        }
        if (!f64Zero(d.interval) && f.event != 28) { registerTimer(s,row,f.time); continue; }
        if (d.kind == 0 || d.kind == 4)
        {
            uint64_t duration = d.duration; bool activationLazy = d.lazyGroup != 0;
            row = findCarrier(s,row,recipientMask,f.time);
            if (s.error != 0) break;
            d = residentDefinition(s,row);
            bool live = s.alive[row] != 0 && f64Less(f.time,s.end[row]);
            if (!live) { resetBulletCarrier(s,row); discardLazy(s,row); s.stacks[row] = 0; s.hpSnapshot[row] = 0; markEntry(s,row); }
            uint previousStack = s.stacks[row];
            if (activationLazy)
            {
                if (!live) { s.lazyPending[row] = 1; s.lazyPendingCount++; s.lazyMappedPendingCount += d.queryResolve; s.activeRecipients[row] = 0; }
                else if (s.lazyPending[row] != 0) unlinkLazyCache(s,row);
            }
            else s.activeRecipients[row] = recipientMask;
            s.stacks[row] = min(s.stacks[row]+1,d.maxStack); s.alive[row] = 1; s.activated[row] = f.time;
            s.end[row] = f64Less(duration,0) ? FOREVER : f64Add(f.time,duration);
            if (d.bulletDuration != 0) prepareBulletActivation(s,row,recipientMask,live,activationLazy,previousStack);
            if (activationLazy)
            {
                if (previousStack != s.stacks[row]) pushFrame(s,frames,depth,0,9,d.owner,int(d.name),f.time,s.stacks[row]);
            }
            else if (s.hpWatchCount != 0 && (d.stat >= S_max_hp_pct && d.stat <= S_max_hp_only_pct || d.stat == S_max_hp_from_max_hp_pct))
            {
                uint64_t grant = prepareHealthGrant(s,row,f.time);
                if (previousStack != s.stacks[row]) pushFrame(s,frames,depth,0,9,d.owner,int(d.name),f.time,s.stacks[row]);
                pushFrame(s,frames,depth,5,0,d.owner,int(row),f.time);
                if (s.error == 0) { frames[depth].healthValue = grant; frames[depth].value = recipientOrder; }
            }
            else
            {
                applyHealthBuff(s,row,f.time);
                if (previousStack != s.stacks[row]) pushFrame(s,frames,depth,0,9,d.owner,int(d.name),f.time,s.stacks[row]);
            }
        }
        else if (d.kind == 6)
        {
            // Stack recipient deliveries in reverse so each child completes
            // synchronously before the next squad member's heal is evaluated.
            for (int index = 4; index >= 0; index--)
            {
                uint encoded = (recipientOrder >> (3*uint(index))) & 7;
                if (encoded != 0) pushFrame(s,frames,depth,3,0,encoded-1,int(row),f.time);
            }
        }
        else if (d.kind == 8)
        {
            if (s.hpWatchCount != 0)
            { pushFrame(s,frames,depth,6,0,d.owner,int(row),f.time); if (s.error == 0) frames[depth].value = recipientOrder; }
            else
            {
                for (uint who = 0; who < 5; who++) if ((recipientMask & (1U << who)) != 0)
                    s.hp[who] = larger(0,f64Mul(s.hp[who],f64Add(ONE,f64Div(d.value,HUNDRED) ^ F64_SIGN)));
                syncHealth(s,f.time);
            }
        }
        else if (d.kind == 5) reduceBurstReady(s,recipientMask,d.value,f.time);
        else if (d.kind == 24) { if (recipientMask != 0) addBurstGauge(s,d.value); }
        else if (d.kind == 25) s.pendingReentry[d.owner] = 1;
        else if (d.kind == 2)
        {
            int prior = s.modeIndex[d.owner];
            if (d.toggle != 0 && prior >= 0 && s.defs[prior].name == d.name)
            { clearMode(s,d.owner,f.time); pushFrame(s,frames,depth,0,29,d.owner,int(d.name),f.time); }
            else
            {
                if (prior != int(row)) { s.modeEpoch[d.owner]++; s.modeShots[d.owner] = 0; }
                s.modeIndex[d.owner] = int(row);
                s.modeEnd[d.owner] = f64Less(d.duration,0) ? FOREVER : f64Add(f.time,d.duration);
            }
        }
        else if (d.kind == 1)
        {
            int mode = s.modeIndex[d.owner];
            if (s.combat != 0 && mode >= 0 && s.defs[mode].name == uint(d.targetName))
            { uint name = s.defs[mode].name; clearMode(s,d.owner,f.time); pushFrame(s,frames,depth,0,29,d.owner,int(name),f.time); }
            uint begin = s.removalCount;
            for (uint pass = 0; pass < s.orderedCount && s.error == 0; pass++)
            {
                uint slot = s.orderedRows[pass];
                if (s.alive[slot] != 0 && residentDefinition(s,slot).name == uint(d.targetName)) queueCarrierEnd(s,slot);
            }
            for (uint j = 0; j < s.count; j++) if (s.defs[j].name == uint(d.targetName)) s.timerActive[j] = 0;
            if (s.removalCount > begin) pushFrame(s,frames,depth,9,0,0,int(begin),f.time);
        }
        else if (d.kind == 33) pushFrame(s,frames,depth,2,0,d.owner,int(row),f.time);
        else if (d.kind == 3)
        {
            uint target = d.target != 0 ? 0 : f.target;
            uint generation = s.combat != 0 ? s.targetGeneration[target] : s.generation;
            if (!targetLive(s,target,generation)) continue;
            s.target = target;
            if (f.event != 28) s.stacks[row] = 1;
            uint64_t amount = damageValue(s,d.owner,f64Mul(d.value,f64FromI64(s.stacks[row])),f.time,false,s.coreBonus,d.damageFlags);
            if (s.error != 0) break;
            land(s,d.owner,target,amount);
            if (s.traceTotal == 0x7fffffff) { s.error = 2; break; }
            s.traceTotal++;
            if (s.traceMode == 0) { pushFrame(s,frames,depth,0,49,d.owner,int(d.name),f.time); continue; }
            if (s.traceCount == P_TRACE) { s.error = 8; break; }
            uint at = output + P_TRACE_BASE + s.traceCount++*P_TRACE_WORDS;
            results[at] = row; storeNumber(at+1,f.time); results[at+3] = s.timerEpoch[row];
            results[at+4] = generation; results[at+5] = uint(depth+1); storeNumber(at+6,s.due[row]);
            pushFrame(s,frames,depth,0,49,d.owner,int(d.name),f.time);
        }
        else s.error = 32;
#ifdef PORTABLE_HEALTH_SCAN_REFERENCE
        syncHealth(s,f.time);
#else
        if (d.kind == 1) syncHealth(s,f.time);
#endif
    }
    s.target = entryTarget;
}

void timerPass(inout Runtime s, uint64_t when, bool damagePass, uint output)
{
    uint rows[P_DEFINITIONS], epochs[P_DEFINITIONS], count = 0;
    // Snapshot registration order AND epoch before any child is run.
    for (uint j = 0; j < s.count; j++) if (s.timerActive[j] != 0 && (s.defs[j].kind == 3) == damagePass)
    {
        uint at = count++;
        while (at > 0 && s.timerOrder[j] < s.timerOrder[rows[at-1]])
        { rows[at] = rows[at-1]; epochs[at] = epochs[at-1]; at--; }
        rows[at] = j; epochs[at] = s.timerEpoch[j];
    }
    for (uint pass = 0; pass < count && s.error == 0; pass++)
    {
        uint j = rows[pass]; Definition d = s.defs[j];
        if (s.timerActive[j] == 0 || s.timerEpoch[j] != epochs[pass]) continue;
        if (damagePass && !targetLive(s,s.timerTarget[j],s.timerGeneration[j])) { s.timerActive[j] = 0; continue; }
        uint64_t limit = f64Add(s.expiry[j], d.immediate != 0 ? END_EPS ^ F64_SIGN : END_EPS);
        bool expired = damagePass ? f64Less(limit,s.due[j]) : !f64Less(when,s.expiry[j]);
        if (expired) { s.timerActive[j] = 0; continue; }
        if (f64Less(when,s.due[j])) continue;
        uint64_t observed = damagePass && !f64Less(when,s.expiry[j]) ? f64Add(s.expiry[j],END_BEFORE ^ F64_SIGN) : when;
        s.due[j] = f64Add(s.due[j],d.interval); // Commit before nested callbacks.
        uint parentTarget = s.target; s.target = s.timerTarget[j];
        if (damagePass || d.immediate != 2 || basicConditions(s,j,observed,true)) dispatch(s,1,28,d.owner,int(j),observed,output); s.target = parentTarget;
    }
}
[noinline]
void tick(inout Runtime s, uint64_t when, uint output)
{
    if (s.hpWatchCount != 0) dispatch(s,7,0,0,0,when,output);
    timerPass(s,when,true,output);
    uint begin = s.removalCount;
    for (uint pass = 0; pass < s.orderedCount && s.error == 0; pass++)
    {
        uint slot = s.orderedRows[pass];
        if (s.alive[slot] != 0 && !f64Less(when,s.end[slot])) queueCarrierEnd(s,slot);
    }
    if (s.removalCount > begin) { syncHealth(s,when); dispatch(s,9,0,0,int(begin),when,output); }
    if (s.combat != 0) for (uint who = 0; who < 5 && s.error == 0; who++)
        if (s.modeIndex[who] >= 0 && !f64Less(when,s.modeEnd[who]))
        { uint name = s.defs[s.modeIndex[who]].name; clearMode(s,who,when); dispatch(s,0,29,who,int(name),when,output); }
    for (uint j = 0; j < s.count && s.error == 0; j++)
        if ((s.downMask & (1U << s.defs[j].owner)) == 0 && (s.defs[j].flags & 1) != 0 && activationConditions(s,j,when))
        {
            uint resident = s.carrierCount;
            for (uint pass = 0; pass < s.orderedCount; pass++)
            { uint slot = s.orderedRows[pass]; if (s.carrierDefinition[slot] == j && s.alive[slot] != 0) { resident = slot; break; } }
            if (resident == s.carrierCount) dispatch(s,1,28,s.defs[j].owner,int(j),when,output);
            else s.end[resident] = larger(s.end[resident],f64Add(when,s.defs[j].duration));
        }
    for (uint j = 0; j < s.count && s.error == 0; j++)
        if (!f64Zero(s.defs[j].period)) for (uint slot = 0; slot < s.defs[j].triggerCount && s.error == 0; slot++)
        {
            uint at = s.inputBase+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8;
            if (commands[at] != 6) continue;
            uint64_t interval = loadNumber(at+1), next = s.periodInitialized[j] != 0 ? s.periodDue[j] : interval;
            if (s.periodInitialized[j] != 0 && !f64Equal(interval,s.periodPrevious[j]))
                next = f64Add(when,f64Mul(larger(0,f64Add(next,when ^ F64_SIGN)),f64Div(interval,s.periodPrevious[j])));
            s.periodInitialized[j] = 1; s.periodDue[j] = next; s.periodPrevious[j] = interval;
            if (!f64Less(when,next))
            { dispatch(s,0,6,s.defs[j].owner,int(j),when,output); s.periodDue[j] = f64Add(next,interval); }
        }
    timerPass(s,when,false,output); syncHealth(s,when);
    if (s.hpWatchCount != 0) dispatch(s,7,0,0,0,when,output);
}

#include "bullet_consume.slang"
#include "combat_runtime.slang"

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if (id.x >= commands[0]) return;
    uint input = 1 + id.x*P_INPUT_WORDS, output = id.x*P_OUTPUT_WORDS;
    Runtime s = {}; s.generation = 1; s.count = commands[input+1]; s.combat = commands[input+3]; s.inputBase = input; s.traceMode = commands[input+5];
    if (commands[input] != PORTABLE_ABI || s.count == 0 || s.count > P_DEFINITIONS || commands[input+2] > P_COMMANDS || s.traceMode > 1)
    { results[output] = 64; return; }
    s.carrierCount = s.count;
    for (uint row = 0; row < s.count; row++) s.carrierDefinition[row] = row;
    for (uint i = 0; i < 5; i++)
    {
        s.baseAttack[i] = loadNumber(input+8+2*i);
        uint health = input+P_HEALTH_BASE+i*P_HEALTH_WORDS;
        s.baseHP[i] = loadNumber(health); s.hp[i] = loadNumber(health+2); s.baseDefense[i] = loadNumber(health+4);
        s.hpPct[i] = f64Mul(f64Div(s.hp[i],s.baseHP[i]),HUNDRED);
    }
    s.defense = loadNumber(input+18); s.coreBonus = loadNumber(input+22);
    s.baseCrit = loadNumber(input+24); s.baseCritDamage = loadNumber(input+26);
    if (s.combat != 0) initializeCombat(s,input);
    if (s.error != 0) { results[output] = s.error; return; }
    uint numericStatus; s.probability = coreProbability(loadNumber(input+20),numericStatus);
    if (numericStatus != 0) { results[output] = 128; return; }
    for (uint j = 0; j < s.count; j++)
    {
        uint at = input+P_DEFINITION_BASE+j*P_DEFINITION_WORDS; Definition d;
        d.owner = commands[at+D_OWNER]; d.kind = commands[at+D_KIND]; d.stat = commands[at+D_STAT];
        d.name = commands[at+D_NAME]; d.maxStack = commands[at+D_MAX_STACK]; d.budget = int(commands[at+D_BUDGET]);
        d.value = loadNumber(at+D_VALUE); d.duration = loadNumber(at+D_DURATION); d.interval = loadNumber(at+D_INTERVAL);
        d.immediate = commands[at+D_IMMEDIATE]; d.preserve = commands[at+D_PRESERVE];
        d.event = commands[at+D_EVENT]; d.threshold = commands[at+D_THRESHOLD]; d.countMode = commands[at+D_COUNT_MODE];
        d.eventName = int(commands[at+D_EVENT_NAME]); d.targetName = int(commands[at+D_TARGET_NAME]);
        d.stageArg = commands[at+D_STAGE_ARG]; d.stageOverride = commands[at+D_STAGE_OVERRIDE];
        d.reentry = commands[at+D_REENTRY]; d.toggle = commands[at+D_TOGGLE];
        d.triggerCount = commands[at+D_TRIGGER_COUNT]; d.conditionCount = commands[at+D_CONDITION_COUNT];
        d.flags = commands[at+D_FLAGS]; d.period = loadNumber(at+D_PERIOD); d.damageFlags = commands[at+D_DAMAGE_FLAGS];
        d.target = commands[at+D_TARGET]; d.recipients = commands[at+D_RECIPIENTS];
        d.mergeEligible = commands[input+P_RECIPIENT_BASE+j*8+7] & 3;
        d.queryResolve = (commands[input+P_RECIPIENT_BASE+j*8+7] >> 2) & 1;
        d.lazyGroup = commands[input+P_RECIPIENT_BASE+j*8+7] >> 4; s.lazyEnabled |= uint(d.lazyGroup != 0); d.statKey = commands[input+P_RECIPIENT_BASE+j*8+6];
        if ((d.kind == 0 || d.kind == 4 || d.kind == 5 || d.kind == 6 || d.kind == 8 || d.kind == 24) && !validRecipientPlan(input+P_RECIPIENT_BASE+j*8)) { s.error = 64; break; }
        if (d.lazyGroup != 0)
        {
            uint plan = input+P_RECIPIENT_BASE+j*8, selector = commands[plan];
            if (d.lazyGroup > s.count || d.kind != 0 && d.kind != 4 || !(selector == 5 || selector == 6 || selector == 7 || selector == 15 || selector == 16)) { s.error = 64; break; }
            uint previous = s.lazyGroupDefinition[d.lazyGroup-1];
            if (previous != 0)
            {
                uint prior = input+P_RECIPIENT_BASE+(previous-1)*8;
                bool same = s.defs[previous-1].owner == d.owner;
                for (uint field = 0; field < 4; field++) if (commands[prior+field] != commands[plan+field]) same = false;
                if (!same) { s.error = 64; break; }
            }
            else s.lazyGroupDefinition[d.lazyGroup-1] = j+1;
        }
        uint bullet = input+P_BULLET_DEFINITION_BASE+j*2;
        d.bulletDuration = commands[bullet]; d.bulletBound = commands[bullet+1];
        if (d.bulletDuration > 0x7fffffff || d.bulletBound > 1 || d.bulletDuration == 0 && d.bulletBound != 0 || d.bulletDuration != 0 && (s.combat == 0 || d.kind != 0 && d.kind != 4)) { s.error = 64; break; }
        uint extra = input+P_DEFINITION_EXTRA_BASE+j*P_DEFINITION_EXTRA_WORDS;
        uint health = input+P_HEALTH_DEFINITION_BASE+j*P_HEALTH_DEFINITION_WORDS;
        d.healthScaling = commands[health]; d.alliedFlags = commands[health+1];
        if (d.kind == 0 && (d.stat >= S_max_hp_pct && d.stat <= S_max_hp_only_pct || d.stat == S_max_hp_from_max_hp_pct)) s.healthMask |= 1;
        if (d.kind == 0 && ((d.alliedFlags & 1) != 0 || d.stat == S_def_caster_based_pct)) s.healthMask |= 2;
        if (d.kind == 0 && d.stat == S_heal_received_pct) s.healthMask |= 4;
        if (d.kind == 0 && d.stat == S_outgoing_heal_pct) s.healthMask |= 8;
        if (d.kind == 6 || d.kind == 8) s.healthMask |= 16;
        d.group = commands[extra]; d.exclusive = commands[extra+1]; d.alias = int(commands[extra+2]); d.quantityFlags = commands[extra+3];
        d.fixedValue = loadNumber(extra+4); d.fixedLiteral = commands[extra+6]; d.polarity = commands[extra+7];
        if (d.group >= s.count || d.alias >= int(j)) { s.error = 64; break; }
        if (d.kind == 0 && d.stat == S_invincible) s.incomingMask |= 1;
        if (d.kind == 0 && d.stat == S_undying) s.incomingMask |= 2;
        if (d.kind == 0 && d.stat == S_received_dmg_pct) s.incomingMask |= 4;
        if ((d.kind == 5 || d.kind == 24 || d.kind == 0 && d.stat == S_burst_cooldown) && s.combat == 0) { s.error = 64; break; }
        if (d.kind == 0 && d.stat == S_burst_cooldown) s.burstModifierMask |= 1;
        if (d.kind == 0 && d.stat == S_reload_speed_pct) s.quantityMask |= 64;
        if (d.kind == 0 && d.stat == S_max_ammo_flat) s.quantityMask |= 16;
        if (d.kind == 0 && d.stat == S_charge_time_flat) s.quantityMask |= 32;
        if (d.kind == 0 && d.stat == S_max_ammo_pct) s.quantityMask |= 1;
        if (d.kind == 0 && (d.stat == S_charge_speed_pct || d.stat == S_charge_speed_caster_based_pct)) s.quantityMask |= 2;
        if ((d.quantityFlags & 64) != 0) s.quantityMask |= 4;
        if (d.kind == 0 && d.stat == S_charge_time_fixed) s.quantityMask |= 8;
        if (d.owner >= 5 || d.triggerCount == 0 || d.triggerCount > P_TRIGGERS || d.conditionCount > P_CONDITIONS) { s.error = 64; break; } s.defs[j] = d;
    }
    initializeHPWatches(s);
    uint queries = 0;
    for (uint step = 0; step < commands[input+2] && s.error == 0; step++)
    {
        uint at = input+P_COMMAND_BASE+step*8, op = commands[at]; uint64_t when = loadNumber(at+1);
        if (s.combat == 0 || op == 4) { beginLazyRoot(s,when); sampleWorld(s); }
        if (op == 4 && s.combat != 0 && s.combatStarted == 0)
        { s.combatStarted = 1; teamNotify(s,0,when,output); initializeMagazines(s,when); }
        if (s.combat == 0 || op == 4) tick(s,when,output);
        if (s.error != 0) break;
        if (op == 0)
        {
            uint event = commands[at+3];
            if (s.combat == 0 && event == 1) s.phase = 5;
            if (s.combat == 0 && event == 2) s.phase = 0;
            dispatch(s,0,event,commands[at+4],int(commands[at+5]),when,output);
        }
        else if (op == 4 && s.combat != 0) { squadFrame(s,when,output); s.frameCount++; }
        else if (op == 25) dispatch(s,8,0,0,int(step),when,output);
        else if (op == 24 && s.combat != 0) advanceCombat(s,when,output);
        else if ((op == 20 || op == 21 || op == 22) && s.combat != 0)
        {
            uint target = commands[at+5], who = commands[at+4];
            if (target >= s.targetCount || who >= 5) { s.error = 64; break; }
            if (op == 20) { s.aim[who] = target; s.target = target; }
            else if (op == 22) s.targetAlive[target] = 0;
            else
            {
                if (s.targetGeneration[target] == 0x7fffffff) { s.error = 2; break; }
                s.targetGeneration[target]++; s.targetAlive[target] = 1; s.targetHP[target] = loadNumber(at+6);
            }
        }
        else if (op == 18)
        {
            uint who = commands[at+4];
            if (who >= 5) { s.error = 64; break; }
            if ((s.downMask & (1U << who)) != 0) continue;
            uint target = s.combat != 0 ? aimedTarget(s,who) : 0;
            if (target == 0xffffffff) continue;
            s.target = target;
            uint64_t amount = damageValue(s,who,loadNumber(at+5),when,true,s.coreBonus,0,ONE,(s.attackContext[who] & 1) != 0);
            if (s.error != 0) break;
            land(s,who,target,amount);
            dispatch(s,0,8,who,0,when,output);
        }
        else if (op == 2)
        {
            uint index = commands[at+6];
            if (index >= P_COMMANDS) { s.error = 64; break; }
            if (s.hpWatchCount != 0) dispatch(s,7,0,0,0,when,output); else syncHealth(s,when);
            writeHealth(s,when,output+P_HEALTH_QUERY_BASE+index*P_HEALTH_QUERY_WORDS);
            writeIncoming(s,output+P_INCOMING_QUERY_BASE+index*P_INCOMING_QUERY_WORDS);
            queries = max(queries,index+1); uint dst = output+P_QUERY_BASE+index*P_QUERY_WORDS;
            storeNumber(dst,when);
            for (uint who = 0; who < 5; who++) { storeNumber(dst+2+2*who,s.total[who]); storeNumber(dst+16+2*who,readStat(s,who,0,when)); }
            uint masks[P_MASK_WORDS]; for (uint word = 0; word < P_MASK_WORDS; word++) masks[word] = 0;
            for (uint j = 0; j < s.count; j++) if (s.timerActive[j] != 0) masks[j/32] |= 1U << (j%32);
            for (uint word = 0; word < P_MASK_WORDS; word++) results[output+P_TIMER_MASK_BASE+index*P_MASK_WORDS+word] = masks[word];
            if (s.combat != 0) writeCombatQuery(s,output+P_COMBAT_QUERY_BASE+index*P_COMBAT_QUERY_WORDS,output+P_COMBAT_STATE_QUERY_BASE+index*P_COMBAT_STATE_QUERY_WORDS);
            results[dst+12] = masks[0]; results[dst+13] = s.combat != 0 ? s.targetGeneration[s.target] : s.generation; results[dst+14] = 0; results[dst+15] = s.timerClock;
        }
        else s.error = 64;
    }
    writeIncoming(s,output+P_INCOMING_STATE_BASE);
    writeHealth(s,commands[input+2] > 0 ? loadNumber(input+P_COMMAND_BASE+(commands[input+2]-1)*8+1) : 0,output+P_HEALTH_STATE_BASE);
    for (uint j = 0; j < s.count; j++)
    {
        uint at = output+P_STATE_BASE+j*10; storeNumber(at,s.due[j]); storeNumber(at+2,s.expiry[j]);
        results[at+4] = s.timerEpoch[j]; results[at+5] = s.timerOrder[j]; results[at+6] = s.timerActive[j];
        results[at+7] = s.stacks[j]; results[at+8] = s.activations[j];
        for (uint slot = 0; slot < 8; slot++) results[output+P_COUNTER_STATE_BASE+j*8+slot] = s.counters[j*8+slot];
        storeNumber(output+P_PERIOD_STATE_BASE+j*4,s.periodDue[j]); storeNumber(output+P_PERIOD_STATE_BASE+j*4+2,s.periodPrevious[j]);
        results[output+P_TIMER_TARGET_BASE+j*2] = s.timerTarget[j];
        results[output+P_TIMER_TARGET_BASE+j*2+1] = s.timerGeneration[j];
    }
    if (s.combat != 0) for (uint who = 0; who < 5; who++)
    {
        uint at = output+P_WEAPON_STATE_BASE+who*P_WEAPON_STATE_WORDS;
        storeNumber(at,s.warm[who]); storeNumber(at+2,s.lastFire[who]); storeNumber(at+4,s.lastInterval[who]);
        storeNumber(at+6,s.postReloadUntil[who]); storeNumber(at+8,s.lastSpread[who]); storeNumber(at+10,s.lastProbability[who]);
        results[at+12] = s.probabilityEvaluations[who]; results[at+13] = s.pendingAutoReload[who]; storeNumber(at+14,s.chargeStartedAt[who]);
    }
    if (s.combat != 0) for (uint j = 0; j < s.targetCount; j++)
    {
        uint dst = output+P_TARGET_STATE_BASE+j*10;
        results[dst] = s.targetGeneration[j]; results[dst+1] = s.targetAlive[j];
        storeNumber(dst+2,s.targetHP[j]); storeNumber(dst+4,s.targetDamage[j]); results[dst+6] = s.targetHits[j];
    }
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint slot = s.orderedRows[pass], at = output+P_CARRIER_STATE_BASE+pass*P_CARRIER_WORDS;
        results[at] = slot; results[at+1] = s.carrierDefinition[slot]; results[at+2] = s.activeRecipients[slot];
        results[at+3] = s.stacks[slot]; results[at+4] = s.alive[slot] | (s.lazyPending[slot] << 1);
        storeNumber(at+5,s.end[slot]); storeNumber(at+7,s.activated[slot]); results[at+9] = s.entryOrder[slot]; storeNumber(at+10,s.hpSnapshot[slot]);
        results[at+12] = uint(s.bulletLeft[slot]);
        for (uint who = 0; who < 5; who++) { results[at+13+who] = s.recipientBullets[slot*5+who]; results[at+18+who] = s.recipientStacks[slot*5+who]; }
    }
    results[output+9] = s.orderedCount;
    results[output+10] = s.cacheCount; results[output+11] = s.cacheEvaluations; results[output+12] = s.cacheReuses; results[output+13] = s.lazyPendingCount; results[output+14] = s.lazyMappedPendingCount; results[output+15] = s.bulletCount;
    results[output] = s.error; results[output+1] = queries; results[output+2] = s.traceCount; results[output+3] = s.maxDepth; results[output+4] = s.burstTraceCount; results[output+6] = s.traceTotal;
    results[output+7] = s.burstTraceTotal; results[output+8] = s.frameCount;
}
