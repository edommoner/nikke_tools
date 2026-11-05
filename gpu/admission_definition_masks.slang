        uint bullet = input+P_BULLET_DEFINITION_BASE+j*2;
        if (d.bulletDuration > 0x7fffffff || d.bulletBound > 1 || d.bulletDuration == 0 && d.bulletBound != 0 || d.bulletDuration != 0 && (s.combat == 0 || d.kind != 0 && d.kind != 4)) { s.error = 64; break; }
        uint extra = input+P_DEFINITION_EXTRA_BASE+j*P_DEFINITION_EXTRA_WORDS;
        uint health = input+P_HEALTH_DEFINITION_BASE+j*P_HEALTH_DEFINITION_WORDS;
        uint duration = input+P_DURATION_DEFINITION_BASE+j*2;
        if (d.kind == 0 && d.stat == S_fullburst_duration)
        {
            if (s.combat == 0 || d.durationGroup == 0 || d.durationGroup > s.count || d.durationCast > 1) { s.error = 64; break; }
            bool cast = false;
            for (uint slot = 0; slot < d.triggerCount; slot++) if (commands[input+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8] == 3 && commands[input+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8+3] == 0) cast = true;
            if (d.durationCast != uint(cast)) { s.error = 64; break; }
            s.durationEnabled = 1;
        }
        else if (d.durationGroup != 0 || d.durationCast != 0) { s.error = 64; break; }
        // Low bits retain the named-event/audience policy. Higher bits hold an
        // optional stat-applied event name plus one, authored by the compiler.
        uint statNotice = d.buffEvent >> 2;
        if (d.enemyBuff > 1 || d.kind != 0 && d.kind != 4 && d.buffEvent != 0 ||
            statNotice > P_DEFINITIONS || statNotice != 0 && (d.kind != 0 || d.stat != S_dot_dmg_pct && d.stat != S_split_dmg_pct)) { s.error = 64; break; }
        if (d.healthScaling > 1) { s.error = 64; break; }
        PROJECTILE_ADMIT_STAGE(s,406)
        if (d.kind == 0 && d.stat == S_cover_hp_pct) s.coverMask |= 1;
        if ((d.kind == 7 || d.kind == 30) && (f64Less(d.value,0) || d.kind == 30 && f64Zero(d.value))) { s.error = 64; break; }
        if (d.kind == 7 || d.kind == 30) s.coverMask |= 2;
        if (d.kind == 0 && (d.stat >= S_max_hp_pct && d.stat <= S_max_hp_only_pct || d.stat == S_max_hp_from_max_hp_pct)) s.healthMask |= 1;
        if (d.kind == 0 && d.enemyBuff == 0 && ((d.alliedFlags & 1) != 0 || d.stat == S_def_caster_based_pct)) s.healthMask |= 2;
        if (d.kind == 0 && d.stat == S_heal_received_pct) s.healthMask |= 4;
        if (d.kind == 0 && d.stat == S_outgoing_heal_pct) s.healthMask |= 8;
        if (d.kind == 0 && d.stat == S_lifesteal_pct) s.healthMask |= 64;
        if(d.stat==S_heal_split)
        {
#ifndef PORTABLE_WORLD_ROSTER
            s.error=64;break;
#else
            if(s.combat==0 || d.kind!=0 || d.enemyBuff!=0 || d.healthScaling!=0 || d.alliedFlags!=0 || d.damageFlags!=0 || d.quantityFlags!=0 || d.queryResolve!=0 || !f64Finite(d.value)) { s.error=64;break; }
            s.healthMask|=128;
#endif
        }
        if (d.kind == 6 || d.kind == 8) s.healthMask |= 16;
        if (d.group >= s.count || d.alias >= int(j)) { s.error = 64; break; }
        PROJECTILE_ADMIT_STAGE(s,407)
        if(d.stat==S_focus_fire)
        { if(d.kind!=0 || s.combat==0 || !focusAimEnabled(s) || commands[input+P_WORLD_FRAME_INPUT_BASE]==0 || d.enemyBuff!=0 || d.healthScaling!=0 || d.alliedFlags!=0 || d.damageFlags!=0 || d.quantityFlags!=0 || !f64Finite(d.value) || !f64Zero(d.interval)) { s.error=64;break; }s.incomingMask|=64; }
        if (d.kind == 0 && d.stat == S_invincible) s.incomingMask |= 1;
        if (d.kind == 0 && d.stat == S_undying) s.incomingMask |= 2;
        if (d.kind == 0 && d.stat == S_received_dmg_pct) s.incomingMask |= 4;
        if ((d.kind == 13 || d.kind == 14 || d.kind == 5 || d.kind == 24 || d.kind == 0 && d.stat == S_burst_cooldown) && s.combat == 0) { s.error = 64; break; }
        if (d.kind == 0 && d.stat == S_burst_cooldown) s.burstModifierMask |= 1;
        if (d.kind == 0 && d.stat == S_reload_speed_pct) s.quantityMask |= 64;
        if (d.kind == 0 && d.stat == S_max_ammo_flat) s.quantityMask |= 16;
        if (d.kind == 0 && d.stat == S_charge_time_flat) s.quantityMask |= 32;
        if (d.kind == 0 && d.stat == S_max_ammo_pct) s.quantityMask |= 1;
        if (d.kind == 0 && (d.stat == S_charge_speed_pct || d.stat == S_charge_speed_caster_based_pct)) s.quantityMask |= 2;
        if ((d.quantityFlags & 64) != 0) s.quantityMask |= 4;
        if (d.kind == 0 && d.stat == S_charge_time_fixed) s.quantityMask |= 8;
