// Typed enemy recipients bind to the existing resident/stack/event executor.
// No duplicate activation,expiry,scalar arithmetic or carrier-name merge loop.
bool actorFieldsEnabled(inout Runtime s) { return actorPoolsEnabled(s); }
uint actorFieldScope(inout Runtime s,uint row,out ActorBits bits)
{
    bits=actorBitsEmpty();uint index=0;while(index<P_WORLD_ACTOR_SETS&&results[actorPoolSet(s,index)+5]!=0) index++;
    if(index==P_WORLD_ACTOR_SETS) { s.error=64;return index; }
    Definition d=readDefinition(s.inputBase,row);actorSetCapture(s,33,index,d.damageRoute,d.damageCount,s.target,d.owner NAMED_ENEMY_ARGUMENT(row));
    if(s.error==0) for(uint i=0;i<4;i++) bits.words[i]=results[actorPoolSet(s,index)+1+i];return index;
}
bool worldDurationAffected(inout Runtime s,uint row,ActorBits scope)
{
    for(uint target=0;target<actorPoolCount(s);target++)
        if(actorBitsHas(scope,target)&&(actorFieldMember(s,row,target==0?0:ACTOR_REF|target)
#ifdef PORTABLE_COORDINATE_ORIGINAL_SOURCE_OPS
            || worldPeriodicNamedMember(s,s.carrierDefinition[row],target)
#endif
        )) return true;
    return false;
}
uint actorFieldKey(inout Runtime s,uint row) { return s.resourceOutput+P_WORLD_ACTOR_FIELD_KEY_BASE+row*4; }
uint actorFieldHead(inout Runtime s) { return s.resourceOutput+P_WORLD_ACTOR_FIELDS_BASE; }
void actorFieldReset(inout Runtime s,uint row)
{ uint at=actorFieldKey(s,row);for(uint i=0;i<4;i++) results[at+i]=0; WORLD_RECIPIENT_RESET(s,row) }
void actorFieldBind(inout Runtime s,uint row,uint target,uint generation)
{ uint at=actorFieldKey(s,row);results[at]=(target&127U)+1;results[at+1]=generation; WORLD_RECIPIENT_BIND(s,row,target,generation) }
bool actorFieldSame(inout Runtime s,uint row,uint generation)
{ uint at=actorFieldKey(s,row);return WORLD_RECIPIENT_SAME(s,row,generation,results[at]==(s.target&127U)+1 && results[at+1]==generation); }
uint actorFieldLogicalSlot(inout Runtime s,uint target)
{ uint slot=(target&ACTOR_REF)!=0 ? target&127U : target;if(slot>=actorPoolCount(s)) return 128;uint kind=commands[actorBinding(s,slot)];return kind==1||kind==6 ? 0 : slot; }
bool actorFieldQueryLive(inout Runtime s,uint target)
{ uint slot=actorFieldLogicalSlot(s,target);return slot<actorPoolCount(s) && results[actorPoolAt(s,slot)+1]!=0; }
bool actorFieldMember(inout Runtime s,uint row,uint target)
{ uint slot=actorFieldLogicalSlot(s,target),at=actorFieldKey(s,row);return WORLD_RECIPIENT_MEMBER(s,row,target,WORLD_STATE_MEMBER(s,row,slot<128 && results[at]==slot+1 && results[at+1]==results[actorPoolAt(s,slot)])); }
bool actorFieldConditions(inout Runtime s,uint row,uint target,uint64_t when)
{ WORLD_STATE_SCOPE_BEGIN(s,target) uint saved=s.target,slot=actorFieldLogicalSlot(s,target);s.target=slot==0 ? 0 : ACTOR_REF|slot;bool ok=basicConditions(s,row,when,true);s.target=saved; WORLD_STATE_SCOPE_END(s) return ok; }
bool actorFieldContextAdd(inout Runtime s,uint who)
{
    if((s.target&ACTOR_REF)!=0) return COUNTER_CONTEXT_ADD(s,commands[actorBinding(s,s.target&127U)]==5);
    return COUNTER_CONTEXT_ADD(s,commands[actorBinding(s,actorPhysicalTarget(s,who,0)&127U)]==5);
}
bool actorFieldTargetMismatch(inout Runtime s,uint who,uint kind)
{ return kind==C_TARGET_BOSS && actorFieldContextAdd(s,who) || kind==C_TARGET_ADD && !actorFieldContextAdd(s,who); }
bool actorFieldsDefinitionValid(inout Runtime s,uint row,Definition d)
{
    WORLD_STATE_HEALTH_GUARD(s,d) if(WORLD_DURATION_KIND(s,d,WORLD_SKILL_KIND(s,row,d,COUNTER_FIELD_KIND(s,d,WORLD_MUTATION_KIND_INVALID(s,d,d.kind!=0&&d.kind!=2&&d.kind!=4))))) return false;
    for(uint i=0;i<d.conditionCount;i++)
    {
        uint at=s.inputBase+P_CONDITION_BASE+row*P_CONDITION_WORDS+i*4,kind=commands[at];uint64_t arg=loadNumber(at+2);
#ifdef PORTABLE_COORDINATE_ORIGINAL_SHIELD_HEAL
        if(kind==C_SHIELD)
        { if(s.combat==0 || commands[at+1]!=0 || !f64Zero(arg)) return false;continue; }
#endif
        if(kind==C_FOCUSING || kind==C_NO_BROKEN_COVER_ALLY)
        { if(!validStatePredicate(s.inputBase,row,at,s.combat)) return false;continue; }
        if(kind==C_SELF_UNDYING)
        { if(!validUndyingPredicate(s.inputBase,row,at,s.combat)) return false;continue; }
        if(kind==C_STAT_ABOVE)
        { if(!validStatAbovePredicate(commands[at+1],arg)) return false;continue; }
        if(kind==C_TARGET_STUNNED || kind==C_SELF_STUN_IMMUNE)
        { if(s.combat==0 || commands[at+1]!=0 || !f64Zero(arg)) return false;continue; }
        if(kind==C_NOT_CORE)
        {
#ifdef PORTABLE_NOT_CORE
            if(s.combat==0 || commands[at+1]!=0 || !f64Zero(arg)) return false;continue;
#else
            return false;
#endif
        }
#ifdef PORTABLE_BURST1_ALLY
        if(kind==C_BURST1_ALLY || kind==C_NO_BURST1_ALLY)
        { if(s.combat==0 || commands[at+1]!=0 || !f64Zero(arg)) return false;continue; }
#endif
        if(kind==C_CORE || kind==C_OPTIMAL_RANGE)
        { if(!hasRangeGeometry(s) || commands[at+1]!=0 || !f64Zero(arg)) return false;continue; }
        WORLD_TEAM_CONDITION(s,row,d,at,kind,arg) WORLD_ENEMY_ATTACK_ADMIT(s,d,at,kind,arg) WORLD_STATE_ADMIT_CONDITION(s,at,kind,arg) if(kind!=C_ENEMIES_ABOVE&&kind!=C_ENEMIES_BELOW&&kind!=C_TARGET_BOSS&&kind!=C_TARGET_ADD || commands[at+1]!=0 || !f64Finite(arg)) return false;
        if(kind==C_TARGET_BOSS||kind==C_TARGET_ADD) { if(!f64Zero(arg)) return false; }
        else { uint status;uint64_t value=f64ToI64(arg,1,status);if(status!=0||!f64Equal(arg,f64FromI64(value))||f64Less(f64FromI64(2147483647),f64Abs(arg))) return false; }
    }
    WORLD_STATUS_FIELD_GUARD(s,d) if(d.enemyBuff==0) return true;
    bool accumStat=false;
#ifdef PORTABLE_DAMAGE_ACCUM
    accumStat=d.stat>=81U && d.stat<=83U;
#endif
    if(WORLD_STATUS_FIELD_INVALID(s,d,d.kind!=0 || d.stat!=S_enemy_def_down_pct&&d.stat!=S_def_caster_based_pct&&d.stat!=S_received_dmg_pct&&!namedMagnitudeStat(d.stat)&&!accumStat&&!projectileCarrierStat(d.stat)) || d.bulletDuration!=0 || !f64Zero(d.interval) || d.lazyGroup!=0 || referenceScaleMode(s,row)!=0) return false;
    if(!validEnemyRoute(s.inputBase,d.damageRoute) || d.damageCount==0 || d.damageCount>256 || (d.buffEvent&2)!=0) return false;
    if(d.damageRoute==3) for(uint slot=1;slot<actorPoolCount(s);slot++)
        if(commands[actorBinding(s,slot)]==5 && commands[actorPoolDef(s,slot)]==3) return false; // Native max-HP rank has no HP for hit-only actors.
    return true;
}
bool initializeActorFields(inout Runtime s)
{
    uint head=actorFieldHead(s);for(uint i=0;i<P_WORLD_ACTOR_FIELDS_OUTPUT_WORDS-P_WORLD_ACTOR_POOL_OUTPUT_WORDS;i++) results[head+i]=0;
    WORLD_RECIPIENT_INIT(s) if(!actorFieldsEnabled(s)) return true;
    results[head]=0x57463031;return true;
}
uint64_t actorFieldRank(inout Runtime s,uint slot,uint route)
{
    if(route==9) return loadNumber(slot==0 ? s.inputBase+P_WORLD_ACTOR_POOL_INPUT_BASE+2 : actorPoolDef(s,slot)+9);
    uint p=actorPoolAt(s,slot),d=actorPoolDef(s,slot);
    if(route==3) return loadNumber(d+2);
    return commands[d]==3 ? f64FromI64(uint64_t(commands[d+1])-uint64_t(results[p+3])) : f64Add(loadNumber(d+2),actorNumber(p+4)^F64_SIGN);
}
[noinline]
void actorFieldSelectOrder(inout Runtime s,inout uint order[128],inout uint count,uint route,uint limit,uint inherited,uint who NAMED_ENEMY_PARAMETER)
{
#ifdef PORTABLE_NAMED_ENEMY
    if(route==11)
    {
        if(definition>=s.count) { s.error=64;return; }
        if(count<=1) { order[0]=0;count=1;namedEnemyTrace(s,definition,order,count);return; }
        uint written=0;for(uint i=0;i<count;i++) if(namedEnemyPresent(s,definition,order[i])) order[written++]=order[i];
        if(written==0) order[written++]=0;count=written;namedEnemyTrace(s,definition,order,count);return;
    }
#endif
    if(route==2) { count=min(count,limit);return; }
    if(route==10)
    {
        // Native does not sample when no add is alive, even for singleton body.
        if(count>1)
        { mtSampleSlots128(s.resourceOutput+P_ENEMY_RNG_BASE,order,count,limit);actorSortSpawnOrder(s,order,count); }
        else count=min(count,limit);
        return;
    }
    if(route==1) { order[0]=0;count=1;return; }
    uint first=COUNTER_FIELDS_FIRST(s,route,(inherited&ACTOR_REF)!=0 ? actorFieldLogicalSlot(s,inherited) : actorFieldLogicalSlot(s,actorPhysicalTarget(s,who,0)));
    if(route==0) { order[0]=first;count=first<128 ? 1 : 0;return; }
    if(route==6)
    {
        uint output[128],n=0;output[n++]=first;
        for(uint i=0;i<count;i++) if(order[i]!=first && order[i]!=0) output[n++]=order[i];
        if(first!=0) output[n++]=0;
        count=min(n,limit);for(uint i=0;i<count;i++) order[i]=output[i];return;
    }
    // Stable insertion keeps add birth order at equal ranks. Body's infinite
    // HP/zero-defense conventions are explicit;attack compares actual scalars.
    for(uint i=1;i<count;i++)
    {
        uint key=order[i],j=i;
        while(j>0)
        {
            uint prior=order[j-1];bool before=false;
            if(route==9) before=f64Less(actorFieldRank(s,prior,route),actorFieldRank(s,key,route));
            else if(route==5||route==8) before=prior==0 || key!=0 && route==5 && f64Less(actorFieldRank(s,key,route),actorFieldRank(s,prior,route));
            else before=key==0 || prior!=0 && (route==3||route==4) && f64Less(actorFieldRank(s,prior,route),actorFieldRank(s,key,route));
            if(!before) break;order[j]=prior;j--;
        }
        order[j]=key;
    }
    count=min(count,limit);
}
[noinline]
void beginActorFields(inout Runtime s,inout Frame frames[32],inout int depth,uint row,Frame parent)
{
    uint index=0;while(index<P_WORLD_ACTOR_SETS && results[actorPoolSet(s,index)+5]!=0) index++;
    if(index==P_WORLD_ACTOR_SETS) { s.error=64;return; }
    Definition d=readDefinition(s.inputBase,row);actorSetCapture(s,33,index,d.damageRoute,d.damageCount,parent.target,d.owner NAMED_ENEMY_ARGUMENT(row));
    if(s.error!=0) return;
    pushFrame(s,frames,depth,25,parent.event,d.owner,int(row),parent.time,index);
    if(s.error==0) results[actorFieldHead(s)+1]++;
}
[noinline]
void advanceActorFields(inout Runtime s,inout Frame frames[32],inout int depth)
{
    Frame f=frames[depth];uint index=uint(f.value),at=actorPoolSet(s,index);
    if(f.cursor>=results[at])
    { results[at+5]=0;results[actorPoolHead(s)+7]--;depth--;return; }
    uint entry=at+8+f.cursor*4,slot=results[entry],generation=results[entry+1];frames[depth].cursor++;
    // Do not re-resolve the frozen ID/generation after a synchronous child.
    pushFrame(s,frames,depth,19,f.event,f.owner,f.argument,f.time,32);
    if(s.error==0) { frames[depth].target=ACTOR_REF|slot;frames[depth].repeatPassive=generation; }
}
void actorFieldRead(inout Runtime s,uint who,uint kind,uint identity,uint generation,uint out,uint64_t when)
{
    for(uint i=0;i<16;i++) results[out+i]=0;
    uint slot,status=worldActorResolve(s,kind,identity,generation,slot);results[out]=status;
    if(status!=0) return;
    uint prior=s.target;s.target=kind==1||slot==0 ? 0 : ACTOR_REF|slot;
    ensureNativeNumeric(s,who,when);s.target=prior;
    results[out+1]=kind;results[out+2]=identity;results[out+3]=generation;results[out+4]=results[actorPoolAt(s,slot)+1];results[out+5]=s.enemySnapshot;
    uint64_t values[3];collectEnemyModifiers(s,who,kind==1||slot==0 ? 0 : ACTOR_REF|slot,when,values);
    for(uint i=0;i<3;i++) storeNumber(out+6+i*2,values[i]);
}
[noinline]
bool actorFieldCommand(inout Runtime s,uint at,uint op,uint64_t when)
{
    if(!actorFieldsEnabled(s)) return false;
    uint who=commands[at+3];if(who>=5) return false;
    if(op==39)
    {
        uint kind=commands[at+4],id=commands[at+5],gen=commands[at+6],index=commands[at+7];
        if(kind>5||id>=0x10000000U||gen==0||gen>=0x80000000U||index>=64) return false;
        actorFieldRead(s,who,kind,id,gen,s.resourceOutput+P_WORLD_ACTOR_FIELD_QUERY_BASE+index*16,when);
    }
    else
    {
        for(uint i=4;i<8;i++) if(commands[at+i]!=0) return false;
#ifdef PORTABLE_COORDINATE_ORIGINAL_COVER_REVIVE
        // The original battle has no finish-time get_buffs probe. Keep this
        // diagnostic actor snapshot under the same policy as writePortableQuery.
        // Explicit op39 queries retain their ordinary native query contract.
        uint diagnostic=results[s.resourceOutput+P_NATIVE_QUERY_BASE+9];
        if(nativeNumericEnabled(s)) results[s.resourceOutput+P_NATIVE_QUERY_BASE+9]=1;
#endif
        // The native finish observer reads enemy ATK before numeric fields.
        // That reader resolves pending caster-ATK membership even on allies.
        if(nativeNumericEnabled(s)) { WORLD_ENEMY_ATTACK_SNAPSHOT(s,when) }
        for(uint slot=0;slot<actorPoolCount(s);slot++)
        {
            uint b=actorBinding(s,slot),gen=results[actorPoolAt(s,slot)],out=s.resourceOutput+P_WORLD_ACTOR_FIELD_ALL_BASE+slot*12;
            // Queries have16 words;the all-Actor snapshot stores12. Last four
            // scratch words must never overwrite the next actor's record.
            uint scratch=actorFieldHead(s)+P_WORLD_ACTOR_FIELDS_OUTPUT_WORDS-P_WORLD_ACTOR_FIELDS_BASE-16;
            if(commands[b]==6) { for(uint i=0;i<12;i++) results[out+i]=0;results[out]=1; }
            else if(gen==0) { for(uint i=0;i<12;i++) results[out+i]=0;results[out]=2; }
            else { actorFieldRead(s,who,commands[b],commands[b+1],gen,scratch,when);for(uint i=0;i<12;i++) results[out+i]=results[scratch+i]; }
        }
        if(!nativeNumericEnabled(s)) { WORLD_ENEMY_ATTACK_SNAPSHOT(s,when) }
#ifdef PORTABLE_COORDINATE_ORIGINAL_COVER_REVIVE
        if(nativeNumericEnabled(s)) results[s.resourceOutput+P_NATIVE_QUERY_BASE+9]=diagnostic;
#endif
        results[actorFieldHead(s)+2]=actorPoolCount(s);
    }
    return true;
}
