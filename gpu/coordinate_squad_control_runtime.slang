// Squad events run before arbitration; the live old owner is excluded from space-cover.
static const uint CSQ_INPUT=109656U,CSQ_BASE=1769808U,CSQ_MAGIC=0x53515631U;
uint squadInput(inout Runtime s){return s.inputBase+CSQ_INPUT;}
uint squadHead(inout Runtime s){return s.resourceOutput+CSQ_BASE;}
bool squadCoverFlag(inout Runtime s,uint who){return results[squadHead(s)+8+who]!=0;}
void clearSquadCoverFlag(inout Runtime s,uint who){results[squadHead(s)+8+who]=0;}
bool initializeSquadControls(inout Runtime s)
{
    uint p=squadInput(s),count=commands[p+2];
    if(commands[p]!=CSQ_MAGIC||commands[p+1]!=1||count>16||commands[p+3]!=16||commands[p+4]!=8||commands[p+5]!=0||commands[p+6]!=0||commands[p+7]!=0)return false;
    if(count!=0&&(!manualControls(s)||commands[ciInput(s)+3]!=0))return false;
    for(uint i=0;i<16;i++)
    {
        uint a=p+8+i*8;if(i>=count){for(uint j=0;j<8;j++)if(commands[a+j]!=0)return false;continue;}
        uint kind=commands[a+2],target=commands[a+3];uint64_t at=loadNumber(a),duration=loadNumber(a+4);
        if(kind<1||kind>2||target>5||kind==2&&target!=0||!f64Finite(at)||f64Less(at,0)||f64Less(f64FromI64(180),at)||i>0&&f64Less(at,loadNumber(a-8))||!f64Finite(duration)||!f64Equal(duration,ONE|F64_SIGN)&&(f64Less(duration,0)||f64Less(f64FromI64(180),duration))||kind==1&&duration!=0||commands[a+6]!=0||commands[a+7]!=0)return false;
    }
    // This bank is the explicit 48-word padding of the policy output; old captures stay zero.
    if(count!=0){uint h=squadHead(s);for(uint i=0;i<48;i++)results[h+i]=0;results[h]=CSQ_MAGIC;results[h+1]=1;results[h+3]=count;}
    return true;
}
void pumpSquadControls(inout Runtime s,uint64_t when)
{
    uint p=squadInput(s),count=commands[p+2];if(count==0)return;uint h=squadHead(s),i=results[h+2];
    while(i<count&&!f64Less(when,loadNumber(p+8+i*8))&&s.error==0)
    {
        uint a=p+8+i*8;i++;results[h+2]=i;
        if(commands[a+2]==1){results[ciHead(s)+14]=commands[a+3];continue;}
        uint keep=results[ciHead(s)+14];if(keep==0)keep=results[controlHead(s)+2];results[h+4]=keep;
        for(uint who=0;who<5;who++)
        {
            if(keep==who+1||s.modeIndex[who]>=0||protectionMarker(s,who,7,when))continue;
            // A squad action precedes character tick: no explicit-entry frame is consumed.
            enterManualCover(s,who,when,loadNumber(a+4),0,false);results[manualState(s,who)+6]=0;results[h+8+who]=1;invalidateNativeNumeric(s);
        }
    }
}
