// Generated ordered spread body; no helper in the default profile.
#ifndef PORTABLE_NORMAL_SPREAD_BODY
#define PORTABLE_NORMAL_SPREAD_BODY \
    uint64_t spread = s.spreadStart[who]; \
    if (!f64Zero(s.spreadShots[who])) \
    { \
        uint64_t progress = f64Div(smaller(s.warm[who],s.spreadShots[who]),s.spreadShots[who]); \
        spread = f64Add(spread,f64Mul(f64Add(s.spreadEnd[who],spread ^ F64_SIGN),progress)); \
    } \
    uint64_t slope = uint64_t(0x3f829888) << 32 | 0xf861a60d; \
    spread = larger(ONE,f64Mul(spread,f64Add(ONE,f64Mul(slope,accuracy) ^ F64_SIGN))); \
    s.lastSpread[who] = spread;
#endif
