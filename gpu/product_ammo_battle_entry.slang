#define PORTABLE_PRODUCT_ENEMY_AMMO
#define PORTABLE_PRODUCT_ENEMY_HEALING
#define PORTABLE_ENEMY_HEALING
#define ENEMY_HEALING_ENABLED(s) (commands[(s).inputBase+EHL_BASE]!=0)
#include "enemy_healing_ammo_layout.slang"
#define PORTABLE_ENEMY_AMMO_SELF_DESTRUCT
#define PORTABLE_ADD_SELF_DESTRUCT
#define ADD_SELF_DESTRUCT_ENABLED(s) productEnemyAmmoHasSelfDestruct(s)
#include "enemy_ammo_self_destruct_layout.slang"
#define PORTABLE_ENEMY_AMMO
#define PORTABLE_ADD_ATTACK_BATTLE
#include "world_add_attack_battle_layout.slang"
#include "enemy_ammo_layout.slang"
#define WORLD_ENEMY_AMMO_RESOURCE_KIND(s,row,d,legacy) (d.kind==11 && worldSkillsEnabled(s) && resourceDefinition(s,row).op==3 && (resourceDefinition(s,row).flags&2)!=0 ? false : (legacy))
// Use the complete existing output tail; no stride or runtime storage growth.
#define RESOURCE_TRACE_CAPACITY ((productEnemyAmmoHasSelfDestruct(s)||ENEMY_HEALING_ENABLED(s)) ? EAM_RESOURCE_CAPACITY : (128U+(EAM_OUTPUT_WORDS-EAM_OUTPUT_BASE-EAM_RESOURCE_BASE)/8U))
#define RESOURCE_TRACE_ENABLED(s) true
#define RESOURCE_TRACE_AT(output,index) ((index)<128U ? (output)+P_RESOURCE_TRACE_BASE+(index)*8U : (output)+EAM_OUTPUT_BASE+EAM_RESOURCE_BASE+((index)-128U)*8U)
#define portableEvents unusedProductAmmoBaseEntry
#ifdef PORTABLE_PRODUCT_AMMO_TARGET
#include "product_target_battle_entry.slang"
#elif defined(PORTABLE_PRODUCT_AMMO_GROUP)
#include "product_group_battle_entry.slang"
#include "product_group_target_axes.slang"
#else
#include "product_battle_entry.slang"
#endif
#undef portableEvents
#include "world_add_attack_cursor.slang"
#include "world_add_attack_battle_runtime.slang"
#include "enemy_ammo_runtime.slang"
#include "add_self_destruct_runtime.slang"
#include "enemy_ammo_self_destruct_runtime.slang"
#include "enemy_healing_runtime.slang"
// Authored literal rows only: reserve the existing final-queue receipt bank
// only when a self-destruct row exists, including a future generation.
bool productEnemyAmmoHasSelfDestruct(inout Runtime s)
{
    for(uint node=0;node<32;node++)
        if(commands[s.inputBase+ADB_BASE+ADB_ROW_BASE+node*ADB_ROW_WORDS+4]==1)return true;
    return false;
}
// Keep every original descriptor, then validate the remaining zero padding.
uint productAmmoPrefix(uint input)
{
#ifdef PORTABLE_PRODUCT_AMMO_TARGET
    return 110112U;
#elif defined(PORTABLE_PRODUCT_AMMO_GROUP)
    return commands[input+104408U]==0x50474131U ? 104672U : 104408U;
#else
    return 104400U;
#endif
}
bool initializeProductAmmoPrefix(inout Runtime s)
{
#ifdef PORTABLE_PRODUCT_AMMO_TARGET
    return initializeDestructibleBattle(s)&&validBattleModifierAxes(s)&&validShieldBattleRoutes(s);
#elif defined(PORTABLE_PRODUCT_AMMO_GROUP)
    return commands[s.inputBase+104408U]==0 || validProductGroupTargetAxes(s);
#else
    return true;
#endif
}
bool validProductAmmoPadding(uint input)
{
    for(uint i=productAmmoPrefix(input);i<ADB_BASE;i++)
        if((i<EHL_BASE||i>=EHL_BASE+EHL_WORDS)&&commands[input+i]!=0)return false;
    return true;
}
bool initializeProductAmmoHealing(inout Runtime s)
{
    if(!ENEMY_HEALING_ENABLED(s))
    {
        for(uint i=0;i<EHL_WORDS;i++)if(commands[s.inputBase+EHL_BASE+i]!=0)return false;
        return true;
    }
    return initializeEnemyHealing(s);
}
#include "product_ammo_entry.slang"
