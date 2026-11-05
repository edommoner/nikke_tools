uint referenceScaleMode(inout Runtime s, uint row) { return (commands[s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4]>>2)&3; }
uint referenceCaptureAddress(inout Runtime s, uint slot) { return s.resourceOutput+P_REFERENCE_CAPTURE_BASE+slot*3; }
uint referenceCaptureFlags(inout Runtime s, uint slot) { return results[referenceCaptureAddress(s,slot)]; }
uint64_t referenceCaptureValue(inout Runtime s, uint slot) { uint at=referenceCaptureAddress(s,slot)+1; return uint64_t(results[at])|(uint64_t(results[at+1])<<32); }
void storeReferenceCapture(inout Runtime s, uint slot, uint flags, uint64_t value)
{ uint at=referenceCaptureAddress(s,slot); results[at]=flags; storeNumber(at+1,value); }
uint64_t carrierStackValue(inout Runtime s, uint slot)
{ return (referenceCaptureFlags(s,slot)&2)!=0 ? referenceCaptureValue(s,slot) : f64FromI64(s.stacks[slot]); }
// Resolve ref_count precedence without narrowing binary64 before truncation.
uint64_t truncateReference(uint64_t value)
{
    int exponent=int((value>>52)&2047)-1023;
    if (exponent<0) return 0;
    if (exponent>=52) return value;
    uint64_t mask=(uint64_t(1)<<uint(52-exponent))-1;
    return value & ~mask;
}
[noinline]
uint64_t referenceCount(inout Runtime s, uint who, uint key, uint name, bool gaugeOnly, out bool present)
{
    uint selected=key;
#ifdef PORTABLE_REFERENCE_RESOURCE_SCAN
    selected=P_RESOURCE_KEYS;
    for (uint candidate=0; candidate<s.resourceCount; candidate++)
        if (commands[s.inputBase+P_RESOURCE_NAME_BASE+candidate]==name) { selected=candidate; break; }
#endif
    if (selected<s.resourceCount && (resourceFlags(s,who*P_RESOURCE_KEYS+selected)&1)!=0)
    { present=true; return truncateReference(resourceValue(s,who*P_RESOURCE_KEYS+selected)); }
    if (!gaugeOnly && s.sourceEnabled!=0)
    {
        uint encoded=sourceLookup(s,who,name);
        if (encoded!=0) { present=true; return f64FromI64(sourceLiveCount(s,encoded-1,s.sourceTime)); }
    }
    if (!gaugeOnly) for (uint pass=0; pass<s.orderedCount; pass++)
    {
        uint slot=s.orderedRows[pass]; Definition d=residentDefinition(s,slot);
        if (s.alive[slot]!=0 && d.owner==who && d.name==name) { present=true; return carrierStackValue(s,slot); }
    }
    present=false; return 0;
}
#include "duration_scaling_runtime.slang"
uint modeCapacityReference(inout Runtime s, uint row)
{ return commands[s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4+3]; }
[noinline]
uint referencedModeCapacity(inout Runtime s, uint who, uint row, uint64_t when)
{
    uint descriptor=modeCapacityReference(s,row), base=commands[s.inputBase+P_MODE_BASE+row*P_MODE_WORDS+1];
    bool present; s.sourceTime=when;
    uint64_t value=referenceCount(s,who,(descriptor&511U)-1,descriptor>>9,false,present);
    if (!present) value=ONE;
    uint status; uint64_t count=f64ToI64(value,1,status);
    if (base==0) { s.error=2;return 0; }
    if (!f64Finite(value) || f64Less(value,0) || status!=0 || count>uint64_t(0x7fffffffU/base))
    { s.error=2;return 0; }
    return uint(count)*base;
}
[noinline]
uint activationHitCount(inout Runtime s, uint row)
{
    Definition d=readDefinition(s.inputBase,row); uint at=s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4,mode=commands[at]&3;
    if (f64Zero(d.value)) return 0;
    if (mode==0) return d.damageHits;
    bool present; uint64_t value=referenceCount(s,d.owner,(commands[at+1]&511)-1,commands[at+2]&255,mode==2,present);
    if (!present) return mode==2 ? 0 : 1;
    if (!f64Less(0,value)) return 0;
    if (f64Less(f64FromI64(256),value)) { s.error=2; return 0; }
    uint status; uint64_t count=f64ToI64(value,1,status);
    if (status!=0) { s.error=2; return 0; }
    return uint(count);
}
[noinline]
uint64_t scaleReferenceCount(inout Runtime s, uint source, out bool present)
{
    uint at=s.inputBase+P_REFERENCE_DEFINITION_BASE+source*4;
    return referenceCount(s,definition_owner(s.inputBase,source),((commands[at+1]>>9)&511)-1,(commands[at+2]>>8)&255,false,present);
}
void captureBuffReference(inout Runtime s, uint slot, uint source)
{
    bool present=false; uint64_t count=0;
    if (referenceScaleMode(s,source)==2) count=scaleReferenceCount(s,source,present);
    // Initialized carriers retain their birth-time runtime predicate policy.
    storeReferenceCapture(s,slot,(referenceCaptureFlags(s,slot)&4)|uint(present),count);
}
[noinline]
uint64_t scalarReferenceCount(inout Runtime s, uint slot, out bool scaled)
{
    uint source=s.carrierDefinition[slot],mode=referenceScaleMode(s,source); scaled=mode==1 || mode==2;
    if (!scaled) return 0;
    if ((referenceCaptureFlags(s,slot)&1)!=0) return referenceCaptureValue(s,slot);
    bool present; uint64_t value=scaleReferenceCount(s,source,present); return present ? value : 0;
}
[noinline]
bool registerDotReference(inout Runtime s, uint row, bool resident)
{
    if (referenceScaleMode(s,row)!=3) { storeReferenceCapture(s,row,0,0); return false; }
    if (!resident || definition_maxStack(s.inputBase,row)!=1)
    {
        bool present; uint64_t value=scaleReferenceCount(s,row,present);
        storeReferenceCapture(s,row,3,present ? value : ONE);
    }
    uint64_t value=referenceCaptureValue(s,row); uint status; uint64_t integral=f64ToI64(value,1,status);
    s.stacks[row]=status==0 && integral<=0x7fffffff ? uint(integral) : 0;
    return true;
}
uint64_t activationDamageCoefficient(inout Runtime s, uint row)
{
    Definition d=readDefinition(s.inputBase,row); uint64_t scale=referenceScaleMode(s,row)==3 ? carrierStackValue(s,row) : f64FromI64((d.periodicFlags&2)!=0 ? s.stacks[row] : 1);
    // Native reads the first active same-name carrier on every DoT tick. Named
    // removal can retire it even without a cleanse/status policy in this input.
    if(d.kind==3 && !f64Zero(d.interval) && (d.periodicFlags&2)!=0)
    {
        bool present=false;scale=0;
        for(uint pass=0;pass<s.orderedCount;pass++)
        {
            uint slot=s.orderedRows[pass];
            if(s.alive[slot]!=0 && definition_owner(s.inputBase,s.carrierDefinition[slot])==d.owner && definition_name(s.inputBase,s.carrierDefinition[slot])==d.name)
            { scale=carrierStackValue(s,slot);present=true;break; }
        }
        if(!present && referenceScaleMode(s,row)==3) scale=scaleReferenceCount(s,row,present);
    }
#ifdef PORTABLE_COORDINATE_ORIGINAL_SOURCE_OPS
    uint scope=s.resourceOutput+P_STAGED_HEADER_BASE+2;
    if(results[scope]==row+1 && s.alive[row]!=0 && results[scope+2]==s.entryOrder[row] && results[scope+1]==stagedGeneration(s,row)) scale=f64FromI64(results[scope+3]);
#else
    if(s.stagedScopeRow==row+1 && s.alive[row]!=0 && s.stagedScopeEntry==s.entryOrder[row] && s.stagedScopeGeneration==stagedGeneration(s,row)) scale=f64FromI64(s.stagedScopeStack);
#endif
    return f64Mul(d.value,scale);
}
[noinline]
bool validateReferences(inout Runtime s)
{
    for (uint slot=0; slot<P_CARRIERS; slot++) storeReferenceCapture(s,slot,0,0);
    for (uint key=0; key<s.resourceCount; key++) if (commands[s.inputBase+P_RESOURCE_NAME_BASE+key]>=P_DEFINITIONS) return false;
    for (uint row=0; row<s.count; row++)
    {
        uint at=s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4,word=commands[at],hit=word&3,scale=(word>>2)&3,keys=commands[at+1],names=commands[at+2];
        if (hit>2 || (word&~15U)!=0 || (keys&~0x3ffffU)!=0 || (names&~0xffffU)!=0) return false;
        for (uint part=0; part<2; part++)
        {
            uint mode=part==0 ? hit : scale,key=(keys>>(part*9))&511,name=(names>>(part*8))&255;
            if (mode==0) { if (key!=0 || name!=0) return false; continue; }
            if (key==0 || key>s.resourceCount || name!=commands[s.inputBase+P_RESOURCE_NAME_BASE+key-1]) return false;
        }
        Definition d=readDefinition(s.inputBase,row);
        uint magazine=commands[at+3],capacityKey=magazine&511U,capacityName=magazine>>9;
        if((magazine&0x80000000U)!=0)
        {
#ifdef PORTABLE_DURATION_SCALING
            capacityName=(magazine>>9)&255U;
            if((magazine&~0x8001ffffU)!=0 || (d.kind!=0&&d.kind!=4) || s.combat==0 || commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE]!=0x57533031U || !f64Finite(d.duration) ||
               capacityKey>s.resourceCount || (capacityKey==0 ? capacityName!=0 : capacityName!=commands[s.inputBase+P_RESOURCE_NAME_BASE+capacityKey-1])) return false;
#else
            return false;
#endif
        }
        else if (magazine!=0 && ((magazine&~0x1ffffU)!=0 || d.kind!=2 || s.combat==0 || capacityKey==0 || capacityKey>s.resourceCount ||
            capacityName!=commands[s.inputBase+P_RESOURCE_NAME_BASE+capacityKey-1] || commands[s.inputBase+P_MODE_BASE+row*P_MODE_WORDS+21]!=0)) return false;
#ifdef PORTABLE_MAX_AMMO_SCALING
        if ((d.flags&~7679U)!=0 || !validMaxAmmoScaling(s,row,d) || uint((d.flags&4)!=0)!=uint(scale!=0)) return false;
#else
        if ((d.flags&~3583U)!=0 || uint((d.flags&4)!=0)!=uint(scale!=0)) return false;
#endif
        bool directHealth=(d.alliedFlags&1)!=0 || d.stat==S_def_caster_based_pct || (d.stat>=S_max_hp_pct&&d.stat<=S_max_hp_only_pct) || d.stat==S_max_hp_from_max_hp_pct;
        if ((d.flags&256U)!=0 && (d.kind!=0 || d.enemyBuff!=0 || s.combat==0 || !directHealth || (d.flags&2)==0 || !f64Less(d.duration,0))) return false;
        bool damageAccumLostHP=false;
#ifdef PORTABLE_DAMAGE_ACCUM
        damageAccumLostHP=d.stat==83U && d.kind==0;
#endif
        if (!damageAccumLostHP && (d.flags&128U)!=0 && (d.kind!=0 || !((d.stat==S_atk_pct && d.alliedFlags==0) || (d.stat==S_enemy_def_down_pct && d.alliedFlags==1)) || d.enemyBuff!=0 || s.combat==0 || scale!=0 || commands[s.inputBase+P_RECIPIENT_BASE+row*8]!=0)) return false;
        if ((scale==1 || scale==2) && (d.stat==S_max_hp_pct || d.stat==S_max_hp_only_pct || d.stat==S_hp_caster_based_pct || d.stat==S_hp_only_caster_based_pct)) s.healthMask|=32;
        if (hit!=0 && d.kind!=3 && !(hit==1 && (d.kind==20 || d.kind==21))) return false;
        if (scale==3 && (d.kind!=3 || f64Zero(d.interval) || (d.periodicFlags&2)==0)) return false;
        if ((scale==1 || scale==2) && d.kind!=0 && d.kind!=4) return false;
    }
    return true;
}
