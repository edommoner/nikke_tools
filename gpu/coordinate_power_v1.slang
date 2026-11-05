// Generated variable-exponent specialization; pinned algorithm SHA256 afa22590fd81f11ff88a300929efbc34e3818cbb3f1ebbc5d523a454728b5366
#ifndef COORDINATE_UNIT_POWER_V1
#define COORDINATE_UNIT_POWER_V1
[noinline]
uint64_t coordinateUnitPower(uint64_t x, uint64_t exponentBits, out uint status)
{
    status = 0;
    if (!f64Finite(exponentBits) || exponentBits < (uint64_t(0x3bf00000U)<<32) || exponentBits > (uint64_t(0x40f00000U)<<32) || f64Less(uint64_t(1023)<<52,x)) { status=2;return 0; }
    if (!f64Finite(x) || ((x & F64_SIGN) != 0 && !f64Zero(x))) { status = 2; return 0; }
    if (f64Zero(x)) return 0;
    if (!f64Less(x, uint64_t(1023) << 52)) return uint64_t(1023) << 52;
    int exponent; uint64_t significand; f64Unpack(x, exponent, significand);
    Bounds t = ratioBounds(significand - (uint64_t(1) << 52), significand + (uint64_t(1) << 52));
    Bounds square = boundProduct(t, t), power = t, logM = t;
    for (uint i = 1; i < 64; i++)
    {
        power = boundProduct(power, square); Bounds term = boundDivide(power, 2*i+1);
        logM.lo = wideAdd(logM.lo, term.lo); logM.hi = wideAdd(logM.hi, term.hi);
    }
    // For t<=1/3 the omitted atanh tail is <2^-200, below one Q128 unit.
    logM.lo = wideTimes(logM.lo, 2); logM.hi = wideAdd(wideTimes(logM.hi, 2), wideSmall(1));
    Bounds ln2;
    ln2.lo = wideSmall(0); ln2.lo.limb[0] = 0x03f2f6af; ln2.lo.limb[1] = 0xc9e3b398;
    ln2.lo.limb[2] = 0xd1cf79ab; ln2.lo.limb[3] = 0xb17217f7;
    ln2.hi = wideAdd(ln2.lo, wideSmall(1));
    uint n = uint(1023 - exponent);
    Bounds z; z.lo = wideSub(wideTimes(ln2.lo, n), logM.hi); z.hi = wideSub(wideTimes(ln2.hi, n), logM.lo);
    // Exact binary64 exponent: all significand bits fit Q128 on this domain.
    int ye;uint64_t ys;f64Unpack(exponentBits,ye,ys);uint shift=uint(ye-1075+128);
    Bounds y;y.lo=wideSmall(0);
    for(uint bit=0;bit<53;bit++)if((ys&(uint64_t(1)<<bit))!=0)y.lo.limb[(bit+shift)/32]|=1U<<((bit+shift)%32);
    y.hi=y.lo;
    z = boundProduct(z, y);
    uint lo = 0, hi = 134217728;
    while (hi - lo > 1)
    {
        uint mid = (lo + hi)/2;
        if (!wideLess(z.lo, wideTimes(ln2.hi, mid))) lo = mid; else hi = mid;
    }
    Bounds r; r.lo = wideSub(z.lo, wideTimes(ln2.hi, lo)); r.hi = wideSub(z.hi, wideTimes(ln2.lo, lo));
    if (!wideLess(r.hi, wideOne())) { status = 3; return 0; }
    Bounds term; term.lo = wideOne(); term.hi = term.lo;
    Bounds sum = term;
    for (uint i = 1; i < 48; i++)
    {
        term = boundDivide(boundProduct(term, r), i);
        if ((i & 1) != 0) { sum.lo = wideSub(sum.lo, term.hi); sum.hi = wideSub(sum.hi, term.lo); }
        else { sum.lo = wideAdd(sum.lo, term.lo); sum.hi = wideAdd(sum.hi, term.hi); }
    }
    // Odd partial sum is a lower bound; next term <=1/48! <2^-128.
    sum.hi = wideAdd(sum.hi, wideSmall(1));
    uint64_t lower = wideToBinary64(sum.lo, lo), upper = wideToBinary64(sum.hi, lo);
    if (lower != upper) { status = 4; return 0; }
    return lower;
}

#endif
