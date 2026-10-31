// Receipts and per-depth immutable attack snapshots; never a second HP or clock.
#include "incoming_damage_numeric.slang"
uint coverDefenseHead(inout Runtime s) { return s.resourceOutput+CDF_OUTPUT_BASE; }
uint coverDefenseSnapshot(inout Runtime s,uint depth) { return coverDefenseHead(s)+CDF_SNAPSHOT_BASE+depth*CDF_SNAPSHOT_WORDS; }
bool initializeCoverDefense(inout Runtime s)
{
    uint input=s.inputBase+CDF_BASE;
    if(commands[input]!=CDF_MAGIC||commands[input+1]!=1||commands[input+2]!=5)return false;
#ifdef PORTABLE_PRODUCT_UNSPECIFIED_COVER
    if(commands[input+3]>1)return false;
#else
    if(commands[input+3]!=0)return false;
#endif
    for(uint i=4;i<8;i++)if(commands[input+i]!=0)return false;
    for(uint i=18;i<CDF_WORDS;i++)if(commands[input+i]!=0)return false;
    for(uint who=0;who<5;who++)
    {
        uint64_t base=loadNumber(input+8+who*2);
#ifdef PORTABLE_PRODUCT_UNSPECIFIED_COVER
        if(commands[input+3]==1&&base!=0)return false;
#endif
        if(!f64Finite(base)||f64Less(base,0)||f64Less((uint64_t(0x46293e59)<<32)|uint64_t(0x39a08cea),base))return false;
    }
    for(uint i=CDF_OUTPUT_BASE;i<CDF_OUTPUT_WORDS;i++)results[s.resourceOutput+i]=0;
    results[coverDefenseHead(s)]=CDF_MAGIC;return true;
}
void captureCoverDefense(inout Runtime s,uint depth,uint64_t attack,uint64_t coefficient,uint64_t received,uint divisor)
{
    if(depth>=CDF_DEPTH||divisor==0||divisor>5){s.error=64;return;}
    uint at=coverDefenseSnapshot(s,depth);
    for(uint i=0;i<CDF_SNAPSHOT_WORDS;i++)results[at+i]=0;
    storeNumber(at,attack);storeNumber(at+2,coefficient);storeNumber(at+4,received);results[at+6]=divisor;results[at+7]=CDF_MAGIC;
}
void copyCoverDefense(inout Runtime s,uint parent,uint child)
{
    if(parent>=CDF_DEPTH||child>=CDF_DEPTH){s.error=64;return;}
    uint from=coverDefenseSnapshot(s,parent),to=coverDefenseSnapshot(s,child);
    for(uint i=0;i<CDF_SNAPSHOT_WORDS;i++)results[to+i]=results[from+i];
}
uint64_t coverDefenseQuantity(inout Runtime s,uint depth,uint who,uint64_t when)
{
#ifdef PORTABLE_PRODUCT_UNSPECIFIED_COVER
    if(commands[s.inputBase+CDF_BASE+3]!=0){s.error=64;return 0;}
#endif
    uint snapshot=coverDefenseSnapshot(s,depth),head=coverDefenseHead(s),count=results[head+1];
    if(depth>=CDF_DEPTH||who>=5||results[snapshot+7]!=CDF_MAGIC||results[snapshot+6]==0||results[snapshot+6]>5){s.error=64;return 0;}
    if(count>=CDF_RECEIPTS){s.error=2;return 0;}
    uint divisor=results[snapshot+6];uint64_t attack=protectionNumber(snapshot),coefficient=protectionNumber(snapshot+2),received=protectionNumber(snapshot+4);
    uint64_t base=loadNumber(s.inputBase+CDF_BASE+8+who*2),percent=liveQuantity(s,who,CDF_STAT,when);
    uint64_t defense=incomingDefensePercentage(base,percent),quantity=incomingDefendedQuantity(attack,coefficient,defense,received),shared=f64Div(quantity,f64FromI64(divisor));
    if(!f64Finite(defense)||!f64Finite(quantity)||!f64Finite(shared)){s.error=16;return 0;}
    uint64_t hp=s.coverHP[who],applied=smaller(hp,shared);uint out=head+CDF_RECEIPT_BASE+count*CDF_RECEIPT_WORDS;
    results[head+1]=count+1;results[out]=who;results[out+1]=divisor;storeNumber(out+2,when);storeNumber(out+4,attack);storeNumber(out+6,coefficient);storeNumber(out+8,received);
    storeNumber(out+10,base);storeNumber(out+12,defense);storeNumber(out+14,quantity);storeNumber(out+16,shared);storeNumber(out+18,hp);storeNumber(out+20,applied);storeNumber(out+22,f64Add(hp,applied^F64_SIGN));
    return applied;
}
