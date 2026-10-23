"""One pinned adapter metadata correction; no native numerical expectation waiver."""
import copy,hashlib,json
NAME='leftmost-rejection-domains-v1'
ORIGIN='831de07363be74bf457240464fb810568c95984e9de83355862ee2f79f8e3964'
ADAPTER='research/verify-world-leftmost-retention-short.py'
REJECTED=tuple(range(40,47))+tuple(range(60,68))
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def verify(original,current,entries):
    if original['package_id']!=ORIGIN or original['suite']!=current['suite'] or current['suite']!='leftmost-retention':raise ValueError('Wrong pinned leftmost metadata origin')
    from pathlib import Path
    pins=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/portable-leftmost-replay-migration.json').read_text())
    before={r['path']:r['sha256'] for r in original['files']};after={r['path']:r['sha256'] for r in current['files']}
    if before.get(ADAPTER)!=pins['old_adapter_sha256'] or after.get(ADAPTER)!=pins['new_adapter_sha256']:raise ValueError('Unreviewed leftmost adapter correction')
    for path in before.keys()|after.keys():
        if path.startswith(('app/','research/')) and path.endswith('.py') and path not in (ADAPTER,'app/portable_leftmost_replay_migration.py') and before.get(path)!=after.get(path):raise ValueError('Native source changed during metadata correction: '+path)
    old=original['golden'];new=current['golden'];expected=copy.deepcopy(old)
    if len(entries)!=74 or len(old['entries'])!=74 or len(new['entries'])!=74:raise ValueError('Wrong leftmost correction row count')
    if tuple(i for i,(_,_,d) in enumerate(entries) if d is None)!=REJECTED:raise ValueError('Wrong leftmost rejection domains')
    for i in REJECTED:
        row=old['entries'][i]
        if row['native_sha256']!=digest(dict(rejected=True)) or entries[i][0]!=row['name'] or '/reject/' not in row['name']:raise ValueError('Wrong original rejection metadata')
        expected['entries'][i]['native_sha256']=digest(dict(status=64))
    if expected!=new:raise ValueError('Metadata correction changed another source/input/native baseline')
    return dict(kind=NAME,origin_package_id=ORIGIN,corrected_rejection_indices=list(REJECTED),corrected_rejections=15,positive_native_oracles_unchanged=59,all_input_and_gpu_baselines_equal=True,gpu_calls=0)
