// Generated from portable_original_lock_layout.py.
#define PL_PULSE_CAPACITY 256U
#define PL_PULSE_AT(s,index) ((s).resourceOutput+1069200U+(index)*16U)
#define LP_DIAGNOSTIC_CAPACITY 512U
#define LP_TRACE_AT(output,index) ((output)+1073296U+(index)*16U)
#define TCS_TRACE_CAPACITY 2048U
#define TCS_TRACE_AT(s,index) ((s).resourceOutput+1081488U+(index)*20U)
#define WF_TRACE_CAPACITY 8192U
#define WF_TRACE_AT(s,index) ((s).resourceOutput+1122448U+(index)*8U)
#define WT_TRACE_CAPACITY 4096U
#define WT_TRACE_AT(s,index) ((s).resourceOutput+1187984U+(index)*8U)
#ifdef PORTABLE_PRODUCT_LONG_LOCK
#define PL_LAYOUT_OUTPUT 2032000U
#define PORTABLE_WORLD_SKILL_HISTORY
#define WORLD_SKILL_HISTORY_ADMIT(s) (true)
#undef PL_PULSE_CAPACITY
#define PL_PULSE_CAPACITY 1024U
#undef PL_PULSE_AT
#define PL_PULSE_AT(s,index) ((index)<256U ? (s).resourceOutput+1069200U+(index)*16U : (s).resourceOutput+1310720U+((index)-256U)*16U)
#undef LP_DIAGNOSTIC_CAPACITY
#define LP_DIAGNOSTIC_CAPACITY 2048U
#undef LP_TRACE_AT
#define LP_TRACE_AT(output,index) ((index)<512U ? (output)+1073296U+(index)*16U : (output)+1323008U+((index)-512U)*16U)
#undef TCS_TRACE_CAPACITY
#define TCS_TRACE_CAPACITY 8192U
#undef TCS_TRACE_AT
#define TCS_TRACE_AT(s,index) ((index)<2048U ? (s).resourceOutput+1081488U+(index)*20U : (s).resourceOutput+1347584U+((index)-2048U)*20U)
#undef WF_TRACE_CAPACITY
#define WF_TRACE_CAPACITY 16384U
#undef WF_TRACE_AT
#define WF_TRACE_AT(s,index) ((index)<8192U ? (s).resourceOutput+1122448U+(index)*8U : (s).resourceOutput+1470464U+((index)-8192U)*8U)
#undef WT_TRACE_CAPACITY
#define WT_TRACE_CAPACITY 16384U
#undef WT_TRACE_AT
#define WT_TRACE_AT(s,index) ((index)<4096U ? (s).resourceOutput+1187984U+(index)*8U : (s).resourceOutput+1536000U+((index)-4096U)*8U)
#undef PL_SHOT_CAPACITY
#define PL_SHOT_CAPACITY 128U
#undef PL_SNAPSHOT_AT
#define PL_SNAPSHOT_AT(s,index) ((index)<31U ? (s).resourceOutput+1050120U+(index)*520U : (s).resourceOutput+1634304U+((index)-31U)*520U)
#undef LP_SHOT_TIME_AT
#define LP_SHOT_TIME_AT(s,index) ((index)<31U ? (s).resourceOutput+1068368U+(index)*2U : (s).resourceOutput+1684744U+((index)-31U)*2U)
#undef WORLD_SKILL_TRACE_CAPACITY
#define WORLD_SKILL_TRACE_CAPACITY 2048U
#undef WORLD_SKILL_TRACE_AT
#define WORLD_SKILL_TRACE_AT(s,index) ((index)<128U ? (s).resourceOutput+512192U+(index)*48U : (s).resourceOutput+1684938U+((index)-128U)*48U)
#undef PORTABLE_PACKET_FATE_CAPACITY
#define PORTABLE_PACKET_FATE_CAPACITY 2048U
#undef PF_FLAG_AT
#define PF_FLAG_AT(output,index) ((index)<128U ? (output)+1069072U+(index)*1U : (output)+1777098U+((index)-128U)*1U)
#endif
