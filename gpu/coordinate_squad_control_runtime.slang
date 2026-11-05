// Squad events run before arbitration; the live old owner is excluded from space-cover.
static const uint CSQ_INPUT=109656U,CSQ_BASE=1769808U,CSQ_MAGIC=0x53515631U;
uint squadInput(inout Runtime s){return s.inputBase+CSQ_INPUT;}
uint squadHead(inout Runtime s){return s.resourceOutput+CSQ_BASE;}
bool squadCoverFlag(inout Runtime s,uint who){return results[squadHead(s)+8+who]!=0;}
void clearSquadCoverFlag(inout Runtime s,uint who){results[squadHead(s)+8+who]=0;}
bool squadModeStateEnabled(inout Runtime s)
{
#ifdef PORTABLE_COORDINATE_SQUAD_MODE_STATE
    return commands[squadInput(s)+1]==2;
#else
    return false;
#endif
}
bool squadCharacterMode(inout Runtime s,uint who)
{return s.modeIndex[who]>=0||(squadModeStateEnabled(s)&&results[squadHead(s)+16+who]!=0);}
void squadModeTickStart(inout Runtime s,uint who)
{if(squadModeStateEnabled(s))results[squadHead(s)+16+who]=uint(s.modeIndex[who]>=0);}
void squadModeReloadEntry(inout Runtime s,uint who)
{if(squadModeStateEnabled(s)&&s.modeIndex[who]>=0)results[squadHead(s)+16+who]=1;}
void captureSquadModeState(inout Runtime s,uint64_t when)
{
    if(!squadModeStateEnabled(s))return;uint h=squadHead(s),mask=0;
    for(uint who=0;who<5;who++)mask|=results[h+16+who]<<who;
    uint words[3];words[0]=uint(when);words[1]=uint(when>>32);words[2]=mask;
    uint64_t a=actorNumber(h+24),b=actorNumber(h+26);
    for(uint i=0;i<3;i++){uint64_t w=words[i];a=(a^w)*uint64_t(0x100000001b3);b=((b<<7)|(b>>57))^w*uint64_t(0x9e3779b185ebca87);}
    storeNumber(h+24,a);storeNumber(h+26,b);results[h+28]++;
}
bool initializeSquadControls(inout Runtime s)
{
    uint p=squadInput(s),count=commands[p+2];
    if(commands[p]!=CSQ_MAGIC||(!squadModeStateEnabled(s)&&commands[p+1]!=1)||count>16||commands[p+3]!=16||commands[p+4]!=8||commands[p+5]!=(squadModeStateEnabled(s)?0x4d535431U:0U)||commands[p+6]!=0||commands[p+7]!=0)return false;
    if((count!=0||squadModeStateEnabled(s))&&(!manualControls(s)||commands[ciInput(s)+3]!=0))return false;
    for(uint i=0;i<16;i++)
    {
        uint a=p+8+i*8;if(i>=count){for(uint j=0;j<8;j++)if(commands[a+j]!=0)return false;continue;}
        uint kind=commands[a+2],target=commands[a+3];uint64_t at=loadNumber(a),duration=loadNumber(a+4);
        if(kind<1||kind>2||target>5||kind==2&&target!=0||!f64Finite(at)||f64Less(at,0)||f64Less(f64FromI64(180),at)||i>0&&f64Less(at,loadNumber(a-8))||!f64Finite(duration)||!f64Equal(duration,ONE|F64_SIGN)&&(f64Less(duration,0)||f64Less(f64FromI64(180),duration))||kind==1&&duration!=0||commands[a+6]!=0||commands[a+7]!=0)return false;
    }
    // This bank is the explicit 48-word padding of the policy output; old captures stay zero.
    if(count!=0||squadModeStateEnabled(s)){uint h=squadHead(s);for(uint i=0;i<48;i++)results[h+i]=0;results[h]=CSQ_MAGIC;results[h+1]=commands[p+1];results[h+3]=count;if(squadModeStateEnabled(s)){results[h+5]=0x4d535431U;storeNumber(h+24,uint64_t(0xcbf29ce484222325));storeNumber(h+26,uint64_t(0x84222325cbf29ce4));results[h+29]=0x4d535431U;}}
    return true;
}
void pumpSquadControls(inout Runtime s,uint64_t when)
{
    captureSquadModeState(s,when);uint p=squadInput(s),count=commands[p+2];if(count==0)return;uint h=squadHead(s),i=results[h+2];
    while(i<count&&!f64Less(when,loadNumber(p+8+i*8))&&s.error==0)
    {
        uint a=p+8+i*8;i++;results[h+2]=i;
        if(commands[a+2]==1){results[ciHead(s)+14]=commands[a+3];continue;}
        uint keep=results[ciHead(s)+14];if(keep==0)keep=results[controlHead(s)+2];results[h+4]=keep;
        for(uint who=0;who<5;who++)
        {
            if(keep==who+1||squadCharacterMode(s,who)||protectionMarker(s,who,7,when))continue;
            // A squad action precedes character tick: no explicit-entry frame is consumed.
            enterManualCover(s,who,when,loadNumber(a+4),0,false);results[manualState(s,who)+6]=0;results[h+8+who]=1;invalidateNativeNumeric(s);
        }
    }
}
