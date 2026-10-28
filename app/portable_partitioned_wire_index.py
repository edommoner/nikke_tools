"""Read-only row/page fingerprints of a source-pinned logical wire view."""
import hashlib,json,os,struct,time
from pathlib import Path
from portable_readback_blocks import checked_hash,digest
from portable_partitioned_addresses import WORDS,logical_row_inplace,check_source

MODE='partitioned-saved-wire-index-v1'
SOURCE_OWNER='e2f6470dbd561236dd6690dad2b600b0c839ff0447665ce6307ff9ff54bfdae8'
PAGE_WORDS=16384


def scan(path,layout,expected_raw_sha256,entries,details=None):
    checked_hash(expected_raw_sha256);path=Path(path)
    if path.is_symlink() or layout['output_words']!=WORDS or layout['input_count']!=len(entries) or path.stat().st_size!=WORDS*4*len(entries):raise ValueError('Exact complete frozen wire required')
    detail_pages={};different=[];samples=[]
    if details is not None:
        if details.get('block_words')!=1024 or details.get('maximum_samples')!=8:raise ValueError('Fixed bounded diagnostic blocks required')
        for item in details['pages']:
            key=(item['case_index'],item['page_index'])
            if key in detail_pages or any(type(n) is not int for n in key) or not 0<=key[0]<len(entries) or not 0<=key[1]<(WORDS+PAGE_WORDS-1)//PAGE_WORDS:raise ValueError('Invalid or duplicate diagnostic page')
            count=(min(PAGE_WORDS,WORDS-key[1]*PAGE_WORDS)+1023)//1024
            if len(item['block_sha256'])!=count:raise ValueError('Complete reference subpage hashes required')
            for sha in item['block_sha256']:checked_hash(sha)
            detail_pages[key]=item['block_sha256']
    raw=hashlib.sha256();logical=hashlib.sha256();rows=[];changes=[];active=0
    with path.open('rb') as source:
        for batch in layout['batches']:
            if batch['first_case']!=len(rows):raise ValueError('Noncontiguous saved-wire plan')
            for local in range(batch['cases']):
                part=bytearray(source.read(WORDS*4))
                if len(part)!=WORDS*4:raise ValueError('Truncated saved wire')
                raw.update(part);raw_sha=digest(part)
                count,moved=logical_row_inplace(part,local,batch['first_case']);active+=count;changes.extend(moved)
                logical.update(part);sha=digest(part);i=len(rows);expected=entries[i]['output_sha256']
                for (case,page),blocks in detail_pages.items():
                    if case!=i:continue
                    for number,want in enumerate(blocks):
                        word=page*PAGE_WORDS+number*1024;piece=part[word*4:min((word+1024)*4,len(part))]
                        if digest(piece)!=want:
                            entry=dict(case_index=i,name=entries[i]['name'],page_index=page,block_index=number,case_word_offset=word,reference_sha256=want,actual_sha256=digest(piece))
                            different.append(entry)
                            if len(samples)<8 and not any(s['case_index']==i for s in samples):samples.append(dict(entry,words=list(struct.unpack('<'+str(len(piece)//4)+'I',piece))))
                rows.append(dict(index=i,name=entries[i]['name'],status=struct.unpack_from('<I',part)[0],raw_sha256=raw_sha,
                    logical_sha256=sha,expected_logical_sha256=expected,matches_expected=sha==expected,
                    logical_pages=[digest(part[at:at+PAGE_WORDS*4]) for at in range(0,len(part),PAGE_WORDS*4)]))
        if source.read(1) or len(rows)!=len(entries) or raw.hexdigest()!=expected_raw_sha256:raise ValueError('Saved wire changed or does not match its recorded hash')
    return dict(schema=MODE,raw_sha256=raw.hexdigest(),logical_sha256=logical.hexdigest(),input_count=len(rows),output_words=WORDS,page_words=PAGE_WORDS,
                rows=rows,mismatching_cases=[r['index'] for r in rows if not r['matches_expected']],active_references_checked=active,
                logical_address_changes=changes,detail_different_blocks=different,detail_samples=samples,
                raw_modified=False,numeric_words_modified=0,gpu_calls=0,compiler_calls=0,native_calls=0,calculation_verified=False)


def compare(reference,candidate):
    for record in (reference,candidate):
        if (record.get('schema')!=MODE or record.get('output_words')!=WORDS or record.get('page_words')!=PAGE_WORDS
            or type(record.get('input_count')) is not int or record['input_count']!=len(record['rows'])):raise ValueError('Exact saved-wire index schema required')
        checked_hash(record['raw_sha256']);checked_hash(record['logical_sha256'])
        for i,row in enumerate(record['rows']):
            if row['index']!=i or len(row['logical_pages'])!=(WORDS+PAGE_WORDS-1)//PAGE_WORDS:raise ValueError('Incomplete row/page index')
            for value in (row['raw_sha256'],row['logical_sha256'],row['expected_logical_sha256'],*row['logical_pages']):checked_hash(value)
    if reference['input_count']!=candidate['input_count']:raise ValueError('Different frozen corpus sizes')
    changed=[]
    for a,b in zip(reference['rows'],candidate['rows'],strict=True):
        if a['name']!=b['name'] or a['expected_logical_sha256']!=b['expected_logical_sha256']:raise ValueError('Different frozen case identities')
        pages=[i for i,(x,y) in enumerate(zip(a['logical_pages'],b['logical_pages'],strict=True)) if x!=y]
        if bool(pages)!=(a['logical_sha256']!=b['logical_sha256']):raise ValueError('Contradictory row/page fingerprints')
        if pages:changed.append(dict(index=a['index'],name=a['name'],reference_status=a['status'],candidate_status=b['status'],pages=pages))
    if bool(changed)!=(reference['logical_sha256']!=candidate['logical_sha256']):raise ValueError('Contradictory full/row fingerprints')
    return dict(schema='partitioned-saved-wire-page-diff-v1',reference_logical_sha256=reference['logical_sha256'],candidate_logical_sha256=candidate['logical_sha256'],
                input_count=reference['input_count'],changed_cases=changed,changed_page_count=sum(len(r['pages']) for r in changed),
                all_logical_rows_equal=not changed,gpu_calls=0,compiler_calls=0,native_calls=0,calculation_verified=False)


def compare_samples(reference,candidate,reference_raw):
    """Compare bounded exported words with an entirely hashed identity-view raw.

    This diagnoses retained output only. It never grants calculation admission.
    A raw requiring address relocation must first use its source-pinned view;
    silently treating its file offsets as logical offsets is forbidden here.
    """
    delta=compare(reference,candidate)
    if reference['raw_sha256']!=reference['logical_sha256']:raise ValueError('Identity-view reference raw required')
    samples=candidate.get('detail_samples',[]);blocks=candidate.get('detail_different_blocks',[])
    if not isinstance(samples,list) or len(samples)>8:raise ValueError('At most eight bounded samples required')
    by_case={}
    for sample in samples:
        case=sample['case_index'];word=sample['case_word_offset'];words=sample['words']
        if (type(case) is not int or not 0<=case<reference['input_count'] or case in by_case
            or type(word) is not int or word<0 or word%1024 or word>=WORDS
            or sample['page_index']!=word//PAGE_WORDS or sample['block_index']!=(word%PAGE_WORDS)//1024
            or sample['name']!=reference['rows'][case]['name']
            or not isinstance(words,list) or len(words)!=min(1024,WORDS-word)
            or any(type(v) is not int or not 0<=v<=0xffffffff for v in words)):
            raise ValueError('Invalid bounded word sample')
        record={k:v for k,v in sample.items() if k!='words'}
        if record not in blocks or digest(struct.pack('<'+str(len(words))+'I',*words))!=checked_hash(sample['actual_sha256']):raise ValueError('Sample does not match exported block receipt')
        checked_hash(sample['reference_sha256']);by_case[case]=sample
    path=Path(reference_raw)
    if path.is_symlink() or path.stat().st_size!=WORDS*4*reference['input_count']:raise ValueError('Complete reference raw required')
    full=hashlib.sha256();differences=[]
    with path.open('rb') as source:
        for case,row in enumerate(reference['rows']):
            raw=source.read(WORDS*4);full.update(raw)
            if digest(raw)!=row['raw_sha256'] or row['raw_sha256']!=row['logical_sha256']:raise ValueError('Reference row changed or needs address view')
            if case not in by_case:continue
            sample=by_case[case];word=sample['case_word_offset'];piece=raw[word*4:(word+len(sample['words']))*4]
            if digest(piece)!=sample['reference_sha256']:raise ValueError('Sample references a different Metal block')
            expected=struct.unpack('<'+str(len(piece)//4)+'I',piece)
            changed=[dict(word=word+i,reference=a,candidate=b) for i,(a,b) in enumerate(zip(expected,sample['words'],strict=True)) if a!=b]
            if not changed:raise ValueError('Exported differing block has no differing words')
            differences.append(dict(case_index=case,name=row['name'],block_word=word,changed_words=changed))
        if source.read(1) or full.hexdigest()!=reference['raw_sha256']:raise ValueError('Reference full hash changed')
    return dict(delta,sample_comparisons=differences,sample_words=sum(len(s['words']) for s in samples),
                reference_raw_verified=True,numeric_words_modified=0,raw_modified=False)


def child(cli,capture):
    from portable_phase_audit import Journal
    from portable_partitioned_cuda_origin import gpu_forbidden
    from portable_partitioned_transport import plan
    deadline=time.monotonic()+60
    while not (capture/'start.json').exists():
        if time.monotonic()>deadline:raise RuntimeError('Saved-wire CPU gate was not released')
        time.sleep(.02)
    j=Journal(capture/'phases.jsonl');m=j.invoke('wire_index_controller',cli.verify_package,cli.ROOT);request=cli.load(capture/'run.json')
    if request.get('mode')!=MODE or request.get('package_id')!=m['package_id']:raise ValueError('Unknown saved-wire index request')
    root=Path(request['source_package']);source=Path(request['source_capture'])
    with gpu_forbidden(cli):
        old=j.invoke('wire_index_original_owner',cli.verify_package,root)
        if old['package_id']!=SOURCE_OWNER or old['golden']!=m['golden']:raise ValueError('Exact failed CUDA owner/corpus required')
        anchors=cli.load(source/'artifacts.json')['files'];cli.check_records(source,anchors)
        result=cli.load(source/'result.json');facts=cli.load(source/'execution.json')
        if result.get('passed') is not False or result.get('calculation_verified') is not False or facts.get('timed_out') is not False or facts.get('child_exit_code')!=1:raise ValueError('Preserved completed mismatch capture required')
        if 'Complete typed-address wire view differs from sealed baseline' not in (source/'stderr.log').read_text():raise ValueError('Unknown failed CUDA stage')
        check_source(root,cli.SUITES[m['suite']]['source'],WORDS)
        layout=cli.load(source/'readback.bin.batches/plan.json');prepared=Path(cli.load(source/'run.json')['prepared'])
        packed=(prepared/'input.bin').read_bytes()
        if cli.sha(packed)!=m['golden']['input_sha256'] or layout!=plan(packed,115680,WORDS,16,runtime_stride=143048):raise ValueError('Frozen input/partition plan changed')
        details=None
        if 'details_sha256' in request:
            raw=(capture/'detail-request.json').read_bytes()
            if cli.sha(raw)!=request['details_sha256']:raise ValueError('Diagnostic request changed')
            details=json.loads(raw)
            if details['reference_logical_sha256']!=m['golden']['output_sha256']:raise ValueError('Diagnostic reference differs from frozen Metal')
        report=j.invoke('wire_index_all_saved_rows',scan,source/'readback.bin.partial',layout,request['raw_sha256'],m['golden']['entries'],details)
        cli.check_records(source,anchors)
        report.update(package_id=m['package_id'],source_package_id=old['package_id'],original_stage_passed=False,source_raw_sha256=request['raw_sha256'])
        cli.write(capture/'index.json',report)


def run(cli,source_package,source_capture,capture,workspace,raw_sha256,timeout=180,*,details=None,details_sha256=None):
    from portable_staged_preflight import outside,exclusive
    checked_hash(raw_sha256)
    if os.name!='nt' or type(timeout) is not int or not 1<=timeout<=180:raise ValueError('Windows CPU-only index with 1..180 second budget required')
    m=cli.verify_package(cli.ROOT);capture=outside(capture,[cli.ROOT,Path(source_package),Path(source_capture)]);capture.mkdir(parents=True,exist_ok=False)
    request=dict(mode=MODE,package_id=m['package_id'],source_package=str(Path(source_package).resolve()),source_capture=str(Path(source_capture).resolve()),raw_sha256=raw_sha256)
    if details is not None:
        raw=Path(details).read_bytes()
        if digest(raw)!=checked_hash(details_sha256):raise ValueError('Pinned diagnostic request hash differs')
        with (capture/'detail-request.json').open('xb') as f:f.write(raw)
        request['details_sha256']=details_sha256
    exclusive(capture/'run.json',request)
    os.environ['NIKKE_VALIDATION_JOB_MEMORY_MB']='2048'
    try:
        facts=cli.run_job(capture,'cuda',timeout,original_workspace=str(Path(workspace).resolve()))
        report=cli.load(capture/'index.json') if (capture/'index.json').is_file() else None
        rows=[json.loads(x) for x in (capture/'phases.jsonl').read_bytes().splitlines()] if (capture/'phases.jsonl').exists() else []
        contained,_=cli.job_contained(capture,rows,memory_limit_bytes=2147483648)
        result=dict(mode=MODE,package_id=m['package_id'],passed=bool(facts.get('passed') and contained and report),containment_verified=contained,
                    input_count=report['input_count'] if report else None,mismatching_cases=report['mismatching_cases'] if report else None,
                    gpu_calls=0,compiler_calls=0,native_calls=0,calculation_verified=False,original_stage_passed=False)
        exclusive(capture/'result.json',result);return result
    finally:cli.collect(capture,capture/'artifacts.json')
