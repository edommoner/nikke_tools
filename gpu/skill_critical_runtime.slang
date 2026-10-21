// Named-skill critical fractions have their own (caster,name) key. They do not
// consume physical critical counters or RNG. A notify frame owns its context.
void initializeSkillCritical(inout Runtime s)
{
    if((s.incomingMask&32)==0) return;
    for(uint word=0;word<P_SKILL_CRITICAL_STATE_WORDS;word++) results[s.resourceOutput+P_SKILL_CRITICAL_STATE_BASE+word]=0;
}
uint skillCriticalHit(inout Runtime s,Definition d,uint64_t fraction)
{
    if((s.incomingMask&32)==0 || (d.damageFlags&H_NAMED_SKILL)==0) return 0;
    if(!f64Less(fraction,ONE)) return 1;
    if(!f64Less(0,fraction)) return 0;
    uint at=s.resourceOutput+P_SKILL_CRITICAL_STATE_BASE+(d.owner*P_DEFINITIONS+d.name)*3;
    uint64_t value=f64Add(uint64_t(results[at+1])|(uint64_t(results[at+2])<<32),fraction);
    uint fired=uint(!f64Less(value,ONE));
    if(fired!=0) value=f64Add(value,ONE^F64_SIGN);
    results[at]=1;storeNumber(at+1,value);return fired;
}
void pushSkillHit(inout Runtime s,inout Frame frames[32],inout int depth,Definition d,uint64_t fraction,uint64_t when)
{
    uint critical=skillCriticalHit(s,d,fraction);
    pushFrame(s,frames,depth,0,49,d.owner,int(d.name),when);
    if(s.error==0) frames[depth].hitCrit=critical;
}
