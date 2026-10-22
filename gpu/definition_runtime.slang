// Immutable definitions are views of the existing input wire, never replay state.
// Keep one decoder for admission and every CUDA/Metal execution consumer.
[noinline]
void loadDefinition(uint input,uint row,out Definition d)
{ d._wireInput=input;d._wireRow=row;d._overrideMask=0;d._route=0;d._hits=0; }
// Inline only the tiny view wrapper. The decoder writes caller storage,
// avoiding a large by-value function result on the Metal backend.
[ForceInline]
Definition readDefinition(uint input,uint row)
{
    Definition d;loadDefinition(input,row,d);return d;
}

[ForceInline]
uint definition_owner(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_OWNER]; }

[ForceInline]
uint definition_kind(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_KIND]; }

[ForceInline]
uint definition_stat(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_STAT]; }

[ForceInline]
uint definition_name(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_NAME]; }

[ForceInline]
uint definition_maxStack(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_MAX_STACK]; }

[ForceInline]
int definition_budget(uint input,uint row) { return int(commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_BUDGET]); }

[ForceInline]
uint64_t definition_value(uint input,uint row) { return loadNumber((input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_VALUE); }

[ForceInline]
uint64_t definition_duration(uint input,uint row) { return loadNumber((input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_DURATION); }

[ForceInline]
uint64_t definition_interval(uint input,uint row) { return loadNumber((input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_INTERVAL); }

[ForceInline]
uint definition_immediate(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_IMMEDIATE]; }

[ForceInline]
uint definition_preserve(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_PRESERVE]; }

[ForceInline]
uint definition_event(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_EVENT]; }

[ForceInline]
uint definition_threshold(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_THRESHOLD]; }

[ForceInline]
uint definition_countMode(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_COUNT_MODE]; }

[ForceInline]
int definition_eventName(uint input,uint row) { return int(commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_EVENT_NAME]); }

[ForceInline]
int definition_targetName(uint input,uint row) { return int(commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_TARGET_NAME]); }

[ForceInline]
uint definition_recipients(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_RECIPIENTS]; }

[ForceInline]
uint definition_target(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_TARGET]; }

[ForceInline]
uint definition_stageArg(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_STAGE_ARG]; }

[ForceInline]
uint definition_stageOverride(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_STAGE_OVERRIDE]; }

[ForceInline]
uint definition_reentry(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_REENTRY]; }

[ForceInline]
uint definition_toggle(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_TOGGLE]; }

[ForceInline]
uint definition_triggerCount(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_TRIGGER_COUNT]; }

[ForceInline]
bool validStatAbovePredicate(uint stat,uint64_t threshold)
{ return (stat==0 || stat==5 || stat==6 || stat==21) && f64Finite(threshold); }

uint definition_conditionCount(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_CONDITION_COUNT]; }

[ForceInline]
uint definition_flags(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_FLAGS]; }

[ForceInline]
uint64_t definition_period(uint input,uint row) { return loadNumber((input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_PERIOD); }

[ForceInline]
uint definition_damageFlags(uint input,uint row) { return commands[(input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS)+D_DAMAGE_FLAGS]; }

[ForceInline]
uint definition_group(uint input,uint row) { return commands[(input+P_DEFINITION_EXTRA_BASE+row*P_DEFINITION_EXTRA_WORDS)]; }

[ForceInline]
uint definition_exclusive(uint input,uint row) { return commands[(input+P_DEFINITION_EXTRA_BASE+row*P_DEFINITION_EXTRA_WORDS)+1]; }

[ForceInline]
uint definition_quantityFlags(uint input,uint row) { return commands[(input+P_DEFINITION_EXTRA_BASE+row*P_DEFINITION_EXTRA_WORDS)+3]; }

[ForceInline]
uint definition_fixedLiteral(uint input,uint row) { return commands[(input+P_DEFINITION_EXTRA_BASE+row*P_DEFINITION_EXTRA_WORDS)+6]; }

[ForceInline]
uint definition_polarity(uint input,uint row) { return commands[(input+P_DEFINITION_EXTRA_BASE+row*P_DEFINITION_EXTRA_WORDS)+7]; }

[ForceInline]
int definition_alias(uint input,uint row) { return int(commands[(input+P_DEFINITION_EXTRA_BASE+row*P_DEFINITION_EXTRA_WORDS)+2]); }

[ForceInline]
uint64_t definition_fixedValue(uint input,uint row) { return loadNumber((input+P_DEFINITION_EXTRA_BASE+row*P_DEFINITION_EXTRA_WORDS)+4); }

[ForceInline]
uint definition_damageRoute(uint input,uint row) { return commands[(input+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS)]; }

[ForceInline]
uint definition_damageCount(uint input,uint row) { return commands[(input+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS)+1]; }

[ForceInline]
uint definition_damageHits(uint input,uint row) { return commands[(input+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS)+2]; }

[ForceInline]
uint definition_damageNormal(uint input,uint row) { return commands[(input+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS)+3]; }

[ForceInline]
uint definition_damagePending(uint input,uint row) { return commands[(input+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS)+6]; }

[ForceInline]
uint definition_pendingHits(uint input,uint row) { return commands[(input+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS)+7]; }

[ForceInline]
uint64_t definition_damageGauge(uint input,uint row) { return loadNumber((input+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS)+4); }

[ForceInline]
uint definition_bulletDuration(uint input,uint row) { return commands[(input+P_BULLET_DEFINITION_BASE+row*2)]; }

[ForceInline]
uint definition_bulletBound(uint input,uint row) { return commands[(input+P_BULLET_DEFINITION_BASE+row*2)+1]; }

[ForceInline]
uint definition_durationGroup(uint input,uint row) { return commands[(input+P_DURATION_DEFINITION_BASE+row*2)]; }

[ForceInline]
uint definition_durationCast(uint input,uint row) { return commands[(input+P_DURATION_DEFINITION_BASE+row*2)+1]; }

[ForceInline]
uint definition_periodicFlags(uint input,uint row) { return commands[(input+P_PERIODIC_DEFINITION_BASE+row*2)]; }

[ForceInline]
uint definition_periodicGroup(uint input,uint row) { return commands[(input+P_PERIODIC_DEFINITION_BASE+row*2)+1]; }

[ForceInline]
uint definition_healthScaling(uint input,uint row) { return commands[(input+P_HEALTH_DEFINITION_BASE+row*P_HEALTH_DEFINITION_WORDS)]; }

[ForceInline]
uint definition_alliedFlags(uint input,uint row) { return commands[(input+P_HEALTH_DEFINITION_BASE+row*P_HEALTH_DEFINITION_WORDS)+1]; }

[ForceInline]
uint definition_buffEvent(uint input,uint row) { return commands[(input+P_HEALTH_DEFINITION_BASE+row*P_HEALTH_DEFINITION_WORDS)+2]; }

[ForceInline]
uint definition_enemyBuff(uint input,uint row) { return commands[(input+P_HEALTH_DEFINITION_BASE+row*P_HEALTH_DEFINITION_WORDS)+3]; }

[ForceInline]
uint definition_mergeEligible(uint input,uint row) { return commands[input+P_RECIPIENT_BASE+row*8+7] & 3; }

[ForceInline]
uint definition_statKey(uint input,uint row) { return commands[input+P_RECIPIENT_BASE+row*8+6]; }

[ForceInline]
uint definition_lazyGroup(uint input,uint row) { return commands[input+P_RECIPIENT_BASE+row*8+7] >> 4; }

[ForceInline]
uint definition_queryResolve(uint input,uint row) { return (commands[input+P_RECIPIENT_BASE+row*8+7] >> 2) & 1; }
