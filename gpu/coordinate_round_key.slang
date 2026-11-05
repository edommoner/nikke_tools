// Exact decimal-six rounding of finite binary64, then nearest/even binary64.
// The exact product is significand *5^6, shifted by its remaining power of2.
// Caller includes the shared binary64 and PacketIntegerSum implementations.
uint64_t coordinateRoundSix(uint64_t value,out uint status)
{
    status=0;if(!f64Finite(value)){status=1;return 0;}
    uint64_t sign=value&F64_SIGN;int exponent=int((value>>52)&2047)-1023;
    // At exponent33 the binary64 ULP exceeds1e-6: decimal-six rounding
    // perturbs by less than half an ULP, so conversion returns the input.
    if(exponent>=33)return value;
    if(exponent< -21)return sign;
    PacketIntegerSum product=packetIntegerZero();product.low=(value&F64_FRAC)|(uint64_t(1)<<52);
    product=packetIntegerMultiply(product,15625U);
    uint distance=uint(46-exponent);uint64_t integer;bool more,tie;
    if(distance<64)
    {
        integer=(product.high<<(64-distance))|(product.low>>distance);
        uint64_t tail=product.low&((uint64_t(1)<<distance)-1),half=uint64_t(1)<<(distance-1);
        more=tail>half;tie=tail==half;
    }
    else if(distance==64)
    {
        integer=product.high;more=product.low>(uint64_t(1)<<63);tie=product.low==(uint64_t(1)<<63);
    }
    else
    {
        uint shift=distance-64;integer=product.high>>shift;
        uint64_t tail=product.high&((uint64_t(1)<<shift)-1),half=uint64_t(1)<<(shift-1);
        more=tail>half||(tail==half&&product.low!=0);tie=tail==half&&product.low==0;
    }
    if(more||(tie&&(integer&1)!=0))integer++;
    uint64_t million=(uint64_t(0x412e8480U)<<32);
    return sign|f64Div(f64FromI64(integer),million);
}
uint64_t coordinateCacheKey(uint64_t value,out uint status)
{uint64_t rounded=coordinateRoundSix(value,status);return f64Zero(rounded)?uint64_t(0):rounded;}
