import hashlib,json,shutil,sys
from pathlib import Path
R=Path(__file__).resolve().parent;name=sys.argv[1];index=int(sys.argv[2]);assert not (R/'stop.json').exists();P=R/name;program=json.loads((P/'program.json').read_text(encoding='utf-8'));b=next(x for x in program['batches'] if x['index']==index);assert (P/'jit-link-object-verified.json').is_file()
if index:assert (P/'progress'/('batch-'+str(index-1).zfill(3)+'.json')).is_file()
B=P/('batch-'+str(index).zfill(3));assert not B.exists()
keys={'api_job','api_job_sha256','api_expected','api_expected_sha256'}
if keys&set(b):
 assert keys<=set(b),'Incomplete independently hashed batch documents'
 documents=b
else:documents=program
raw=(R/documents['api_job']).read_bytes();assert hashlib.sha256(raw).hexdigest()==documents['api_job_sha256'];fulljob=json.loads(raw)
expected_raw=(R/documents['api_expected']).read_bytes()
if 'api_expected_sha256' in documents:assert hashlib.sha256(expected_raw).hexdigest()==documents['api_expected_sha256']
fullexpected=json.loads(expected_raw);assert fullexpected['owner']==program['owner'] and program['source_commit'].startswith(fullexpected['source_commit'])
members=b['member_indices'];job=dict(kind='batch',evaluations=[fulljob['evaluations'][i] for i in members]);assert all(x['compute_backend']=='cuda_shared_detail' and x['duration']==fulljob['evaluations'][mi]['duration'] and type(x.get('verify_detail',False)) is bool for x,mi in zip(job['evaluations'],members,strict=True))
jobraw=raw if members==list(range(len(fulljob['evaluations']))) else (json.dumps(job,ensure_ascii=False,indent=2,allow_nan=False)+chr(10)).encode();expected=dict(schema='special-batch-expectations-v1',owner=program['owner'],source_commit=program['source_commit'],source=program['source'],body_sha256=hashlib.sha256(jobraw).hexdigest(),physical_cases=b['cases'],input_words=program['input_words'],output_words=program['output_words'],physical_input_bytes=b['physical_input_bytes'],physical_output_bytes=b['physical_output_bytes'],physical_input_sha256=b['physical_input_sha256'],physical_output_sha256=b['physical_output_sha256'],cases=[dict(fullexpected['cases'][i],duration=fulljob['evaluations'][i]['duration']) for i in members]);assert [x['index'] for x in expected['cases']]==b['original_profile_indices']
base=json.loads((R.parent/'standard-remaining-fixed-windows-v2/base-paths.json').read_text(encoding='utf-8'));cfg=json.loads((P/'sdk-paths.json').read_text(encoding='utf-8'));link=json.loads((P/'jit-link-v1/proof/jit-link.json').read_text(encoding='utf-8'))['receipt']['artifact'];gen=json.loads((P/'compile-ptx-v1/proof/generation-cache.json').read_text(encoding='utf-8'));base.update(cfg,calculation_package=cfg['packet'],validation_root=str(B),api_capture=str(B/'api-once-v1'),temporary=str(B/'temporary'),expected_file=str(B/'expected.json'),body_file=str(B/'job.json'),original_body_file=str(B/'job.json'),image_sha256=link['sha256'],image_bytes=link['bytes'],generation_cache_key=gen['key'])
validation=dict(program=program['program'],owner=program['owner'],source_commit=program['source_commit'],artifact=dict(bytes=link['bytes'],sha256=link['sha256']),paired_cache=dict(key=gen['key'],hit=True,compiler_invocations=0),batches=[dict(x,profile_indices=x['original_profile_indices'],physical_readback_bytes=x['physical_output_bytes'],expected_physical_input_sha256=x['physical_input_sha256'],expected_physical_output_sha256=x['physical_output_sha256']) for x in program['batches']])
if not (P/'validation-request.json').exists():(P/'validation-request.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
else:assert json.loads((P/'validation-request.json').read_text(encoding='utf-8'))==validation
B.mkdir();(B/'temporary').mkdir();(B/'job.json').write_bytes(jobraw);(B/'expected.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2),encoding='utf-8');(B/'paths.json').write_text(json.dumps(base,indent=2),encoding='utf-8')
for src in (R/'api-templates').rglob('*.py'):
 dst=B/src.relative_to(R/'api-templates');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for stage,script in [('static-preflight',B/'static-preflight.py'),('api-once-v1',B/'api-once-v1/api-once.py'),('saved-audit',B/'audit-saved.py')]:
 (B/stage/'request.json').write_text(json.dumps(dict(cwd=cfg['packet'],argv=[str(script)])),encoding='utf-8')
print(json.dumps(dict(program=name,batch=index,cases=b['cases'],profile_indices=b['original_profile_indices'],owner=program['owner'],paired_cache_key=gen['key'],post_calls=0,gpu_calls=0)),flush=True)
