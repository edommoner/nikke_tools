"""Independent audit of completed fixed-source Mac validation; no GPU dispatch."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SOURCE='20e213bf28544a3ad2709fdc852d239eed108b5e'
PRIOR='3c3cd7d4fe3731a66587ea3577bf0496ef74a458'


def load(name):return json.loads((ROOT/'research'/(name+'.json')).read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def git_bytes(path,commit=SOURCE):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(8*1024*1024):h.update(block)
    return h.hexdigest()


def main():
    gates=load('portable-burst-charge-global-gates')
    assert gates['passed'] and gates['complete'] and len(gates['gates'])==41 and gates['source_commit']==SOURCE
    assert all(g['exit_code']==0 and g['source_commit']==SOURCE for g in gates['gates'])
    subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=ROOT,check=True)
    # Include every committed compute/input/test file, also helpers not listed
    # in the older core verifier's manually maintained validation hash list.
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',SOURCE,'--','app','scripts','gpu','tests'],cwd=ROOT,text=True).splitlines()
    complete_sources={}
    for path in paths:
        expected=sha(git_bytes(path));assert sha((ROOT/path).read_bytes())==expected,path
        complete_sources[path]=expected
    core=load('portable-combat-metal');parity=core['burst_charge_existing_parity']
    assert core['passed'] and core['gpu_execution_verified'] and core['backend']=='metal'
    assert len(core['cases'])==2835 and len(core['rejected_cases'])==496
    assert len(core['burst_charge_cpu_regressions'])==310
    assert parity['passed'] and parity['source_commit']==SOURCE and parity['compute_worktree_clean']
    assert parity['prior_inputs']==2950 and parity['current_inputs']==3331 and parity['gpu_execution_reused']
    assert parity['all_old_output_words_equal'] and not parity['changed'] and parity['no_output_normalization']
    for group in ('source_sha256','validation_sha256'):
        for path,expected in core[group].items():assert sha((ROOT/path).read_bytes())==sha(git_bytes(path))==expected,path
    for key,path in [('input_sha256',parity['input_path']),('output_sha256',parity['raw_path'])]:
        assert file_sha(path)==core[key]
    # Verify the original fresh3331 capture behind the later CPU-only replay.
    evidence=json.loads((Path(parity['replay_source'])/'evidence.json').read_text())
    assert evidence['gpu_execution_verified'] and evidence['backend']=='metal'
    for path,digest in evidence['source_sha256'].items():assert sha(git_bytes(path))==digest,path
    assert evidence['input_sha256']==core['input_sha256'] and evidence['output_sha256']==core['output_sha256']
    assert file_sha(Path(parity['replay_source'])/'readback.bin')==core['output_sha256']
    assert load('portable-burst-charge-mode-fix-existing-parity')['passed']
    roster=load('portable-roster-battles-metal')
    assert roster['passed'] and len(roster['cases'])==130 and all(c['passed'] for c in roster['cases'])
    assert len(roster['known_cpu_difference_cases'])==2
    prior=json.loads(git_bytes('research/portable-roster-battles-metal.json',PRIOR))
    lookup={(c['character'],c['grown']):c for c in roster['cases']}
    assert len(prior['cases'])==126
    for old in prior['cases']:
        current=lookup[old['character'],old['grown']]
        assert all(k=='cpu_reference_wall_seconds' or old.get(k)==current.get(k) for k in set(old)|set(current)),old['character']
    first=load('portable-burst-charge-first-roster-metal')
    assert first['passed'] and len(first['cases'])==130
    for old,current in zip(first['cases'],roster['cases']):
        assert (old['character'],old['grown'])==(current['character'],current['grown'])
        assert old['gpu_result']==current['gpu_result'] and old['native_reference']==current['native_reference']
    for batch in roster['gpu_batches']:
        for field,key in [('input_path','input_sha256'),('readback_path','output_sha256')]:
            assert file_sha(batch['captured'][field])==batch[key]
    for path,digest in roster['validation_sha256'].items():assert sha((ROOT/path).read_bytes())==digest,path
    unit={}
    for name,count in {'unit':254,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
        row=next(g for g in gates['gates'] if g['name']==name);text=Path(row['log']).read_text()
        assert f'Ran {count} tests' in text and text.rstrip().endswith('OK')
        unit[name]=dict(tests=count,output=text)
    native=load('portable-burst-charge-speed-native')
    assert native['passed'] and len(native['cases'])==310
    assert load('portable-burst-charge-firing-native')['passed']
    skill=load('portable-burst-charge-skills-native');assert skill['passed'] and len(skill['cases'])==40
    refs=load('portable-burst-reference-catalog-audit');assert refs['passed'] and refs['characters']==203
    hp=load('portable-health-runtime-metal');assert hp['passed'] and hp['gpu_execution_verified'] and len(hp['cases'])==20
    api=load('portable-api-metal');assert api['passed']
    audit=load('portable-catalog-readiness');assert audit['own_effect_preflight_passed']==65 and audit['full_character_verified']==0
    favorite=load('portable-favorite-readiness');assert favorite['passed'] and favorite['audited_contexts']==812
    report=dict(passed=True,source_commit=SOURCE,previous_proof_commit=PRIOR,all_current_gates_passed=True,
        checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),mac_gates=41,core_programs=3331,positive_cases=2835,rejections=496,
        burst_charge_native_cases=310,unit_tests=254,unit_groups=unit,real_profiles=130,native_projection_exact_profiles=128,known_native_hp_gap_profiles=2,
        prior126_profiles_preserved=True,first130_profiles_preserved=True,conditional_hp_contract_cases=20,
        complete_compute_and_test_source_sha256=complete_sources,own_effect_preflight_passed=65,unadmitted_effects=sum(audit['issues'].values()),
        favorite_preflight_contexts=favorite['own_effect_preflight_contexts_passed'],all_four_stages_preflight_characters=favorite['all_four_stages_preflight_characters'],
        full_character_verified=0,normal_ui='CPU',full_goal_complete=False,efficiency_evaluated=False,initial_unlocalized_metal_finding_open=True,
        scope='Fixed-source Mac evidence only. New API-specific burst-charge cases are not added;existing API suite is regression coverage. CUDA/transfer/efficiency are sealed separately.')
    (ROOT/'research/portable-burst-charge-broad-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('41 fixed-source Mac gates and3331 inputs sealed;full catalog certification remains0/203')


if __name__=='__main__':main()
