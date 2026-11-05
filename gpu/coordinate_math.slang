// Two-dimensional CPython-compatible norm for shared CUDA/Metal geometry.
// Integer-only IEEE binary64 bits. Round the scaled normal norm to53 bits,
// then rescale with nearest/even gradual underflow, matching vector_norm.
// Four limbs keep every square and midpoint comparison exact, including
// subnormal output quanta. No approximate sqrt or native float/double.
struct CoordinateWide {uint64_t v[4];};
CoordinateWide cmWide(uint64_t hi,uint64_t lo)
{CoordinateWide r;r.v[0]=lo;r.v[1]=hi;r.v[2]=0;r.v[3]=0;return r;}
CoordinateWide cmShift(CoordinateWide a,uint n)
{
    CoordinateWide r=cmWide(0,0);uint words=n/64,bits=n%64;
    for(uint i=0;i<4;i++)if(i>=words){r.v[i]=a.v[i-words]<<bits;if(bits!=0&&i>words)r.v[i]|=a.v[i-words-1]>>(64-bits);}
    return r;
}
CoordinateWide cmAdd(CoordinateWide a,CoordinateWide b)
{
    CoordinateWide r;uint64_t carry=0;
    for(uint i=0;i<4;i++){uint64_t sum=a.v[i]+b.v[i],value=sum+carry;r.v[i]=value;carry=uint64_t(sum<a.v[i]||value<sum);}
    return r;
}
bool cmLess(CoordinateWide a,CoordinateWide b)
{for(int i=3;i>=0;i--){if(a.v[i]!=b.v[i])return a.v[i]<b.v[i];}return false;}
CoordinateWide cmSquare(uint64_t x,uint shift)
{uint64_t hi,lo;mulWide(x,x,hi,lo);return cmShift(cmWide(hi,lo),shift);}
[noinline]
uint64_t coordinateHypot(uint64_t a,uint64_t b)
{
    a=f64Abs(a);b=f64Abs(b);
    // Python hypot lets infinity dominate NaN; all other NaNs are canonical.
    if(a==F64_INF||b==F64_INF)return F64_INF;
    if(f64Nan(a)||f64Nan(b))return F64_NAN;
    if(a<b){uint64_t swap=a;a=b;b=swap;}
    if(b==0)return a;
    int ea,eb;uint64_t sa,sb;f64Unpack(a,ea,sa);f64Unpack(b,eb,sb);
    uint gap=uint(ea-eb);
    // At gap >=28, y/x <2^-27. sqrt(x*x+y*y)-x <x*2^-55,
    // strictly below half an ulp of x, including subnormal x.
    if(gap>=28)return a;
    CoordinateWide sum=cmAdd(cmSquare(sa,2*gap),cmSquare(sb,0));
    int base=eb-1075,quantum=ea-1075;
    uint shift=uint(quantum-base);
    CoordinateWide nextBinade=cmShift(cmWide(0,1),2*(shift+53));
    if(!cmLess(sum,nextBinade)){quantum++;shift++;}
    if(quantum>=972)return F64_INF;
    uint64_t root=0;
    for(int bit=52;bit>=0;bit--)
    {
        uint64_t candidate=root|(uint64_t(1)<<uint(bit));
        if(!cmLess(sum,cmSquare(candidate,2*shift)))root=candidate;
    }
    CoordinateWide fourSum=cmShift(sum,2),midpoint=cmSquare(2*root+1,2*shift);
    bool above=cmLess(midpoint,fourSum),equal=!above&&!cmLess(fourSum,midpoint);
    if(above||(equal&&(root&1)!=0))root++;
    // Keep CPython's second rounding when the original result is subnormal.
    return f64Pack(0,quantum+1075,root<<3);
}
