// ERG1 literal colliders and selected definition rows; no precalculated answers.
static const uint ER_INPUT=86176U;
static const uint ER_MAGIC=0x45524731U;
bool rangeDefinition(uint tail,uint row){return (commands[tail+16+row/32]&(1U<<(row%32)))!=0;}
bool validRangeWire(inout Runtime s,uint tail)
{
    uint count=commands[tail+4];
    if(commands[tail]!=ER_MAGIC||commands[tail+1]!=1||commands[tail+2]>=5||commands[tail+3]>=P_DEFINITIONS||count==0||count>8)return false;
    for(uint i=5;i<8;i++)if(commands[tail+i]!=0)return false;
    for(uint i=24;i<32;i++)if(commands[tail+i]!=0)return false;
    for(uint i=8;i<16;i+=2)if(!f64Finite(loadNumber(tail+i)))return false;
    if(f64Less(loadNumber(tail+8),0)||f64Less(loadNumber(tail+10),0))return false;
    uint selected=0;
    for(uint row=0;row<256;row++)if(rangeDefinition(tail,row))
    {
        if(row>=s.count)return false;Definition d=readDefinition(s.inputBase,row);uint plan=s.inputBase+P_RECIPIENT_BASE+row*8;
        if(d.kind!=0||d.stat!=0||d.enemyBuff!=0||d.targetName<0||d.targetName>=int(P_DEFINITIONS)||d.lazyGroup!=0||d.queryResolve!=0||d.healthScaling!=0||d.alliedFlags!=0||d.quantityFlags!=0||d.damageFlags!=0||!f64Finite(d.value)||f64Less(d.value,HUNDRED^F64_SIGN)||!f64Zero(d.interval))return false;
        // Only the static, all-allied and existing allies-with-marker plans.
        if(commands[plan]!=0&&commands[plan]!=1&&commands[plan]!=12)return false;
        selected++;
    }
    if(selected==0)return false;
    for(uint i=0;i<8;i++)
    {
        uint at=tail+32+i*16;
        if(i>=count){for(uint j=0;j<16;j++)if(commands[at+j]!=0)return false;continue;}
        uint kind=commands[at];if((kind!=1&&kind!=2)||commands[at+1]!=0||commands[at+14]!=0||commands[at+15]!=0)return false;
        for(uint j=2;j<14;j+=2)if(!f64Finite(loadNumber(at+j)))return false;
        uint64_t r=loadNumber(at+6),w=loadNumber(at+8),h=loadNumber(at+10);
        if(kind==1?!(f64Less(0,r)&&f64Zero(w)&&f64Zero(h)):!(f64Zero(r)&&f64Less(0,w)&&f64Less(0,h)))return false;
    }
    uint countCommands=commands[s.inputBase+2];if(countCommands==0)return false;
    for(uint i=0;i<countCommands;i++)
    {
        uint at=s.inputBase+P_COMMAND_BASE+i*8;
        if(i+1==countCommands){if(commands[at]!=2||commands[at+6]!=0||!f64Equal(loadNumber(at+1),loadNumber(tail+8)))return false;}
        else if(commands[at]!=0||f64Less(loadNumber(tail+8),loadNumber(at+1)))return false;
    }
    return true;
}
void executeNamedRange(inout Runtime s,uint index)
{
    uint input=1+index*ER_INPUT,output=index*P_OUTPUT_WORDS;
    initializeRuntime(s);bool ready;initializePortableProgram(s,input,output,ready);if(!ready)return;
    uint tail=input+P_INPUT_WORDS;if(!validRangeWire(s,tail)){results[output]=64;return;}
    uint queries;executePortableCommands(s,input,output,queries);writePortableProgram(s,input,output,queries);if(results[output]!=0)return;
    uint who=commands[tail+2],name=commands[tail+3];uint64_t when=loadNumber(tail+8),total=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint slot=s.orderedRows[pass];Definition d=residentDefinition(s,slot);
        if(!rangeDefinition(tail,s.carrierDefinition[slot])||d.targetName!=int(name)||s.alive[slot]==0||!f64Less(when,s.end[slot])||(s.activeRecipients[slot]&(1U<<who))==0||!basicConditions(s,slot,when,true,who))continue;
        total=f64Add(total,recipientValue(s,slot,who));
    }
    uint64_t factor=f64Add(ONE,f64Div(total,HUNDRED)),base=loadNumber(tail+10),radius=f64Mul(base,factor);
    if(!f64Finite(total)||!f64Finite(factor)||!f64Finite(radius)||f64Less(factor,0)||f64Less(radius,0)){results[output]=64;return;}
    uint at=output+P_QUERY_BASE+63*P_QUERY_WORDS;for(uint j=0;j<32;j++)results[at+j]=0;
    results[at]=ER_MAGIC;results[at+1]=who;results[at+2]=name;results[at+3]=commands[tail+4];results[at+15]=1;
    storeNumber(at+4,total);storeNumber(at+6,factor);storeNumber(at+8,base);storeNumber(at+10,radius);storeNumber(at+12,when);
    for(uint i=0;i<commands[tail+4];i++)
    {
        uint p=tail+32+i*16;uint64_t si=0,co=ONE;if(commands[p]==2)coordinateSinCosDegrees(loadNumber(p+12),si,co);
        uint64_t distance=coordinateShapeDistance(commands[p],loadNumber(p+2),loadNumber(p+4),loadNumber(p+6),loadNumber(p+8),loadNumber(p+10),co,si,loadNumber(tail+12),loadNumber(tail+14));
        if(!f64Finite(distance)){results[output]=64;return;}
        storeNumber(at+16+i*2,distance);if(coordinateShapeContains(distance,radius))results[at+14]|=1U<<i;
    }
}
