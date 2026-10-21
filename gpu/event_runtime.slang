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
    uint mode, event, owner, cursor, target, repeatRow, repeatLeft, repeatPassive;
    int argument;
    uint64_t value, time, healthValue, healthPrevious, healthNext, gaugeFlat;
};
struct Runtime
{
#ifdef PORTABLE_WORLD_TEAM
    uint teamEvent;
#endif
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
    uint64_t modeEnd[5], reentryDelay, modeEntryUntil[5];
    uint automaticAddAim, enemyAttackOrder, enemySpawnOrder, combatStarted, combat, targetCount, target, aim[5], targetAlive[8], targetGeneration[8], targetHits[8];
    uint64_t targetHP[8], targetMaxHP[8], targetDamage[8], targetDefense[8];
    uint64_t scoredDamage[5], addScoredDamage[5], addOverkill[5], targetScoredDamage[8], targetDealt[8];
    uint timerTarget[P_DEFINITIONS], periodicOrder[P_DEFINITIONS], periodicGeneration[P_DEFINITIONS*8], periodicOwner[P_DEFINITIONS];
    uint weaponEnabled[5], weaponMode[5], capacity[5], shots[5], stage[5], charging[5];
    int ammo[5]; uint reloadCancelOnFull[5], modeCapacityEpoch[5];
    uint frameAmmoActive[5], frameAmmoBase[5], infiniteRowCount, infiniteRows[P_CARRIERS];
    uint enemyBuffCount, enemyBuffRows[P_CARRIERS], enemyCaptureGeneration[P_CARRIERS], enemyEpoch, enemyBirth[8];
    uint namedEventOwners, stackEventOwners; uint phase, castMask, traceMode, traceTotal, burstTraceTotal, nextFrame, frameCount, clockMode; uint64_t frameTime;
    uint burstModifierMask, cooldownWaitMask, gaugeCharging, normalLandedMask, physicalGaugeOwner; uint64_t cooldownApplied[5], physicalGaugeGain;
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
#ifdef PORTABLE_WORLD_PROJECTILE_DIAGNOSTIC
#define PROJECTILE_DIAGNOSTIC_FIELDS(s,row,d,stage) { uint diagnostic=s.resourceOutput+786416;results[diagnostic]=0x57504144;results[diagnostic+1]=stage;results[diagnostic+2]=row+1;results[diagnostic+3]=d.kind;results[diagnostic+4]=d.stat;results[diagnostic+5]=d.quantityFlags;results[diagnostic+6]=d.owner;results[diagnostic+7]=d.triggerCount;results[diagnostic+8]=d.conditionCount;results[diagnostic+9]=d.damageFlags;results[diagnostic+10]=d.healthScaling;results[diagnostic+11]=d.alliedFlags;results[diagnostic+12]=uint(d.value);results[diagnostic+13]=uint(d.value>>32);results[diagnostic+14]=uint(d.duration);results[diagnostic+15]=uint(d.duration>>32); }
#define PROJECTILE_ADMIT_ROW(s,row,d) PROJECTILE_DIAGNOSTIC_FIELDS(s,row,d,4)
#define PROJECTILE_COUNTER_ROW(s,row,d) PROJECTILE_DIAGNOSTIC_FIELDS(s,row,d,11)
#define PROJECTILE_ADMIT_STAGE(s,value) results[s.resourceOutput+786416]=0x57504144;results[s.resourceOutput+786417]=value;
#else
#define PROJECTILE_ADMIT_ROW(s,row,d)
#define PROJECTILE_COUNTER_ROW(s,row,d)
#define PROJECTILE_ADMIT_STAGE(s,value)
#endif
#ifdef PORTABLE_WORLD_PROJECTILE
#define WORLD_PROJECTILE_INIT(s) initializeProjectiles(s);
#define WORLD_PROJECTILE_KIND(d,legacy) (d.kind==1||d.kind==9||d.kind==10 ? false : (legacy))
#define WORLD_PROJECTILE_CONDITION(s,at,kind,arg) if(kind>=C_GAUGE_ABOVE&&kind<=C_GAUGE_MOD) { if(!validProjectileResourceCondition(s,at,kind,arg)) return false;continue; }
#define WORLD_PROJECTILE_SKIP_SLOT(event,stage) if(event==26&&stage==2) continue;
#define WORLD_PROJECTILE_FRAME(s) if(s.error==0) snapshotProjectileParts(s);
#define WORLD_PROJECTILE_PARTS(s,legacy) results[s.resourceOutput+720912+3]
#define WORLD_PROJECTILE_SAMPLE(s,w,who,when) sampleProjectilePellets(s,who,when,w.pellets);if(s.error!=0) return;
#define WORLD_PROJECTILE_REACH(s,who,flags,when,legacy) projectileReach(s,who,flags,when,legacy)
#define WORLD_PROJECTILE_RECORD(s,w,who,when,amount) recordProjectileShot(s,who,w.mode,w.pellets,w.muzzles,when,amount);
#else
#define WORLD_PROJECTILE_INIT(s)
#define WORLD_PROJECTILE_KIND(d,legacy) legacy
#define WORLD_PROJECTILE_CONDITION(s,at,kind,arg)
#define WORLD_PROJECTILE_SKIP_SLOT(event,stage)
#define WORLD_PROJECTILE_FRAME(s)
#define WORLD_PROJECTILE_PARTS(s,legacy) legacy
#define WORLD_PROJECTILE_SAMPLE(s,w,who,when)
#define WORLD_PROJECTILE_REACH(s,who,flags,when,legacy) legacy
#define WORLD_PROJECTILE_RECORD(s,w,who,when,amount)
#endif
#ifdef PORTABLE_WORLD_ROSTER
// Diagnostic omission is explicit; never skip accumulation or dispatch.
#define WORLD_ROSTER_TRACE_BEGIN(s,head,count,limit,slot) if(count>=limit) results[head+slot]++;else {
#define WORLD_ROSTER_TRACE_END }
#else
#define WORLD_ROSTER_TRACE_BEGIN(s,head,count,limit,slot) if(count>=limit) { s.error=64;return; }
#define WORLD_ROSTER_TRACE_END
#endif
#ifdef PORTABLE_WORLD_RELOAD
#define WORLD_RELOAD_FORCE_KIND(kind) (kind==23)
#define WORLD_RELOAD_KIND(d,legacy) (d.kind==23||d.kind==13||d.kind==14 ? false : (legacy))
#define WORLD_RELOAD_ORIGIN(input,row,legacy) ((legacy)||definition_kind(input,row)==23||definition_kind(input,row)==13||definition_kind(input,row)==14||definition_stat(input,row)==S_reload_time_fixed)
#define WORLD_RELOAD_INIT(s) initializeWorldReload(s); WORLD_PROJECTILE_INIT(s)
#define WORLD_RELOAD_DURATION(s,w,who,when) uint64_t reloadFixed;if(fixedReloadDuration(s,who,when,reloadFixed)) return reloadFixed;
#define WORLD_RELOAD_RECORD(s,who,when,kind) recordWorldReload(s,who,when,kind);
#define WORLD_RELOAD_ACTIVE(s,who,legacy) f64Less(0,s.reloadUntil[who])
#define WORLD_RELOAD_PHASE_EXPIRE(s,who) (!f64Less(0,s.reloadUntil[who]))
#define WORLD_RELOAD_AFTER_COMPLETE(s,who) if(f64Less(0,s.reloadUntil[who])) return;
#define WORLD_RELOAD_ACTIVATE(s,d,when) if(d.kind==23) recordForcedReload(s,d,when);
#define WORLD_RELOAD_DISPATCH(s,d,order,when) else if(d.kind==23) applyForcedReload(s,order,when);
#define WORLD_RELOAD_ORDERED(s,d,member,when) else if(d.kind==23) applyForcedReload(s,uint64_t(member+1),when);
#define WORLD_RELOAD_FINAL(s) for(uint reloadWho=0;reloadWho<5;reloadWho++) storeNumber(s.resourceOutput+P_WORLD_RELOAD_HEAD_BASE+4+reloadWho*2,s.reloadUntil[reloadWho]);
#else
#define WORLD_RELOAD_FORCE_KIND(kind) false
#define WORLD_RELOAD_KIND(d,legacy) legacy
#define WORLD_RELOAD_ORIGIN(input,row,legacy) legacy
#define WORLD_RELOAD_INIT(s)
#define WORLD_RELOAD_DURATION(s,w,who,when)
#define WORLD_RELOAD_RECORD(s,who,when,kind)
#define WORLD_RELOAD_ACTIVE(s,who,legacy) legacy
#define WORLD_RELOAD_PHASE_EXPIRE(s,who) true
#define WORLD_RELOAD_AFTER_COMPLETE(s,who)
#define WORLD_RELOAD_ACTIVATE(s,d,when)
#define WORLD_RELOAD_DISPATCH(s,d,order,when)
#define WORLD_RELOAD_ORDERED(s,d,member,when)
#define WORLD_RELOAD_FINAL(s)
#endif
#ifdef PORTABLE_WORLD_CHARGE_CONTROL
#ifdef PORTABLE_WORLD_PROJECTILE
#define WORLD_CONTROL_WIRE_MODE 24
#elif defined(PORTABLE_WORLD_ROSTER)
#define WORLD_CONTROL_WIRE_MODE 23
#elif defined(PORTABLE_WORLD_RELOAD)
#define WORLD_CONTROL_WIRE_MODE 22
#else
#define WORLD_CONTROL_WIRE_MODE 21
#endif
#ifdef PORTABLE_WORLD_ROSTER
// Admit proven shared scalar health/cooldown operators and ordinary conditions.
#define WORLD_CONTROL_ORIGIN(input,row,legacy) true
#else
#define WORLD_CONTROL_ORIGIN(input,row,legacy) WORLD_RELOAD_ORIGIN(input,row,((legacy)||controlDefinition(input,row)))
#endif
#define WORLD_CONTROL_AMMO(input,row,kind) ((kind==13||kind==14)&&controlDefinition(input,row))
#define WORLD_CONTROL_CONDITION_KIND(kind,legacy) ((kind==C_CHARGING)||(legacy))
#define WORLD_CONTROL_CONDITION_VALID(at,kind,arg,legacy) (kind==C_CHARGING ? commands[at+1]==0&&f64Zero(arg) : (legacy))
#define WORLD_CONTROL_NAMED(event,legacy) ((event==39)||(legacy))
#define WORLD_CONTROL_INIT(s) initializeChargeControl(s);
#define WORLD_CONTROL_TICK(s,who,when,output) advanceChargeControl(s,who,when);
#define WORLD_CONTROL_ARBITRATE(s,when,output) arbitrateChargeControl(s,when);
#define WORLD_CONTROL_CAMERA(s,legacy) results[s.resourceOutput+P_WORLD_CONTROL_HEAD_BASE+3]
#define WORLD_CONTROL_GAIN(s,w,who) if(w.mode==1) w.gaugeMultiplier=(results[s.resourceOutput+P_WORLD_CONTROL_HEAD_BASE+3]&(1U<<who))!=0?w.fullChargeMult:ONE;
#define WORLD_CONTROL_WAIT(s,who,charge,when) if(waitChargeControl(s,who,charge,when)) return;
#define WORLD_CONTROL_START(s,who,charge,when) startChargeControl(s,who,charge,when);
#define WORLD_CONTROL_READY(s,who,when,output) if(readyChargeControl(s,who,when,output)) return;
#define WORLD_CONTROL_HEAVY(s,who,legacy) (f64Less(actorNumber(controlState(s,who)+6),0) ? (legacy) : false)
#define WORLD_CONTROL_FINISH(s,who) if(w.mode==1&&!changedWeaponSession(s,who,epoch,mode)) finishChargeControl(s,who);
#define WORLD_CONTROL_CANCEL(s,who) cancelChargeControl(s,who,false);
#define WORLD_CONTROL_RELOAD(s,who) cancelChargeControl(s,who,true);
#define WORLD_CONTROL_CYCLE(s) for(uint controlStage=0;controlStage<3;controlStage++) results[s.resourceOutput+P_WORLD_CONTROL_HEAD_BASE+10+controlStage]=0;
#define WORLD_CONTROL_CAST(s,stage,who) results[s.resourceOutput+P_WORLD_CONTROL_HEAD_BASE+9+stage]|=1U<<who;
#else
#define WORLD_CONTROL_WIRE_MODE 19
#define WORLD_CONTROL_ORIGIN(input,row,legacy) legacy
#define WORLD_CONTROL_AMMO(input,row,kind) false
#define WORLD_CONTROL_CONDITION_KIND(kind,legacy) legacy
#define WORLD_CONTROL_CONDITION_VALID(at,kind,arg,legacy) legacy
#define WORLD_CONTROL_NAMED(event,legacy) legacy
#define WORLD_CONTROL_INIT(s)
#define WORLD_CONTROL_TICK(s,who,when,output)
#define WORLD_CONTROL_ARBITRATE(s,when,output)
#define WORLD_CONTROL_CAMERA(s,legacy) legacy
#define WORLD_CONTROL_GAIN(s,w,who)
#define WORLD_CONTROL_WAIT(s,who,charge,when)
#define WORLD_CONTROL_START(s,who,charge,when)
#define WORLD_CONTROL_READY(s,who,when,output)
#define WORLD_CONTROL_HEAVY(s,who,legacy) legacy
#define WORLD_CONTROL_FINISH(s,who)
#define WORLD_CONTROL_CANCEL(s,who)
#define WORLD_CONTROL_RELOAD(s,who)
#define WORLD_CONTROL_CYCLE(s)
#define WORLD_CONTROL_CAST(s,stage,who)
#endif
#ifdef PORTABLE_WORLD_TEAM
// This private ABI admits only mode19; portableEvents validates its marker first.
bool worldTeamEnabled(inout Runtime s) { return true; }
#define WORLD_TEAM_INPUT(input,output) if(commands[input+P_TARGET_COUNTER_INPUT_BASE]!=0x57433031||commands[input+P_TARGET_COUNTER_INPUT_BASE+6]!=WORLD_CONTROL_WIRE_MODE) { results[output]=64;return; }
#define WORLD_TEAM_MODE(s) worldTeamEnabled(s)
#define WORLD_TEAM_INIT(s) initializeWorldTeam(s);
#define WORLD_TEAM_BUDGET(s,row) teamBudgetRow(s.inputBase,row)
#define WORLD_TEAM_OWNER(s,row,runtime,legacy) teamConditionOwner(s.inputBase,row,runtime,s.teamEvent,legacy)
#define WORLD_TEAM_TARGET(s,row,runtime,name,when,present,legacy) (teamActivationContext(s.inputBase,row,runtime,s.teamEvent) ? teamConditionTarget(s,row,name,present) : (legacy))
#define WORLD_TEAM_STUN_TARGET(s,row,runtime,legacy) (teamActivationContext(s.inputBase,row,runtime,s.teamEvent) ? 5U+actorFieldLogicalSlot(s,actorPhysicalTarget(s,teamBindingOwner(s.inputBase,row)-1,0)) : (legacy))
#define WORLD_TEAM_COUNTER(s,event,counter) ((worldTeamEnabled(s)&&(event==44||event==45)) ? results[s.resourceOutput+P_WORLD_TEAM_HEAD_BASE+2+event-44] : ++s.counters[counter])
#define WORLD_TEAM_FRAME(s,f) if(worldTeamEnabled(s)) s.teamEvent=f.mode==0&&(f.event==44||f.event==45) ? f.event : 0;
#define WORLD_TEAM_BEGIN(s) uint savedTeamEvent=worldTeamEnabled(s)?s.teamEvent:0;
#define WORLD_TEAM_END(s) if(worldTeamEnabled(s)) s.teamEvent=savedTeamEvent;
#define WORLD_TEAM_GUARD(s,row,f) if(worldTeamEnabled(s)&&(f.event==44||f.event==45)&&teamBindingOwner(s.inputBase,row)!=0&&(s.downMask&(1U<<(teamBindingOwner(s.inputBase,row)-1)))!=0) continue;
#define WORLD_TEAM_PELLET(s,w,who,when,output) if(worldTeamEnabled(s)&&w.mode!=1) notifyWorldTeam(s,who,when,output);
#define WORLD_TEAM_CHARGE(s,w,who,count,when,output) if(worldTeamEnabled(s)&&w.mode==1) for(uint teamHit=0;teamHit<count;teamHit++) notifyWorldTeam(s,who,when,output);
#define WORLD_TEAM_VALIDATE(s,d,input,j) for(uint teamSlot=0;teamSlot<d.triggerCount;teamSlot++) { uint teamEvent=commands[input+P_EVENT_BASE+j*P_EVENT_WORDS+teamSlot*8];if((teamEvent==44||teamEvent==45)&&!worldTeamEnabled(s)) { s.error=64;break; } } if(s.error!=0) break;
#define WORLD_TEAM_KIND(s,d,legacy) (worldTeamEnabled(s)&&(d.kind==25||d.kind==22) ? false : WORLD_PROJECTILE_KIND(d,WORLD_RELOAD_KIND(d,(worldTeamEnabled(s)&&WORLD_CONTROL_ORIGIN(s.inputBase,row,teamBindingOwner(s.inputBase,row)!=0)&&(d.kind==5||d.kind==6||d.kind==7||d.kind==8||WORLD_CONTROL_AMMO(s.inputBase,row,d.kind)) ? false : (legacy)))))
#define WORLD_TEAM_CONDITION(s,d,at,kind,arg) WORLD_PROJECTILE_CONDITION(s,at,kind,arg) if(worldTeamEnabled(s)&&WORLD_CONTROL_ORIGIN(s.inputBase,row,teamBindingOwner(s.inputBase,row)!=0)&&WORLD_CONTROL_CONDITION_KIND(kind,teamAdditionalCondition(kind))) { if(!WORLD_CONTROL_CONDITION_VALID(at,kind,arg,validTeamAdditionalCondition(at,kind,arg))) return false;continue; }
#else
#define WORLD_TEAM_INPUT(input,output)
#define WORLD_TEAM_MODE(s) false
#define WORLD_TEAM_INIT(s)
#define WORLD_TEAM_BUDGET(s,row) row
#define WORLD_TEAM_OWNER(s,row,runtime,legacy) legacy
#define WORLD_TEAM_TARGET(s,row,runtime,name,when,present,legacy) legacy
#define WORLD_TEAM_STUN_TARGET(s,row,runtime,legacy) legacy
#define WORLD_TEAM_COUNTER(s,event,counter) ++s.counters[counter]
#define WORLD_TEAM_FRAME(s,f)
#define WORLD_TEAM_BEGIN(s)
#define WORLD_TEAM_END(s)
#define WORLD_TEAM_GUARD(s,row,f)
#define WORLD_TEAM_PELLET(s,w,who,when,output)
#define WORLD_TEAM_CHARGE(s,w,who,count,when,output)
#define WORLD_TEAM_VALIDATE(s,d,input,j)
#define WORLD_TEAM_KIND(s,d,legacy) legacy
#define WORLD_TEAM_CONDITION(s,d,at,kind,arg)
#endif
#ifdef PORTABLE_WORLD_FRACTION
bool worldFractionEnabled(inout Runtime s) { return targetCountersEnabled(s)&&commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE+6]==17||WORLD_TEAM_MODE(s); }
#define WORLD_FRACTION_MODE(s) worldFractionEnabled(s)
#define WORLD_FRACTION_POST_DELAY(s,who,mode,legacy) (worldFractionEnabled(s) ? loadNumber(mode>=0 ? s.inputBase+P_MODE_BASE+uint(mode)*P_MODE_WORDS+18 : s.inputBase+P_WORLD_FRACTION_CLOCK_BASE+4+who*2) : (legacy))
#define WORLD_FRACTION_INIT(s) initializeWorldFraction(s);
#define WORLD_FRACTION_SAMPLE(s,who,critical,core,physical,flags) if(worldFractionEnabled(s)&&physical&&(flags&H_PART)==0) sampleWorldFraction(s,who,critical,core);
#define WORLD_FRACTION_AUTO(s,w,who,when,output) if(worldFractionEnabled(s)&&w.mode!=1) { notifyWorldFraction(s,who,0,when,output);notifyWorldFraction(s,who,1,when,output); }
#define WORLD_FRACTION_CHARGE(s,w,who,count,when,output) if(worldFractionEnabled(s)&&w.mode==1) for(uint fractionKind=0;fractionKind<2;fractionKind++) for(uint fractionHit=0;fractionHit<count;fractionHit++) notifyWorldFraction(s,who,fractionKind,when,output);
#define WORLD_FRACTION_VALIDATE(s,d,input,j) for(uint fractionSlot=0;fractionSlot<d.triggerCount;fractionSlot++) { uint fractionAt=input+P_EVENT_BASE+j*P_EVENT_WORDS+fractionSlot*8; if((commands[fractionAt]==22||commands[fractionAt]==23)&&!worldFractionEnabled(s)) { s.error=64;break; } } if(s.error!=0) break;
#else
#define WORLD_FRACTION_MODE(s) false
#define WORLD_FRACTION_POST_DELAY(s,who,mode,legacy) legacy
#define WORLD_FRACTION_INIT(s)
#define WORLD_FRACTION_SAMPLE(s,who,critical,core,physical,flags)
#define WORLD_FRACTION_AUTO(s,w,who,when,output)
#define WORLD_FRACTION_CHARGE(s,w,who,count,when,output)
#define WORLD_FRACTION_VALIDATE(s,d,input,j)
#endif
#ifdef PORTABLE_WORLD_INITIAL_SPAWN
bool worldInitialSpawnEnabled(inout Runtime s) { return targetCountersEnabled(s)&&commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE+6]==15||WORLD_FRACTION_MODE(s); }
#define WORLD_INITIAL_SPAWN_MODE(s) worldInitialSpawnEnabled(s)
#define WORLD_INITIAL_SPAWN_INIT(s) initializeWorldSpawn(s);
#define WORLD_INITIAL_SPAWN_START(s,when,output) if(worldInitialSpawnEnabled(s)) { results[s.resourceOutput+P_WORLD_SPAWN_HEAD_BASE+2]++;teamNotify(s,5,when,output); }
#define WORLD_INITIAL_SPAWN_OBSERVE(s,mode,event,owner,when) if(worldInitialSpawnEnabled(s)&&mode==0&&event==5) recordWorldSpawn(s,owner,when);
#define WORLD_INITIAL_SPAWN_ADMIT(s,at) if(commands[at]==5&&!worldInitialSpawnEnabled(s)) { s.error=64;break; }
#define WORLD_INITIAL_SPAWN_VALIDATE(s,d,input,j) for(uint spawnSlot=0;spawnSlot<d.triggerCount;spawnSlot++) { uint spawnAt=input+P_EVENT_BASE+j*P_EVENT_WORDS+spawnSlot*8; WORLD_INITIAL_SPAWN_ADMIT(s,spawnAt) } if(s.error!=0) break;
#else
#define WORLD_INITIAL_SPAWN_MODE(s) false
#define WORLD_INITIAL_SPAWN_INIT(s)
#define WORLD_INITIAL_SPAWN_START(s,when,output)
#define WORLD_INITIAL_SPAWN_OBSERVE(s,mode,event,owner,when)
#define WORLD_INITIAL_SPAWN_ADMIT(s,at)
#define WORLD_INITIAL_SPAWN_VALIDATE(s,d,input,j)
#endif
#ifdef PORTABLE_WORLD_ENEMY_ATTACK
bool worldEnemyAttackEnabled(inout Runtime s) { return targetCountersEnabled(s)&&commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE+6]==13||WORLD_INITIAL_SPAWN_MODE(s); }
#define WORLD_ENEMY_ATTACK_INVALID(s,d,legacy) ((legacy)&&!(worldEnemyAttackEnabled(s)&&(d.stat==S_atk_pct||d.stat==S_atk_caster_based_pct)))
#define WORLD_ENEMY_ATTACK_ADMIT(s,d,at,kind,arg) if(worldEnemyAttackEnabled(s)&&d.enemyBuff!=0&&(d.stat==S_atk_pct||d.stat==S_atk_caster_based_pct)&&(kind==C_HP_ABOVE||kind==C_HP_BELOW||kind==C_HP_MAX)) { if(commands[at+1]!=0||!f64Finite(arg)||kind==C_HP_MAX&&!f64Zero(arg)) return false;continue; }
#define WORLD_ENEMY_ATTACK_DAMAGE_MEMBER(s,row,who,when,legacy) ((legacy)||worldEnemyAttackDamageMember(s,row,who,when))
#define WORLD_ENEMY_ATTACK_STAT(s,d,legacy) ((legacy)||(worldEnemyAttackEnabled(s)&&(d.stat==S_atk_pct||d.stat==S_atk_caster_based_pct)))
#define WORLD_ENEMY_ATTACK_CAPTURE(s,frames,depth,f) if(f.mode==8&&f.cursor==0&&scheduledArgument(uint(f.argument))&&worldEnemyAttackEnabled(s)) frames[depth].gaugeFlat=larger(0,f64Add(loadNumber(incomingDamageAddress(s,uint(f.argument))),collectWorldEnemyAttackFlat(s,0,f.time)));
#define WORLD_ENEMY_ATTACK_VALUE(s,frames,depth,f,legacy) (worldEnemyAttackEnabled(s)&&scheduledArgument(uint(f.argument)) ? frames[depth].gaugeFlat : (legacy))
#define WORLD_ENEMY_ATTACK_SNAPSHOT(s,when) if(worldEnemyAttackEnabled(s)) for(uint slot=0;slot<actorPoolCount(s);slot++) storeNumber(s.resourceOutput+P_WORLD_ENEMY_ATTACK_BASE+slot*2,collectWorldEnemyAttackFlat(s,slot==0?0:ACTOR_REF|slot,when));
#define WORLD_ENEMY_ATTACK_SKIP(d) if(d.stat==S_atk_pct||d.stat==S_atk_caster_based_pct) continue;
#define WORLD_ENEMY_ATTACK_MODE(s) worldEnemyAttackEnabled(s)
#else
#define WORLD_ENEMY_ATTACK_INVALID(s,d,legacy) legacy
#define WORLD_ENEMY_ATTACK_ADMIT(s,d,at,kind,arg)
#define WORLD_ENEMY_ATTACK_DAMAGE_MEMBER(s,row,who,when,legacy) legacy
#define WORLD_ENEMY_ATTACK_STAT(s,d,legacy) legacy
#define WORLD_ENEMY_ATTACK_CAPTURE(s,frames,depth,f)
#define WORLD_ENEMY_ATTACK_VALUE(s,frames,depth,f,legacy) legacy
#define WORLD_ENEMY_ATTACK_SNAPSHOT(s,when)
#define WORLD_ENEMY_ATTACK_SKIP(d)
#define WORLD_ENEMY_ATTACK_MODE(s) false
#endif
#ifdef PORTABLE_WORLD_PERIODIC
#define WORLD_PERIODIC_ENABLED(s) (targetCountersEnabled(s)&&commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE+6]==11||WORLD_ENEMY_ATTACK_MODE(s))
#define WORLD_PERIODIC_RETAINED(s,d,legacy) ((legacy)||worldPeriodicClock(s,d))
#define WORLD_PERIODIC_MASK(s,row,packed,legacy) if(worldPeriodicClock(s,readDefinition(s.inputBase,row))) { packed=0;return worldPeriodicAnyLive(s,row)?0xffffffffU:0; } legacy
#define WORLD_PERIODIC_CAPTURE(s,row,source,append,a,b,c) if(worldPeriodicClock(s,readDefinition(s.inputBase,row))) { captureWorldPeriodicDefinition(s,row,source,append);return; } a,b,c
#define WORLD_PERIODIC_STATUS(s,d,legacy) ((legacy)&&!worldPeriodicClock(s,d))
#define WORLD_PERIODIC_VALID(s,r,legacy) ((legacy)||(worldPeriodicClock(s,readDefinition(s.inputBase,r.row))&&r.mask==0))
#define WORLD_PERIODIC_STORE(s,at,r) storeWorldPeriodicPacket(s,at,r);
#define WORLD_PERIODIC_LOAD(r,at) r.target=results[at+7];
#define WORLD_PERIODIC_CAPTURE_PACKET(s,r,index,legacy) if(worldPeriodicClock(s,readDefinition(s.inputBase,r.row))) captureWorldPeriodicPacket(s,r,index);else legacy
#define WORLD_PERIODIC_FAMILY(s,d,legacy) (worldPeriodicClock(s,d)&&(d.damageFlags&H_DOT)!=0&&d.damageNormal==0?2U:(legacy))
#define WORLD_PERIODIC_INIT(s) initializeWorldPeriodic(s);
#define WORLD_PERIODIC_NAMED(s,row,target,count,present,name) if(s.alive[row]!=0&&int(definition_name(s.inputBase,s.carrierDefinition[row]))==name&&worldPeriodicNamedMember(s,row,target)) { present=true;count=larger(count,carrierStackValue(s,row));continue; }
#else
#define WORLD_PERIODIC_ENABLED(s) false
#define WORLD_PERIODIC_RETAINED(s,d,legacy) legacy
#define WORLD_PERIODIC_MASK(s,row,packed,legacy) legacy
#define WORLD_PERIODIC_CAPTURE(s,row,source,append,a,b,c) a,b,c
#define WORLD_PERIODIC_STATUS(s,d,legacy) legacy
#define WORLD_PERIODIC_VALID(s,r,legacy) legacy
#define WORLD_PERIODIC_STORE(s,at,r)
#define WORLD_PERIODIC_LOAD(r,at)
#define WORLD_PERIODIC_CAPTURE_PACKET(s,r,index,legacy) legacy
#define WORLD_PERIODIC_FAMILY(s,d,legacy) legacy
#define WORLD_PERIODIC_INIT(s)
#define WORLD_PERIODIC_NAMED(s,row,target,count,present,name)
#endif
bool worldPeriodicEnabled(inout Runtime s) { return WORLD_PERIODIC_ENABLED(s); }
#ifdef PORTABLE_WORLD_PENDING_SKILLS
#define WORLD_PENDING_ENABLED(s) (targetCountersEnabled(s)&&commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE+6]==9||worldPeriodicEnabled(s))
#define WORLD_PENDING_KIND(s,d) (worldPendingEnabled(s)&&(d.kind==24||d.kind==9))
#define WORLD_PENDING_SCOPE_BEGIN(s) uint pendingQueryScope=0;if(worldPendingEnabled(s)) pendingQueryScope=actorStatePushQuery(s,0);
#define WORLD_PENDING_SCOPE_END(s) if(worldPendingEnabled(s)) actorStatePopQuery(s,pendingQueryScope);
#define WORLD_PENDING_LAND(s,d,row,index,hit,when,output) if(worldPendingEnabled(s)) { landWorldPending(s,d,row,index,hit,when,output);continue; }
#else
#define WORLD_PENDING_ENABLED(s) false
#define WORLD_PENDING_KIND(s,d) false
#define WORLD_PENDING_SCOPE_BEGIN(s)
#define WORLD_PENDING_SCOPE_END(s)
#define WORLD_PENDING_LAND(s,d,row,index,hit,when,output)
#endif
bool worldPendingEnabled(inout Runtime s) { return WORLD_PENDING_ENABLED(s); }
#ifdef PORTABLE_WORLD_SKILLS
#define WORLD_SKILL_FIELDS(s,legacy) ((legacy)||worldSkillsEnabled(s))
#define WORLD_SKILL_KIND(s,d,legacy) WORLD_TEAM_KIND(s,d,((legacy)&&!(worldSkillsEnabled(s)&&d.kind==3)&&!WORLD_PENDING_KIND(s,d)))
#define WORLD_SKILL_DEFINITION(s,row,d,legacy) WORLD_TEAM_KIND(s,d,(worldSkillsEnabled(s)&&d.kind==3 ? !validWorldSkillDefinition(s,row,d) : WORLD_PENDING_KIND(s,d) ? false : (legacy)))
#define WORLD_SKILL_INHERITS(s,event,legacy) ((legacy)||(worldSkillsEnabled(s)&&event==49))
#define WORLD_SKILL_BASIS(s,legacy) (worldSkillsEnabled(s) ? 0U : (legacy))
#define WORLD_SKILL_SCOPE_BEGIN(s) uint skillQueryScope=0;if(worldSkillsEnabled(s)) skillQueryScope=actorStatePushQuery(s,0);
#define WORLD_SKILL_SCOPE_END(s) if(worldSkillsEnabled(s)) actorStatePopQuery(s,skillQueryScope);
#define WORLD_SKILL_RECEIPT_VALID(s,r,legacy) validWorldSkillReceipt(s,r,legacy)
#define WORLD_SKILL_RECEIPT_STORE(s,at,r) storeWorldSkillReceipt(s,at,r)
#define WORLD_SKILL_DRAIN(s,when,output,legacy) if(worldSkillsEnabled(s)) { drainWorldSkills(s,when,output);return; } legacy
#define WORLD_SKILL_FINAL(s,when,output) if(worldSkillsEnabled(s)&&f64Equal(when,loadNumber(s.inputBase+P_WORLD_FRAME_INPUT_BASE+6))) drainLandings(s,when,output);
#define WORLD_SKILL_FAMILY(s,legacy) (worldSkillsEnabled(s) ? results[counterHead(s)+11] : (legacy))
#define WORLD_SKILL_INIT(s) initializeWorldSkills(s);
#define WORLD_SKILL_EMPTY_COUNTERS(s,legacy) ((legacy)&&!worldSkillsEnabled(s))
#else
#define WORLD_SKILL_FIELDS(s,legacy) legacy
#define WORLD_SKILL_KIND(s,d,legacy) legacy
#define WORLD_SKILL_DEFINITION(s,row,d,legacy) legacy
#define WORLD_SKILL_INHERITS(s,event,legacy) legacy
#define WORLD_SKILL_BASIS(s,legacy) legacy
#define WORLD_SKILL_SCOPE_BEGIN(s)
#define WORLD_SKILL_SCOPE_END(s)
#define WORLD_SKILL_RECEIPT_VALID(s,r,legacy) legacy
#define WORLD_SKILL_RECEIPT_STORE(s,at,r) storeLandingReceipt(at,r)
#define WORLD_SKILL_DRAIN(s,when,output,legacy) legacy
#define WORLD_SKILL_FINAL(s,when,output)
#define WORLD_SKILL_FAMILY(s,legacy) legacy
#define WORLD_SKILL_INIT(s)
#define WORLD_SKILL_EMPTY_COUNTERS(s,legacy) legacy
#endif
#ifdef PORTABLE_COUNTER_FIELDS
#define COUNTER_FIELDS_CONTEXT(s,legacy) ((legacy)||counterFieldsEnabled(s))
#define COUNTER_FIELDS_DEFINITION(s,row,d,legacy) counterFieldDefinitionInvalid(s,row,d,legacy)
#define COUNTER_FIELDS_FIRST(s,route,legacy) counterFieldFirst(s,route,legacy)
#define COUNTER_FIELDS_WORK_LIMIT(s,legacy) (counterFieldsEnabled(s) ? P_CARRIERS*P_DEPTH : (legacy))
#define COUNTER_FIELDS_WORK_RECORD(s,work) recordCounterFieldWork(s,work);
#define COUNTER_FIELDS_WORK_INIT(s) initializeCounterFieldWork(s);
#else
#define COUNTER_FIELDS_CONTEXT(s,legacy) legacy
#define COUNTER_FIELDS_DEFINITION(s,row,d,legacy) legacy
#define COUNTER_FIELDS_FIRST(s,route,legacy) legacy
#define COUNTER_FIELDS_WORK_LIMIT(s,legacy) legacy
#define COUNTER_FIELDS_WORK_RECORD(s,work)
#define COUNTER_FIELDS_WORK_INIT(s)
#endif
#ifdef PORTABLE_COUNTER_CONTEXT
#define COUNTER_CONTEXT_MODE(s,legacy) ((legacy)||counterContextEnabled(s))
#define COUNTER_CONTEXT_CONDITIONS(s,row,d,legacy) ((legacy)&&!counterContextEnabled(s))
#define COUNTER_CONTEXT_BEGIN(s) if(!beginCounterContext(s)) return;
#define COUNTER_CONTEXT_PUSH(s,depth,mode,event) pushCounterContext(s,uint(depth),mode,event);
#define COUNTER_CONTEXT_READY(s,depth,src) setCounterCompletionContext(s,uint(depth),src);
#define COUNTER_CONTEXT_SAMPLE(s,depth) sampleCounterContext(s,uint(depth));
#define COUNTER_CONTEXT_END(s) endCounterContext(s);
#define COUNTER_CONTEXT_ADD(s,legacy) counterContextAdd(s,legacy)
#define COUNTER_CONTEXT_TARGET(s,legacy) counterContextTarget(s,legacy)
#define COUNTER_CONTEXT_INIT(s) if(counterContextEnabled(s)) for(uint i=0;i<1096;i++) results[counterContextHead(s)+i]=0;
#else
#define COUNTER_CONTEXT_MODE(s,legacy) legacy
#define COUNTER_CONTEXT_CONDITIONS(s,row,d,legacy) legacy
#define COUNTER_CONTEXT_BEGIN(s)
#define COUNTER_CONTEXT_PUSH(s,depth,mode,event)
#define COUNTER_CONTEXT_READY(s,depth,src)
#define COUNTER_CONTEXT_SAMPLE(s,depth)
#define COUNTER_CONTEXT_END(s)
#define COUNTER_CONTEXT_ADD(s,legacy) legacy
#define COUNTER_CONTEXT_TARGET(s,legacy) legacy
#define COUNTER_CONTEXT_INIT(s)
#endif
#ifdef PORTABLE_COUNTER_LANDINGS
#define COUNTER_PACKET_WORD(at,legacy) counterPacketWord(at)
#define COUNTER_PACKET_NUMBER(at,legacy) counterPacketNumber(at)
#define COUNTER_MODE_INVALID(s,base,legacy) ((legacy)&&!counterLandingsEnabled(s))
#define COUNTER_FIELD_KIND(s,d,legacy) (counterLandingsEnabled(s)&&d.kind==8 ? false : (legacy))
#define COUNTER_DEFINITION_INVALID(s,row,d,legacy) counterLandingDefinitionInvalid(s,row,d,legacy)
#define COUNTER_PART_INPUT(s,base,step) if(counterLandingsEnabled(s)) { if(!validCounterLandingInput(s,base,step)) return false;continue; }
#define COUNTER_SHOT(s,who,w,coefficient,when) sampleCounterPartShot(s,who,f64Div(coefficient,f64FromI64(w.pellets)),WORLD_PACKET_NORMAL(s,who),w.coreBonus,WORLD_PACKET_FLAGS(s,who,(w.mode==1 ? H_CHARGE|((s.attackContext[who]&4)!=0 ? H_EXPLOSION : 0) : 0)),w.fullChargeMult,w.optimal!=0,when);
#define COUNTER_CAPTURE(s,who,target) uint counterLandingTarget=actorPhysicalTarget(s,who,target);
#define COUNTER_TARGET(s,legacy) (counterLandingsEnabled(s) ? counterLandingTarget : (legacy))
#define COUNTER_IMPACT(s,who,amount,when,output) if(counterLandingsEnabled(s)&&s.error==0) publishCounterLanding(s,who,counterLandingTarget,amount,when,output);
#define COUNTER_PARTS(s,who,when,output) if(counterLandingsEnabled(s)&&s.error==0) deliverCounterParts(s,who,counterLandingTarget,when,output);
#define COUNTER_PART_CORE(s,flags,legacy) (counterLandingsEnabled(s)&&(flags&H_PART)!=0 ? uint64_t(0) : (legacy))
#define COUNTER_PART_DIRECT(s,kind,legacy) (counterExtraPart(s,kind) ? false : (legacy))
#define COUNTER_PART_DEALT(s,kind,d,p,legacy) (counterExtraPart(s,kind)&&f64Zero(loadNumber(d+2)) ? actorNumber(p+4) : (legacy))
#define COUNTER_EXTRA_RESET(s,slot) resetCounterPartExtra(s,slot);
#else
#define COUNTER_PACKET_WORD(at,legacy) legacy
#define COUNTER_PACKET_NUMBER(at,legacy) legacy
#define COUNTER_MODE_INVALID(s,base,legacy) legacy
#define COUNTER_FIELD_KIND(s,d,legacy) legacy
#define COUNTER_DEFINITION_INVALID(s,row,d,legacy) legacy
#define COUNTER_PART_INPUT(s,base,step)
#define COUNTER_SHOT(s,who,w,coefficient,when)
#define COUNTER_CAPTURE(s,who,target)
#define COUNTER_TARGET(s,legacy) legacy
#define COUNTER_IMPACT(s,who,amount,when,output)
#define COUNTER_PARTS(s,who,when,output)
#define COUNTER_PART_CORE(s,flags,legacy) legacy
#define COUNTER_PART_DIRECT(s,kind,legacy) legacy
#define COUNTER_PART_DEALT(s,kind,d,p,legacy) legacy
#define COUNTER_EXTRA_RESET(s,slot)
#endif
#ifdef PORTABLE_TARGET_COUNTERS
#define COUNTER_WORLD_LITERAL(s,through,legacy) targetCounterLiteralRoot(s,through,legacy)
#define COUNTER_PREPARE(s,row,when) prepareTargetCounter(s,row,when);
#define COUNTER_GUARD(s,row) if(targetCounterDeadDefinition(s,row)) continue;
#define COUNTER_FRAME(s,frames,depth) if(frames[depth].mode==26) { advanceTargetCounter(s,frames,depth);continue; }
#define COUNTER_ROOT(s,frames,depth,mode) if(mode==26) frames[depth].value=results[counterHead(s)+4];
#define COUNTER_NAMED(s,event,legacy) ((legacy)||(targetCountersEnabled(s)&&event==58))
#define COUNTER_INIT(s,output) if(!initializeTargetCounters(s)) { results[output]=64;return; }
#define COUNTER_COMMAND(s,at) else if(op==43) { if(!targetCounterCommand(s,at,step,when,output)) { s.error=64;break; } }
#else
#define COUNTER_WORLD_LITERAL(s,through,legacy) legacy
#define COUNTER_PREPARE(s,row,when)
#define COUNTER_GUARD(s,row)
#define COUNTER_FRAME(s,frames,depth)
#define COUNTER_ROOT(s,frames,depth,mode)
#define COUNTER_NAMED(s,event,legacy) legacy
#define COUNTER_INIT(s,output)
#define COUNTER_COMMAND(s,at)
#endif
#ifdef PORTABLE_WORLD_OVERLAYS
#include "world_overlay_runtime.slang"
#define WORLD_OVERLAY_INIT(s,output) if(!initializeWorldOverlays(s)) { results[output]=64;return; }
#define WORLD_CLEANSE(s,row,scope,when) worldCleanseResidents(s,row,scope,when)
#define WORLD_SKILL_BEGIN(s,who,target,amount) if(worldOverlayLand(s,who,target,amount,false)) {
#define WORLD_PHYSICAL_BEGIN(s,who,target,amount) if(worldOverlayLand(s,who,target,amount,worldPhysicalNormal(s,who))) {
#define WORLD_GATE_END }
#define WORLD_SKILL_GAUGE(s,who) if(worldSkillGauge(s,who))
#define WORLD_PHYSICAL_GAUGE(s) if(worldPhysicalGauge(s))
#define WORLD_PAUSE_WEAPON(s,w,who,when) if(worldPauseWeapon(s,w,who,when)) return;
#define WORLD_MODE_POLICY_INVALID(s,value) worldModePolicyInvalid(s,value)
#define WORLD_SAMPLE_SHOT_KIND(s,who,mode,hits) worldSampleShotKind(s,who,mode,hits);
#define WORLD_PACKET_NORMAL(s,who) (!worldPhysicalSkill(s,who))
#define WORLD_NORMAL_ONLY(s,who) if(!worldPhysicalSkill(s,who))
#define WORLD_PACKET_FLAGS(s,who,value) ((value) | (worldPhysicalSkill(s,who) ? 32768U : 0U))
#define WORLD_MODE_CORE(s,who,flags,accuracy) ((flags & 32768U)!=0 ? normalProbability(s,who,accuracy) : 0)
#define WORLD_MODE_CHARGE_CANCEL(s,who) worldChargeCancel(s,who); WORLD_CONTROL_CANCEL(s,who)
#define WORLD_CHARGE_START(s,who) worldChargeReset(s,who);
#define WORLD_CHARGE_HOLD(s,w,who,when) WORLD_CONTROL_READY(s,who,when,output) if(WORLD_CONTROL_HEAVY(s,who,worldChargeHold(s,w,who,when))) return;
#define WORLD_CHARGE_FINISH(s,w,who) if(w.mode==1) worldChargeReset(s,who); WORLD_CONTROL_FINISH(s,who)
#define WORLD_MODE_GAUGE(s,w,who,index) if(index>=0 && w.mode==1) w.gaugeMultiplier=(commands[s.inputBase+WO_IN+1]&(1U<<who))!=0 ? w.fullChargeMult : ONE;
#else
#define WORLD_OVERLAY_INIT(s,output)
#define WORLD_CLEANSE(s,row,scope,when) cleanseResidents(s,row,scope)
#define WORLD_SKILL_BEGIN(s,who,target,amount)
#define WORLD_PHYSICAL_BEGIN(s,who,target,amount)
#define WORLD_GATE_END
#define WORLD_SKILL_GAUGE(s,who)
#define WORLD_PHYSICAL_GAUGE(s)
#define WORLD_PAUSE_WEAPON(s,w,who,when)
#define WORLD_MODE_POLICY_INVALID(s,value) (value!=0)
#define WORLD_SAMPLE_SHOT_KIND(s,who,mode,hits)
#define WORLD_PACKET_NORMAL(s,who) true
#define WORLD_NORMAL_ONLY(s,who)
#define WORLD_PACKET_FLAGS(s,who,value) value
#define WORLD_MODE_CORE(s,who,flags,accuracy) 0
#define WORLD_MODE_GAUGE(s,w,who,index)
#define WORLD_MODE_CHARGE_CANCEL(s,who)
#define WORLD_CHARGE_START(s,who)
#define WORLD_CHARGE_HOLD(s,w,who,when)
#define WORLD_CHARGE_FINISH(s,w,who)
#endif
#ifdef PORTABLE_WORLD_ACTOR_POOLS
#define WORLD_POOL_LAND(s,who,target,amount) if((target&0x80000000U)!=0) { actorPoolLand(s,who,target&127U,amount);return; }
#define WORLD_POOL_SAMPLE(s) if(actorPoolsEnabled(s)) { s.enemySnapshot=actorPoolsEnemyCount(s);return; }
#define WORLD_POOL_ACCOUNTING(s,legacy) (actorPoolsEnabled(s) || (legacy))
#define WORLD_POOL_PHYSICAL_TARGET(s,who,target) actorPhysicalTarget(s,who,target)
#undef WORLD_PHYSICAL_BEGIN
#define WORLD_PHYSICAL_BEGIN(s,who,target,amount) if(actorPhysicalGate(s,who,target,amount,when)) {
#else
#define WORLD_POOL_LAND(s,who,target,amount)
#define WORLD_POOL_SAMPLE(s)
#define WORLD_POOL_ACCOUNTING(s,legacy) legacy
#define WORLD_POOL_PHYSICAL_TARGET(s,who,target) target
#endif
#ifdef PORTABLE_WORLD_ACTOR_FIELDS
#define WORLD_FIELDS_ENEMY_SELECT(s,d,target,order) if(actorFieldsEnabled(s)&&d.enemyBuff!=0) { order=1;return 1; }
#define WORLD_FIELDS_SAME(s,slot,recipients,gen) if(actorFieldsEnabled(s)) return actorFieldSame(s,slot,gen);
#define WORLD_FIELDS_QUERY_DEAD(s,target,legacy) (actorFieldsEnabled(s) ? !actorFieldQueryLive(s,target) : (legacy))
#define WORLD_FIELDS_MEMBER_INVALID(s,row,target,legacy) (actorFieldsEnabled(s) ? !actorFieldMember(s,row,target) : (legacy))
#define WORLD_FIELDS_CONDITION(s,row,target,when,legacy) (actorFieldsEnabled(s) ? actorFieldConditions(s,row,target,when) : (legacy))
#define WORLD_FIELDS_RESET(s,row) actorFieldReset(s,row);
#define WORLD_FIELDS_BIND(s,row,d,f) if(actorFieldsEnabled(s)&&d.enemyBuff!=0) actorFieldBind(s,row,f.target,f.repeatPassive);
#define WORLD_FIELDS_FRAME(s,frames,depth,f) if(f.mode==25) { advanceActorFields(s,frames,depth);continue; }
#define WORLD_FIELDS_FANOUT(s,frames,depth,d,row,f) if(actorFieldsEnabled(s)&&WORLD_STACK_FIELD_FANOUT(s,d,d.enemyBuff!=0)&&f.mode!=19) { beginActorFields(s,frames,depth,row,f);continue; }
#define WORLD_FIELDS_TARGET_INVALID(s,who,kind,legacy) (actorFieldsEnabled(s) ? actorFieldTargetMismatch(s,who,kind) : (legacy))
#define WORLD_FIELDS_INIT(s,output) if(!initializeActorFields(s)) { results[output]=64;return; }
#define WORLD_FIELDS_COMMAND(s,at) else if(op==39||op==40) { if(!actorFieldCommand(s,at,op,when)) { s.error=64;break; } }
#else
#define WORLD_FIELDS_ENEMY_SELECT(s,d,target,order)
#define WORLD_FIELDS_SAME(s,slot,recipients,gen)
#define WORLD_FIELDS_QUERY_DEAD(s,target,legacy) legacy
#define WORLD_FIELDS_MEMBER_INVALID(s,row,target,legacy) legacy
#define WORLD_FIELDS_CONDITION(s,row,target,when,legacy) legacy
#define WORLD_FIELDS_RESET(s,row)
#define WORLD_FIELDS_BIND(s,row,d,f)
#define WORLD_FIELDS_FRAME(s,frames,depth,f)
#define WORLD_FIELDS_FANOUT(s,frames,depth,d,row,f)
#define WORLD_FIELDS_TARGET_INVALID(s,who,kind,legacy) legacy
#define WORLD_FIELDS_INIT(s,output)
#define WORLD_FIELDS_COMMAND(s,at)
#endif
#ifdef PORTABLE_WORLD_ACTOR_STACKS
#define WORLD_STACK_POLICY(s,legacy) ((legacy)||actorStacksEnabled(s))
#define WORLD_STACK_HEADER(value,legacy) ((legacy)&&value!=0x57543031)
#define WORLD_STACK_KIND(s,d,legacy) ((legacy)&&!(actorStacksEnabled(s)&&stackOperation(d.kind)))
#define WORLD_STACK_FIELD_INVALID(s,d,legacy) (actorStacksEnabled(s)&&d.kind==19 ? false : (legacy))
#define WORLD_STACK_FIELD_FANOUT(s,d,legacy) ((legacy)&&(!actorStacksEnabled(s)||d.kind==0||d.kind==4))
#define WORLD_STACK_IMMUNITY_MEMBERS(s,row,legacy) (actorStacksEnabled(s)&&results[actorRecipientAt(s,row)]!=0 ? 0U : (legacy))
#define WORLD_STACK_SCOPE_BEGIN(s,row,d,own,maximum) uint stackSet=P_WORLD_ACTOR_SETS;ActorBits stackScope=actorBitsEmpty();bool stackWideScope=actorStacksEnabled(s)&&d.target==2&&!own&&!maximum;if(stackWideScope) { stackSet=actorStatusScope(s,row,stackScope);if(s.error!=0) return; }
#define WORLD_STACK_SCOPE_MISS(s,row,scope,legacy) (stackWideScope ? !actorStackAffected(s,row,stackScope) : (legacy))
#define WORLD_STACK_SCOPE_END(s) if(stackSet<P_WORLD_ACTOR_SETS) { results[actorPoolSet(s,stackSet)+5]=0;results[actorPoolHead(s)+7]--; }
#else
#define WORLD_STACK_POLICY(s,legacy) legacy
#define WORLD_STACK_HEADER(value,legacy) legacy
#define WORLD_STACK_KIND(s,d,legacy) legacy
#define WORLD_STACK_FIELD_INVALID(s,d,legacy) legacy
#define WORLD_STACK_FIELD_FANOUT(s,d,legacy) legacy
#define WORLD_STACK_IMMUNITY_MEMBERS(s,row,legacy) legacy
#define WORLD_STACK_SCOPE_BEGIN(s,row,d,own,maximum)
#define WORLD_STACK_SCOPE_MISS(s,row,scope,legacy) legacy
#define WORLD_STACK_SCOPE_END(s)
#endif
#ifdef PORTABLE_WORLD_ACTOR_STATUS
#define WORLD_STATUS_POLICY(s,legacy) ((legacy)||actorStatusEnabled(s))
#define WORLD_STATUS_HEADER(value,legacy) WORLD_STACK_HEADER(value,((legacy)&&value!=0x57493031))
#define WORLD_STATUS_KIND(s,d,legacy) WORLD_STACK_KIND(s,d,((legacy)&&!(actorStatusEnabled(s)&&d.kind==26)))
#define WORLD_STATUS_FIELD_INVALID(s,d,legacy) WORLD_STACK_FIELD_INVALID(s,d,(actorStatusEnabled(s) ? actorStatusFieldInvalid(s,d) : (legacy)))
#define WORLD_STATUS_FIELD_GUARD(s,d) if(actorStatusEnabled(s)&&!actorStatusScopeValid(s,d)) return false;
#define WORLD_STATUS_USED(s,who,name,legacy) actorStatusUsed(s,who,name)
#define WORLD_STATUS_BIT(s,who,legacy) (actorStatusEnabled(s)&&who>=5 ? 32U : (legacy))
#define WORLD_STATUS_MEMBER_INVALID(s,row,who,legacy) actorStatusMemberInvalid(s,row,who)
#define WORLD_STATUS_VISIBLE(s,row,who,legacy) actorStatusVisible(s,row,who)
#define WORLD_STATUS_COUNT_MEMBER_INVALID(s,row,who,legacy) actorStatusCountMemberInvalid(s,row,who)
#define WORLD_STATUS_FILTER(s,d,mask,order) if(actorStatusEnabled(s)&&d.enemyBuff!=0) return harmfulBlocked(s,5+(s.target&127U),d) ? 0U : mask;
#define WORLD_STATUS_RECHARGE(s,definition,mask,name) if(actorStatusEnabled(s)&&definition_enemyBuff(s.inputBase,definition)!=0) { if((mask&32)!=0) storeNumber(immunityUsed(s,5+(s.target&127U),name),0);return; }
#define WORLD_STATUS_CLEANSE_BEGIN(s,row) uint statusSet=P_WORLD_ACTOR_SETS;ActorBits statusScope=actorBitsEmpty();if(actorStatusEnabled(s)&&definition_target(s.inputBase,row)==2) { statusSet=actorStatusScope(s,row,statusScope);if(s.error!=0) return; }
#define WORLD_STATUS_CLEANSE_COUNT(s,legacy) (actorStatusEnabled(s) ? 5+actorPoolCount(s) : (legacy))
#define WORLD_STATUS_CLEANSE_SCOPE_MISS(s,scope,who,legacy) (actorStatusEnabled(s)&&who>=5 ? !actorBitsHas(statusScope,who-5) : (legacy))
#define WORLD_STATUS_CLEANSE_MEMBERS(s,row,who,bit,legacy) actorStatusCleanseMembers(s,row,who,bit)
#define WORLD_STATUS_CLEANSE_END(s) if(statusSet<P_WORLD_ACTOR_SETS) { results[actorPoolSet(s,statusSet)+5]=0;results[actorPoolHead(s)+7]--; }
#else
#define WORLD_STATUS_POLICY(s,legacy) legacy
#define WORLD_STATUS_HEADER(value,legacy) legacy
#define WORLD_STATUS_KIND(s,d,legacy) legacy
#define WORLD_STATUS_FIELD_INVALID(s,d,legacy) legacy
#define WORLD_STATUS_FIELD_GUARD(s,d)
#define WORLD_STATUS_USED(s,who,name,legacy) legacy
#define WORLD_STATUS_BIT(s,who,legacy) legacy
#define WORLD_STATUS_MEMBER_INVALID(s,row,who,legacy) legacy
#define WORLD_STATUS_VISIBLE(s,row,who,legacy) legacy
#define WORLD_STATUS_COUNT_MEMBER_INVALID(s,row,who,legacy) legacy
#define WORLD_STATUS_FILTER(s,d,mask,order)
#define WORLD_STATUS_RECHARGE(s,definition,mask,name)
#define WORLD_STATUS_CLEANSE_BEGIN(s,row)
#define WORLD_STATUS_CLEANSE_COUNT(s,legacy) legacy
#define WORLD_STATUS_CLEANSE_SCOPE_MISS(s,scope,who,legacy) legacy
#define WORLD_STATUS_CLEANSE_MEMBERS(s,row,who,bit,legacy) legacy
#define WORLD_STATUS_CLEANSE_END(s)
#endif
#ifdef PORTABLE_WORLD_ACTOR_RECIPIENTS
#define WORLD_RECIPIENT_STATE(s,legacy) ((legacy)||actorRecipientsEnabled(s))
#define WORLD_RECIPIENT_HEADER(value,legacy) WORLD_STATUS_HEADER(value,((legacy)&&value!=0x57523031))
#define WORLD_RECIPIENT_KIND(s,d,legacy) WORLD_STATUS_KIND(s,d,((legacy)&&!(actorRecipientsEnabled(s)&&d.kind==18)))
#define WORLD_RECIPIENT_RESET(s,row) resetActorRecipients(s,row);
#define WORLD_RECIPIENT_BIND(s,row,target,gen) bindActorRecipient(s,row,target,gen);
#define WORLD_RECIPIENT_MEMBER(s,row,target,legacy) (actorRecipientsEnabled(s) ? actorRecipientMember(s,row,target) : (legacy))
#define WORLD_RECIPIENT_SAME(s,row,gen,legacy) (actorRecipientsEnabled(s) ? actorRecipientSame(s,row,gen) : (legacy))
#define WORLD_RECIPIENT_GONE(s) if(actorRecipientsEnabled(s)) { actorRecipientsDropGone(s);return; }
#define WORLD_RECIPIENT_SCOPE_MISS(s,row,bits,legacy) (actorRecipientsEnabled(s) ? !actorRecipientsStrip(s,row,bits) : (legacy))
#define WORLD_RECIPIENT_INIT(s) initializeActorRecipients(s);
#define WORLD_RECIPIENT_STACK_INIT(s,slot,d,target) if(actorRecipientsEnabled(s)) { captureActorRecipients(s,slot,d,target); } else
#else
#define WORLD_RECIPIENT_STATE(s,legacy) legacy
#define WORLD_RECIPIENT_HEADER(value,legacy) legacy
#define WORLD_RECIPIENT_KIND(s,d,legacy) legacy
#define WORLD_RECIPIENT_RESET(s,row)
#define WORLD_RECIPIENT_BIND(s,row,target,gen)
#define WORLD_RECIPIENT_MEMBER(s,row,target,legacy) legacy
#define WORLD_RECIPIENT_SAME(s,row,gen,legacy) legacy
#define WORLD_RECIPIENT_GONE(s)
#define WORLD_RECIPIENT_SCOPE_MISS(s,row,bits,legacy) legacy
#define WORLD_RECIPIENT_INIT(s)
#define WORLD_RECIPIENT_STACK_INIT(s,slot,d,target)
#endif
#ifdef PORTABLE_WORLD_ACTOR_MUTATION
#define WORLD_MUTATION_STATE_ENABLED(s,legacy) WORLD_RECIPIENT_STATE(s,((legacy)||actorMutationEnabled(s)))
#define WORLD_MUTATION_HEADER_INVALID(s,value,legacy) WORLD_RECIPIENT_HEADER(value,((legacy)&&value!=0x574D3031))
#define WORLD_MUTATION_KIND_INVALID(s,d,legacy) WORLD_RECIPIENT_KIND(s,d,((legacy)&&!(actorMutationEnabled(s)&&d.kind==1)))
#define WORLD_MUTATION_NAMED_REMOVE(s,row,target,when) if(actorMutationEnabled(s)) { actorMutationRemoveNamed(s,row,target,when);return; }
#else
#define WORLD_MUTATION_STATE_ENABLED(s,legacy) legacy
#define WORLD_MUTATION_HEADER_INVALID(s,value,legacy) legacy
#define WORLD_MUTATION_KIND_INVALID(s,d,legacy) legacy
#define WORLD_MUTATION_NAMED_REMOVE(s,row,target,when)
#endif
#ifdef PORTABLE_WORLD_ACTOR_STATE
#define WORLD_STATE_TARGET_STACK(s,name,when,present,legacy) (actorStateEnabled(s) ? actorNamedTargetStack(s,name,present) : (legacy))
#define WORLD_STATE_STUN_TARGET(s,legacy) (actorStateEnabled(s) ? 5U+actorStateCurrentTarget(s) : (legacy))
#define WORLD_STATE_SELF_STACK(s,owner,name,arg) if(kind==C_SELF_STACK&&actorStateEnabled(s)) { if(f64Less(actorNamedSelfStack(s,owner,name),arg)) return false;continue; }
#define WORLD_STATE_SCOPE_BEGIN(s,target) uint actorStateScope=actorStatePushQuery(s,target);
#define WORLD_STATE_SCOPE_END(s) actorStatePopQuery(s,actorStateScope);
#define WORLD_STATE_DISPATCH_BEGIN(s) uint actorStateSavedOwner=results[actorFieldHead(s)+4],actorStateSavedTarget=results[actorFieldHead(s)+5];
#define WORLD_STATE_DISPATCH_FRAME(s,frames,depth) actorStateEvent(s,frames,depth,actorStateSavedOwner,actorStateSavedTarget);
#define WORLD_STATE_DISPATCH_END(s) if(actorStateEnabled(s)) { results[actorFieldHead(s)+4]=actorStateSavedOwner;results[actorFieldHead(s)+5]=actorStateSavedTarget; }
#define WORLD_STATE_GONE(s,slot) actorStateGone(s,slot);
#define WORLD_STATE_DROP_GONE(s) actorStateDropGone(s);
#define WORLD_STATE_END_REPEATS(s,slot,legacy) (actorStateEnabled(s)&&results[actorFieldKey(s,slot)]!=0 ? 1U : (legacy))
#define WORLD_STATE_MEMBER(s,row,legacy) (actorStateEnabled(s) ? (s.activeRecipients[row]&32)!=0&&(legacy) : (legacy))
#define WORLD_STATE_HEALTH_GUARD(s,d) if(actorStateEnabled(s)&&!actorStateHealthContract(d)) return false;
#define WORLD_STATE_ADMIT_CONDITION(s,at,kind,arg) if(actorStateEnabled(s)&&actorNamedConditionKind(kind)) { if(!actorNamedConditionValid(s,at,kind,arg)) return false;continue; }
#define WORLD_STATE_HEADER_INVALID(s,base,index,legacy) actorStateHeaderInvalid(s,base,index)
#define WORLD_STATE_BEFORE_RESET(s,b,p,slot) if(commands[b]==5&&results[p+1]!=0) actorStateGone(s,slot);
#define WORLD_STATE_NUMERIC_CONDITION(s,row,who,when,legacy) actorNamedNumericCondition(s,row,who,when)
#define WORLD_STATE_INIT(s,output) if(!initializeActorState(s)) { results[output]=64;return; }
#define WORLD_STATE_COMMAND(s,at) else if(op==41) { if(!actorNamedQueryCommand(s,at,step,when)) { s.error=64;break; } }
#else
#define WORLD_STATE_TARGET_STACK(s,name,when,present,legacy) legacy
#define WORLD_STATE_STUN_TARGET(s,legacy) legacy
#define WORLD_STATE_SELF_STACK(s,owner,name,arg)
#define WORLD_STATE_SCOPE_BEGIN(s,target)
#define WORLD_STATE_SCOPE_END(s)
#define WORLD_STATE_DISPATCH_BEGIN(s)
#define WORLD_STATE_DISPATCH_FRAME(s,frames,depth)
#define WORLD_STATE_DISPATCH_END(s)
#define WORLD_STATE_GONE(s,slot)
#define WORLD_STATE_DROP_GONE(s)
#define WORLD_STATE_END_REPEATS(s,slot,legacy) legacy
#define WORLD_STATE_MEMBER(s,row,legacy) legacy
#define WORLD_STATE_HEALTH_GUARD(s,d)
#define WORLD_STATE_ADMIT_CONDITION(s,at,kind,arg)
#define WORLD_STATE_HEADER_INVALID(s,base,index,legacy) legacy
#define WORLD_STATE_BEFORE_RESET(s,b,p,slot)
#define WORLD_STATE_NUMERIC_CONDITION(s,row,who,when,legacy) legacy
#define WORLD_STATE_INIT(s,output)
#define WORLD_STATE_COMMAND(s,at)
#endif
#include "geometry_runtime.slang"

bool hasProtection(inout Runtime s,uint who,uint kind);
bool statusStunImmune(inout Runtime s,uint who);
bool statusStunned(inout Runtime s,uint who);
void chooseEnemyVictims(inout Runtime s,uint step,uint64_t when);

[ForceInline]
Definition residentDefinition(inout Runtime s, uint slot) { return readDefinition(s.inputBase,s.carrierDefinition[slot]); }

uint64_t carrierOrder(inout Runtime s,uint slot)
{
    if(commands[s.inputBase+P_RECIPIENT_META_BASE]==0) return s.carrierRecipientOrder[slot];
    uint at=s.resourceOutput+P_RECIPIENT_ORDER_BASE+slot*2;
    return uint64_t(results[at])|(uint64_t(results[at+1])<<32);
}
uint64_t visibleCarrierOrder(inout Runtime s,uint slot)
{
    uint64_t order=carrierOrder(s,slot),outOrder=0;uint count=0,mask=s.activeRecipients[slot];
    for(uint i=0;i<21;i++) { uint encoded=(order>>(3*i))&7;if(encoded==0) break;if((mask&(1U<<(encoded-1)))!=0) outOrder|=uint64_t(encoded)<<(3*count++); }
    return outOrder;
}
void storeCarrierOrder(inout Runtime s,uint slot,uint64_t order)
{
    s.carrierRecipientOrder[slot]=uint(order);
    if(commands[s.inputBase+P_RECIPIENT_META_BASE]!=0) storeNumber(s.resourceOutput+P_RECIPIENT_ORDER_BASE+slot*2,order);
}
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
// Native target predicates inspect any enemy member of an exact-name carrier,
// independently of its caster and of the currently aimed enemy. Stack count
// is the largest instance, not a sum across casters or enemy recipients.
uint64_t targetStateStack(inout Runtime s,int name,uint64_t when,out bool present)
{
    uint64_t count=0;present=false;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];
        if(s.alive[slot]==0 || !f64Less(when,s.end[slot]) || int(definition_name(s.inputBase,s.carrierDefinition[slot]))!=name) continue;
        Definition carrier=residentDefinition(s,slot);bool member=false;
        if(carrier.enemyBuff!=0)
            for(uint enemy=0;enemy<s.targetCount;enemy++)
                if((s.activeRecipients[slot]&(1U<<(enemy+5)))!=0 && targetLive(s,enemy,enemyCarrierGeneration(s,slot,enemy))) member=true;
        if(carrier.kind==3 && !f64Zero(carrier.interval))
        {
            uint packed;
            member=(carrier.periodicFlags&1)!=0 ? periodicDamageMask(s,s.carrierDefinition[slot],packed)!=0 : targetLive(s,s.timerTarget[s.carrierDefinition[slot]],s.timerGeneration[s.carrierDefinition[slot]]);
        }
        if(member) { present=true;count=larger(count,carrierStackValue(s,slot)); }
    }
    return count;
}
[noinline]
bool basicConditions(inout Runtime s, uint row, uint64_t when, bool runtime, uint recipient = 0xffffffff, uint conditionSlot = 0xffffffff)
{
    uint definition = s.carrierDefinition[row], owner = WORLD_TEAM_OWNER(s,definition,runtime,definition_owner(s.inputBase,definition));
    if (runtime && (referenceCaptureFlags(s,row)&4)==0 && (!f64Less(definition_duration(s.inputBase,definition),0) || (definition_flags(s.inputBase,definition) & 2) == 0)) return true;
    uint first=conditionSlot==0xffffffff ? 0 : conditionSlot;
    uint last=conditionSlot==0xffffffff ? definition_conditionCount(s.inputBase,definition) : conditionSlot+1;
    for (uint i = first; i < last; i++)
    {
        uint at = s.inputBase+P_CONDITION_BASE+definition*P_CONDITION_WORDS+i*4;
        uint kind = commands[at]; int name = int(commands[at+1]); uint64_t arg = loadNumber(at+2);
        if(kind==C_TARGET_STATE || kind==C_NOT_TARGET_STATE || kind==C_TARGET_STACK && !runtime)
        {
            bool present;uint64_t count=WORLD_TEAM_TARGET(s,definition,runtime,name,when,present,WORLD_STATE_TARGET_STACK(s,name,when,present,targetStateStack(s,name,when,present)));
            if(kind==C_TARGET_STATE && !present || kind==C_NOT_TARGET_STATE && present || kind==C_TARGET_STACK && f64Less(count,arg)) return false;
            continue;
        }
        if (runtime && kind != C_GAUGE_ABOVE && kind != C_GAUGE_BELOW && kind != C_FULL && kind != C_NOT_FULL && kind != C_SELF_STATE && kind != C_NOT_SELF_STATE && kind != C_SELF_STACK && kind != C_CAST && kind != C_NOT_CAST && kind != C_CHARGING && kind != C_ENEMIES_ABOVE && kind != C_ENEMIES_BELOW && kind != C_HP_ABOVE && kind != C_HP_BELOW && kind != C_HP_MAX && kind != C_ALLY_HP_BELOW && kind != C_COVER_ALIVE && kind != C_COVER_BROKEN && kind != C_SHIELD && kind != C_TARGET_CODE) continue;
        if (kind >= C_GAUGE_ABOVE && kind <= C_GAUGE_MOD && !resourceCondition(s,owner,kind,uint(name),arg,int(commands[s.inputBase+P_RESOURCE_CONDITION_BASE+definition*3+i]))) return false;
        if (kind == C_CORE && !geometryCore(s)) return false;
        if (kind == C_TARGET_STUNNED && !statusStunned(s,WORLD_TEAM_STUN_TARGET(s,definition,runtime,WORLD_STATE_STUN_TARGET(s,5U+s.target)))) return false;
        if (kind == C_SELF_STUN_IMMUNE && !statusStunImmune(s,owner)) return false;
        if (kind == C_TARGET_CODE)
        {
            uint code=commands[s.inputBase+P_WORLD_META_BASE];
            if(code!=0 && code!=uint(name)) return false;
        }
        if (kind == C_FULL && s.phase != 5 || kind == C_NOT_FULL && s.phase == 5) return false;
        if (kind == C_SELF_STATE || kind == C_NOT_SELF_STATE)
        {
            uint flags = f64Equal(arg,ONE) ? 1 : f64Equal(arg,f64FromI64(2)) ? 2 : 0;
            bool present = stateMember(s,owner,name,flags);
            if (kind == C_SELF_STATE && !present || kind == C_NOT_SELF_STATE && present) return false;
        }
        WORLD_STATE_SELF_STACK(s,owner,name,arg) if (kind == C_SELF_STACK)
        {
            uint64_t count = 0;
            for (uint pass = 0; pass < s.orderedCount; pass++)
            {
                uint j = s.orderedRows[pass]; Definition carrier = residentDefinition(s,j);
                bool member=(s.activeRecipients[j]&(1U<<owner))!=0;
                if (carrier.enemyBuff!=0) for (uint enemy=0; enemy<s.targetCount; enemy++)
                    if ((s.activeRecipients[j]&(1U<<(enemy+5)))!=0 && s.targetAlive[enemy]!=0 && s.targetGeneration[enemy]==enemyCarrierGeneration(s,j,enemy)) member=true;
                if (carrier.kind==3)
                { uint packed; member=(carrier.periodicFlags&1)!=0 ? periodicDamageMask(s,s.carrierDefinition[j],packed)!=0 : targetLive(s,s.timerTarget[s.carrierDefinition[j]],s.timerGeneration[s.carrierDefinition[j]]); }
                if (carrier.owner == owner && int(carrier.name) == name && s.alive[j] != 0 && member) { count = carrierStackValue(s,j); break; }
            }
            if (s.combat != 0 && s.modeIndex[owner] >= 0 && int(definition_name(s.inputBase,s.modeIndex[owner])) == name) count = ONE;
            if (f64Less(count,arg)) return false;
        }
        if (kind == C_HP_ABOVE && f64Less(s.hpPct[owner],arg) || kind == C_HP_BELOW && f64Less(arg,s.hpPct[owner]) || kind == C_HP_MAX && f64Less(s.hpPct[owner],HUNDRED)) return false;
        if (kind == C_SHIELD && !hasProtection(s,owner,1)) return false;
        if (kind == C_COVER_ALIVE && f64Zero(s.coverHP[owner]) || kind == C_COVER_BROKEN && !f64Zero(s.coverHP[owner])) return false;
        if (kind == C_NOT_SELF_HEAL && (s.healSource < 0 || uint(s.healSource) == owner)) return false;
        if (kind == C_ALLY_HP_BELOW)
        {
            bool present = false;
            if (runtime) present = recipient < 5 ? !f64Less(arg,s.hpPct[recipient]) : !f64Less(arg,HUNDRED);
            else for (uint who = 0; who < 5; who++) if (!f64Less(arg,s.hpPct[who])) present = true;
            if (!present) return false;
        }
        if (kind == C_BACK_ROW && owner != 1 && owner != 3) return false;
        if (kind == C_CAST && (s.castMask & (1U << owner)) == 0 || kind == C_NOT_CAST && (s.castMask & (1U << owner)) != 0) return false;
        if (kind == C_STATIC && f64Zero(arg) || kind == C_CHARGING && s.charging[owner] == 0) return false;
        if (kind == C_BURST1_ALLY || kind == C_NO_BURST1_ALLY)
        {
            bool has = false; for (uint who = 0; who < 5; who++) if (who != owner && s.currentStage[who] == 1) has = true;
            if (kind == C_BURST1_ALLY && !has || kind == C_NO_BURST1_ALLY && has) return false;
        }
        if (kind == C_ENEMIES_ABOVE && f64Less(f64FromI64(s.enemySnapshot),arg) || kind == C_ENEMIES_BELOW && f64Less(arg,f64FromI64(s.enemySnapshot))) return false;
        if (WORLD_FIELDS_TARGET_INVALID(s,owner,kind,kind == C_TARGET_BOSS && s.target != 0 || kind == C_TARGET_ADD && s.target == 0)) return false;
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
#ifdef PORTABLE_WORLD_ENEMY_ATTACK
#include "world_enemy_attack_runtime.slang"
#endif
#include "carrier_runtime.slang"
#include "quantity_runtime.slang"
#include "health_runtime.slang"
#include "lifesteal_runtime.slang"
#include "cover_runtime.slang"
#include "hp_edge_runtime.slang"
#include "hp_attack_runtime.slang"

// Collect in resident order once per query/hit. Four critical sums use the
// same compensated accumulation as the reference; other scalar sums are ordered.
[noinline]
void collectStats(inout Runtime s, uint who, uint64_t when, out uint64_t values[64])
{
    WORLD_STATE_SCOPE_BEGIN(s,s.target) bool query = needsBuffResolution(s) && beginBuffQuery(s,who,when);
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
        if((s.quantityMask & 256)!=0 && d.stat==S_atk_caster_based_pct) continue;
        if(d.stat==S_stun) continue; // Presence must not consume a pending rank as a numeric buff.
        if (d.alliedFlags != 0 || d.kind != 0 || d.stat >= 64 || d.stat == S_infinite_ammo || s.alive[selected] == 0 || !f64Less(when,s.end[selected]) ||
            !WORLD_ENEMY_ATTACK_DAMAGE_MEMBER(s,selected,who,when,queryRecipient(s,selected,who,when))) continue;
        // Native boolean flags ignore their numeric value and stack scaling.
        // Reuse their existing slots in the64-value vector, with no new query.
        if(d.stat==S_pierce_enabled || d.stat==S_armor_break_enabled)
        { values[d.stat]=ONE;continue; }
        uint64_t value = d.stat == S_atk_caster_based_pct ? scalarValue(s,selected,who) : recipientValue(s,selected,who);
        if (d.stat == S_crit_rate || d.stat == S_normal_atk_crit_rate)
        {
            value = f64Div(value,HUNDRED); addSum(rate,value);
            if (d.stat == S_crit_rate) addSum(skillRate,value);
        }
        else if (d.stat == S_crit_dmg || d.stat == S_normal_atk_crit_dmg)
        { addSum(critical,value); if (d.stat == S_crit_dmg) addSum(skillCritical,value); }
        else if (d.stat == S_atk_caster_based_pct) values[S_atk_flat] = f64Add(values[S_atk_flat],f64Mul(s.baseAttack[d.owner],f64Div(value,HUNDRED)));
        else if(d.stat==S_burst_charge_speed_pct)
        {
            uint at=s.inputBase+P_BURST_REFERENCE_BASE+8+d.owner*4;
            uint64_t reference=loadNumber(at);
            if((s.normalLandedMask & (1U<<d.owner))==0)
                reference=(commands[s.inputBase+P_BURST_REFERENCE_BASE+1] & (1U<<d.owner))!=0 ? loadNumber(at+2) : f64Div(reference,f64FromI64(2));
            values[d.stat]=f64Add(values[d.stat],f64Div(f64Mul(reference,value),HUNDRED));
        }
        else values[d.stat] = f64Add(values[d.stat],value);
    }
    if((s.quantityMask & 256)!=0) collectHPAttack(s,who,when,values[S_atk_flat]);
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
    if (query) s.queryActive = 0; WORLD_STATE_SCOPE_END(s)
}
#include "recipient_runtime.slang"
#include "skill_clock_runtime.slang"

[noinline]
uint64_t readStat(inout Runtime s, uint who, uint key, uint64_t when)
{
    if(key==S_stun) return statusStunned(s,who) ? ONE : 0;
    uint64_t values[64]; collectStats(s,who,when,values); return values[key];
}

[noinline]
bool activationConditions(inout Runtime s, uint row, uint64_t when)
{
    uint owner=WORLD_TEAM_OWNER(s,row,false,definition_owner(s.inputBase,row));
    for (uint i = 0; i < definition_conditionCount(s.inputBase,row); i++)
    {
        uint at = s.inputBase+P_CONDITION_BASE+row*P_CONDITION_WORDS+i*4;
        if (commands[at] == C_STAT_ABOVE)
        {
            if(!f64Less(loadNumber(at+2),readStat(s,owner,commands[at+1],when))) return false;
        }
        else if(commands[at] == C_OPTIMAL_RANGE)
        {
            uint64_t values[64];
            if((commands[s.inputBase+P_GEOMETRY_BASE]&2)!=0) collectStats(s,owner,when,values);
            else { values[S_optimal_range_min]=0;values[S_optimal_range_max_pct]=0; }
            if(!geometryRange(s,owner,false,values[S_optimal_range_min],values[S_optimal_range_max_pct])) return false;
        }
        else if(commands[at] == C_PROB)
        {
            uint address=s.resourceOutput+P_PROBABILITY_STATE_BASE+(WORLD_TEAM_BUDGET(s,row)*5+owner)*2;
            uint64_t value=uint64_t(results[address]) | uint64_t(results[address+1])<<32;
            value=f64Add(value,loadNumber(at+2));
            bool passed=!f64Less(value,ONE);
            if(passed) value=f64Add(value,ONE ^ F64_SIGN);
            storeNumber(address,value);
            if(!passed) return false;
        }
        else if(!basicConditions(s,row,when,false,0xffffffff,i)) return false;
    }
    return true;
}

void sampleWorld(inout Runtime s)
{
    WORLD_POOL_SAMPLE(s) s.enemySnapshot = s.combat == 0 ? 1 : 0;
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
    WORLD_POOL_LAND(s,who,target,amount) if (s.combat != 0 && s.targetHits[target] == 0x7fffffff) { s.error = 2; return; }
#ifdef PORTABLE_ACCOUNTING_REFERENCE
    bool separate = true;
#else
    bool separate = WORLD_POOL_ACCOUNTING(s,s.combat != 0 && s.targetCount > 1);
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
    bool separate = WORLD_POOL_ACCOUNTING(s,s.combat != 0 && s.targetCount > 1);
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
    s.modeIndex[who] = -1; s.modeEpoch[who]++; s.appliedEpoch[who] = s.modeEpoch[who]; s.modeShots[who] = 0; s.modeEntryUntil[who] = F64_SIGN | ONE;
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

void pushFrame(inout Runtime s, inout Frame frames[32], inout int depth, uint mode, uint event, uint owner, int argument, uint64_t when, uint64_t value = 0)
{
    if (depth == 31) { s.error = 1; return; }
    depth++;
    Frame f = {};
    if (mode == 9) { f.value = uint(argument); f.repeatLeft = s.removalCount-uint(argument); }
    f.mode = mode; f.event = event; f.owner = owner; f.argument = argument; f.time = when; f.value = mode == 9 ? uint(argument) : value;
    uint inherited = event < 32 ? P_TARGET_INHERIT_0 : P_TARGET_INHERIT_1;
    f.target = s.combat == 0 || mode != 0 || (event < 64 && (inherited & (1U << (event%32))) != 0) ? s.target : 0;
    frames[depth] = f; COUNTER_CONTEXT_PUSH(s,depth,mode,event) s.maxDepth = max(s.maxDepth,uint(depth+1));
}

#include "element_runtime.slang"
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
#ifdef PORTABLE_WORLD_OVERLAYS
void worldCleanseResidents(inout Runtime s,uint row,uint scope,uint64_t when)
{ if(worldCleanseDefinition(s,row)) worldDispel(s,row,scope,when);else cleanseResidents(s,row,scope); }
#endif
#include "event_candidate_runtime.slang"
#include "pending_burst_runtime.slang"
#include "incoming_descriptor_runtime.slang"
#include "protection_runtime.slang"
#include "healing_storage_runtime.slang"

[noinline]
uint packedRecipientMask(uint64_t order)
{
    uint mask = 0;
    for (uint i = 0; i < 21; i++) { uint who = (order >> (3*i)) & 7; if (who != 0) mask |= 1U << (who-1); }
    return mask;
}
[noinline]
uint64_t buffAudienceOrder(inout Runtime s, uint row)
{
    Definition d = residentDefinition(s,row);
    if (d.enemyBuff != 0 && (d.buffEvent & 2) != 0) return 0;
    if ((d.buffEvent & 2) == 0) return 1U | (2U<<3) | (3U<<6) | (4U<<9) | (5U<<12);
    if (s.lazyPending[row] != 0) return d.owner+1;
    uint count=0;uint64_t result=0,order=carrierOrder(s,row);
    for (uint i = 0; i < 21; i++)
    {
        uint who = (order >> (3*i)) & 7;
        if (who != 0 && (s.activeRecipients[row] & (1U << (who-1))) != 0) { result |= uint64_t(who) << (3*count); count++; }
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
                    if ((buff.buffEvent&1)!=0 && f.healthValue != 0) pushFrame(s,frames,depth,12,31,buff.owner,int(buff.name),f.time,f.healthValue);
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
                    uint64_t order = s.entryOrder[slot] == f.repeatPassive ? buffAudienceOrder(s,slot) : f.healthValue;
                    if (order != 0 && (s.namedEventOwners & packedRecipientMask(order)) != 0)
                        pushFrame(s,frames,depth,12,31,buff.owner,int(buff.name),f.time,order);
                }
                return;
            }
            if (f.event == 2 && (buff.buffEvent >> 2) != 0)
            {
                frames[depth].event = 3;
                // Native activation keeps its eagerly selected local target
                // list across named/stack callbacks, even if they remove or
                // replace the carrier. Incoming lazy targets have a zero captured
                // order; the resident may originate from a different selector.
                if (f.value != 0)
                    pushFrame(s,frames,depth,12,31,buff.owner,int((buff.buffEvent >> 2)-1),f.time,f.value);
                return;
            }
            if (f.repeatLeft!=0 && s.entryOrder[slot]==f.repeatPassive && s.carrierDefinition[slot]==f.repeatRow) captureBuffReference(s,slot,f.cursor-1);
            rechargeImmunity(s,f.cursor-1,packedRecipientMask(buff.enemyBuff!=0 ? 0 : f.value)|(buff.enemyBuff!=0 ? uint(f.value>>16) : 0));
            depth--;
            uint protection=protectionPolicy(s,f.repeatRow)&255;
            if((protection==1 || protection==2 || protection==9) && buff.lazyGroup==0 && f.value!=0 && s.alive[slot]!=0 && s.entryOrder[slot]==f.repeatPassive && s.carrierDefinition[slot]==f.repeatRow)
            {
                if(f.repeatLeft!=0) captureBuffReference(s,slot,f.repeatRow);
                uint64_t order=0;
                if(protection==9) buildHealingStorage(s,slot,f.time);
                else order=buildProtection(s,slot,f.time);
                if(order!=0 && s.error==0) pushFrame(s,frames,depth,21,0,buff.owner,0,f.time,order);
                return;
            }
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
    WORLD_INITIAL_SPAWN_OBSERVE(s,mode,event,owner,when) s.sourceTime=when; syncHealth(s,when);
    WORLD_TEAM_BEGIN(s) COUNTER_CONTEXT_BEGIN(s) WORLD_STATE_DISPATCH_BEGIN(s) uint entryTarget = s.target;
    Frame frames[32]; int depth = -1;
    if ((s.healthMask&32)!=0) pushFrame(s,frames,depth,16,0,0,0,when);
    pushFrame(s,frames,depth,mode,event,owner,argument,when);
    COUNTER_ROOT(s,frames,depth,mode) if (mode == 17 && s.error == 0) frames[depth].healthValue=landingAmount;
    uint work = 0;
    while (depth >= 0 && s.error == 0)
    {
        if (++work > COUNTER_FIELDS_WORK_LIMIT(s,4096)) { s.error = 4; break; }
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
        COUNTER_FRAME(s,frames,depth) COUNTER_CONTEXT_SAMPLE(s,depth) WORLD_STATE_DISPATCH_FRAME(s,frames,depth) Frame f = frames[depth]; s.sourceTime=f.time; s.target = f.target; s.healSource = f.event == 16 ? f.argument : -1; uint row = s.count, passive = 0; WORLD_TEAM_FRAME(s,f)
        if (f.cursor == 0 && (f.mode == 0 || f.mode == 1 || f.mode == 2) &&
            (s.downMask & (1U << f.owner)) != 0 && f.event != 26 && f.event != 28 && f.event != 38)
        { depth--; continue; }
        if(f.mode==20) { advanceProtectionHit(s,frames,depth);continue; }
        if(f.mode==21)
        {
            uint encoded=f.cursor<5 ? (f.value>>(f.cursor*3))&7 : 0;
            if(encoded==0) { depth--;continue; }
            frames[depth].cursor++;pushFrame(s,frames,depth,0,18,encoded-1,0,f.time);continue;
        }
        WORLD_FIELDS_FRAME(s,frames,depth,f) if (f.mode==18)
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
            if (f.cursor == (f.value==0 ? 5 : 21)) { depth--; continue; }
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
                    uint64_t gain = f64Less(damage.damageGauge,0) ? (s.physicalGaugeOwner==damage.owner+1 ? s.physicalGaugeGain : s.gain[damage.owner]) : damage.damageGauge;
                    WORLD_SKILL_GAUGE(s,damage.owner) addBurstGauge(s,f64Add(f64Mul(gain,f64FromI64(f.value)),f64Mul(f.gaugeFlat,f64FromI64(f.value))));
                }
                continue;
            }
            if (s.landingPolicy != 0)
            {
                if (f.cursor == 0)
                {
                    s.target=WORLD_SKILL_BASIS(s,damage.damageRoute>=2 || damage.damageRoute==1 ? 0 : f.target);
                    WORLD_SKILL_SCOPE_BEGIN(s) frames[depth].healthPrevious=damage.damageNormal!=0 ? damageValue(s,damage.owner,f.healthValue,f.time,true,s.combat!=0 ? s.coreDamageBonus[damage.owner] : s.coreBonus,damage.damageFlags,ONE,(s.attackContext[damage.owner]&1)!=0) : damageValue(s,damage.owner,f.healthValue,f.time,false,s.coreBonus,damage.damageFlags); WORLD_SKILL_SCOPE_END(s)
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
            { uint encoded = (packedOrder >> (pass*4)) & 15; if (encoded == 0) break; WORLD_SKILL_BEGIN(s,damage.owner,encoded-1,share) land(s,damage.owner,encoded-1,share); WORLD_GATE_END }
            frames[depth].cursor++; frames[depth].value++;
            logDamagePacket(s,damage,uint(f.argument),mask,basis,f.cursor+1,share,weighted,packedOrder,f.time,uint(depth+1),output);
            if (s.error == 0) pushFrame(s,frames,depth,0,49,damage.owner,int(damage.name),f.time);
            continue;
        }
        if (f.mode == 11)
        {
            Definition cover = readDefinition(s.inputBase,uint(f.argument));
            uint encoded = f.cursor < 21 ? (f.value >> (3*f.cursor)) & 7 : 0;
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
        if(f.mode==24)
        {
            // One captured ordered target at a time. Child notifications finish
            // before the next recipient's live basis and state are evaluated.
            Definition instant=readDefinition(s.inputBase,uint(f.argument));
            uint encoded=f.cursor<21 ? (f.value>>(3*f.cursor))&7 : 0;
            if(encoded==0)
            {
                depth--;
                if(instant.kind==13 && instant.target!=0 && s.error==0) pushFrame(s,frames,depth,0,31,instant.owner,int(instant.name),f.time);
                continue;
            }
            frames[depth].cursor++;uint member=encoded-1;
            if((s.downMask&(1U<<member))!=0) continue;
            if(instant.kind==6) pushFrame(s,frames,depth,3,0,member,f.argument,f.time);
            else if(instant.kind==7 || instant.kind==30) pushFrame(s,frames,depth,11,0,instant.owner,f.argument,f.time,encoded);
            else if(instant.kind==8) pushFrame(s,frames,depth,6,0,instant.owner,f.argument,f.time,encoded);
            else if(instant.kind==5) reduceBurstReady(s,1U<<member,instant.value,f.time);
            WORLD_RELOAD_ORDERED(s,instant,member,f.time) else if(instant.kind==13 || instant.kind==14) applyAmmoInstant(s,instant,1U<<member,f.time);
            else if(instant.kind==27 || instant.kind==31)
            {
                uint kind=instant.kind==27 ? 1 : 2;
                if(!f64Zero(instant.value))
                {
                    uint64_t basis=instant.healthScaling!=0 ? effectiveMaxHP(s,instant.owner,f.time) : protectionCapacity(s,member,kind);
                    uint64_t amount=f64Div(f64Mul(basis,instant.value),HUNDRED);
                    if(!f64Finite(amount)) { s.error=16;continue; }
                    healProtection(s,member,kind,amount,f.time);
                }
            }
            else s.error=64;
            continue;
        }
        if(f.mode==22)
        {
            uint encoded=f.cursor<5 ? (f.value>>(3*f.cursor))&7 : 0;
            if(encoded==0) { depth--;continue; }
            frames[depth].cursor++;uint member=encoded-1;
            if((s.downMask&(1U<<member))!=0) continue;
            pushFrame(s,frames,depth,23,0,member,f.argument,f.time);
            if(s.error==0)
            {
                frames[depth].healthValue=f.healthValue;frames[depth].repeatPassive=uint(member==f.owner);
                uint legacy=f.cursor==0 ? P_PROTECTION_HIT_BASE+(uint(f.argument)*5+f.owner)*16 : P_SPLIT_HIT_BASE+(uint(f.argument)*20+f.owner*4+f.cursor-1)*16;
                frames[depth].repeatRow=incomingRecordAddress(s,uint(f.argument),f.owner,member,member==f.owner,legacy);
            }
            continue;
        }
        if (f.mode == 8 || f.mode == 23)
        {
            uint at = incomingCommandAddress(s,uint(f.argument));
            if(f.event==5) { depth--;continue; }
            if(f.event==6) { frames[depth].event=0;continue; }
            if(f.mode==23 && f.event==0)
            {
                frames[depth].event=1;
                pushFrame(s,frames,depth,20,0,f.owner,f.argument,f.time);
                if(s.error==0) { frames[depth].healthValue=f.healthValue;frames[depth].repeatPassive=f.repeatRow; }
                continue;
            }
            if (f.event == 0)
            {
                // Selection is part of this event frame:sourceTime and HP edges
                // are current before choosing the frozen,ordered victim list.
                WORLD_ENEMY_ATTACK_CAPTURE(s,frames,depth,f) if(f.mode==8 && commands[at]==32 && f.cursor==0)
                {
                    chooseEnemyVictims(s,uint(f.argument),f.time);
                    if(s.error!=0) break;
                }
                uint who;
                if(commands[at]==32)
                {
                    uint order=results[enemyQueryAddress(s,uint(f.argument))+1],cursor=frames[depth].cursor,encoded=0;
                    while(cursor<5)
                    {
                        encoded=(order>>(3*cursor++))&7;
                        if(encoded==0 || (s.downMask&(1U<<(encoded-1)))==0) break;
                    }
                    if(encoded==0 || (s.downMask&(1U<<(encoded-1)))!=0) { depth--;continue; }
                    who=encoded-1;frames[depth].cursor=cursor;
                }
                else
                {
                    uint mask=commands[at+5] & ~s.downMask;who=frames[depth].cursor;
                    while(who<5 && (mask&(1U<<who))==0) who++;
                    if(who==5) { depth--;continue; }
                    frames[depth].cursor=who+1;
                }
                frames[depth].owner=who;
                uint input = incomingDamageAddress(s,uint(f.argument));
                frames[depth].healthValue = incomingBodyDamage(s,who,WORLD_ENEMY_ATTACK_VALUE(s,frames,depth,f,loadNumber(input)),loadNumber(input+2),f.time);
                frames[depth].event = 1;
                if((commands[at]==31 || commands[at]==32))
                {
                    uint64_t amount=frames[depth].healthValue;
                    uint group=incomingSplitGroup(s,who,f.time);
                    if(group!=0)
                    {
                        uint count=0;for(uint order=group;order!=0;order>>=3) count++;
                        frames[depth].event=6;pushFrame(s,frames,depth,22,0,who,f.argument,f.time,group);
                        if(s.error==0) frames[depth].healthValue=f64Div(amount,f64FromI64(count));
                        continue;
                    }
                    uint record=incomingRecordAddress(s,uint(f.argument),who,who,true,P_PROTECTION_HIT_BASE+(uint(f.argument)*5+who)*16);frames[depth].repeatRow=record;
                    pushFrame(s,frames,depth,20,0,who,f.argument,f.time);
                    if(s.error==0) { frames[depth].healthValue=amount;frames[depth].repeatPassive=record; }
                }
                continue;
            }
            if (f.event == 1)
            {
                uint64_t amount = liveMarker(s,f.owner,S_invincible,f.time) ? 0 : f.healthValue;
                amount=transferHealingStorage(s,f.owner,amount,f.time,false);
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
                if((commands[at]==31 || commands[at]==32)) frames[depth].healthValue=amount;
                s.receivedDamage[f.owner] = f64Add(s.receivedDamage[f.owner],amount);
                if (!f64Finite(s.receivedDamage[f.owner])) { s.error = 16; break; }
                if (s.receivedHits[f.owner] == 0x7fffffff) { s.error = 2; break; }
                s.receivedHits[f.owner]++;
                s.hp[f.owner] = larger(0,f64Add(s.hp[f.owner],amount ^ F64_SIGN));
                if (!fell) syncHealthActor(s,f.owner,f.time);
                frames[depth].value = uint(fell); frames[depth].event = 3;
                if(f.mode==8 || f.repeatPassive!=0) pushFrame(s,frames,depth,0,32,f.owner,0,f.time); continue;
            }
            if(f.event==3 && f64Less(0,f.healthPrevious))
            { frames[depth].event=4;pushFrame(s,frames,depth,0,36,f.owner,0,f.time);continue; }
            if((commands[at]==31 || commands[at]==32))
            {
                uint hit=output+f.repeatRow;
                storeNumber(hit+12,f.healthValue);storeNumber(hit+14,f.value!=0 && (s.downMask&(1U<<f.owner))==0 ? 0 : s.hp[f.owner]);
                if(f.value!=0 && (s.downMask&(1U<<f.owner))==0) results[hit+3]|=4;
            }
            frames[depth].event = f.mode==23 ? 5 : 0;
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
            uint encoded = index < 21 ? (f.value >> (3*index)) & 7 : 0;
            if (encoded == 0) { depth--; continue; }
            frames[depth].cursor = index+1; uint who = encoded-1;
            if ((s.downMask & (1U << who)) != 0) continue;
            if (f.mode == 5) s.hp[who] = smaller(f64Add(s.hp[who],f.healthValue),effectiveMaxHP(s,who,f.time));
            else s.hp[who] = storageBodyReduce(s,who,health.value,f.time);
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
            s.hp[f.owner] = storageBodyHeal(s,f.owner,amount,f.time);
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
                    if (COUNTER_NAMED(s,event,WORLD_CONTROL_NAMED(event,(event == 9 || event == 29 || event == 30 || event == 31 || event == 48 || event == 49 || event == 59))) && tag != f.argument) continue;
                    if (event == 9 && commands[at+5] != f.value) continue; WORLD_PROJECTILE_SKIP_SLOT(event,stage)
                    multiplicity++; bool ok = event != 30 || resourceModulo(f.healthValue,uint(f64ToPositiveStep(loadNumber(at+1)))) == 0;
                    if (mode != 0 || event == 7 || event == 8)
                    {
                        uint counter = j*8+slot, status;
                        uint64_t threshold64 = f64ToI64(loadNumber(at+1),1,status);
                        if (status != 0 || threshold64 == 0 || threshold64 > 0x7fffffff || s.counters[counter] == 0x7fffffff) { s.error = 2; break; }
                        uint count = WORLD_TEAM_COUNTER(s,f.event,counter), threshold = uint(threshold64);
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
        Definition d = readDefinition(s.inputBase,row); WORLD_TEAM_GUARD(s,row,f)
        if (f.mode == 2)
        { pushFrame(s,frames,depth,1,47,d.owner,int(row),f.time); continue; }
        if (f.mode == 0 && !activationConditions(s,row,f.time) && !(f.event == 0 && f64Less(d.duration,0) && passive != 0)) continue;
        if(d.kind==15 && f.event!=28 && d.budget>=0 && s.activations[WORLD_TEAM_BUDGET(s,row)]>=uint(d.budget)) continue;
        uint64_t recipientOrder=0;uint recipientMask=f.mode==19 ? uint(f.value) : d.recipients,enemyOrder=0;
        if(stackOperation(d.kind))
        {
            uint64_t order;
            if((f.event!=28 || (d.flags&1)!=0 && s.alive[row]==0) && d.budget>=0 && !stackLazySelector(s,row) && stackSelectedRecipients(s,row,f.target,f.time,true,order)==0) continue;
            recipientMask=d.kind>=19 ? stackSelectedRecipients(s,row,f.target,f.time,false,order) : 0;
        }
        if (f.mode!=19 && d.kind==22)
            recipientMask=f64Zero(d.value) ? 0 : selectRecipients(s,row,f.time,recipientOrder);
        if (f.mode!=19 && (WORLD_RELOAD_FORCE_KIND(d.kind) || d.kind == 0 || d.kind == 4 || d.kind == 5 || d.kind == 6 || d.kind == 7 || d.kind == 8 || d.kind == 13 || d.kind == 14 || d.kind == 24 || d.kind == 27 || d.kind == 31 || d.kind == 30 || d.kind==15 || d.kind==26))
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
        COUNTER_GUARD(s,row) bool stageRegister=s.stagedEnabled!=0 && isStaged(s,row) && (f.event!=28 || (d.flags&1)!=0 && s.alive[row]==0);
        if(stageRegister) { stagedTotal=stagedCount(s,row);if(s.error!=0) break;if(stagedTotal==0) continue; }
        if (f.mode!=19 && (f.event != 28 || (d.flags & 1) != 0 && ((s.stagedEnabled==0 || !isStaged(s,row)) || stageRegister)))
        {
            if (d.budget >= 0 && s.activations[WORLD_TEAM_BUDGET(s,row)] >= uint(d.budget)) continue;
            if (s.activations[WORLD_TEAM_BUDGET(s,row)] == 0x7fffffff) { s.error = 2; break; }
            s.activations[WORLD_TEAM_BUDGET(s,row)]++;
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
        WORLD_FIELDS_FANOUT(s,frames,depth,d,row,f) if((d.kind==0 || d.kind==4) && d.enemyBuff!=0 && recipientMask!=0 && f.mode!=19 && (countbits(recipientMask)!=1 || s.hpPendingMask!=0 || s.hpDirtyMask!=0))
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
        WORLD_RELOAD_ACTIVATE(s,d,f.time) if (d.kind==35) { registerSource(s,row,f.time); continue; }
        if((WORLD_RELOAD_FORCE_KIND(d.kind) || d.kind==5 || d.kind==6 || d.kind==7 || d.kind==8 || d.kind==13 || d.kind==14 || d.kind==27 || d.kind==30 || d.kind==31) && commands[s.inputBase+P_RECIPIENT_BASE+row*8]==17)
        { pushFrame(s,frames,depth,24,0,d.owner,int(row),f.time,recipientOrder);continue; }
        if (d.kind == 0 || d.kind == 4)
        {
            uint sourceRow=row; uint64_t duration = d.duration; bool activationLazy = d.lazyGroup != 0;
            if(!activationLazy) { recipientMask=filterHarmful(s,d,recipientMask,recipientOrder);if(d.polarity==2 && recipientMask==0) continue; }
            uint capturedGeneration=d.enemyBuff!=0 && recipientMask!=0 ? (f.mode==19 ? f.repeatPassive : s.targetGeneration[firstbithigh(recipientMask>>5)]) : 0;
            row = findCarrier(s,row,recipientMask,f.time,capturedGeneration,recipientOrder);
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
            else { s.activeRecipients[row] = recipientMask; storeCarrierOrder(s,row,recipientOrder); }
            if(!live || d.maxStack!=1) s.stacks[row] = checkedStackIncrement(s.stacks[row],d.maxStack,s.error);
            if (s.error!=0) break;
            WORLD_FIELDS_BIND(s,row,d,f) s.alive[row] = 1; s.activated[row] = f.time;
            s.end[row] = f64Less(duration,0) ? F64_INF : f64Add(f.time,duration);
            if(activationLazy && d.stat==S_heal_overcharge_store)
            {
                uint object=protectionObject(s,row);
                if(object!=PROTECTION_NONE) results[protectionAddress(s,object)+22]|=STORAGE_PENDING;
            }
            COUNTER_PREPARE(s,row,f.time) if (d.enemyBuff != 0) s.enemyCaptureGeneration[row] = capturedGeneration;
            if (d.bulletDuration != 0) prepareBulletActivation(s,row,recipientMask,live,activationLazy,previousStack);
            bool namedCandidate = (d.buffEvent & 1) != 0 && (!live || d.maxStack != 1) && s.namedEventOwners != 0;
#ifdef PORTABLE_BUFF_AUDIENCE_SCAN_REFERENCE
            uint64_t audienceOrder = buffAudienceOrder(s,row);
#else
            uint64_t audienceOrder = namedCandidate ? buffAudienceOrder(s,row) : 0;
#endif
            bool namedNotice = namedCandidate && (s.namedEventOwners & packedRecipientMask(audienceOrder)) != 0;
            bool stackNotice = (d.buffEvent & 1) != 0 && previousStack != s.stacks[row] && (s.stackEventOwners & (1U << d.owner)) != 0;
            if (live && !namedNotice && !stackNotice) captureBuffReference(s,row,sourceRow);
            if (namedNotice || stackNotice || (d.buffEvent >> 2) != 0 || immunityPolicy(s.inputBase,sourceRow)==3 || (protectionPolicy(s,sourceRow)&255)==1 || (protectionPolicy(s,sourceRow)&255)==2 || (protectionPolicy(s,sourceRow)&255)==9)
            {
                pushFrame(s,frames,depth,13,0,d.owner,int(row),f.time,d.enemyBuff!=0 ? uint64_t(recipientMask&~31U)<<16 : recipientOrder);
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
        else if(d.kind==27 || d.kind==31)
        {
            uint kind=d.kind==27 ? 1 : 2;
            if(!f64Zero(d.value)) for(uint i=0;i<5;i++)
            {
                uint encoded=(recipientOrder>>(i*3))&7;if(encoded==0) break;uint who=encoded-1;
                uint64_t basis=d.healthScaling!=0 ? effectiveMaxHP(s,d.owner,f.time) : protectionCapacity(s,who,kind);
                uint64_t amount=f64Div(f64Mul(basis,d.value),HUNDRED);
                if(!f64Finite(amount)) { s.error=16;break; }
                healProtection(s,who,kind,amount,f.time);
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
                    s.hp[who] = storageBodyReduce(s,who,d.value,f.time);
                syncHealth(s,f.time);
            }
        }
        else if (d.kind == 5) reduceBurstReady(s,recipientMask,d.value,f.time);
        else if (d.kind == 22) reduceSkillCooldown(s,recipientMask,d.value,f.time);
        else if (d.kind == 24) { if (recipientMask != 0) addBurstGauge(s,d.value); }
        WORLD_RELOAD_DISPATCH(s,d,recipientOrder,f.time) else if (d.kind == 13 || d.kind == 14)
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
        else if (d.kind==26) WORLD_CLEANSE(s,row,recipientMask,f.time);
        else if (d.kind == 33) pushFrame(s,frames,depth,2,0,d.owner,int(row),f.time);
        else if (d.kind == 3)
        { WORLD_SKILL_SCOPE_BEGIN(s)
            if (f.event != 28) s.stacks[row] = 1;
            if (d.damagePending != 0) enqueuePendingBurst(s,row,f.time);
            else
            {
                uint64_t coefficient=activationDamageCoefficient(s,row);
                uint hits=f64Zero(coefficient) ? 0 : activationHitCount(s,row);
                if (s.error==0) pushFrame(s,frames,depth,10,0,d.owner,int(row),f.time);
                if (s.error==0)
                {
                    frames[depth].repeatLeft=hits; frames[depth].healthValue=coefficient;
                    // Native skill damage captures buffs before named-hit children.
                    // Unlike physical firing, later callbacks do not resample this gain.
                    if(hits!=0 && (s.quantityMask & 128)!=0) frames[depth].gaugeFlat=readStat(s,d.owner,S_burst_charge_speed_pct,f.time);
                }
            } WORLD_SKILL_SCOPE_END(s)
        }
        else s.error = 32;
#ifdef PORTABLE_HEALTH_SCAN_REFERENCE
        if((s.healthMask&32)==0) syncHealth(s,f.time);
#else
        // Reference/stack-derived HP flushes after all synchronous children.
        if (d.kind == 1 && (s.healthMask&32)==0) syncHealth(s,f.time);
#endif
    }
    COUNTER_FIELDS_WORK_RECORD(s,work) WORLD_TEAM_END(s) COUNTER_CONTEXT_END(s) WORLD_STATE_DISPATCH_END(s) s.target = entryTarget;
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
            if (f64Less(next,when) || f64Equal(when,next))
            { dispatch(s,0,6,definition_owner(s.inputBase,j),int(j),when,output); s.periodDue[j] = f64Add(next,interval); }
        }
    timerPass(s,when,false,output); syncHealth(s,when); syncCovers(s,when);
    if (s.hpWatchCount != 0) dispatch(s,7,0,0,0,when,output);
}

#include "bullet_consume.slang"
#ifdef PORTABLE_WORLD_ACTOR_POOLS
#include "world_actor_pools.slang"
#ifdef PORTABLE_WORLD_ACTOR_FIELDS
#include "world_actor_fields.slang"
#ifdef PORTABLE_WORLD_ACTOR_STATE
#include "world_actor_state.slang"
#ifdef PORTABLE_WORLD_ACTOR_MUTATION
#include "world_actor_mutation.slang"
#ifdef PORTABLE_WORLD_ACTOR_RECIPIENTS
#include "world_actor_recipients.slang"
#ifdef PORTABLE_WORLD_ACTOR_STATUS
#include "world_actor_status.slang"
#ifdef PORTABLE_WORLD_ACTOR_STACKS
#include "world_actor_stacks.slang"
#ifdef PORTABLE_TARGET_COUNTERS
#include "target_counter_runtime.slang"
#ifdef PORTABLE_WORLD_PROJECTILE
#include "world_projectile_runtime.slang"
#endif
#ifdef PORTABLE_COUNTER_LANDINGS
#include "counter_landing_runtime.slang"
#ifdef PORTABLE_COUNTER_CONTEXT
#include "counter_context_runtime.slang"
#ifdef PORTABLE_COUNTER_FIELDS
#include "counter_field_runtime.slang"
#ifdef PORTABLE_WORLD_SKILLS
#include "world_skill_runtime.slang"
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#define WORLD_POOL_INIT(s,output) if(!initializeActorPools(s)) { results[output]=64;return; }
#define WORLD_POOL_COMMAND(s,at) WORLD_FIELDS_COMMAND(s,at) else if(op>=34 && op<=38) { if(!actorPoolCommand(s,op,step,when)) { s.error=64;break; } }
#else
#define WORLD_POOL_INIT(s,output) WORLD_FIELDS_INIT(s,output)
#define WORLD_POOL_COMMAND(s,at)
#endif
#ifdef PORTABLE_WORLD_ACTORS
#include "world_actor_registry.slang"
#define WORLD_ACTORS_INIT(s,output) if(!initializeWorldActors(s)) { results[output]=64;return; }
#define WORLD_ACTOR_COMMAND(s,at) else if(op==33) { uint kind=commands[at+3],identity=commands[at+4],generation=commands[at+5],root=commands[at+6],query=commands[at+7]; if(kind>5 || identity>=0x10000000U || generation==0 || generation>=0x80000000U || root>1 || query>=P_COMMANDS || !worldActorsEnabled(s)) { s.error=64;break; } worldActorQuery(s,kind,identity,generation,root,query); }
#else
#define WORLD_ACTORS_INIT(s,output)
#define WORLD_ACTOR_COMMAND(s,at)
#endif
#ifdef PORTABLE_WORLD_FRAME
#include "world_frame_runtime.slang"
#endif
#include "combat_runtime.slang"

#include "admission_runtime.slang"
#include "portable_mt19937.slang"
#include "enemy_target_runtime.slang"

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if (id.x >= commands[0]) return;
    uint input = 1 + id.x*P_INPUT_WORDS, output = id.x*P_OUTPUT_WORDS; WORLD_TEAM_INPUT(input,output)
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
    if(!validGeometry(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,4) admitDefinitions(s,input);
    if (s.error != 0) { results[output] = s.error; return; }
    PROJECTILE_ADMIT_STAGE(s,5) if(!initializeWorldFrame(s)) { results[output]=64;return; } PROJECTILE_ADMIT_STAGE(s,6) WORLD_OVERLAY_INIT(s,output) PROJECTILE_ADMIT_STAGE(s,7) WORLD_ACTORS_INIT(s,output) PROJECTILE_ADMIT_STAGE(s,8) WORLD_POOL_INIT(s,output) PROJECTILE_ADMIT_STAGE(s,9) WORLD_FIELDS_INIT(s,output) PROJECTILE_ADMIT_STAGE(s,10) WORLD_STATE_INIT(s,output) PROJECTILE_ADMIT_STAGE(s,11) COUNTER_INIT(s,output)
    PROJECTILE_ADMIT_STAGE(s,12) if(!validEnemyTargeting(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,13) if(!validProtection(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,14) if (!validStatusDefinitions(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,15) if (!validStackDefinitions(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,16) if (!validEventCandidates(s)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,17) for (uint row = 0; row < s.count; row++) if (!validPendingDefinition(s,row)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,18) if (!validateDurationGroups(s)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,19) if (!validatePeriodicDefinitions(s)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,20) if (!initializeResources(s) || !validateReferences(s)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,22) if (!initializeSources(s)) { results[output]=64; return; }
    PROJECTILE_ADMIT_STAGE(s,23) if(!initializeStaged(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,24) if (!initializeLandings(s)) { results[output]=64;return; }
    for(uint word=0;word<P_PROBABILITY_STATE_WORDS;word++) results[output+P_PROBABILITY_STATE_BASE+word]=0;
    if(commands[input+P_ENEMY_TARGET_META_BASE]!=0) mtSeed(output+P_ENEMY_RNG_BASE,uint64_t(commands[input+P_ENEMY_TARGET_META_BASE+1])|(uint64_t(commands[input+P_ENEMY_TARGET_META_BASE+2])<<32));
    initializeHPWatches(s);
    uint queries = 0;
    for (uint step = 0; step < commands[input+2] && s.error == 0; step++)
    {
        uint at = input+P_COMMAND_BASE+step*8, op = commands[at]; uint64_t when = loadNumber(at+1);
        if (s.combat == 0 || op == 4) { beginLazyRoot(s,when); sampleWorld(s); }
        if (op == 4 && s.combat != 0 && s.combatStarted == 0)
        { s.combatStarted = 1; teamNotify(s,0,when,output); WORLD_INITIAL_SPAWN_START(s,when,output) initializeMagazines(s,when); }
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
        WORLD_ACTOR_COMMAND(s,at) WORLD_POOL_COMMAND(s,at) WORLD_FIELDS_COMMAND(s,at) WORLD_STATE_COMMAND(s,at) COUNTER_COMMAND(s,at) else if (op == 26)
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
        else if(op==32)
        {
            uint raw=s.inputBase+P_INCOMING_BASE+step*P_INCOMING_WORDS;
            if(commands[at+3]>1 || commands[at+4]!=0 || commands[at+5]!=0 || commands[at+6]!=0 || commands[at+7]!=0 || !f64Finite(loadNumber(raw)) || !f64Finite(loadNumber(raw+2)) || f64Less(loadNumber(raw),0) || f64Less(loadNumber(raw+2),0) || f64Less((uint64_t(0x46293e59)<<32)|uint64_t(0x39a08cea),loadNumber(raw)) || f64Less(f64FromI64(1000000),loadNumber(raw+2))) { s.error=64;break; }
            dispatch(s,8,0,0,int(step),when,output);
        }
        else if(op==31)
        {
            uint raw=s.inputBase+P_INCOMING_BASE+step*P_INCOMING_WORDS;
            if(commands[at+3]>1 || commands[at+4]>31 || commands[at+5]==0 || commands[at+5]>31 || commands[at+6]!=0 || commands[at+7]!=0 || !f64Finite(loadNumber(raw)) || !f64Finite(loadNumber(raw+2)) || f64Less(loadNumber(raw),0) || f64Less(loadNumber(raw+2),0) || f64Less((uint64_t(0x46293e59)<<32)|uint64_t(0x39a08cea),loadNumber(raw)) || f64Less(f64FromI64(1000000),loadNumber(raw+2))) { s.error=64;break; }
            dispatch(s,8,0,0,int(step),when,output);
        }
        else if (op == 25) dispatch(s,8,0,0,int(step),when,output);
        else if (op == 24 && s.combat != 0) { advanceCombat(s,when,output); WORLD_SKILL_FINAL(s,when,output) }
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
            WORLD_PHYSICAL_BEGIN(s,who,target,amount) if (s.landingPolicy!=0) land(s,who,target,amount);
            if ((s.healthMask & 64) != 0 && s.error == 0) dispatch(s,17,0,who,0,when,output,amount); WORLD_GATE_END
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
            writeProtection(s,output+P_PROTECTION_QUERY_BASE+index*50);
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
    worldFrameFinish(s);
    writeDamageAccounting(s,output+P_DAMAGE_ACCOUNTING_STATE_BASE,true);
    writePendingBurst(s,output+P_PENDING_STATE_BASE,true);
    writeCovers(s,commands[input+2] > 0 ? loadNumber(input+P_COMMAND_BASE+(commands[input+2]-1)*8+1) : 0,output+P_COVER_STATE_BASE);
    writeIncoming(s,output+P_INCOMING_STATE_BASE);
    writeProtection(s,output+P_PROTECTION_STATE_BASE);
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
    if((s.quantityMask & 512)!=0) for(uint who=0;who<5;who++) storeNumber(output+P_MODE_ENTRY_STATE_BASE+who*2,s.modeEntryUntil[who]);
    results[output] = s.error; results[output+1] = queries; results[output+2] = s.traceCount; results[output+3] = s.maxDepth; results[output+4] = s.burstTraceCount; results[output+6] = s.traceTotal;
    results[output+7] = s.burstTraceTotal; results[output+8] = s.frameCount; WORLD_RELOAD_FINAL(s)
}
