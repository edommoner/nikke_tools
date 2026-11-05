#ifdef PORTABLE_NAMED_ENEMY
#define NAMED_ENEMY_ARGUMENT(row) ,row
#define NAMED_ENEMY_PARAMETER ,uint definition=0xffffffffU
#else
#define NAMED_ENEMY_ARGUMENT(row)
#define NAMED_ENEMY_PARAMETER
#endif
// New recipient routes belong only to the private world executor.
bool validEnemyRoute(uint input,uint route)
{
    if(route<=9) return true;
#ifdef PORTABLE_NAMED_ENEMY
    if(route==11) return commands[input+P_WORLD_ACTOR_POOL_INPUT_BASE]==0x57485031;
#endif
#if defined(PORTABLE_WORLD_PROJECTILE) && defined(PORTABLE_WORLD_ACTOR_FIELDS)
    return route==10 && commands[input+P_ENEMY_TARGET_META_BASE]==1 && commands[input+P_WORLD_ACTOR_POOL_INPUT_BASE]==0x57485031;
#else
    return false;
#endif
}
