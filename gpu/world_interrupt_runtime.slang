// Private interruption extras: no canonical ActorHandle, total, gauge or hit credit.
static const uint WORLD_INTERRUPT_TOTAL_BASE=785424;
static const uint INTERRUPT_AIM_DIAG_BASE=785536;
static const uint INTERRUPT_AIM_DIAG_COUNT=16;
#if defined(PORTABLE_INTERRUPT_AIM_DIAGNOSTIC) && (defined(PORTABLE_NATIVE_QUERY_DIAGNOSTIC) || defined(PORTABLE_HEAL_SHARE_DIAGNOSTIC))
#error Interrupt aim diagnostics require a separate entry
#endif
void initializeInterruptAimDiagnostics(inout Runtime s)
{
#ifdef PORTABLE_INTERRUPT_AIM_DIAGNOSTIC
    for(uint i=0;i<16+INTERRUPT_AIM_DIAG_COUNT*32;i++) results[s.resourceOutput+INTERRUPT_AIM_DIAG_BASE+i]=0;
    results[s.resourceOutput+INTERRUPT_AIM_DIAG_BASE]=0x49415231U;
#endif
}
void accumulateInterruptAimDamage(inout Runtime s,uint who,uint64_t amount)
{
    uint at=s.resourceOutput+WORLD_INTERRUPT_TOTAL_BASE+who*2;
    uint64_t sum=f64Add(actorNumber(at),amount);if(!f64Finite(sum)) { s.error=16;return; }storeNumber(at,sum);
}
uint beginInterruptAimReceipt(inout Runtime s,uint who,uint slot,uint64_t amount)
{
#ifdef PORTABLE_INTERRUPT_AIM_DIAGNOSTIC
    uint head=s.resourceOutput+INTERRUPT_AIM_DIAG_BASE,count=results[head+1];
    if(count>=INTERRUPT_AIM_DIAG_COUNT) { s.error=64;return 0; }
    uint at=head+16+count*32,p=actorPoolAt(s,slot),binding=actorBinding(s,slot);
    results[at]=who;results[at+1]=commands[binding+1];results[at+2]=results[p];
    results[at+3]=results[p+1];results[at+5]=results[p+3];
    storeNumber(at+8,actorNumber(actorPoolHead(s)+2));storeNumber(at+10,amount);
    storeNumber(at+12,actorNumber(p+4));storeNumber(at+16,actorNumber(p+6));
    storeNumber(at+20,actorNumber(s.resourceOutput+WORLD_INTERRUPT_TOTAL_BASE+who*2));
    return at;
#else
    return 0;
#endif
}
void endInterruptAimReceipt(inout Runtime s,uint at,uint who,uint slot)
{
#ifdef PORTABLE_INTERRUPT_AIM_DIAGNOSTIC
    uint p=actorPoolAt(s,slot);results[at+4]=results[p+1];results[at+6]=results[p+3];
    storeNumber(at+14,actorNumber(p+4));storeNumber(at+18,actorNumber(p+6));
    storeNumber(at+22,actorNumber(s.resourceOutput+WORLD_INTERRUPT_TOTAL_BASE+who*2));
    results[s.resourceOutput+INTERRUPT_AIM_DIAG_BASE+1]++;
#endif
}
void storeWorldSkillReachPacket(inout Runtime s,uint at,LandingReceipt r)
{
    if(r.interruptReach==0) return;
    uint index=(at-s.resourceOutput-P_LANDING_STATE_BASE)/P_LANDING_WORDS;
    if(index>=P_LANDINGS) { s.error=64;return; }
    uint old=results[at+7],to=s.resourceOutput+P_WORLD_PERIODIC_PACKET_BASE+index*38;
    uint order[128],count=0,birth=0;bool frozen=old!=0;
    if(frozen)
    {
        if(old!=index+1||results[to]>128) { s.error=64;return; }
        count=results[to];birth=results[to+1];
        for(uint i=0;i<count;i++) order[i]=(results[to+6+i/4]>>((i%4)*8))&255;
    }
    if(!storeInterruptPacket(to,order,count,birth,uint(r.interruptAmount),uint(r.interruptAmount>>32),r.interruptReach,frozen)) { s.error=64;return; }
    results[at+7]=0x80000000U|(index+1);
}
void loadWorldSkillReachPacket(inout LandingReceipt r,uint at)
{
    uint marker=results[at+7];if((marker&0x80000000U)==0) return;
    uint output=(at/P_OUTPUT_WORDS)*P_OUTPUT_WORDS,index=(at-output-P_LANDING_STATE_BASE)/P_LANDING_WORDS;
    r.interruptReach=5; // Failure sentinel, rejected before landing.
    if(index>=P_LANDINGS||(marker&0x7fffffffU)!=index+1) return;
    uint from=output+P_WORLD_PERIODIC_PACKET_BASE+index*38;
    if(!validInterruptPacket(from)) return;
    r.interruptReach=results[from+36];r.interruptAmount=sourceNumber(from+34);
    r.target=(results[from+37]&2U)!=0?index+1:0;
}
void deliverWorldInterruptGroup(inout Runtime s,uint who,uint64_t when,uint output,uint reach,uint64_t amount)
{
    uint count=0,head=actorPoolHead(s);
    for(uint slot=1;slot<actorPoolCount(s)&&s.error==0;slot++)
    {
        uint input=s.inputBase+P_TARGET_COUNTER_INPUT_BASE+4104+slot*8,p=actorPoolAt(s,slot),d=actorPoolDef(s,slot);
        if(commands[actorBinding(s,slot)]!=6||commands[input]!=2||commands[input+1]==0||commands[input+1]>reach||results[p+1]==0) continue;
        uint extra=s.resourceOutput+P_COUNTER_LANDING_EXTRA_BASE+slot*4,total=s.resourceOutput+WORLD_INTERRUPT_TOTAL_BASE+who*2;
        if(results[extra]==0x7fffffffU) { s.error=2;break; }
        uint64_t extraDealt=f64Add(actorNumber(extra+2),amount),sum=f64Add(actorNumber(total),amount);
        if(!f64Finite(extraDealt)||!f64Finite(sum)) { s.error=16;break; }
        results[extra]++;storeNumber(extra+2,extraDealt);storeNumber(total,sum);count++;
        if(!f64Less(0,loadNumber(d+2))) continue; // Native unbreakable target keeps dealt zero.
        uint64_t dealt=f64Add(actorNumber(p+4),amount);
        if(!f64Finite(dealt)) { s.error=16;break; }storeNumber(p+4,dealt);
        if(!f64Less(dealt,loadNumber(d+2)))
        {
            results[p+1]=0;results[p+2]=1;results[head+14]++;
            WorldSchedule w=frameSchedule(s);wsLog(w,5,commands[actorBinding(s,slot)+3],slot,when);s.error=w.error;
            uint64_t score=actorNumber(head+8),next=score+uint64_t(commands[d+8]);
            if(next<score) { s.error=2;break; }storeNumber(head+8,next);
            for(uint i=0;i<commands[d+6];i++) actorPoolNotice(s,slot,results[p],(commands[d+7]>>(i*3))&7);
            worldActorsApply(s);
        }
    }
    // All target HP updates precede every lifesteal callback, even after death.
    for(uint i=0;i<count&&s.error==0;i++)
        if((s.healthMask&64)!=0) dispatch(s,17,0,who,0,when,output,amount);
}
