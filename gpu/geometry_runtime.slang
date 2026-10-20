// Only descriptor reads vary;the range arithmetic stays one common implementation.
#ifdef PORTABLE_WORLD_OVERLAYS
#define WG_CORE(s) (worldOverlayEnabled(s)?woCore(s):loadNumber(s.inputBase+P_GEOMETRY_BASE+2))
#define WG_FLAGS(s,meta) (worldOverlayEnabled(s)?woRangeFlags(s):commands[meta])
#define WG_MASK(s,meta) (worldOverlayEnabled(s)?woRangeMask(s):commands[meta+1])
#define WG_DISTANCE(s,meta) (worldOverlayEnabled(s)?woDistance(s):loadNumber(meta+4))
#else
#define WG_CORE(s) loadNumber(s.inputBase+P_GEOMETRY_BASE+2)
#define WG_FLAGS(s,meta) commands[meta]
#define WG_MASK(s,meta) commands[meta+1]
#define WG_DISTANCE(s,meta) loadNumber(meta+4)
#endif
// Immutable authored geometry,shared by CUDA and Metal;no Runtime arrays.
bool hasRangeGeometry(inout Runtime s) { return (commands[s.inputBase+P_GEOMETRY_BASE]&1)!=0; }
bool geometryCore(inout Runtime s) { return !f64Less(WG_CORE(s),ONE); }
bool geometryRange(inout Runtime s,uint who,bool activeMode,uint64_t minimumPct,uint64_t maximumPct)
{
    uint meta=s.inputBase+P_GEOMETRY_BASE;
    int mode=activeMode && s.combat!=0 ? s.modeIndex[who] : -1;
    uint at=mode>=0 ? meta+56+uint(mode)*6 : meta+16+who*8;
    if((WG_FLAGS(s,meta)&2)==0) return (WG_MASK(s,meta)&(1U<<(commands[at]-1)))!=0;
    uint64_t lower=larger(0,f64Mul(loadNumber(at+2),f64Add(ONE,f64Div(minimumPct,HUNDRED)^F64_SIGN)));
    uint64_t upper=f64Mul(loadNumber(at+4),f64Add(ONE,f64Div(maximumPct,HUNDRED)));
    uint64_t epsilon=uint64_t(0x3e112e0b)<<32 | 0xe826d695; // binary64 1e-9
    uint64_t distance=WG_DISTANCE(s,meta);
    return !f64Less(distance,f64Add(lower,epsilon^F64_SIGN)) && !f64Less(f64Add(upper,epsilon),distance);
}
bool validGeometry(inout Runtime s)
{
    uint meta=s.inputBase+P_GEOMETRY_BASE,flags=commands[meta];
    if(flags==0)
    {
        for(uint i=1;i<P_GEOMETRY_WORDS;i++) if(commands[meta+i]!=0) return false;
        return true;
    }
    if(flags!=1 && flags!=3 || commands[meta+1]>63 || (flags&2)!=0 && commands[meta+1]!=0) return false;
    if(!f64Finite(loadNumber(meta+2)) || f64Less(loadNumber(meta+2),0) || !f64Finite(loadNumber(meta+4))) return false;
    if((flags&2)==0 && !f64Zero(loadNumber(meta+4))) return false;
    for(uint i=6;i<16;i++) if(commands[meta+i]!=0) return false;
    for(uint i=0;i<5+P_DEFINITIONS;i++)
    {
        uint at=i<5 ? meta+16+i*8 : meta+56+(i-5)*6;
        bool mode=i>=5,used=!mode || i-5<s.count && definition_kind(s.inputBase,i-5)==2;
        if(!used) { for(uint k=0;k<6;k++) if(commands[at+k]!=0) return false;continue; }
        if(commands[at]==0 || commands[at]>6 || commands[at+1]!=0) return false;
        uint64_t lo=loadNumber(at+2),hi=loadNumber(at+4);
        if(!f64Finite(lo) || !f64Finite(hi) || f64Less(lo,0) || f64Less(hi,lo)) return false;
        if(!mode && (commands[at+6]!=0 || commands[at+7]!=0)) return false;
    }
    return true;
}

#undef WG_CORE
#undef WG_FLAGS
#undef WG_MASK
#undef WG_DISTANCE
