// Integer stack contract. Inputs may be binary64 resources, but native
// ref_count truncates gauges and all owned stack constructors preserve ints.
// Clamp before the checked narrowing conversion: even a huge finite delta
// can safely saturate a finite cap. Unlimited out-of-range results fail closed.
[noinline]
uint64_t stackIntegerDelta(uint64_t value,uint policy,out uint status)
{
    status=0;
    if (!f64Finite(value) || policy>3) { status=64;return 0; }
    uint64_t delta=(policy&1)!=0 && f64Zero(value) ? uint64_t(0x3ff00000)<<32 : f64Integral(value,1);
    if ((policy&2)!=0) delta^=F64_SIGN;
    return f64Zero(delta) ? 0 : delta;
}
[noinline]
uint checkedStackChange(uint64_t current,uint64_t value,uint cap,uint floor,uint policy,out uint status)
{
    status=0;
    if (!f64Finite(current) || !f64Finite(value) || !f64Equal(current,f64Integral(current,1)) ||
        floor>1 || cap==0 || cap!=0xffffffff && cap>0x7fffffff || policy>3)
    { status=64;return 0; }
    uint64_t delta=stackIntegerDelta(value,policy,status);
    if(status!=0) return 0;
    uint64_t next=f64Add(current,delta),minimum=f64FromI64(floor);
    if (cap!=0xffffffff && f64Less(f64FromI64(cap),next)) next=f64FromI64(cap);
    if (f64Less(next,minimum)) next=minimum;
    if (!f64Finite(next) || f64Less(f64FromI64(0x7fffffff),next)) { status=2;return 0; }
    uint convert;uint64_t integer=f64ToI64(next,1,convert);
    if (convert!=0) { status=2;return 0; }
    return uint(integer);
}

[noinline]
uint checkedStackIncrement(uint current,uint cap,out uint status)
{
#ifdef PORTABLE_STACK_INCREMENT_INTEGER_CANDIDATE
    status=0;
    if(cap==0 || cap!=0xffffffff && cap>0x7fffffff) { status=64;return 0; }
    uint64_t next=uint64_t(current)+1;
    if(cap!=0xffffffff) next=min(next,uint64_t(cap));
    if(next>0x7fffffff) { status=2;return 0; }
    return uint(next);
#else
    return checkedStackChange(f64FromI64(current),uint64_t(0x3ff00000)<<32,cap,0,0,status);
#endif
}
