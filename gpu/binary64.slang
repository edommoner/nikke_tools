// Integer-only IEEE binary64 candidate for CUDA and Metal. Round to nearest,
// ties to even; gradual underflow; canonical quiet NaN. No native double/float.
// Not yet connected to the production interpreter.
static const uint64_t F64_SIGN = uint64_t(1) << 63;
static const uint64_t F64_FRAC = (uint64_t(1) << 52) - 1;
static const uint64_t F64_INF = uint64_t(0x7ff) << 52;
static const uint64_t F64_NAN = F64_INF | (uint64_t(1) << 51);

uint64_t shiftJam(uint64_t x, uint distance)
{
    if (distance == 0) return x;
    if (distance >= 64) return x != 0 ? 1 : 0;
    return (x >> distance) | ((x << (64 - distance)) != 0 ? 1 : 0);
}

bool f64Nan(uint64_t x) { return (x & ~F64_SIGN) > F64_INF; }
bool f64Zero(uint64_t x) { return (x & ~F64_SIGN) == 0; }
bool f64Finite(uint64_t x) { return (x & ~F64_SIGN) < F64_INF; }
uint64_t f64Abs(uint64_t x) { return x & ~F64_SIGN; }

// mode 0: nearest/even, 1: toward zero, 2: floor. Preserve signed zero.
uint64_t f64Integral(uint64_t x, uint mode)
{
    uint64_t magnitude = f64Abs(x), sign = x & F64_SIGN;
    if (f64Nan(x)) return F64_NAN;
    int exponent = int((x >> 52) & 2047) - 1023;
    if (exponent >= 52 || magnitude == 0) return x;
    if (exponent < 0)
    {
        bool one = mode == 2 ? sign != 0 : mode == 0 && magnitude > (uint64_t(1022) << 52);
        return sign | (one ? uint64_t(1023) << 52 : 0);
    }
    uint shift = uint(52 - exponent);
    uint64_t unit = uint64_t(1) << shift, mask = unit - 1, tail = magnitude & mask;
    uint64_t rounded = magnitude & ~mask;
    bool increment = mode == 2 ? sign != 0 && tail != 0 :
        mode == 0 && (tail > (unit >> 1) || (tail == (unit >> 1) && (rounded & unit) != 0));
    if (increment) rounded += unit;
    return sign | rounded;
}

// Explicit range failure, never CUDA's architecture-specific invalid sentinel.
uint64_t f64ToI64(uint64_t x, uint mode, out uint status)
{
    status = 0;
    if (!f64Finite(x)) { status = 1; return 0; }
    uint64_t rounded = f64Integral(x, mode), magnitude = f64Abs(rounded);
    if (magnitude == 0) return 0;
    int exponent = int((rounded >> 52) & 2047) - 1023;
    bool negative = (rounded & F64_SIGN) != 0;
    if (exponent > 63 || (exponent == 63 && (!negative || (rounded & F64_FRAC) != 0)))
    { status = 1; return 0; }
    if (exponent < 0) return 0;
    uint64_t significand = (rounded & F64_FRAC) | (uint64_t(1) << 52);
    uint64_t integer = exponent >= 52 ? significand << uint(exponent - 52) : significand >> uint(52 - exponent);
    return negative ? (~integer + 1) : integer;
}

uint64_t f64FromI64(uint64_t integer)
{
    uint64_t sign = integer & F64_SIGN;
    uint64_t magnitude = sign != 0 ? (~integer + 1) : integer;
    if (magnitude == 0) return 0;
    uint highest = 0;
    for (uint64_t scan = magnitude; scan > 1; scan >>= 1) highest++;
    uint64_t extended = highest > 55 ? shiftJam(magnitude, highest - 55) : magnitude << (55 - highest);
    return f64Pack(sign, int(highest) + 1023, extended);
}

bool f64Equal(uint64_t a, uint64_t b)
{
    return !f64Nan(a) && !f64Nan(b) && (a == b || (f64Zero(a) && f64Zero(b)));
}

bool f64Less(uint64_t a, uint64_t b)
{
    if (f64Nan(a) || f64Nan(b) || f64Equal(a, b)) return false;
    bool negativeA = (a & F64_SIGN) != 0, negativeB = (b & F64_SIGN) != 0;
    if (negativeA != negativeB) return negativeA;
    return negativeA ? a > b : a < b;
}

// significand has three rounding bits; hidden bit is at bit 55.
uint64_t f64Pack(uint64_t sign, int exponent, uint64_t significand)
{
    if (significand == 0) return sign;
    if (significand >= (uint64_t(1) << 56))
    {
        significand = shiftJam(significand, 1);
        exponent++;
    }
    while (significand < (uint64_t(1) << 55) && exponent > 1)
    {
        significand <<= 1;
        exponent--;
    }
    if (exponent < 1)
    {
        significand = shiftJam(significand, uint(1 - exponent));
        exponent = 1;
    }
    uint tail = uint(significand & 7);
    uint64_t rounded = significand >> 3;
    if (tail > 4 || (tail == 4 && (rounded & 1) != 0)) rounded++;
    if (rounded >= (uint64_t(1) << 53)) { rounded >>= 1; exponent++; }
    if (exponent >= 2047) return sign | F64_INF;
    if (rounded < (uint64_t(1) << 52)) exponent = 0;
    return sign | (uint64_t(exponent) << 52) | (rounded & F64_FRAC);
}

void f64Unpack(uint64_t bits, out int exponent, out uint64_t significand)
{
    exponent = int((bits >> 52) & 2047);
    significand = bits & F64_FRAC;
    if (exponent != 0) significand |= uint64_t(1) << 52;
    else
    {
        exponent = 1;
        // Caller handles zero before unpacking.
        while (significand < (uint64_t(1) << 52)) { significand <<= 1; exponent--; }
    }
}

[noinline]
uint64_t f64Add(uint64_t a, uint64_t b)
{
    if (f64Nan(a) || f64Nan(b)) return F64_NAN;
    uint64_t ma = a & ~F64_SIGN, mb = b & ~F64_SIGN;
    if (ma == F64_INF || mb == F64_INF)
    {
        if (ma == mb && ((a ^ b) & F64_SIGN) != 0) return F64_NAN;
        return ma == F64_INF ? a : b;
    }
    // Order by magnitude before subtraction. Equal opposite operands give +0.
    if (ma < mb) { uint64_t swap = a; a = b; b = swap; }
    uint64_t sa = (a & F64_FRAC) | (((a >> 52) & 2047) != 0 ? uint64_t(1) << 52 : 0);
    uint64_t sb = (b & F64_FRAC) | (((b >> 52) & 2047) != 0 ? uint64_t(1) << 52 : 0);
    int ea = max(1, int((a >> 52) & 2047));
    int eb = max(1, int((b >> 52) & 2047));
    sa <<= 3;
    sb = shiftJam(sb << 3, uint(ea - eb));
    if (((a ^ b) & F64_SIGN) == 0) return f64Pack(a & F64_SIGN, ea, sa + sb);
    if (sa == sb) return 0;
    return f64Pack(a & F64_SIGN, ea, sa - sb);
}

void mulWide(uint64_t a, uint64_t b, out uint64_t hi, out uint64_t lo)
{
    uint64_t al = uint(a), ah = a >> 32, bl = uint(b), bh = b >> 32;
    uint64_t p = al * bl;
    uint64_t middle = ah * bl + (p >> 32);
    uint64_t carry = middle >> 32;
    middle = uint(middle) + al * bh;
    hi = ah * bh + carry + (middle >> 32);
    lo = (middle << 32) | uint(p);
}

[noinline]
uint64_t f64Mul(uint64_t a, uint64_t b)
{
    uint64_t sign = (a ^ b) & F64_SIGN;
    uint64_t ma = a & ~F64_SIGN, mb = b & ~F64_SIGN;
    if (f64Nan(a) || f64Nan(b)) return F64_NAN;
    if (ma == F64_INF || mb == F64_INF)
        return ma == 0 || mb == 0 ? F64_NAN : sign | F64_INF;
    if (ma == 0 || mb == 0) return sign;
    int ea, eb; uint64_t sa, sb, hi, lo;
    f64Unpack(a, ea, sa); f64Unpack(b, eb, sb);
    mulWide(sa, sb, hi, lo);
    uint64_t sig = (hi << 15) | (lo >> 49);
    sig |= (lo << 15) != 0 ? 1 : 0;
    return f64Pack(sign, ea + eb - 1023, sig);
}

[noinline]
uint64_t f64Div(uint64_t a, uint64_t b)
{
    uint64_t sign = (a ^ b) & F64_SIGN;
    uint64_t ma = a & ~F64_SIGN, mb = b & ~F64_SIGN;
    if (f64Nan(a) || f64Nan(b) || (ma == F64_INF && mb == F64_INF) || (ma == 0 && mb == 0)) return F64_NAN;
    if (ma == F64_INF || mb == 0) return sign | F64_INF;
    if (ma == 0 || mb == F64_INF) return sign;
    int ea, eb; uint64_t remainder, divisor;
    f64Unpack(a, ea, remainder); f64Unpack(b, eb, divisor);
    int exponent = ea - eb + 1023;
    if (remainder < divisor) { remainder <<= 1; exponent--; }
    uint64_t sig = 0;
    // Long division of normalized significands; remainder stays below 2^54.
    for (uint bit = 0; bit < 56; bit++)
    {
        sig <<= 1;
        if (remainder >= divisor) { remainder -= divisor; sig |= 1; }
        if (bit < 55) remainder <<= 1;
    }
    sig |= remainder != 0 ? 1 : 0;
    return f64Pack(sign, exponent, sig);
}
