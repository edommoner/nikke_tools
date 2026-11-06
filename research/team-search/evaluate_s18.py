"""S18 saved-profile ranking evaluation. Truth is used only in this evaluator.

Reuse S9's exact split, average-rank Spearman, tau-b, ceil-K and stable-ID
recall. M2 uses saved S9 weights unchanged; no refit or calibration of L2.
"""
import argparse, collections, json, math, pathlib, random, socket, statistics, time
import measure_s9 as s9
from l2_score import Score


def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def evaluate(out,fast=False):
    scorer=Score
    if fast:
        from l2_fast import Score as scorer
    started=time.perf_counter();score=scorer.load(out/'profiles.json')
    rows=s9.valid(s9.read(s9.HERE/'s9-dataset.jsonl'));random.Random(45).shuffle(rows)
    train=rows[:10000];holdout=rows[10000:12000];external=s9.valid(s9.read(s9.HERE/'s1-results.jsonl'))
    old=json.loads((s9.SCRATCH/'part-c.json').read_text())
    assert [r['id'] for r in holdout]==old['holdout_ids']
    model=json.loads((s9.SCRATCH/'models.json').read_text())['fitted']['M2']
    sets={'holdout':holdout,'all':rows,'S1-external':external}
    sets.update({f'S1-{c}':[r for r in external if r['cohort']==c] for c in 'ABC'})
    pred={};member={};prediction_seconds={}
    for label,rs in (('all',rows),('S1-external',external)):
        t=time.perf_counter();raw=[score.member_scores(r['members']) for r in rs];prediction_seconds[label]=time.perf_counter()-t
        pred[label]={r['id']:math.log(max(sum(v.values()),1.)) for r,v in zip(rs,raw)}
        member[label]={r['id']:v for r,v in zip(rs,raw)}
    def predictions(name,label,rs):
        if name=='L2':return [pred['S1-external' if label.startswith('S1') else 'all'][r['id']] for r in rs]
        if name=='M0':return [math.log(sum(s9.CHARS[n]['potential'] for n in r['members'])) for r in rs]
        return [s9.linear_predict(model,s9.slot(r['members'])) for r in rs]
    metrics={name:{label:s9.metrics(rs,predictions(name,label,rs)) for label,rs in sets.items()} for name in ('L2','M0','M2')}
    # Verify unchanged S9 prediction metrics, avoiding a silent split/model drift.
    for name in ('M0','M2'):
        for label in old['scores'][name]:
            for k in ('spearman','kendall_tau_b','rmse_log'):
                assert abs(metrics[name][label][k]-old['scores'][name][label][k])<1e-12,(name,label,k)
            assert metrics[name][label]['recall']==old['scores'][name][label]['recall']
    timed=holdout[:512];timings=[];checksum=0.
    for repeat in range(5):
        t=time.perf_counter_ns()
        for row in timed:checksum+=score(row['members'])
        timings.append((time.perf_counter_ns()-t)/len(timed))
    residual={};cases=[]
    for r in holdout:
        error=pred['all'][r['id']]-math.log(r['total_damage']);cases.append(dict(id=r['id'],members=r['members'],log_error=error,ratio=math.exp(error)))
        for n in r['members']:
            v=residual.setdefault(n,dict(n=0,absolute_log_error_contribution=0.,signed_log_error=0.))
            v['n']+=1;v['absolute_log_error_contribution']+=abs(error)/5;v['signed_log_error']+=error
    for n,v in residual.items():
        v['mean_absolute_log_error']=v['absolute_log_error_contribution']*5/v['n'];v['mean_signed_log_error']=v.pop('signed_log_error')/v['n']
        v['flags']=score.chars[n]['flags'];v['dependencies']=[d['kind'] for d in score.chars[n]['dependencies']]
    ranked=sorted(residual,key=lambda n:-residual[n]['absolute_log_error_contribution'])[:20]
    flags={}
    for flag in sorted({f for p in score.chars.values() for f in p['flags']}):
        selected=[v for v in cases if any(flag in score.chars[n]['flags'] for n in v['members'])]
        if selected:flags[flag]=dict(n=len(selected),mean_abs_log_error=statistics.mean(abs(v['log_error']) for v in selected),mean_log_error=statistics.mean(v['log_error'] for v in selected))
    stopped=metrics['L2']['holdout']['spearman']<.5
    result=dict(metrics=metrics,stop_rule_triggered=stopped,
        M5='Not run: optional learned correction; L2 remains wholly profile-based.',
        speed=dict(host=socket.gethostname(),implementation='native C++' if fast else 'pure Python',n_per_repeat=len(timed),repeats=5,ns_per_squad=timings,median_ns_per_squad=statistics.median(timings),checksum=checksum,includes='recipient selection + static burst cycle + all bucket products and dependencies',numpy='not implemented'),
        residual=dict(method='Each squad absolute log error is split equally among its five membership indicators; these are associations, not causal damage attribution.',top20=[dict(character=n,**residual[n]) for n in ranked],characters=residual,
                      largest_errors=sorted(cases,key=lambda v:-abs(v['log_error']))[:20],by_flag=flags),
        prediction_seconds=prediction_seconds,wall_seconds=time.perf_counter()-started,
        split=dict(train_n=len(train),holdout_n=len(holdout),train_ids=[r['id'] for r in train],holdout_ids=[r['id'] for r in holdout]))
    save(out/'evaluation.json',result)
    save(out/'predictions.json',dict(all=pred['all'],external=pred['S1-external']))
    print(json.dumps(dict(holdout=metrics['L2']['holdout'],stop=stopped,ns_per_squad=result['speed']['median_ns_per_squad'])))


def report(out):
    e=json.loads((out/'evaluation.json').read_text());p=json.loads((out/'profiles.json').read_text())
    runs=[json.loads(f.read_text()) for folder in (out/'runs',out/'supplement/runs') for f in sorted(folder.glob('*.json'))]
    run=json.loads((out/('run-total.json' if (out/'run-total.json').exists() else 'run.json')).read_text())
    max_res=[max(r['profile']['reconciliation'][i] for r in runs) for i in range(7)]
    counts=collections.Counter(f for v in p['characters'].values() for f in v['flags'])
    lines=['# S18: character profiles and profile-only L2 squad ranking','',
        f"L2 holdout Spearman is **{e['metrics']['L2']['holdout']['spearman']:.6f}**. " + ('The <0.5 stop rule triggered; no further elaboration or tuning was performed.' if e['stop_rule_triggered'] else 'The <0.5 stop rule did not trigger. No truth-driven tuning was performed.'),'',
        '## Profile design and reference citations','',
        'All 206 S1 characters use unchanged S1 growth, level 400, 180 s, DEF 31784, wind, core 50 px, distance 25 m, automatic burst, fixed gauge, expected mode and seed 0. Only the compute backend is CPU. No reference closure, native kernel, web or product source was edited.',
        'The primary standard squad per character uses seed 180206, puts that character first, samples four other identities uniformly, and rejects missing burst-stage coverage using `measure_s1.covered`. All S9 rows (including holdout and failures) and all S1 exact ordered squads are excluded. No damage truth participates in standard-squad selection, profile extraction or `l2_score.py`.',
        'The primary context gives burst priority to the target. Before reading ranking labels, profiles with no observed personal burst receive one second context (seed 180207), requiring literal stage 1/2/3 coverage with the upstream Red Hood automatic A→B3 exception. S9’s A-stage rule alone can admit a standard squad that never bursts. The second context replaces the first for profile arithmetic only when it observes a personal cast; both remain in evidence and build cost. There are at most two profiling squads per character. This does not estimate dormant/secondary burst behavior or general context variance. `selection.json`, `supplement/selection.json` and body files preserve every input.', '',
        '`profile_s18.ProfileLog` extends the existing `bucket_log.BucketLog`; it does not fork-copy the S17 observer. The original scalar return locals and final HitEvent objects provide the hit linkage (`bucket_log.py:43–139`). For each target, hit-kind × full-burst phase groups store count, Σ D/Π B_i, observed damage, mean own input values, mean self buckets, and the actual scalar weapon/hit flags. Groups use the first observed hit flags within a kind/phase; mixed coefficients, core probabilities and temporal covariance are approximations.',
        'Caster attribution is observed externally from original `BuffManager.get_buffs` locals. `buff_manager.py:4515–4534` builds a plan, folding permanent contributions through `_plan_step` (`4463–4513`). The return wrapper preserves each original tuple object and records its ActiveBuff caster/effect. The scoped line tracer observes numeric bucket-input deltas and crit-list deltas between actual plan steps (`4592–4703`), and special assignments for named received-damage amplification (`4728–4755`), HP-to-ATK (`4757–4776`) and caster-based ATK (`4778–4817`). It never rebuilds plans, activates buffs, resolves targets, consumes RNG, mutates carriers, or changes return objects. Existing compat wrappers are preserved; inspect.unwrap identifies the original traced code.',
        'The cache observer retains original buff dictionaries and their source maps. Scalar calls with copied dictionaries use the latest query attribution for that attacker; any mismatch appears in reconciliation. Crit probability begins at 0.15 as in `get_buffs`, and clipping/nonlinear postprocessing is measured as residual rather than attributed to the last caster.',
        'For supplied buffs, query return samples are integrated as piecewise constant until the next query for that recipient, split by the observed full-burst state. The last sample extends to battle end. The profile stores the maximum absolute recipient mean for each effect/phase and the original target encoding, so time without the effect is included. This is query-time integration, not exact activation/expiry integration; phase transitions between queries and recipient-specific conditional uptime are approximate. No differential runs were needed.', '',
        '## Targeting and dependencies','',
        'Recipient rules come from `buff_manager.py:_resolve_target_raw:5149–5388`. L2 implements self, all allies, allies excluding self, enemy debuffs, literal in-squad names, first N, adjacent (self + left then right), right N, weapon/class/code filters and caps, code+weapon leftmost, same faction squad, innate B3 and longest base charge time. Runtime final-ATK/HP rankings, random selection and buff-state/casted-state selectors are flagged and omitted as foreign supply. Final-ATK rankings cannot safely be replaced by base-ATK rankings: `_top_by` calls `_effective_atk` (`5405–5427,5518–5525`), and lazy selection snapshots at first query (`5086–5124`). The profile retains all original effects, including unobserved and unmodelled effects.',
        'Caster-based ATK is stored as recipient atk_flat plus a coefficient times the supplying character’s S1 base ATK, following `buff_manager.py:4799–4817`. Ordinary atk_pct remains a recipient-base-ATK input. Nonlinear named amplifications are part of the observed coefficient; generalizing them to new team conditions is flagged.',
        '`timeline.py:4820–4835` emits accumulated damage after source damage has already passed the seven factors, with only split_dmg added; `4839–4855` emits dealt_fixed from the triggering shot’s dealt damage. Accumulator sources are self dealt vs team received according to actual `dmg_accum_*` effects (`buff_manager.py:2622–2697`). Profiles store observed source ratios. L2 applies each ratio to predicted direct self/team damage once, not another seven-factor multiplication. Source windows, caps, shot-specific fixed-damage mix and cross-accumulator feedback are unmodelled and flagged. These are proportional approximations, not an exact replay of accumulator state.', '',
        '## Non-interference and coverage','',
        f"All **{len(runs)}/{len(runs)}** profiling bodies passed exact logged/unlogged full-payload equality, excluding no fields; saved digests match. **{sum(r['profile']['landed_hits'] for r in runs):,}** landed hits reconcile to member and squad totals. The per-body evidence retains digests, times, hit counts, query counts, attribution residuals and profiles. Baseline and logged calls each use a fresh child process.",
        'The fresh gx10 snapshot matched all files in the existing `parity_gate.cpu_sources()` closure; `transport-identity.json` records transport equality, not source-hash pins. The small Mac pilot and focused test also compare full payloads; pilots are excluded from profile-build cost. Beyond the build there are fourteen research reference executions: two original paired pilots (four calls), three paired HP-transform audit bodies (six calls), and two paired Red Hood overflow/control bodies (four calls); automated test fixture calls are separate. The first 1 s pilot initially traced the outer compat wrapper rather than the original function and had attribution residuals; unwrap identification corrected that before the remote build. Both original pilot payloads also match their plain runs.', '',
        '| Bucket | Maximum relative attributed reconstruction residual |','|---|---:|']
    for i,v in enumerate(max_res,1):lines.append(f'| f{i} | {v:.9g} |')
    audit=json.loads((out/'hp-transform-audit.json').read_text())
    lines+=['','The nonzero f2 raw reconstruction residuals include explicit intrinsic HP transforms after get_buffs: `timeline.py:4983–4996` clears atk_pct/atk_flat for max_hp_replacement or adds effective max HP × scaling_hp_pct to atk_flat. These are not missing buff-entry casters. A separate 10 s paired audit observes original effective_max_hp returns and ancestor scaling locals; its three pilots all preserve full payloads and reconstruct all seven factors with maximum residual '+str(max(max(r['corrected_max_residual']) for r in audit))+'. The replacement and additive paths were each observed; the 2B pilot is a no-transform control. Full-run table values below remain the raw aggregation residuals, not retroactively corrected audit values. Profiles flag HP scaling and postprocessed inputs; L2 does not model changes to HP caused by a new team. No differential fallback is used for these known intrinsic operations. See hp-transform-audit.json.']
    overflow=json.loads((out/'overflow-audit.json').read_text())[0]
    lines+=['','The f4 raw residual is also a known postprocessing operation: Red Hood charge-speed overflow is converted into charge damage at `buff_manager.py:4840–4847`. The active 10 s audit observes '+str(overflow['transforms'].get('charge_speed_overflow_conversion',0))+' affected scalar calls and reconstructs all factors with maximum residual '+str(max(overflow['corrected_max_residual']))+'. The original no-burst control remains in overflow-no-burst-control.json. This nonlinear self conversion is retained in measured self buckets; varying incoming charge speed is flagged and is not modelled as a foreign additive charge-damage buff.']
    lines+=['','Residual reconstruction starts from reference zero inputs + base crit + all attributed entries, then evaluates the deterministic seven expected-mode factors against actual per-hit B_i. It includes all landed direct hits in each profiling squad, not only the target. Is_element_match is copied from the actual scalar as an intrinsic combat condition. Residual measures raw attributed aggregation before known postprocessing, not numerical parity failure. The table gives a conservative maximum over the entire standard squad (including companions), not a causal residual assigned to the named target. Context-prefixed flags refer to that observation context; scaling/action/target flags come from the named character’s effects. The own baseline retains that residual, explicitly flagged, so it is not assigned to another caster.','','| Character | Attributed effect/phase entries | Differential | Flags | Max standard-squad bucket residual |','|---|---:|---|---|---:|']
    for n,v in p['characters'].items():
        flags=', '.join(v['flags']).replace('|','/')
        lines.append(f"| {n} | {v['coverage']['attributed_effects']} | no | {flags} | {max(v['coverage']['reconciliation']):.6g} |")
    lines+=['','Flag counts (a character may have several). These are conservative catalog-presence flags, including equipment/passive stats that may be inactive for the weapon. A target flag on a damage effect does not omit its observed landed damage; unsupported new-squad recipient selection omits only the associated foreign supply:','','| Flag | Characters |','|---|---:|']
    for flag,n in sorted(counts.items()):lines.append(f'| {flag} | {n} |')
    lines+=['','## Build cost and storage','',
        f"Profile build: **{run['reference_runs']} CPU reference executions** ({len(runs)} logged + {len(runs)} plain), {run['workers']} gx10 workers, **{run['wall_seconds']:.3f} s** sum of measured coordinator walls (primary {run.get('primary_wall_seconds',run['wall_seconds']):.3f} s + supplement {run.get('supplement_wall_seconds',0.):.3f} s), excluding transport, selection and the pause between runs. Summed plain simulation seconds: {sum(r['baseline_seconds'] for r in runs):.3f}; summed logged observation seconds: {sum(r['logged_seconds'] for r in runs):.3f}. Child process startup/serialization and scheduling are included in coordinator wall and per-job wall, not those inner timers. The observation overhead is substantial; this implementation does not establish cheap browser-side profile construction.",
        f"Compact `s18/profiles.json`: **{(out/'profiles.json').stat().st_size:,} bytes**, below 20 MB. Evidence total is checked below 200 MB; local and remote monitors sample every 10 s and enforce a 20.5 GiB reserve. No evidence, caches or other files were deleted."]
    for filename in ('local-storage.json','storage.json'):
        x=json.loads((out/filename).read_text());lines.append(f"`{filename}` minimum free: **{x['min_free']/1024**3:.3f} GiB**.")
    final_storage=out/'final-storage.json'
    if final_storage.exists():
        fs=json.loads(final_storage.read_text())
        lines+=['',f"Final local evidence (including the report): approximately {fs['local_evidence_bytes']/1000000:.2f} MB. Complete remote snapshot, including source/data and evidence: {fs.get('remote_snapshot_allocated_bytes',0)/1024**2:.2f} MiB allocated. Their combined size is below 200 MB. Minimum free across both remote runs: {fs['remote_min_free']/1024**3:.3f} GiB; local observed minimum: {fs['local_min_free']/1024**3:.3f} GiB. See final-storage.json."]
    lines+=['','## L2 formula, cycle and scoring speed','',
        '`l2_score.py` reads only profiles. For every attacker/kind/phase: unit = Σ D/Π B_i; predicted damage = unit × Π [measured mean self bucket + bucket(mean own raw + reaching foreign inputs) − bucket(mean own raw)]. This retains measured mean coefficients and self-factor covariance within a bucket, while foreign inputs supply arithmetic deltas. Own supply is already present and is not double counted. f2 recomputes recipient ATK%/flat/defense; f3 recomputes expected crit/core with caps; other factors use damage.py:109–367. Phase hit/unit exposure scales by predicted phase duration / observed phase duration; explicit burst-damage groups scale by predicted personal casts / observed casts. Self burst buffs and other burst-triggered bonus hits retain their observed behavior and are a known error source.',
        'Static cycle arithmetic follows `timeline.py:3415–3419,3487–3500,3579–3584,3629,3782–3792,3839–3880,3944–3970`: first gauge readiness 3 s; stage delays 0.1/0.1/0.37 s; first ordered ready candidate, earliest cooldown wait if none ready; base metadata cooldown; 10 s full burst then 2 s fixed gauge regeneration. The Red Hood A→automatic-B3 exception is copied from existing `_rebuild_burst_order`, not invented. Frame quantization, shooting controls, cooldown reductions, duration changes, stage overrides and reentry are flagged. Gauge accumulation equations do not determine the S1 cycle because S1 uses fixed gauge (`3932–3942`). This subset is a declared approximation, not the full BurstController.',
        f"Pure Python scoring on {e['speed']['host']}: median **{e['speed']['median_ns_per_squad']:,.0f} ns/squad**, five repeats × {e['speed']['n_per_repeat']} holdout squads; includes selection, cycle, bucket products and dependencies, excludes JSON loading. Repeat ns: {e['speed']['ns_per_squad']}. No NumPy implementation was added. This speed does not support the design memo’s assumed ~100 ns/squad.", '',
        '## Ranking against native detailed truth','',
        'S9 definitions and exact seed-45 successful-row split are reused through `measure_s9.metrics`: average-rank Spearman, tie-corrected Kendall tau-b, natural-log RMSE, ceil(fraction × n) shortlist sizes, stable row ID ties, top-N recall denominator min(N,n). S9 native successes are parity-verified equal to the CPU reference under these settings (prior evidence); this unit does not rerun all truth squads. M0 is unfitted potential; M2 uses unchanged saved S9 weights. All overlapping S9 report metrics are asserted equal within 1e-12. When the shortlist is smaller than N, recall cannot reach 100%; for S1-A (n=160), top-100 recall at K=20% has a 32% ceiling. “all” includes the 10,000 M2 training rows and is not an independent test. S1 A/B/C have their original distinct sampling distributions.', '',
        '| Model | Set | n | Spearman | Kendall tau-b | Log RMSE |','|---|---|---:|---:|---:|---:|']
    for model,sets in e['metrics'].items():
        for label,m in sets.items():lines.append(f"| {model} | {label} | {m['n']} | {m['spearman']:.6f} | {m['kendall_tau_b']:.6f} | {m['rmse_log']:.6f} |")
    lines+=['','| Model / set | True top-N | K=1% | K=5% | K=10% | K=20% |','|---|---:|---:|---:|---:|---:|']
    for model,sets in e['metrics'].items():
        for label,m in sets.items():
            for top,rec in m['recall'].items():lines.append(f'| {model} / {label} | {top} | '+' | '.join(f'{v:.1%}' for v in rec.values())+' |')
    lines+=['',e['M5'],'','## Residual diagnosis','',e['residual']['method'],
        'Contribution below is Σ |squad log error|/5 over holdout squads containing that character. Frequency and conditional mean errors are included; this decomposition cannot identify causal per-character truth errors because the S9 label is squad total. Flags identify mechanisms for follow-up, not proof that an effect caused an error.', '',
        '| Character | Squads | Absolute log-error contribution | Mean absolute error | Mean signed error | Effect flags |','|---|---:|---:|---:|---:|---|']
    for r in e['residual']['top20']:
        lines.append(f"| {r['character']} | {r['n']} | {r['absolute_log_error_contribution']:.4f} | {r['mean_absolute_log_error']:.4f} | {r['mean_signed_log_error']:+.4f} | {', '.join(r['flags']).replace('|','/')} |")
    lines+=['','Effect-flag associations (at least 20 holdout squads; overlapping groups, sorted by conditional mean absolute log error):','','| Effect flag | Squads | Mean absolute log error | Mean signed log error |','|---|---:|---:|---:|']
    effect_rows=[(flag,v) for flag,v in e['residual']['by_flag'].items() if v['n']>=20 and flag!='burst_cycle_dynamic_effects_unmodelled']
    for flag,v in sorted(effect_rows,key=lambda item:-item[1]['mean_abs_log_error'])[:20]:
        lines.append(f"| {flag.replace('|','/')} | {v['n']} | {v['mean_abs_log_error']:.4f} | {v['mean_log_error']:+.4f} |")
    lines+=['','Largest holdout squad errors:','','| ID | Predicted / truth | Log error | Members |','|---|---:|---:|---|']
    for r in e['residual']['largest_errors']:lines.append(f"| {r['id']} | {r['ratio']:.4f} | {r['log_error']:+.4f} | {', '.join(r['members'])} |")
    names=', '.join(r['character'] for r in e['residual']['top20'][:3])
    lines+=['','The largest membership-associated absolute-error totals are '+names+'. The effect-flag table identifies the observed classes most associated with large errors; it does not separate their causal effects from teammates, burst selection or the one-context hit-count approximation. Detailed per-member truth or controlled intervention experiments are needed for causal attribution. The saved reference effect catalogs give concrete mechanisms: Tia has cover-heal-triggered burst cooldown reduction; Anis: Star has team-conditioned cooldown/reentry and caster-based ATK transfer; Cinderella has stack-count burst bonus damage and charge-speed stacks; Scarlet: Shin Slaughter has crit-count-triggered ammo refill. L2 keeps fixed observed action counts and a static cycle. These are likely missing interactions, not a causal allocation. See each character’s effects in profiles.json, extracted from the reference manager and parsed_skills.json data.']
    lines+=['','`evaluation.json` also contains residual means/counts by every effect flag and all characters. Overlapping flags are not independent comparisons.','','## Validation, wall times and reproduction','',
        'Run from the allowed worktree with Python 3.12 (no installs):','','```sh',
        'python3.12 -B research/team-search/measure_s18.py prepare --out "$S/s18"',
        '# Fresh CPU-only gx10 snapshot; copy app/, data/, research/upstream/ and research helpers.',
        'python3.12 -B research/team-search/measure_s18.py run --out evidence --workers 20',
        'python3.12 -B research/team-search/supplement_s18.py --out "$S/s18"',
        '# Copy supplement inputs to gx10, run the same CPU runner with --out supplement, and copy results back.',
        'python3.12 -B research/team-search/measure_s18.py build --out "$S/s18"',
        'python3.12 -B research/team-search/evaluate_s18.py evaluate --out "$S/s18"',
        'python3.12 -B research/team-search/evaluate_s18.py report --out "$S/s18"','```','',
        f"Mac evaluation wall: {e['wall_seconds']:.3f} s; all-row L2 prediction {e['prediction_seconds']['all']:.3f} s, external {e['prediction_seconds']['S1-external']:.3f} s. gx10 measured wall is above. `commands.json` retains local command wall times and their exit codes; validation.json retains test exit codes. Remote run.json and run-total.json retain host/workers/wall. The copied snapshot is `~/nikke-remote/s18-20261107-v1/`. Resumption reads completed per-character files and checks their selection identity.", '',
        'Focused tests cover reference-vs-L2 bucket arithmetic, exact tiny logged/plain payload equality, attribution reconciliation, caster ATK transfer without self double counting, source-dependent bypass damage, static targeting and ordered-ready burst arithmetic. Full Python and Node acceptance results are recorded in validation.json and their logs.', '',
        '## Open issues and steps 3+','',
        'One or two observed squads cannot separate intrinsic hit cadence from teammates’ ammo/reload/charge/attack-speed effects, burst use, skill-trigger counts or team conditions. Averaging factors loses temporal covariance; first hit flags miss within-kind variations. Query-time maximum recipient means overestimate some conditional support. Dynamic top-ATK/HP and state selection is currently omitted. The static cycle ignores several large mechanics; conditional source mix and accumulator caps need event/state-aware profiles. These limitations prevent safe aggressive pruning even if global correlation is reasonable.',
        'Step 3+ needs the exact manual/auto candidate rule and cooldown/duration/reentry behavior represented explicitly, profile contexts separating used/unused burst and action-rate effects, and supported dynamic recipient selection with source attribution. Validate top-tail recall and uncertainty on fresh squads before choosing a pruning threshold. No safe upper bound or browser/WASM profile-build feasibility is established here.']
    lines+=['','Changed files: research/team-search/profile_s18.py, measure_s18.py, supplement_s18.py, diagnose_s18.py, l2_score.py, evaluate_s18.py; tests/test_team_search_l2.py; docs/team-search-design.md (S18 append only). bucket_log.py is reused unchanged. No commit or push was made.']
    validation=json.loads((out/'validation.json').read_text())
    checks=['','| Check | Result | Seconds |','|---|---|---:|']
    for label in ('python','focused','node'):
        v=validation[label];checks.append(f"| {label}: `{v['command']}` | {v['tests']} passed; exit {v['exit_code']} | {v['seconds']:.3f} |")
    checks+=['',validation['python']['note'], 'Acceptance environment: PYTHONPATH='+validation['env']['PYTHONPATH']+', NIKKE_SLANG_ROOT='+validation['env']['NIKKE_SLANG_ROOT']+', PYTHONDONTWRITEBYTECODE=1.','']
    offset=lines.index('## Open issues and steps 3+');lines[offset:offset]=checks
    (out.parent/'s18-report.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['evaluate','report']);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--fast',action='store_true',help='opt in to the built native L2 scorer');a=p.parse_args()
    evaluate(a.out,fast=a.fast) if a.action=='evaluate' else report(a.out)
