// Codec only changes representation. binary64 payloads and event order are exact.
struct LandingReceipt
{
    uint row,target,mask,order,hit,hits,depth,epoch;
    uint64_t amount,when,partAmount;
};
#ifdef PORTABLE_WORLD_PROJECTILE
#include "skill_part_receipt.slang"
#endif
bool validLandingReceipt(LandingReceipt r)
{
    return r.row<P_DEFINITIONS && r.target<8 && (r.mask==0xffffffff || r.mask<256) &&
        r.hit>=1 && r.hit<=256 && r.hits>=r.hit && r.hits<=256 && r.depth>=1 && r.depth<=P_DEPTH && r.epoch<=0x7fffffff;
}
void storeLandingReceipt(uint at,LandingReceipt r)
{
#ifdef PORTABLE_WIDE_LANDINGS
    results[at]=r.row;results[at+1]=r.target;results[at+2]=r.mask;results[at+3]=r.order;
    storeNumber(at+4,r.amount);storeNumber(at+6,r.when);
    results[at+8]=r.hit;results[at+9]=r.hits;results[at+10]=r.depth;results[at+11]=r.epoch;
#else
    uint mask=r.mask==0xffffffff ? 256 : r.mask;
    results[at]=r.row|(r.target<<8)|(mask<<11);results[at+1]=r.order;
    storeNumber(at+2,r.amount);storeNumber(at+4,r.when);
    results[at+6]=r.hit|(r.hits<<9)|(r.depth<<18);results[at+7]=r.epoch;
#endif
}
[ForceInline]
LandingReceipt loadLandingReceipt(uint at)
{
    LandingReceipt r={};
#ifdef PORTABLE_WIDE_LANDINGS
    r.row=results[at];r.target=results[at+1];r.mask=results[at+2];r.order=results[at+3];
    r.amount=sourceNumber(at+4);r.when=sourceNumber(at+6);
    r.hit=results[at+8];r.hits=results[at+9];r.depth=results[at+10];r.epoch=results[at+11];
#else
    uint packed=results[at],mask=(packed>>11)&511,counts=results[at+6];
    r.row=packed&255;r.target=(packed>>8)&7;r.mask=mask==256 ? 0xffffffff : mask;r.order=results[at+1];
    r.amount=sourceNumber(at+2);r.when=sourceNumber(at+4);
    r.hit=counts&511;r.hits=(counts>>9)&511;r.depth=(counts>>18)&63;r.epoch=results[at+7];
#endif
    return r;
}
// Immutable packet receipts in GPU-owned output memory, never CPU replay.
uint landingHeader(inout Runtime s) { return s.resourceOutput+P_LANDING_HEADER_BASE; }
uint landingAddress(inout Runtime s,uint index) { return s.resourceOutput+P_LANDING_STATE_BASE+index*P_LANDING_WORDS; }
bool initializeLandings(inout Runtime s)
{
    uint meta=s.inputBase+P_LANDING_META_BASE;s.landingPolicy=commands[meta];
    if(s.landingPolicy>1 || s.landingPolicy!=0 && s.combat==0 || s.landingPolicy==0 && (s.healthMask&64)!=0) return false;
    for(uint i=1;i<8;i++) if(commands[meta+i]!=0) return false;
    for(uint i=0;i<8;i++) results[landingHeader(s)+i]=0;
    return true;
}
[noinline]
void enqueueLanding(inout Runtime s,uint row,uint target,uint mask,uint order,uint64_t amount,uint64_t when,uint hit,uint hits,uint depth,uint epoch,uint64_t partAmount=0)
{
    LandingReceipt receipt;receipt.row=row;receipt.target=target;receipt.mask=mask;receipt.order=order;
    receipt.amount=amount;receipt.when=when;receipt.hit=hit;receipt.hits=hits;receipt.depth=depth;receipt.epoch=epoch;receipt.partAmount=partAmount;
    if(!WORLD_SKILL_RECEIPT_VALID(s,receipt,validLandingReceipt(receipt))) { s.error=64;return; }
    uint header=landingHeader(s),count=results[header];
    if(count>=P_LANDINGS) { s.error=64;return; }
    if(results[header+2]==0x7fffffff) { s.error=2;return; }
    WORLD_SKILL_RECEIPT_STORE(s,landingAddress(s,count),receipt);
    results[header]=count+1;results[header+2]++;results[header+5]=max(results[header+5],count+1-results[header+1]);
}
// Called outside dispatch: child skills append receipts rather than recurse
// into this drain. The live tail mirrors the native list-iteration contract.
[noinline]
void drainLandings(inout Runtime s,uint64_t when,uint output)
{
    WORLD_SKILL_DRAIN(s,when,output,if(s.landingPolicy==0) return;)
    uint header=landingHeader(s);
    if(results[header]==results[header+1]) return;
    if(results[header+4]==0x7fffffff) { s.error=2;return; }
    results[header+4]++;
    uint parentTarget=s.target,work=0;
    while(results[header+1]<results[header] && s.error==0)
    {
        if(++work>4096) { s.error=4;break; }
        LandingReceipt receipt=loadLandingReceipt(landingAddress(s,results[header+1]++));
        uint row=receipt.row,inherited=receipt.target,mask=receipt.mask,order=receipt.order,epoch=receipt.epoch;
        Definition d=readDefinition(s.inputBase,row);d.damageHits=receipt.hits;
        if(mask==0xffffffff)
        {
            mask=enemyDamageMask(s,d,inherited,order);
            if(d.damageRoute==0 && (inherited>=s.targetCount || s.enemyBirth[inherited]>epoch)) { mask=0;order=0; }
        }
        else
        {
            uint filtered=0,nextOrder=0,count=0;
            for(uint i=0;i<8;i++)
            {
                uint encoded=(order>>(i*4))&15;if(encoded==0) break;uint target=encoded-1;
                if(s.targetAlive[target]==0 || s.enemyBirth[target]>epoch) continue;
                filtered|=1U<<target;nextOrder|=encoded<<(4*count++);
            }
            mask=filtered;order=nextOrder;
        }
        uint64_t amount=receipt.amount,weighted=amount,share=amount;
        if((d.damageFlags&H_SPLIT)!=0 && d.damageRoute>=2 && (d.periodicFlags&1)==0 && mask!=0)
            weighted=f64Mul(amount,f64Div(ONE,f64FromI64(enemyMaskCount(mask))));
        share=weighted;
        if((d.damageFlags&H_SPLIT)!=0 && enemyMaskCount(mask)>1)
        {
            uint status;uint64_t rounded=f64ToI64(weighted,0,status);
            if(status!=0) { s.error=16;break; }share=f64FromI64(rounded);
        }
        uint basis=d.damageRoute>=2 || d.damageRoute==1 ? 0 : inherited;
        logDamagePacket(s,d,row,mask,basis,receipt.hit,share,weighted,order,receipt.when,receipt.depth,output);
        for(uint i=0;i<8 && s.error==0;i++)
        {
            uint encoded=(order>>(i*4))&15;if(encoded==0) break;uint target=encoded-1;
            if(s.targetAlive[target]==0) continue;
            WORLD_SKILL_BEGIN(s,d.owner,target,share) s.target=target;land(s,d.owner,target,share);
            if((s.healthMask&64)!=0 && s.error==0) dispatch(s,17,0,d.owner,0,when,output,share); WORLD_GATE_END
        }
        if(results[header+3]==0x7fffffff) { s.error=2;break; }results[header+3]++;
    }
    if(s.error==0) { results[header]=0;results[header+1]=0; }
    s.target=parentTarget;
}
