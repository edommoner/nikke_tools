#include "binary64.slang"
#include "core_probability.slang"
#include "portable_schema.slang"
#include "stack_numeric.slang"

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
    uint damageRoute, damageCount, damageHits, damageNormal, damagePending, pendingHits; uint64_t damageGauge;
    uint bulletDuration, bulletBound;
    uint durationGroup, durationCast;
    uint periodicFlags, periodicGroup;
    uint healthScaling, alliedFlags, buffEvent, enemyBuff, mergeEligible, statKey, lazyGroup, queryResolve;
};
struct Frame
{
    uint mode, event, owner, cursor, target, value, repeatRow, repeatLeft, repeatPassive;
    int argument;
    uint64_t time, healthValue, healthPrevious, healthNext;
};
struct Runtime
{
    uint sourceEnabled; uint64_t sourceTime;
    uint stagedEnabled,stagedScopeRow,stagedScopeGeneration,stagedScopeEntry,stagedScopeStack;
    uint resourceCount, resourceAmmoObserved, resourceTraceCount, resourceTraceTotal, resourceOutput;
    uint bulletHead, bulletTail, bulletCount, bulletLinked[P_CARRIERS], bulletPrev[P_CARRIERS], bulletNext[P_CARRIERS], bulletInitialized[P_CARRIERS];
    int bulletLeft[P_CARRIERS]; uint recipientBullets[P_CARRIERS*5], recipientStacks[P_CARRIERS*5];
    uint carrierCount, carrierDefinition[P_CARRIERS], multiCarrier[P_DEFINITIONS], removalCount;
    uint lazyPending[P_CARRIERS], lazyLink[P_CARRIERS], lazyPendingCount, lazyMappedPendingCount, lazyEnabled;
    uint cacheCount, cacheCursor, cacheEvaluations, cacheReuses;
    uint cacheGroup[P_LAZY_CACHE], cacheMask[P_LAZY_CACHE], cacheOrder[P_LAZY_CACHE], cacheRefs[P_LAZY_CACHE];
    uint cacheNewest[P_DEFINITIONS], cacheSeen[P_DEFINITIONS], lazyGroupDefinition[P_DEFINITIONS];
    uint64_t cacheTime[P_LAZY_CACHE], cacheNewestTime[P_DEFINITIONS], cacheRootTime, cacheFloor;
    uint queryActive, queryWho, queryAllowed[P_CARRIERS]; uint64_t queryWhen;
    uint incomingMask, downMask, activeRecipients[P_CARRIERS], carrierRecipientOrder[P_CARRIERS], receivedHits[5];
    uint64_t receivedDamage[5];
    uint hpWatchCount, hpWatchSlots[P_DEFINITIONS*P_TRIGGERS], hpDirtyMask, hpPendingMask, hpEdgeGuard;
    uint64_t hpPrevious[5], hpNext[5];
    uint durationEnabled, lastB3Caster, durationGroupFirst[P_DEFINITIONS]; uint64_t lastB3Time, lastFullStart;
    uint landingPolicy;
    uint healthMask; int healSource;
    uint pendingCount, pendingEnqueued, pendingFired, damageExclusion;
    uint pendingRow[P_PENDING], pendingHits[P_PENDING]; uint64_t pendingCoefficient[P_PENDING], pendingCastTime[P_PENDING], pendingAmount[P_PENDING];
    uint coverMask, coverSync; uint64_t baseCoverHP[5], coverHP[5], coverMaxHP[5], coverDamage[5];
    uint64_t baseHP[5], hp[5], hpPct[5], baseDefense[5], hpSnapshot[P_CARRIERS], healing[5];
    uint quantityMask, weaponInitialized[5], modeMagazine[5], delayCover[5], pendingAutoReload[5];
    uint64_t rawCharge[5], activated[P_CARRIERS];
    uint rawRate[5], clipCount[5], geometry[5], probabilityValid[5], probabilityEvaluations[5];
    uint64_t chargeStartedAt[5], minCycle[5], gaugeMultiplier[5], coreDamageBonus[5];
    uint64_t warm[5], lastFire[5], lastInterval[5], postReloadUntil[5];
    uint64_t rateMin[5], rateMax[5], warmLimit[5], coolTime[5], postReloadDelay[5];
    uint64_t spreadStart[5], spreadEnd[5], spreadShots[5], coreDiameter[5], lastSpread[5], lastProbability[5], probabilityRatio[5];
    int modeIndex[5], physicalModeIndex[5];
    uint currentStage[5], enemySnapshot, attackContext[5];
    uint64_t fullChargeMult[5];
    uint modeEpoch[5], appliedEpoch[5], modeShots[5], pendingReentry[5], reentrySlot, reentryDone, casts[5], burstTraceCount;
    uint pellets[5], muzzles[5], inputBase;
    uint64_t modeEnd[5], reentryDelay;
    uint automaticAddAim, enemyAttackOrder, enemySpawnOrder, combatStarted, combat, targetCount, target, aim[5], targetAlive[8], targetGeneration[8], targetHits[8];
    uint64_t targetHP[8], targetMaxHP[8], targetDamage[8], targetDefense[8];
    uint64_t scoredDamage[5], addScoredDamage[5], addOverkill[5], targetScoredDamage[8], targetDealt[8];
    uint timerTarget[P_DEFINITIONS], periodicOrder[P_DEFINITIONS], periodicGeneration[P_DEFINITIONS*8], periodicOwner[P_DEFINITIONS];
    uint weaponEnabled[5], weaponMode[5], capacity[5], shots[5], stage[5], charging[5];
    int ammo[5]; uint reloadCancelOnFull[5], modeCapacityEpoch[5];
    uint frameAmmoActive[5], frameAmmoBase[5], infiniteRowCount, infiniteRows[P_CARRIERS];
    uint enemyBuffCount, enemyBuffRows[P_CARRIERS], enemyCaptureGeneration[P_CARRIERS], enemyEpoch, enemyBirth[8];
    uint namedEventOwners, stackEventOwners; uint phase, castMask, traceMode, traceTotal, burstTraceTotal, nextFrame, frameCount, clockMode; uint64_t frameTime;
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
#include "runtime_init.slang"
#include "definition_runtime.slang"

[ForceInline]
Definition residentDefinition(inout Runtime s, uint slot) { return readDefinition(s.inputBase,s.carrierDefinition[slot]); }

struct Sum { uint64_t total; uint64_t correction; };
void addSum(inout Sum sum, uint64_t term)
{
    uint64_t combined = f64Add(sum.total,term);
    uint64_t correction = !f64Less(f64Abs(sum.total),f64Abs(term)) ?
        f64Add(f64Add(sum.total,combined ^ F64_SIGN),term) : f64Add(f64Add(term,combined ^ F64_SIGN),sum.total);
    sum.correction = f64Add(sum.correction,correction); sum.total = combined;
}
#include "resource_runtime.slang"
#include "source_runtime.slang"
#include "reference_runtime.slang"
#include "staged_runtime.slang"

// Definition predicates use compiled IDs and exact binary64 operands.
// Runtime tests are deliberately distinct from activation-time gates.
bool stateMember(inout Runtime s, uint who, int name, uint flags)
{
    for (uint j = 0; j < s.carrierCount; j++)
        if (s.alive[j] != 0 && int(residentDefinition(s,j).name) == name && (s.activeRecipients[j] & (1U << who)) != 0) return true;
    if (s.combat == 0) return flags == 2;
    int mode = s.modeIndex[who];
    if (flags == 1) return mode >= 0;
    if (mode >= 0) return int(definition_name(s.inputBase,mode)) == name;
    return flags == 2;
}
[noinline]
bool basicConditions(inout Runtime s, uint row, uint64_t when, bool runtime, uint recipient = 0xffffffff)
{
    uint definition = s.carrierDefinition[row]; Definition d = readDefinition(s.inputBase,definition);
    if (runtime && (referenceCaptureFlags(s,row)&4)==0 && (!f64Less(d.duration,0) || (d.flags & 2) == 0)) return true;
    for (uint i = 0; i < d.conditionCount; i++)
    {
        uint at = s.inputBase+P_CONDITION_BASE+definition*P_CONDITION_WORDS+i*4;
        uint kind = commands[at]; int name = int(commands[at+1]); uint64_t arg = loadNumber(at+2);
        if (runtime && kind != C_GAUGE_ABOVE && kind != C_GAUGE_BELOW && kind != C_FULL && kind != C_NOT_FULL && kind != C_SELF_STATE && kind != C_NOT_SELF_STATE && kind != C_SELF_STACK && kind != C_CAST && kind != C_NOT_CAST && kind != C_CHARGING && kind != C_ENEMIES_ABOVE && kind != C_ENEMIES_BELOW && kind != C_HP_ABOVE && kind != C_HP_BELOW && kind != C_HP_MAX && kind != C_ALLY_HP_BELOW && kind != C_COVER_ALIVE && kind != C_COVER_BROKEN) continue;
        if (kind >= C_GAUGE_ABOVE && kind <= C_GAUGE_MOD && !resourceCondition(s,d.owner,kind,uint(name),arg,int(commands[s.inputBase+P_RESOURCE_CONDITION_BASE+definition*3+i]))) return false;
        if (kind == C_FULL && s.phase != 5 || kind == C_NOT_FULL && s.phase == 5) return false;
        if (kind == C_SELF_STATE || kind == C_NOT_SELF_STATE)
        {
            uint flags = f64Equal(arg,ONE) ? 1 : f64Equal(arg,f64FromI64(2)) ? 2 : 0;
            bool present = stateMember(s,d.owner,name,flags);
            if (kind == C_SELF_STATE && !present || kind == C_NOT_SELF_STATE && present) return false;
        }
        if (kind == C_SELF_STACK)
        {
            uint64_t count = 0;
            for (uint pass = 0; pass < s.orderedCount; pass++)
            {
                uint j = s.orderedRows[pass]; Definition carrier = residentDefinition(s,j);
                bool member=(s.activeRecipients[j]&(1U<<d.owner))!=0;
                if (carrier.enemyBuff!=0) for (uint enemy=0; enemy<s.targetCount; enemy++)
                    if ((s.activeRecipients[j]&(1U<<(enemy+5)))!=0 && s.targetAlive[enemy]!=0 && s.targetGeneration[enemy]==enemyCarrierGeneration(s,j,enemy)) member=true;
                if (carrier.kind==3)
                { uint packed; member=(carrier.periodicFlags&1)!=0 ? periodicDamageMask(s,s.carrierDefinition[j],packed)!=0 : targetLive(s,s.timerTarget[s.carrierDefinition[j]],s.timerGeneration[s.carrierDefinition[j]]); }
                if (carrier.owner == d.owner && int(carrier.name) == name && s.alive[j] != 0 && member) { count = carrierStackValue(s,j); break; }
            }
            if (s.combat != 0 && s.modeIndex[d.owner] >= 0 && int(definition_name(s.inputBase,s.modeIndex[d.owner])) == name) count = ONE;
            if (f64Less(count,arg)) return false;
        }
        if (kind == C_HP_ABOVE && f64Less(s.hpPct[d.owner],arg) || kind == C_HP_BELOW && f64Less(arg,s.hpPct[d.owner]) || kind == C_HP_MAX && f64Less(s.hpPct[d.owner],HUNDRED)) return false;
        if (kind == C_COVER_ALIVE && f64Zero(s.coverHP[d.owner]) || kind == C_COVER_BROKEN && !f64Zero(s.coverHP[d.owner])) return false;
        if (kind == C_NOT_SELF_HEAL && (s.healSource < 0 || uint(s.healSource) == d.owner)) return false;
        if (kind == C_ALLY_HP_BELOW)
        {
            bool present = false;
            if (runtime) present = recipient < 5 ? !f64Less(arg,s.hpPct[recipient]) : !f64Less(arg,HUNDRED);
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
[noinline]
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
    uint enemyPosition = 0; while (enemyPosition < s.enemyBuffCount && s.enemyBuffRows[enemyPosition] != row) enemyPosition++;
    if (enemyPosition < s.enemyBuffCount)
    { for (uint i = enemyPosition; i+1 < s.enemyBuffCount; i++) s.enemyBuffRows[i] = s.enemyBuffRows[i+1]; s.enemyBuffCount--; }
    if (residentDefinition(s,row).enemyBuff != 0) s.enemyBuffRows[s.enemyBuffCount++] = row;
    // Keep the boolean-stat index in precisely the same activation order.
    uint position = 0; while (position < s.infiniteRowCount && s.infiniteRows[position] != row) position++;
    if (position < s.infiniteRowCount)
    {
        for (uint i = position; i+1 < s.infiniteRowCount; i++) s.infiniteRows[i] = s.infiniteRows[i+1];
        s.infiniteRowCount--;
    }
    Definition indexed = residentDefinition(s,row);
    if (indexed.kind == 0 && indexed.stat == S_infinite_ammo) s.infiniteRows[s.infiniteRowCount++] = row;
}

bool excludedDamageBuff(inout Runtime s, uint resident, uint who)
{
    if (s.damageExclusion == 0 || definition_owner(s.inputBase,s.damageExclusion-1) != who) return false;
    uint definition = s.carrierDefinition[resident];
    uint at = s.inputBase+P_PENDING_EXCLUDE_BASE+(s.damageExclusion-1)*P_MASK_WORDS;
    return (commands[at+definition/32] & (1U << (definition%32))) != 0;
}
#include "bullet_runtime.slang"
#include "rank_runtime.slang"
#include "lazy_runtime.slang"
#include "enemy_buff_runtime.slang"
#include "carrier_runtime.slang"
#include "quantity_runtime.slang"
#include "health_runtime.slang"
#include "lifesteal_runtime.slang"
#include "cover_runtime.slang"
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
        if (d.alliedFlags != 0 || d.kind != 0 || d.stat >= 64 || d.stat == S_infinite_ammo || s.alive[selected] == 0 || !f64Less(when,s.end[selected]) ||
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
    for (uint i = 0; i < definition_conditionCount(s.inputBase,row); i++)
    {
        uint at = s.inputBase+P_CONDITION_BASE+row*P_CONDITION_WORDS+i*4;
        if (commands[at] == C_STAT_ABOVE && !f64Less(loadNumber(at+2),readStat(s,definition_owner(s.inputBase,row),commands[at+1],when))) return false;
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
#include "enemy_spawn_order_runtime.slang"
#include "enemy_aim_runtime.slang"

uint aimedTarget(inout Runtime s, uint who)
{
    if ((s.automaticAddAim & (1U << who)) != 0) return automaticEnemyAim(s,enemySpawnSequence(s));
    uint t = s.aim[who];
    if (s.targetAlive[t] != 0) return t;
    for (uint j = 0; j < s.targetCount; j++) if (s.targetAlive[j] != 0) return j;
    return 0xffffffff;
}
[noinline]
void land(inout Runtime s, uint who, uint target, uint64_t amount)
{
    if (s.combat != 0 && s.targetHits[target] == 0x7fffffff) { s.error = 2; return; }
#ifdef PORTABLE_ACCOUNTING_REFERENCE
    bool separate = true;
#else
    bool separate = s.combat != 0 && s.targetCount > 1;
#endif
    if (separate)
    {
        bool add = s.combat != 0 && target != 0;
        uint64_t remaining = add ? larger(0,f64Add(s.targetMaxHP[target],s.targetDealt[target] ^ F64_SIGN)) : amount;
        uint64_t scored = smaller(amount,remaining);
        if (add)
        {
            s.addScoredDamage[who] = f64Add(s.addScoredDamage[who],scored);
            s.targetDealt[target] = f64Add(s.targetDealt[target],scored);
        }
        else s.scoredDamage[who] = f64Add(s.scoredDamage[who],scored);
        s.addOverkill[who] = f64Add(s.addOverkill[who],f64Add(amount,scored ^ F64_SIGN));
        if (s.combat != 0) s.targetScoredDamage[target] = f64Add(s.targetScoredDamage[target],scored);
    }
    s.total[who] = f64Add(s.total[who],amount);
    if (s.combat == 0) return;
    s.targetDamage[target] = f64Add(s.targetDamage[target],amount);
    s.targetHP[target] = target != 0 ? larger(0,f64Add(s.targetMaxHP[target],s.targetDealt[target] ^ F64_SIGN)) : larger(0,f64Add(s.targetHP[target],amount ^ F64_SIGN));
    s.targetHits[target]++;
    if (f64Zero(s.targetHP[target])) s.targetAlive[target] = 0;
}

[noinline]
void writeDamageAccounting(inout Runtime s, uint output, bool targets = false)
{
#ifdef PORTABLE_ACCOUNTING_REFERENCE
    bool separate = true;
#else
    bool separate = s.combat != 0 && s.targetCount > 1;
#endif
    for (uint who = 0; who < 5; who++)
    {
        storeNumber(output+who*2,separate ? f64Add(s.scoredDamage[who],s.addScoredDamage[who]) : s.total[who]);
        storeNumber(output+10+who*2,s.addOverkill[who]);
        storeNumber(output+20+who*2,separate ? s.scoredDamage[who] : s.total[who]);
        storeNumber(output+30+who*2,s.addScoredDamage[who]);
    }
    if (targets && s.combat != 0) for (uint target = 0; target < s.targetCount; target++)
        storeNumber(output+40+target*2,separate ? s.targetScoredDamage[target] : s.targetDamage[target]);
}

// End the old session before callbacks. A child may install a new session.
void clearMode(inout Runtime s, uint who, uint64_t when)
{
    s.modeIndex[who] = -1; s.modeEpoch[who]++; s.appliedEpoch[who] = s.modeEpoch[who]; s.modeShots[who] = 0;
    // A logical mode cancelled before any physical entry never replaced the gun.
    if (s.physicalModeIndex[who] < 0) return;
    // End callbacks operate on the restored base magazine, not the capacity
    // captured for the old physical shot. Pending-only modes keep that shot.
    s.frameAmmoActive[who] = 0;
    // -2 means a physical mode ended: the first base-weapon frame must
    // restart cadence at its own sampling time, without refilling a second time.
    s.physicalModeIndex[who] = -2; s.pendingAutoReload[who] = 0;
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

#include "damage_runtime.slang"
#include "incoming_runtime.slang"
#include "burst_runtime.slang"
#include "enemy_attack_rank_runtime.slang"
#include "enemy_damage_runtime.slang"
#include "landing_runtime.slang"
#include "periodic_runtime.slang"
#include "removal_runtime.slang"
#include "duration_extend_runtime.slang"
#include "stack_runtime.slang"
#include "status_runtime.slang"
#include "event_candidate_runtime.slang"
#include "pending_burst_runtime.slang"

[noinline]
uint packedRecipientMask(uint order)
{
    uint mask = 0;
    for (uint i = 0; i < 5; i++) { uint who = (order >> (3*i)) & 7; if (who != 0) mask |= 1U << (who-1); }
    return mask;
}
[noinline]
uint buffAudienceOrder(inout Runtime s, uint row)
{
    Definition d = residentDefinition(s,row);
    if (d.enemyBuff != 0 && (d.buffEvent & 2) != 0) return 0;
    if ((d.buffEvent & 2) == 0) return 1U | (2U<<3) | (3U<<6) | (4U<<9) | (5U<<12);
    if (s.lazyPending[row] != 0) return d.owner+1;
    uint result = 0, count = 0, order = s.carrierRecipientOrder[row];
    for (uint i = 0; i < 5; i++)
    {
        uint who = (order >> (3*i)) & 7;
        if (who != 0 && (s.activeRecipients[row] & (1U << (who-1))) != 0) { result |= who << (3*count); count++; }
    }
    return result;
}

[noinline]
void advanceBuffActivation(inout Runtime s, inout Frame frames[32], inout int depth)
{
    Frame f = frames[depth];
            uint slot = uint(f.argument); Definition buff = readDefinition(s.inputBase,f.repeatRow);
            if (f.event == 0)
            {
                frames[depth].event = 1;
                if (f.repeatLeft == 0)
                {
                    if ((buff.buffEvent&1)!=0 && uint(f.healthValue) != 0) pushFrame(s,frames,depth,12,31,buff.owner,int(buff.name),f.time,uint(f.healthValue));
                }
                else if (f.healthPrevious != f.healthNext && (s.stackEventOwners & (1U << buff.owner)) != 0)
                    pushFrame(s,frames,depth,0,9,buff.owner,int(buff.name),f.time,uint(f.healthNext));
                return;
            }
            if (f.event == 1)
            {
                frames[depth].event = 2;
                if (f.repeatLeft == 0)
                {
                    if ((buff.buffEvent&1)!=0 && (s.stackEventOwners & (1U << buff.owner)) != 0) pushFrame(s,frames,depth,0,9,buff.owner,int(buff.name),f.time,1);
                }
                else if ((buff.buffEvent&1)!=0 && buff.maxStack != 1)
                {
                    // Refresh computes its audience after synchronous stack children.
                    uint order = s.entryOrder[slot] == f.repeatPassive ? buffAudienceOrder(s,slot) : uint(f.healthValue);
                    if (order != 0 && (s.namedEventOwners & packedRecipientMask(order)) != 0)
                        pushFrame(s,frames,depth,12,31,buff.owner,int(buff.name),f.time,order);
                }
                return;
            }
            if (f.repeatLeft!=0 && s.entryOrder[slot]==f.repeatPassive && s.carrierDefinition[slot]==f.repeatRow) captureBuffReference(s,slot,f.cursor-1);
            rechargeImmunity(s,f.cursor-1,packedRecipientMask(f.value)|(f.value>>16));
            depth--;
            // CPU health postprocessing finds the still-active effect after all
            // notifications; cancellation can remove it or reinstall a carrier.
            if (buff.lazyGroup != 0 || f.value == 0 || !(buff.stat >= S_max_hp_pct && buff.stat <= S_max_hp_only_pct || buff.stat == S_max_hp_from_max_hp_pct)) return;
            uint active = P_CARRIERS;
            for (uint i = 0; i < s.orderedCount; i++)
            { uint candidate = s.orderedRows[i]; if (s.alive[candidate] != 0 && s.carrierDefinition[candidate] == f.repeatRow) { active = candidate; break; } }
            if (active == P_CARRIERS) return;
            uint64_t grant = prepareHealthGrant(s,active,f.time);
            if (s.hpWatchCount != 0)
            { pushFrame(s,frames,depth,5,0,buff.owner,int(active),f.time,f.value); if (s.error == 0) frames[depth].healthValue = grant; }
            else
            {
                uint mask = packedRecipientMask(f.value);
                if (!f64Zero(grant)) for (uint who = 0; who < 5; who++) if ((mask & (1U << who)) != 0)
                    s.hp[who] = smaller(f64Add(s.hp[who],grant),effectiveMaxHP(s,who,f.time));
                syncHealth(s,f.time);
            }
            return;
}

[noinline]
void dispatch(inout Runtime s, uint mode, uint event, uint owner, int argument, uint64_t when, uint output, uint64_t landingAmount = 0)
{
    if (owner >= 5) { s.error = 64; return; }
    s.sourceTime=when; syncHealth(s,when);
    uint entryTarget = s.target;
    Frame frames[32]; int depth = -1;
    if ((s.healthMask&32)!=0) pushFrame(s,frames,depth,16,0,0,0,when);
    pushFrame(s,frames,depth,mode,event,owner,argument,when);
    if (mode == 17 && s.error == 0) frames[depth].healthValue=landingAmount;
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
        Frame f = frames[depth]; s.sourceTime=f.time; s.target = f.target; s.healSource = f.event == 16 ? f.argument : -1; uint row = s.count, passive = 0;
        if (f.cursor == 0 && (f.mode == 0 || f.mode == 1 || f.mode == 2) &&
            (s.downMask & (1U << f.owner)) != 0 && f.event != 26 && f.event != 28 && f.event != 38)
        { depth--; continue; }
        if (f.mode==18)
        {
            uint encoded=f.cursor<8 ? (f.value>>(f.cursor*4))&15 : 0;
            if(encoded==0) { depth--;continue; }
            uint target=encoded-1;frames[depth].cursor++;
            uint generation=target<2 ? uint(f.healthValue>>(32*target)) : target<4 ? uint(f.healthPrevious>>(32*(target-2))) : target<6 ? uint(f.healthNext>>(32*(target-4))) : target==6 ? f.repeatLeft : f.repeatPassive;
            pushFrame(s,frames,depth,19,f.event,f.owner,f.argument,f.time,1U<<(target+5));
            if(s.error==0) frames[depth].repeatPassive=generation;
            continue;
        }
        if (f.mode==16)
        {
            if (f.cursor==0) { frames[depth].cursor=1; syncHealth(s,f.time); continue; }
            uint guard=s.hpEdgeGuard; s.hpEdgeGuard=1;
            for (uint who=0; who<5 && s.error==0; who++) syncHealthActor(s,who,f.time);
            s.hpEdgeGuard=guard; depth--; continue;
        }
        if (f.mode == 14)
        {
            uint64_t boundary;
            if (!nextResourceBoundary(s,f.owner,uint(f.argument),f.healthPrevious,f.healthNext,boundary)) { depth--; continue; }
            frames[depth].healthPrevious = boundary;
            logResourceNotification(s,30,f.owner,uint(f.argument),f.time,boundary,output);
            if (s.error == 0) pushFrame(s,frames,depth,0,30,f.owner,f.argument,f.time);
            if (s.error == 0) frames[depth].healthValue = boundary;
            continue;
        }
        if (f.mode == 15)
        {
            if (f.value == 0) { depth--; continue; }
            frames[depth].value--;
            logResourceNotification(s,26,f.owner,uint(f.argument),f.time,ONE,output);
            if (s.error == 0) pushFrame(s,frames,depth,0,26,f.owner,0,f.time); continue;
        }
        if (f.mode == 13) { advanceBuffActivation(s,frames,depth); continue; }
        if (f.mode == 12)
        {
            // A resumable squad broadcast keeps depth bounded and the original
            // name/order intact even when one recipient changes the mode.
            if (f.cursor == 5) { depth--; continue; }
            uint index = frames[depth].cursor++;
            uint encoded = f.value == 0 ? index+1 : (f.value >> (3*index)) & 7;
            if (encoded == 0) { depth--; continue; }
            pushFrame(s,frames,depth,0,31,encoded-1,f.argument,f.time);
            continue;
        }
        if (f.mode == 10)
        {
            Definition damage = readDefinition(s.inputBase,uint(f.argument)); damage.damageHits=f.repeatLeft;
            if (f.cursor >= damage.damageHits || f64Zero(f.healthValue))
            {
                depth--;
                if (s.combat != 0 && f.value != 0)
                {
                    uint64_t gain = f64Less(damage.damageGauge,0) ? s.gain[damage.owner] : damage.damageGauge;
                    addBurstGauge(s,f64Mul(gain,f64FromI64(f.value)));
                }
                continue;
            }
            if (s.landingPolicy != 0)
            {
                if (f.cursor == 0)
                {
                    s.target=damage.damageRoute>=2 || damage.damageRoute==1 ? 0 : f.target;
                    frames[depth].healthPrevious=damage.damageNormal!=0 ? damageValue(s,damage.owner,f.healthValue,f.time,true,s.combat!=0 ? s.coreDamageBonus[damage.owner] : s.coreBonus,damage.damageFlags,ONE,(s.attackContext[damage.owner]&1)!=0) : damageValue(s,damage.owner,f.healthValue,f.time,false,s.coreBonus,damage.damageFlags);
                    uint order=0;frames[depth].repeatRow=(damage.periodicFlags&1)!=0 ? periodicDamageMask(s,uint(f.argument),order) : 0xffffffff;
                    frames[depth].repeatPassive=order;frames[depth].healthNext=s.enemyEpoch;
                }
                if (s.error!=0) break;
                enqueueLanding(s,uint(f.argument),f.target,frames[depth].repeatRow,frames[depth].repeatPassive,frames[depth].healthPrevious,f.time,f.cursor+1,damage.damageHits,uint(depth+1),uint(frames[depth].healthNext));
                frames[depth].cursor++;frames[depth].value++;
                if (s.error==0) pushFrame(s,frames,depth,0,49,damage.owner,int(damage.name),f.time);
                continue;
            }
            uint packedOrder; uint mask = (damage.periodicFlags & 1) != 0 ? periodicDamageMask(s,uint(f.argument),packedOrder) : enemyDamageMask(s,damage,f.target,packedOrder);
            if (mask == 0 && (damage.periodicFlags & 1) == 0) { frames[depth].cursor = damage.damageHits; continue; }
            uint basis = damage.damageRoute >= 2 || damage.damageRoute == 1 ? 0 : f.target;
            s.target = basis;
            uint64_t coefficient = f.healthValue, amount;
            if (damage.damageNormal != 0)
                amount = damageValue(s,damage.owner,coefficient,f.time,true,s.combat != 0 ? s.coreDamageBonus[damage.owner] : s.coreBonus,damage.damageFlags,ONE,(s.attackContext[damage.owner] & 1) != 0);
            else amount = damageValue(s,damage.owner,coefficient,f.time,false,s.coreBonus,damage.damageFlags);
            if (s.error != 0) break;
            uint64_t weighted = (damage.damageFlags & H_SPLIT) != 0 && damage.damageRoute >= 2 && (damage.periodicFlags & 1) == 0 ? f64Mul(amount,f64Div(ONE,f64FromI64(enemyMaskCount(mask)))) : amount;
            uint64_t share = weighted;
            if ((damage.damageFlags & H_SPLIT) != 0 && enemyMaskCount(mask) > 1)
            {
                uint status; uint64_t rounded = f64ToI64(weighted,0,status);
                if (status != 0) { s.error = 16; break; }
                share = f64FromI64(rounded);
            }
            for (uint pass = 0; pass < 8; pass++)
            { uint encoded = (packedOrder >> (pass*4)) & 15; if (encoded == 0) break; land(s,damage.owner,encoded-1,share); }
            frames[depth].cursor++; frames[depth].value++;
            logDamagePacket(s,damage,uint(f.argument),mask,basis,f.cursor+1,share,weighted,packedOrder,f.time,uint(depth+1),output);
            if (s.error == 0) pushFrame(s,frames,depth,0,49,damage.owner,int(damage.name),f.time);
            continue;
        }
        if (f.mode == 11)
        {
            Definition cover = readDefinition(s.inputBase,uint(f.argument));
            uint encoded = f.cursor < 5 ? (f.value >> (3*f.cursor)) & 7 : 0;
            if (encoded == 0) { depth--; continue; }
            frames[depth].cursor++; uint who = encoded-1;
            if ((s.downMask & (1U << who)) != 0) continue;
            if (cover.kind == 30)
            {
                if (f64Zero(cover.value)) { s.error = 64; break; }
                if (f64Zero(s.coverHP[who])) s.coverHP[who] = larger(0,f64Div(f64Mul(s.coverMaxHP[who],cover.value),HUNDRED));
            }
            else if (!f64Zero(s.coverHP[who]) && !f64Zero(cover.value))
            {
                uint64_t base = cover.healthScaling != 0 ? effectiveMaxHP(s,cover.owner,f.time) : s.coverMaxHP[who];
                s.coverHP[who] = smaller(s.coverMaxHP[who],f64Add(s.coverHP[who],f64Div(f64Mul(base,cover.value),HUNDRED)));
                if (!f64Finite(s.coverHP[who])) { s.error = 16; break; }
                pushFrame(s,frames,depth,0,17,who,0,f.time);
            }
            continue;
        }
        if (f.mode == 9)
        {
            if (f.cursor == f.repeatLeft) { s.removalCount = f.value; depth--; continue; }
            uint payload=loadRemovalNotice(s,f.value+f.cursor);frames[depth].cursor++;
            uint index=f.value+f.cursor,stack=loadStackNoticeValue(s,index);
            pushFrame(s,frames,depth,0,(payload&32768)!=0 ? 9 : 29,payload&7,int((payload>>3)&255),f.time,stack);continue;
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
                uint observer = definition_owner(s.inputBase,s.hpWatchSlots[watch]/8);
#ifdef PORTABLE_HP_WATCH_SCAN_REFERENCE
                bool seen = false;
                for (uint i = 0; i < watch; i++)
                {
                    uint prior = hpWatchAddress(s,i);
                    if (definition_owner(s.inputBase,s.hpWatchSlots[i]/8) == observer && commands[prior] == commands[at] && commands[prior+4] == commands[at+4]) seen = true;
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
        if (f.mode == 17)
        {
            depth--;
            if (applyLifestealState(s,f.owner,f.healthValue,f.time) && s.error == 0)
                pushFrame(s,frames,depth,0,16,f.owner,int(f.owner),f.time);
            continue;
        }
        if (f.mode == 3)
        {
            depth--; if ((s.downMask & (1U << f.owner)) != 0) continue;
            Definition heal = readDefinition(s.inputBase,uint(f.argument));
            uint64_t base = heal.healthScaling != 0 ? effectiveMaxHP(s,heal.owner,f.time) : s.baseHP[f.owner];
            uint64_t amount = f64Mul(f64Div(f64Mul(base,heal.value),HUNDRED),healMultiplier(s,f.owner,heal.owner,f.time));
            if (!f64Finite(amount)) { s.error = 16; break; }
            uint64_t before = s.hp[f.owner];
            s.hp[f.owner] = smaller(f64Add(before,amount),effectiveMaxHP(s,f.owner,f.time));
            s.healing[f.owner] = f64Add(s.healing[f.owner],larger(0,f64Add(s.hp[f.owner],before ^ F64_SIGN)));
            syncHealthActor(s,f.owner,f.time);
            pushFrame(s,frames,depth,0,16,f.owner,int(heal.owner),f.time); continue;
        }
        if (f.mode == 1 || f.mode == 19)
        {
            if (f.cursor == 0 && f.argument >= 0 && uint(f.argument) < s.count) row = uint(f.argument);
            frames[depth].cursor++;
        }
        else if (f.repeatLeft != 0)
        { row = f.repeatRow; passive = f.repeatPassive; frames[depth].repeatLeft--; }
        else
        {
#ifndef PORTABLE_NAMED_EVENT_SCAN_REFERENCE
            // Keep the frame, health drains and work/depth accounting intact.
            // With no named-event listener for this owner, no definition can match.
            if (f.mode == 0 && f.event == 31 && (s.namedEventOwners & (1U << f.owner)) == 0)
                frames[depth].cursor = s.count;
#endif
            while (frames[depth].cursor < s.count)
            {
#ifndef PORTABLE_EVENT_SCAN_REFERENCE
                if (f.mode == 0)
                {
                    frames[depth].cursor = nextEventCandidate(s,f.event,frames[depth].cursor);
                    if (frames[depth].cursor >= s.count) break;
                }
#endif
                uint j = frames[depth].cursor++; Definition d = readDefinition(s.inputBase,j);
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
                    if ((event == 9 || event == 29 || event == 30 || event == 31 || event == 48 || event == 49 || event == 59) && tag != f.argument) continue;
                    if (event == 9 && commands[at+5] != f.value) continue;
                    multiplicity++; bool ok = event != 30 || resourceModulo(f.healthValue,uint(f64ToPositiveStep(loadNumber(at+1)))) == 0;
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
        Definition d = readDefinition(s.inputBase,row);
        if (f.mode == 2)
        { pushFrame(s,frames,depth,1,47,d.owner,int(row),f.time); continue; }
        if (f.mode == 0 && !activationConditions(s,row,f.time) && !(f.event == 0 && f64Less(d.duration,0) && passive != 0)) continue;
        if(d.kind==15 && f.event!=28 && d.budget>=0 && s.activations[row]>=uint(d.budget)) continue;
        uint recipientOrder = 0, recipientMask = f.mode==19 ? f.value : d.recipients, enemyOrder=0;
        if(stackOperation(d.kind))
        {
            uint order;
            if((f.event!=28 || (d.flags&1)!=0 && s.alive[row]==0) && d.budget>=0 && !stackLazySelector(s,row) && stackSelectedRecipients(s,row,f.target,f.time,true,order)==0) continue;
            recipientMask=d.kind>=19 ? stackSelectedRecipients(s,row,f.target,f.time,false,order) : 0;
        }
        if (f.mode!=19 && (d.kind == 0 || d.kind == 4 || d.kind == 5 || d.kind == 6 || d.kind == 7 || d.kind == 8 || d.kind == 13 || d.kind == 14 || d.kind == 24 || d.kind == 30 || d.kind==15 || d.kind==26))
        {
            if(d.kind==15 && d.budget<0 && !hasDurationExtensionMembers(s,row)) recipientMask=0;
            else if (d.enemyBuff != 0 || (d.kind==15 || d.kind==26) && d.target==2)
            { recipientMask = enemyDamageMask(s,d,f.target,enemyOrder) << 5; recipientOrder = 0; }
            else if (d.lazyGroup == 0) recipientMask = selectRecipients(s,row,f.time,recipientOrder);
            else recipientMask = 0;
            uint selector = commands[s.inputBase+P_RECIPIENT_BASE+row*8];
            bool lazy = selector == 5 || selector == 6 || selector == 7 || selector == 15 || selector == 16;
            if (d.budget >= 0 && recipientMask == 0 && (!lazy || d.kind==15)) continue;
        }
        uint stagedTotal=0;
        bool stageRegister=s.stagedEnabled!=0 && isStaged(s,row) && (f.event!=28 || (d.flags&1)!=0 && s.alive[row]==0);
        if(stageRegister) { stagedTotal=stagedCount(s,row);if(s.error!=0) break;if(stagedTotal==0) continue; }
        if (f.mode!=19 && (f.event != 28 || (d.flags & 1) != 0 && ((s.stagedEnabled==0 || !isStaged(s,row)) || stageRegister)))
        {
            if (d.budget >= 0 && s.activations[row] >= uint(d.budget)) continue;
            if (s.activations[row] == 0x7fffffff) { s.error = 2; break; }
            s.activations[row]++;
        }
        bool staged=s.stagedEnabled!=0 && isStaged(s,row);
        bool registering=f.event!=28 || staged && (d.flags&1)!=0 && s.alive[row]==0;
        if (!f64Zero(d.interval) && registering)
        {
            uint count=staged ? stagedTotal : 1;
            if (s.error!=0) break;
            if (staged && count==0) continue;
            bool previousCarrier=s.alive[row]!=0;
            registerTimer(s,row,f.time);
            if(staged && s.error==0) prepareStaged(s,row,count,f.time,previousCarrier);
            continue;
        }
        if((d.kind==0 || d.kind==4) && d.enemyBuff!=0 && recipientMask!=0 && f.mode!=19 && (countbits(recipientMask)!=1 || s.hpPendingMask!=0 || s.hpDirtyMask!=0))
        {
            pushFrame(s,frames,depth,18,f.event,d.owner,int(row),f.time,enemyOrder);
            if(s.error==0)
            {
                frames[depth].healthValue=uint64_t(s.targetGeneration[0])|(uint64_t(s.targetGeneration[1])<<32);
                frames[depth].healthPrevious=uint64_t(s.targetGeneration[2])|(uint64_t(s.targetGeneration[3])<<32);
                frames[depth].healthNext=uint64_t(s.targetGeneration[4])|(uint64_t(s.targetGeneration[5])<<32);
                frames[depth].repeatLeft=s.targetGeneration[6];frames[depth].repeatPassive=s.targetGeneration[7];
            }
            continue;
        }
        if (d.kind==35) { registerSource(s,row,f.time); continue; }
        if (d.kind == 0 || d.kind == 4)
        {
            uint sourceRow=row; uint64_t duration = d.duration; bool activationLazy = d.lazyGroup != 0;
            if(!activationLazy) { recipientMask=filterHarmful(s,d,recipientMask,recipientOrder);if(d.polarity==2 && recipientMask==0) continue; }
            uint capturedGeneration=d.enemyBuff!=0 && recipientMask!=0 ? (f.mode==19 ? f.repeatPassive : s.targetGeneration[firstbithigh(recipientMask>>5)]) : 0;
            row = findCarrier(s,row,recipientMask,f.time,capturedGeneration);
            if (s.error != 0) break;
            d = residentDefinition(s,row);
            bool live = s.alive[row] != 0;
            if (!live) { storeReferenceCapture(s,row,0,0);captureBuffReference(s,row,sourceRow); }
            if (!live) { resetBulletCarrier(s,row); discardLazy(s,row); s.stacks[row] = 0; s.hpSnapshot[row] = 0; markEntry(s,row); }
            uint previousStack = s.stacks[row];
            if (activationLazy)
            {
                if (!live) { s.lazyPending[row] = 1; s.lazyPendingCount++; s.lazyMappedPendingCount += d.queryResolve; s.activeRecipients[row] = 0; }
                else if (s.lazyPending[row] != 0) unlinkLazyCache(s,row);
            }
            else { s.activeRecipients[row] = recipientMask; s.carrierRecipientOrder[row] = recipientOrder; }
            if(!live || d.maxStack!=1) s.stacks[row] = checkedStackIncrement(s.stacks[row],d.maxStack,s.error);
            if (s.error!=0) break;
            s.alive[row] = 1; s.activated[row] = f.time;
            s.end[row] = f64Less(duration,0) ? F64_INF : f64Add(f.time,duration);
            if (d.enemyBuff != 0) s.enemyCaptureGeneration[row] = capturedGeneration;
            if (d.bulletDuration != 0) prepareBulletActivation(s,row,recipientMask,live,activationLazy,previousStack);
            bool namedCandidate = (d.buffEvent & 1) != 0 && (!live || d.maxStack != 1) && s.namedEventOwners != 0;
#ifdef PORTABLE_BUFF_AUDIENCE_SCAN_REFERENCE
            uint audienceOrder = buffAudienceOrder(s,row);
#else
            uint audienceOrder = namedCandidate ? buffAudienceOrder(s,row) : 0;
#endif
            bool namedNotice = namedCandidate && (s.namedEventOwners & packedRecipientMask(audienceOrder)) != 0;
            bool stackNotice = (d.buffEvent & 1) != 0 && previousStack != s.stacks[row] && (s.stackEventOwners & (1U << d.owner)) != 0;
            if (live && !namedNotice && !stackNotice) captureBuffReference(s,row,sourceRow);
            if (namedNotice || stackNotice || immunityPolicy(s.inputBase,sourceRow)==3)
            {
                pushFrame(s,frames,depth,13,0,d.owner,int(row),f.time,recipientOrder | ((recipientMask&~31U)<<16));
                if (s.error == 0)
                {
                    frames[depth].healthValue = audienceOrder; frames[depth].healthPrevious = previousStack;
                    frames[depth].healthNext = s.stacks[row]; frames[depth].repeatLeft = uint(live);
                    frames[depth].repeatRow = s.carrierDefinition[row]; frames[depth].repeatPassive = s.entryOrder[row]; frames[depth].cursor=sourceRow+1;
                }
            }
            else if (activationLazy) { }
            else if (s.hpWatchCount != 0 && (d.stat >= S_max_hp_pct && d.stat <= S_max_hp_only_pct || d.stat == S_max_hp_from_max_hp_pct))
            {
                uint64_t grant = prepareHealthGrant(s,row,f.time);
                pushFrame(s,frames,depth,5,0,d.owner,int(row),f.time);
                if (s.error == 0) { frames[depth].healthValue = grant; frames[depth].value = recipientOrder; }
            }
            else
            {
                applyHealthBuff(s,row,f.time);
            }
        }
        else if (d.kind == 7 || d.kind == 30)
        {
            pushFrame(s,frames,depth,11,0,d.owner,int(row),f.time);
            if (s.error == 0) frames[depth].value = recipientOrder;
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
        else if (d.kind == 13 || d.kind == 14)
        {
            applyAmmoInstant(s,d,recipientMask,f.time);
            // The percentage form emits its named completion even with no recipients.
            if (d.kind == 13 && d.target != 0 && s.error == 0)
                pushFrame(s,frames,depth,0,31,d.owner,int(d.name),f.time);
        }
        else if (d.kind >= 9 && d.kind <= 11)
        {
            ResourceDefinition r = resourceDefinition(s,row);
            if ((r.flags & 2) == 0) continue;
            uint key = r.key-1, at = d.owner*P_RESOURCE_KEYS+key;
            if ((r.flags & 1) != 0) { setResourceCap(s,at,r.cap); }
            uint64_t old = resourceValue(s,at), value = old, spent = 0;
            if (d.kind == 9)
            {
                value = f64Add(old,d.value);
                if ((resourceFlags(s,at) & 2) != 0) value = smaller(value,effectiveResourceCap(s,d.owner,key));
            }
            else
            {
                uint64_t available = larger(0,f64Add(old,r.minimum ^ F64_SIGN));
                bool all = f64Equal(d.value,F64_SIGN | ONE);
                value = all ? r.minimum : larger(r.minimum,f64Add(old,d.value ^ F64_SIGN));
                spent = all ? available : larger(0,smaller(d.value,available));
            }
            if (!f64Finite(value) || !f64Finite(spent)) { s.error = 16; break; }
            setResourceValue(s,at,value); results[resourceAddress(s,at)] |= 1;
            if (d.kind == 9 && f64Less(old,value) && results[s.resourceOutput+P_RESOURCE_STEP_HEAD_BASE+at] != 0)
            {
                pushFrame(s,frames,depth,14,0,d.owner,int(key),f.time);
                if (s.error == 0) { frames[depth].healthPrevious = old; frames[depth].healthNext = value; }
            }
            else if (d.kind == 11 && f64Less(0,spent))
            {
                uint status; uint64_t count = f64ToI64(spent,1,status);
                if (status != 0 || count > 0x7fffffff) { s.error = 2; break; }
                if (s.resourceAmmoObserved == 0 && s.traceMode != 1)
                {
                    if (count > 0x7fffffff-s.resourceTraceTotal) { s.error = 2; break; }
                    s.resourceTraceTotal += uint(count);
                }
                else if (count != 0) pushFrame(s,frames,depth,15,0,d.owner,int(key),f.time,uint(count));
            }
        }
        else if (d.kind == 25) s.pendingReentry[d.owner] = 1;
        else if (d.kind == 2)
        {
            int prior = s.modeIndex[d.owner];
            if (d.toggle != 0 && prior >= 0 && definition_name(s.inputBase,prior) == d.name)
            { clearMode(s,d.owner,f.time); pushFrame(s,frames,depth,0,29,d.owner,int(d.name),f.time); }
            else
            {
                if (prior != int(row)) { s.modeEpoch[d.owner]++; s.modeShots[d.owner] = 0; }
                s.modeIndex[d.owner] = int(row);
                s.modeEnd[d.owner] = f64Less(d.duration,0) ? FOREVER : f64Add(f.time,d.duration);
                if (d.target != 0) pushFrame(s,frames,depth,12,31,d.owner,int(d.name),f.time);
            }
        }
        else if(stackOperation(d.kind))
        {
            uint begin=s.removalCount;
            if(d.kind==18) initializeStack(s,row,f.target,f.time);
            else mutateStacks(s,row,recipientMask,f.time);
            if(s.error==0 && s.removalCount>begin) pushFrame(s,frames,depth,9,0,0,int(begin),f.time);
        }
        else if (d.kind == 15) extendNamedResidents(s,row,recipientMask,f.time);
        else if (d.kind == 1)
        {
            uint begin = s.removalCount;
            removeNamedResidents(s,row,f.target,f.time);
            if (s.removalCount > begin) pushFrame(s,frames,depth,9,0,0,int(begin),f.time);
        }
        else if (d.kind==26) cleanseResidents(s,row,recipientMask);
        else if (d.kind == 33) pushFrame(s,frames,depth,2,0,d.owner,int(row),f.time);
        else if (d.kind == 3)
        {
            if (f.event != 28) s.stacks[row] = 1;
            if (d.damagePending != 0) enqueuePendingBurst(s,row,f.time);
            else
            {
                uint64_t coefficient=activationDamageCoefficient(s,row);
                uint hits=f64Zero(coefficient) ? 0 : activationHitCount(s,row);
                if (s.error==0) pushFrame(s,frames,depth,10,0,d.owner,int(row),f.time);
                if (s.error==0) { frames[depth].repeatLeft=hits; frames[depth].healthValue=coefficient; }
            }
        }
        else s.error = 32;
#ifdef PORTABLE_HEALTH_SCAN_REFERENCE
        if((s.healthMask&32)==0) syncHealth(s,f.time);
#else
        // Reference/stack-derived HP flushes after all synchronous children.
        if (d.kind == 1 && (s.healthMask&32)==0) syncHealth(s,f.time);
#endif
    }
    s.target = entryTarget;
}

void timerPass(inout Runtime s, uint64_t when, bool damagePass, uint output)
{
    uint rows[P_DEFINITIONS], epochs[P_DEFINITIONS], count = 0;
    // Snapshot registration order AND epoch before any child is run.
    for (uint j = 0; j < s.count; j++) if (s.timerActive[j] != 0 && (definition_kind(s.inputBase,j) == 3) == damagePass)
    {
        uint at = count++;
        while (at > 0 && s.timerOrder[j] < s.timerOrder[rows[at-1]])
        { rows[at] = rows[at-1]; epochs[at] = epochs[at-1]; at--; }
        rows[at] = j; epochs[at] = s.timerEpoch[j];
    }
    for (uint pass = 0; pass < count && s.error == 0; pass++)
    {
        uint j = rows[pass]; Definition d = readDefinition(s.inputBase,j);
        if (s.timerActive[j] == 0 || s.timerEpoch[j] != epochs[pass]) continue;
        if (damagePass && (d.periodicFlags & 1) == 0 && !targetLive(s,s.timerTarget[j],s.timerGeneration[j])) { s.timerActive[j] = 0; continue; }
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
// Native staged heap ordering: deadline then unique registration sequence.
[noinline]
void stagedPass(inout Runtime s,uint64_t when,uint output)
{
    if(s.stagedEnabled==0) return;
    uint work=0;
    while(s.error==0)
    {
        uint selected=s.count,sequence=0;uint64_t due=0;
#ifdef PORTABLE_STAGED_FULL_SCAN
        for(uint slot=0;slot<s.count;slot++)
#else
        for(uint slot=0;slot<s.stagedEnabled;slot++)
#endif
        {
#ifdef PORTABLE_STAGED_FULL_SCAN
            uint row=slot;
#else
            uint row=commands[s.inputBase+P_STAGED_INDEX_BASE+1+slot];
#endif
            uint at=stagedAddress(s,row);
            if(results[at]==0 || s.alive[row]==0 || results[at+3]>=results[at+2]) continue;
            uint64_t next=stagedNext(s,row);
            if(f64Less(when,next)) continue;
            if(selected==s.count || f64Less(next,due) || f64Equal(next,due) && results[at+1]<sequence)
            { selected=row;due=next;sequence=results[at+1]; }
        }
        if(selected==s.count) break;
        if(++work>4096) { s.error=4;break; }
        uint at=stagedAddress(s,selected),index=++results[at+3];s.stacks[selected]=min(index,definition_maxStack(s.inputBase,selected));
        uint previousRow=s.stagedScopeRow,previousGen=s.stagedScopeGeneration,previousEntry=s.stagedScopeEntry,previousStack=s.stagedScopeStack;
        uint override=commands[stagedDefinition(s,selected)+6];
        s.stagedScopeRow=selected+1;s.stagedScopeGeneration=results[at];s.stagedScopeEntry=s.entryOrder[selected];s.stagedScopeStack=override==0 ? s.stacks[selected] : override-1;
        dispatch(s,1,28,definition_owner(s.inputBase,selected),int(selected),when,output);
        s.stagedScopeRow=previousRow;s.stagedScopeGeneration=previousGen;s.stagedScopeEntry=previousEntry;s.stagedScopeStack=previousStack;
    }
}
// Snapshot keys/owners, not epochs: a later existing key observes a child's
// replacement. New keys wait until the next phase. Only the current record's
// post-notify advance is guarded against replacement.
[noinline]
void sourcePass(inout Runtime s, uint64_t when, uint output)
{
    if (s.sourceEnabled==0) return;
    uint header=s.resourceOutput+P_SOURCE_HEADER_BASE, count=results[header], owners=results[header+1];
    for (uint i=0; i<owners && s.error==0; i++) for (uint slot=0; slot<count && s.error==0; slot++)
    {
        uint owner=results[header+2+i], record=sourceAddress(s,slot), row=results[record]-1;
        if (definition_owner(s.inputBase,row)!=owner || results[record+2]==0) continue;
        uint64_t due=sourceNumber(record+6); if (f64Less(when,due)) continue;
        uint population=sourceLiveCount(s,slot,when);
        if (population==0) { results[record+2]=0; continue; }
        uint epoch=results[record+1], at=sourceDescriptor(s,row);
        dispatch(s,0,commands[at+2]!=0 ? 60 : 59,owner,int(commands[at]),when,output);
        if (results[record+1]==epoch) storeNumber(record+6,f64Add(due,sourceInterval(s,row,population)));
    }
    s.sourceTime=when;
}
[noinline]
void tick(inout Runtime s, uint64_t when, uint output)
{
    s.sourceTime=when;
    if (s.hpWatchCount != 0) dispatch(s,7,0,0,0,when,output);
    stagedPass(s,when,output);
    timerPass(s,when,true,output);
    sourcePass(s,when,output);
    uint begin = s.removalCount;
    for (uint pass = 0; pass < s.orderedCount && s.error == 0; pass++)
    {
        uint slot = s.orderedRows[pass];
        if (s.alive[slot] != 0 && !f64Less(when,s.end[slot])) queueCarrierEnd(s,slot);
    }
    if (s.removalCount > begin) { syncHealth(s,when); dispatch(s,9,0,0,int(begin),when,output); }
    if (s.combat != 0) for (uint who = 0; who < 5 && s.error == 0; who++)
        if (s.modeIndex[who] >= 0 && !f64Less(when,s.modeEnd[who]))
        { uint name = definition_name(s.inputBase,s.modeIndex[who]); clearMode(s,who,when); dispatch(s,0,29,who,int(name),when,output); }
    for (uint j = 0; j < s.count && s.error == 0; j++)
        if ((s.downMask & (1U << definition_owner(s.inputBase,j))) == 0 && (definition_flags(s.inputBase,j) & 1) != 0 && activationConditions(s,j,when))
        {
            uint resident = s.carrierCount;
            for (uint pass = 0; pass < s.orderedCount; pass++)
            { uint slot = s.orderedRows[pass]; if (s.carrierDefinition[slot] == j && s.alive[slot] != 0) { resident = slot; break; } }
            if (resident == s.carrierCount) dispatch(s,1,28,definition_owner(s.inputBase,j),int(j),when,output);
            else s.end[resident] = larger(s.end[resident],f64Add(when,definition_duration(s.inputBase,j)));
        }
    for (uint j = 0; j < s.count && s.error == 0; j++)
        if (!f64Zero(definition_period(s.inputBase,j))) for (uint slot = 0; slot < definition_triggerCount(s.inputBase,j) && s.error == 0; slot++)
        {
            uint at = s.inputBase+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8;
            if (commands[at] != 6) continue;
            uint64_t interval = loadNumber(at+1), next = s.periodInitialized[j] != 0 ? s.periodDue[j] : interval;
            if (s.periodInitialized[j] != 0 && !f64Equal(interval,s.periodPrevious[j]))
                next = f64Add(when,f64Mul(larger(0,f64Add(next,when ^ F64_SIGN)),f64Div(interval,s.periodPrevious[j])));
            s.periodInitialized[j] = 1; s.periodDue[j] = next; s.periodPrevious[j] = interval;
            if (!f64Less(when,next))
            { dispatch(s,0,6,definition_owner(s.inputBase,j),int(j),when,output); s.periodDue[j] = f64Add(next,interval); }
        }
    timerPass(s,when,false,output); syncHealth(s,when); syncCovers(s,when);
    if (s.hpWatchCount != 0) dispatch(s,7,0,0,0,when,output);
}

#include "bullet_consume.slang"
#include "combat_runtime.slang"

#include "admission_runtime.slang"

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if (id.x >= commands[0]) return;
    uint input = 1 + id.x*P_INPUT_WORDS, output = id.x*P_OUTPUT_WORDS;
    #ifdef PORTABLE_AGGREGATE_INIT_REFERENCE
    Runtime s = {};
#else
    Runtime s; initializeRuntime(s);
#endif
    s.resourceOutput = output;
    s.resourceCount = commands[input+P_RESOURCE_META_BASE];
    if (s.resourceCount > P_RESOURCE_KEYS) { results[output] = 64; return; }
    s.generation = 1; s.count = commands[input+1]; s.combat = commands[input+3]; s.inputBase = input; s.traceMode = commands[input+5];
    if (commands[input] != PORTABLE_ABI || s.count == 0 || s.count > P_DEFINITIONS || commands[input+2] > P_COMMANDS || s.traceMode > 2)
    { results[output] = 64; return; }
    s.coverSync = commands[input+7];
    if (s.coverSync > 1) { results[output] = 64; return; }
    s.carrierCount = s.count;
    for (uint row = 0; row < s.count; row++) s.carrierDefinition[row] = row;
    for (uint i = 0; i < 5; i++)
    {
        s.baseAttack[i] = loadNumber(input+8+2*i);
        uint health = input+P_HEALTH_BASE+i*P_HEALTH_WORDS;
        s.baseHP[i] = loadNumber(health); s.hp[i] = loadNumber(health+2); s.baseDefense[i] = loadNumber(health+4);
        uint cover = input+P_COVER_BASE+i*4;
        s.baseCoverHP[i] = loadNumber(cover); s.coverHP[i] = loadNumber(cover+2); s.coverMaxHP[i] = s.baseCoverHP[i];
        if (!f64Finite(s.baseCoverHP[i]) || !f64Less(0,s.baseCoverHP[i]) || !f64Finite(s.coverHP[i]) || f64Less(s.coverHP[i],0) || f64Less(s.baseCoverHP[i],s.coverHP[i])) { results[output] = 64; return; }
        s.hpPct[i] = f64Mul(f64Div(s.hp[i],s.baseHP[i]),HUNDRED);
    }
    s.defense = loadNumber(input+18); s.coreBonus = loadNumber(input+22);
    s.baseCrit = loadNumber(input+24); s.baseCritDamage = loadNumber(input+26);
    if (s.combat == 0) for (uint word = 0; word < 16; word++)
        if (commands[input+P_TARGET_ATTACK_BASE+word] != 0) { results[output] = 64; return; }
    if (s.combat == 0 && commands[input+P_AIM_POLICY_BASE] != 0) { results[output] = 64; return; }
    if (s.combat != 0) initializeCombat(s,input);
    if (s.error != 0) { results[output] = s.error; return; }
    uint numericStatus; s.probability = coreProbability(loadNumber(input+20),numericStatus);
    if (numericStatus != 0) { results[output] = 128; return; }
    admitDefinitions(s,input);
    if (s.error != 0) { results[output] = s.error; return; }
    if (!validStatusDefinitions(s)) { results[output]=64;return; }
    if (!validStackDefinitions(s)) { results[output]=64;return; }
    if (!validEventCandidates(s)) { results[output] = 64; return; }
    for (uint row = 0; row < s.count; row++) if (!validPendingDefinition(s,row)) { results[output] = 64; return; }
    if (!validateDurationGroups(s)) { results[output] = 64; return; }
    if (!validatePeriodicDefinitions(s)) { results[output] = 64; return; }
    if (!initializeResources(s) || !validateReferences(s)) { results[output] = 64; return; }
    if (!initializeSources(s)) { results[output]=64; return; }
    if(!initializeStaged(s)) { results[output]=64;return; }
    if (!initializeLandings(s)) { results[output]=64;return; }
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
        else if (op == 4 && s.combat != 0) { if (s.clockMode != 0) { s.error = 64; break; } squadFrame(s,when,output); s.frameCount++; }
        else if (op == 26)
        {
            uint mask = commands[at+5]; uint64_t amount = loadNumber(at+6);
            if (commands[at+3] != 0 || commands[at+4] != 0 || mask == 0 || mask > 31 || !f64Finite(amount) || f64Less(amount,0)) { s.error = 64; break; }
            for (uint who = 0; who < 5 && s.error == 0; who++) if ((mask & ~s.downMask & (1U << who)) != 0 && !f64Zero(s.coverHP[who]) && !f64Zero(amount))
            {
                uint64_t taken = smaller(s.coverHP[who],amount);
                s.coverHP[who] = f64Add(s.coverHP[who],taken ^ F64_SIGN);
                s.coverDamage[who] = f64Add(s.coverDamage[who],taken);
                dispatch(s,0,36,who,0,when,output);
            }
        }
        else if (op==29)
        {
            uint owner=commands[at+4], name=commands[at+5], index=commands[at+6];
            if (owner>=5 || name>=P_DEFINITIONS || index>=P_COMMANDS || commands[at+3]!=0 || commands[at+7]!=0) { s.error=64; break; }
            writeSourceQuery(s,owner,name,index,when);
        }
        else if (op == 25) dispatch(s,8,0,0,int(step),when,output);
        else if (op == 24 && s.combat != 0) advanceCombat(s,when,output);
        else if ((op == 20 || op == 21 || op == 22 || op == 27) && s.combat != 0)
        {
            uint target = commands[at+5], who = commands[at+4];
            if (who >= 5 || (op == 27 ? target > 1 : target >= s.targetCount)) { s.error = 64; break; }
            if (op == 27)
            {
                uint bit = 1U << who; s.automaticAddAim = target != 0 ? s.automaticAddAim | bit : s.automaticAddAim & ~bit;
                uint aimed = aimedTarget(s,who); s.target = aimed == 0xffffffff ? 0 : aimed;
            }
            else if (op == 20) { s.automaticAddAim &= ~(1U << who); s.aim[who] = target; s.target = target; }
            else if (op == 22) s.targetAlive[target] = 0;
            else
            {
                if (s.targetGeneration[target] == 0x7fffffff) { s.error = 2; break; }
                if (s.enemyEpoch == 0x7fffffff) { s.error = 2; break; }
                s.enemyBirth[target] = ++s.enemyEpoch;
                s.enemyAttackOrder = 0; s.enemySpawnOrder = 0; // Both ranks depend on spawn order.
                s.targetGeneration[target]++; s.targetAlive[target] = 1; s.targetHP[target] = loadNumber(at+6); s.targetMaxHP[target] = s.targetHP[target]; s.targetDealt[target] = 0;
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
            if (s.landingPolicy==0) land(s,who,target,amount);
            dispatch(s,0,8,who,0,when,output);
            if (s.landingPolicy!=0) land(s,who,target,amount);
            if ((s.healthMask & 64) != 0 && s.error == 0) dispatch(s,17,0,who,0,when,output,amount);
        }
        else if (op == 30)
        {
            if (s.landingPolicy==0 || commands[at+3]!=0 || commands[at+4]!=0 || commands[at+5]!=0 || commands[at+6]!=0 || commands[at+7]!=0) { s.error=64;break; }
            drainLandings(s,when,output);
        }
        else if (op == 28)
        {
            uint who = commands[at+4], key = commands[at+5], index = commands[at+6];
            if (who >= 5 || key >= s.resourceCount || index >= P_COMMANDS || commands[at+3] != 0 || commands[at+7] != 0) { s.error = 64; break; }
            uint dst = output+P_RESOURCE_QUERY_BASE+index*12, pos = who*P_RESOURCE_KEYS+key;
            storeNumber(dst,when); results[dst+2] = who; results[dst+3] = key;
            results[dst+4] = resourceFlags(s,pos); results[dst+5] = 0;
            storeNumber(dst+6,resourceValue(s,pos)); storeNumber(dst+8,resourceCap(s,pos));
            storeNumber(dst+10,(resourceFlags(s,pos) & 2) != 0 ? effectiveResourceCap(s,who,key) : 0);
        }
        else if (op == 2)
        {
            uint index = commands[at+6];
            if (index >= P_COMMANDS) { s.error = 64; break; }
            if (s.hpWatchCount != 0) dispatch(s,7,0,0,0,when,output); else syncHealth(s,when);
            writeHealth(s,when,output+P_HEALTH_QUERY_BASE+index*P_HEALTH_QUERY_WORDS);
            writeCovers(s,when,output+P_COVER_QUERY_BASE+index*40);
            writePendingBurst(s,output+P_PENDING_QUERY_BASE+index*4,false);
            writeIncoming(s,output+P_INCOMING_QUERY_BASE+index*P_INCOMING_QUERY_WORDS);
            writeDamageAccounting(s,output+P_DAMAGE_ACCOUNTING_QUERY_BASE+index*40);
            queries = max(queries,index+1); uint dst = output+P_QUERY_BASE+index*P_QUERY_WORDS;
            storeNumber(dst,when);
            for (uint who = 0; who < 5; who++) { storeNumber(dst+2+2*who,s.total[who]); storeNumber(dst+16+2*who,readStat(s,who,0,when)); }
            uint masks[P_MASK_WORDS]; for (uint word = 0; word < P_MASK_WORDS; word++) masks[word] = 0;
            for (uint j = 0; j < s.count; j++) if (s.timerActive[j] != 0) masks[j/32] |= 1U << (j%32);
            for (uint word = 0; word < P_MASK_WORDS; word++) results[output+P_TIMER_MASK_BASE+index*P_MASK_WORDS+word] = masks[word];
            if (s.combat != 0) writeCombatQuery(s,output+P_COMBAT_QUERY_BASE+index*P_COMBAT_QUERY_WORDS,output+P_COMBAT_STATE_QUERY_BASE+index*P_COMBAT_STATE_QUERY_WORDS);
            if (int(commands[at+5]) < -1) { s.error = 64; break; }
            uint selectedEnemy = int(commands[at+5]) < 0 ? 0 : commands[at+5];
            if (s.combat != 0 && selectedEnemy >= s.targetCount) { s.error = 64; break; }
            uint64_t enemyModifiers[3]; collectEnemyModifiers(s,commands[at+4],selectedEnemy,when,enemyModifiers);
            for (uint key = 0; key < 3; key++) storeNumber(dst+26+2*key,enemyModifiers[key]);
            results[dst+12] = masks[0]; results[dst+13] = s.combat != 0 ? s.targetGeneration[s.target] : s.generation; results[dst+14] = 0; results[dst+15] = s.timerClock;
        }
        else s.error = 64;
    }
    writeDamageAccounting(s,output+P_DAMAGE_ACCOUNTING_STATE_BASE,true);
    writePendingBurst(s,output+P_PENDING_STATE_BASE,true);
    writeCovers(s,commands[input+2] > 0 ? loadNumber(input+P_COMMAND_BASE+(commands[input+2]-1)*8+1) : 0,output+P_COVER_STATE_BASE);
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
        uint periodic = output+P_PERIODIC_STATE_BASE+j*12;
        results[periodic] = definition_periodicFlags(s.inputBase,j); results[periodic+1] = definition_periodicGroup(s.inputBase,j);
        results[periodic+2] = s.periodicOrder[j]; results[periodic+3] = 0;
        for (uint target = 0; target < 8; target++) results[periodic+4+target] = s.periodicGeneration[j*8+target];
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
        results[at+3] = s.stacks[slot]; results[at+4] = s.alive[slot] | (s.lazyPending[slot] << 1) | (uint(s.bulletInitialized[slot]==2)<<2);
        storeNumber(at+5,s.end[slot]); storeNumber(at+7,s.activated[slot]); results[at+9] = s.entryOrder[slot]; storeNumber(at+10,s.hpSnapshot[slot]);
        results[at+12] = definition_enemyBuff(s.inputBase,s.carrierDefinition[slot])!=0 ? s.enemyCaptureGeneration[slot] : uint(s.bulletLeft[slot]);
        for (uint who = 0; who < 5; who++) { results[at+13+who] = s.recipientBullets[slot*5+who]; results[at+18+who] = s.recipientStacks[slot*5+who]; }
    }
    if (s.error==0 && s.sourceEnabled!=0 && commands[input+2]!=0) finishSourceCounts(s,loadNumber(input+P_COMMAND_BASE+(commands[input+2]-1)*8+1));
    results[output+P_RESOURCE_HEADER_BASE] = s.resourceTraceCount; results[output+P_RESOURCE_HEADER_BASE+1] = s.resourceTraceTotal;
    results[output+9] = s.orderedCount;
    results[output+10] = s.cacheCount; results[output+11] = s.cacheEvaluations; results[output+12] = s.cacheReuses; results[output+13] = s.lazyPendingCount; results[output+14] = s.lazyMappedPendingCount; results[output+15] = s.bulletCount;
    results[output] = s.error; results[output+1] = queries; results[output+2] = s.traceCount; results[output+3] = s.maxDepth; results[output+4] = s.burstTraceCount; results[output+6] = s.traceTotal;
    results[output+7] = s.burstTraceTotal; results[output+8] = s.frameCount;
}
