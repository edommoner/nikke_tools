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
    s.pendingEnqueued++;
    s.pendingRow[index] = row; s.pendingCoefficient[index] = coefficient;
    s.pendingCastTime[index] = when; s.pendingHits[index] = d.pendingHits;
    s.pendingAmount[index] = 0;
}
void logPendingPacket(inout Runtime s,Definition d,uint row,uint index,uint hit,uint mask,uint order,uint64_t when,uint output)
{
    uint trace=s.traceCount;
    logDamagePacket(s,d,row,mask,0,hit+1,s.pendingAmount[index],s.pendingAmount[index],order,when,1,output);
    if(s.error==0 && s.traceMode==1)
    { uint at=output+P_PENDING_TRACE_BASE+trace*4;results[at]=1;storeNumber(at+1,s.pendingCastTime[index]); }
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
    for (uint index = 0; index < count && s.error == 0; index++)
    {
        uint row = s.pendingRow[index]; Definition d = readDefinition(s.inputBase,row); d.damageHits = s.pendingHits[index];
        for (uint hit = 0; hit < d.damageHits && s.error == 0 && !f64Zero(s.pendingAmount[index]); hit++)
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
                WORLD_SKILL_BEGIN(s,d.owner,target,s.pendingAmount[index]) if(recovery) s.target=target;land(s,d.owner,target,s.pendingAmount[index]);
                if(recovery && s.error==0) dispatch(s,17,0,d.owner,0,when,output,s.pendingAmount[index]); WORLD_GATE_END
            }
            if(!recovery) logPendingPacket(s,d,row,index,hit,mask,packedOrder,when,output);
        }
        if (s.pendingFired == 0x7fffffff) { s.error = 2; break; }
        s.pendingFired++;
    }
    s.damageExclusion = 0;s.target=parentTarget;
    if (s.error == 0)
    {
        // Native clears its captured batch before landing. Children queued by
        // recovery survive for the next B3 collection rather than being lost.
        uint tail=s.pendingCount-count;
        for(uint i=0;i<tail;i++)
        { s.pendingRow[i]=s.pendingRow[count+i];s.pendingHits[i]=s.pendingHits[count+i];s.pendingCoefficient[i]=s.pendingCoefficient[count+i];s.pendingCastTime[i]=s.pendingCastTime[count+i];s.pendingAmount[i]=s.pendingAmount[count+i]; }
        s.pendingCount=tail;
    }
}
void writePendingBurst(inout Runtime s, uint output, bool entries)
{
    results[output] = s.pendingCount; results[output+1] = s.pendingEnqueued; results[output+2] = s.pendingFired;
    if (entries) for (uint index = 0; index < s.pendingCount; index++)
    {
        uint at = output+4+index*8; results[at] = s.pendingRow[index];
        storeNumber(at+1,s.pendingCastTime[index]); storeNumber(at+3,s.pendingCoefficient[index]);
        results[at+5] = s.pendingHits[index]; storeNumber(at+6,s.pendingAmount[index]);
    }
}
