// New recipient routes belong only to the private world executor.
bool validEnemyRoute(uint input,uint route)
{
    if(route<=9) return true;
#if defined(PORTABLE_WORLD_PROJECTILE) && defined(PORTABLE_WORLD_ACTOR_FIELDS)
    return route==10 && commands[input+P_ENEMY_TARGET_META_BASE]==1 && commands[input+P_WORLD_ACTOR_POOL_INPUT_BASE]==0x57485031;
#else
    return false;
#endif
}
