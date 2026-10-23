// Objects outlive carrier retirement while one incoming hit holds references.
// At most512 live carriers +512 captured shield objects; no private arrays.
static const uint PROTECTION_NONE=0xffffffff;
static const uint PROTECTION_RESERVED=65536,PROTECTION_ENDED=131072;
uint protectionPolicy(inout Runtime s,uint definition) { return commands[s.inputBase+P_PROTECTION_DEFINITION_BASE+definition]; }
uint protectionAddress(inout Runtime s,uint object) { return s.resourceOutput+P_PROTECTION_OBJECT_BASE+object*P_PROTECTION_OBJECT_WORDS; }
uint64_t protectionNumber(uint at) { return uint64_t(results[at])|(uint64_t(results[at+1])<<32); }
uint protectionObject(inout Runtime s,uint slot)
{
    uint object=results[s.resourceOutput+P_PROTECTION_MAP_BASE+slot];
    if(object==0 || object>P_PROTECTION_OBJECTS || s.alive[slot]==0) return PROTECTION_NONE;
    uint at=protectionAddress(s,object-1);
    uint binding=21;
#ifdef PORTABLE_DAMAGE_ACCUM
    uint kind=results[at+22]&255U;if(kind==13 || kind==15 || kind==16) binding=6;
#endif
    return results[at+20]==s.entryOrder[slot] && results[at+binding]==slot ? object-1 : PROTECTION_NONE;
}
bool protectionObjectActive(inout Runtime s,uint object)
{
    uint at=protectionAddress(s,object),binding=21;
#ifdef PORTABLE_DAMAGE_ACCUM
    uint kind=results[at+22]&255U;if(kind==13 || kind==15 || kind==16) binding=6;
    if(kind==14 || kind==17) return false;
#endif
    uint slot=results[at+binding];
    return slot<P_CARRIERS && s.alive[slot]!=0 && results[at+20]!=0 && results[at+20]==s.entryOrder[slot] && results[s.resourceOutput+P_PROTECTION_MAP_BASE+slot]==object+1;
}
[noinline]
uint allocateProtection(inout Runtime s,uint slot,uint policy)
{
    uint object=protectionObject(s,slot);
    if(object==PROTECTION_NONE)
    {
        for(object=0;object<P_PROTECTION_OBJECTS;object++)
        { uint at=protectionAddress(s,object);if((results[at+22]&PROTECTION_RESERVED)==0 && !protectionObjectActive(s,object)) break; }
        if(object==P_PROTECTION_OBJECTS) { s.error=64;return PROTECTION_NONE; }
    }
    uint at=protectionAddress(s,object);
    for(uint word=0;word<20;word++) results[at+word]=0;
    results[at+20]=s.entryOrder[slot];results[at+21]=slot;
    results[at+22]=(results[at+22]&(PROTECTION_RESERVED|PROTECTION_ENDED))|policy;results[at+23]=0;
    results[s.resourceOutput+P_PROTECTION_MAP_BASE+slot]=object+1;
    return object;
}
[noinline]
bool hasProtection(inout Runtime s,uint who,uint kind)
{
    if(commands[s.inputBase+P_PROTECTION_META_BASE]==0) return false;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint object=protectionObject(s,s.orderedRows[pass]);if(object==PROTECTION_NONE) continue;
        uint at=protectionAddress(s,object);
        if((results[at+22]&255)==kind && f64Less(0,protectionNumber(at+who*4))) return true;
    }
    return false;
}
[noinline]
bool protectionMarker(inout Runtime s,uint who,uint kind,uint64_t when)
{
    if((commands[s.inputBase+P_PROTECTION_META_BASE]&(kind==4 ? 2U : 4U))==0) return false;
    for(uint pass=0;pass<s.orderedCount;pass++)
    { uint slot=s.orderedRows[pass];if((protectionPolicy(s,s.carrierDefinition[slot])&255)==kind && queryRecipient(s,slot,who,when)) return true; }
    return false;
}
[noinline]
uint64_t nextShieldAmplification(inout Runtime s,uint who,uint64_t when)
{
    if((commands[s.inputBase+P_PROTECTION_META_BASE]&8U)==0) return 0;
    uint64_t sum=0;uint bit=1U<<who;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];
        if((protectionPolicy(s,s.carrierDefinition[slot])&255)!=3 || !queryRecipient(s,slot,who,when)) continue;
        sum=f64Add(sum,scalarValue(s,slot,who));s.activeRecipients[slot]&=~bit;
        storeCarrierOrder(s,slot,filterRemovalOrder(carrierOrder(s,slot),s.activeRecipients[slot]&31,3,21));
        if(s.activeRecipients[slot]==0) { unlinkBulletCarrier(s,slot);discardLazy(s,slot);s.alive[slot]=0;s.stacks[slot]=0; }
    }
    return sum;
}
[noinline]
uint64_t buildProtection(inout Runtime s,uint slot,uint64_t when)
{
    Definition d=residentDefinition(s,slot);uint policy=protectionPolicy(s,s.carrierDefinition[slot]),kind=policy&255;
    uint mask=s.activeRecipients[slot]&31,scratch=s.resourceOutput+P_PROTECTION_BUILD_BASE;
    for(uint word=0;word<10;word++) results[scratch+word]=0;
    uint64_t amount=f64Div(f64Mul(effectiveMaxHP(s,d.owner,when),scalarValue(s,slot,d.owner)),HUNDRED);
    // Build every target snapshot before the first shield_applied callback.
    uint64_t order=carrierOrder(s,slot);
    for(uint i=0;i<21;i++)
    {
        uint encoded=(order>>(i*3))&7;if(encoded==0) break;uint who=encoded-1;
        uint64_t value=amount;
        if(kind==1) value=f64Mul(amount,f64Add(ONE,f64Div(nextShieldAmplification(s,who,when),HUNDRED)));
        if(!f64Finite(value)) { s.error=16;return 0; }
        storeNumber(scratch+who*2,value);
    }
    // Existing maps remain visible to HP predicates and next-shield amplitudes.
    uint object=allocateProtection(s,slot,policy|(d.owner<<10));if(s.error!=0) return 0;
    uint at=protectionAddress(s,object);
    for(uint who=0;who<5;who++)
    { uint64_t value=protectionNumber(scratch+who*2);storeNumber(at+who*4,value);storeNumber(at+who*4+2,value);results[scratch+who*2]=0;results[scratch+who*2+1]=0; }
    results[at+23]=mask;uint seen=0,written=0;uint64_t unique=0;
    for(uint i=0;i<21;i++) { uint encoded=(order>>(3*i))&7;if(encoded==0) break;uint bit=1U<<(encoded-1);if((seen&bit)==0) { seen|=bit;unique|=uint64_t(encoded)<<(3*written++); } }
    return kind==1 ? unique : 0;
}
[noinline]
uint64_t protectionCapacity(inout Runtime s,uint who,uint kind)
{
    uint64_t total=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint object=protectionObject(s,s.orderedRows[pass]);if(object==PROTECTION_NONE) continue;
        uint at=protectionAddress(s,object);if((results[at+22]&255)==kind) total=f64Add(total,protectionNumber(at+who*4+2));
    }
    return total;
}
[noinline]
void healProtection(inout Runtime s,uint who,uint kind,uint64_t amount,uint64_t when)
{
    if(!f64Less(0,amount)) return;
    // Stable decreasing activation time: equal-time healing follows active-list order.
    uint64_t ceiling=F64_INF;uint lowerOrder=0;
    for(uint iteration=0;iteration<P_CARRIERS;iteration++)
    {
        uint selected=PROTECTION_NONE,bestOrder=0;uint64_t latest=0;
        for(uint pass=0;pass<s.orderedCount;pass++)
        {
            uint slot=s.orderedRows[pass],object=protectionObject(s,slot);if(object==PROTECTION_NONE || !f64Less(when,s.end[slot])) continue;
            uint at=protectionAddress(s,object);if((results[at+22]&255)!=kind || (results[at+23]&(1U<<who))==0) continue;
            uint order=s.entryOrder[slot];uint64_t time=s.activated[slot];
            if(f64Less(ceiling,time) || f64Equal(time,ceiling) && order<=lowerOrder) continue;
            if(selected==PROTECTION_NONE || f64Less(latest,time) || f64Equal(latest,time) && order<bestOrder) { selected=object;latest=time;bestOrder=order; }
        }
        if(selected==PROTECTION_NONE) break;
        ceiling=latest;lowerOrder=bestOrder;uint at=protectionAddress(s,selected)+who*4;
        uint64_t current=protectionNumber(at),room=f64Add(protectionNumber(at+2),current^F64_SIGN);
        if(!f64Less(0,room)) continue;
        uint64_t put=smaller(room,amount);storeNumber(at,f64Add(current,put));amount=f64Add(amount,put^F64_SIGN);
        if(!f64Less(0,amount)) break;
    }
}
[noinline]
uint captureShields(inout Runtime s,uint who,uint64_t when,bool pierce)
{
    uint count=0;
    while(count<P_CARRIERS)
    {
        uint selected=PROTECTION_NONE,best=0;uint64_t latest=0;
        for(uint pass=0;pass<s.orderedCount;pass++)
        {
            uint slot=s.orderedRows[pass],object=protectionObject(s,slot);if(object==PROTECTION_NONE || !f64Less(when,s.end[slot])) continue;
            uint at=protectionAddress(s,object);if((results[at+22]&255)!=1 || (results[at+22]&PROTECTION_RESERVED)!=0 || !f64Less(0,protectionNumber(at+who*4))) continue;
            if(selected==PROTECTION_NONE || f64Less(latest,s.activated[slot]) || f64Equal(latest,s.activated[slot]) && best<s.entryOrder[slot]) { selected=object;latest=s.activated[slot];best=s.entryOrder[slot]; }
        }
        if(selected==PROTECTION_NONE) break;
        uint at=protectionAddress(s,selected);results[at+22]|=PROTECTION_RESERVED;
        results[s.resourceOutput+P_PROTECTION_SELECTION_BASE+count++]=selected;
        if(!pierce) break;
    }
    return count;
}
[noinline]
bool protectionEmpty(inout Runtime s,uint object)
{
    uint at=protectionAddress(s,object);
    for(uint who=0;who<5;who++) if(f64Less(0,protectionNumber(at+who*4))) return false;
    return true;
}
[noinline]
void endProtectionObject(inout Runtime s,uint object)
{
    if(!protectionObjectActive(s,object)) return;
    uint slot=results[protectionAddress(s,object)+21];queueCarrierEnd(s,slot);
}
[noinline]
void advanceProtectionHit(inout Runtime s,inout Frame frames[32],inout int depth)
{
    Frame f=frames[depth];uint command=incomingCommandAddress(s,uint(f.argument));
    if(f.event==0)
    {
        uint hit=s.resourceOutput+f.repeatPassive;
        storeNumber(hit,f.time);results[hit+2]=scheduledArgument(uint(f.argument))?results[hit+2]|1U:1U;storeNumber(hit+4,f.healthValue);
        bool automaticCover=commands[command]==32 ? f64Less(0,s.reloadUntil[f.owner]) : (commands[command+4]&(1U<<f.owner))!=0;
        bool covered=automaticCover && f64Less(0,s.coverHP[f.owner]) && !protectionMarker(s,f.owner,7,f.time);
        frames[depth].value=commands[command+3]|(uint(covered)<<1);results[hit+3]=frames[depth].value|(f.repeatPassive>=P_SPLIT_HIT_BASE ? f.owner<<3 : 0);
        frames[depth].repeatLeft=captureShields(s,f.owner,f.time,commands[command+3]!=0);frames[depth].event=1;return;
    }
    if(f.event==1)
    {
        if(f.cursor==f.repeatLeft) { frames[depth].event=2;return; }
        uint object=results[s.resourceOutput+P_PROTECTION_SELECTION_BASE+f.cursor],at=protectionAddress(s,object);frames[depth].cursor++;
        uint slot=results[at+21],owner=definition_owner(s.inputBase,s.carrierDefinition[slot]);
        // An orphaned captured object retains its caster through carrier reuse.
        owner=(results[at+22]>>10)&7;
        if(protectionMarker(s,owner,4,f.time)) { frames[depth].healthPrevious=f64Add(f.healthPrevious,f.healthValue);return; }
        uint64_t current=protectionNumber(at+f.owner*4),taken=smaller(current,f.healthValue);
        uint64_t left=f64Add(current,taken^F64_SIGN);storeNumber(at+f.owner*4,larger(0,left));
        frames[depth].healthPrevious=f64Add(f.healthPrevious,taken);
        if(!f64Less(0,left))
        {
            if((results[at+22]&256)!=0 && protectionEmpty(s,object)) results[at+22]|=PROTECTION_ENDED;
            syncHealth(s,f.time);pushFrame(s,frames,depth,0,43,f.owner,0,f.time);
        }
        return;
    }
    if(f.event==2)
    {
        if(f.repeatRow<f.repeatLeft)
        {
            uint object=results[s.resourceOutput+P_PROTECTION_SELECTION_BASE+f.repeatRow];frames[depth].repeatRow++;
            if((results[protectionAddress(s,object)+22]&PROTECTION_ENDED)!=0)
            {
                uint begin=s.removalCount;endProtectionObject(s,object);syncHealth(s,f.time);
                if(s.removalCount>begin) pushFrame(s,frames,depth,9,0,0,int(begin),f.time);
            }
            return;
        }
        for(uint i=0;i<f.repeatLeft;i++)
        { uint at=protectionAddress(s,results[s.resourceOutput+P_PROTECTION_SELECTION_BASE+i]);results[at+22]&=~(PROTECTION_RESERVED|PROTECTION_ENDED);results[s.resourceOutput+P_PROTECTION_SELECTION_BASE+i]=0; }
        frames[depth].event=3;return;
    }
    if(f.event==3)
    {
        bool pierce=(f.value&1)!=0,covered=(f.value&2)!=0;uint64_t cover=0;
        if((pierce || !f64Less(0,f.healthPrevious)) && covered)
        {
            cover=smaller(s.coverHP[f.owner],f.healthValue);s.coverHP[f.owner]=f64Add(s.coverHP[f.owner],cover^F64_SIGN);
            s.coverDamage[f.owner]=f64Add(s.coverDamage[f.owner],cover);
#ifdef PORTABLE_WORLD_FRAME
            if(f64Less(0,cover) && f64Zero(s.coverHP[f.owner]) && scheduledArgument(uint(f.argument)))
                worldCoverBreakLog(s,uint(f.argument)&31U,f.time);
#endif
        }
        frames[depth].healthNext=cover;
        uint64_t amount=pierce || !f64Less(0,f.healthPrevious) && !f64Less(0,cover) ? f.healthValue : 0;
        if(f64Less(0,amount) && !covered)
        {
            uint selected=PROTECTION_NONE,best=0;uint64_t latest=0;
            for(uint pass=0;pass<s.orderedCount;pass++)
            {
                uint slot=s.orderedRows[pass],object=protectionObject(s,slot);if(object==PROTECTION_NONE || !f64Less(f.time,s.end[slot])) continue;
                uint at=protectionAddress(s,object);if((results[at+22]&255)!=2 || !f64Less(0,protectionNumber(at+f.owner*4))) continue;
                if(selected==PROTECTION_NONE || f64Less(latest,s.activated[slot]) || f64Equal(latest,s.activated[slot]) && best<s.entryOrder[slot]) { selected=object;latest=s.activated[slot];best=s.entryOrder[slot]; }
            }
            if(selected!=PROTECTION_NONE)
            {
                uint at=protectionAddress(s,selected)+f.owner*4;uint64_t current=protectionNumber(at),taken=smaller(current,amount);
                storeNumber(at,larger(0,f64Add(current,taken^F64_SIGN)));storeNumber(s.resourceOutput+f.repeatPassive+10,taken);amount=0;frames[depth].healthValue=0;frames[depth].event=4;
                if(protectionEmpty(s,selected)) { uint begin=s.removalCount;endProtectionObject(s,selected);syncHealth(s,f.time);if(s.removalCount>begin) pushFrame(s,frames,depth,9,0,0,int(begin),f.time); }
                return;
            }
        }
        frames[depth].healthValue=amount;frames[depth].event=4;return;
    }
    if(depth<1) { s.error=64;return; }
    uint hit=s.resourceOutput+f.repeatPassive;
    storeNumber(hit+6,f.healthPrevious);storeNumber(hit+8,f.healthNext);
    frames[depth-1].healthValue=f.healthValue;frames[depth-1].healthPrevious=f.healthNext;depth--;
}
[noinline]
void writeProtection(inout Runtime s,uint output)
{
    if(commands[s.inputBase+P_PROTECTION_META_BASE]==0) return;
    for(uint who=0;who<5;who++)
    {
        uint64_t shield=0,decoy=0;
        for(uint pass=0;pass<s.orderedCount;pass++)
        {
            uint object=protectionObject(s,s.orderedRows[pass]);if(object==PROTECTION_NONE) continue;
            uint at=protectionAddress(s,object),kind=results[at+22]&255;
            if(kind==1) shield=f64Add(shield,protectionNumber(at+who*4));
            if(kind==2) decoy=f64Add(decoy,protectionNumber(at+who*4));
        }
        uint at=output+who*10;storeNumber(at,shield);storeNumber(at+2,protectionCapacity(s,who,1));storeNumber(at+4,decoy);storeNumber(at+6,protectionCapacity(s,who,2));
        results[at+8]=uint(hasProtection(s,who,1));results[at+9]=uint(hasProtection(s,who,2));
    }
}
[noinline]
bool validProtection(inout Runtime s)
{
    uint enabled=0;bool negativeHealth=false;
    for(uint row=0;row<s.count;row++)
    {
        uint policy=protectionPolicy(s,row),kind=policy&255;Definition d=readDefinition(s.inputBase,row);
        if(d.kind==8 && f64Less(d.value,0) || d.kind==0 && d.stat==S_hp_copy && baseCopyDefinition(s,row) || d.kind==0 && (d.stat==S_max_hp_only_pct || d.stat==S_hp_only_caster_based_pct) && f64Less(d.value,0)) negativeHealth=true;
#ifdef PORTABLE_DAMAGE_ACCUM
        if(kind>=13) { if(!validDamageAccum(s,row,d,policy)) return false;enabled|=129U;continue; }
        if((d.stat>=81U && d.stat<=83U || d.kind==34) && kind==0) return false;
#endif
#ifdef PORTABLE_HEAL_CHARGE
        if(kind>=10) { if(!validHealCharge(s,row,d,policy)) return false;enabled|=65U;continue; }
        if((d.stat==76U || d.stat==77U || d.kind==32) && kind==0) return false;
#endif
        if(kind==0) { if(policy!=0 || d.kind==27 || d.kind==31 || d.kind==0 && (d.stat==45 || d.stat==72 || d.stat==71 || d.stat==69 || d.stat==S_heal_overcharge_store)) return false;continue; }
        enabled|=1U|(kind==4 ? 2U : 0U)|(kind==7 ? 4U : 0U)|(kind==3 ? 8U : 0U)|(kind==8 ? 16U : 0U)|(kind==9 ? 32U : 0U);
        if(d.quantityFlags!=(kind==4 ? 4U : 0U) || (d.flags&120U)!=0) return false;
        if(kind>9 || (policy&~511U)!=0 || (policy&256)!=0 && kind!=1 || !f64Finite(d.value) || d.enemyBuff!=0) return false;
        if(kind==9 && (s.combat==0 || d.kind!=0 || d.stat!=S_heal_overcharge_store)) return false;
        if(kind==8 && (d.kind!=0 || d.stat!=69) || kind==1 && (d.kind!=0 || d.stat!=45) || kind==2 && (d.kind!=0 || d.stat!=72) || (kind==3 || kind==4) && (d.kind!=4 || d.stat!=0) || kind==7 && (d.kind!=0 || d.stat!=71) || kind==5 && d.kind!=27 || kind==6 && d.kind!=31) return false;
        if(!validRecipientPlan(s.inputBase+P_RECIPIENT_BASE+row*8,false,s.inputBase)) return false;
    }
    if(enabled!=0)
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        if(d.kind==0 && (d.stat>=S_max_hp_pct && d.stat<=S_max_hp_only_pct || d.stat==S_max_hp_from_max_hp_pct))
            for(uint i=0;i<d.conditionCount;i++) if(commands[s.inputBase+P_CONDITION_BASE+row*P_CONDITION_WORDS+i*4]==C_SHIELD) s.healthMask|=32;
    }
    uint hpPolicy=commands[s.inputBase+P_HP_UNCLAMP_POLICY];
    if(hpPolicy>1 || hpPolicy!=0 && !negativeHealth) return false;
    for(uint word=2;word<8;word++) if(commands[s.inputBase+P_PROTECTION_META_BASE+word]!=0) return false;
    return commands[s.inputBase+P_PROTECTION_META_BASE]==enabled;
}

// The attacked member is first; union order follows native carrier/recipient order.
// Freeze the ordered group and divisor before any landing callback changes state.
[noinline]
uint incomingSplitGroup(inout Runtime s,uint who,uint64_t when)
{
    if((commands[s.inputBase+P_PROTECTION_META_BASE]&16U)==0) return 0;
    uint seen=1U<<who,order=who+1,count=1;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];
        if((protectionPolicy(s,s.carrierDefinition[slot])&255)!=8 || !queryRecipient(s,slot,who,when)) continue;
        uint64_t members=carrierOrder(s,slot);
        for(uint i=0;i<21;i++)
        {
            uint encoded=(members>>(i*3))&7;if(encoded==0) break;uint member=encoded-1,bit=1U<<member;
            if((seen&bit)!=0 || (s.downMask&bit)!=0 || !queryRecipient(s,slot,member,when)) continue;
            seen|=bit;order|=encoded<<(3*count++);
        }
    }
    return count>1 ? order : 0;
}
