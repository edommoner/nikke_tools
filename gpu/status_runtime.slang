// Persona is presence in already-resolved active membership, just as native
// _has_persona_state. Do not resolve lazy carriers or evaluate value/conditions.
bool statusPersona(inout Runtime s,uint who)
{
    if(who>=5 || (s.quantityMask&16384)==0) return false;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]!=0 && s.lazyPending[slot]==0 && definition_kind(s.inputBase,definition)==4 &&
           (definition_quantityFlags(s.inputBase,definition)&1)!=0 && (s.activeRecipients[slot]&(1U<<who))!=0) return true;
    }
    return false;
}

// Presence reads the already-resolved carrier membership, without consuming a
// lazy selector or rechecking conditions/expiry ahead of the shared lifecycle.
// This is native _has_immune/is_stunned, distinct from numeric buff queries.
bool statusStunImmune(inout Runtime s,uint who)
{
    if(who>=133 || (s.incomingMask&16)==0) return false;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]!=0 && s.lazyPending[slot]==0 && definition_kind(s.inputBase,definition)==4 &&
           (definition_quantityFlags(s.inputBase,definition)&2)!=0 &&
           !WORLD_STATUS_MEMBER_INVALID(s,slot,who,(s.activeRecipients[slot]&(1U<<who))==0)) return true;
    }
    return false;
}
bool statusStunned(inout Runtime s,uint who)
{
    if(who>=133 || (s.incomingMask&8)==0 || statusStunImmune(s,who)) return false;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]!=0 && s.lazyPending[slot]==0 && definition_kind(s.inputBase,definition)==0 &&
           definition_stat(s.inputBase,definition)==S_stun &&
           !WORLD_STATUS_MEMBER_INVALID(s,slot,who,(s.activeRecipients[slot]&(1U<<who))==0)) return true;
    }
    return false;
}

// Status counters live in the shared output buffer, never private arrays.
uint immunityPolicy(uint input,uint row) { return (definition_flags(input,row)>>4)&3; }
uint64_t statusNumber(uint at) { return uint64_t(results[at])|(uint64_t(results[at+1])<<32); }
uint immunityUsed(inout Runtime s,uint who,uint name) { return WORLD_STATUS_USED(s,who,name,s.resourceOutput+P_IMMUNITY_USED_BASE+(who*P_DEFINITIONS+name)*2); }
void clearImmunityScratch(inout Runtime s,uint count)
{
    uint scratch=s.resourceOutput+P_IMMUNITY_SCRATCH_BASE;
    if(count<=64)
    {
        for(uint group=0;group<count;group++)
        {
            uint name=results[scratch+P_DEFINITIONS*3+group];
            results[scratch+name*2]=0;results[scratch+name*2+1]=0;
            results[scratch+P_DEFINITIONS*2+name]=0;results[scratch+P_DEFINITIONS*3+group]=0;
        }
    }
    else for(uint word=0;word<P_DEFINITIONS*4;word++) results[scratch+word]=0;
}
[noinline]
bool harmfulBlocked(inout Runtime s,uint who,Definition incoming)
{
    if((commands[s.inputBase+P_STATUS_META_BASE]&1)==0) return false;
    uint bit=WORLD_STATUS_BIT(s,who,1U<<who);
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot],policy=immunityPolicy(s.inputBase,definition);
        if(s.alive[slot]==0 || s.lazyPending[slot]!=0 || WORLD_STATUS_MEMBER_INVALID(s,slot,who,(s.activeRecipients[slot]&bit)==0)) continue;
        bool visible=WORLD_STATUS_VISIBLE(s,slot,who,who<5 || (s.targetAlive[who-5]!=0 && s.targetGeneration[who-5]==enemyCarrierGeneration(s,slot,who-5)));
        if(visible && (policy==1 || policy==2 && (incoming.buffEvent&1)!=0 && definition_targetName(s.inputBase,definition)==int(incoming.name))) return true;
    }
    if((commands[s.inputBase+P_STATUS_META_BASE]&2)==0) return false;
    uint scratch=s.resourceOutput+P_IMMUNITY_SCRATCH_BASE,count=0;
    // Native cap-dict insertion order is the first *valued* carrier per name.
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]==0 || s.lazyPending[slot]!=0 || WORLD_STATUS_COUNT_MEMBER_INVALID(s,slot,who,(s.activeRecipients[slot]&bit)==0) || immunityPolicy(s.inputBase,definition)!=3 || (definition_flags(s.inputBase,definition)&64)==0) continue;
        uint name=definition_name(s.inputBase,definition),seen=scratch+P_DEFINITIONS*2+name;
        if(results[seen]==0) { results[seen]=1;results[scratch+P_DEFINITIONS*3+count++]=name;storeNumber(scratch+name*2,0); }
        // _consume_immune_charge calls _get_value without a stack override.
        storeNumber(scratch+name*2,larger(statusNumber(scratch+name*2),scalarValue(s,slot,who<5 ? who : 0)));
    }
    bool blocked=false;
    for(uint group=0;group<count;group++)
    {
        uint name=results[scratch+P_DEFINITIONS*3+group],used=immunityUsed(s,who,name);
        if(f64Less(statusNumber(used),statusNumber(scratch+name*2)))
        { storeNumber(used,f64Add(statusNumber(used),ONE));blocked=true;break; }
    }
    clearImmunityScratch(s,count);return blocked;
}
[noinline]
uint filterHarmful(inout Runtime s,Definition d,uint mask,inout uint64_t order)
{
    if(d.polarity!=2 || (commands[s.inputBase+P_STATUS_META_BASE]&1)==0) return mask;
    WORLD_STATUS_FILTER(s,d,mask,order) uint kept=0,count=0;uint64_t packed=0;
    for(uint i=0;i<21;i++)
    {
        uint encoded=(order>>(i*3))&7;if(encoded==0) break;uint who=encoded-1;
        if(!harmfulBlocked(s,who,d)) { kept|=1U<<who;packed|=uint64_t(encoded)<<(count++*3); }
    }
    for(uint who=5;who<13;who++) if((mask&(1U<<who))!=0 && !harmfulBlocked(s,who,d)) kept|=1U<<who;
    order=packed;return kept;
}
void rechargeImmunity(inout Runtime s,uint definition,uint mask)
{
    if(immunityPolicy(s.inputBase,definition)!=3) return;
    uint name=definition_name(s.inputBase,definition);
    WORLD_STATUS_RECHARGE(s,definition,mask,name) for(uint who=0;who<13;who++) if((mask&(1U<<who))!=0) storeNumber(immunityUsed(s,who,name),0);
}
[noinline]
void cleanseResidents(inout Runtime s,uint row,uint scope)
{
    uint64_t value=definition_value(s.inputBase,row);uint limit=P_CARRIERS;
    if(f64Less(0,value) && f64Less(value,f64FromI64(P_CARRIERS)))
    { uint status;limit=max(1,uint(f64ToI64(value,1,status)));if(status!=0) { s.error=2;return; } }
    WORLD_STATUS_CLEANSE_BEGIN(s,row) for(uint who=0;who<WORLD_STATUS_CLEANSE_COUNT(s,13);who++)
    {
        uint bit=WORLD_STATUS_BIT(s,who,1U<<who),taken=0;if(WORLD_STATUS_CLEANSE_SCOPE_MISS(s,scope,who,(scope&bit)==0)) continue;
        for(uint pass=0;pass<s.orderedCount && taken<limit;pass++)
        {
            uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];Definition d=readDefinition(s.inputBase,definition);
            if(s.alive[slot]==0 || d.polarity!=2 || s.lazyPending[slot]!=0) continue;
            uint members=removalMembers(s,slot);
            if(WORLD_STATUS_MEMBER_INVALID(s,slot,who,(members&bit)==0)) continue;
            taken++;
            // Dispel is silent, retaining timer clocks and independent maps.
            s.activeRecipients[slot]=WORLD_STATUS_CLEANSE_MEMBERS(s,slot,who,bit,s.activeRecipients[slot]&~bit);
            storeCarrierOrder(s,slot,filterRemovalOrder(carrierOrder(s,slot),s.activeRecipients[slot]&31,3,21));
            if(s.activeRecipients[slot]==0) { unlinkBulletCarrier(s,slot);discardLazy(s,slot);s.alive[slot]=0;s.stacks[slot]=0; }
        }
    } WORLD_STATUS_CLEANSE_END(s)
}
[noinline]
bool validStatusDefinitions(inout Runtime s)
{
    uint expected=0;
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);uint policy=immunityPolicy(s.inputBase,row);
        if(policy!=0)
        {
            if(d.kind!=4 || d.stat!=0 || d.name>=P_DEFINITIONS || !f64Finite(d.value) || (d.flags&8)!=0) return false;
            if(policy==2 ? d.targetName<0 || d.targetName>=int(P_DEFINITIONS) : d.targetName!=-1) return false;
            if(policy==3 && (d.flags&64)==0 && !f64Zero(d.value)) return false;
            expected|=1;if(policy==3) expected|=2;
        }
        if((d.flags&64)!=0 && policy!=3) return false;
        if(d.kind!=26) continue;
        expected|=4;
        if(d.target<1 || d.target>2 || !f64Finite(d.value) || d.enemyBuff!=0 || d.buffEvent!=0) return false;
        uint recipient=s.inputBase+P_RECIPIENT_BASE+row*8;
        if(d.target==1) { if(!validRecipientPlan(recipient,false,s.inputBase) || commands[recipient+7]!=0) return false; }
        else for(uint word=0;word<8;word++) if(commands[recipient+word]!=0) return false;
        uint packet=s.inputBase+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS;
        if(d.target==2)
        {
            if(s.combat==0 || !validEnemyRoute(s.inputBase,d.damageRoute) || d.damageCount==0 || d.damageCount>256) return false;
            for(uint word=2;word<8;word++) if(commands[packet+word]!=0) return false;
        }
        else for(uint word=0;word<8;word++) if(commands[packet+word]!=0) return false;
        s.healthMask|=32;
    }
    for(uint word=1;word<8;word++) if(commands[s.inputBase+P_STATUS_META_BASE+word]!=0) return false;
    return commands[s.inputBase+P_STATUS_META_BASE]==expected;
}
