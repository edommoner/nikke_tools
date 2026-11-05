// The complete resident executor; only physical snapshot/notification hooks vary.
#define PORTABLE_COORDINATE_PHYSICAL
#define WEAPON_TYPED_DAMAGE(s,who,w,coefficient,when,legacy) coordinatePhysicalSample(s,who,w,coefficient,when)
#ifdef PORTABLE_COORDINATE_SAMPLING
#define WEAPON_TYPED_PELLET(s,w,who,when,output,hit,amount) sampleCoordinatePhysicalPellet(s,w,who,when,output,hit)
#define WEAPON_BODY_AMOUNT(s,who,legacy) deliverSampledCoordinateShot(s,who,legacy)
#else
#define WEAPON_TYPED_PELLET(s,w,who,when,output,hit,amount) true
#define WEAPON_BODY_AMOUNT(s,who,legacy) coordinatePhysicalDeliver(s,who,legacy)
#endif
#define WEAPON_BODY_SUPPRESSED(s,who,hit) true
#include "world_coordinate_composed_entry.slang"
#include "coordinate_physical_runtime.slang"
