// Nonweapon MODE records form a tagged static union; no new state arrays.
static const uint STACK_META_MAGIC=0x53544b31;
bool stackOperation(uint kind) { return kind>=16 && kind<=21; }
uint stackMeta(inout Runtime s,uint row) { return s.inputBase+P_MODE_BASE+row*P_MODE_WORDS; }
uint64_t stackLiteralDuration(inout Runtime s,uint row) { return loadNumber(stackMeta(s,row)+2); }
bool stackLazySelector(inout Runtime s,uint row)
{ uint kind=commands[s.inputBase+P_RECIPIENT_BASE+row*8];return kind==5 || kind==6 || kind==7 || kind==15 || kind==16; }
[noinline]
uint stackSelectedRecipients(inout Runtime s,uint row,uint target,uint64_t when,bool budget,out uint64_t order)
{
    Definition d=readDefinition(s.inputBase,row);
    if(d.target==1) return selectRecipients(s,row,when,order);
    WORLD_STACK_SELECT(s,d,order)
    if(budget && d.kind!=19 && d.damageRoute==0) d.damageRoute=6;
    uint enemyOrder;uint mask=enemyDamageMask(s,d,target,enemyOrder)<<5;order=enemyOrder;return mask;
}
[noinline]
uint stackImmunity(inout Runtime s)
{
    uint mask=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]!=0 && s.lazyPending[slot]==0 && (definition_flags(s.inputBase,definition)&8)!=0) mask|=WORLD_STACK_IMMUNITY_MEMBERS(s,slot,removalMembers(s,slot));
    }
    return mask;
}
void setCarrierStack(inout Runtime s,uint slot,uint value)
{
    invalidateFocusNumeric(s);
    s.stacks[slot]=value;
    uint flags=referenceCaptureFlags(s,slot);
    if((flags&2)!=0) storeReferenceCapture(s,slot,flags,f64FromI64(value));
}
void refreshStackDuration(inout Runtime s,uint slot,uint64_t when)
{
    uint64_t duration=stackLiteralDuration(s,s.carrierDefinition[slot]);
    if(s.end[slot]!=F64_INF && duration!=F64_INF && f64Less(0,duration))
    { s.activated[slot]=when;s.end[slot]=f64Add(when,duration); }
}
[noinline]
void mutateStacks(inout Runtime s,uint row,uint scope,uint64_t when)
{
    Definition d=readDefinition(s.inputBase,row);uint immunity=stackImmunity(s);
    bool own=d.kind==16 || d.kind==17,maximum=d.kind==19;
    if(own && (immunity&(1U<<d.owner))!=0) return;
    scope&=~immunity;if(maximum) scope&=31;
    if(!own && scope==0) return;
    uint policy=maximum ? 0 : 1;uint64_t value=d.value;
    if(d.kind==20 || d.kind==21)
    {
        uint ref=s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4;
        if((commands[ref]&3)!=0)
        {
            bool present;uint64_t count=referenceCount(s,d.owner,(commands[ref+1]&511)-1,commands[ref+2]&255,false,present);
            if(present) { value=count;policy=0; }
        }
    }
    if(d.kind==17 || d.kind==21) policy|=2;
    uint numericStatus;uint64_t delta=stackIntegerDelta(value,policy,numericStatus);
    if(numericStatus!=0) { s.error=numericStatus;return; }
    if(maximum && !f64Less(0,delta)) return;
    WORLD_STACK_SCOPE_BEGIN(s,row,d,own,maximum) for(uint pass=0;pass<s.orderedCount && s.error==0;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]==0) continue;
        Definition carrier=readDefinition(s.inputBase,definition);
        uint members=removalMembers(s,slot),floor=1;
        if(own)
        { if(carrier.name!=uint(d.targetName) || (members&(1U<<d.owner))==0) continue; }
        else if(maximum)
        {
            if(commands[stackMeta(s,definition)+1]!=1 || carrier.polarity!=1 || carrier.maxStack==1) continue;
            if(s.lazyPending[slot]!=0) { uint64_t order;members=selectRecipients(s,definition,when,order); }
            if((members&scope)==0 || (members&~scope)!=0) continue;
        }
        else
        {
            if(d.targetName>=0) { if(carrier.name!=uint(d.targetName)) continue;floor=0; }
            else if(carrier.polarity!=2 || carrier.maxStack<=1 || carrier.maxStack==0xffffffff) continue;
            if(WORLD_STACK_SCOPE_MISS(s,slot,scope,(members&scope)==0)) continue;
        }
        uint64_t previous=carrierStackValue(s,slot);
        uint next=checkedStackChange(previous,delta,carrier.maxStack,floor,0,s.error);
        if(s.error!=0) return;
        setCarrierStack(s,slot,next);
        if(maximum && carrier.bulletDuration!=0 && s.bulletInitialized[slot]==1)
            for(uint who=0;who<5;who++)
            {
                uint at=slot*5+who;
                if(s.recipientStacks[at]!=0) s.recipientStacks[at]=checkedStackChange(f64FromI64(s.recipientStacks[at]),delta,carrier.maxStack,0,0,s.error);
                if(s.error!=0) return;
            }
        bool changed=!f64Equal(previous,f64FromI64(next));
        if((own && f64Less(0,delta)) || maximum && changed) refreshStackDuration(s,slot,when);
        if(changed && (maximum || own && f64Less(0,delta))) queueStackNotice(s,carrier.owner,carrier.name,next);
    } WORLD_STACK_SCOPE_END(s)
}
[noinline]
uint initializeStack(inout Runtime s,uint row,uint target,uint64_t when)
{
    Definition operation=readDefinition(s.inputBase,row);
    uint selected=commands[stackMeta(s,row)+4];if(selected==0) return P_CARRIERS;
    uint numericStatus;uint64_t count=stackIntegerDelta(operation.value,1,numericStatus);
    if(numericStatus!=0) { s.error=numericStatus;return P_CARRIERS; }
    if(!f64Less(0,count)) return P_CARRIERS;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];
        if(s.alive[slot]!=0 && definition_name(s.inputBase,s.carrierDefinition[slot])==uint(operation.targetName) && s.lazyPending[slot]==0 && (s.activeRecipients[slot]&(1U<<operation.owner))!=0) return P_CARRIERS;
    }
    uint definition=selected-1;Definition d=readDefinition(s.inputBase,definition);
    uint stack=checkedStackChange(0,count,d.maxStack,0,0,s.error);
    if(s.error!=0) return P_CARRIERS;
    uint slot=definition;
    if(s.alive[slot]!=0)
    {
        for(slot=s.count;slot<s.carrierCount;slot++) if(s.alive[slot]==0) break;
        if(slot==s.carrierCount) { if(slot==P_CARRIERS) { s.error=64;return P_CARRIERS; } s.carrierCount++; }
        s.multiCarrier[definition]=1;
    }
    resetBulletCarrier(s,slot);discardLazy(s,slot);s.carrierDefinition[slot]=definition;
    s.activeRecipients[slot]=0;storeCarrierOrder(s,slot,0);s.hpSnapshot[slot]=0;
    s.activated[slot]=when;uint64_t duration=stackLiteralDuration(s,definition);
    s.end[slot]=duration==F64_INF ? F64_INF : f64Add(when,duration);
    s.stacks[slot]=stack;s.bulletLeft[slot]=-1;
    if(d.lazyGroup!=0) { s.lazyPending[slot]=1;s.lazyPendingCount++;s.lazyMappedPendingCount+=d.queryResolve; }
    else if(d.enemyBuff!=0) WORLD_RECIPIENT_STACK_INIT(s,slot,d,target)
    {
        if(d.damageRoute==0) d.damageRoute=6;
        uint order;s.activeRecipients[slot]=enemyDamageMask(s,d,target,order)<<5;
        // Native initialization creates ONE shared enemy carrier. Enemy fields
        // never have bullet lifetimes; reuse their otherwise-unused 5+5 words.
        s.bulletInitialized[slot]=2;s.enemyCaptureGeneration[slot]=countbits(s.activeRecipients[slot])==1 ? s.targetGeneration[firstbithigh(s.activeRecipients[slot]>>5)] : 0;
        for(uint enemy=0;enemy<8;enemy++)
            if(enemy<5) s.recipientBullets[slot*5+enemy]=((s.activeRecipients[slot]&(1U<<(enemy+5)))!=0 ? s.targetGeneration[enemy] : 0);
            else s.recipientStacks[slot*5+enemy-5]=((s.activeRecipients[slot]&(1U<<(enemy+5)))!=0 ? s.targetGeneration[enemy] : 0);
    }
    else
    { uint64_t order;s.activeRecipients[slot]=selectRecipients(s,definition,when,order);storeCarrierOrder(s,slot,order); }
    storeReferenceCapture(s,slot,0,0);captureBuffReference(s,slot,definition);
    if(commands[stackMeta(s,definition)+5]!=0) storeReferenceCapture(s,slot,referenceCaptureFlags(s,slot)|4,referenceCaptureValue(s,slot));
    s.alive[slot]=1;markEntry(s,slot);prepareBaseCopy(s,slot,true);
    return slot;
}
[noinline]
bool validStackDefinitions(inout Runtime s)
{
    bool enabled=false;for(uint row=0;row<s.count;row++) enabled|=stackOperation(definition_kind(s.inputBase,row)) || ((definition_flags(s.inputBase,row)>>4)&3)!=0;
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        if(enabled && d.kind==0 && (d.stat>=S_max_hp_pct && d.stat<=S_max_hp_only_pct || d.stat==S_hp_copy)) s.healthMask|=32;
        if((d.flags&8)!=0 && d.kind!=4) return false;
        if(!enabled || d.kind==2) continue;
        uint meta=stackMeta(s,row);
        if(commands[meta]!=STACK_META_MAGIC || commands[meta+1]!=uint(d.kind==0 || d.kind==4 || d.kind==19)) return false;
        uint64_t duration=loadNumber(meta+2);if(!f64Finite(duration) && duration!=F64_INF) return false;
        uint selected=commands[meta+4];
        if(d.kind!=18 && selected!=0 || selected>s.count) return false;
        uint runtime=uint(commands[meta+1]!=0 && duration==F64_INF && (d.flags&2)!=0);
        if(commands[meta+5]!=runtime) return false;
        for(uint field=6;field<P_MODE_WORDS;field++)
        {
#ifdef PORTABLE_NAMED_ENEMY
            // MODE24..27 belongs to the named-enemy descriptor. Its tag,
            // symbol, flags and route are checked by initializeActorState.
            if(field>=24 && field<28) continue;
#endif
            if(!(skillHPBasisMode(s,row)!=0&&field>=20&&field<24) && !(triggerReducer(s,row)&&field<P_TRIGGER_REDUCTION_END) && !(namedSkillInterval(s,row)&&field<P_SKILL_INTERVAL_END) && !(baseCopyDefinition(s,row)&&field<P_BASE_COPY_END) && commands[meta+field]!=0) return false;
        }
        if(d.kind==18)
        {
            uint expected=0;
            for(uint other=0;other<s.count;other++)
                if(d.targetName>=0 && definition_owner(s.inputBase,other)==d.owner && definition_name(s.inputBase,other)==uint(d.targetName) && (definition_kind(s.inputBase,other)==0 || definition_kind(s.inputBase,other)==4 || definition_kind(s.inputBase,other)==19) && commands[stackMeta(s,other)+1]==1) { expected=other+1;break; }
            if(selected!=expected) return false;
        }
        if(!stackOperation(d.kind)) continue;
        if(d.target<1 || d.target>2 || d.targetName< -1 || d.targetName>=int(P_DEFINITIONS) || !f64Finite(d.value)) return false;
        uint recipients=s.inputBase+P_RECIPIENT_BASE+row*8;
        if(d.target==1) { if(!validRecipientPlan(recipients,false,s.inputBase) || commands[recipients+7]!=0) return false; }
        else if(d.enemyBuff!=0) { if(!validRecipientPlan(recipients,true,s.inputBase)) return false; }
        else for(uint field=0;field<8;field++) if(commands[recipients+field]!=0) return false;
        uint packet=s.inputBase+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS;
        if(d.target==2)
        {
            if(s.combat==0 || !validEnemyRoute(s.inputBase,d.damageRoute) || d.damageCount==0 || d.damageCount>256) return false;
            for(uint field=2;field<8;field++) if(commands[packet+field]!=0) return false;
        }
        else for(uint field=0;field<8;field++) if(commands[packet+field]!=0) return false;
    }
    return true;
}
