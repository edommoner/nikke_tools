// One counter-notice executor shared by physical shield hits and fixed releases.
void destructibleNotifyShieldReceipt(inout Runtime s,uint who,uint64_t when,uint kind,uint identity,uint generation,uint family,uint64_t amount,uint index,DWReceipt r,uint packet)
{
    if(r.delivered==0||s.error!=0) return;
    for(uint i=0;i<16;i++) results[packet+i]=0;
    results[packet]=3;dtStore(packet+1,when);results[packet+3]=who;results[packet+4]=kind;results[packet+5]=identity;results[packet+6]=generation;results[packet+7]=family;results[packet+8]=2;dtStore(packet+9,amount);dtStore(packet+11,ONE);results[packet+13]=index+1;
    uint start=collectTargetCounters(s,packet|0x80000000U,when);
    if(s.error==0&&results[counterHead(s)+4]>start) dispatch(s,26,0,0,int(start),when,s.resourceOutput);
    if(r.broken!=0&&s.error==0)
    {
        results[packet]=4;start=collectTargetCounters(s,packet|0x80000000U,when);
        if(s.error==0&&results[counterHead(s)+4]>start) dispatch(s,26,0,0,int(start),when,s.resourceOutput);
    }
}
bool destructibleAccumLanding(inout Runtime s,LandingReceipt receipt,uint64_t when,uint output)
{
    if(commands[s.inputBase+110080]!=0x48534936U) return false;
    Definition d=readDefinition(s.inputBase,receipt.row);
    if(d.kind!=34||d.stat!=0||d.damageFlags!=H_SPLIT||d.damageRoute<1||d.damageRoute>9||d.damageCount<1||d.damageCount>128||d.damageHits!=1||d.damagePending!=0||d.damageNormal!=0) { s.error=64;return true; }
    Frame f={};f.target=0;
    if(!rosterShieldSkillBody(s,d,f)) return s.error!=0;
    uint slot=destructibleWeaponSelect(s);if(slot==0xffffffffU) return false;
    uint head=output+786432,index=results[head+1];
    if(index>=commands[DF_DESCRIPTOR(s)+1]) { s.error=64;return true; }
    uint trace=output+790000+index*1040;results[head+1]=index+1;
    uint at=dtAt(DF_BASE(output),slot),kind=results[at],identity=results[at+1],generation=results[at+2];
    // releaseDamageAccum already took, scaled and truncated this quantity.
    // Never apply an ATK/DEF/crit/shield factor to it a second time.
    uint64_t amount=receipt.amount;
    results[trace]=index+1;results[trace+1]=receipt.row;results[trace+2]=d.owner;results[trace+3]=1;dtStore(trace+4,when);dtStore(trace+6,0);dtStore(trace+8,amount);
    results[trace+11]=1;results[trace+12]=3;results[trace+13]=d.damageRoute;results[trace+14]=H_SPLIT;results[trace+15]=d.damageCount;
    WorldSchedule w=frameSchedule(s);DWReceipt r=dwLand(w,DF_BASE(output),commands[DF_EXTRA(s)+2320],DF_HEADER(output),slot,kind,identity,generation,2,amount,ONE,when);
    if(w.error!=0) { s.error=w.error;return true; }
    uint record=trace+16;results[record]=slot;results[record+1]=kind;results[record+2]=identity;results[record+3]=generation;results[record+4]=r.delivered;results[record+5]=r.broken;dtStore(record+6,r.took);
    // Reserve by unique typed attack index. Synchronous child releases cannot
    // overwrite an ancestor's packet, and the existing 128-attack bound applies.
    uint packet=output+960000+index*16;
    destructibleNotifyShieldReceipt(s,d.owner,when,kind,identity,generation,1,amount,index,r,packet);
    for(uint i=0;i<16;i++) results[packet+i]=0;
    results[trace+10]=1;return true;
}
