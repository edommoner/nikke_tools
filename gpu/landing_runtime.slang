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
void enqueueLanding(inout Runtime s,uint row,uint target,uint mask,uint order,uint64_t amount,uint64_t when,uint hit,uint hits,uint depth,uint epoch)
{
    uint header=landingHeader(s),count=results[header];
    if(count>=P_LANDINGS) { s.error=64;return; }
    if(results[header+2]==0x7fffffff) { s.error=2;return; }
    uint at=landingAddress(s,count);results[at]=row;results[at+1]=target;results[at+2]=mask;results[at+3]=order;
    storeNumber(at+4,amount);storeNumber(at+6,when);results[at+8]=hit;results[at+9]=hits;results[at+10]=depth;results[at+11]=epoch;
    results[header]=count+1;results[header+2]++;results[header+5]=max(results[header+5],count+1-results[header+1]);
}
// Called outside dispatch: child skills append receipts rather than recurse
// into this drain. The live tail mirrors the native list-iteration contract.
[noinline]
void drainLandings(inout Runtime s,uint64_t when,uint output)
{
    if(s.landingPolicy==0) return;
    uint header=landingHeader(s);
    if(results[header]==results[header+1]) return;
    if(results[header+4]==0x7fffffff) { s.error=2;return; }
    results[header+4]++;
    uint parentTarget=s.target,work=0;
    while(results[header+1]<results[header] && s.error==0)
    {
        if(++work>4096) { s.error=4;break; }
        uint at=landingAddress(s,results[header+1]++),row=results[at],inherited=results[at+1],mask=results[at+2],order=results[at+3],epoch=results[at+11];
        Definition d=s.defs[row];d.damageHits=results[at+9];
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
        uint64_t amount=sourceNumber(at+4),weighted=amount,share=amount;
        if((d.damageFlags&H_SPLIT)!=0 && d.damageRoute>=2 && (d.periodicFlags&1)==0 && mask!=0)
            weighted=f64Mul(amount,f64Div(ONE,f64FromI64(enemyMaskCount(mask))));
        share=weighted;
        if((d.damageFlags&H_SPLIT)!=0 && enemyMaskCount(mask)>1)
        {
            uint status;uint64_t rounded=f64ToI64(weighted,0,status);
            if(status!=0) { s.error=16;break; }share=f64FromI64(rounded);
        }
        uint basis=d.damageRoute>=2 || d.damageRoute==1 ? 0 : inherited;
        logDamagePacket(s,d,row,mask,basis,results[at+8],share,weighted,order,sourceNumber(at+6),results[at+10],output);
        for(uint i=0;i<8 && s.error==0;i++)
        {
            uint encoded=(order>>(i*4))&15;if(encoded==0) break;uint target=encoded-1;
            if(s.targetAlive[target]==0) continue;
            s.target=target;land(s,d.owner,target,share);
            if((s.healthMask&64)!=0 && s.error==0) dispatch(s,17,0,d.owner,0,when,output,share);
        }
        if(results[header+3]==0x7fffffff) { s.error=2;break; }results[header+3]++;
    }
    if(s.error==0) { results[header]=0;results[header+1]=0; }
    s.target=parentTarget;
}
