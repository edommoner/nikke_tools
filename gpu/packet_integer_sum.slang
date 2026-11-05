// Exact nonnegative packet integers, then one nearest/even binary64 rounding.
// Both backends use this code. The caller bounds terms and multiplier before
// accumulating; 128 signed-63-bit terms times1024 need at most80 bits.
struct PacketIntegerSum { uint64_t low,high; };
PacketIntegerSum packetIntegerZero(){PacketIntegerSum r;r.low=0;r.high=0;return r;}
void packetIntegerAdd(inout PacketIntegerSum sum,PacketIntegerSum value)
{
    uint64_t before=sum.low;sum.low+=value.low;sum.high+=value.high+uint64_t(sum.low<before);
}
bool packetIntegerAddAmount(inout PacketIntegerSum sum,uint64_t amount)
{
    uint status;uint64_t value=f64ToI64(amount,1,status);
    if(status!=0||f64Less(amount,0)||!f64Equal(amount,f64Integral(amount,0)))return false;
    PacketIntegerSum term=packetIntegerZero();term.low=value;packetIntegerAdd(sum,term);return true;
}
PacketIntegerSum packetIntegerMultiply(PacketIntegerSum value,uint multiplier)
{
    PacketIntegerSum sum=packetIntegerZero();
    while(multiplier!=0)
    {
        if((multiplier&1)!=0)packetIntegerAdd(sum,value);
        multiplier>>=1;
        if(multiplier!=0){value.high=(value.high<<1)|(value.low>>63);value.low<<=1;}
    }
    return sum;
}
uint64_t packetIntegerBinary64(PacketIntegerSum value)
{
    if(value.low==0&&value.high==0)return 0;
    uint highest=value.high!=0?64U:0U;uint64_t scan=value.high!=0?value.high:value.low;
    while(scan>1){scan>>=1;highest++;}
    uint64_t extended;
    if(highest<=55)extended=value.low<<(55-highest);
    else
    {
        uint distance=highest-55;
        if(distance<64)extended=(value.high<<(64-distance))|shiftJam(value.low,distance);
        else extended=shiftJam(value.high,distance-64)|uint64_t(value.low!=0);
    }
    return f64Pack(0,int(highest)+1023,extended);
}
