// Decoder-only probe; frozen v41 semantics are checked independently on host.
#include "event_runtime.slang"
[shader("compute")]
[numthreads(1,1,1)]
void definitionInputProbe(uint3 thread : SV_DispatchThreadID)
{
    uint id=thread.x;if(id>=commands[0]) return;
    uint input=1+id*P_INPUT_WORDS,output=id*15616U;
    for(uint row=0;row<P_DEFINITIONS;row++)
    {
        Definition d=readDefinition(input,row);
        uint at=output+row*61U;
        results[at+0U]=uint(d.owner);
        results[at+1U]=uint(d.kind);
        results[at+2U]=uint(d.stat);
        results[at+3U]=uint(d.name);
        results[at+4U]=uint(d.maxStack);
        results[at+5U]=uint(d.budget);
        storeNumber(at+6U,d.value);
        storeNumber(at+8U,d.duration);
        storeNumber(at+10U,d.interval);
        results[at+12U]=uint(d.immediate);
        results[at+13U]=uint(d.preserve);
        results[at+14U]=uint(d.event);
        results[at+15U]=uint(d.threshold);
        results[at+16U]=uint(d.countMode);
        results[at+17U]=uint(d.eventName);
        results[at+18U]=uint(d.targetName);
        results[at+19U]=uint(d.recipients);
        results[at+20U]=uint(d.target);
        results[at+21U]=uint(d.stageArg);
        results[at+22U]=uint(d.stageOverride);
        results[at+23U]=uint(d.reentry);
        results[at+24U]=uint(d.toggle);
        results[at+25U]=uint(d.triggerCount);
        results[at+26U]=uint(d.conditionCount);
        results[at+27U]=uint(d.flags);
        storeNumber(at+28U,d.period);
        results[at+30U]=uint(d.damageFlags);
        results[at+31U]=uint(d.group);
        results[at+32U]=uint(d.exclusive);
        results[at+33U]=uint(d.quantityFlags);
        results[at+34U]=uint(d.fixedLiteral);
        results[at+35U]=uint(d.polarity);
        results[at+36U]=uint(d.alias);
        storeNumber(at+37U,d.fixedValue);
        results[at+39U]=uint(d.damageRoute);
        results[at+40U]=uint(d.damageCount);
        results[at+41U]=uint(d.damageHits);
        results[at+42U]=uint(d.damageNormal);
        results[at+43U]=uint(d.damagePending);
        results[at+44U]=uint(d.pendingHits);
        storeNumber(at+45U,d.damageGauge);
        results[at+47U]=uint(d.bulletDuration);
        results[at+48U]=uint(d.bulletBound);
        results[at+49U]=uint(d.durationGroup);
        results[at+50U]=uint(d.durationCast);
        results[at+51U]=uint(d.periodicFlags);
        results[at+52U]=uint(d.periodicGroup);
        results[at+53U]=uint(d.healthScaling);
        results[at+54U]=uint(d.alliedFlags);
        results[at+55U]=uint(d.buffEvent);
        results[at+56U]=uint(d.enemyBuff);
        results[at+57U]=uint(d.mergeEligible);
        results[at+58U]=uint(d.statKey);
        results[at+59U]=uint(d.lazyGroup);
        results[at+60U]=uint(d.queryResolve);
    }
}
