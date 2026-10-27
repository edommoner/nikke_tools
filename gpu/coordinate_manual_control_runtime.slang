// Persistent explicit-cover state in the unused sampled output tail.
#ifdef PORTABLE_PHYSICAL_LOCK_COVER
#include "physical_lock_cover_layout.slang"
static const uint CMC_BASE=PL_COVER_BASE;
#else
static const uint CMC_BASE=919744U;
#endif
static const uint CMC_WORDS=80U;
uint manualState(inout Runtime s,uint who){return s.resourceOutput+CMC_BASE+who*16;}
bool manualControls(inout Runtime s){return commands[controlInput(s)+1]==3;}
void initializeManualControls(inout Runtime s)
{
    if(!manualControls(s))return;
    uint tag=commands[controlInput(s)+6];bool associated=tag==0xffffffffU;
    for(uint row=0;row<s.count;row++)for(uint i=0;i<definition_triggerCount(s.inputBase,row);i++)
    {uint e=s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+i*8;if(commands[e]==31&&commands[e+4]==tag)associated=true;}
    if(!associated){s.error=64;return;}
    for(uint who=0;who<5;who++){uint a=manualState(s,who);for(uint j=0;j<16;j++)results[a+j]=0;storeNumber(a+2,ONE|F64_SIGN);results[a+15]=0x4d435631U;}
}
bool manualCharging(inout Runtime s,uint who)
{return s.charging[who]!=0&&(!manualControls(s)||results[manualState(s,who)+9]==0);}
bool manualBaseReload(inout Runtime s,uint who)
{return manualControls(s)&&s.weaponMode[who]!=1&&results[manualState(s,who)+10]!=0;}
bool manualOpen(inout Runtime s,uint who)
{if(!manualControls(s))return false;uint a=manualState(s,who);return (results[a]&2)!=0||((results[a]&1)!=0&&f64Less(0,actorNumber(a+2)));}
bool manualCovering(inout Runtime s,uint who,uint64_t when)
{if(!manualOpen(s,who))return false;uint a=manualState(s,who);return (results[a]&2)!=0||f64Less(when,actorNumber(a+2));}
void exitManualCover(inout Runtime s,uint who,uint64_t when)
{
    uint a=manualState(s,who);if(!manualOpen(s,who))return;
    results[a]=0;storeNumber(a+2,ONE|F64_SIGN);results[a+8]++;s.nextShot[who]=larger(s.nextShot[who],when);
    if(s.weaponMode[who]==1)results[controlState(s,who)+24]=0; // Exit changes posture, preserving a later authored hold.
}
void resetManualCover(inout Runtime s,uint who)
{
    if(!manualControls(s))return;uint a=manualState(s,who);results[a]=0;results[a+1]=0;results[a+6]=0;results[a+9]=0;results[a+10]=0;storeNumber(a+2,ONE|F64_SIGN);
}
void enterManualCover(inout Runtime s,uint who,uint64_t when,uint64_t duration,uint priority,bool fresh)
{
#ifdef PORTABLE_COORDINATE_SQUAD_ACTIONS
    clearSquadCoverFlag(s,who);
#endif
    uint a=controlState(s,who),m=manualState(s,who);results[m]=f64Less(duration,0)?2U:1U;results[m+1]=0;results[m+6]=1;results[m+7]++;storeNumber(m+2,f64Less(duration,0)?ONE|F64_SIGN:f64Add(when,duration));storeNumber(m+4,when);
        results[m+9]=1;if(fresh)invalidateNativeNumeric(s);
        if(s.weaponMode[who]==1){s.charging[who]=0;cancelChargeControl(s,who,true);s.nextShot[who]=when;}
        else{results[a]=0;storeNumber(a+2,ONE|F64_SIGN);storeNumber(a+4,ONE|F64_SIGN);storeNumber(a+6,ONE|F64_SIGN);results[a+14]=0xffffffff;}
        results[a+15]=priority;
        uint tag=commands[controlInput(s)+6];if(tag!=0xffffffffU)dispatch(s,0,31,who,int(tag),when,s.resourceOutput);
        Weapon w;selectWeapon(s,who,when,w);w.reloadTime=s.reloadTime[who]; // Manual input sees the restored base weapon.
        if(!f64Less(0,s.reloadUntil[who])&&s.ammo[who]<int(w.capacity)){results[m+10]=1;beginReload(s,w,who,when);results[m+10]=0;}
}
void pumpManualSequences(inout Runtime s,uint who,uint64_t when)
{
    uint a=controlState(s,who),input=controlOwnerInput(s,who),index=results[a+1],n=commands[input+1];
    while(index<n&&!f64Less(when,loadNumber(controlSequence(s,who,index)))&&s.error==0)
    {
        uint row=controlSequence(s,who,index);index++;results[a+1]=index;
        if(commands[row+4]==0)
        {if(commands[input+4]!=0){results[a+14]=0xffffffff;storeNumber(a+6,loadNumber(row+2));results[a+15]=99;}continue;}
        if(protectionMarker(s,who,7,when))continue;
        enterManualCover(s,who,when,loadNumber(row+2),99,false);
    }
}
bool manualBeforeReload(inout Runtime s,Weapon w,uint who,uint64_t when)
{
    if(!manualControls(s))return false;uint m=manualState(s,who);
    if(results[m+6]!=0){results[m+6]=0;return true;}
    if(manualOpen(s,who)&&protectionMarker(s,who,7,when))exitManualCover(s,who,when);
    if((results[m]&1)!=0&&f64Less(0,actorNumber(m+2))&&!f64Less(when,actorNumber(m+2)))
    {
        exitManualCover(s,who,when);
        if(f64Less(0,s.reloadUntil[who]))
        {
            if(s.ammo[who]>0){s.reloadUntil[who]=ONE|F64_SIGN;results[m+1]=0;}
            else results[m+1]=1;
        }
    }
    return false;
}
bool manualAfterReload(inout Runtime s,uint who,uint64_t when)
{
    if(!manualControls(s))return false;uint m=manualState(s,who);
    if((results[m]&2)!=0&&!f64Less(0,s.reloadUntil[who]))exitManualCover(s,who,when);
    return manualCovering(s,who,when);
}
bool manualCancelClip(inout Runtime s,uint who,uint64_t when)
{
    if(!manualControls(s))return false;uint m=manualState(s,who);if(results[m+1]==0)return false;
    results[m+1]=0;s.reloadUntil[who]=ONE|F64_SIGN;s.nextShot[who]=larger(s.nextShot[who],when);return true;
}
