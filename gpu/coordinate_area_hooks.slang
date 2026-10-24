// Shared selector/landing bindings for legacy and composed entries.
#ifndef PORTABLE_COORDINATE_AREA_HOOKS
#define PORTABLE_COORDINATE_AREA_HOOKS
#define sampleCoordinateSkill(s,d,v,t,p) sampleCoordinateAreaSkill(s,d,v,t,p,interruptAmount,interruptReach)
#define captureCoordinateCast captureCoordinateAreaCast
#define validCoordinateSkillDefinition validCoordinateAreaSkill
#define deliverCoordinateParts deliverCoordinateAreaTargets
#define PORTABLE_COORDINATE_SKILLS
#define PORTABLE_COORDINATE_POOL
#endif
