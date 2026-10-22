// Physical receipts feed the existing counter collector and continuation.
// Input and GPU-owned records have one layout; the high address bit selects
// the owning buffer. Neither CUDA nor Metal has a second credit algorithm.
uint counterPacketWord(uint at) { return (at&0x80000000U)!=0 ? results[at&0x7fffffffU] : commands[at]; }
uint64_t counterPacketNumber(uint at)
{ return uint64_t(counterPacketWord(at))|(uint64_t(counterPacketWord(at+1))<<32); }
bool counterLandingsEnabled(inout Runtime s)
{ return COUNTER_CONTEXT_MODE(s,targetCountersEnabled(s)&&commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE+6]==1); }
bool counterExtraPart(inout Runtime s,uint kind)
{ return kind==1&&counterLandingsEnabled(s)&&results[counterHead(s)+10]!=0; }
void resetCounterPartExtra(inout Runtime s,uint slot)
{
    if(!counterLandingsEnabled(s)) return;
    uint at=s.resourceOutput+P_COUNTER_LANDING_EXTRA_BASE+slot*4;for(uint j=0;j<4;j++) results[at+j]=0;
}
bool counterLandingDefinitionInvalid(inout Runtime s,uint row,Definition d,bool legacy)
{
    if(!counterLandingsEnabled(s)) return legacy;
    // Reuse the actor-field status admission contract; execution and the raw
    // status/scope validators remain common to both transports.
    if(WORLD_SKILL_DEFINITION(s,row,d,COUNTER_CONTEXT_CONDITIONS(s,row,d,d.conditionCount!=0)||WORLD_DURATION_KIND(s,d,WORLD_STATUS_KIND(s,d,d.kind!=0&&d.kind!=4&&d.kind!=2&&d.kind!=8)))) return true;
    if(d.enemyBuff!=0)
    {
        uint p=counterPolicy(s,row);
        return COUNTER_FIELDS_DEFINITION(s,row,d,commands[p]!=1||d.damageRoute!=1||d.damageCount!=1||((commands[p+8]&8)!=0&&actorPoolCount(s)!=1));
    }
    return false;
}
bool validCounterLandingInput(inout Runtime s,uint base,uint step)
{
    if(s.combat!=1||commands[s.inputBase+P_LANDING_META_BASE]!=1) return false;
    if(step<commands[base+3])
    {
        uint op=commands[s.inputBase+P_COMMAND_BASE+step*8];
        if(op!=2&&op!=24&&op!=30&&op!=33&&op!=37&&op!=39&&op!=40&&op!=41) return false;
    }
    for(uint j=0;j<2;j++)
    {
        uint slot=step*2+j,at=base+4104+slot*8;
        bool part=slot<actorPoolCount(s)&&commands[actorBinding(s,slot)]==1;
        if(part)
        { if(commands[at]!=1||commands[at+1]>5) return false;for(uint k=2;k<8;k++) if(commands[at+k]!=0) return false; }
        else for(uint k=0;k<8;k++) if(commands[at+k]!=0) return false;
    }
    if(step==0) { WORLD_SKILL_INIT(s) COUNTER_FIELDS_WORK_INIT(s) COUNTER_CONTEXT_INIT(s) for(uint i=P_COUNTER_LANDING_PACKET_BASE;i<P_COUNTER_LANDING_EXTRA_BASE+128*4;i++) results[s.resourceOutput+i]=0; }
    return true;
}
void sampleCounterPartShot(inout Runtime s,uint who,uint64_t coefficient,bool normal,uint64_t coreBonus,uint flags,uint64_t charge,bool optimal,uint64_t when)
{
    if(!counterLandingsEnabled(s)) return;
    uint out=s.resourceOutput+P_COUNTER_LANDING_SHOT_BASE+who*8;results[out]=0;storeNumber(out+2,0);
    uint64_t b[64];collectStats(s,who,when,b);
    uint reach=WORLD_PROJECTILE_REACH(s,who,flags,when,((flags&H_EXPLOSION)!=0 ? 3U : !f64Zero(b[S_pierce_enabled]) ? 1U : 0U));
    if(reach==0) return;
    bool any=false;
    for(uint slot=1;slot<actorPoolCount(s);slot++)
    {
        uint part=s.inputBase+P_TARGET_COUNTER_INPUT_BASE+4104+slot*8;
        if(commands[part]==1&&commands[part+1]!=0&&commands[part+1]<=reach&&results[actorPoolAt(s,slot)+1]!=0) any=true;
    }
    if(!any) return;
    results[out]=reach;
    storeNumber(out+2,damageValue(s,who,coefficient,when,normal,coreBonus,flags|H_PART,charge,optimal,true));
}
void counterPhysicalPacket(inout Runtime s,uint who,uint slot,uint generation,uint64_t amount,bool killed,uint64_t when,uint output)
{
    uint at=s.resourceOutput+P_COUNTER_LANDING_PACKET_BASE;
    for(uint i=0;i<16;i++) results[at+i]=0;
    results[at]=3;storeNumber(at+1,when);results[at+3]=who;
    uint binding=actorBinding(s,slot);results[at+4]=commands[binding];results[at+5]=commands[binding+1];results[at+6]=generation;
    // All physical HitEvent tags (including skill-formula weapon modes) are
    // normal/core/pellet/full_charge. Canonical classify_hit maps these to0.
    results[at+7]=WORLD_SKILL_FAMILY(s,0);results[at+8]=2;storeNumber(at+9,amount);storeNumber(at+11,ONE);
    uint owned=at|0x80000000U,start=collectTargetCounters(s,owned,when);
    if(s.error==0&&results[counterHead(s)+4]>start) dispatch(s,26,0,0,int(start),when,output);
    if(killed&&s.error==0)
    {
        // A threshold child may refresh the marker. Death collects that new
        // epoch only after the original immutable completion has returned.
        results[at]=4;start=collectTargetCounters(s,owned,when);
        if(s.error==0&&results[counterHead(s)+4]>start) dispatch(s,26,0,0,int(start),when,output);
    }
}
void publishCounterLanding(inout Runtime s,uint who,uint target,uint64_t amount,uint64_t when,uint output)
{
    uint slot=target&127U,receipt=actorPoolHead(s)+18;
    if(results[receipt]==0) return;
    uint binding=actorBinding(s,slot),generation=results[actorPoolAt(s,slot)];bool killed=results[receipt+1]!=0;
    uint64_t damage=commands[binding]==5 ? actorNumber(receipt+2) : amount;
    counterPhysicalPacket(s,who,slot,generation,damage,killed,when,output);
}
void deliverCounterPartGroup(inout Runtime s,uint who,uint target,uint64_t when,uint output,uint reach,uint64_t amount)
{
    if(commands[actorBinding(s,target&127U)]!=0) return;
    uint count=0;
    if(reach==0) return;
    storeNumber(actorPoolHead(s)+2,when);
    results[counterHead(s)+10]=1;
    // Native Boss.part_hits applies every reached part before returning its
    // ordered packet list. Counter/HP children cannot change that captured list.
    for(uint slot=1;slot<actorPoolCount(s)&&s.error==0;slot++)
    {
        uint input=s.inputBase+P_TARGET_COUNTER_INPUT_BASE+4104+slot*8,p=actorPoolAt(s,slot);
        if(commands[input]!=1||commands[input+1]==0||commands[input+1]>reach||results[p+1]==0) continue;
        uint gen=results[p],out=s.resourceOutput+P_COUNTER_LANDING_PART_BASE+count*8;
        uint extra=s.resourceOutput+P_COUNTER_LANDING_EXTRA_BASE+slot*4;
        if(results[extra]==0x7fffffff) { s.error=2;break; }
        uint64_t extraDealt=f64Add(actorNumber(extra+2),amount);
        if(!f64Finite(extraDealt)) { s.error=16;break; }
        results[extra]++;storeNumber(extra+2,extraDealt);
        land(s,who,ACTOR_REF|slot,amount);uint receipt=actorPoolHead(s)+18;
        results[out]=slot;results[out+1]=gen;results[out+2]=results[receipt];results[out+3]=results[receipt+1];count++;
    }
    results[counterHead(s)+10]=0;
    for(uint i=0;i<count&&s.error==0;i++)
    {
        uint at=s.resourceOutput+P_COUNTER_LANDING_PART_BASE+i*8;
        if(results[at+2]==0) continue;
        counterPhysicalPacket(s,who,results[at],results[at+1],amount,results[at+3]!=0,when,output);
        if((s.healthMask&64)!=0&&s.error==0) dispatch(s,17,0,who,0,when,output,amount);
    }
}
void deliverCounterParts(inout Runtime s,uint who,uint target,uint64_t when,uint output)
{
    uint shot=s.resourceOutput+P_COUNTER_LANDING_SHOT_BASE+who*8;
    deliverCounterPartGroup(s,who,target,when,output,results[shot],actorNumber(shot+2));
}
