// Decoder-only probe; frozen v41 semantics are checked independently on host.
#include "event_runtime.slang"
[shader("compute")]
[numthreads(1,1,1)]
void definitionScalarProbe(uint3 thread : SV_DispatchThreadID)
{
    uint id=thread.x;if(id>=commands[0]) return;
    uint input=1+id*P_INPUT_WORDS,output=id*15616U;
    for(uint row=0;row<P_DEFINITIONS;row++)
    {
        // Each scalar accessor executes independently.
        uint at=output+row*61U;
        results[at+0U]=uint(definition_owner(input,row));
        results[at+1U]=uint(definition_kind(input,row));
        results[at+2U]=uint(definition_stat(input,row));
        results[at+3U]=uint(definition_name(input,row));
        results[at+4U]=uint(definition_maxStack(input,row));
        results[at+5U]=uint(definition_budget(input,row));
        storeNumber(at+6U,definition_value(input,row));
        storeNumber(at+8U,definition_duration(input,row));
        storeNumber(at+10U,definition_interval(input,row));
        results[at+12U]=uint(definition_immediate(input,row));
        results[at+13U]=uint(definition_preserve(input,row));
        results[at+14U]=uint(definition_event(input,row));
        results[at+15U]=uint(definition_threshold(input,row));
        results[at+16U]=uint(definition_countMode(input,row));
        results[at+17U]=uint(definition_eventName(input,row));
        results[at+18U]=uint(definition_targetName(input,row));
        results[at+19U]=uint(definition_recipients(input,row));
        results[at+20U]=uint(definition_target(input,row));
        results[at+21U]=uint(definition_stageArg(input,row));
        results[at+22U]=uint(definition_stageOverride(input,row));
        results[at+23U]=uint(definition_reentry(input,row));
        results[at+24U]=uint(definition_toggle(input,row));
        results[at+25U]=uint(definition_triggerCount(input,row));
        results[at+26U]=uint(definition_conditionCount(input,row));
        results[at+27U]=uint(definition_flags(input,row));
        storeNumber(at+28U,definition_period(input,row));
        results[at+30U]=uint(definition_damageFlags(input,row));
        results[at+31U]=uint(definition_group(input,row));
        results[at+32U]=uint(definition_exclusive(input,row));
        results[at+33U]=uint(definition_quantityFlags(input,row));
        results[at+34U]=uint(definition_fixedLiteral(input,row));
        results[at+35U]=uint(definition_polarity(input,row));
        results[at+36U]=uint(definition_alias(input,row));
        storeNumber(at+37U,definition_fixedValue(input,row));
        results[at+39U]=uint(definition_damageRoute(input,row));
        results[at+40U]=uint(definition_damageCount(input,row));
        results[at+41U]=uint(definition_damageHits(input,row));
        results[at+42U]=uint(definition_damageNormal(input,row));
        results[at+43U]=uint(definition_damagePending(input,row));
        results[at+44U]=uint(definition_pendingHits(input,row));
        storeNumber(at+45U,definition_damageGauge(input,row));
        results[at+47U]=uint(definition_bulletDuration(input,row));
        results[at+48U]=uint(definition_bulletBound(input,row));
        results[at+49U]=uint(definition_durationGroup(input,row));
        results[at+50U]=uint(definition_durationCast(input,row));
        results[at+51U]=uint(definition_periodicFlags(input,row));
        results[at+52U]=uint(definition_periodicGroup(input,row));
        results[at+53U]=uint(definition_healthScaling(input,row));
        results[at+54U]=uint(definition_alliedFlags(input,row));
        results[at+55U]=uint(definition_buffEvent(input,row));
        results[at+56U]=uint(definition_enemyBuff(input,row));
        results[at+57U]=uint(definition_mergeEligible(input,row));
        results[at+58U]=uint(definition_statKey(input,row));
        results[at+59U]=uint(definition_lazyGroup(input,row));
        results[at+60U]=uint(definition_queryResolve(input,row));
    }
}
