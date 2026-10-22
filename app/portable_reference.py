"""CPU-only native contract stage, before portable admission or GPU execution."""
import copy,hashlib,importlib,json,platform,sys,time
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
REFERENCES={'skill-hp-basis-protection':('portable_skill_hp_basis_protection_cases','world_skill_hp_basis_native','portable_skill_hp_basis_contracts'),
            'skill-hp-basis':('portable_skill_hp_basis_cases','world_skill_hp_basis_native','portable_skill_hp_basis_contracts'),
            'mode-capacity':('portable_mode_capacity_cases','world_mode_capacity_native','portable_mode_capacity_contracts'),
            'ally-burst':('portable_ally_burst_cases','world_ally_burst_native','portable_ally_burst_contracts'),
            'revive':('portable_revive_cases','world_revive_native','portable_revive_contracts'),
            'entry-reload':('portable_entry_reload_cases','world_entry_reload_native','portable_entry_reload_contracts'),
            'heal-share':('portable_heal_share_cases','world_heal_share_native','portable_heal_share_contracts'),
            'heal-share-extended':('portable_heal_share_extra_cases','world_heal_share_native','portable_heal_share_contracts'),
            'heal-share-targets':('portable_heal_share_target_cases','world_heal_share_native','portable_heal_share_contracts'),
            'heal-share-lifesteal':('portable_heal_share_lifesteal_cases','world_heal_share_native','portable_heal_share_contracts'),
            'parts-skill':('portable_parts_skill_cases','world_parts_skill_native','portable_parts_skill_contracts'),
            'parts-skill-extended':('portable_parts_skill_extra_cases','world_parts_skill_native','portable_parts_skill_contracts'),
            'parts-skill-lifecycle':('portable_parts_skill_lifecycle_cases','world_parts_skill_native','portable_parts_skill_contracts')}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def source_identity():
    paths=[ROOT/'app/portable_reference.py',ROOT/'scripts/nikke_gpu.py',ROOT/'app/engine_worker.py',ROOT/'app/engine_compat.py']
    # Native execution includes installed application compatibility layers (for
    # example weapon_mode_runtime), not only the upstream calculator files.
    paths += sorted((ROOT/'app').glob('*.py'))
    paths += sorted((ROOT/'research/upstream/nikke-calc-master/calculator').rglob('*.py'))
    # These native observers form one call chain. Include the literal factories
    # too, without importing or executing the rest of the research tree.
    paths += sorted((ROOT/'research').glob('world_*native.py'))
    paths += [ROOT/'research'/name for name in ('portable_revive_cases.py','portable_revive_contracts.py','portable_persona_cases.py','portable_stun_cases.py','world_enemy_attack_cases.py','portable_burst_recipient_cases.py','portable_recipient_extension_cases.py','world_revive_native.py','enemy_target_native.py')]
    paths += sorted((ROOT/'research').glob('*cases.py'))
    paths += sorted((ROOT/'research').glob('portable_*contracts.py'))
    paths += sorted((ROOT/'research').glob('verify-world*.py'))
    paths += sorted((ROOT/'scripts').glob('*cases.py'))
    paths += sorted((ROOT/'research/upstream/nikke-calc-master/data').rglob('*.json'))
    paths += sorted((ROOT/'data').glob('*.json'))
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}


def run_reference(suite,output,*,write,forbid_gpu):
    if suite not in REFERENCES:raise ValueError('Unknown native reference suite')
    output=Path(output)
    # Reserve before importing/running a case; failed evidence is never replaced.
    with output.open('x',encoding='utf-8') as stream:stream.write('{}\n')
    started=time.perf_counter()
    report=dict(schema=1,suite=suite,stage='cpu-native-contract',passed=False,cpu_reference_verified=False,calculation_verified=False,gpu_supported=False,gpu_calls=dict(build=0,execute=0),packing_calls=0,python=sys.version,platform=platform.platform(),cases=[],reference_model_gap_cases=0,positive_contract_cases=0,full_character_verified=0,full_goal_complete=False)
    try:
        # Legacy native comparators contain assertions. Reject before importing
        # or running them; optimized Python must never certify those contracts.
        if sys.flags.optimize:
            raise RuntimeError('Native reference requires assertions enabled; optimized Python is forbidden')
        sources=source_identity();report['source_sha256']=sources
        import portable_runtime,portable_backend,detail_gpu
        def no_packing(*args,**kw):raise RuntimeError('Portable packing forbidden in native contract stage')
        # Install guards before imports: aliases imported by adapters inherit them.
        with forbid_gpu(),patch.object(portable_runtime,'compile_program',no_packing),patch.object(detail_gpu,'compile_effects',no_packing),patch.object(detail_gpu,'compile_full',no_packing),patch.object(portable_runtime,'execute',portable_backend.execute),patch.object(portable_runtime,'execute_batches',portable_backend.execute_batches):
            factories,natives,contracts=[importlib.import_module(name) for name in REFERENCES[suite]]
            cases=factories.fixtures();before=copy.deepcopy(cases)
            if not cases or len({c['name'] for c in cases})!=len(cases):raise ValueError('Empty or duplicate native contracts')
            for case in cases:
                report['current_case']=case['name']
                input_hash=digest(case)
                native,trace=natives.observe(case)
                contract=contracts.verify(case,native)
                report['cases'].append(dict(name=case['name'],input_sha256=input_hash,native_sha256=digest(native),trace_sha256=digest(trace),contract=contract,native=native))
                if contract.get('verified') is not True:raise ValueError('Native contract not verified: '+case['name'])
                if contract.get('reference_model_gap') is True:report['reference_model_gap_cases']+=1
                else:report['positive_contract_cases']+=1
            if cases!=before:raise ValueError('Native observation changed literal inputs')
        if source_identity()!=sources:raise ValueError('Native reference sources changed during execution')
        from portable_typed_cuda_proof_audit import verify_cpu_gpu_calls
        verify_cpu_gpu_calls(report['gpu_calls'])
        report.update(passed=True,cpu_reference_verified=True,case_count=len(cases))
        report.pop('current_case',None)
    except BaseException as error:
        report['error']=type(error).__name__+': '+str(error)
        raise
    finally:
        report['elapsed_seconds']=time.perf_counter()-started
        write(output,report)
    return {k:report[k] for k in ('suite','stage','passed','cpu_reference_verified','calculation_verified','gpu_supported','case_count','positive_contract_cases','reference_model_gap_cases','gpu_calls','packing_calls','elapsed_seconds')}
