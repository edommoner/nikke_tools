// DBT1: actual full battle clock, normal scalar context, one plain skill row.
// Admission deliberately excludes canonical targets-cleared coupling.
bool initializeDestructibleBattle(inout Runtime s)
{
    uint descriptor=DF_DESCRIPTOR(s),extra=DF_EXTRA(s),count=commands[extra+2320];
    bool weaponOnly=false;
#ifdef PORTABLE_COORDINATE_TYPED_WEAPONS
    weaponOnly=coordinateTypedWeapons(s)&&commands[descriptor]==0xffffffffU;
#endif
#ifdef PORTABLE_DESTRUCTIBLE_WEAPON
    weaponOnly=destructibleWeaponEnabled(s)&&commands[descriptor]==0xffffffffU;
#endif
    if((!weaponOnly&&commands[descriptor]>=s.count)||commands[descriptor+1]<1||commands[descriptor+1]>128||commands[descriptor+2]!=1||commands[descriptor+3]!=0x44425431U) return false;
    for(uint i=4;i<16;i++) if(commands[descriptor+i]!=0) return false;
#ifdef PORTABLE_COORDINATE_TYPED_TARGETS
    if(!validTypedGeometry(s))return false;
#else
    for(uint i=0;i<2320;i++) if(commands[extra+i]!=0) return false;
#endif
    for(uint i=2321;i<2328;i++) if(commands[extra+i]!=0) return false;
    for(uint i=3864;i<5120;i++) if(commands[extra+i]!=0) return false;
    if(!worldFrameEnabled(s)) return false;
    if(!weaponOnly)
    {
    Definition d=readDefinition(s.inputBase,commands[descriptor]);
    // Both accepted bits already have an ordinary common-executor consumer:
    // named scalar factors and post-handler completion notification (event51).
    if(d.kind!=3||d.stat!=0||d.damageRoute!=1||d.damageCount!=1||d.damageHits!=1||d.damagePending!=0||d.damageNormal!=0||(d.damageFlags&~(H_NAMED_SKILL|524288U))!=0||d.healthScaling!=0||d.quantityFlags!=0||!dtQuantity(d.value)) return false;
    }
    WorldSchedule w=frameSchedule(s);
    for(uint slot=0;slot<count&&slot<128;slot++)
    { uint node=commands[extra+2328+slot*12];if(node>=w.count||(commands[wsNode(w,node)+1]&2)!=0) return false; }
#ifdef PORTABLE_DESTRUCTIBLE_EMPTY_BODY
    // Only the product plain-body entry accepts an explicitly empty universe.
    // Other typed entries retain their nonempty binding admission contract.
    if(count==0)
    {
        if(!weaponOnly||actorPoolCount(s)==0||commands[actorBinding(s,0)]!=0) return false;
        for(uint slot=1;slot<actorPoolCount(s);slot++) if(commands[actorBinding(s,slot)]!=1) return false;
        for(uint i=2328;i<3864;i++) if(commands[extra+i]!=0) return false;
    }
    else
#endif
    if(!dwValidate(w,extra+2328,count,DF_BASE(s.resourceOutput))) return false;
    results[DT_OUTPUT(s.resourceOutput,0)]=0x44425431U;
    results[DF_HEADER(s.resourceOutput)+4]=1;
    return true;
}
void destructibleBattleSync(inout Runtime s,uint64_t when,bool finished)
{
    uint header=DF_HEADER(s.resourceOutput);
    if(results[header+4]==0) return;
    if(results[header+3]!=0) { s.error=64;return; }
    uint base=DF_BASE(s.resourceOutput),extra=DF_EXTRA(s),count=commands[extra+2320],status;
    dtAdvance(base,count,when,dtNumber(header),status);
    if(status!=0) { s.error=status;return; }
    WorldSchedule w=frameSchedule(s);dwSync(w,extra+2328,count,base,when);s.error=w.error;
    dtStore(header,when);results[header+2]=1;results[header+3]=uint(finished);
}
void destructibleBattleCapture(inout Runtime s,uint scratch,uint selected,Frame f,Definition d)
{
    results[scratch+530]=0;results[scratch+531]=0;
    if(selected==0) return;
    uint head=DT_OUTPUT(s.resourceOutput,0),index=results[head+1];
    if(index>=commands[DF_DESCRIPTOR(s)+1]) { s.error=64;return; }
    results[head+1]=index+1;
    uint trace=DT_OUTPUT(s.resourceOutput,3568)+index*1040;
    results[scratch+530]=trace;results[scratch+531]=index+1;
    results[trace]=index+1;results[trace+1]=uint(f.argument);results[trace+2]=d.owner;results[trace+3]=selected;
    dtStore(trace+4,f.time);dtStore(trace+6,dtNumber(scratch+532));dtStore(trace+8,dtNumber(scratch+534));
#ifdef PORTABLE_DESTRUCTIBLE_ROSTER_SKILL
    if(rosterShieldSkillsEnabled(s))
    { results[trace+11]=1;results[trace+12]=2;results[trace+13]=d.damageRoute;results[trace+14]=d.damageFlags&(H_BURST|H_AOE_BURST|H_SINGLE_BURST);results[trace+15]=d.damageCount; }
#endif
}
