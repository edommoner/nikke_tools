        if(kind!=0&&kind!=2&&kind!=3&&kind!=4&&kind!=6&&kind!=7&&kind!=8&&kind!=24
#ifdef PORTABLE_COORDINATE_EXISTING_HANDLERS
            &&kind!=18&&kind!=20&&kind!=21&&kind!=31&&kind!=34&&kind!=35&&kind!=37 // Private existing handlers; kind acceptance is not native battle certification.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_COVER_REVIVE
            &&kind!=30 // Existing shared broken-cover revival and recipient handlers.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_SHIELD_HEAL
            &&kind!=27 // Existing shared protection healing and periodic instant handlers.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_FORCED_RELOAD
            &&kind!=23 // Existing common reload request and lifecycle handlers.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_SOURCE_OPS
            &&kind!=15&&kind!=33 // Existing named duration and forced skill-slot handlers.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_CLEANSE
            &&kind!=26 // Existing allied cleanse and enemy overlay dispel handlers.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_STACKS
            &&kind!=16&&kind!=17&&kind!=19 // Existing own-stack and current-stack increase handlers.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_AMMO
            &&kind!=13&&kind!=14 // Existing shared percentage and flat ammo handlers.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_RESOURCES
            &&kind!=9&&kind!=10 // Existing shared gauge charge/consume handlers.
#endif
#ifdef PORTABLE_ENEMY_AMMO
            &&kind!=11 // Existing ammo-observed gauge consumption; opt-in enemy magazine battles.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_CLOCKS
            &&kind!=22 // Existing shared remaining skill-clock reduction.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_ROSTER
            &&kind!=1 // Existing named removal, recipient snapshot and callbacks.
#endif
#ifdef PORTABLE_COORDINATE_HEALING
            &&kind!=32 // Existing received-healing pool discharge, including lifecycle.
#endif
#ifdef PORTABLE_COORDINATE_BURST_CONTROLS
            &&((kind!=5&&kind!=25)||!burstControls(s)) // Existing shared cooldown/reentry handlers.
#endif
#ifdef PORTABLE_COORDINATE_SQUAD_MODE_STATE
            &&kind!=29 // Existing shared revival handler; mode flags survive on_down/on_revive.
#endif
        )return false; // Shared weapon/heal/reduce dispatch.
