// One original clock, actor fields and sampled pellet; no baked trajectory.
#define PORTABLE_MOVING_TYPED
#define PORTABLE_ENEMY_MOVEMENT
#define PORTABLE_COORDINATE_LOGICAL_ACTORS
#include "moving_typed_layout.slang"
#include "logical_actor_geometry_history.slang"
#undef WORLD_SKILL_HISTORY_ADMIT
#define WORLD_SKILL_HISTORY_ADMIT(s) (commands[(s).inputBase+TMR_LAG_BASE]==0x4c414731U && commands[(s).inputBase+TMR_LAG_BASE+1U]==1U && commands[DF_EXTRA(s)+12U]==3U)
#include "world_coordinate_typed_logical_owner_entry.slang"
#include "enemy_movement_runtime.slang"
#include "moving_typed_attachment_runtime.slang"
