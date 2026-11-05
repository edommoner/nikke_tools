// Per-depth frozen factors occupy the gap between sampled pellet rows and META.
// Native captures buffs once, then interleaves each critical draw with children.
static const uint CSS_BASE=914352U;
static const uint CSS_DEPTHS=32U;
static const uint CSS_WORDS=48U;
uint sampledSkillFrame(inout Runtime s,uint depth){return s.resourceOutput+CSS_BASE+depth*CSS_WORDS;}
void beginSampledSkillFrame(inout Runtime s,uint depth,uint row)
{
    if(depth>=CSS_DEPTHS){s.error=2;return;}
    uint at=sampledSkillFrame(s,depth);for(uint i=0;i<CSS_WORDS;i++)results[at+i]=0;
    results[at]=0x43535331U;results[at+1]=row;results[csMeta(s)+60]=depth+1;
}
uint sampledSkillActive(inout Runtime s,uint row)
{
    uint depth=results[csMeta(s)+60];if(depth==0||depth>CSS_DEPTHS){s.error=16;return 0;}
    uint at=sampledSkillFrame(s,depth-1);
    if(results[at]!=0x43535331U||results[at+1]!=row){s.error=16;return 0;}return at;
}
uint64_t sampledSkillCriticalFraction(inout Runtime s,uint row,uint64_t rate)
{
    uint at=sampledSkillActive(s,row);if(s.error!=0)return 0;
    bool critical=f64Less(coordinateRandom53(csRng(s)),rate);results[at+9]++;results[at+10]=uint(critical);
    return critical?ONE:uint64_t(0);
}
void captureSampledSkillFactors(inout Runtime s,uint row,uint64_t factors[9],uint64_t rate,uint64_t bonus,uint64_t core,uint flags,uint64_t intercept)
{
    uint at=sampledSkillActive(s,row);if(s.error!=0)return;
    storeNumber(at+2,rate);storeNumber(at+4,bonus);storeNumber(at+6,core);results[at+8]=flags;
    for(uint i=0;i<9;i++)storeNumber(at+12+i*2,factors[i]);storeNumber(at+30,intercept);
}
void resampleSkillFrame(inout Runtime s,uint depth,uint row,inout uint64_t body,inout uint64_t part,inout uint64_t interrupt,inout uint64_t critical)
{
    if(depth>=CSS_DEPTHS){s.error=16;return;}
    uint at=sampledSkillFrame(s,depth);
    if(results[at]!=0x43535331U||results[at+1]!=row){s.error=16;return;}
    bool hit=f64Less(coordinateRandom53(csRng(s)),actorNumber(at+2));results[at+9]++;results[at+10]=uint(hit);critical=hit?ONE:uint64_t(0);
    uint64_t factors[9];for(uint i=0;i<9;i++)factors[i]=actorNumber(at+12+i*2);
    uint64_t f3=f64Add(ONE,f64Mul(critical,actorNumber(at+4)));uint flags=results[at+8];
    if((flags&1)!=0)f3=f64Add(f3,uint64_t(0x3fe00000U)<<32);
    if((flags&2)!=0)f3=f64Add(f3,(uint64_t(0x3fd33333U)<<32)|uint64_t(0x33333333U));
    factors[7]=f3;uint64_t core=actorNumber(at+6);if(!f64Zero(core))f3=f64Add(f3,core);factors[2]=f3;
    body=damageFromFactors(s,factors,false);
    if(!f64Zero(part)&&s.error==0)part=damageFromFactors(s,factors,true);
    if(!f64Zero(interrupt)&&s.error==0){factors[8]=actorNumber(at+30);interrupt=damageFromFactors(s,factors,true);}
}
