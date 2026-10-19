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
    if (!gaugeOnly) for (uint pass=0; pass<s.orderedCount; pass++)
    {
        uint slot=s.orderedRows[pass]; Definition d=residentDefinition(s,slot);
        if (s.alive[slot]!=0 && d.owner==who && d.name==name) { present=true; return f64FromI64(s.stacks[slot]); }
    }
    present=false; return 0;
}
[noinline]
uint activationHitCount(inout Runtime s, uint row)
{
    Definition d=s.defs[row]; uint at=s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4,mode=commands[at];
    if (f64Zero(d.value)) return 0;
    if (mode==0) return d.damageHits;
    bool present; uint64_t value=referenceCount(s,d.owner,commands[at+1]-1,commands[at+2],mode==2,present);
    if (!present) return mode==2 ? 0 : 1;
    if (!f64Less(0,value)) return 0;
    if (f64Less(f64FromI64(256),value)) { s.error=2; return 0; }
    uint status; uint64_t count=f64ToI64(value,1,status);
    if (status!=0) { s.error=2; return 0; }
    return uint(count);
}
[noinline]
bool validateReferences(inout Runtime s)
{
    for (uint key=0; key<s.resourceCount; key++) if (commands[s.inputBase+P_RESOURCE_NAME_BASE+key]>=P_DEFINITIONS) return false;
    for (uint row=0; row<s.count; row++)
    {
        uint at=s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4,mode=commands[at];
        if (mode>2 || commands[at+3]!=0) return false;
        if (mode==0) { if (commands[at+1]!=0 || commands[at+2]!=0) return false; continue; }
        if (s.defs[row].kind!=3 || commands[at+1]==0 || commands[at+1]>s.resourceCount) return false;
        if (commands[at+2]!=commands[s.inputBase+P_RESOURCE_NAME_BASE+commands[at+1]-1]) return false;
    }
    return true;
}
