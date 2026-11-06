// Appended to unmodified Slang-generated implementations by native_binary64_diff.py.
#include <cstdio>
#include <cstdlib>
#include <cfenv>
#include <vector>
#include <limits>
static uint64_t rngState=0x1306b1645eedULL;
static uint64_t randomBits() { rngState^=rngState>>12; rngState^=rngState<<25; rngState^=rngState>>27; return rngState*2685821657736338717ULL; }
static uint64_t counts[6]={};
static void fail(const char* op,uint64_t a,uint64_t b,uint64_t s,uint64_t h) {
    std::fprintf(stderr,"%s a=%016llx b=%016llx soft=%016llx hard=%016llx\n",op,(unsigned long long)a,(unsigned long long)b,(unsigned long long)s,(unsigned long long)h); std::exit(1);
}
static void check(uint64_t a,uint64_t b) {
#define CHECK(OP,I) {auto s=soft_##OP(a,b),h=hard_##OP(a,b); ++counts[I]; if(s!=h) fail(#OP,a,b,s,h);}
    CHECK(f64Add,0); CHECK(f64Mul,1); CHECK(f64Div,2); CHECK(f64Equal,3); CHECK(f64Less,4);
#undef CHECK
    auto s=soft_f64FromI64(a),h=hard_f64FromI64(a); ++counts[5]; if(s!=h) fail("f64FromI64",a,0,s,h);
}
int main(int argc,char** argv) {
    if(std::fegetround()!=FE_TONEAREST) return 2;
    uint64_t pairs=argc>1 ? std::strtoull(argv[1],nullptr,10):20000000;
    std::vector<uint64_t> special;
    for(uint64_t x: {0ULL,1ULL,0xfffffffffffffULL,0x10000000000000ULL,0x7fefffffffffffffULL,0x7ff0000000000000ULL,0x7ff0000000000001ULL,0x7ff8000000000000ULL,0x7fffffffffffffffULL,0x3ff0000000000000ULL,0x3fe0000000000000ULL,0x4000000000000000ULL,0x3ff8000000000000ULL})
        {special.push_back(x);special.push_back(x|0x8000000000000000ULL);}
    // Neighbours of every power of two: ties, cancellation, normalization,
    // exponent boundaries, underflow/overflow and rounding carries.
    for(uint64_t e=0;e<2047;++e) for(int d=-3;d<=3;++d) {
        uint64_t a=(e<<52)+d;
        for(uint64_t b:special) {check(a,b);check(b,a);check(a^0x8000000000000000ULL,b);}
        check(a,a);check(a,a^0x8000000000000000ULL);
        for(int k: {1,52,53,54}) if(e>=uint64_t(k)) {uint64_t b=(e-k)<<52;check(a,b);check(a,b^0x8000000000000000ULL);}
    }
    for(uint64_t a:special) for(uint64_t b:special) check(a,b);
    // Integer edge neighbourhoods include all powers, 2^53 ties and INT64_MIN.
    for(unsigned bit=0;bit<64;++bit) for(int d=-8;d<=8;++d) {uint64_t a=(1ULL<<bit)+d;check(a,0);check(~a+1,0);}
    for(uint64_t i=0;i<pairs;++i) {
        uint64_t a=randomBits(),b=randomBits();
        // One uniform pair and one biased pair per iteration.
        check(a,b);
        {
            static const unsigned exps[]={0,1,2,3,2043,2044,2045,2046,2047};
            unsigned ea=exps[randomBits()%9],eb;
            if(i&1) eb=unsigned(int(ea)+int(randomBits()%7)-3)&2047;
            else eb=exps[randomBits()%9];
            a=(a&0x800fffffffffffffULL)|(uint64_t(ea)<<52);
            b=(b&0x800fffffffffffffULL)|(uint64_t(eb)<<52);
        }
        check(a,b);
    }
    // Independent uniform signed integer words (rather than exponent-biased).
    for(uint64_t i=0;i<pairs;++i) {uint64_t a=randomBits();auto s=soft_f64FromI64(a),h=hard_f64FromI64(a);++counts[5];if(s!=h)fail("f64FromI64",a,0,s,h);}
    std::printf("{\"random_pairs\":%llu,\"counts\":[",(unsigned long long)pairs);
    for(int i=0;i<6;++i) std::printf("%s%llu",i?",":"",(unsigned long long)counts[i]);
    std::puts("],\"differences\":0}");
}
