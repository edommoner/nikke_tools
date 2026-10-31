#define PORTABLE_PRODUCT_ENEMY_AMMO
#define PORTABLE_ENEMY_AMMO
#define PORTABLE_ADD_ATTACK_BATTLE
#include "world_add_attack_battle_layout.slang"
#include "enemy_ammo_layout.slang"
#define WORLD_ENEMY_AMMO_RESOURCE_KIND(s,row,d,legacy) (d.kind==11 && worldSkillsEnabled(s) && resourceDefinition(s,row).op==3 && (resourceDefinition(s,row).flags&2)!=0 ? false : (legacy))
// Use the complete existing output tail; no stride or runtime storage growth.
#define RESOURCE_TRACE_CAPACITY (128U+(EAM_OUTPUT_WORDS-EAM_OUTPUT_BASE-EAM_RESOURCE_BASE)/8U)
#define RESOURCE_TRACE_ENABLED(s) true
#define RESOURCE_TRACE_AT(output,index) ((index)<128U ? (output)+P_RESOURCE_TRACE_BASE+(index)*8U : (output)+EAM_OUTPUT_BASE+EAM_RESOURCE_BASE+((index)-128U)*8U)
#define portableEvents unusedProductAmmoBaseEntry
#include "product_battle_entry.slang"
#undef portableEvents
#include "world_add_attack_cursor.slang"
#include "world_add_attack_battle_runtime.slang"
#include "enemy_ammo_runtime.slang"
#include "product_ammo_entry.slang"
