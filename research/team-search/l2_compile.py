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

def compile_profiles(p):
    chars=p['characters'];names=list(chars);index={n:i for i,n in enumerate(names)};keys=list(KEYS)
    for c in chars.values():
        for obj in [*(g['own'] for g in c['groups']),*(b['amount'] for b in c['buffs'])]:
            for k in obj:
                if k not in keys:keys.append(k)
    ki={k:i for i,k in enumerate(keys)};symbols={None:0};coverage={n:0 for n in OPCODES}
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
            if prefix in ('allies','allies_adjacent','allies_right','allies_top_base_charge_time'):
                op={'allies':'first','allies_adjacent':'adjacent','allies_right':'right','allies_top_base_charge_time':'charge_first'}[prefix];limit=int(q[1])
            elif prefix in ('allies_weapon','allies_weapon_excl_self','allies_class','allies_code','allies_code_excl_self','allies_code_weapon','allies_code_weapon_leftmost'):
                op={'allies_weapon':'weapon','allies_weapon_excl_self':'weapon_exclude','allies_class':'class','allies_code':'code','allies_code_excl_self':'code_exclude','allies_code_weapon':'code_weapon','allies_code_weapon_leftmost':'code_weapon_first'}[prefix];a=sym(q[1])
                if op in ('code_weapon','code_weapon_first'):b=sym(q[2])
                if op=='class' and len(q)>2:limit=int(q[2])
                if op=='code_weapon_first':limit=int(q[3])
        coverage[op]+=1
        return [(OPCODES.index(op),a,b,limit)]
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
    meta=dict(version=1,names=names,keys=keys,flags=FLAGS,opcodes=OPCODES,profile_opcode_counts=coverage,sum_mode='cpython312' if words[4] else 'left_fold')
    return b'L2FT0001'+struct.pack('<Q',len(words))+struct.pack('<%sd'%len(words),*words)+json.dumps(meta,ensure_ascii=False,separators=(',',':')).encode()

def unpack(raw):
    if raw[:8]!=b'L2FT0001':raise ValueError('unknown table version')
    n=struct.unpack_from('<Q',raw,8)[0];end=16+8*n
    return raw[16:end],json.loads(raw[end:])

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('profiles',type=pathlib.Path);a.add_argument('output',type=pathlib.Path);args=a.parse_args();args.output.write_bytes(compile_profiles(json.loads(args.profiles.read_text())))
