// Policy producer reuses manual posture and the aim executor's live anchors.
static const uint CPP_INPUT=109528U,CPP_BASE=1769472U,CPP_WORDS=384U,CPP_MAGIC=0x43505631U;
uint policyInput(inout Runtime s){return s.inputBase+CPP_INPUT;}
uint policyRow(inout Runtime s,uint who){return policyInput(s)+8+who*24;}
uint policyState(inout Runtime s,uint who){return s.resourceOutput+CPP_BASE+16+who*64;}
bool policyOwner(inout Runtime s,uint who){return (commands[policyInput(s)+2]&(1U<<who))!=0;}
bool initializeCoverPolicies(inout Runtime s)
{
    uint p=policyInput(s),mask=commands[p+2];
    if(commands[p]!=CPP_MAGIC||commands[p+1]!=1||mask>=32||commands[p+3]!=5||commands[p+4]!=24||commands[p+5]!=64||commands[p+6]!=16||commands[p+7]!=0)return false;
    for(uint who=0;who<5;who++)
    {
        uint r=policyRow(s,who);if(!policyOwner(s,who)){for(uint j=0;j<24;j++)if(commands[r+j]!=0)return false;continue;}
        if(!manualControls(s)||commands[r]>1||commands[r+1]>99||commands[r+4]>5||commands[r+5]>99||commands[r+8]>1||commands[r+9]>1||commands[r+12]>3||commands[r+13]>=32||commands[r+15]>1)return false;
        if(commands[r+12]==0&&commands[r+13]!=0||commands[r+4]!=5&&commands[r+14]!=0xffffffffU||commands[r+4]==5&&commands[r+14]>=256||commands[r+9]!=0&&commands[r+4]!=2&&commands[r+4]!=3)return false;
        uint64_t extend=loadNumber(r+2),offset=loadNumber(r+6),duration=loadNumber(r+10),bound=f64FromI64(180);
        if(!f64Finite(extend)||f64Less(bound,extend&~F64_SIGN)||!f64Finite(offset)||f64Less(bound,offset&~F64_SIGN)||!f64Finite(duration)||!f64Equal(duration,ONE|F64_SIGN)&&(f64Less(duration,0)||f64Less(bound,duration)))return false;
        for(uint j=16;j<24;j++)if(commands[r+j]!=0)return false;
        s.reloadCancelOnFull[who]=commands[r+15];
    }
    if(mask==0)return true;
    uint h=s.resourceOutput+CPP_BASE;for(uint i=0;i<CPP_WORDS;i++)results[h+i]=0;results[h]=CPP_MAGIC;results[h+1]=1;results[h+2]=mask;results[h+3]=5;
    for(uint who=0;who<5;who++){uint a=policyState(s,who);storeNumber(a,ONE|F64_SIGN);storeNumber(a+2,ONE|F64_SIGN);storeNumber(a+6,ONE|F64_SIGN);}
    return true;
}
bool policyBurstRequest(inout Runtime s,uint who,uint64_t when,out uint64_t anchor,out uint64_t duration)
{
    anchor=0;duration=0;uint r=policyRow(s,who);
    if(commands[r]==0||protectionMarker(s,who,7,when)||s.phase!=5||(s.castMask&(1U<<who))==0||!f64Less(0,s.fullEnd)||f64Equal(s.fullEnd,actorNumber(policyState(s,who))))return false;
    anchor=s.fullEnd;duration=f64Add(f64Add(anchor,when^F64_SIGN),loadNumber(r+2));return f64Less(0,duration);
}
bool policyReloadRequestBody(inout Runtime s,uint who,uint64_t when,out uint64_t anchor)
{
    anchor=0;uint r=policyRow(s,who),code=commands[r+4];if(code==0||protectionMarker(s,who,7,when)||f64Less(0,s.reloadUntil[who])||f64Less(0,s.postReloadUntil[who]))return false;
    uint full=fullCapacity(s,who,s.capacity[who],true,when);if(s.ammo[who]>=int(full))return false;
    uint64_t at;if(!coordinateControlAnchor(s,who,code-1,commands[r+12],commands[r+13],commands[r+14],loadNumber(r+6),commands[r+8],when,anchor,at)||f64Less(when,at))return false;
    if(commands[r+9]!=0)
    {
        uint64_t next=actorNumber(ciHead(s)+10);if(!f64Less(0,next))next=actorNumber(ciHead(s)+12);if(!f64Less(0,next))return false;
        uint64_t base=s.rateMin[who];if(s.weaponMode[who]==2)base=f64Add(base,f64Div(f64Mul(f64Add(s.rateMax[who],base^F64_SIGN),smaller(s.warm[who],s.warmLimit[who])),s.warmLimit[who]));
        uint64_t speed=larger(uint64_t(0x3f847ae1)<<32|0x47ae147b,f64Add(ONE,f64Div(readStat(s,who,S_attack_speed_pct,when),HUNDRED)));
        uint64_t rate=larger(uint64_t(0x3f847ae1)<<32|0x47ae147b,f64Mul(base,speed)),have=f64Div(f64FromI64(s.ammo[who]),rate),need=f64Add(f64Add(anchor,when^F64_SIGN),larger(0,f64Add(next,anchor^F64_SIGN)));
        if(!f64Less(have,need))return false;
    }
    return !f64Equal(anchor,actorNumber(policyState(s,who)+2));
}
bool policyReloadRequest(inout Runtime s,uint who,uint64_t when,out uint64_t anchor)
{uint target=s.target;s.target=0;bool wanted=policyReloadRequestBody(s,who,when,anchor);s.target=target;return wanted;}
uint coverPolicyRequest(inout Runtime s,uint who,uint64_t when)
{
    if(!policyOwner(s,who)||s.modeIndex[who]>=0)return 0;uint64_t anchor,duration;uint r=policyRow(s,who);
    if(policyBurstRequest(s,who,when,anchor,duration))return commands[r+1]+1;
    if(policyReloadRequest(s,who,when,anchor))return commands[r+5]+1;return 0;
}
void applyCoverPolicies(inout Runtime s,uint who,uint64_t when)
{
    if(!policyOwner(s,who)||!controlOwns(s,who)||s.modeIndex[who]>=0||manualOpen(s,who)||results[manualState(s,who)+6]!=0)return;
    uint a=policyState(s,who),r=policyRow(s,who);uint64_t anchor,duration;uint kind=0,priority=0;
    if(policyBurstRequest(s,who,when,anchor,duration)){kind=1;priority=commands[r+1];storeNumber(a,anchor);}
    else if(policyReloadRequest(s,who,when,anchor)){kind=2;priority=commands[r+5];duration=loadNumber(r+10);storeNumber(a+2,anchor);}
    if(kind==0)return;results[a+4]=kind;storeNumber(a+6,anchor);results[controlState(s,who)+22]=0;enterManualCover(s,who,when,duration,priority,true);
}
void releaseCoverPolicy(inout Runtime s,uint who,uint64_t when)
{
    if(commands[policyInput(s)+2]==0)return;uint a=policyState(s,who),kind=results[a+4],c=controlState(s,who);
    if(kind==0||!manualOpen(s,who)&&!f64Less(when,actorNumber(c+6)))return;
    uint64_t anchor=actorNumber(a+6);uint n=results[a+5];
    for(uint i=0;i<n;i++)if(results[a+8+i*3]==kind&&f64Equal(actorNumber(a+9+i*3),anchor))return;
    if(n>=16){s.error=64;return;}results[a+8+n*3]=kind;storeNumber(a+9+n*3,anchor);results[a+5]=n+1;storeNumber(a+(kind==1?0:2),ONE|F64_SIGN);results[a+4]=0;
}
void coverPolicyHoldAnchor(inout Runtime s,uint who,uint64_t anchor)
{if(commands[policyInput(s)+2]==0)return;uint a=policyState(s,who);results[a+4]=0;storeNumber(a+6,anchor);}
