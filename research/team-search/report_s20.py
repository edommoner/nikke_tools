"""Assemble the S20 report from saved receipts without rescoring any squads."""
import argparse
import collections
import json
import pathlib
import re
import statistics


def load(p):
    return json.loads(p.read_text())


def run(out):
    seal=load(out/'seal.json');a=load(out/'dev/ablation.json');final=load(out/'final/final-evaluation.json')
    diagnosis=load(out/'diagnosis.json');identity=load(out/'parity/identity.json')
    p=load(out/'dev/final-profiles.json');mask=a['selected_switches']
    lines=['# S20: profile-only L2 accuracy','',
        f"Final switches: **{mask}** (action rate=1, burst mechanics=2, dynamic recipients=4, context cadence=8). Main-model parameters come only from the reference effect data and external profile observations; no detailed-truth coefficient fitting. Development selection uses S9 holdout; S1 A/B/C are reported for every candidate. Optional learned correction was not run.",'',
        'Adopted: '+', '.join(name for name,bit in [('action rate',1),('burst mechanics',2),('dynamic recipients',4),('context cadence',8)] if mask&bit)+'. Not selected: '+(', '.join(name for name,bit in [('action rate',1),('burst mechanics',2),('dynamic recipients',4),('context cadence',8)] if not mask&bit) or 'none')+'.','',
        '## Sealed fresh set','',
        f"`research/team-search/s20-sealed.jsonl`: **{seal['rows']} rows**, **{seal['native_successes']} native successes**, {len(seal['failures'])} failures with reasons in row status and `seal.json`. Seed {seal['seed']}; identical uniform ordered sampling and S1 burst coverage rule as S9, excluding every S9/S1 row including failures and every S18 standard squad.",
        f"Sealed at **{seal['sealed_at']}**. SHA-256 **{seal['sha256']}**. `s20-report.md` recorded the seal before the first L2 formula/profile change. Collector imports no L2 module. The compact file contains only id/members/total/backend/status.",
        'The versioned oracle file was created at 2026-11-06T20:56:35.945930+00:00, after sealing (`chronology.json`); the pre-final protocol/candidate ledger is retained. An exclusion audit also confirms zero overlap with saved S9 search rows and reproduces all 3,000 selections unchanged. The fresh gx10 snapshot under ~/nikke-remote/s20-20261107 matched all 923 checked CPU closure/app/GPU/data files; the pre-existing remote checkout differed in nine checked files and was not used as the source snapshot (`snapshot-identity.json`, `transport-identity.json`). These are transport identities, not source pins.',
        f"gx10 used unchanged S9 `evaluate_many(..., verification='deferred')`, 32-row batches, ten native host threads and forbidden CPU fallback. Collection wall **{seal['wall_seconds']:.3f} s**. Truth remains deferred/unverified in this unit; this is not a new CPU parity claim.",
        f"Final scoring started **{final['started_at']}**, completed **{final['completed_at']}**, once for the frozen final L2, S18 L2, M0 and M2. An exclusive `final/final-once.json` is created before scoring and prevents a repeat. No development evaluator opens the sealed rows. Final profile SHA-256 {final['profiles_sha256']}.",'',
        '## Reference mechanics and approximations','',
        '| Modelled rule | Reference citation | L2 representation / boundary |',
        '|---|---|---|',
        '| Auto stage selection and stage overrides | timeline.py:3472–3485,3782–3795,3944–3965 | Ordered ready candidate / earliest wait; structural conditions use nominal stage before overrides; no frame quantization. |',
        '| Reentry | timeline.py:3548–3584,3967–3983,4245–4255 | One extra same-stage slot per cycle, 0.5 s delay; effect-data reentry and structural-state reentry. |',
        '| Cooldown reduction | timeline.py:3641–3653,3992–4003,4135–4138; buff_manager.py:1875–1880 | Cast/start/end/squad-stage events; full-burst count thresholds; persistent full-burst-start CD supply as once-per-cycle cuts. Event-count/unknown-state triggers remain omitted. |',
        '| Trigger limits | buff_manager.py:3549–3570 | Per-rule max_trigger counter; Red Hood stage-linked cooldown cuts each occur at most once. Limited effects with multiple timing arms remain omitted because they require a shared effect counter. |',
        '| Tia cover-heal CD | timeline.py:3992–4003,3641–3653; Tia effects in profiles.json | Her own burst-triggered self cover heal supplies one cover_healed CD application. Other heals, extra stacks, expiry timing and between-cast refreshes are omitted. |',
        '| Full-burst duration | timeline.py:3586–3629 | Sum unambiguous duration effects of the B3 caster; minimum 1 s. Unknown state/stack conditions omitted. |',
        '| Team conditions / ATK transfer | buff_manager.py:2230–2250,4799–4817 | no/has other B1, same faction squad; battle-start state markers resolve structural conditions; same conditions gate foreign supply. Caster transfer uses source base ATK. |',
        '| Cast-triggered group counts | timeline.py:4942–4975,5031–5063; buff_manager.py:3583–3631,4071–4105 | Unambiguous automatic/sequential families follow personal casts even if is_burst_damage is false. Ambiguous bonus/dot families retain exposure scaling. Fixed automatic ticks are excluded from weapon-rate scaling. |',
        '| Weapon action rates | timeline.py:95–104,1600–1608,1945–1957,3142–3204,3274–3286 | Sustained rate = 1/(shot interval + empty-magazine reload time / ammo). Ammo half-up quantization, charge 0.01 s quantization, reload speed/clip refill and DOWN_Charge fire-rate floor. Compact mean-input quantization approximates per-source instantaneous rounding; MG warmup, finite boundaries, weapon swaps, fixed-time/immunity windows and refill triggers are not replayed. |',
        '| Dynamic targets | buff_manager.py:5191–5245,5318–5324,5405–5427,5518–5535 | One deterministic pass of own ATK plus static foreign ATK inputs; stable squad-order ties; top ATK, exclusions, weapon-filtered ATK, top base HP/DEF, lowest HP and below predicted DEF. HP% defaults to 100; DEF prediction uses base stats; self HP loss and DEF buff state remain approximations. No recursive target fixed point or random/state selector is invented. |',
        '| Context cadence | profile-only observations; same weapon arithmetic above | Median unit cadence across at most four distinct contexts, normalized by exposure/personal casts and received action rate. No truth calibration; the context candidate changes unit cadence, not a replay of stack or state history. |','',
        'The seven damage factors and dependency pass remain S18 arithmetic. `l2_score.py` is unchanged; `l2_score_s20.py` is the version 2 oracle. The compiler emits L2FT0002 with explicit switch bits and appended weapon/ranking/group/condition/mechanics records; L2FT0001 remains readable and numerically unchanged. C++ preserves Python 3.12 compensated sum, ordered +=, multiplication order and -ffp-contract=off. No fast-math, source pins or protected/product edits.','',
        '## Controlled diagnosis and non-interference','',
        f"**{diagnosis['payload_equalities']}/{diagnosis['reference_bodies']}** accepted paired bodies preserve the entire payload, with no excluded fields; **{diagnosis['landed_hits']:,}** landed hits reconcile. Each body uses fresh plain/logged processes. Accepted runs comprise 206 reobserved chosen S18 contexts, ten new seed-200206 contexts for the five residual targets, and five one-intervention contexts. Other characters keep one/two distinct S18 standards; those five use four. New contexts exclude S9/S1/S18 standards; control/intervention rows and exact inputs are retained.",
        'The random single/multiple-B1 contexts measure context variation, not isolated causality. The five interventions hold the other slots fixed. A replacement changes a complete teammate and can change several effects together; no independent causal percentage is claimed for individual co-occurring buffs.','',
        '| Character | Intervention | Normal hits before → after | Charge shots | Reload starts | Casts | Cycles | Full-burst s |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    failures=collections.Counter(str(r['reason'].get('failed')) for r in seal['failures'])
    insertion=['| Native failure reason | Rows |','|---|---:|']
    insertion.extend(f'| {reason} | {count} |' for reason,count in failures.items())
    insertion.append('')
    at=lines.index('## Reference mechanics and approximations')
    lines[at:at]=insertion
    for r in diagnosis['comparisons']:
        x,y=r['control'],r['intervention_result']
        cells=[f"{x[k]} → {y[k]}" for k in ('normal_hits','charge_shots','reload_starts','casts','cycles')]
        lines.append(f"| {r['character']} | {r['intervention']} | "+' | '.join(cells)+f" | {x['full_burst_seconds']:.3f} → {y['full_burst_seconds']:.3f} |")
    lines+=['','| Character | Control full-burst starts, first ≤8 (s) | Intervention starts, first ≤8 (s) |','|---|---|---|']
    for r in diagnosis['comparisons']:
        before=', '.join(f'{v:.3f}' for v in r['control']['first_full_burst_times'])
        after=', '.join(f'{v:.3f}' for v in r['intervention_result']['first_full_burst_times'])
        lines.append(f"| {r['character']} | {before} | {after} |")
    lines+=['','`diagnosis.json` also retains reload finishes, mean/min/max original weapon-method returns, instant cooldown/ammo event counts, first eight full-burst starts and per-target damage. These observations identify actual cadence/cycle changes; coarse S18 kind/phase groups cannot isolate every stack-triggered coefficient.','',
        'Tia: adding another B1 increases full-burst cycles 3→5 while her personal casts fall 6→5; weapon hits change only 121→122. The large team effect is reentry/cycle availability, not her own attack cadence. Her observed burst_reentry instants exactly match those casts.','',
        'Anis: Star: adding another B1 changes the structural branch. Observed cooldown-reduction instants fall 15→0, cycles 14→5, casts 14→6, and charge shots 197→170. This supports the conditional CDR/reentry model and shows that cycle changes also alter her charge-time/burst exposure. Her caster-ATK transfer uses the same no-other-B1 state marker.','',
        'Cinderella: replacing the first B2 with charge-speed supplier Yuni leaves charge shots 485→485, reloads 8→8 and personal casts 5→5. Her self 100% charge-speed buff and DOWN_Charge fire-rate floor explain why extra charge speed has no action-count gain here (timeline.py:863–872,1945–1957). Damage still changes because the replaced teammate supplies other effects. The every-3-s HP stacks and stack-count burst bonus are retained in effect data but are not causally separated by this intervention; their residual share cannot be identified from these squad labels.','',
        'Scarlet: Shin Slaughter: the crit supplier increases observed ammo_charge_flat instants 40→43, but normal hits remain 267 and reloads remain four. Expected crit fractions accumulate through timeline.py:1889–1891,2366–2368; the threshold is buff_manager.py:1985–1993 and ammo refill is timeline.py:4110–4120. The count evidence from this intervention does not support attributing her entire residual association to missing ammo rate. Her teammate replacement also changes team cycles 5→9.','',
        'Diesel: Winter Sweets: changing priority leaves cycles nine and normal hits 123, but casts fall 5→4 while target damage increases slightly. The first-full-burst burst_casted/burst_not_casted branches select Intro/Climax (buff_manager.py:2127–2133 plus the retained effect catalog); a fixed phase profile cannot replay that state. No fabricated stack or target rule was added to force a fit.','',
        'Observer incident: the initial pass retained 110 successful paired bodies, then stopped on an uncovered/derived hit whose scalar link was null. The action-summary loop was corrected to skip those links exactly as S18 does. Completed outputs and the failed `run.log` are retained; only unfinished bodies resumed. The initial one-row pilot preceded the final observer fields and is excluded from profile construction. Accepted reference calls total '+str(diagnosis['reference_calls'])+'; extra pilot/failed attempts are reported separately in the wall receipt.','',
        '## Every candidate and development ablation','',
        'Pre-observation pilot candidates are all retained: initial event cycle, dynamic targets, their combination (`pilot-dev.json`); structural supply-condition completeness revision (`conditioned-pilot-dev.json`); cast-triggered group count completeness revision (`cast-count-pilot-dev.json`). A final data-completeness correction honors max_trigger (the earlier pilot Red Hood cuts lacked the cap); its standalone and combined effects are in the final 16-mask ablation. No fitted constants or silent threshold sweep occurred. Final action/context candidates were evaluated once after the paired build. Objective: S9 holdout true top100 recall at K5%, then true top20 at K1%, then Spearman; lower mask breaks exact ties. All 16 combinations, including rejected ones, follow. S1-A top100 recall has shortlist-size ceilings (n=160).','',
        '| Pilot / mask | Set | Spearman | Kendall | Top20 recall K1/5/10/20 | Top100 recall K1/5/10/20 |',
        '|---|---|---:|---:|---|---|']
    for filename in ('pilot-dev.json','conditioned-pilot-dev.json','cast-count-pilot-dev.json'):
        for key,sets in load(out/filename)['metrics'].items():
            for label,m in sets.items():
                recall=lambda n:'/'.join(f'{v:.1%}' for v in m['recall'][n].values())
                lines.append(f"| {filename} / {key} | {label} | {m['spearman']:.6f} | {m['kendall_tau_b']:.6f} | {recall('20')} | {recall('100')} |")
    lines+=['','The action-rate and context switches are weaker alone, but improve the selected combination. Marginal removals below use the same saved ablation, with no new scoring or tuning.','',
        '| Holdout variant | Spearman | Top100 K5 | Top20 K1 |','|---|---:|---:|---:|']
    for label,key in [('selected',mask),*[(f'remove {name}',mask^bit) for name,bit in [('action rate',1),('burst mechanics',2),('dynamic recipients',4),('context cadence',8)] if mask&bit]]:
        m=a['metrics'][str(key)]['holdout']
        lines.append(f"| {label} (mask {key}) | {m['spearman']:.6f} | {m['recall']['100']['0.05']:.1%} | {m['recall']['20']['0.01']:.1%} |")
    lines+=['',f'All combinations other than selected mask {mask} were not adopted. Initial cycle variants were superseded by the explicitly recorded completeness revisions.','',
        '| Mask | Set | n | Spearman | Kendall tau-b | Log RMSE |',
        '|---:|---|---:|---:|---:|---:|']
    for key,sets in a['metrics'].items():
        for label,m in sets.items():lines.append(f"| {key} | {label} | {m['n']} | {m['spearman']:.6f} | {m['kendall_tau_b']:.6f} | {m['rmse_log']:.6f} |")
    lines+=['','| Mask / set | True top-N | K1% | K5% | K10% | K20% |','|---|---:|---:|---:|---:|---:|']
    for key,sets in a['metrics'].items():
        for label,m in sets.items():
            for n,r in m['recall'].items():lines.append(f'| {key} / {label} | {n} | '+' | '.join(f'{v:.1%}' for v in r.values())+' |')
    base=a['S9_dev_residual']['0']['total_absolute_log_error']
    lines+=['','## Residual shares','',
        'The following shares are measured model-ablation reductions of Σ absolute squad log error on all successful S9 dev rows (train plus holdout). They are overlapping and may be negative; they are not causal per-mechanism truth allocations. A causal allocation cannot be recovered from squad-total truth alone.','',
        '| Switch alone | Absolute log-error sum | Reduction vs mask 0 | Share of baseline residual removed |','|---|---:|---:|---:|']
    for key in (1,2,4,8,mask):
        v=a['S9_dev_residual'][str(key)]['total_absolute_log_error'];lines.append(f'| {key} | {v:.4f} | {base-v:+.4f} | {(base-v)/base:+.2%} |')
    lines+=['','| Character | S9 dev squads | Baseline associated error / 5 | Final associated error / 5 | Reduction of conditional absolute error |','|---|---:|---:|---:|---:|']
    for name in ('티아','아니스 : 스타','신데렐라','홍련 : 신살','디젤 : 윈터 스위츠'):
        b=a['S9_dev_residual']['0']['characters'][name];v=a['S9_dev_residual'][str(mask)]['characters'][name]
        lines.append(f"| {name} | {b['n']} | {b['absolute_log_error']/5:.4f} | {v['absolute_log_error']/5:.4f} | {1-v['absolute_log_error']/b['absolute_log_error']:+.2%} |")
    lines+=['','## Bit identity and S18 reproduction','',
        '| Corpus | Squads | Raw doubles per engine | Differences |','|---|---:|---:|---:|']
    for r in identity['results']:lines.append(f"| {r['label']} | {r['squads']:,} | {(r['member_values']+r['total_values']):,} | {r['differences']} |")
    count=sum(r['squads'] for r in identity['results'])
    lines += ['',f"**{count:,} squads**, **{count*6:,} raw binary64 values per engine**, **{count*18:,} comparisons across native binding, native CLI and WASM**, zero differences. This includes 218,588 version 2 squads and 258 legacy synthetic squads. All 12,000 S9 and 2,460 S1 rows, 200,000 seed-190019 distinct-member ordered random squads, and synthetic opcode/switch coverage are included. Version 1 S18 predictions remain byte-identical; metrics/residuals/split compare exactly (`frozen-s18-reproduction/comparison.json`).",'',
        '## Final sealed-set evaluation','',
        '| Model | n | Spearman | Kendall tau-b | Log RMSE |','|---|---:|---:|---:|---:|']
    for name,m in final['metrics'].items():lines.append(f"| {name} | {m['n']} | {m['spearman']:.6f} | {m['kendall_tau_b']:.6f} | {m['rmse_log']:.6f} |")
    lines+=['','| Model | True top-N | K1% | K5% | K10% | K20% |','|---|---:|---:|---:|---:|---:|']
    for name,m in final['metrics'].items():
        for n,r in m['recall'].items():lines.append(f'| {name} | {n} | '+' | '.join(f'{v:.1%}' for v in r.values())+' |')
    lines+=['','M0 is unchanged potential, M2 uses saved S9 weights without refitting. Failed native rows are excluded from metrics and retained in the sealed file. Spearman uses average ranks, Kendall is tau-b, recalls use ceil(K × n), stable ID ties and denominator min(N,n), exactly as S9. Optional per-character correction and learning curves were not run.','',
        '## Speed','',
        'All repeats are retained below. S9/family/random workloads and synchronized aggregate throughput use the corrected S19 harness. Kernel timing excludes generation/packing/checksum; coordinator wall includes them. No full output corpus is stored. Native thread and WASM worker counts are requests, not claims of identical physical cores.','',
        '| Engine | Workload | Workers | Kernel ns/squad, repeats | Coordinator wall s, repeats |','|---|---|---:|---|---|']
    bench=[json.loads(l) for l in (out/'benchmark/benchmark.jsonl').read_text().splitlines()]
    grouped=collections.defaultdict(list)
    for r in bench:grouped[(r['engine'],r['workload'],r['workers'])].append(r)
    for (engine,workload,workers),rows in grouped.items():
        lines.append(f'| {engine} | {workload} | {workers} | '+', '.join(f"{r['kernel_ns_per_squad']:.2f}" for r in rows)+' | '+', '.join(f"{r['wall_seconds']:.6f}" if 'wall_seconds' in r else 'not separately timed' for r in rows)+' |')
    med=lambda engine,workers:statistics.median(r['kernel_ns_per_squad'] for r in grouped[(engine,'random',workers)])
    lines+=['',f"10M random medians: native 1/10 threads **{med('native',1):.2f}/{med('native',10):.2f} ns/squad**; WASM 1/10 workers **{med('WASM',1):.2f}/{med('WASM',10):.2f} ns/squad**. S19 saved medians were 979.75/175.45 and 1139.92/207.69 respectively, measured in its separate run. The additional mechanics cost throughput; version 1 remains available. The ≤1 µs single-thread target and 100 ns assumption are not met by version 2."]
    lines+=['','## Acceptance, storage, walls and open issues','']
    validation=load(out/'validation.json')
    lines+=['| Check | Exit | Seconds |','|---|---:|---:|']
    for name,r in validation['results'].items():lines.append(f"| {name} | {r['exit_code']} | {r['seconds']:.3f} |")
    pytests=re.search(r'Ran (\d+) tests', (out/'python-validation-frozen.log').read_text()).group(1)
    nodetests=re.search(r'ℹ pass (\d+)', (out/'node-validation-frozen.log').read_text()).group(1)
    lines+=['',f'Frozen full suite: **{pytests} Python tests, OK**; **{nodetests} Node tests passed**, zero failures/skips. Focused S20: five tests passed.']
    lines+=['', 'Full commands and requested environment are in `validation.json`; complete stdout/stderr are retained. Focused S20 tests exercise all switch masks, raw members/totals in all engines, stable dynamic ties, reentry/CDR, max-trigger caps and nullable uncovered-hit links. The first full suite overlapped table development and failed one S20 test; its receipt/logs are retained in validation-initial.json and python-validation.log (Node passed). The first post-build dev coordinator also refused an invalid table before scoring any candidate: the new trigger-limit serialization accidentally appended a word to old recipient records. That wire bug was corrected; the complete suite was restarted after runtime/test code froze. No check or assertion was weakened.','',
        f"Accepted observation CPU seconds: plain **{diagnosis['summed_plain_seconds']:.3f}**, logged **{diagnosis['summed_logged_seconds']:.3f}**. Coordinator walls and failed/pilot overhead are in `walls.json`; native collection wall is {seal['wall_seconds']:.3f} s; dev ablation wall {a['wall_seconds']:.3f} s. Hosts: gx10 for detailed/reference observations, Mac for L2 scoring/build/parity/acceptance. No local research native detailed runs, installs, commit or push."]
    walls=load(out/'walls.json')
    lines+=['','| Host / job | Wall seconds |','|---|---:|',
        f"| gx10 sealed collection | {seal['wall_seconds']:.3f} |",
        f"| gx10 initial profile pass, failed, approximately | {walls['initial_profile_coordinator_approx_seconds']:.3f} |",
        f"| gx10 resumed profile coordinator | {walls['resumed']['wall_seconds']:.3f} |",
        f"| gx10 controlled interventions | {walls['controlled']['wall_seconds']:.3f} |",
        f"| gx10 initial pilot | {walls['pilot']['wall_seconds']:.3f} |",
        f"| Mac final dev ablation | {a['wall_seconds']:.3f} |",
        f"| Mac bit verification, sum of corpus walls | {sum(r['seconds'] for r in identity['results']):.3f} |",
        f"| Mac benchmark coordinator | {load(out/'benchmark-wall.json')['seconds']:.3f} |",'',
        'Jobs overlap; these walls must not be added as elapsed host time. The inherited S18 resume receipt counts scheduled rows, including cached rows. Actual newly accepted resumed bodies are 106; accepted total is 221 pairs plus one earlier pilot pair. Failed postprocessing attempts did not produce accepted payload receipts; their exact extra call count was not journaled by that inherited runner and remains unavailable (at least one failed pair attempt). This limitation is retained explicitly in walls.json.']
    storage=load(out/'storage-final.json')
    lines+=['',f"Local observed minimum free **{storage['local_min_free']/1024**3:.3f} GiB**, remote observed minimum **{storage['remote_min_free']/1024**3:.3f} GiB**; requested 20.5 GiB floor retained. Local evidence {storage['local_evidence_bytes']/1024**2:.3f} MiB; new remote snapshot/evidence allocation {storage['remote_allocated_bytes']/1024**2:.3f} MiB, excluding symlinked pre-existing warm caches. No pre-existing file was deleted. Only owned transient S9 native captures were cleaned after extraction.",'',
        'Remaining errors include source/time quantization lost by mean profiles, conditional self buffs and own supply when a dynamic-target owner loses eligibility, dynamic HP/DEF and target activation snapshots, crit-count ammo refill, charge/reload fixed and immunity windows, MG warmup/weapon changes, action-count CDR, independent cover-heal stacks, ambiguous bonus/dot trigger mixtures, Cinderella stack history and Diesel first-cycle state. Context medians do not replay these states. All omitted cycle effects remain in the profile. Residual association is not a causal partition. Better average correlation and finite top-tail recall do not establish a safe aggressive-pruning bound or seconds-scale exhaustive search.','',
        'Reproduce with `measure_s20.py prepare/collect`, `contexts_s20.py prepare/controlled/run`, `build_s20.py`, `evaluate_s20.py dev`, `l2_fast/verify.py --full --random 200000`, `l2_fast/benchmark.py`, and `report_s20.py --out ...`. `evaluate_s20.py final` intentionally refuses to overwrite a final-once receipt; do not rerun it on this sealed set. No product files or reference closure were edited.']
    lines+=['',f"Observed local filesystem free-space change: {storage['initial_local_free']:,} → {storage['current_local_free']:,} bytes ({storage['current_local_free']-storage['initial_local_free']:+,} bytes). No historical allocation reclamation was performed. `MONITOR_STOP` is created only after final model checks, documentation and report generation."]
    lines+=['','## Changed files and reproduction','',
        'New research files: measure_s20.py, contexts_s20.py, observe_s20.py, build_s20.py, l2_score_s20.py, evaluate_s20.py, diagnose_s20.py, report_s20.py and s20-sealed.jsonl. Backward-compatible changes: l2_compile.py and l2_fast/{l2.h,l2.cpp,cli.cpp,verify.py,benchmark.py}. New tests: tests/test_team_search_l2_s20.py. docs/team-search-design.md receives only an S20 append. S18 oracle/profile artifacts and protected product/reference files are unchanged.','',
        'From the allowed worktree, with S set to the supplied proof directory. Use fresh output directories for reruns; existing evidence is retained.','',
        '```sh',
        'python3.12 -B research/team-search/l2_fast.py build',
        'python3.12 -B research/team-search/l2_fast.py build --wasm',
        'python3.12 -B research/team-search/build_s20.py --previous "$S/s18" --contexts "$S/s20/observations" --output "$S/s20/new-profiles.json"',
        'python3.12 -B research/team-search/evaluate_s20.py dev --profiles "$S/s20/new-profiles.json" --out "$S/s20/new-dev"',
        'python3.12 -B research/team-search/l2_fast/verify.py --profiles "$S/s20/new-dev/final-profiles.json" --out "$S/s20/new-parity" --full --random 200000',
        'python3.12 -B research/team-search/l2_fast/benchmark.py --profiles "$S/s20/new-dev/final-profiles.json" --out "$S/s20/new-benchmark" --count 10000000 --repeats 3',
        'PYTHONPATH="$S/../pin-update-v1/validation-deps" NIKKE_SLANG_ROOT=/Users/edo/Documents/ChatGPT/nikke_tools/.tools/slang-2026.20-Darwin-arm64 PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s tests',
        'node --test tests/*.test.mjs',
        '```','']
    (out.parent/'s20-report.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=pathlib.Path,required=True)
    run(p.parse_args().out)
