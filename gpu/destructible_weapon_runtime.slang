// A weapon's factor snapshot is owned by its existing fire operation. Quantities
// are rounded only for actor kinds actually selected, avoiding unused overflow.
bool destructibleWeaponEnabled(inout Runtime s)
{
    bool magic=commands[s.inputBase+110080]==0x48534933U;
#ifdef PORTABLE_DESTRUCTIBLE_ROSTER_SKILL
    magic=magic||commands[s.inputBase+110080]==0x48534934U;
#endif
#ifdef PORTABLE_DESTRUCTIBLE_BODY_LIFESTEAL
    magic=magic||commands[s.inputBase+110080]==0x48534935U;
#endif
    return magic&&commands[s.inputBase+110085]==1;
}
uint destructibleWeaponBank(inout Runtime s,uint who) { return s.resourceOutput+970000+who*256; }
bool validDestructibleWeapons(inout Runtime s)
{
    if(commands[s.inputBase+110084]>1||s.landingPolicy==0||actorPoolCount(s)!=1) return false;
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
#ifdef PORTABLE_DESTRUCTIBLE_BODY_LIFESTEAL
        if(d.kind==0&&((d.stat==S_lifesteal_pct&&commands[s.inputBase+110080]!=0x48534935U)||d.stat==81||d.stat==82)) return false;
#else
        if(d.kind==0&&(d.stat==S_lifesteal_pct||d.stat==81||d.stat==82)) return false;
#endif
    }
    return true;
}
uint destructibleWeaponSelect(inout Runtime s)
{
    uint count=commands[DF_EXTRA(s)+2320],base=DF_BASE(s.resourceOutput);bool hits=commands[s.inputBase+110084]!=0;
    for(uint slot=0;slot<count;slot++)
    {
        uint at=dtAt(base,slot);
        if(results[at+3]!=0&&(results[at]==3||(hits&&results[at]==4))&&results[at+10]==0&&results[at+11]==0&&results[at+12]==1) return slot;
    }
    return 0xffffffffU;
}
uint64_t destructibleWeaponAmount(inout Runtime s,uint who,uint kind)
{
    uint bank=destructibleWeaponBank(s,who),valid=kind==3?3U:2U,amount=kind==3?10U:8U;
    if(results[bank+valid]!=0) return dtNumber(bank+amount);
    uint64_t factors[9];for(uint i=0;i<9;i++) factors[i]=dtNumber(bank+14+i*2);
    if(kind==3) factors[4]=f64Add(factors[4],f64Div(dtNumber(bank+12),HUNDRED));
    uint64_t value=damageFromFactors(s,factors,false);dtStore(bank+amount,value);results[bank+valid]=1;return value;
}
uint64_t destructibleWeaponSample(inout Runtime s,uint who,Weapon w,uint64_t coefficient,uint64_t when)
{
    uint bank=destructibleWeaponBank(s,who),count=w.pellets*w.muzzles;
    if(count==0||count>128||s.target!=0||actorPoolCount(s)!=1||!f64Equal(dtNumber(DF_HEADER(s.resourceOutput)),when)) { s.error=64;return 0; }
    for(uint i=0;i<256;i++) results[bank+i]=0;
    results[bank]=count;results[bank+4]=uint(!WORLD_PACKET_NORMAL(s,who));
    uint64_t split=f64Div(coefficient,f64FromI64(w.pellets));dtStore(bank+6,split);
    uint flags=WORLD_PACKET_FLAGS(s,who,(w.mode==1?(PARTIAL_IS_FULL(w)?H_CHARGE:0U)|((s.attackContext[who]&4)!=0?H_EXPLOSION:0U):0U));
    uint64_t factors[9],interceptFactor,explosionRange,pierceRange;uint sampledFlags;
    sampleDamageFactorsForReach(s,who,split,when,factors,interceptFactor,explosionRange,pierceRange,sampledFlags,false,WORLD_PACKET_NORMAL(s,who),w.coreBonus,flags,w.fullChargeMult,w.optimal!=0,true);
    if((sampledFlags&H_PIERCE)!=0) { s.error=64;return 0; }
    for(uint i=0;i<9;i++) dtStore(bank+14+i*2,factors[i]);
    dtStore(bank+12,destructibleModifierQuantity(s,s.inputBase+109568,who,3,when));
    uint slot=destructibleWeaponSelect(s),kind=0;
    if(slot!=0xffffffffU) kind=results[dtAt(DF_BASE(s.resourceOutput),slot)];
    return s.error==0?destructibleWeaponAmount(s,who,kind):uint64_t(0);
}
bool destructibleWeaponPellet(inout Runtime s,uint who,uint64_t when,uint hit)
{
    if(!destructibleWeaponEnabled(s)) return false;
    uint bank=destructibleWeaponBank(s,who);
    if(hit>=results[bank]||hit>=128) { s.error=64;return true; }
    uint slot=destructibleWeaponSelect(s);
    if(slot==0xffffffffU) { destructibleWeaponAmount(s,who,0);return false; }
    results[bank+64+hit]=1;
    uint output=s.resourceOutput,head=output+786432,index=results[head+1];
    if(index>=commands[DF_DESCRIPTOR(s)+1]) { s.error=64;return true; }
    uint trace=output+790000+index*1040;results[head+1]=index+1;
    uint at=dtAt(DF_BASE(output),slot),kind=results[at],identity=results[at+1],generation=results[at+2];
    uint64_t amount=destructibleWeaponAmount(s,who,kind);if(s.error!=0) return true;
    results[trace]=index+1;results[trace+1]=0xffffffffU;results[trace+2]=who;results[trace+3]=1;dtStore(trace+4,when);dtStore(trace+6,dtNumber(bank+6));dtStore(trace+8,amount);results[trace+12]=1;results[trace+13]=results[bank+4];
    WorldSchedule w=frameSchedule(s);DWReceipt r=dwLand(w,DF_BASE(output),commands[DF_EXTRA(s)+2320],DF_HEADER(output),slot,kind,identity,generation,2,amount,ONE,when);
    if(w.error!=0) { s.error=w.error;return true; }
    uint receipt=trace+16;results[receipt]=slot;results[receipt+1]=kind;results[receipt+2]=identity;results[receipt+3]=generation;results[receipt+4]=r.delivered;results[receipt+5]=r.broken;dtStore(receipt+6,r.took);
    if(r.delivered!=0)
    {
        uint packet=bank+224;for(uint i=0;i<16;i++) results[packet+i]=0;
        results[packet]=3;dtStore(packet+1,when);results[packet+3]=who;results[packet+4]=kind;results[packet+5]=identity;results[packet+6]=generation;results[packet+8]=2;dtStore(packet+9,amount);dtStore(packet+11,ONE);results[packet+13]=index+1;
        uint start=collectTargetCounters(s,packet|0x80000000U,when);
        if(s.error==0&&results[counterHead(s)+4]>start) dispatch(s,26,0,0,int(start),when,output);
        if(r.broken!=0&&s.error==0)
        {
            results[packet]=4;start=collectTargetCounters(s,packet|0x80000000U,when);
            if(s.error==0&&results[counterHead(s)+4]>start) dispatch(s,26,0,0,int(start),when,output);
        }
    }
    results[trace+10]=1;return true;
}
uint64_t destructibleWeaponBodyAmount(inout Runtime s,uint who,uint64_t legacy)
{
    if(!destructibleWeaponEnabled(s)||f64Zero(legacy)) return legacy;
    uint bank=destructibleWeaponBank(s,who);return results[bank+2]!=0?dtNumber(bank+8):legacy;
}
