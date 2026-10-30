        if ((d.kind == 2 || d.kind == 13 || d.kind == 14) && (d.target > 1 || !f64Finite(d.value))) { s.error = 64; break; }
        PROJECTILE_ADMIT_STAGE(s,403)
         s.lazyEnabled |= uint(d.lazyGroup != 0);
        if ((WORLD_RELOAD_FORCE_KIND(d.kind) || d.kind == 0 || d.kind == 4 || d.kind == 5 || d.kind == 6 || d.kind == 7 || d.kind == 8 || d.kind == 13 || d.kind == 14 || d.kind == 22 || d.kind == 24 || d.kind == 27 || d.kind == 31 || d.kind == 30 || d.kind==29) && !(
#ifdef PORTABLE_ENEMY_AMMO
            enemyAmmoDefinition(s,j,d)?enemyAmmoRecipientValid(s,j,d):
#endif
            validRecipientPlan(input+P_RECIPIENT_BASE+j*8,d.enemyBuff != 0,input))) { s.error = 64; break; }
        if (d.lazyGroup != 0)
        {
            uint plan = input+P_RECIPIENT_BASE+j*8, selector = commands[plan];
            if (d.lazyGroup > s.count || d.kind != 0 && d.kind != 4 || !(selector == 5 || selector == 6 || selector == 7 || selector == 15 || selector == 16 || selector == 19 || selector == 25)) { s.error = 64; break; }
            uint previous = s.lazyGroupDefinition[d.lazyGroup-1];
            if (previous != 0)
            {
                uint prior = input+P_RECIPIENT_BASE+(previous-1)*8;
                bool same = definition_owner(s.inputBase,previous-1) == d.owner;
                for (uint field = 0; field < 4; field++) if (commands[prior+field] != commands[plan+field]) same = false;
                if (!same) { s.error = 64; break; }
            }
            else s.lazyGroupDefinition[d.lazyGroup-1] = j+1;
        }
        if((d.stat==S_optimal_range_min || d.stat==S_optimal_range_max_pct) && (d.kind!=0 || d.enemyBuff!=0 || !hasRangeGeometry(s))) { s.error=64;break; }
        uint packet = input+P_DAMAGE_DEFINITION_BASE+j*P_DAMAGE_DEFINITION_WORDS;
        PROJECTILE_ADMIT_STAGE(s,404)
        if(d.stat==S_element_code_override)
        {
            elementDefinitions++;
            if(d.kind!=0 || d.enemyBuff!=0 || d.damageRoute>codeNames || d.damageFlags!=0 || !f64Zero(d.value)) { s.error=64;break; }
            for(uint word=1;word<P_DAMAGE_DEFINITION_WORDS;word++) if(commands[packet+word]!=0) { s.error=64;break; }
            if(s.error!=0) break;
        }
        uint periodic = input+P_PERIODIC_DEFINITION_BASE+j*2;
        bool accumEnemy=false;
#ifdef PORTABLE_ENEMY_MOVEMENT
        accumEnemy=enemyMovementMarker(s,d);
#endif
#ifdef PORTABLE_DAMAGE_ACCUM
        accumEnemy=d.kind==0 && d.stat>=81U && d.stat<=83U;
#endif
#ifdef PORTABLE_ENEMY_HEALING
        accumEnemy=accumEnemy || d.kind==0 && d.stat==S_heal_received_pct;
#endif
        if (d.enemyBuff != 0 && (d.enemyBuff != 1 || !(d.kind==0 || d.kind==4 && (d.flags&56)!=0 || d.kind==4 && d.stat==0 || d.kind==19) || s.combat == 0 || d.lazyGroup != 0 ||
            !WORLD_ENEMY_ATTACK_STAT(s,d,(d.stat == S_enemy_def_down_pct || d.stat == S_def_caster_based_pct || d.stat == S_received_dmg_pct || accumEnemy || projectileCarrierStat(d.stat) || namedMagnitudeStat(d.stat) || d.stat == S_taunt || d.stat == S_stun || d.kind==4 && (d.flags&56)!=0 || d.kind==4 && d.stat==0 || d.kind==19)) ||
            !validEnemyRoute(s.inputBase,d.damageRoute) || d.damageCount == 0 || d.damageCount > 256 || d.damageHits != 0 || d.damageNormal != 0 || !f64Zero(d.damageGauge) || d.damagePending != 0 || d.pendingHits != 0 ||
            commands[input+P_RECIPIENT_BASE+j*8] != 4)) { s.error = 64; break; }
        if (d.kind == 3 && (!f64Finite(d.value) || !validEnemyRoute(s.inputBase,d.damageRoute) || d.damageCount == 0 || d.damageCount > 256 || d.damageHits > 256 ||
            d.damageRoute >= 2 && s.combat == 0 || !f64Finite(d.damageGauge) || f64Less(d.damageGauge,0) && !f64Equal(d.damageGauge,F64_SIGN | ONE) || f64Less(f64FromI64(1000000),d.damageGauge) ||
            d.damageNormal > 1 || FULL_BURST_PENDING_INVALID(s,d))) { s.error = 64; break; }
        if ((d.kind == 3 || d.enemyBuff != 0 || (d.kind == 1 || d.kind == 15) && d.target == 2) && (d.damageRoute == 7 || d.damageRoute == 8))
            for (uint target = 1; target < s.targetCount; target++) if (!f64Zero(s.targetDefense[target])) { s.error = 64; break; }
        if(!validDurationExtension(input,s.count,s.combat,j)) { s.error=64;break; }
        if(!validRemovalDefinition(input,s.combat,j)) { s.error=64;break; }
        PROJECTILE_ADMIT_STAGE(s,405)
