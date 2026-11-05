// Generated logical geometry admission; common skill-history addresses.
#define PORTABLE_WORLD_SKILL_HISTORY
#define WORLD_SKILL_TRACE_CAPACITY 2048U
#define WORLD_SKILL_TRACE_AT(s,index) ((index)<128U ? (s).resourceOutput+P_WORLD_SKILL_TRACE_BASE+(index)*48U : (s).resourceOutput+1773424U+((index)-128U)*48U)
#define WORLD_SKILL_HISTORY_ADMIT(s) (commands[(s).inputBase+109968U]==0x4c414731U && commands[(s).inputBase+109969U]==1U)
