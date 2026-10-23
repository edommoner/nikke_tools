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
void generateFullBurstLandings(inout Runtime s,uint count,uint64_t when,uint output,out uint begin,out uint end)
{
    uint header=landingHeader(s);begin=results[header];
    for(uint index=0;index<count && s.error==0;index++)
    {
        uint row=s.pendingRow[index];Definition d=readDefinition(s.inputBase,row);if(d.damagePending!=2) continue;
        s.sourceTime=when;
        uint64_t coefficient=activationDamageCoefficient(s,row);
        coefficient=namedDamageCoefficient(s,row,coefficient,when,true);
        if(s.error==0) dispatch(s,34,0,d.owner,int(row),when,output,coefficient,s.pendingHits[index]);
    }
    end=results[header];
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
        for(uint i=0;i<tail;i++) for(uint word=0;word<P_LANDING_WORDS;word++) results[landingAddress(s,begin+i)+word]=results[landingAddress(s,end+i)+word];
        results[header]=begin+tail;
    }
    s.target=saved;
}
