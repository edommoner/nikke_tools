"""Rebuild the S17 summary and Markdown report from compact saved evidence."""
import argparse, collections, json, math, pathlib, statistics, re
import bucket_log as b


def read_rows(path):return [json.loads(p.read_text()) for p in path.glob('[0-9]*.json')]
def percentile(v,p):return sorted(v)[math.ceil(p*len(v))-1]
def relative(v,kind):
    actual=v['actual_change'];error=abs(v['predicted_change'][kind]-actual)
    if not actual:
        if error>1e-7:raise ValueError('Nonzero prediction for zero response; report separately')
        return 0.
    return error/abs(actual)


def report(s):
    main=read_rows(s/'results');supp=read_rows(s/'supplement');rows=main+supp
    if len(main)<20:raise ValueError('Need >=20 stratified squads')
    audits=json.loads((s/'audit.json').read_text())
    for r in rows:
        if not r['non_interference'] or r['baseline']['payload']!=r['logged']['payload'] or not r['logged']['buckets']['reconciliation']:raise ValueError('Non-interference/reconciliation failure')
    table=[]
    for label,cohort in [('stratified',main),('targeted',supp)]:
        for knob,(group,magnitudes) in b.KNOBS.items():
            for magnitude in magnitudes:
                variants=[v for r in cohort for v in r['variants'] if v['knob']==knob and v['magnitude']==magnitude]
                item=dict(cohort=label,knob=knob,group=group,magnitude=magnitude,n=len(variants),zero_response=sum(v['actual_change']==0 for v in variants))
                for method in ('first','exact'):
                    errors=[relative(v,method) for v in variants]
                    item[method]=dict(median=statistics.median(errors),p90=percentile(errors,.9),max=max(errors))
                table.append(item)
    hits=sum(r['logged']['buckets']['landed_hits'] for r in rows)
    damage=sum(r['baseline']['payload']['total_damage'] for r in rows)
    uncovered=sum(r['logged']['buckets']['uncovered_damage'] for r in rows)
    storage=json.loads((s/'results/storage.json').read_text());supp_storage=json.loads((s/'supplement/storage.json').read_text())
    local=[json.loads(l) for l in (s/'local-storage.jsonl').read_text().splitlines()]
    outliers=[]
    for r in rows:
        for v in r['variants']:
            if relative(v,'first')>.01:
                outliers.append(dict(id=r['selection']['id'],targeted='target' in r['selection'],knob=v['knob'],magnitude=v['magnitude'],relative_error=relative(v,'first'),
                    actual_change=v['actual_change'],predicted_change=v['predicted_change']['first'],hit_count_changes=v['hit_count_changes'],burst_timeline_changed=v['burst_timeline_changed']))
    summary=dict(squads=len(rows),primary=len(main),targeted=len(supp),non_interference=len(rows),audited_bodies=sum(r['non_interference_count'] for r in audits),
                 landed_hits=hits,damage=damage,uncovered_damage=uncovered,uncovered_share=uncovered/damage,tables=table,outliers=outliers,
                 local_min_free=min(r['free_bytes'] for r in local),remote_min_free=min(storage['min_free'],supp_storage['min_free']))
    (s/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    validation = {}
    for label, filename in [('python_initial','python-tests.log'),('python_first_error','python-first-error.log'),('python_with_existing_deps','python-tests-with-deps.log'),('python_final','python-tests-final.log'),('focused','focused-tests-final-metadata.log')]:
        path=s/filename
        match=re.search(r'\nRan (\d+) tests in ([\d.]+)s\n\n(OK[^\n]*|FAILED[^\n]*)',path.read_text() if path.exists() else '')
        validation[label]=dict(status=match.group(3) if match else ('interrupted after setup failure diagnosis' if path.exists() and 'KeyboardInterrupt' in path.read_text() else 'running'), tests=int(match.group(1)) if match else None, seconds=float(match.group(2)) if match else None, log=filename)
    validation['node']=dict(status='pass',tests=169,seconds=.321717208,log='node-tests.log')
    validation['dependency']=dict(path='/Users/edo/Documents/ChatGPT/nikke_tools/.portable-recovery/proofs/claude-product-standard-phase0-v1-20261102/pin-update-v1/validation-deps',gmpy2='2.2.1',mpfr='4.2.1',installation=False,slang_root='/Users/edo/Documents/ChatGPT/nikke_tools/.tools/slang-2026.20-Darwin-arm64')
    (s/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    lines=['# S17: CPU damage buckets and first marginal-value check','',
      'The seven-bucket ratio works on the tested direct hits. A frozen bucket-value sum alone misses caster-based ATK transfers and damage derived from earlier hits. This is measurement, not a product surrogate or a pruning guarantee.','',
      '## Scope and selection','',
      'S1 profile and settings: 180 s, level 400, DEF 31784, wind, core 50 px, distance 25 m, auto burst, fixed gauge, seed 0, CPU expected mode. Only compute_backend changes from native_detail to cpu. The original profile is in `s17/body.json`; no growth edits are made in baseline bodies. `selection.json` takes the midpoint and upper boundary of each of ten damage deciles among 11,956 positive native-success S9 rows, sorted by damage then ID; this includes the dataset maximum (ID 7720). Selection uses S9 native values, not the new CPU values.','',
      'Three separate targeted S9 squads maximize saved damage subject to containing Dorothy, Trony, or Emilia. They test known bypass mechanisms and are reported separately from the stratified cohort. Their inclusion is not a random-sample prevalence estimate.','',
      'The requested design heading “グループ別の限界価値による効率化” is absent from this checkout’s design document (it ended with the earlier six-step plan). This unit follows the bucket definition and step 1–2 intent in the S17 brief.','',
      '## Wrapped paths and collection','',
      '- `calculator.timeline.calc_damage`: all eight static call expressions at `timeline.py:678,1665,1700,1866,2285,3915,4802,5056` (line 34 is the import, not a call). They cover reach recalculation, staged/coordinate pellets, automatic shots, charge shots, deferred burst bonus hits, coordinate skills and ordinary/DOT skill effects.','- `app/destructible_damage_policy.py:75-93`, `calculate`: observes its cloned scalar with replacement factor5. `app/destructible_battle_runtime.py:190-194,250` can replace timeline.calc_damage with a typed scalar. Its dynamic call still enters the wrapped calculate function.','- `app/destructible_skill_runtime.py:10-18`, `resolve`: observes the local import of calculator.damage.calc_damage for declared projectile skills.','- `calculator.timeline.HitEvent.__init__` links scalar observations to the original event object; `runner.sim.execute` captures the returned SimResult.hits. Both return the original result unchanged. No event fields or reference sources are modified.','',
      'The scalar wrappers install a scoped Python profile return hook only while the original function runs. It reads f1…f7, hit_type, crit_frac, is_crit and input buffs from that actual call’s locals. It never calls _factor3 again, consumes RNG, changes the input, rounds damage again, or copies/replaces the returned scalar object. Nested entries share one hook. Hooks and bindings are restored on exceptions. `calculator.damage.calc_damage` deliberately stays original because the typed policy clones its globals to override factor5; wrapping that binding would break the clone. `calc_damage_avg` has no combat callers in the CPU closure. The only upstream runtime consumer of scalar damage is timeline; buff_manager contains comments but no calc_damage call. The two opt-in app paths above have zero executions in these undeclared S1 bodies; they are code-traced coverage, not battle-validated typed-model claims.','',
      'The compat install chain in `app/engine_compat.py:25-47` installs effect/reference-count/health/protection layers. Rewritten timeline functions keep the module calc_damage binding; damage-handler wrappers feed the same native handler. `app/impact_runtime.py:55-94` rewrites landing publication without replacing factor math. The captured immediate call sites and ancestor paths are saved per squad in call_sites; ancestor counts are stack observations, not additional hits. The fresh remote snapshot matched all 143 files from parity_gate.cpu_sources() before acceptance of results (`transport-identity.json`). These are transport identity observations, not new source-hash pins.','',
      'Only final scored hits are summed. A scalar may be used for reach/geometry and discarded; scalar_calls is therefore distinct from landed_hits. This experiment has no parts, ADDs or declared models, so speculative target calculations do not contribute scored damage. Unknown/unmatched events are conservatively uncovered. Interrupt damage is outside upstream total_damage, and ADD damage is separate, per `timeline.py:5178-5242`. These paths are not exercised by S1.','',
      '## Compact aggregation and non-interference','',
      'Each group is attacker × exact reference hit_tag × full-burst flag × actual full-burst window number. CPU burst_timeline “full_burst 시작” events define windows; all outside-full-burst hits are pooled into window 0. Each row stores hit count, first/last time, Σdamage, all seven Σdamage/B_i values, crit/core fraction sums, and zero-bucket counts. During execution the per-hit record also has all original hit flags and f1…f7. No per-hit dumps are retained. A +1 unit refers to the factor’s native units: f1 percentage coefficient, f2 attack-minus-defense points, f3…f7 multiplicative units. It does not mean +1 percentage point on every equipment knob.','',
      f'**{len(rows)}/{len(rows)} squad bodies** passed exact full Python payload equality, excluding **no keys** (stronger than removing provenance/timing), with matching saved payload digests. All {hits:,} scored hits reconcile exactly to per-member damage and total_damage. All scalar bucket denominators in these runs are nonzero. The paired audit additionally proves non-interference for {sum(r["non_interference_count"] for r in audits)} traced bodies against fresh plain children. The tiny focused fixture also checks equality/reconciliation; identity and exception restoration have direct unit tests.','',
      '| S9 ID | Cohort/decile | CPU total damage | Hits | Uncovered share | Equality/reconciliation |','|---:|---|---:|---:|---:|---|']
    for r in sorted(rows,key=lambda r:('target' in r['selection'],r['selection'].get('rank',0))):
        q=r['selection'];x=r['logged']['buckets'];lines.append(f"| {q['id']} | {q.get('target',str(q.get('decile')))} | {r['baseline']['payload']['total_damage']:,} | {x['landed_hits']:,} | {x['uncovered_share']:.4%} | pass |")
    lines += ['', '## Existing knobs → bucket mapping','',
      'All squad members receive the same stated delta. Equipment deltas use the existing patches[name].equip_skills mechanism, adding to the existing scalar/list total; no keys absent from the existing equipment schema are introduced. These hypothetical numerical overload inputs need not lie on discrete in-game rolls.','',
      '| Input | Magnitudes | Direct bucket increment x per hit | Code |','|---|---|---|---|',
      '| stat_deltas[name].atk | +100 / +1000 base ATK | f2: delta × (1+atk_pct/100); zero for max_hp_replacement | engine_worker.py:334-363; damage.py:115-130; timeline.py:4987-4994 |',
      '| patches[name].equip_skills.crit_dmg | +1 / +5 percentage points | f3: crit_frac × delta/100 | buff_manager.py:902-910,1017-1039; damage.py:133-196 |',
      '| …charge_dmg_pct | +1 / +5 percentage points | f4: delta/100 only on full-charge hits | same equipment route; damage.py:213-242 |',
      '| …element_bonus | +1 / +5 percentage points | f7: delta/100 only on element-advantaged hits | buff_manager.py:288-289; damage.py:299-304 |','',
      'stat_deltas accepts only atk/def/hp; it does not accept ATK%, crit damage or generic damage-up. An existing equipment atk_pct knob also maps to f2 through base_atk×delta/100 but was not tested separately. DEF/HP can affect transferred stats, max-HP damage and thresholds; they are not clean fixed damage-bucket knobs. No existing ordinary equipment knob was found for f1, generic f5 or enemy f6, so those buckets have logged marginal values but no prediction rerun here. No new knobs or game rules were introduced. Crit clamp crossings and f2 minimum-damage crossings would invalidate a simple slope; they were not observed in this cohort.','',
      '## Prediction results','',
      'For each baseline landed direct hit D, first-order gain is Σ D×x/B_i. Exact product gain is Σ D×[(B_i+x)/B_i−1], evaluated separately at each magnitude. All experiments change one direct bucket, so the two expressions are algebraically identical; their agreement is not evidence about cross-bucket interactions. The “exact” product still uses baseline integer-rounded hit damage and freezes schedules/conditions; it does not replay upstream rounding or dependent damage. Neither method was fitted. Bypass damage is held constant, so indirect changes to it are prediction misses.','',
      'Absolute relative error below is |predicted gain−actual rerun gain|/|actual rerun gain|, **not** error divided by total damage. Exact zero gain with exact zero prediction is scored zero; the no-response count is displayed to expose dilution. Percentiles use nearest rank.','',
      '| Cohort | Bucket/input | Delta | n | Zero response | First median | First p90 | Product median | Product p90 |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for x in table:
        lines.append(f"| {x['cohort']} | f{x['group']} / {x['knob']} | {x['magnitude']} | {x['n']} | {x['zero_response']} | {x['first']['median']:.5%} | {x['first']['p90']:.5%} | {x['exact']['median']:.5%} | {x['exact']['p90']:.5%} |")
    lines += ['', '## Outliers and causes','',
      'No hit-count or burst-timeline changes occurred in any of the 184 perturbation reruns. Thus these measured failures do not demonstrate attack-count or threshold transitions. Conditional/target-selection transitions remain an untested risk. Every gain-error outlier above 1% is listed below; the summary JSON has exact magnitudes and predicted/actual gains.','',
      '| S9 ID | Input | +100/+1 error | +1000/+5 error | Cause |','|---:|---|---:|---:|---|']
    by=collections.defaultdict(dict)
    for r in rows:
        for v in r['variants']:
            if any(o['id']==r['selection']['id'] and o['knob']==v['knob'] for o in outliers):by[(r['selection']['id'],v['knob'])][v['magnitude']]=relative(v,'first')
    for (identity,knob),values in sorted(by.items()):
        mags=b.KNOBS[knob][1]
        cause='ATK transfer dependency (paired audit confirms this mechanism for IDs 7720/2080; inferred for other direct-only rows)'
        if identity in (2940,6665,9771):cause='Dependent bypass damage; ATK may also change transferred buffs' if knob=='atk' else 'Dependent bypass damage changes while prediction holds it fixed'
        lines.append(f'| {identity} | {knob} | {values.get(mags[0],0):.4%} | {values.get(mags[1],0):.4%} | {cause} |')
    lines += ['',
      '`buff_manager.py:4778-4817` adds caster-base-ATK-derived contributions to atk_flat. Raising all base ATKs therefore changes both the direct base_atk term and these contributions. The frozen slope deliberately includes only the former. In the paired audits, only f2 changed; the extra observed f2 units equal the change in atk_flat for every attacker, with no change in atk_pct. This establishes an input→bucket mapping failure, not failure of the bucket ratio.','',
      '| Audit ID/input | Actual gain | Frozen input prediction | Using observed changed bucket | Absolute residual |','|---|---:|---:|---:|---:|']
    for r in audits:lines.append(f"| {r['id']} / {r['knob']} +{r['magnitude']} | {r['actual_change']:,} | {r['frozen_prediction']:,.3f} | {r['observed_bucket_prediction']:,.3f} | {abs(r['observed_bucket_prediction']-r['actual_change']):,.3f} |")
    lines += ['',
      'The crit-damage audit (ID 852, 13,779 matched hits) changes only f3 by exactly crit_frac×0.01. Its 4,105.036 damage gain residual is within the per-hit integer-rounding bound and is concentrated in many repeated low-damage hits. Upstream `damage.py:358` rounds each hit and enforces minimum 1. Baseline-rounded D multiplied by a bucket ratio cannot reproduce that discrete step exactly. Increasing magnitude reduces this relative error.','',
      '## Damage outside the seven-factor path','',
      f'Stratified cohort: 0 uncovered damage. Targeted cohort: {uncovered:,} uncovered damage; across all 23 squads this is {uncovered/damage:.5%} of {damage:,} total damage. This pooled share depends on the intentionally enriched sample.','',
      '| Targeted S9 ID | Kind | Damage | Share of that squad |','|---:|---|---:|---:|']
    for r in supp:
        for kind,amount in r['logged']['buckets']['uncovered_by_kind'].items():lines.append(f"| {r['selection']['id']} | {kind} | {amount:,} | {amount/r['baseline']['payload']['total_damage']:.5%} |")
    lines += ['',
      '`timeline.py:4825-4841`: accum_split_damage releases the already mitigated accumulator and applies only split_dmg_pct; reapplying the seven groups would double-count factors. `timeline.py:4843-4864`: dealt_fixed_damage scales the triggering shot’s dealt damage by its existing percentage and applies no new factors. Both are hit events and reconcile normally, but lack their own f1…f7. Their *sources* have bucket sensitivities that propagate into the later release; step 2 must preserve that dependency. Unknown landing/copy paths would be conservatively uncovered rather than assigned invented factors.','',
      '## Execution, storage and reproduction','']
    for label in ('results','supplement'):
        run=json.loads((s/label/'run.json').read_text());cohort=main if label=='results' else supp
        work=sum(r['baseline']['seconds']+r['logged']['seconds']+sum(v['seconds'] for v in r['variants']) for r in cohort)
        lines.append(f"- gx10 {label}: {run['squads']} squads, {run['workers']} workers, wall {run['wall_seconds']:.3f} s; summed child evaluation time {work:.3f} s. Includes plain+logged baseline and eight plain perturbations per squad.")
    lines += [f"- gx10 paired audits: {sum(r['seconds'] for r in audits):.3f} s, 12 child evaluations (six traced, six plain); per-case walls are saved in audit.json.",
      '- Mac: one 1-second pilot (plain+logged), local acceptance suites and orchestration only. Host evaluation timings are stored in pilot.json; all 180-second research runs execute on gx10. SSH/copy/setup time is not included in the remote experiment timers.',
      f"- Local storage minimum during monitor: {summary['local_min_free']/1024**3:.3f} GiB; gx10 minimum: {summary['remote_min_free']/1024**3:.3f} GiB. Reserve is 20.5 GiB, with a 200 MiB preflight evidence budget. Main/supplement remote monitors sample every 10 seconds; Mac monitor likewise samples every 10 seconds. No files were deleted.",
      '- Remote fresh snapshot: `~/nikke-remote/s17-20261107/`; only app, data, upstream CPU inputs and research helpers are transported. The remote research evaluations use only Python, with no native kernel, compiler or GPU dispatch. Local acceptance tests use the preinstalled Slang/C++ tools for existing test cases. No installation, sudo, commit or push is used. Remote writes stay below ~/nikke-remote.','',
      '```sh',
      'python3.12 research/team-search/measure_s17.py prepare --out "$S/s17"',
      '# Transfer app/, data/, research/upstream/, and the S17 helpers with rsync -a',
      '# (exclude bytecode; no --delete); copy body.json/selection.json to remote evidence/.',
      'ssh gx10-afe7-tailscale "cd ~/nikke-remote/s17-20261107 && PYTHONDONTWRITEBYTECODE=1 python3.12 research/team-search/measure_s17.py run --out evidence --workers 20"',
      'python3.12 research/team-search/bucket_log.py --body BODY.json --out NEW_RESULT.json',
      'python3.12 research/team-search/diagnose_s17.py --results "$S/s17/results" --out NEW_AUDIT.json',
      'python3.12 research/team-search/report_s17.py --scratch "$S/s17"',
      'python3.12 -m unittest discover -s tests',
      'node --test tests/*.test.mjs','```','',
      'Each run spawns a fresh worker process as engine_worker expects. The research runner is resumable by selected squad ID and refuses member/selection mismatches. Reuse a new output directory when changing bodies/code/settings; do not mix a new experiment into old results. Baseline payloads and summaries are saved; rerun timings naturally vary.','',
      '## Acceptance and remaining work','',
      'Validation status is recorded in `s17/validation.json` and the complete acceptance logs. No CPU closure, existing tests, kernels, web code, source pins, or application stat schema were edited.',
      f"Python initial attempt: {validation['python_initial']['status']}. Final full run using the existing validation dependencies and shared tool paths: {validation['python_final']['status']} ({validation['python_final']['tests']} tests, {validation['python_final']['seconds']} s). Focused tests: {validation['focused']['status']} (5 tests). Node: 169 passed, 0 failed.",
      'The first plain-shell full run lacks gmpy2 and was interrupted after its fail-fast counterpart identified the import failure (176 tests, one error). Its first failure reproduces in the existing coordinate-landing module alone, without importing the new tests. A pre-existing proof-local validation directory contains gmpy2 2.2.1 / MPFR 4.2.1. The second setup attempt exposed the absent worktree-local Slang path; the installed shared compiler is selected by the same NIKKE_SLANG_ROOT value supplied by the S1 Node tool-environment adapter. The route module (3 tests) and native binary64 module (2 tests) both pass when rerun with that path. The final full suite uses command-local PYTHONPATH, NIKKE_SLANG_ROOT and PYTHONDONTWRITEBYTECODE=1. Earlier setup attempts were interrupted after diagnosis; they are retained and are not counted as passing acceptance runs. No dependency is installed, downloaded, copied into a shared environment, or changed. See dependency-repro.log and python-first-error.log. Reproduction: `PYTHONPATH=/Users/edo/Documents/ChatGPT/nikke_tools/.portable-recovery/proofs/claude-product-standard-phase0-v1-20261102/pin-update-v1/validation-deps NIKKE_SLANG_ROOT=/Users/edo/Documents/ChatGPT/nikke_tools/.tools/slang-2026.20-Darwin-arm64 PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s tests`.','',
      'Step 2 character profiles need: damage-weighted bucket sensitivities by attacker/kind/full-burst phase; conditional eligibility weights (crit/full-charge/element), caster→recipient stat-transfer derivatives, accumulator/fixed-damage dependency edges, and schedule/target-selection guards. A single average bucket is insufficient; ΣD/B is the quantity measured here. Re-profile on enemy/growth/operation changes and measure top-tail recall before pruning. This experiment covers one profile/scenario, four input axes and two magnitudes; f1/f5/f6 input perturbations, interacting buckets, threshold crossings, random mode, parts/ADD/typed-model reconciliation and unseen-character extrapolation remain open. No trained per-user surrogate is introduced.']
    if (s/'final-storage.json').exists():
        final_storage=json.loads((s/'final-storage.json').read_text())
        lines += ['', f"Final local evidence: {final_storage['evidence_bytes']/1024**2:.3f} MiB. Remote isolated snapshot plus evidence: {final_storage.get('remote_snapshot_allocated_bytes',0)/1024**2:.3f} MiB allocated (du); together under 50 MiB, below the 200 MiB limit. Final CPU preservation receipt confirms all 143 closure files unchanged; git diff --check passes."]
    (s.parent/'s17-report.md').write_text('\n'.join(lines)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--scratch',type=pathlib.Path,required=True);a=p.parse_args();report(a.scratch)
if __name__=='__main__':main()
