// The second native queue: latch at cast, query/calculate again at full-burst entry.
bool fullBurstPendingInvalid(inout Runtime s,Definition d)
{
    uint descriptor=s.inputBase+P_MODE_BASE+d._wireRow*P_MODE_WORDS+17;
    if(commands[descriptor+1]!=0 || commands[descriptor+2]!=0 || commands[descriptor]!=(d.damagePending==2 ? 0x46424c31U : 0)) return true;
    if(d.damagePending==0) return d.pendingHits!=0;
    if(d.damagePending==1) return s.combat==0 || d.damageHits!=1 || d.damageFlags!=0 || d.damageNormal!=0 || d.pendingHits==0 || d.pendingHits>256;
    if(d.damagePending!=2 || s.combat==0 || !worldPendingEnabled(s) || (commands[s.inputBase+P_WEAPON_BASE+d.owner*P_WEAPON_WORDS+3]&7)!=3) return true;
    uint row=d._wireRow,reference=s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4,tag=d.pendingHits;
    if(tag>=4096 && tag<4096+P_DEFINITIONS)
        return (commands[reference]&3)!=1 || (commands[reference+2]&255)!=tag-4096 || d.damageHits!=1;
    int literal=int(tag);
    return literal< -256 || literal>256 || d.damageHits!=uint(max(0,literal)) || (commands[reference]&3)!=0;
}
// Separate diagnostic bank; observe returned values without another query.
void recordFullBurstQuery(inout Runtime s,uint kind,uint row,uint64_t when,uint64_t x,uint64_t y,uint present=1)
{
#ifdef PORTABLE_FULL_BURST_QUERY_DIAGNOSTIC
    uint head=s.resourceOutput+P_NATIVE_DIAG_BASE,index=results[head+2]++;
    if(index>=128) { results[head+3]++;return; }results[head+1]++;
    uint at=head+16+index*12;results[at]=kind;results[at+1]=row;results[at+2]=definition_owner(s.inputBase,row);results[at+3]=present;
    storeNumber(at+4,when);storeNumber(at+6,x);storeNumber(at+8,y);
#endif
}
void readFullBurstLandingReference(inout Runtime s,uint row,uint64_t when)
{
    Definition d=readDefinition(s.inputBase,row);uint tag=d.pendingHits;
    if(tag<4096 || int(tag)<0) return;
    uint at=s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4;bool present;
    uint64_t value=referenceCount(s,d.owner,(commands[at+1]&511)-1,commands[at+2]&255,false,present);
    // Native reads this live value, then replaces it with the cast-time latch.
    // It is neither a new capacity bound nor a new integer conversion.
    recordFullBurstQuery(s,2,row,when,present?value:0,0,uint(present));
}
void collectFullBurstEnemyStats(inout Runtime s,uint who,uint64_t when,inout uint64_t b[64])
{
    uint64_t enemy[3];collectEnemyModifiers(s,who,s.target,when,enemy);
    b[S_enemy_def_down_pct]=f64Add(b[S_enemy_def_down_pct],enemy[0]);
    b[S_enemy_def_down_flat]=f64Add(b[S_enemy_def_down_flat],enemy[1]);
    b[S_received_dmg_pct]=f64Add(b[S_received_dmg_pct],enemy[2]);
}
void queryOnlyFullBurstLanding(inout Runtime s,uint row,uint64_t when)
{
    Definition d=readDefinition(s.inputBase,row);uint64_t b[64];collectStats(s,d.owner,when,b);
    collectFullBurstEnemyStats(s,d.owner,when,b);recordFullBurstQuery(s,1,row,when,b[S_atk_flat],b[S_atk_pct]);
    readFullBurstLandingReference(s,row,when);
    if(skillHPBasisMode(s,row)!=0) { uint64_t hp=nativeAttackMaxHP(s,d.owner,when,row);recordFullBurstQuery(s,3,row,when,hp,0); }
}
uint fullBurstLandingCount(inout Runtime s,uint row)
{
    Definition d=readDefinition(s.inputBase,row);uint tag=d.pendingHits;
    if(tag<4096 || int(tag)<0) return uint(max(0,int(tag)));
    uint at=s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4;bool present;
    uint64_t value=referenceCount(s,d.owner,(commands[at+1]&511)-1,commands[at+2]&255,false,present);
    if(!present || !f64Less(0,value)) return 0;
    if(!f64Finite(value) || f64Less(f64FromI64(256),value)) { s.error=2;return 0; }
    uint status;uint64_t count=f64ToI64(value,1,status);if(status!=0) { s.error=2;return 0; }return uint(count);
}
void generateFullBurstLandings(inout Runtime s,uint64_t when,uint output,out uint begin,out uint end)
{
    uint header=landingHeader(s);begin=results[header];
    for(uint index=0;index<s.pendingCount && s.error==0;index++)
    {
        uint row=s.pendingRow[index];Definition d=readDefinition(s.inputBase,row);if(d.damagePending!=2) continue;
        s.sourceTime=when;
        uint64_t coefficient=activationDamageCoefficient(s,row);
        coefficient=namedDamageCoefficient(s,row,coefficient,when,true);
        if(s.error==0) dispatch(s,34,0,d.owner,int(row),when,output,coefficient,s.pendingHits[index]);
    }
    end=results[header];
}
// A receipt owns its scalar part value and immutable periodic/interrupt tuple.
// Moving only the eight core words leaves both sidecars attached to the old slot.
void moveFullBurstReceipt(inout Runtime s,uint fromIndex,uint toIndex)
{
    if(fromIndex==toIndex) return;
    if(fromIndex>=P_LANDINGS || toIndex>=P_LANDINGS) { s.error=64;return; }
    uint from=landingAddress(s,fromIndex),to=landingAddress(s,toIndex),marker=results[from+7];
    if(marker!=0 && (marker&0x7fffffffU)!=fromIndex+1) { s.error=64;return; }
    for(uint i=0;i<P_LANDING_WORDS;i++) results[to+i]=results[from+i];
    uint fromPart=skillPartReceiptAddress(from),toPart=skillPartReceiptAddress(to);
    for(uint i=0;i<2;i++) results[toPart+i]=results[fromPart+i];
    uint fromSnapshot=periodicPacketSnapshot(s,fromIndex),toSnapshot=periodicPacketSnapshot(s,toIndex);
    for(uint i=0;i<38;i++) results[toSnapshot+i]=results[fromSnapshot+i];
#ifdef PORTABLE_COORDINATE_SKILLS
    moveCoordinateReceipt(s,fromIndex,toIndex);
#endif
    if(marker!=0) results[to+7]=(marker&0x80000000U)|(toIndex+1);
}
void landFullBurstRange(inout Runtime s,uint begin,uint end,uint64_t when,uint output)
{
    uint header=landingHeader(s),saved=s.target;
    for(uint index=begin;index<end && s.error==0;index++)
    {
        LandingReceipt r=loadWorldSkillReceipt(landingAddress(s,index));
        if(!validWorldSkillReceipt(s,r,false)) { s.error=64;break; }
        if(!landWorldSkillReceipt(s,r,when,output)) break;
        if(results[header+3]==0x7fffffff) { s.error=2;break; }results[header+3]++;
    }
    if(s.error==0)
    {
        uint tail=results[header]-end;
        for(uint i=0;i<tail && s.error==0;i++) moveFullBurstReceipt(s,end+i,begin+i);
        results[header]=begin+tail;
    }
    s.target=saved;
}
