// Generated from portable_product_coordinate_lock; full old arenas relocated.
#define PL_LAYOUT_OFFSET 1507712U
#define PL_LAYOUT_OUTPUT 2558208U
#define PL_PULSE_CAPACITY 256U
#define PL_PULSE_AT(s,index) (((s).resourceOutput)+2314768U+(index)*16U)
#define LP_DIAGNOSTIC_CAPACITY 512U
#define LP_TRACE_AT(output,index) ((output)+2318864U+(index)*16U)
#define TCS_TRACE_CAPACITY 2048U
#define TCS_TRACE_AT(s,index) (((s).resourceOutput)+2327056U+(index)*20U)
#define WF_TRACE_CAPACITY 8192U
#define WF_TRACE_AT(s,index) (((s).resourceOutput)+2368016U+(index)*8U)
#define WT_TRACE_CAPACITY 4096U
#define WT_TRACE_AT(s,index) (((s).resourceOutput)+2433552U+(index)*8U)
#define PORTABLE_CUSTOM_PACKET_FATES_LAYOUT
static const uint PF_HEAD=2314624U;
static const uint PF_FLAGS=2314640U;
static const uint PF_CAPACITY=2048U;
static const uint PF_END=2314768U;
static const uint PF_MAGIC=1346777137U;
#define PF_FLAG_AT(output,index) ((index)<128U ? (output)+2314640U+(index) : (output)+2556288U+(index)-128U)
