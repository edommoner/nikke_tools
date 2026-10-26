// Resource-backed interval storage. One owner thread per case; no shared writes.
#include "coordinate_arc_arena_layout.slang"
struct ArcArenaWords
{
    uint base;
    uint errorAt;
    __subscript(uint index) -> uint64_t
    {
        get
        {
            if(index>=ARC_ARENA_CAPACITY){results[errorAt]=1;return 0;}
            uint at=base+index*2;return uint64_t(results[at])|(uint64_t(results[at+1])<<32);
        }
        set(uint64_t value)
        {
            if(index>=ARC_ARENA_CAPACITY){results[errorAt]=1;return;}
            uint at=base+index*2;results[at]=uint(value);results[at+1]=uint(value>>32);
        }
    }
};
struct ArcArenaView
{
    uint caseBase;
    uint scratchOffset;
    uint base;
    ArcArenaWords start;
    ArcArenaWords end;
    property uint count
    {
        get{uint n=results[base];if(n>ARC_ARENA_CAPACITY){results[caseBase+scratchOffset]=1;return 0;}return n;}
        set(uint value){if(value>ARC_ARENA_CAPACITY){results[caseBase+scratchOffset]=1;results[base]=0;}else results[base]=value;}
    }
    property bool overflow
    {
        get{return results[base+1]!=0;}
        set(bool value){results[base+1]=uint(value);}
    }
};
ArcArenaView arcArenaView(uint caseBase,uint scratchOffset,uint slot)
{
    if(slot>=ARC_ARENA_SLOTS){results[caseBase+scratchOffset]=1;slot=0;}
    ArcArenaView v;v.caseBase=caseBase;v.scratchOffset=scratchOffset;
    v.base=caseBase+scratchOffset+ARC_ARENA_HEADER_WORDS+slot*ARC_ARENA_ROW_WORDS;
    v.start.base=v.base+2;v.end.base=v.start.base+ARC_ARENA_CAPACITY*2;
    v.start.errorAt=caseBase+scratchOffset;v.end.errorAt=v.start.errorAt;return v;
}
ArcArenaView arcArenaSibling(ArcArenaView anchor,uint slot){return arcArenaView(anchor.caseBase,anchor.scratchOffset,slot);}
bool arcArenaDistinctOne(ArcArenaView a,ArcArenaView value)
{
    if(a.base==value.base){results[value.caseBase+value.scratchOffset]=1;return false;}return true;
}
bool arcArenaDistinct(ArcArenaView a,ArcArenaView b,ArcArenaView value)
{
    return arcArenaDistinctOne(a,value)&&arcArenaDistinctOne(b,value);
}
