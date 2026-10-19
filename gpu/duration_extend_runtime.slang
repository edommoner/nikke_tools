[noinline]
bool hasDurationExtensionMembers(inout Runtime s,uint row)
{
    uint at=s.inputBase+P_FORCE_BASE+row*P_MASK_WORDS;
    uint any=0;for(uint i=0;i<P_MASK_WORDS;i++) any|=commands[at+i];
    return any!=0;
}
// Native named extension changes a whole shared resident after ANY member
// intersects. It never splits recipients or resets registration/next-tick order.
[noinline]
void extendNamedResidents(inout Runtime s,uint row,uint scope,uint64_t when)
{
    uint membership=s.inputBase+P_FORCE_BASE+row*P_MASK_WORDS;
    uint any=0;for(uint word=0;word<P_MASK_WORDS;word++) any|=commands[membership+word];
    if(any==0) return;
    if(scope==0) return;
    uint64_t amount=definition_value(s.inputBase,row);
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]==0 || s.lazyPending[slot]!=0) continue;
        if((commands[membership+definition/32]&(1U<<(definition%32)))==0) continue;
        if(s.end[slot]==F64_INF) continue;
        if((removalMembers(s,slot)&scope)==0) continue;
        s.end[slot]=f64Add(s.end[slot],amount);
        if(definition_kind(s.inputBase,definition)==3 && s.timerActive[definition]!=0) s.expiry[definition]=s.end[slot];
    }
}
[noinline]
bool validDurationExtension(uint input,uint count,uint combat,uint row)
{
    uint at=input+P_DEFINITION_BASE+row*P_DEFINITION_WORDS;
    if(commands[at+D_KIND]!=15) return true;
    uint policy=commands[at+D_TARGET];
    if(policy<1 || policy>2 || !f64Finite(loadNumber(at+D_VALUE))) return false;
    uint recipients=input+P_RECIPIENT_BASE+row*8;
    if(policy==1) { if(!validRecipientPlan(recipients,false,input) || commands[recipients+7]!=0) return false; }
    else for(uint i=0;i<8;i++) if(commands[recipients+i]!=0) return false;
    uint packet=input+P_DAMAGE_DEFINITION_BASE+row*P_DAMAGE_DEFINITION_WORDS;
    if(policy==2)
    {
        if(combat==0 || commands[packet]>9 || commands[packet+1]==0 || commands[packet+1]>256) return false;
        for(uint i=2;i<8;i++) if(commands[packet+i]!=0) return false;
    }
    else for(uint i=0;i<8;i++) if(commands[packet+i]!=0) return false;
    uint membership=input+P_FORCE_BASE+row*P_MASK_WORDS;
    for(uint i=count;i<P_DEFINITIONS;i++) if((commands[membership+i/32]&(1U<<(i%32)))!=0) return false;
    return true;
}
