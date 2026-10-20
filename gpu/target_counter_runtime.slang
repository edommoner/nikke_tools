// Target-scoped resources. Activation, expiry, carrier allocation and child
// dispatch stay in the common executor; neither backend owns a second loop.
uint counterHead(inout Runtime s) { return s.resourceOutput+P_TARGET_COUNTER_HEAD; }
uint counterPolicy(inout Runtime s,uint definition) { return s.inputBase+P_TARGET_COUNTER_INPUT_BASE+8+definition*16; }
uint counterResource(inout Runtime s,uint slot) { return s.resourceOutput+P_TARGET_COUNTER_RESOURCE_BASE+slot*16; }
uint counterReady(inout Runtime s,uint index) { return s.resourceOutput+P_TARGET_COUNTER_READY_BASE+index*20; }
bool targetCountersEnabled(inout Runtime s) { return commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE]==0x57433031; }
bool targetCounterLiteralRoot(inout Runtime s,uint64_t through,bool autonomousReached)
{
    if(autonomousReached) return true;
    if(!targetCountersEnabled(s)||commands[s.inputBase+2]==0) return false;
    // Literal resource tests neither advance the world nor fire weapons. Their
    // own full sidecar/action admission runs before executing the first action.
    for(uint i=0;i<commands[s.inputBase+2];i++)
    {
        uint at=s.inputBase+P_COMMAND_BASE+i*8;uint64_t time=loadNumber(at+1);
        if(commands[at]!=43||!f64Finite(time)||f64Less(time,0)||f64Less(through,time)) return false;
    }
    return true;
}
bool counterActorEqual(uint at,uint kind,uint id,uint gen)
{ return results[at]==kind&&results[at+1]==id&&results[at+2]==gen; }
bool counterActorDead(inout Runtime s,uint kind,uint id,uint gen)
{
    for(uint i=0;i<results[counterHead(s)+3];i++)
        if(counterActorEqual(s.resourceOutput+P_TARGET_COUNTER_DEAD_BASE+i*3,kind,id,gen)) return true;
    return false;
}
bool targetCounterDeadDefinition(inout Runtime s,uint row)
{
    if(!targetCountersEnabled(s)) return false;
    uint p=counterPolicy(s,row);
    return commands[p]!=0&&counterActorDead(s,commands[p+1],commands[p+2],commands[p+3]);
}
void prepareTargetCounter(inout Runtime s,uint slot,uint64_t when)
{
    if(!targetCountersEnabled(s)) return;
    uint row=s.carrierDefinition[slot],p=counterPolicy(s,row);if(commands[p]==0) return;
    uint h=counterHead(s),at=counterResource(s,slot);uint64_t credit=0;
    if((commands[p+8]&1)!=0&&results[at+1]==s.entryOrder[slot]&&results[at+2]==0&&results[at+3]!=0&&counterActorEqual(at+8,commands[p+1],commands[p+2],commands[p+3])&&f64Less(when,actorNumber(at+6))) credit=actorNumber(at+4);
    if(results[h+1]==0x7fffffff) { s.error=2;return; }
    results[at]=++results[h+1];results[at+1]=s.entryOrder[slot];results[at+2]=0;results[at+3]=row+1;
    storeNumber(at+4,credit);storeNumber(at+6,s.end[slot]);
    for(uint j=0;j<3;j++) results[at+8+j]=commands[p+1+j];
    results[at+11]=commands[p+9];results[at+12]=commands[p+10];results[at+13]=commands[p+8];results[at+14]=commands[p+6];results[at+15]=commands[p+7];
}
// All siblings are marked done before the caller pushes any completion frame.
uint collectTargetCounters(inout Runtime s,uint action,uint64_t when)
{
    uint h=counterHead(s),start=results[h+4],kind=commands[action],actorKind=commands[action+4],id=commands[action+5],gen=commands[action+6];
    if(kind==3&&counterActorDead(s,actorKind,id,gen)) return start;
    if(kind==4)
    {
        if(counterActorDead(s,actorKind,id,gen)) return start;
        uint count=results[h+3];if(count==512) { s.error=64;return start; }
        uint dead=s.resourceOutput+P_TARGET_COUNTER_DEAD_BASE+count*3;
        results[dead]=actorKind;results[dead+1]=id;results[dead+2]=gen;results[h+3]=count+1;
    }
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],at=counterResource(s,slot);
        if(s.alive[slot]==0||results[at+3]==0||results[at+1]!=s.entryOrder[slot]||results[at+2]!=0||!f64Less(when,actorNumber(at+6))||!counterActorEqual(at+8,actorKind,id,gen)) continue;
        uint p=counterPolicy(s,results[at+3]-1);
        if(kind==3)
        {
            uint who=commands[action+3],family=commands[action+7],outcome=commands[action+8];uint64_t credit=loadNumber(action+11);
            if(f64Zero(credit)||(commands[p+6]&(1U<<family))==0||(commands[p+7]&(1U<<outcome))==0||(commands[p+8]&4)!=0&&who!=commands[p+9]) continue;
            credit=smaller(loadNumber(p+4),f64Add(actorNumber(at+4),credit));storeNumber(at+4,credit);
            if(f64Less(credit,loadNumber(p+4))) continue;
        }
        uint index=results[h+4];if(index==4096) { s.error=64;return start; }
        results[at+2]=1;uint dst=counterReady(s,index);results[h+4]=index+1;
        results[dst]=slot;results[dst+1]=results[at+1];results[dst+2]=results[at];results[dst+3]=results[at+3]-1;
        results[dst+4]=kind==3?1:((commands[p+8]&2)!=0?2:3);
        for(uint j=0;j<3;j++) results[dst+5+j]=results[at+8+j];
        storeNumber(dst+8,actorNumber(at+4));
        if(kind==3)
        {
            results[dst+10]=commands[action+3];results[dst+11]=commands[action+7];results[dst+12]=commands[action+8];results[dst+13]=commands[action+13];
            storeNumber(dst+14,loadNumber(action+9));storeNumber(dst+16,loadNumber(action+11));results[dst+18]=1;
        }
    }
    return start;
}
void advanceTargetCounter(inout Runtime s,inout Frame frames[32],inout int depth)
{
    Frame f=frames[depth];uint h=counterHead(s);
    if(f.event==0) { frames[depth].event=1;frames[depth].cursor=uint(f.argument);return; }
    if(f.cursor>=uint(f.value)) { depth--;return; }
    uint src=counterReady(s,f.cursor),slot=results[src],at=counterResource(s,slot),row=results[src+3];
    if(f.event==1)
    {
        frames[depth].event=2;
        if(results[src+4]!=3)
        {
            if(results[h+2]==0x7fffffff||results[h+6]==128) { s.error=64;return; }
            results[h+2]++;uint out=s.resourceOutput+P_TARGET_COUNTER_TRACE_BASE+results[h+6]*24;results[h+6]++;
            for(uint j=0;j<20;j++) results[out+j]=results[src+j];storeNumber(out+20,f.time);results[out+22]=results[h+2];results[out+23]=s.alive[slot];
            // The immutable ready row survives refresh in the synchronous child.
            pushFrame(s,frames,depth,0,58,definition_owner(s.inputBase,row),int(definition_name(s.inputBase,row)),f.time);
        }
        return;
    }
    frames[depth].event=1;frames[depth].cursor=f.cursor+1;
    if(results[at+1]==results[src+1]&&results[at]==results[src+2])
    {
        results[at+3]=0;
        if(s.alive[slot]!=0&&s.entryOrder[slot]==results[src+1])
        {
            uint begin=s.removalCount;queueCarrierEnd(s,slot,1);
            if(s.error==0&&s.removalCount>begin) pushFrame(s,frames,depth,9,0,0,int(begin),f.time);
        }
    }
}
bool validTargetCounterAction(uint at)
{
    uint kind=commands[at];uint64_t time=loadNumber(at+1);
    if(kind<1||kind>4||!f64Finite(time)||f64Less(time,0)||f64Less(f64FromI64(180),time)||commands[at+14]!=0||commands[at+15]!=0) return false;
    if(kind<3) { for(uint j=3;j<14;j++) if(commands[at+j]!=0) return false;return true; }
    if(commands[at+4]>5||commands[at+5]>=0x10000000U||commands[at+6]==0||commands[at+6]>=0x80000000U) return false;
    if(kind==4) { if(commands[at+3]!=0) return false;for(uint j=7;j<14;j++) if(commands[at+j]!=0) return false;return true; }
    uint family=commands[at+7],outcome=commands[at+8];uint64_t damage=loadNumber(at+9),credit=loadNumber(at+11),limit=f64FromI64(1000000000000000UL);limit=f64Mul(limit,limit);
    return commands[at+3]<5&&family<4&&outcome<3&&commands[at+13]<0x1000000U&&f64Finite(damage)&&f64Finite(credit)&&!f64Less(damage,0)&&!f64Less(credit,0)&&!f64Less(limit,damage)&&!f64Less(limit,credit)&&(outcome==2||f64Zero(damage))&&(outcome!=0||f64Zero(credit));
}
bool initializeTargetCounters(inout Runtime s)
{
    uint base=s.inputBase+P_TARGET_COUNTER_INPUT_BASE;
    if(commands[base]==0) { for(uint j=1;j<5128;j++) if(commands[base+j]!=0) return false;return true; }
    if(!targetCountersEnabled(s)||!actorStacksEnabled(s)||commands[base+1]!=1||commands[base+2]!=s.count||commands[base+3]!=commands[s.inputBase+2]||commands[base+4]!=16||commands[base+5]!=16||commands[base+6]!=0||commands[base+7]!=0) return false;
    uint definitions=0;
    for(uint row=0;row<256;row++)
    {
        uint at=counterPolicy(s,row);
        if(commands[at]==0) { for(uint j=1;j<16;j++) if(commands[at+j]!=0) return false;continue; }
        if(row>=s.count||commands[at]!=1||commands[at+1]>5||commands[at+2]>=0x10000000U||commands[at+3]==0||commands[at+3]>=0x80000000U||commands[at+6]==0||commands[at+6]>15||(commands[at+7]!=2&&commands[at+7]!=4&&commands[at+7]!=6)||commands[at+8]>15||commands[at+9]>=5||commands[at+10]>=256) return false;
        uint64_t threshold=loadNumber(at+4),duration=loadNumber(at+11);
        if(!f64Finite(threshold)||!f64Less(0,threshold)||f64Less(f64FromI64(1000000000000UL),threshold)||!f64Finite(duration)||!(f64Equal(duration,ONE|F64_SIGN)||f64Less(0,duration)&&!f64Less(f64FromI64(180),duration))) return false;
        if((commands[at+8]&8)!=0&&(commands[at+1]!=0||commands[at+2]!=0||commands[at+3]!=1)) return false;
        for(uint j=13;j<16;j++) if(commands[at+j]!=0) return false;
        Definition d=readDefinition(s.inputBase,row);
        if(d.kind!=4||d.stat!=0||d.maxStack!=1||d.owner!=commands[at+9]||d.name!=commands[at+10]||d.enemyBuff!=1||d.conditionCount!=0||!f64Zero(d.value)||!f64Zero(d.interval)||d.bulletDuration!=0||!f64Equal(d.duration,duration)) return false;
        for(uint prior=0;prior<row;prior++)
        {
            uint p=counterPolicy(s,prior);if(commands[p]==0||commands[p+9]!=d.owner||commands[p+10]!=d.name) continue;
            for(uint j=1;j<9;j++) if(commands[p+j]!=commands[at+j]) return false;
        }
        definitions++;
    }
    if(definitions==0) return false;
    // Physical/skill landing integration is a subsequent gate. This literal
    // resource stage cannot silently admit a damage child with no impact hook.
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        if(d.kind!=0&&d.kind!=4||d.conditionCount!=0||d.enemyBuff!=0&&commands[counterPolicy(s,row)]==0) return false;
    }
    uint64_t previous=0;
    for(uint step=0;step<64;step++)
    {
        uint at=base+4104+step*16;
        if(step<commands[base+3])
        {
            if(!validTargetCounterAction(at)||f64Less(loadNumber(at+1),previous)) return false;
            previous=loadNumber(at+1);uint cmd=s.inputBase+P_COMMAND_BASE+step*8;
            if(commands[cmd]!=43||loadNumber(cmd+1)!=previous||commands[cmd+3]!=step) return false;
            for(uint j=4;j<8;j++) if(commands[cmd+j]!=0) return false;
        }
        else for(uint j=0;j<16;j++) if(commands[at+j]!=0) return false;
    }
    for(uint j=P_TARGET_COUNTER_HEAD;j<P_TARGET_COUNTER_QUERY_BASE+64*16;j++) results[s.resourceOutput+j]=0;
    results[counterHead(s)]=0x57433031;return true;
}
void snapshotTargetCounters(inout Runtime s,uint step)
{
    uint h=counterHead(s),out=s.resourceOutput+P_TARGET_COUNTER_QUERY_BASE+step*16,count=0;uint64_t credit=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass],at=counterResource(s,slot);
        if(s.alive[slot]==0||results[at+3]==0||results[at+1]!=s.entryOrder[slot]) continue;
        if(count<2) { uint p=out+8+count*4;results[p]=results[at+1];results[p+1]=results[at];storeNumber(p+2,actorNumber(at+4)); }
        count++;credit=f64Add(credit,actorNumber(at+4));
    }
    results[out]=count;storeNumber(out+1,credit);results[out+3]=results[h+2];results[out+4]=results[h+1];results[out+5]=results[h+3];results[out+6]=results[h+6];results[out+7]=results[h+4];
}
bool targetCounterCommand(inout Runtime s,uint at,uint step,uint64_t when,uint output)
{
    if(!targetCountersEnabled(s)||commands[at+3]!=step) return false;
    uint action=s.inputBase+P_TARGET_COUNTER_INPUT_BASE+4104+step*16,kind=commands[action];
    beginLazyRoot(s,when);tick(s,when,output);if(s.error!=0) return true;
    if(kind==1||kind==2) dispatch(s,0,kind==1?0:7,0,0,when,output);
    else
    {
        uint start=collectTargetCounters(s,action,when);
        if(s.error==0&&results[counterHead(s)+4]>start) dispatch(s,26,0,0,int(start),when,output);
    }
    if(s.error==0) snapshotTargetCounters(s,step);return true;
}
