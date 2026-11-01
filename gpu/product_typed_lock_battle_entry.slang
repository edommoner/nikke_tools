// One shared coordinate clock and typed world for weapons and original skills.
#define PORTABLE_PRODUCT_TYPED_LOCK
#define PORTABLE_COORDINATE_TYPED_TARGETS
#define PORTABLE_COORDINATE_TYPED_WEAPONS
#define PORTABLE_COORDINATE_TYPED_AIM
#define PORTABLE_COORDINATE_TYPED_ACTORS
#define PORTABLE_COORDINATE_TYPED_OWNERS
#define DT_INPUT(s,offset) ((s).inputBase+115680U+(offset))
#define CTW_SCRATCH(s) DT_OUTPUT((s).resourceOutput,220768U)
#define DF_ROW_ENABLED(s,row) ((row)==commands[DF_DESCRIPTOR(s)])
#define DF_BODY_FALLBACK(s,row) false
#define DF_MATCH(s,row,at,selected) (results[at+3]!=0&&results[at]==2)
#include "product_coordinate_lock_battle_entry.slang"
