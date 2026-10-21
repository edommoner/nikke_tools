// Authored hold producers feed the common charge clock and event executor.
// No shot times, completion instants or control-owner decisions are CPU inputs.
uint controlInput(inout Runtime s) { return s.inputBase+P_WORLD_CONTROL_INPUT_BASE; }
uint controlHead(inout Runtime s) { return s.resourceOutput+P_WORLD_CONTROL_HEAD_BASE; }
uint controlState(inout Runtime s,uint who) { return s.resourceOutput+P_WORLD_CONTROL_STATE_BASE+who*32; }
uint controlOwnerInput(inout Runtime s,uint who) { return controlInput(s)+16+who*8; }
uint controlClick(inout Runtime s,uint who,uint index) { return controlInput(s)+56+(who*8+index)*16; }
uint controlSequence(inout Runtime s,uint who,uint index) { return controlInput(s)+696+(who*8+index)*8; }
uint controlThreshold(inout Runtime s,uint index) { return controlInput(s)+1016+index*4; }
bool controlDefinition(uint input,uint row)
{
    for(uint i=0;i<definition_triggerCount(input,row);i++) if(commands[input+P_EVENT_BASE+row*P_EVENT_WORDS+i*8]==39) return true;
    return false;
}
[noinline]
void initializeChargeControl(inout Runtime s)
{
    uint p=controlInput(s),total=commands[p+4];
    if(commands[p]!=0x57434831||commands[p+1]!=1||commands[p+2]>2||commands[p+3]>31||commands[p+3]!=commands[s.inputBase+WO_IN+1]||total>1280) { s.error=64;return; }
    for(uint j=5;j<16;j++) if(commands[p+j]!=0) { s.error=64;return; }
    uint offset=0;
    for(uint who=0;who<5;who++)
    {
        uint a=controlOwnerInput(s,who),nc=commands[a],ns=commands[a+1],first=commands[a+2],count=commands[a+3],kind=commands[a+4];
        if(nc>8||ns>8||first!=offset||first+count>total||count>256||kind>2||kind==0&&nc!=0||kind==2&&ns!=0) { s.error=64;return; }
        for(uint j=5;j<8;j++) if(commands[a+j]!=0) { s.error=64;return; }
        for(uint i=0;i<8;i++)
        {
            uint row=controlClick(s,who,i);
            if(i>=nc) { for(uint j=0;j<16;j++) if(commands[row+j]!=0) s.error=64; }
            else
            {
                uint mode=commands[row],window=commands[row+1];uint64_t lead=loadNumber(row+6);
                if((mode!=0&&mode!=2&&mode!=3&&mode!=4)||window>4||commands[row+2]>99||commands[row+3]>3||commands[row+4]>31||commands[row+3]==0&&commands[row+4]!=0||commands[row+5]!=0||!f64Finite(lead)||f64Less(f64FromI64(180),f64Abs(lead))||(mode==3)!=(window==2)||(mode==4)!=(window==4)||kind==2&&(mode==2||mode==4)) { s.error=64;return; }
                for(uint j=8;j<16;j++) if(commands[row+j]!=0) s.error=64;
            }
            row=controlSequence(s,who,i);
            if(i>=ns) { for(uint j=0;j<8;j++) if(commands[row+j]!=0) s.error=64; }
            else
            {
                uint64_t at=loadNumber(row),until=loadNumber(row+2);
                if(!f64Finite(at)||f64Less(at,0)||f64Less(f64FromI64(180),at)||i!=0&&f64Less(at,loadNumber(row-8))||!f64Finite(until)||!f64Equal(until,ONE|F64_SIGN)&&(f64Less(until,0)||f64Less(f64FromI64(180),until))) { s.error=64;return; }
                for(uint j=4;j<8;j++) if(commands[row+j]!=0) s.error=64;
            }
        }
        uint seen[8];for(uint j=0;j<8;j++) seen[j]=0;
        for(uint i=first;i<first+count;i++)
        {
            uint row=controlThreshold(s,i),tag=commands[row+1];uint64_t seconds=loadNumber(row+2);
            if(tag>=256) { s.error=64;return; }
            if(commands[row]!=who||tag>=256||!f64Finite(seconds)||f64Less(seconds,0)||i>first&&f64Less(seconds,loadNumber(row-2))||(seen[tag/32]&(1U<<(tag%32)))!=0) { s.error=64;return; }
            seen[tag/32]|=1U<<(tag%32);
        }
        offset+=count;
    }
    if(offset!=total||s.error!=0) { s.error=64;return; }
    for(uint i=total;i<1280;i++) for(uint j=0;j<4;j++) if(commands[controlThreshold(s,i)+j]!=0) { s.error=64;return; }
    uint referenced[40];for(uint j=0;j<40;j++) referenced[j]=0;
    for(uint row=0;row<s.count;row++) for(uint slot=0;slot<definition_triggerCount(s.inputBase,row);slot++)
    {
        uint at=s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8;if(commands[at]!=39) continue;
        uint who=definition_owner(s.inputBase,row),a=controlOwnerInput(s,who),first=commands[a+2],end=first+commands[a+3],found=1280,status;
        uint64_t count=loadNumber(at+1),integer=f64ToI64(count,1,status);
        if(commands[at+4]>=256||commands[at+3]>1||int(commands[at+7])!=-1||status!=0||integer==0||integer>0x7fffffff||!f64Equal(count,f64FromI64(integer))) { s.error=64;return; }
        for(uint i=first;i<end;i++) if(commands[controlThreshold(s,i)+1]==commands[at+4]) { found=i;break; }
        if(found==1280) { s.error=64;return; }
        if(!f64Equal(loadNumber(controlThreshold(s,found)+2),loadNumber(at+5))) { s.error=64;return; }
        referenced[found/32]|=1U<<(found%32);
    }
    for(uint i=0;i<total;i++) if((referenced[i/32]&(1U<<(i%32)))==0) { s.error=64;return; }
    for(uint i=P_WORLD_CONTROL_STATE_BASE;i<P_WORLD_CONTROL_TRACE_BASE+P_WORLD_CONTROL_TRACE_COUNT*8;i++) results[s.resourceOutput+i]=0;
    uint h=controlHead(s);results[h]=0x57434831;results[h+3]=commands[p+3];storeNumber(h+4,ONE|F64_SIGN);
    for(uint who=0;who<5;who++)
    {
        uint a=controlState(s,who);for(uint j=2;j<=12;j+=2) storeNumber(a+j,ONE|F64_SIGN);results[a+14]=0xffffffff;
    }
}
bool controlWindow(inout Runtime s,uint who,uint row)
{
    uint stage=commands[row+3],mask=commands[row+4],window=commands[row+1];
    if(stage!=0&&(results[controlHead(s)+9+stage]&mask)==0) return false;
    if(window==0) return true;
    if(window==1) return s.gaugeCharging!=0;
    if(window==2) return s.gaugeCharging==0&&s.phase!=5;
    return s.phase==5&&(s.castMask&(1U<<who))!=0;
}
uint controlPick(inout Runtime s,uint who,bool holdOnly)
{
    uint count=commands[controlOwnerInput(s,who)];
    for(uint i=0;i<count;i++)
    {
        uint row=controlClick(s,who,i),mode=commands[row];
        if(holdOnly&&mode!=2&&mode!=3&&mode!=4) continue;
        if(controlWindow(s,who,row)) return i;
    }
    return 8;
}
bool controlOwns(inout Runtime s,uint who)
{ return commands[controlInput(s)+2]!=0||results[controlHead(s)+2]==who+1; }
uint controlRequest(inout Runtime s,uint who,uint64_t when)
{
    uint a=controlState(s,who),input=controlOwnerInput(s,who),index=results[a+1];
    if(index<commands[input+1]&&!f64Less(when,loadNumber(controlSequence(s,who,index)))) return 100; // priority99 plus presence.
    if(f64Less(when,actorNumber(a+6))&&(results[a+14]==0xffffffff||controlWindow(s,who,controlClick(s,who,results[a+14])))) return results[a+15]+1;
    uint selected=controlPick(s,who,false);if(selected==8) return 0;
    uint row=controlClick(s,who,selected);return commands[row]==0?0:commands[row+2]+1;
}
void releaseChargeControl(inout Runtime s,uint who,uint64_t when)
{
    uint a=controlState(s,who);
    if(!f64Less(when,actorNumber(a+6))) return;
    storeNumber(a+6,ONE|F64_SIGN);results[a+14]=0xffffffff;
    if(results[a+22]==0) return;
    uint count=results[a+29],base=s.resourceOutput+P_WORLD_CONTROL_HISTORY_BASE+who*32;uint64_t anchor=actorNumber(a+8);
    for(uint i=0;i<count;i++) if(f64Equal(actorNumber(base+i*2),anchor)) return;
    if(count>=16) { s.error=64;return; }
    storeNumber(base+count*2,anchor);results[a+29]=count+1;storeNumber(a+8,ONE|F64_SIGN);results[a+22]=0;
}
uint controlTrace(inout Runtime s,uint kind,uint who,uint64_t when)
{
    uint h=controlHead(s),count=results[h+1];if(count>=P_WORLD_CONTROL_TRACE_COUNT) { s.error=64;return 0; }
    uint at=s.resourceOutput+P_WORLD_CONTROL_TRACE_BASE+count*8;results[h+1]=count+1;results[at]=kind;results[at+1]=who;storeNumber(at+2,when);return at;
}
[noinline]
void arbitrateChargeControl(inout Runtime s,uint64_t when)
{
    if(s.error!=0) return;
    uint request[5],edge[5],count=0,h=controlHead(s),old=results[h+2],owner=old,preempted=0;
    for(uint who=0;who<5;who++)
    {
        uint a=controlState(s,who);request[who]=controlRequest(s,who,when);edge[who]=uint(request[who]!=0&&results[a+16]==0);results[a+16]=uint(request[who]!=0);count+=uint(request[who]!=0);
    }
    uint mode=commands[controlInput(s)+2];if(mode==2&&count>1) { s.error=64;return; }
    if(mode==0)
    {
        if(owner!=0&&request[owner-1]==0)
        { if(results[controlState(s,owner-1)+14]!=0xffffffff) releaseChargeControl(s,owner-1,when);owner=0; }
        uint best=5;
        for(uint who=0;who<5;who++)
        {
            if(request[who]==0||owner==who+1) continue;
            if(owner!=0&&!(request[who]>request[owner-1]||request[who]==request[owner-1]&&edge[who]!=0)) continue;
            if(best==5||request[who]>request[best]||request[who]==request[best]&&edge[who]>edge[best]) best=who;
        }
        if(best!=5)
        {
            if(owner!=0)
            {
                preempted=owner;releaseChargeControl(s,owner-1,when);uint a=controlState(s,owner-1);
                if(results[a+27]==0x7fffffff||results[h+6]==0x7fffffff) { s.error=2;return; }
                results[a+27]++;results[h+6]++;
            }
            owner=best+1;
        }
        if(owner!=old&&owner!=0) storeNumber(h+4,when);
    }
    uint camera=mode==0&&owner!=0 ? 1U<<(owner-1) : commands[controlInput(s)+3];
    bool changed=results[h+8]==0||owner!=old||camera!=results[h+3]||preempted!=0;results[h+2]=owner;results[h+3]=camera;
    if(changed)
    {
        uint at=controlTrace(s,0,owner,when);if(s.error!=0) return;
        results[at+4]=camera;results[at+5]=preempted;results[h+8]++;
    }
}
[noinline]
void advanceChargeControl(inout Runtime s,uint who,uint64_t when)
{
    uint a=controlState(s,who),input=controlOwnerInput(s,who),close=results[a+14];
    if(close!=0xffffffff&&!controlWindow(s,who,controlClick(s,who,close)))
    { results[a+14]=0xffffffff;storeNumber(a+6,ONE|F64_SIGN);results[a+22]=0; }
    if(controlOwns(s,who))
    {
        if(commands[input+4]!=0)
        {
            uint selected=controlPick(s,who,true);
            if(selected!=8)
            {
                uint row=controlClick(s,who,selected),mode=commands[row];
                if(mode==3)
                { results[a+14]=selected;storeNumber(a+6,uint64_t(0x7ff00000)<<32);results[a+15]=commands[row+2]; }
                else if(f64Less(0,s.fullEnd)&&!f64Equal(s.fullEnd,actorNumber(a+8)))
                {
                    storeNumber(a+8,s.fullEnd);results[a+22]=1;results[a+15]=commands[row+2];uint64_t lead=loadNumber(row+6);
                    if(mode==2) storeNumber(a+6,f64Add(s.fullEnd,lead^F64_SIGN));
                    else if(commands[input+3]!=0)
                    {
                        uint last=commands[input+2]+commands[input+3]-1;uint64_t judge=f64Add(s.fullEnd,lead),need=loadNumber(controlThreshold(s,last)+2);
                        storeNumber(a+12,judge);storeNumber(a+10,f64Add(f64Add(judge,effectiveCharge(s,who,s.chargeTime[who],when)^F64_SIGN),need^F64_SIGN));
                    }
                }
            }
        }
        uint index=results[a+1],n=commands[input+1];
        while(index<n&&!f64Less(when,loadNumber(controlSequence(s,who,index))))
        {
            if(commands[input+4]!=0) { results[a+14]=0xffffffff;storeNumber(a+6,loadNumber(controlSequence(s,who,index)+2));results[a+15]=99; }
            index++;
        }
        results[a+1]=index;
    }
    if(results[a+24]==2&&!f64Less(when,s.nextShot[who])) results[a+24]=0;
}
bool waitChargeControl(inout Runtime s,uint who,uint64_t charge,uint64_t when)
{
    uint a=controlState(s,who);uint64_t start=actorNumber(a+10);
    return f64Less(0,start)&&f64Less(when,start)&&!f64Less(f64Add(effectiveCharge(s,who,charge,when),uint64_t(0x3fd99999)<<32|0x9999999a),f64Add(start,when^F64_SIGN));
}
void startChargeControl(inout Runtime s,uint who,uint64_t charge,uint64_t when)
{
    uint a=controlState(s,who),input=controlOwnerInput(s,who),first=commands[input+2],end=first+commands[input+3];
    results[a]=0;storeNumber(a+2,ONE|F64_SIGN);storeNumber(a+4,ONE|F64_SIGN);results[a+24]=1;
    for(uint i=first;i<end;i++) results[s.resourceOutput+P_WORLD_CONTROL_FIRED_BASE+i/32]&=~(1U<<(i%32));
    uint64_t start=actorNumber(a+10);
    if(f64Less(0,start)&&!f64Less(when,start)&&end!=first)
    {
        uint64_t need=loadNumber(controlThreshold(s,end-1)+2);
        storeNumber(a+6,f64Add(f64Add(f64Add(when,effectiveCharge(s,who,charge,when)),need),uint64_t(0x3f911111)<<32|0x11111111));storeNumber(a+10,ONE|F64_SIGN);
    }
}
[noinline]
bool readyChargeControl(inout Runtime s,uint who,uint64_t when,uint output)
{
    uint a=controlState(s,who);
    if(results[a]==0)
    {
        if(f64Less(when,s.chargeUntil[who])) return false;
        results[a]=1;storeNumber(a+2,when);storeNumber(a+4,s.chargeUntil[who]);
    }
    s.chargeUntil[who]=actorNumber(a+4);uint64_t held=f64Add(when,actorNumber(a+2)^F64_SIGN),reload=s.reloadUntil[who];uint epoch=s.modeEpoch[who],input=controlOwnerInput(s,who),first=commands[input+2],end=first+commands[input+3];
    for(uint i=first;i<end&&s.error==0;i++)
    {
        uint bit=1U<<(i%32),fired=s.resourceOutput+P_WORLD_CONTROL_FIRED_BASE+i/32,p=controlThreshold(s,i);
        if((results[fired]&bit)!=0||f64Less(held,loadNumber(p+2))) continue;
        results[fired]|=bit;uint at=controlTrace(s,1,who,when);if(s.error!=0) return true;
        results[at+4]=commands[p+1];storeNumber(at+6,actorNumber(a+2));if((s.downMask&(1U<<who))==0) dispatch(s,0,39,who,int(commands[p+1]),when,output);
    }
    if(s.error!=0||s.charging[who]==0||s.modeEpoch[who]!=epoch||s.reloadUntil[who]!=reload||(s.downMask&(1U<<who))!=0) return true;
    return !f64Less(actorNumber(a+6),0)&&f64Less(when,actorNumber(a+6));
}
void cancelChargeControl(inout Runtime s,uint who,bool release)
{
    uint a=controlState(s,who);results[a]=0;storeNumber(a+2,ONE|F64_SIGN);storeNumber(a+4,ONE|F64_SIGN);results[a+24]=0;
    if(release||s.modeIndex[who]<0) { storeNumber(a+6,ONE|F64_SIGN);results[a+14]=0xffffffff; }
}
void finishChargeControl(inout Runtime s,uint who)
{ cancelChargeControl(s,who,true);results[controlState(s,who)+24]=2; }
