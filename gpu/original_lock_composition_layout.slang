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
