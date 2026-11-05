// Explicit policy for a frozen ordinal; no live compaction or retargeting.
static const uint LD_READY=0U,LD_EMPTY=1U,LD_MISSING=2U,LD_STALE=3U,LD_DEAD=4U;
uint lockDeliveryIndex(uint hit,uint count)
{if(count==0)return 0xffffffffU;return (hit-1U)%count;}
uint lockDeliveryStatus(uint frozenGeneration,bool present,uint currentGeneration,bool alive)
{return !present?LD_MISSING:currentGeneration!=frozenGeneration?LD_STALE:!alive?LD_DEAD:LD_READY;}
