"""Decide only from completed exact-parity candidate measurements."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'research/portable-attack-flags-benchmark.json'
benchmark = json.loads(path.read_text())
assert benchmark['passed'] and benchmark['all_2950_input_output_bytes_equal'] and benchmark['all_additional20_health_input_output_bytes_equal']
assert benchmark['timing_order']['all_current_mac_gates_complete']
assert benchmark['timing_order']['windows_execution_and_transfer_terminal']
rows = {}
improved, worsened = [], []
for name, workload in benchmark['workloads'].items():
    control, candidate = workload['ranges']['control'], workload['ranges']['candidate']
    overlap = not (control[1] < candidate[0] or candidate[1] < control[0])
    if not overlap:
        (improved if candidate[1] < control[0] else worsened).append(name)
    rows[name] = dict(ratio=workload['candidate_to_control_ratio'], ranges_overlap=overlap,
                      ranges=workload['ranges'], median_gpu_seconds=workload['median_gpu_seconds'])
meaningful=[name for name in improved if name not in ('ordinary','conditional-hp') and benchmark['workloads'][name]['candidate_to_control_ratio']<=0.98]
selected = len(meaningful)>=2 and not worsened
decision = dict(passed=True, source_commit=benchmark['source_commit'], efficiency_evaluated=True,
                candidate='Replace the two boolean stat identity comparisons with one equivalent masked uint comparison;retain all query/lazy/recipient ordering',
                selected_for_adoption=selected, production_change_adopted=False,
                selection_rule='Predeclared:at least2 flag workloads improve by>=2percent median with nonoverlapping ranges,and no nonoverlapping regression',
                meaningful_nonoverlapping_workloads=meaningful,
                adoption_stage='Selected;optimized-source validation still required' if selected else 'Measured;keep current source',
                all_2950_input_output_bytes_equal=True,all_additional20_health_input_output_bytes_equal=True, improved_nonoverlapping_workloads=improved,
                worsened_nonoverlapping_workloads=worsened, workloads=rows,
                benchmark_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                initial_unlocalized_metal_finding_open=True,
                scope='Eight local1024-input workloads,warmup+3 samples on Apple M5;no full-roster,CUDA-speed or peak-memory claim')
(ROOT / 'research/portable-attack-flags-efficiency-decision.json').write_text(json.dumps(decision, indent=2) + '\n')
print('Selected for adoption' if selected else 'Keep current source', improved, worsened)
