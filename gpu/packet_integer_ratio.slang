// Exact unsigned128 / bounded positive integer, one binary64 nearest-even round.
// Requires the existing PacketIntegerSum and binary64 helpers; changes neither.
#ifndef PORTABLE_PACKET_INTEGER_RATIO
#define PORTABLE_PACKET_INTEGER_RATIO
uint64_t packetIntegerRatio(PacketIntegerSum value,uint divisor,out uint status)
{
    status=0;if(divisor==0||divisor>1024){status=2;return 0;}
    uint words[4]={uint(value.low),uint(value.low>>32),uint(value.high),uint(value.high>>32)};
    uint quotient[4];uint64_t remainder=0;
    for(int i=3;i>=0;i--)
    {
        uint64_t word=(remainder<<32)|uint64_t(words[i]);
        quotient[i]=uint(word/uint64_t(divisor));remainder=word%uint64_t(divisor);
    }
    PacketIntegerSum q;q.low=uint64_t(quotient[0])|(uint64_t(quotient[1])<<32);q.high=uint64_t(quotient[2])|(uint64_t(quotient[3])<<32);
    uint64_t extended=0;int exponent;
    if(q.low==0&&q.high==0)
    {
        if(remainder==0)return 0;
        exponent=-1;remainder*=2;
        while(remainder<divisor){remainder*=2;exponent--;}
        remainder-=divisor;extended=1;
        for(uint i=0;i<55;i++)
        {
            remainder*=2;extended<<=1;
            if(remainder>=divisor){extended|=1;remainder-=divisor;}
        }
    }
    else
    {
        uint highest=q.high!=0?64U:0U;uint64_t scan=q.high!=0?q.high:q.low;
        while(scan>1){scan>>=1;highest++;}exponent=int(highest);
        if(highest<=55)
        {
            extended=q.low;
            for(uint i=0;i<55-highest;i++)
            {
                remainder*=2;extended<<=1;
                if(remainder>=divisor){extended|=1;remainder-=divisor;}
            }
        }
        else
        {
            uint distance=highest-55;
            extended=distance<64?(q.high<<(64-distance))|shiftJam(q.low,distance):shiftJam(q.high,distance-64)|uint64_t(q.low!=0);
        }
    }
    extended|=uint64_t(remainder!=0);
    return f64Pack(0,exponent+1023,extended);
}
#endif
