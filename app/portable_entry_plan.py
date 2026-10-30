"""Rank saved static blockers by distinct profiles without rerunning preparation."""
import copy,hashlib,json
from pathlib import Path

def projected_suites(value):
    found={}
    def visit(v):
        if isinstance(v,dict):
            if isinstance(v.get('suite'),str):
                row={k:v[k] for k in ('suite','inputs','native_cases','cases','metal_verified','cuda_verified','independently_audited','scope') if k in v}
                found[json.dumps(row,sort_keys=True)]=row
            for child in v.values():visit(child)
        elif isinstance(v,list):
            for child in v:visit(child)
    visit(value);return sorted(found.values(),key=lambda r:(r['suite'],json.dumps(r,sort_keys=True)))

def compare_entries(before,after):
    """Compare entry guards only when every original profile and wire is identical."""
    for report in (before,after):plan(report)
    if before.get('input_policy')!=after.get('input_policy'):raise ValueError('Entry comparison requires the same input policy')
    key=lambda row:(row['character'],row['favorite_stage'])
    left={key(row):row for row in before['profiles']};right={key(row):row for row in after['profiles']}
    if left.keys()!=right.keys():raise ValueError('Entry comparison requires the same complete profile selection')
    changes=[];packed=0
    for identity,row in left.items():
        other=right[identity]
        if row['original_definitions_sha256']!=other['original_definitions_sha256'] or row['input_packed']!=other['input_packed']:
            raise ValueError('Entry comparison changed original definitions or packing')
        if not row['input_packed']:continue
        for field in ('input_sha256','input_words'):
            if field not in row or row[field]!=other.get(field):raise ValueError('Entry comparison changed packed input')
        if not isinstance(row['input_sha256'],str) or len(row['input_sha256'])!=64 or any(c not in '0123456789abcdef' for c in row['input_sha256']):raise ValueError('Entry comparison requires a packed input fingerprint')
        packed+=1
        old=row.get('kind_admission',{});new=other.get('kind_admission',{})
        if old.get('checked') is not True or new.get('checked') is not True:raise ValueError('Entry comparison requires two checked guards')
        rejected=lambda value:{(r['row'],r['kind']) for r in value.get('unsupported',[])}
        removed=rejected(old)-rejected(new);added=rejected(new)-rejected(old)
        if removed or added:changes.append(dict(character=identity[0],favorite_stage=identity[1],input_sha256=row['input_sha256'],
            removed_kind_rejections=[dict(row=r,kind=k) for r,k in sorted(removed)],added_kind_rejections=[dict(row=r,kind=k) for r,k in sorted(added)],
            kind_guard_clear=not rejected(new),gpu_admission_verified=False))
    return dict(before_source=before.get('source'),after_source=after.get('source'),identical_packed_profiles=packed,
        changed_kind_guard_profiles=len(changes),profiles=changes,calculation_verified=False,gpu_admission_verified=False,
        scope='Identical original definitions and packed bytes; selected entry guard differences only, not missing handlers or executable GPU coverage')

def plan(report):
    report=copy.deepcopy(report)
    if report.get('schema')!=1 or report.get('stage')!='static-original-coordinate-inputs' or report.get('passed') is not True:
        raise ValueError('A successful original static entry inventory is required')
    character_count=report.get('full_character_verified')
    if any(report.get(k) is not False for k in ('calculation_verified','gpu_admission_verified','full_goal_complete')) or not (character_count is False or type(character_count) is int and character_count==0):
        raise ValueError('Static inventory cannot claim runtime or full-character certification')
    calls=report.get('forbidden_calls',{})
    if set(calls)!={'cpu_battle','gpu'} or any(type(v) is not int or v!=0 for v in calls.values()):raise ValueError('Forbidden inventory calls')
    rows=report.get('profiles');seen=set();failed=set();families={}
    if not isinstance(rows,list) or not rows:raise ValueError('Nonempty original profiles required')
    metadata={r['issue']['code']:r.get('reference_readiness',{}) for r in report.get('packing_priorities',[])}
    for row in rows:
        name=row.get('character');stage=row.get('favorite_stage');identity=(name,stage)
        if not isinstance(name,str) or not name or type(stage) is not int or not 0<=stage<=3 or identity in seen:raise ValueError('Duplicate or invalid profile identity')
        seen.add(identity)
        fingerprint=row.get('original_definitions_sha256')
        if type(fingerprint) is not str or len(fingerprint)!=64 or any(c not in '0123456789abcdef' for c in fingerprint):raise ValueError('Original definition identity required')
        if row.get('gpu_admission_verified') is not False:raise ValueError('Static profile cannot claim GPU admission')
        if type(row.get('input_packed')) is not bool:raise ValueError('Literal packing result required')
        rejected=row.get('kind_admission',{}).get('unsupported',[])
        if row['input_packed'] and not rejected:continue
        failed.add(identity)
        blockers=row.get('effect_blockers',[]) if not row['input_packed'] else [dict(issue=dict(category='kind',kind=r.get('kind'))) for r in rejected]
        if not blockers:blockers=[dict(issue=row.get('program_issue',dict(category='unclassified_program')))]
        for blocker in blockers:
            issue=blocker['issue'];readiness=metadata.get(issue.get('code'),{})
            key=json.dumps({k:issue.get(k) for k in ('kind','stat','category','operator')},sort_keys=True)
            family=families.setdefault(key,dict(operator={k:issue.get(k) for k in ('kind','stat','category','operator')},profiles={},targets={},lanes=set(),scoped_suites={},required_extensions=set(),published_evidence={}))
            family['profiles'][identity]=dict(character=name,favorite_stage=stage,original_definitions_sha256=row['original_definitions_sha256'])
            target=issue.get('target');family['targets'][json.dumps(target,sort_keys=True)]=target
            family['lanes'].add(readiness.get('lane','unclassified'))
            for proof in projected_suites(readiness):family['scoped_suites'][json.dumps(proof,sort_keys=True)]=proof
            family['required_extensions'].update(readiness.get('required_extensions',[]))
            published=readiness.get('published_allocation')
            if published:family['published_evidence'][published['evidence']]=published
    packed=sum(r['input_packed'] for r in rows)
    if type(report.get('profile_count')) is not int or report['profile_count']!=len(rows) or type(report.get('packed_profiles')) is not int or report['packed_profiles']!=packed:raise ValueError('Inventory counts do not match profile rows')
    kind_rejected=sum(bool(r.get('kind_admission',{}).get('unsupported')) for r in rows)
    if type(report.get('kind_rejected_profiles')) is not int or report['kind_rejected_profiles']!=kind_rejected:raise ValueError('Kind rejection count mismatch')
    result=[]
    for f in families.values():
        result.append(dict(operator=f['operator'],affected_profiles=len(f['profiles']),profiles=sorted(f['profiles'].values(),key=lambda r:(r['character'],r['favorite_stage'])),
            targets=list(f['targets'].values()),lanes=sorted(f['lanes']),scoped_suites=sorted(f['scoped_suites'].values(),key=lambda r:r['suite']),
            required_extensions=sorted(f['required_extensions']),published_evidence=list(f['published_evidence'].values()),
            default_admission_changed=False,runtime_validation_performed=False))
    from portable_coordinate_kind_admission import EXTENSIONS
    for family in result:
        kind=family['operator'].get('kind')
        entry_scope=family['operator'].get('category')=='kind'
        family['work_kind']='selected_entry_kind_guard' if entry_scope else 'input_lowering_or_model'
        family['known_handler_extensions']=[dict(macro=macro,needs_burst_controls=controls,scope=comment)
            for macro,kinds,controls,comment in EXTENSIONS if entry_scope and kind in kinds]
    result.sort(key=lambda r:(-r['affected_profiles'],json.dumps(r['operator'],sort_keys=True)))
    return dict(schema='static-entry-plan-v1',profile_count=len(rows),packed_profiles=packed,blocked_profiles=len(failed),operator_families=result,
        ranking='Distinct affected profiles descending, then stable operator identity; overlapping families are not additive',
        input_policy=report.get('input_policy'),source=report.get('source'),profile_selection=report.get('profile_selection'),
        work_queues=dict(input_lowering_or_model=[f for f in result if f['work_kind']=='input_lowering_or_model'],
            selected_entry_kind_guard=[f for f in result if f['work_kind']=='selected_entry_kind_guard']),
        current_source_revalidated=False,calculation_verified=False,gpu_admission_verified=False,full_character_verified=False,full_goal_complete=False,
        cpu_battle_calls=0,gpu_calls=0,compiler_calls=0,scope='Saved static diagnostics and explicitly scoped evidence only; no executable admission or new preparation')

def run(inventory,output,*,write,compare_inventory=None):
    inventory=Path(inventory);output=Path(output)
    if output.exists():raise FileExistsError('A fresh entry plan path is required')
    raw=inventory.read_bytes();result=plan(json.loads(raw));result.update(source_inventory_sha256=hashlib.sha256(raw).hexdigest())
    if compare_inventory is not None:
        compared=Path(compare_inventory).read_bytes()
        result['entry_comparison']=compare_entries(json.loads(raw),json.loads(compared))
        result['entry_comparison']['after_inventory_sha256']=hashlib.sha256(compared).hexdigest()
    write(output,result)
    summary={k:result[k] for k in ('schema','profile_count','packed_profiles','blocked_profiles','ranking','current_source_revalidated','gpu_calls','calculation_verified','full_goal_complete')}
    summary['work_queues']={name:dict(operator_families=len(rows),distinct_profiles=len({(p['character'],p['favorite_stage']) for f in rows for p in f['profiles']})) for name,rows in result['work_queues'].items()}
    if 'entry_comparison' in result:
        summary['entry_comparison']={k:result['entry_comparison'][k] for k in ('before_source','after_source','identical_packed_profiles','changed_kind_guard_profiles','calculation_verified','gpu_admission_verified','scope')}
    summary['ranked_operators']=[dict(operator=f['operator'],affected_profiles=f['affected_profiles'],targets=f['targets'],lanes=f['lanes'],
        work_kind=f['work_kind'],known_handler_extensions=f['known_handler_extensions'],
        scoped_suites=sorted({s['suite'] for s in f['scoped_suites']}),published_evidence=[e['evidence'] for e in f['published_evidence']]) for f in result['operator_families']]
    summary['detail_file']=str(output.resolve());return summary
