uint ciHead(inout Runtime s){return s.resourceOutput+CI_STATE;}
uint ciInput(inout Runtime s){return s.inputBase+CI_BASE_INPUT;}
uint ciRow(inout Runtime s,uint who,uint i){return ciInput(s)+CI_HEADER+(who*8+i)*CI_ROW_WORDS;}
uint ciBank(inout Runtime s,uint who){return ciHead(s)+32+who*8;}
void coordinateDefaultAim(inout Runtime s,out uint64_t ax,out uint64_t ay)
{uint m=coordinateAreaInput(s);ax=cNumber(m+4);ay=cNumber(m+6);uint64_t cx,cy,d;coordinateCoreGeometry(s,ax,ay,cx,cy,d);coordinateCachedAim(s,ax,ay);}
bool coordinateAimCenter(inout Runtime s,uint slot,out uint64_t ax,out uint64_t ay)
{
    ax=0;ay=0;
#ifdef PORTABLE_COORDINATE_TYPED_AIM
    if(slot==257&&typedAimEnabled(s)){coordinateDefaultAim(s,ax,ay);return true;}
    if(slot>=129)return typedAimCenter(s,slot,ax,ay);
#endif
    if(slot==128){if(results[gcHead(s)+2]!=0){ax=actorNumber(gcSig(s)+4);ay=actorNumber(gcSig(s)+6);return f64Less(0,actorNumber(gcSig(s)+8));}uint64_t d,x=0,y=0;coordinateCoreGeometry(s,x,y,ax,ay,d);return f64Less(0,d);}
    uint frame=s.resourceOutput+CP_FRAME;
    for(uint i=0;i<results[frame+2];i++)if(results[frame+8+i*4]==slot)
    {uint m=coordinateAreaRow(s,slot),r=cRow(coordinatePoolView(s),commands[m]-1);ax=cNumber(r+6);ay=cNumber(r+8);return true;}
    return false;
}
bool coordinateAimMustBreak(inout Runtime s,uint slot)
{
#ifdef PORTABLE_COORDINATE_TYPED_AIM
 if(slot>=129)return false;
#endif
 return slot!=128&&(commands[actorBinding(s,slot)]==6||commands[actorPoolDef(s,slot)+11]!=0&&f64Less(0,loadNumber(actorPoolDef(s,slot)+2)));}
uint64_t coordinateAimReloadTotal(inout Runtime s,uint who,uint64_t when)
{
    Weapon w;w.reloadTime=s.reloadTime[who];
#ifndef PORTABLE_COORDINATE_CONTROL_COMPOSED
    if(s.modeIndex[who]>=0)w.reloadTime=loadNumber(s.inputBase+P_MODE_BASE+uint(s.modeIndex[who])*P_MODE_WORDS+8);
#endif
    uint64_t one=reloadDuration(s,w,who,when);
#ifndef PORTABLE_COORDINATE_CONTROL_COMPOSED
    if(s.modeIndex[who]>=0||s.clipCount[who]<=1)return one;
    uint full=fullCapacity(s,who,s.capacity[who],true,when),status;
#endif
    uint64_t fraction=smaller(ONE,f64Mul(f64Div(ONE,f64FromI64(s.clipCount[who])),larger(0,f64Add(ONE,f64Div(readStat(s,who,S_reload_ratio_pct,when),HUNDRED)))));
#ifdef PORTABLE_COORDINATE_CONTROL_COMPOSED
    if(!f64Less(fraction,ONE)||s.modeIndex[who]>=0)return one;
    uint full=fullCapacity(s,who,s.capacity[who],true,when),status;
#endif
    uint64_t gain=f64ToI64(f64Add(f64Mul(f64FromI64(full),fraction),uint64_t(0x3fe00000)<<32),2,status);
    if(status!=0||gain>0x7fffffff){s.error=2;return 0;}
    uint need=uint(max(int(full)-s.ammo[who],0)),unit=max(uint(gain),1U),clips=max((need+unit-1)/unit,1U);
    return f64Mul(one,f64FromI64(clips));
}
bool coordinateControlAnchor(inout Runtime s,uint who,uint code,uint stage,uint mask,uint name,uint64_t offset,uint minus,uint64_t when,out uint64_t base,out uint64_t at)
{
    base=0;at=0;if(stage!=0&&(results[controlHead(s)+9+stage]&mask)==0)return false;
    if(code==1||code==2){if(s.phase!=5||code==2&&(s.castMask&(1U<<who))==0||!f64Less(0,s.fullEnd))return false;base=s.fullEnd;}
    else if(code==3){base=actorNumber(ciHead(s)+10);if(!f64Less(0,base))base=actorNumber(ciHead(s)+12);if(!f64Less(0,base))return false;}
    else if(code==4)
    {
        bool found=false;
        for(uint i=0;i<s.carrierCount;i++)if(s.alive[i]!=0&&residentDefinition(s,i).owner==who&&residentDefinition(s,i).name==name&&f64Less(s.end[i],FOREVER)&&f64Less(when,s.end[i])){base=found?larger(base,s.end[i]):s.end[i];found=true;}
        if(!found)return false;
    }
    at=f64Add(base,offset);if(minus!=0)at=f64Add(at,coordinateAimReloadTotal(s,who,when)^F64_SIGN);
    return true;
}
bool coordinateAimWindow(inout Runtime s,uint who,uint row,uint64_t when)
{
    uint stage=commands[row+4],mask=commands[row+5];
    if(stage!=0&&(results[controlHead(s)+9+stage]&mask)==0)return false;
    uint kind=commands[row+2],code=commands[row+3];
    if(kind==0){if(code==0)return true;if(code==1)return s.gaugeCharging!=0;if(code==2)return s.gaugeCharging==0&&s.phase!=5;return s.phase==5&&(s.castMask&(1U<<who))!=0;}
    uint64_t base,at;if(!coordinateControlAnchor(s,who,code,stage,mask,commands[row+6],loadNumber(row+8),commands[row+7],when,base,at))return false;
    return !f64Less(when,at)&&f64Less(when,f64Add(at,loadNumber(row+10)));
}
uint coordinateAimPick(inout Runtime s,uint who,uint64_t when)
{
    uint n=commands[ciInput(s)+8+who];uint64_t x,y;
    for(uint i=0;i<n;i++){uint r=ciRow(s,who,i);if(coordinateAimCenter(s,commands[r],x,y)&&coordinateAimWindow(s,who,r,when))return i;}
    return 8;
}
uint coordinateAimRequest(inout Runtime s,uint who,uint64_t when)
{uint i=coordinateAimPick(s,who,when);if(i==8)return 0;uint r=ciRow(s,who,i),p=commands[r+1];return p!=0?p:coordinateAimMustBreak(s,commands[r])?31U:21U;}
uint coordinateAimForcedOwner(inout Runtime s,uint64_t when)
{
    uint h=ciHead(s),p=ciInput(s),i=results[h+15];
    while(i<commands[p+3]&&!f64Less(when,loadNumber(p+CI_SEQUENCE+i*4))){results[h+14]=commands[p+CI_SEQUENCE+i*4+2];i++;}
    results[h+15]=i;return results[h+14];
}
void coordinateAimPoint(inout Runtime s,uint who,out uint64_t ax,out uint64_t ay)
{if(results[ciHead(s)+2]!=0){uint b=ciBank(s,who);ax=actorNumber(b+1);ay=actorNumber(b+3);}else coordinateDefaultAim(s,ax,ay);}
void ciHash(inout Runtime s,uint word)
{
    uint h=ciHead(s);uint64_t a=actorNumber(h+4),b=actorNumber(h+6);
    storeNumber(h+4,(a^uint64_t(word))*uint64_t(0x100000001b3));
    storeNumber(h+6,((b<<7)|(b>>57))^uint64_t(word)*uint64_t(0x9e3779b185ebca87));
}
void coordinateCaptureAims(inout Runtime s,uint64_t when)
{
    uint camera=focusCamera(s),leadWho=5,lead=0;
    for(uint who=0;who<5;who++)if((camera&(1U<<who))!=0){leadWho=who;break;}
    if((commands[s.inputBase+P_WORLD_META_BASE+4]&1U)!=0)
    {
        for(uint slot=1;slot<actorPoolCount(s);slot++)
        {uint64_t x,y;if(coordinateAimMustBreak(s,slot)&&coordinateAimCenter(s,slot,x,y)){if(lead==0||commands[actorBinding(s,slot)]==6&&commands[actorBinding(s,lead)]!=6)lead=slot;}}
    }
    uint rest=0;
#ifdef PORTABLE_COORDINATE_TYPED_AIM
    if(typedAimEnabled(s))
    {
        // ADD is a logical auto point, never a typed shape center.
        bool adds=typedAimHasAdds(s);
        if(adds){rest=257;if(lead==0||commands[actorBinding(s,lead)]!=6)lead=257;}
        else {rest=typedAimCandidate(s);if(lead==0)lead=rest;}
    }
#endif
    uint targets[5];uint64_t xs[5],ys[5];
    for(uint who=0;who<5;who++)
    {
        targets[who]=rest;coordinateDefaultAim(s,xs[who],ys[who]);
#ifdef PORTABLE_COORDINATE_TYPED_AIM
        if(rest!=0)coordinateAimCenter(s,rest,xs[who],ys[who]);
#endif
        if((camera&(1U<<who))!=0&&lead!=0){targets[who]=lead;coordinateAimCenter(s,lead,xs[who],ys[who]);}
        uint pick=controlOwns(s,who)?coordinateAimPick(s,who,when):8;
        if(pick!=8){targets[who]=commands[ciRow(s,who,pick)];coordinateAimCenter(s,targets[who],xs[who],ys[who]);}
    }
    for(uint who=0;who<5;who++)if((camera&(1U<<who))==0)
    {
        uint pick=controlOwns(s,who)?coordinateAimPick(s,who,when):8;
        if(pick==8&&leadWho!=5&&(s.phase==5||liveMarker(s,who,S_focus_fire,when))){targets[who]=targets[leadWho];xs[who]=xs[leadWho];ys[who]=ys[leadWho];}
    }
    if(focusAimEnabled(s))
    {uint f=s.resourceOutput+P_FOCUS_STATE_BASE,mask=0;uint64_t packed=0;
     for(uint who=0;who<5;who++){packed|=uint64_t(targets[who])<<(
#ifdef PORTABLE_COORDINATE_TYPED_AIM
     (typedAimEnabled(s)?9U:8U)*who
#else
     8*who
#endif
     );if((camera&(1U<<who))!=0||s.phase==5||liveMarker(s,who,S_focus_fire,when))mask|=1U<<who;}
     storeNumber(f,packed);results[f+2]=camera;results[f+3]=uint(s.phase==5);results[f+4]++;results[f+5]=mask;results[f+6]=0x46414331U;}
    uint h=ciHead(s);results[h+2]=1;results[h+3]++;
    ciHash(s,uint(when));ciHash(s,uint(when>>32));ciHash(s,results[controlHead(s)+2]);ciHash(s,camera);ciHash(s,uint(s.phase==5));ciHash(s,s.gaugeCharging);ciHash(s,s.castMask);
    for(uint who=0;who<5;who++)
    {uint b=ciBank(s,who);results[b]=targets[who];storeNumber(b+1,xs[who]);storeNumber(b+3,ys[who]);ciHash(s,targets[who]);ciHash(s,uint(xs[who]));ciHash(s,uint(xs[who]>>32));ciHash(s,uint(ys[who]));ciHash(s,uint(ys[who]>>32));}
}
// The source clocks are observed here at the same burst transitions as native.
void coordinateAimBurstStart(inout Runtime s,uint64_t when)
{uint h=ciHead(s);uint64_t previous=actorNumber(h+8);if(!f64Less(previous,0))storeNumber(h+10,f64Add(when,f64Add(when,previous^F64_SIGN)));storeNumber(h+8,when);}
void coordinateAimBurstEnd(inout Runtime s,uint64_t when)
{
    uint h=ciHead(s);if(f64Less(0,actorNumber(h+10)))return;
#ifdef PORTABLE_COORDINATE_BURST_CONTROLS
    if(burstControls(s)){predictBurstControl(s,when);return;}
#endif
    uint64_t at=when;
    for(uint stage=1;stage<=3;stage++)
    {
        uint64_t best=FOREVER;bool found=false,explicitCandidate=false;
        for(uint who=0;who<5;who++){uint candidate;effectiveStage(s,who,when,candidate);if((candidate==stage||candidate==4)&&(commands[s.inputBase+P_WEAPON_BASE+who*P_WEAPON_WORDS+3]&1024U)!=0)explicitCandidate=true;}
        for(uint who=0;who<5;who++){uint candidate;effectiveStage(s,who,when,candidate);if(candidate!=stage&&candidate!=4)continue;found=true;best=smaller(best,larger(at,s.ready[who]));if(stage<3&&!explicitCandidate)break;}
        if(!found){storeNumber(h+12,ONE|F64_SIGN);return;}at=stage==3?f64Add(best,FULL_DELAY):f64Add(best,STAGE_DELAY);
    }
    storeNumber(h+12,at);
}
bool initializeCoordinateAim(inout Runtime s)
{
    uint p=ciInput(s),h=ciHead(s);
    if(commands[p]!=CI_MAGIC||commands[p+1]!=1||commands[p+2]!=commands[controlInput(s)+2]||commands[p+3]>CI_SEQUENCES)return false;
    for(uint i=4;i<CI_HEADER;i++)if((i<8||i>12)&&commands[p+i]!=0)return false;
    for(uint who=0;who<5;who++)
    {
        uint n=commands[p+8+who];if(n>8)return false;
        for(uint i=0;i<8;i++)
        {
            uint r=ciRow(s,who,i);if(i>=n){for(uint j=0;j<16;j++)if(commands[r+j]!=0)return false;continue;}
            uint slot=commands[r],kind=commands[r+2],code=commands[r+3];
            if(slot==0||slot!=128&&slot>=actorPoolCount(s)
#ifdef PORTABLE_COORDINATE_TYPED_AIM
               &&!typedAimValidSlot(s,slot)
#endif
               ||commands[r+1]>100||kind>1||code>(kind==0?3U:4U)||commands[r+4]>3||commands[r+5]>31||commands[r+4]==0&&commands[r+5]!=0||commands[r+7]>1)return false;
            for(uint j=12;j<16;j++)if(commands[r+j]!=0)return false;
            if(kind==0){for(uint j=6;j<12;j++)if(commands[r+j]!=0)return false;}
            else if(!f64Finite(loadNumber(r+8))||f64Less(f64FromI64(180),f64Abs(loadNumber(r+8)))||!f64Finite(loadNumber(r+10))||!f64Less(0,loadNumber(r+10))||f64Less(f64FromI64(180),loadNumber(r+10))||code!=4&&commands[r+6]!=0xffffffffU)return false;
        }
    }
    for(uint i=0;i<CI_SEQUENCES;i++)
    {uint r=p+CI_SEQUENCE+i*4;if(i>=commands[p+3]){for(uint j=0;j<4;j++)if(commands[r+j]!=0)return false;}else if(!f64Finite(loadNumber(r))||f64Less(loadNumber(r),0)||f64Less(f64FromI64(180),loadNumber(r))||i>0&&f64Less(loadNumber(r),loadNumber(r-4))||commands[r+2]>5||commands[r+3]!=0)return false;}
    for(uint i=0;i<CI_STATE_WORDS;i++)results[h+i]=0;results[h]=CI_MAGIC;results[h+1]=1;
    storeNumber(h+4,uint64_t(0xcbf29ce484222325));storeNumber(h+6,uint64_t(0x84222325cbf29ce4));
    storeNumber(h+8,ONE|F64_SIGN);storeNumber(h+10,ONE|F64_SIGN);storeNumber(h+12,ONE|F64_SIGN);
    return true;
}
