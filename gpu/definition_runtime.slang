// Immutable definitions are views of the existing input wire, never replay state.
// Keep one decoder for admission and every CUDA/Metal execution consumer.
[noinline]
void loadDefinition(uint input,uint row,out Definition d)
{
    d.owner=definition_owner(input,row);
    d.kind=definition_kind(input,row);
    d.stat=definition_stat(input,row);
    d.name=definition_name(input,row);
    d.maxStack=definition_maxStack(input,row);
    d.budget=definition_budget(input,row);
    d.value=definition_value(input,row);
    d.duration=definition_duration(input,row);
    d.interval=definition_interval(input,row);
    d.immediate=definition_immediate(input,row);
    d.preserve=definition_preserve(input,row);
    d.event=definition_event(input,row);
    d.threshold=definition_threshold(input,row);
    d.countMode=definition_countMode(input,row);
    d.eventName=definition_eventName(input,row);
    d.targetName=definition_targetName(input,row);
    d.recipients=definition_recipients(input,row);
    d.target=definition_target(input,row);
    d.stageArg=definition_stageArg(input,row);
    d.stageOverride=definition_stageOverride(input,row);
    d.reentry=definition_reentry(input,row);
    d.toggle=definition_toggle(input,row);
    d.triggerCount=definition_triggerCount(input,row);
    d.conditionCount=definition_conditionCount(input,row);
    d.flags=definition_flags(input,row);
    d.period=definition_period(input,row);
    d.damageFlags=definition_damageFlags(input,row);
    d.group=definition_group(input,row);
    d.exclusive=definition_exclusive(input,row);
    d.quantityFlags=definition_quantityFlags(input,row);
    d.fixedLiteral=definition_fixedLiteral(input,row);
    d.polarity=definition_polarity(input,row);
    d.alias=definition_alias(input,row);
    d.fixedValue=definition_fixedValue(input,row);
    d.damageRoute=definition_damageRoute(input,row);
    d.damageCount=definition_damageCount(input,row);
    d.damageHits=definition_damageHits(input,row);
    d.damageNormal=definition_damageNormal(input,row);
    d.damagePending=definition_damagePending(input,row);
    d.pendingHits=definition_pendingHits(input,row);
    d.damageGauge=definition_damageGauge(input,row);
    d.bulletDuration=definition_bulletDuration(input,row);
    d.bulletBound=definition_bulletBound(input,row);
    d.durationGroup=definition_durationGroup(input,row);
    d.durationCast=definition_durationCast(input,row);
    d.periodicFlags=definition_periodicFlags(input,row);
    d.periodicGroup=definition_periodicGroup(input,row);
    d.healthScaling=definition_healthScaling(input,row);
    d.alliedFlags=definition_alliedFlags(input,row);
    d.buffEvent=definition_buffEvent(input,row);
    d.enemyBuff=definition_enemyBuff(input,row);
    d.mergeEligible=definition_mergeEligible(input,row);
    d.statKey=definition_statKey(input,row);
    d.lazyGroup=definition_lazyGroup(input,row);
    d.queryResolve=definition_queryResolve(input,row);
}
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
