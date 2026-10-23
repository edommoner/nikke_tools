// B3 plain bonus damage captures its coefficient at activation, then calculates
// every queued packet after full-burst buffs and before any queued landing.
bool validPendingDefinition(inout Runtime s, uint row)
{
    Definition d = readDefinition(s.inputBase,row);
    if (d.damagePending != 0)
    {
        bool cast = false;
        for (uint slot = 0; slot < d.triggerCount; slot++)
            if (commands[s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8] == 3) cast = true;
        if (d.kind != 3 || !cast) return false;
    }
    uint at = s.inputBase+P_PENDING_EXCLUDE_BASE+row*P_MASK_WORDS;
    for (uint word = 0; word < P_MASK_WORDS; word++)
    {
        uint bits = commands[at+word];
        if (bits == 0) continue;
        if (d.damagePending == 0 && bits != 0) return false;
        for (uint bit = 0; bit < 32; bit++) if ((bits & (1U << bit)) != 0)
        {
            uint target = word*32+bit;
            if (target >= s.count) return false;
            if (definition_owner(s.inputBase,target) != d.owner || definition_kind(s.inputBase,target) != 0 && definition_kind(s.inputBase,target) != 4) return false;
        }
    }
    return true;
}
void enqueuePendingBurst(inout Runtime s, uint row, uint64_t when)
{
    Definition d = readDefinition(s.inputBase,row);
    if (f64Zero(d.value)) return;
    uint64_t coefficient = namedDamageCoefficient(s,row,d.value,when); // capture before deferral
    if (!f64Finite(coefficient)) { s.error = 16; return; }
    if (s.pendingCount == P_PENDING) { s.error = 64; return; }
    if (s.pendingEnqueued == 0x7fffffff) { s.error = 2; return; }
    uint index = s.pendingCount++;
#ifdef PORTABLE_FULL_BURST_LANDING
    if(d.damagePending==1)
#endif
    s.pendingEnqueued++;
    s.pendingRow[index] = row; s.pendingCoefficient[index] = coefficient;
    s.pendingCastTime[index] = when; s.pendingHits[index] = d.pendingHits;
#ifdef PORTABLE_FULL_BURST_LANDING
    if(d.damagePending==2) s.pendingHits[index]=fullBurstLandingCount(s,row);
#endif
    s.pendingAmount[index] = 0;
}
// Stage the captured batch in the existing serialized-pending output bank.
// Generation keeps its live queue; landing callbacks see only the unconsumed tail.
uint pendingBatchAddress(inout Runtime s,uint index)
{ return s.resourceOutput+P_PENDING_STATE_BASE+4+index*8; }
uint pendingBatchRow(inout Runtime s,uint index)
{
#ifdef PORTABLE_FULL_BURST_LANDING
    return results[pendingBatchAddress(s,index)];
#else
    return s.pendingRow[index];
#endif
}
uint pendingBatchHits(inout Runtime s,uint index)
{
#ifdef PORTABLE_FULL_BURST_LANDING
    return results[pendingBatchAddress(s,index)+5];
#else
    return s.pendingHits[index];
#endif
}
uint64_t pendingBatchAmount(inout Runtime s,uint index)
{
#ifdef PORTABLE_FULL_BURST_LANDING
    return sourceNumber(pendingBatchAddress(s,index)+6);
#else
    return s.pendingAmount[index];
#endif
}
uint64_t pendingBatchTime(inout Runtime s,uint index)
{
#ifdef PORTABLE_FULL_BURST_LANDING
    return sourceNumber(pendingBatchAddress(s,index)+1);
#else
    return s.pendingCastTime[index];
#endif
}
#ifdef PORTABLE_FULL_BURST_LANDING
void stagePendingBatch(inout Runtime s,uint count)
{
    for(uint i=0;i<count;i++)
    {
        uint at=pendingBatchAddress(s,i);results[at]=s.pendingRow[i];
        storeNumber(at+1,s.pendingCastTime[i]);storeNumber(at+3,s.pendingCoefficient[i]);
        results[at+5]=s.pendingHits[i];storeNumber(at+6,s.pendingAmount[i]);
    }
}
void releasePendingBatch(inout Runtime s,uint count)
{
    uint retained=0;
    for(uint i=count;i<s.pendingCount;i++)
    {
        if(definition_damagePending(s.inputBase,s.pendingRow[i])==2) continue;
        s.pendingRow[retained]=s.pendingRow[i];s.pendingHits[retained]=s.pendingHits[i];
        s.pendingCoefficient[retained]=s.pendingCoefficient[i];s.pendingCastTime[retained]=s.pendingCastTime[i];
        s.pendingAmount[retained]=s.pendingAmount[i];retained++;
    }
    s.pendingCount=retained;
}
#endif
void logPendingPacket(inout Runtime s,Definition d,uint row,uint index,uint hit,uint mask,uint order,uint64_t when,uint output)
{
    uint trace=s.traceCount;
    logDamagePacket(s,d,row,mask,0,hit+1,pendingBatchAmount(s,index),pendingBatchAmount(s,index),order,when,1,output);
    if(s.error==0 && s.traceMode==1)
    { uint at=output+P_PENDING_TRACE_BASE+trace*4;results[at]=1;storeNumber(at+1,pendingBatchTime(s,index)); }
}
[noinline]
void firePendingBursts(inout Runtime s, uint64_t when, uint output)
{
    uint parentTarget=s.target;
    uint count = s.pendingCount;
    // Capture all amounts before routing/landing can change target state.
    for (uint index = 0; index < count && s.error == 0; index++)
    {
        uint row = s.pendingRow[index]; Definition d = readDefinition(s.inputBase,row);
#ifdef PORTABLE_FULL_BURST_LANDING
        if(d.damagePending==2) continue;
#endif
#ifndef PORTABLE_PENDING_RECALCULATE_REFERENCE
        // No event is dispatched during this calculation phase. Repeated
        // adjacent definitions with the same captured coefficient share it.
        if (index != 0 && row == s.pendingRow[index-1] && f64Equal(s.pendingCoefficient[index],s.pendingCoefficient[index-1]))
        { s.pendingAmount[index] = s.pendingAmount[index-1]; continue; }
#endif
        uint64_t coefficient=s.pendingCoefficient[index];
        if(f64Zero(coefficient))
        {
            // Native queries buffs before skipping a zero captured coefficient.
            uint target=s.target;s.target=0;s.damageExclusion=row+1;
            WORLD_PENDING_SCOPE_BEGIN(s)
            uint64_t ignored[64];collectStats(s,d.owner,when,ignored);
            uint64_t enemy[3];collectEnemyModifiers(s,d.owner,0,when,enemy);
            WORLD_PENDING_SCOPE_END(s)
            s.damageExclusion=0;s.target=target;s.pendingAmount[index]=0;continue;
        }
        uint reference=s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4;
        if((commands[reference]&3)==1)
        {
            bool present;uint64_t scale=referenceCount(s,d.owner,(commands[reference+1]&511)-1,commands[reference+2]&255,false,present);
            coefficient=f64Mul(coefficient,present ? scale : 0);
            if(!f64Finite(coefficient)) { s.error=16;return; }
            if(f64Zero(coefficient)) { s.pendingAmount[index]=0;continue; }
        }
        uint target = s.target; s.target = 0; s.damageExclusion = row+1;
        WORLD_PENDING_SCOPE_BEGIN(s) s.pendingAmount[index] = damageValue(s,d.owner,coefficient,when,false,s.coreBonus); WORLD_PENDING_SCOPE_END(s)
        s.damageExclusion = 0; s.target = target;
    }
#ifdef PORTABLE_FULL_BURST_LANDING
    stagePendingBatch(s,count);
    uint fullBegin,fullEnd;generateFullBurstLandings(s,when,output,fullBegin,fullEnd);
    if(s.error==0) releasePendingBatch(s,count);
#endif
    for (uint index = 0; index < count && s.error == 0; index++)
    {
        uint row = pendingBatchRow(s,index); Definition d = readDefinition(s.inputBase,row); d.damageHits = pendingBatchHits(s,index);
#ifdef PORTABLE_FULL_BURST_LANDING
        if(d.damagePending==2) continue;
#endif
        for (uint hit = 0; hit < d.damageHits && s.error == 0 && !f64Zero(pendingBatchAmount(s,index)); hit++)
        {
            WORLD_PENDING_LAND(s,d,row,index,hit,when,output) uint packedOrder; uint inherited = aimedTarget(s,d.owner);
            uint mask = enemyDamageMask(s,d,inherited,packedOrder);
            if (mask == 0) break;
            bool recovery=(s.healthMask&64)!=0;
            if(recovery) logPendingPacket(s,d,row,index,hit,mask,packedOrder,when,output);
            for (uint pass = 0; pass < 8 && s.error==0; pass++)
            {
                uint encoded = (packedOrder >> (pass*4)) & 15; if (encoded == 0) break;
                uint target=encoded-1;if(recovery && s.targetAlive[target]==0) continue;
                WORLD_SKILL_BEGIN(s,d.owner,target,pendingBatchAmount(s,index)) if(recovery) s.target=target;land(s,d.owner,target,pendingBatchAmount(s,index));
                if(recovery && s.error==0) dispatch(s,17,0,d.owner,0,when,output,pendingBatchAmount(s,index)); WORLD_GATE_END
            }
            if(!recovery) logPendingPacket(s,d,row,index,hit,mask,packedOrder,when,output);
        }
        if (s.pendingFired == 0x7fffffff) { s.error = 2; break; }
        s.pendingFired++;
    }
#ifdef PORTABLE_FULL_BURST_LANDING
    if(s.error==0) landFullBurstRange(s,fullBegin,fullEnd,when,output);
#endif
    s.damageExclusion = 0;s.target=parentTarget;
    if (s.error == 0)
    {
#ifdef PORTABLE_FULL_BURST_LANDING
        for(uint i=0;i<count*8;i++) results[pendingBatchAddress(s,0)+i]=0;
#else
        // Native clears its captured batch before landing. Children queued by
        // recovery survive for the next B3 collection rather than being lost.
        uint tail=s.pendingCount-count;
        for(uint i=0;i<tail;i++)
        { s.pendingRow[i]=s.pendingRow[count+i];s.pendingHits[i]=s.pendingHits[count+i];s.pendingCoefficient[i]=s.pendingCoefficient[count+i];s.pendingCastTime[i]=s.pendingCastTime[count+i];s.pendingAmount[i]=s.pendingAmount[count+i]; }
        s.pendingCount=tail;
#endif
    }
}
void writePendingBurst(inout Runtime s, uint output, bool entries)
{
    uint logicalCount=s.pendingCount;
#ifdef PORTABLE_FULL_BURST_LANDING
    logicalCount=0;for(uint i=0;i<s.pendingCount;i++) if(definition_damagePending(s.inputBase,s.pendingRow[i])==1) logicalCount++;
#endif
    results[output] = logicalCount; results[output+1] = s.pendingEnqueued; results[output+2] = s.pendingFired;
#ifdef PORTABLE_FULL_BURST_LANDING
    // Private final-state diagnostic. Query word3 and all legacy fields retain
    // their old meaning. Entries remain legacy-first in the existing512 slots.
    if(entries) results[output+3]=s.pendingCount-logicalCount;
#endif
    uint logicalIndex=0;
    if (entries) for (uint index = 0; index < s.pendingCount; index++)
    {
        #ifdef PORTABLE_FULL_BURST_LANDING
        if(definition_damagePending(s.inputBase,s.pendingRow[index])==2) continue;
#endif
        uint at = output+4+logicalIndex++*8; results[at] = s.pendingRow[index];
        storeNumber(at+1,s.pendingCastTime[index]); storeNumber(at+3,s.pendingCoefficient[index]);
        results[at+5] = s.pendingHits[index]; storeNumber(at+6,s.pendingAmount[index]);
    }
#ifdef PORTABLE_FULL_BURST_LANDING
    if(entries) for(uint index=0;index<s.pendingCount;index++)
    {
        if(definition_damagePending(s.inputBase,s.pendingRow[index])!=2) continue;
        uint at=output+4+logicalIndex++*8;results[at]=s.pendingRow[index];
        storeNumber(at+1,s.pendingCastTime[index]);storeNumber(at+3,s.pendingCoefficient[index]);
        results[at+5]=s.pendingHits[index];storeNumber(at+6,s.pendingAmount[index]);
    }
#endif
}

#ifdef PORTABLE_FULL_BURST_LANDING
#include "full_burst_landing_runtime.slang"
#endif
