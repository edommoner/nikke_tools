// One Runtime/WorldSchedule/DFS, with typed target state after all coordinate banks.
#define PORTABLE_COORDINATE_TYPED_TARGETS
#define DT_INPUT(s,offset) ((s).inputBase+109968+(offset))
#define DT_OUTPUT(output,offset) ((output)+1769856+(offset))
#include "destructible_shield_frame_hooks.slang"
#include "world_coordinate_original_shared_entry.slang"
#include "coordinate_typed_geometry_runtime.slang"
#include "destructible_shield_frame_impl.slang"
bool initializeCoordinateTypedTargets(inout Runtime s)
{
    for(uint i=1769856;i<2032000;i++) results[s.resourceOutput+i]=0;
    if(commands[DF_DESCRIPTOR(s)+3]==0)
    {
        for(uint i=0;i<5712;i++) if(commands[DF_EXTRA(s)+i]!=0) return false;
        return true;
    }
    return initializeDestructibleBattle(s)&&validBattleModifierAxes(s)&&validShieldBattleRoutes(s);
}
