// Integer-only MT19937 with CPython's positive integer seed and pool sampler.
// State resides in this program's GPU output scratch, not Runtime/private arrays.
// Reference: CPython Modules/_randommodule.c and Lib/random.py (3.12).
static const uint MT_WORDS=624;
void mtSeed(uint base,uint64_t seed)
{
    for(uint h=0;h<8;h++) results[base+h]=0;
    uint state=base+8;results[state]=19650218U;
    for(uint i=1;i<MT_WORDS;i++)
    { uint prior=results[state+i-1];results[state+i]=1812433253U*(prior^(prior>>30))+i; }
    uint keyWords=(seed>>32)!=0 ? 2 : 1,position=1,key=0;
    for(uint step=0;step<MT_WORDS;step++)
    {
        uint prior=results[state+position-1],part=key==0 ? uint(seed) : uint(seed>>32);
        results[state+position]=(results[state+position]^((prior^(prior>>30))*1664525U))+part+key;
        position++;key++;
        if(position==MT_WORDS) { results[state]=results[state+MT_WORDS-1];position=1; }
        if(key==keyWords) key=0;
    }
    for(uint step=1;step<MT_WORDS;step++)
    {
        uint prior=results[state+position-1];
        results[state+position]=(results[state+position]^((prior^(prior>>30))*1566083941U))-position;
        position++;
        if(position==MT_WORDS) { results[state]=results[state+MT_WORDS-1];position=1; }
    }
    results[state]=0x80000000U;results[base]=MT_WORDS;
}
uint mtNext(uint base)
{
    uint state=base+8,index=results[base];
    if(index==MT_WORDS)
    {
        for(uint i=0;i<MT_WORDS;i++)
        {
            uint pair=(results[state+i]&0x80000000U)|(results[state+(i+1)%MT_WORDS]&0x7fffffffU);
            results[state+i]=results[state+(i+397)%MT_WORDS]^(pair>>1)^((pair&1)!=0 ? 0x9908b0dfU : 0);
        }
        index=0;
    }
    uint value=results[state+index];results[base]=index+1;results[base+1]++;
    value^=value>>11;value^=(value<<7)&0x9d2c5680U;value^=(value<<15)&0xefc60000U;return value^(value>>18);
}
uint mtBits(uint base,uint width)
{ return width==0 ? 0 : mtNext(base)>>(32-width); }
uint mtBelow(uint base,uint bound)
{
    uint width=0;for(uint v=bound;v!=0;v>>=1) width++;
    uint selected=mtBits(base,width);
    while(selected>=bound) { results[base+3]++;selected=mtBits(base,width); }
    return selected;
}
uint mtSampleFive(uint base,uint population,uint requested,out uint mask)
{
    uint pool[5];for(uint i=0;i<population;i++) pool[i]=i;
    uint order=0;mask=0;results[base+2]++;
    for(uint i=0;i<requested;i++)
    {
        uint j=mtBelow(base,population-i),who=pool[j];pool[j]=pool[population-i-1];
        order|=(who+1)<<(i*3);mask|=1U<<who;
    }
    return order;
}

// CPython3.12 sample uses a shrinking pool or selected-index set depending
// on n/k. Both branches consume the same MT/_randbelow stream as Python.
// Input is a GPU-built unique Actor slot list in0..127. Reuse that list as
// the shrinking pool, and return chosen slot IDs; caller restores birth order.
void mtSampleSlots128(uint base,inout uint order[128],inout uint population,uint requested)
{
    uint size=population,k=min(requested,size),setSize=21;
    if(k>5)
    {
        uint power=1;while(power<3*k) power*=4;
        setSize+=power;
    }
    uint selected[4];for(uint i=0;i<4;i++) selected[i]=0;
    results[base+2]++;
    if(size<=setSize)
    {
        for(uint i=0;i<k;i++)
        {
            uint j=mtBelow(base,size-i),who=order[j];
            order[j]=order[size-i-1];selected[who/32]|=1U<<(who%32);
        }
    }
    else for(uint i=0;i<k;i++)
    {
        uint who=order[mtBelow(base,size)];
        while((selected[who/32]&(1U<<(who%32)))!=0) who=order[mtBelow(base,size)];
        selected[who/32]|=1U<<(who%32);
    }
    uint count=0;
    for(uint slot=0;slot<128;slot++) if((selected[slot/32]&(1U<<(slot%32)))!=0) order[count++]=slot;
    population=count;
}
