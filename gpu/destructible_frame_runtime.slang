// A continuation inside the existing DFS dispatcher. Never call dispatch from
// here: threshold/death children use the same Frame stack and work/depth budget.
bool dwFrameDescriptorValid(inout Runtime s,uint at)
{
    uint row=commands[at];
    if(row>=s.count||commands[at+1]>=0x1000000U||commands[at+2]>1||commands[at+3]!=0x44465231U||commands[at+4]<1||commands[at+4]>2||(commands[at+5]!=3&&commands[at+5]!=7)) return false;
    for(uint i=6;i<16;i++) if(commands[at+i]!=0) return false;
    Definition d=readDefinition(s.inputBase,row);
    return d.kind==3&&d.stat==0&&d.damageRoute==1&&d.damageCount==1&&d.damageHits==1&&d.damagePending==0&&d.damageNormal==0&&d.damageFlags==0&&d.healthScaling==0&&d.quantityFlags==0&&dtQuantity(d.value);
}
bool destructibleActivationHasTargets(inout Runtime s,uint row)
{
    if(row!=commands[s.inputBase+102584]) return true;
    uint count=commands[s.inputBase+97464+2320],base=s.resourceOutput+616384;
    for(uint slot=0;slot<count;slot++) { uint at=dtAt(base,slot);if(results[at]==2&&results[at+3]!=0) return true; }
    return false;
}
bool advanceDestructibleSkillFrame(inout Runtime s,inout Frame frames[32],inout int depth,inout Frame f,uint output)
{
    uint descriptor=s.inputBase+102584,row=commands[descriptor];
    if(uint(f.argument)!=row) return false;
    uint extra=s.inputBase+97464,base=output+616384,header=output+618200,count=commands[extra+2320];
    WorldSchedule w;w.input=extra;w.output=output+600016;w.count=commands[extra+1];w.error=0;
    uint scratch=output+715000+uint(depth)*544,packet=scratch+513;
    Definition d=readDefinition(s.inputBase,row);
    if(f.repeatRow==0)
    {
        if(commands[descriptor+3]!=0x44465231U||d.kind!=3||d.damageRoute!=1||d.damageHits!=1||d.damageNormal!=0||d.damagePending!=0||d.damageFlags!=0||f.repeatLeft>1||s.target!=0||!f64Equal(dtNumber(header),f.time)) { s.error=64;return true; }
        dtStore(output+705004,f.healthValue);dtStore(output+705006,0);
        uint selected=0;
        if(f.repeatLeft!=0)
        {
            frames[depth].healthPrevious=damageValue(s,d.owner,f.healthValue,f.time,false,s.coreBonus,d.damageFlags,ONE,false,false,row);
            frames[depth].skillCritRate=s.lastDamageCritRate;dtStore(output+705006,frames[depth].healthPrevious);
            for(uint slot=0;slot<count;slot++)
            {
                uint at=dtAt(base,slot);
                if(results[at+3]!=0&&results[at]==2)
                { uint p=scratch+selected*4;results[p]=slot;results[p+1]=2;results[p+2]=results[at+1];results[p+3]=results[at+2];selected++; }
            }
        }
        results[scratch+512]=selected;results[output+710000]=selected;frames[depth].repeatRow=1;f=frames[depth];
    }
    uint selected=results[scratch+512];
    if(f.repeatRow==4)
    {
        // Let the ordinary end-of-skill path own gauge/completion handling.
        frames[depth].cursor=f.repeatLeft;frames[depth].value=selected!=0?1U:0U;f=frames[depth];return false;
    }
    if(f.cursor>=selected)
    {
        frames[depth].repeatRow=4;
        if(selected!=0&&s.error==0) pushSkillHit(s,frames,depth,d,f.skillCritRate,f.time);
        return true;
    }
    uint p=scratch+f.cursor*4,slot=results[p],kind=results[p+1],identity=results[p+2],generation=results[p+3];
    if(f.repeatRow==1)
    {
        DWReceipt r=dwLand(w,base,count,header,slot,kind,identity,generation,2,f.healthPrevious,ONE,f.time);
        if(w.error!=0) { s.error=w.error;return true; }
        uint a=output+710001+f.cursor*8;results[a]=slot;results[a+1]=kind;results[a+2]=identity;results[a+3]=generation;results[a+4]=r.delivered;results[a+5]=r.broken;dtStore(a+6,r.took);
        if(r.delivered==0) { frames[depth].cursor++;return true; }
        for(uint i=0;i<16;i++) results[packet+i]=0;
        results[packet]=3;dtStore(packet+1,f.time);results[packet+3]=d.owner;results[packet+4]=kind;results[packet+5]=identity;results[packet+6]=generation;
        results[packet+7]=1;results[packet+8]=2;dtStore(packet+9,f.healthPrevious);dtStore(packet+11,ONE);results[packet+13]=commands[descriptor+1];results[scratch+529]=r.broken;
        frames[depth].repeatRow=2;uint start=collectTargetCounters(s,packet|0x80000000U,f.time);
        if(s.error==0&&results[counterHead(s)+4]>start) pushFrame(s,frames,depth,26,0,0,int(start),f.time,uint64_t(results[counterHead(s)+4]));
        return true;
    }
    if(f.repeatRow==2)
    {
        frames[depth].repeatRow=3;
        if(results[scratch+529]!=0)
        {
            results[packet]=4;uint start=collectTargetCounters(s,packet|0x80000000U,f.time);
            if(s.error==0&&results[counterHead(s)+4]>start) pushFrame(s,frames,depth,26,0,0,int(start),f.time,uint64_t(results[counterHead(s)+4]));
        }
        return true;
    }
    if(f.repeatRow==3) { frames[depth].cursor++;frames[depth].repeatRow=1;return true; }
    s.error=64;return true;
}
