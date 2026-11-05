// Battle-owned adapter for the shared scalar core. All quantities originate in
// resident GPU state; input metadata contains only authored policies/names.
static const uint DA_BATTLE_HEADER=260666,DA_BATTLE_QUEUE=260668,DA_BATTLE_QUEUE_COUNT=512;
bool damageAccumEnabled(inout Runtime s) { return (commands[s.inputBase+P_PROTECTION_META_BASE]&128U)!=0; }
uint damageAccumBase(inout Runtime s) { return s.resourceOutput+P_PROTECTION_OBJECT_BASE; }
uint damageAccumHeader(inout Runtime s) { return s.resourceOutput+DA_BATTLE_HEADER; }
[noinline]
void sweepDamageAccum(inout Runtime s)
{
    if(!damageAccumEnabled(s)) return;
    uint base=damageAccumBase(s),header=damageAccumHeader(s);
    for(uint object=0;object<P_PROTECTION_OBJECTS;object++)
    {
        uint at=daAt(base,object),flags=results[at+22],kind=flags&255U;
        if(kind==DA_DEALT || kind==DA_RATE || kind==DA_RECEIVED)
        { if(!protectionObjectActive(s,object)) daRetire(base,header,object); }
        else if((flags&PROTECTION_RESERVED)==0 && !protectionObjectActive(s,object)) results[at+22]=0;
    }
}
[noinline]
void buildDamageAccum(inout Runtime s,uint slot,uint64_t when)
{
    sweepDamageAccum(s);Definition d=residentDefinition(s,slot);uint policy=protectionPolicy(s,s.carrierDefinition[slot]);
    uint base=damageAccumBase(s),header=damageAccumHeader(s),object=protectionObject(s,slot);
    // Unlink before the common allocator clears the linked-list words.
    if(object!=PROTECTION_NONE) daUnlink(base,header,object);
    object=allocateProtection(s,slot,0);if(s.error!=0) return;
    uint at=daAt(base,object),status;results[at+22]=0;
    if(d.stat==81U || d.stat==82U)
    {
        uint saved=s.target;s.target=0;uint64_t values[64];collectStats(s,d.owner,when,values);
        uint64_t attack=skillAttackBasis(s,d.owner,P_DEFINITIONS,when,values[S_atk_pct],values[S_atk_flat]);s.target=saved;
        uint64_t cap=f64Div(f64Mul(attack,scalarValue(s,slot,d.owner)),HUNDRED);
        daInitializePool(base,P_PROTECTION_OBJECTS,header,object,(policy&1024U)!=0 ? d.name : DA_NONE,d.owner,d.stat,s.entryOrder[slot],slot,cap,status);
    }
    else
    {
        uint ratePolicy=((policy&512U)!=0 ? 1U : 0U)|((policy&256U)!=0 ? 2U : 0U)|((d.flags&128U)!=0 ? 4U : 0U)|(d.maxStack>1 ? 8U : 0U);
        daInitializeRate(base,P_PROTECTION_OBJECTS,header,object,uint(d.targetName),d.owner,s.entryOrder[slot],ratePolicy,d.value,s.stacks[slot],s.hpPct[d.owner],status);
    }
    results[at+6]=slot;if(status!=0) s.error=64;
}
[noinline]
void refreshDamageAccumRates(inout Runtime s)
{
    sweepDamageAccum(s);uint base=damageAccumBase(s);
    for(uint object=0;object<P_PROTECTION_OBJECTS;object++)
    {
        uint at=daAt(base,object),flags=results[at+22];if((flags&255U)!=DA_RATE) continue;
        uint slot=results[at+6],owner=(flags>>10)&7U;Definition d=residentDefinition(s,slot);
        daStore(at,d.value);daStore(at+2,s.hpPct[owner]);results[at+21]=s.stacks[slot];
    }
}
[noinline]
void advanceDamageAccumNotices(inout Runtime s,inout DISPATCH_FRAMES(frames),inout int depth,Frame f)
{
    if(!damageAccumEnabled(s)) { depth--;return; }
    uint base=damageAccumBase(s);
    if(f.cursor==0)
    {
        refreshDamageAccumRates(s);uint status,queue=s.resourceOutput+DA_BATTLE_QUEUE;
        uint count=daCollect(base,P_PROTECTION_OBJECTS,damageAccumHeader(s),f.owner,f.healthValue,queue,DA_BATTLE_QUEUE_COUNT,status);
        if(status!=0) { s.error=64;return; }
        uint first=0,last=0;
        // Freeze every notice in a reserved object before the first callback.
        // Child collection may reuse queue scratch, never this ancestor list.
        for(uint i=0;i<count;i++)
        {
            uint object=daFree(base,P_PROTECTION_OBJECTS);if(object==DA_NONE) { s.error=64;return; }
            uint at=daAt(base,object);for(uint w=0;w<DA_WORDS;w++) results[at+w]=0;
            results[at+22]=17U|DA_RESERVED;results[at+4]=results[queue+i*2];results[at+21]=results[queue+i*2+1];
            if(last!=0) results[daAt(base,last-1)+23]=object+1;else first=object+1;last=object+1;
        }
        frames[depth].cursor=1;frames[depth].value=first;return;
    }
    uint link=uint(f.value);if(link==0) { depth--;return; }
    uint at=daAt(base,link-1),name=results[at+4],owner=results[at+21];
    frames[depth].value=results[at+23];results[at+22]=0;
    pushFrame(s,frames,depth,0,50,owner,int(name),f.time);
}
[noinline]
void releaseDamageAccum(inout Runtime s,Definition d,uint row,Frame f,uint depth)
{
    sweepDamageAccum(s);uint status;uint64_t amount=daTake(damageAccumBase(s),P_PROTECTION_OBJECTS,damageAccumHeader(s),uint(d.targetName),status);
    if(status!=0) { s.error=64;return; }
    // Native consumes first and skips the split query for an empty pool.
    if(!f64Less(0,amount)) return;
    uint saved=s.target;s.target=0;uint64_t split=readStat(s,d.owner,S_split_dmg_pct,f.time);s.target=saved;
    bool emit;uint64_t integer=daEmission(amount,split,emit,status);
    if(status!=0) { s.error=64;return; }
    if(emit && s.error==0)
    {
#ifdef PORTABLE_COORDINATE_PHYSICAL
        // enqueueLanding's receipt depth is one past its cast snapshot.
        if(depth==0){s.error=64;return;}
        captureCoordinatePhysicalBodyOnly(s,row,depth-1);
        if(s.error!=0)return;
#endif
        enqueueLanding(s,row,f.target,0xffffffffU,0,f64FromI64(integer),f.time,1,1,depth,s.enemyEpoch);
    }
}
bool validDamageAccum(inout Runtime s,uint row,Definition d,uint policy)
{
    uint kind=policy&255U;
    if(kind<13 || kind>16 || s.combat==0 || commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE]!=0x57533031U ||
       (policy&~2047U)!=0 || !f64Finite(d.value) || !f64Zero(d.interval) || d.bulletDuration!=0 || d.healthScaling!=0 || d.alliedFlags!=0 || d.quantityFlags!=0 || referenceScaleMode(s,row)!=0) return false;
    if(kind==16)
    {
        if(policy!=16 || d.kind!=34 || d.stat!=0 || uint(d.targetName)>=P_DEFINITIONS || d.damageFlags!=16 || d.damageHits!=1 || d.damagePending!=0 || d.damageNormal!=0 || !f64Zero(d.damageGauge)) return false;
        return validWorldSkillDefinition(s,row,d);
    }
    if(d.kind!=0 || d.stat!=kind+68U || d.damageFlags!=0 || (d.flags&120U)!=0) return false;
    if(kind!=15 && (policy&~uint(255U|1024U))!=0 || kind==15 && ((policy&1024U)!=0 || (policy&256U)!=0 && uint(d.targetName)>=P_DEFINITIONS)) return false;
    if((d.flags&128U)!=0 && kind!=15) return false;
    return d.enemyBuff!=0 || validRecipientPlan(s.inputBase+P_RECIPIENT_BASE+row*8,false,s.inputBase);
}
