"""Stream bit comparisons across Python, native CLI/binding and standalone WASM.

Full reproduction: --profiles PATH --out DIR --random 200000 --full.
The first mismatch raises with the exact ordered squad and raw 64-bit values.
"""
import argparse, collections, ctypes as C, json, pathlib, random, struct, subprocess, sys, time
HERE=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
import l2_score, l2_fast
from l2_compile import compile_profiles, OPCODES, DYNAMIC_OPCODES

def synthetic():
    # Every recipient leaf opcode, negative slices, union deduplication, Red Hood,
    # missing coverage, distinct base charge times and stable ties.
    names=['레드 후드','a','b','c','d','e','f'];chars={}
    rules=['unsupported','all_allies','self','all_allies_excl_self','a','allies_burst3','allies_squad','allies:2','allies_adjacent:1','allies_right:2','allies_weapon:AR','allies_weapon_excl_self:AR','allies_class:x:2','allies_code:fire','allies_code_excl_self:fire','allies_code_weapon:fire:AR','allies_code_weapon_leftmost:fire:AR:1','allies_top_base_charge_time:2', ['all_allies','all_allies','self'], 'allies:-1','allies_adjacent:-1','allies_right:-2','allies_class:x:-1','allies_top_base_charge_time:-1']
    for i,n in enumerate(names):
        g=dict(phase=0,unit=1.123,own={'atk_pct':1.},flags={'is_normal_atk':True,'is_full_charge':True,'is_burst_damage':True,'is_pierce_damage':True,'is_dot':True},weapon={'damage_coeff':13.65,'full_charge_mult':250},base_atk=100.,enemy_def=10.)
        buffs=[dict(phase=j%2,effect={'target':r,'trigger':{'burst_cast':True} if j%3 else {}},amount={'atk_pct':.123+j,'atk_flat':.456},**({'caster_atk_coefficient':.123} if j%2 else {})) for j,r in enumerate(rules)]
        chars[n]=dict(metadata=dict(burst_stage=['A','1','2','3','3','2','1'][i],burst_cooldown=20+20*(i%2),squad='s' if i%2 else '',weapon_type='AR' if i%2 else 'SG',element_code='fire' if i%3 else 'water',**{'class':'x'},charge_time=[0,1,2,2,3,1,0][i]),groups=[g,dict(g,phase=1)],buffs=buffs,dependencies=[dict(kind='dealt_fixed_damage',scope='team',ratio=.123)],base_stats={'atk':100.+i},reference={'casts':0,'phase_seconds':[0.,20.]})
    return dict(settings={'duration':180.},characters=chars)

def compare(p,squads,out,lib,wasm,label):
    import l2_score_s20, l2_score_s22
    out.mkdir(parents=True,exist_ok=True);table=out/(label+'.l2ft');table.write_bytes(compile_profiles(p));oracle=(l2_score_s22.Score if 's22' in p else l2_score_s20.Score if 's20' in p else l2_score.Score)(p);fast=l2_fast.Score(p,library=lib)
    count=0;opcounts=collections.Counter();failcoverage=0;rh=0;union=0;started=time.perf_counter()
    # Bounded batches prevent storing the random acceptance output corpus.
    for offset in range(0,len(squads),1024):
        batch=squads[offset:offset+1024];indices=fast._indices(batch);native,members=fast.score_indices(indices,True)
        wire=bytes(indices)
        w=subprocess.run(['node',str(HERE/'runner.mjs'),'--wasm',str(wasm),'--table',str(table)],input=wire,capture_output=True,check=True).stdout
        cli=subprocess.run([str(lib.parent/'l2-cli'),str(table)],input=wire,capture_output=True,check=True).stdout
        expected=bytearray()
        for squad in batch:
            values=oracle.member_scores(squad);total=max(sum(values.values()),1.);expected.extend(struct.pack('<6d',total,*values.values()))
            if not l2_score.cycle(squad,p['characters'],p['settings']['duration'])[2]:failcoverage+=1
            rh+=int('레드 후드' in squad)
            for n in squad:
                for b in p['characters'][n]['buffs']:
                    r=b['effect']['target'];union+=isinstance(r,list)
            count+=1
        bound=b''.join(struct.pack('<6d',native[i],*members[i*5:i*5+5]) for i in range(len(batch)))
        for name,actual in [('binding',bound),('CLI',cli),('WASM',w)]:
            if actual!=expected:
                for i in range(len(batch)):
                    if actual[i*48:i*48+48]!=expected[i*48:i*48+48]:
                        raise AssertionError(dict(engine=name,label=label,row=offset+i,squad=batch[i],expected=expected[i*48:i*48+48].hex(),actual=actual[i*48:i*48+48].hex()))
        if offset%10240==0:print(label,offset+len(batch),flush=True)
    # Count leaf opcode visits from each source appearance (including self-only).
    appearances=collections.Counter(n for squad in squads for n in squad)
    from l2_compile import unpack
    for n,k in appearances.items():
        one=dict(p,characters={n:p['characters'][n]})
        # Rules naming other characters need the original symbol table; count
        # using a profile retaining metadata but only this source's buffs.
        q=dict(p,characters={name:dict(c,buffs=c['buffs'] if name==n else []) for name,c in p['characters'].items()})
        meta=unpack(compile_profiles(q))[1]
        for op,v in meta['profile_opcode_counts'].items():opcounts[op]+=v*k
    result=dict(label=label,squads=count,member_values=count*5,total_values=count,engines=['binding','CLI','WASM'],differences=0,opcode_visits=dict(opcounts),failed_cycle_coverage=failcoverage,red_hood_squads=rh,union_buff_visits=union,seconds=time.perf_counter()-started)
    fast.close();return result

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--profiles',type=pathlib.Path,required=True);a.add_argument('--out',type=pathlib.Path,required=True);a.add_argument('--random',type=int,default=512);a.add_argument('--full',action='store_true');args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    lib=l2_fast.build();wasm=l2_fast.build(True);p=json.loads(args.profiles.read_text());results=[]
    if args.full:
        for label,file in [('S9','s9-dataset.jsonl'),('S1-external','s1-results.jsonl')]:
            rows=[json.loads(l) for l in (HERE.parent/file).read_text().splitlines()]
            rows=[r for r in rows if r['backend']=='native_detail' and r.get('total_damage',0)>0]
            results.append(compare(p,[r['members'] for r in rows],args.out,lib,wasm,label))
        # Also cover saved failed/native-other rows: all valid ordered inputs
        # belong to the scorer's bit contract regardless of truth availability.
        for label,file in [('S9-other','s9-dataset.jsonl'),('S1-other','s1-results.jsonl')]:
            rows=[json.loads(l) for l in (HERE.parent/file).read_text().splitlines()]
            rows=[r for r in rows if not (r['backend']=='native_detail' and r.get('total_damage',0)>0)]
            if rows:results.append(compare(p,[r['members'] for r in rows],args.out,lib,wasm,label))
        if 's22' in p:
            # Score-only shortlist input manifest. No dev or sealed truth read.
            from search_s21 import DEFAULT
            roster=json.loads((DEFAULT/'s21/rosters.json').read_text())['names']
            orders=json.loads((DEFAULT/'s21/orders-206-15.json').read_text())['rows']
            results.append(compare(p,[[roster[i] for i in r['best']['indices']] for r in orders],args.out,lib,wasm,'S22-shortlist10000'))
    rng=random.Random(190019);names=list(p['characters']);squads=[rng.sample(names,5) for _ in range(args.random)]
    results.append(compare(p,squads,args.out,lib,wasm,'random'))
    import itertools
    q=synthetic();samples=[list(s) for s in itertools.islice(itertools.permutations(q['characters'],5),256)]
    samples+=[list('abcdef')[:5],list('bcdef')];results.append(compare(q,samples,args.out,lib,wasm,'synthetic'))
    if 's20' in p:
        import copy
        import l2_score_s20
        q['s20']=dict(version=2,switches=15)
        rules=['allies_top_atk:2','allies_top_atk_excl:1','allies_weapon_top_atk:AR:2','allies_lowest_hp:2','allies_lowest_hp_excl:1','allies_top_hp:2','allies_top_def:2','allies_below_def']
        for i,c in enumerate(q['characters'].values()):
            c['base_stats'].update(hp=1000.+i,**{'def':10.+i})
            c['metadata'].update(is_charge=bool(i%2),max_ammo=6,reload_time=2.,fire_rate=2.,clip_count=3,input_type='DOWN_Charge')
            c['rank_own_s20']={'atk_pct':float(i),'atk_flat':float(i)}
            c['mechanics_s20']=[[0,2,0,2,1.2,1],[2,1,2,1,1.,0]] if i==1 else [[0,3,3,1,1.3,0],[3,1,0,1,-5.,1]]
            for g in c['groups']:
                g['own'].update(max_ammo_pct=13.3,reload_speed_pct=7.,charge_speed_pct=23.,attack_speed_pct=17.)
                g['action_rate_s20']=l2_score_s20.action_rate(c,g['own']);g['context_unit_s20']=g['unit']*.9
                g['flags']['is_burst_damage']=False;g['cast_scaled_s20']=bool(i%2);g['action_eligible_s20']=bool(i%3)
            c['buffs'].extend(dict(phase=1,effect={'target':r},amount={'atk_pct':2.}) for r in rules)
            for j,b in enumerate(c['buffs']):b['condition_s20']=j%4
        for mask in range(16):
            q['s20']['switches']=mask
            results.append(compare(q,samples,args.out,lib,wasm,'synthetic-s20-'+str(mask)))
        if 's22' in p:
            # Exercise every v3 bit combination with observed/unobserved own
            # supply, conditional removal, caps and zero reference phases.
            # The v2 switch space is independently covered immediately above.
            q['s20']['switches']=2
            q['s22']=dict(version=3,switches=0)
            for i,(name,c) in enumerate(q['characters'].items()):
                for g in c['groups']:g['cast_scaled_s22']=bool(i%2)
                for j,b in enumerate(c['buffs']):
                    b['recipients']=[name] if j%2 else []
                    if j%3==0:b['caps_s22']={'atk_pct':.25,'atk_flat':.125}
            for mask in range(0,256,16):
                q['s22']['switches']=mask
                results.append(compare(q,samples,args.out,lib,wasm,'synthetic-s22-'+str(mask)))
    covered={op for r in results for op,n in r['opcode_visits'].items() if n};required=set(OPCODES+(DYNAMIC_OPCODES if 's20' in p else []));assert covered==required,(covered,required)
    receipt=dict(seed=190019,random_count=args.random,results=results,opcode_visits=dict(sum((collections.Counter(r['opcode_visits']) for r in results),collections.Counter())))
    (args.out/'identity.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
