"""Compile the unchanged L2 oracle's squad-independent inputs to L2FT v1.

Wire: b'L2FT0001', little-endian uint64 word count, binary64 words, UTF-8
JSON metadata. Integer fields are exact binary64 integers. See l2.h for records.
Only finite profile inputs are accepted. Python 3.12+ sum semantics are explicit.
"""
import argparse, json, math, pathlib, struct, sys
from l2_score import buckets, burst_dependent, ENEMY
KEYS = ['normal_atk_dmg_pct','atk_pct','atk_flat','enemy_def_down_pct','enemy_def_down_flat','def_ignore_pct','crit_rate','crit_rate_skill','crit_dmg','crit_dmg_skill','core_dmg_pct','charge_dmg_pct','charge_dmg_mag_pct','atk_dmg_pct','burst_dmg_pct','burst_dmg_aoe_pct','burst_dmg_single_pct','pierce_dmg_pct','armor_break_dmg_pct','dot_dmg_pct','projectile_explosion_dmg','projectile_attachment_dmg','sequential_dmg_pct','part_dmg_pct','intercept_dmg_pct','received_dmg','split_dmg_pct','element_bonus_pct','is_element_match']
FLAGS = ['is_normal_atk','is_armor_break_damage','is_full_burst','is_optimal_range','is_core_damage','is_weapon_mode_skill','is_full_charge','is_burst_damage','is_aoe_burst','is_single_burst','is_pierce_damage','is_dot','is_projectile_explosion','is_projectile_attachment','is_sequential','is_part','is_intercept','is_split']
OPCODES = ['unknown','all','self','exclude_self','name','burst3','squad','first','adjacent','right','weapon','weapon_exclude','class','code','code_exclude','code_weapon','code_weapon_first','charge_first']
DYNAMIC_OPCODES = ['top_atk','top_atk_exclude','weapon_top_atk','lowest_hp','lowest_hp_exclude','top_hp','top_def','below_def']

def _compile_v1(p):
    chars=p['characters'];names=list(chars);index={n:i for i,n in enumerate(names)};keys=list(KEYS)
    for c in chars.values():
        for obj in [*(g['own'] for g in c['groups']),*(b['amount'] for b in c['buffs'])]:
            for k in obj:
                if k not in keys:keys.append(k)
    opcodes=OPCODES+DYNAMIC_OPCODES if 's20' in p else OPCODES
    ki={k:i for i,k in enumerate(keys)};symbols={None:0};coverage={n:0 for n in opcodes}
    def sym(x):
        if x not in symbols:symbols[x]=len(symbols)
        return symbols[x]
    def rule(r):
        if isinstance(r,list):return [v for x in r for v in rule(x)]
        op='unknown';a=b=0;limit=2147483647
        if r in ENEMY or r=='all_allies':op='all'
        elif r=='self':op='self'
        elif r=='all_allies_excl_self':op='exclude_self'
        elif r in index:op='name';a=index[r]
        elif r=='allies_burst3':op='burst3'
        elif r=='allies_squad':op='squad'
        else:
            q=r.split(':') if isinstance(r,str) else [];prefix=q[0] if q else ''
            dynamic={'allies_top_atk':'top_atk','allies_top_atk_excl':'top_atk_exclude','allies_weapon_top_atk':'weapon_top_atk','allies_lowest_hp':'lowest_hp','allies_lowest_hp_excl':'lowest_hp_exclude','allies_top_hp':'top_hp','allies_top_def':'top_def','allies_below_def':'below_def'}
            if 's20' in p and prefix in dynamic:
                op=dynamic[prefix]
                if op!='below_def':limit=int(q[-1])
                if op=='weapon_top_atk':a=sym(q[1])
            if prefix in ('allies','allies_adjacent','allies_right','allies_top_base_charge_time'):
                op={'allies':'first','allies_adjacent':'adjacent','allies_right':'right','allies_top_base_charge_time':'charge_first'}[prefix];limit=int(q[1])
            elif prefix in ('allies_weapon','allies_weapon_excl_self','allies_class','allies_code','allies_code_excl_self','allies_code_weapon','allies_code_weapon_leftmost'):
                op={'allies_weapon':'weapon','allies_weapon_excl_self':'weapon_exclude','allies_class':'class','allies_code':'code','allies_code_excl_self':'code_exclude','allies_code_weapon':'code_weapon','allies_code_weapon_leftmost':'code_weapon_first'}[prefix];a=sym(q[1])
                if op in ('code_weapon','code_weapon_first'):b=sym(q[2])
                if op=='class' and len(q)>2:limit=int(q[2])
                if op=='code_weapon_first':limit=int(q[3])
        coverage[op]+=1
        return [(opcodes.index(op),a,b,limit)]
    words=[1,len(chars),len(keys),p['settings']['duration'],int(sys.version_info>=(3,12))]
    for name,c in chars.items():
        m=c['metadata'];stage=str(m.get('burst_stage',''));mask=4 if name=='레드 후드' and stage=='A' else (7 if stage=='A' else {'1':1,'2':2,'3':4}.get(stage,0))
        words.extend([mask,int(stage=='3'),float(m.get('burst_cooldown',40)),sym(m.get('squad')),int(bool(m.get('squad'))),sym(m.get('weapon_type')),sym(m.get('class')),sym(m.get('element_code')),m.get('charge_time') or 0,max(c['reference']['casts'],1),max(c['reference']['phase_seconds'][0],1e-9),max(c['reference']['phase_seconds'][1],1e-9),len(c['groups']),len(c['buffs']),len(c['dependencies'])])
        for g in c['groups']:
            h=g['flags'];w=g['weapon'];base=buckets(g,g['own']);coeff=h.get('coeff');core=h.get('core_prob')
            words.extend([int(g['phase']),sum(1<<i for i,f in enumerate(FLAGS) if h.get(f)),g['unit'],w['damage_coeff'] if coeff is None else coeff,g['base_atk'],g['enemy_def'],float(h.get('is_core',False)) if core is None else core,(w.get('core_dmg_mult',200)-100)/100,w.get('full_charge_mult',100)/100])
            words.extend(g['own'].get(k,0.) for k in keys);words.extend(base);words.extend(g.get('self_buckets',base))
        for q in c['buffs']:
            rules=rule(q['effect']['target']);words.extend([int(q['phase']),int(burst_dependent(q['effect'])),len(q['amount']),len(rules)])
            for k,v in q['amount'].items():
                if k=='atk_flat' and 'caster_atk_coefficient' in q:v=q['caster_atk_coefficient']*c['base_stats']['atk']
                words.extend([ki[k],v])
            for r in rules:words.extend(r)
        for d in c['dependencies']:words.extend([int(d['kind'] in ('dealt_fixed_damage','accum_split_damage')),int(d['scope']=='team'),d['ratio']])
    if not all(math.isfinite(x) for x in words):raise ValueError('non-finite profile input')
    meta=dict(version=1,names=names,keys=keys,flags=FLAGS,opcodes=opcodes,profile_opcode_counts=coverage,sum_mode='cpython312' if words[4] else 'left_fold')
    return b'L2FT0001'+struct.pack('<Q',len(words))+struct.pack('<%sd'%len(words),*words)+json.dumps(meta,ensure_ascii=False,separators=(',',':')).encode()

def compile_profiles(p):
    raw=_compile_v1(p)
    if 's20' not in p:return raw
    payload,meta=unpack(raw);words=list(struct.unpack('<%sd'%(len(payload)//8),payload));words[0]=2
    action=['max_ammo_pct','max_ammo_flat','reload_speed_pct','attack_speed_pct','charge_speed_pct','charge_time_flat','reload_ratio_pct']
    words.append(p['s20']['switches'])
    words.extend(meta['keys'].index(k) if k in meta['keys'] else -1 for k in action)
    for c in p['characters'].values():
        m=c['metadata'];w=c.get('weapon_cycle_s20',{});own=c.get('rank_own_s20',{});base=c['base_stats']
        rate=float(w.get('fire_rate_max') or w.get('fire_rate') or m.get('fire_rate') or 1.)
        words.extend([base['atk'],base.get('hp',0.),base.get('def',0.),own.get('atk_pct',0.),own.get('atk_flat',0.),rate,float(w.get('charge_time_base') or m.get('charge_time') or 0.),float(w.get('post_fire_delay') or 0.),float(m.get('clip_count',1)),float(m.get('max_ammo',1)),float(m.get('reload_time',0.)),1./rate if m.get('input_type')=='DOWN_Charge' else 0.,int(bool(m.get('is_charge'))),int(str(m.get('burst_stage'))=='1')])
        for g in c['groups']:words.extend([g.get('action_rate_s20',1.),g.get('context_unit_s20',g['unit']),int(bool(g.get('cast_scaled_s20'))),int(g.get('action_eligible_s20',bool(g['flags'].get('is_normal_atk'))))])
        words.extend(q.get('condition_s20',0) for q in c['buffs'])
        rules=c.get('mechanics_s20',[]);words.append(len(rules))
        for r in rules:words.extend(r if len(r)==7 else [*r,0])
    if not all(math.isfinite(x) for x in words):raise ValueError('non-finite S20 profile input')
    meta.update(version=2,s20=p['s20'])
    magic=b'L2FT0002'
    if 's22' in p:
        words[0]=3;words.append(p['s22']['switches'])
        for name,c in p['characters'].items():
            words.extend(c['reference']['phase_seconds'])
            words.extend(int(bool(g.get('cast_scaled_s22'))) for g in c['groups'])
            words.extend(int(name in q.get('recipients',[])) for q in c['buffs'])
        if any(q.get('caps_s22') for c in p['characters'].values() for q in c['buffs']):
            words.append(128)
            for c in p['characters'].values():
                for q in c['buffs']:
                    words.extend(q.get('caps_s22',{}).get(k,0.) for k in q['amount'])
        meta.update(version=3,s22=p['s22']);magic=b'L2FT0003'
    if not all(math.isfinite(x) for x in words):raise ValueError('non-finite profile extension')
    return magic+struct.pack('<Q',len(words))+struct.pack('<%sd'%len(words),*words)+json.dumps(meta,ensure_ascii=False,separators=(',',':')).encode()

def unpack(raw):
    if raw[:8] not in (b'L2FT0001',b'L2FT0002',b'L2FT0003'):raise ValueError('unknown table version')
    n=struct.unpack_from('<Q',raw,8)[0];end=16+8*n
    return raw[16:end],json.loads(raw[end:])

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('profiles',type=pathlib.Path);a.add_argument('output',type=pathlib.Path);args=a.parse_args();args.output.write_bytes(compile_profiles(json.loads(args.profiles.read_text())))
