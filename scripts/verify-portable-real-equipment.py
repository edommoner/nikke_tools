"""Real preparation -> 45 equipment definitions -> shared GPU initialization.
This explicitly excludes character skills and battle policies. It is not an
all-character battle certification or a CPU-trace-to-GPU conversion.
"""
import argparse,copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter
from detail_coverage import body_for
from portable_runtime import compile_program,run_programs


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('metal','cuda'),default='metal');args=parser.parse_args()
    path=ROOT/f'research/portable-real-equipment-{args.backend}.json'
    path.write_text(json.dumps(dict(passed=False,gpu_execution_verified=False,stage='preparing'))+'\n')
    tracked=[p for folder in ('app','scripts') for p in (ROOT/folder).glob('*.py')]
    tracked += [p for folder in ('calculator','runner','data') for p in (ROOT/'research/upstream/nikke-calc-master'/folder).rglob('*') if p.suffix in ('.py','.json')]
    tracked += [ROOT/'data/engine-effect-overrides.json']
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(tracked))}
    names=[n for n,d in adapter.META.items() if isinstance(d,dict) and not n.startswith(('_','test_')) and not adapter.spec.is_preview(n)]
    programs=[];inputs=[]
    for name in names:
        squad=[name]+[n for n in ('모더니아','루주','마스트 : 로망틱 메이드','도라','얀') if n!=name][:4]
        prepared=adapter.evaluate({**body_for(squad,grown=True),'_portable_static_inputs':True})
        assert not prepared['cpu_battle_executed'] and prepared['all_character_effects_included']
        equipment=[x for x in prepared['effects'] if x['effect'].get('_source_tag')=='equipment']
        assert len(equipment)==45 and len(prepared['effects'])>len(equipment)
        weapons=copy.deepcopy(prepared['weapons'])
        for w in weapons:w['enabled']=False;w['stage']=0
        programs.append(compile_program(prepared['chars'],[(x['effect'],x['owner']) for x in equipment],
                        [[0,24,0,0,0,-1,0,0],[0,2,0,0,-1,0,0,0]],prepared['base_atk'],allies=prepared['allies'],
                        combat=dict(weapons=weapons,targets=[dict(hp=1e30,defense=prepared['enemy']['def'])],trace='summary')))
        inputs.append((name,prepared,equipment))
    result=run_programs(programs,backend=args.backend)
    result.update(passed=False,stage='readback-before-CPU-reference',validation_sha256=hashes,
                  full_character_verified=0,character_skills_included=False,battle_policies_connected=False,cpu_trace_used_as_gpu_input=False)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    from calculator.buff_manager import BuffManager
    from calculator.timeline import CharState
    rows=[]
    for (name,prepared,equipment),gpu in zip(inputs,result['results']):
        raw=[(copy.deepcopy(x['effect']),x['owner']) for x in equipment]
        class BM(BuffManager):
            def _register_all(self):self._effects=raw;self._build_notify_index()
        stats={c['name']:dict(atk=atk,hp=h['base_hp'],**{'def':h['base_defense']}) for c,atk,h in zip(prepared['chars'],prepared['base_atk'],prepared['allies'])}
        bm=BM(prepared['chars'],state=dict(base_stats=stats,enemy=prepared['enemy'],full_burst=False,rng_acc={}))
        for c in prepared['chars']:bm.notify('battle_start',0,c['name'])
        expected=[];query=gpu['queries'][0]
        for who,c in enumerate(prepared['chars']):
            n=c['name'];attack=bm.get_buffs(n,'__enemy__',0)['atk_pct'];ammo=CharState(c,stats[n]['atk'],prepared['enemy']['code'])._full_ammo(bm,0);defense=bm._effective_def(n)
            assert query['attack_buffs'][who]==attack,(name,n,'attack')
            assert query['combat']['weapons'][who]['ammo']==ammo,(name,n,'ammo')
            assert query['allies'][who]['defense']==defense,(name,n,'defense')
            expected.append(dict(character=n,attack_buff=attack,ammo=ammo,defense=defense))
        rows.append(dict(character=name,passed=True,equipment_definitions=len(equipment),excluded_character_effects=len(prepared['effects'])-len(equipment),
                         prepared_effects_sha256=hashlib.sha256(json.dumps(prepared['effects'],sort_keys=True,ensure_ascii=False).encode()).hexdigest(),expected=expected))
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    result.update(passed=True,stage='verified',cases=rows,scope='203 real fixed grown squads: equipment-only initialization with 45 real definitions each; not full battles')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=True,squads=len(rows),definitions_per_squad=45,device=result['transport']['device'],full_character_verified=0)))


if __name__=='__main__':main()
