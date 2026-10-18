// min(1, x^binary64(2.55)), x >= 0. Integer interval arithmetic, Q128
// fractional bits in 192-bit unsigned storage. No native floating point.
// Return only when both rigorous bounds round to the same binary64 value.
struct Wide { uint limb[6]; };
struct Bounds { Wide lo; Wide hi; };

Wide wideSmall(uint x) { Wide a = {}; a.limb[0] = x; return a; }
Wide wideOne() { Wide a = {}; a.limb[4] = 1; return a; }
bool wideLess(Wide a, Wide b)
{
    for (int i = 5; i >= 0; i--) if (a.limb[i] != b.limb[i]) return a.limb[i] < b.limb[i];
    return false;
}
Wide wideAdd(Wide a, Wide b)
{
    Wide r; uint64_t carry = 0;
    for (uint i = 0; i < 6; i++) { carry += uint64_t(a.limb[i]) + b.limb[i]; r.limb[i] = uint(carry); carry >>= 32; }
    return r;
}
Wide wideSub(Wide a, Wide b)
{
    Wide r; uint64_t borrow = 0;
    for (uint i = 0; i < 6; i++)
    {
        uint64_t sub = uint64_t(b.limb[i]) + borrow;
        r.limb[i] = uint(uint64_t(a.limb[i]) - sub); borrow = uint64_t(a.limb[i]) < sub ? 1 : 0;
    }
    return r;
}
Wide wideTimes(Wide a, uint n)
{
    Wide r; uint64_t carry = 0;
    for (uint i = 0; i < 6; i++) { carry += uint64_t(a.limb[i]) * n; r.limb[i] = uint(carry); carry >>= 32; }
    return r;
}
Wide wideDivide(Wide a, uint n, bool up)
{
    Wide r; uint64_t remainder = 0;
    for (int i = 5; i >= 0; i--)
    { uint64_t next = (remainder << 32) | a.limb[i]; r.limb[i] = uint(next / n); remainder = next % n; }
    return up && remainder != 0 ? wideAdd(r, wideSmall(1)) : r;
}
Wide wideProduct(Wide a, Wide b, bool up)
{
    uint product[12] = {};
    for (uint i = 0; i < 6; i++)
    {
        uint64_t carry = 0;
        for (uint j = 0; j < 6; j++)
        {
            uint64_t next = uint64_t(a.limb[i]) * b.limb[j] + product[i+j] + carry;
            product[i+j] = uint(next); carry = next >> 32;
        }
        product[i+6] = uint(carry);
    }
    Wide r; for (uint i = 0; i < 6; i++) r.limb[i] = product[i+4];
    bool remainder = (product[0] | product[1] | product[2] | product[3]) != 0;
    return up && remainder ? wideAdd(r, wideSmall(1)) : r;
}
Bounds boundProduct(Bounds a, Bounds b)
{
    Bounds r; r.lo = wideProduct(a.lo, b.lo, false); r.hi = wideProduct(a.hi, b.hi, true); return r;
}
Bounds boundDivide(Bounds a, uint n)
{
    Bounds r; r.lo = wideDivide(a.lo, n, false); r.hi = wideDivide(a.hi, n, true); return r;
}
Bounds ratioBounds(uint64_t numerator, uint64_t denominator)
{
    Bounds r = {}; uint64_t remainder = numerator;
    for (int bit = 127; bit >= 0; bit--)
    {
        remainder <<= 1;
        if (remainder >= denominator) { remainder -= denominator; r.lo.limb[bit/32] |= 1U << (bit%32); }
    }
    r.hi = remainder != 0 ? wideAdd(r.lo, wideSmall(1)) : r.lo; return r;
}
uint64_t wideToBinary64(Wide a, uint scale)
{
    int highest = -1;
    for (uint i = 0; i < 192; i++) if ((a.limb[i/32] & (1U << (i%32))) != 0) highest = int(i);
    if (highest < 0) return 0;
    uint64_t significand = 0; bool sticky = false;
    for (int i = 0; i <= highest; i++) if ((a.limb[i/32] & (1U << (i%32))) != 0)
    {
        int at = i - highest + 55;
        if (at >= 0) significand |= uint64_t(1) << uint(at); else sticky = true;
    }
    if (sticky) significand |= 1;
    return f64Pack(0, highest - 128 - int(scale) + 1023, significand);
}

uint64_t coreProbability(uint64_t x, out uint status)
{
    status = 0;
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
    // Exact binary64 2.55, not the rational 51/20.
    Bounds y; y.lo = wideSmall(0); y.lo.limb[2] = 0xccccc000; y.lo.limb[3] = 0x8ccccccc; y.lo.limb[4] = 2; y.hi = y.lo;
    z = boundProduct(z, y);
    uint lo = 0, hi = 4096;
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
