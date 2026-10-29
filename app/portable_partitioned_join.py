"""Join the pinned source-host CUDA envelope and fresh Mac native witness.

No unseen CUDA raw is relabelled as a Mac capture. Proofs retain their original
claims and their independent process/environment preservation outcomes.
"""
import json
from pathlib import Path

WITNESS_SHA='040673e705e0a16e55677eafe8758c94e8a0cbefc16426b9077c13a8c82f7f87'
ENVELOPE_SHA='6648e2c8df64cd8666898399ab7ca9c0f31fd20a42dfdefcc7e5018abcaad3d1'


def validate(manifest,witness,groups,envelope,native_cases):
    from portable_comparison_groups import validate_facts
    if (witness.get('schema')!='partitioned-identical-wire-native-witness-v1'
        or witness.get('package_id')!=manifest['package_id']
        or envelope.get('schema')!='partitioned-current-saved-envelope-v1'
        or witness.get('source_package_id')!=envelope.get('source_package_id')
        or witness.get('original_cuda_capture_observed') is not False
        or any(witness.get(k) is not True for k in ('witness_calculation_verified','conditional_cuda_native_equivalence_verified','pending_original_cuda_envelope_audit'))
        or witness.get('calculation_verified') is not False):raise ValueError('Separate native witness and original CUDA envelope required')
    for key in ('original_capture_observed','original_containment_verified','original_process_preserved',
        'original_sequence_arguments_verified','paired_generation_verified','audit_passed','audit_containment_verified','audit_process_preserved'):
        if envelope.get(key) is not True:raise ValueError('Incomplete source-host envelope: '+key)
    for key in ('original_claims_modified','calculation_verified','audit_timed_out','full_goal_complete','public_gpu_admitted'):
        if envelope.get(key) is not False:raise ValueError('Original proof scope changed: '+key)
    for key in ('fresh_native_calls','gpu_calls','compiler_calls','audit_exit_code','audit_job_post_members'):
        if type(envelope.get(key)) is not int or envelope[key]!=0:raise ValueError('Invalid bounded CPU envelope: '+key)
    g=manifest['golden'];c=witness['comparison'];facts=c['independent_comparison'];count=len(g['entries'])
    validate_facts(facts,count,180)
    if (c.get('calculation_verified') is not True or c.get('entries')!=g['entries']
        or c.get('input_count')!=count or c.get('native_oracles')!=native_cases or facts.get('native_cases')!=native_cases
        or c.get('input_sha256')!=g['input_sha256'] or c.get('logical_output_sha256')!=g['output_sha256']
        or envelope.get('input_count')!=count or envelope.get('native_reference_cases')!=native_cases
        or envelope.get('readback_cases')!=count or envelope.get('launch_calls')!=len(witness['wire']['metal_cache_checks'])
        or any(envelope.get(k)!=c.get(k) for k in ('input_sha256','raw_output_sha256','logical_output_sha256'))
        or envelope.get('output_bytes')!=witness['wire']['output_bytes']
        or len(groups)!=len(facts['groups'])):raise ValueError('Entire input, native and wire corpus must agree')
    entries=[]
    for row,fact in zip(groups,facts['groups'],strict=True):
        indices=fact['case_indices']
        if (row.get('calculation_verified') is not False or row.get('comparison_subset_verified') is not True
            or row.get('case_indices')!=indices or row.get('child_pid')!=fact['child_pid']
            or type(row.get('elapsed_seconds')) not in (int,float) or row.get('elapsed_seconds')!=fact['elapsed_seconds'] or row.get('input_count')!=len(indices)
            or row.get('total_input_count')!=count or type(row.get('native_oracles')) is not int or row.get('native_oracles')!=fact['native_cases']
            or row.get('entries')!=[g['entries'][i] for i in indices] or row.get('mismatches')!=[]
            or row.get('generated_normalized')!=g['generated_normalized']
            or any(row.get(k)!=c[k] for k in ('input_sha256','raw_output_sha256','logical_output_sha256'))
            or row.get('live_parent_receipt_present') is not False or type(row.get('gpu_calls')) is not int or row['gpu_calls']!=0):
            raise ValueError('Every original fresh native/rejection group must agree')
        entries.extend(row['entries'])
    if entries!=g['entries']:raise ValueError('Missing or reordered native comparisons')
    return True


def run(cli,witness_package,witness_audit,envelope_summary,out):
    from portable_continuation_package import owner_snapshot
    from portable_partitioned_addresses import check_source,view_file,WORDS
    from portable_staged_preflight import outside,exclusive
    witness_package=Path(witness_package).resolve();witness_audit=Path(witness_audit).resolve();envelope_summary=Path(envelope_summary).resolve()
    out=outside(out,[cli.ROOT,witness_package,witness_audit,envelope_summary])
    if out.exists():raise FileExistsError(out)
    with cli.forbid_gpu():
        raw=(witness_audit/'result.json').read_bytes();peer=envelope_summary.read_bytes()
        if cli.sha(raw)!=WITNESS_SHA or cli.sha(peer)!=ENVELOPE_SHA:raise ValueError('Exact reviewed native/envelope proof bytes required')
        witness=json.loads(raw);envelope=json.loads(peer);info=owner_snapshot(cli,witness_package);m=info['manifest']
        context=cli.load(witness_audit/'context.json');plan=cli.load(witness_audit/'plan.json')
        if (context['package_id']!=m['package_id'] or context['source_package_id']!=witness['source_package_id']
            or context['anchors']!=witness['anchors'] or plan['per_group_timeout_seconds']!=180
            or plan['case_groups']!=[g['case_indices'] for g in witness['comparison']['independent_comparison']['groups']]):
            raise ValueError('Original native audit context/plan changed')
        groups=[cli.load(witness_audit/(str(i)+'.json')) for i in range(len(plan['case_groups']))]
        validate(m,witness,groups,envelope,info['config']['native'])
        for anchor in witness['anchors']:cli.check_records(Path(anchor['root']),anchor['records'])
        check_source(witness_package,info['config']['source'],WORDS)
        capture=Path(context['witness_capture']);layout=cli.load(capture/'readback.bin.batches/plan.json')
        view=view_file(capture/'readback.bin.partial',layout,m['golden']['entries'])
        if any(view[k]!=witness['wire'][k] for k in ('profile','raw_joined_output_sha256','logical_view_sha256',
            'active_references_checked','logical_address_changes','input_count','raw_gpu_bytes_modified','numeric_words_modified')):
            raise ValueError('Native witness raw changed after fresh comparison')
        if owner_snapshot(cli,witness_package)!=info:raise ValueError('Native witness owner changed during join')
        result=dict(schema='partitioned-current-cuda-native-join-v1',source_package_id=witness['source_package_id'],
            witness_package_id=m['package_id'],envelope_auditor_package_id=envelope['auditor_package_id'],
            input_count=len(m['golden']['entries']),native_cases=info['config']['native'],rejection_cases=len(m['golden']['entries'])-info['config']['native'],
            independent_native_groups=len(groups),input_sha256=envelope['input_sha256'],
            raw_output_sha256=envelope['raw_output_sha256'],logical_output_sha256=envelope['logical_output_sha256'],
            cubin_sha256=envelope['cubin_sha256'],witness_proof_sha256=WITNESS_SHA,envelope_proof_sha256=ENVELOPE_SHA,
            source_host_cuda_envelope_independently_audited=True,cuda_envelope_received_as_peer_summary=True,
            original_cuda_raw_read_on_mac=False,metal_witness_native_independently_verified=True,
            source_host_process_preserved=True,environment_preservation_verified=envelope['original_environment_preservation_verified'],
            audit_environment_preservation_verified=envelope['audit_preservation_verified'],
            calculation_verified=True,overall_stage_passed=False,original_claims_modified=False,
            gpu_calls=0,compiler_calls=0,fresh_native_calls_during_join=0,
            full_goal_complete=False,public_gpu_admitted=False,
            scope='Entire frozen 106-input corpus. Source-host CUDA bytes and trace via pinned peer report; fresh native semantics on byte-identical Metal witness. No whole-character/public admission.')
        exclusive(out,result);return result
