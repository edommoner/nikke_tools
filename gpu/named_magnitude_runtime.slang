// Named operators retain canonical stat/name references and existing carriers.
bool namedMagnitudeStat(uint stat)
{ return stat==S_dmg_scale_mag_pct || stat==S_received_dmg_buff_mag_pct; }
[noinline]
bool validNamedMagnitudes(inout Runtime s)
{
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        if(d.stat==79) return false; // Canonical ATK magnitude remains unported.
        if(!namedMagnitudeStat(d.stat)) continue;
#ifndef PORTABLE_WORLD_PROJECTILE
        return false;
#else
        if(s.combat==0 || d.kind!=0 || d.targetName<0 || d.targetName>=int(P_DEFINITIONS) ||
           d.quantityFlags>32 || (d.quantityFlags&~32U)!=0 || d.alliedFlags!=0 ||
           d.healthScaling!=0 || d.damageFlags!=0 || !f64Finite(d.value)) return false;
        s.quantityMask|=32768;
#endif
    }
    return true;
}
// timeline reads these carriers directly: no recipient/runtime-condition query.
// Capture before B3 deferral; each resident multiplication keeps native order.
uint64_t namedDamageCoefficient(inout Runtime s,uint row,uint64_t coefficient,uint64_t when)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    if((s.quantityMask&32768)==0 || f64Zero(coefficient)) return coefficient;
    Definition damage=readDefinition(s.inputBase,row);
    if(damage.name>=P_DEFINITIONS) return coefficient;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];Definition mag=residentDefinition(s,slot);
        if(s.alive[slot]==0 || mag.kind!=0 || mag.stat!=S_dmg_scale_mag_pct ||
           mag.owner!=damage.owner || mag.targetName!=int(damage.name) || !f64Less(when,s.end[slot])) continue;
        coefficient=f64Mul(coefficient,f64Add(ONE,f64Div(scalarValue(s,slot,mag.owner),HUNDRED)));
        if(!f64Finite(coefficient)) { s.error=16;return 0; }
    }
#endif
    return coefficient;
}
// Boss-bound base effects share the same insertion order as authored carriers.
// Their names are literal bindings, never a CPU-precomputed magnitude or state.
void addNamedReceivedOverlays(inout Runtime s,uint target,int name,uint cutoff,inout uint visited,uint64_t magnitude,inout uint64_t total)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    if((s.quantityMask&65536)==0 || actorFieldLogicalSlot(s,target)!=0) return;
    uint count=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];
    for(uint pass=0;pass<count;pass++)
    {
        uint selected=32,sequence=cutoff;
        for(uint n=0;n<count;n++)
        {
            uint order=results[woState(s,n)+3];
            if((visited&(1U<<n))==0 && order!=0 && order<sequence && commands[woNode(s,n)+11]==uint(name+1))
            { selected=n;sequence=order; }
        }
        if(selected==32) break;
        visited|=1U<<selected;
        total=f64Add(total,f64Mul(loadNumber(woNode(s,selected)+6),f64Div(magnitude,HUNDRED)));
        if(!f64Finite(total)) { s.error=16;return; }
    }
#endif
}
// get_buffs adds increments after its normal ordered received-damage pass.
// Do not fold into the base sum or apply the pending-damage exclusion policy.
void amplifyNamedReceived(inout Runtime s,uint target,uint64_t when,inout uint64_t total)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    if((s.quantityMask&32768)==0) return;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];Definition mag=residentDefinition(s,slot);
        if(s.alive[slot]==0 || mag.kind!=0 || mag.stat!=S_received_dmg_buff_mag_pct || mag.enemyBuff==0 ||
           !f64Less(when,s.end[slot]) || WORLD_FIELDS_MEMBER_INVALID(s,slot,target,true) ||
           !WORLD_FIELDS_CONDITION(s,slot,target,when,true)) continue;
        uint64_t magnitude=scalarValue(s,slot,mag.owner);uint visited=0;
        for(uint inner=0;inner<s.orderedCount;inner++)
        {
            uint base=s.orderedRows[inner];Definition d=residentDefinition(s,base);
            addNamedReceivedOverlays(s,target,mag.targetName,s.entryOrder[base],visited,magnitude,total);
            if(s.alive[base]==0 || d.kind!=0 || d.stat!=S_received_dmg_pct || d.enemyBuff==0 ||
               int(d.name)!=mag.targetName || !f64Less(when,s.end[base]) ||
               WORLD_FIELDS_MEMBER_INVALID(s,base,target,true) || !WORLD_FIELDS_CONDITION(s,base,target,when,true)) continue;
            uint64_t value=scalarValue(s,base,d.owner);
            total=f64Add(total,f64Mul(value,f64Div(magnitude,HUNDRED)));
            if(!f64Finite(total)) { s.error=16;return; }
        }
        addNamedReceivedOverlays(s,target,mag.targetName,0xffffffffU,visited,magnitude,total);
    }
#endif
}
