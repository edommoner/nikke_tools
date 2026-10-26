"""Full raw retention with one source-defined absolute trace-address relocation.

No words are ignored or normalized. The changed address must equal its actual
trace record under both strides; every other prefix byte and all tail bytes are
checked. This is not a native calculation certificate or a GPU code normalizer.
"""
import hashlib,json,struct
from pathlib import Path
PREFIX=2032000;OUTPUT=2064786;INPUT=115680
TYPED=1769856;POINTER=TYPED+153568+544+530;RECORD=TYPED+3568
WITNESSES=('gpu/destructible_battle_runtime.slang','gpu/destructible_shield_frame_hooks.slang','gpu/world_coordinate_typed_entry.slang')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def word(block,index):return struct.unpack_from('<I',block,index*4)[0]

def compare_block(before,after,index):
    if len(before)!=PREFIX*4 or len(after)!=OUTPUT*4:raise ValueError('Complete resident arc blocks required')
    if any(after[PREFIX*4:]):raise ValueError('Resident arc tail not cleared')
    prefix=after[:PREFIX*4]
    if before==prefix:return None
    at=POINTER*4
    if before[:at]!=prefix[:at] or before[at+4:]!=prefix[at+4:]:raise ValueError('Non-address prefix bytes changed')
    record_index=word(before,POINTER+1)
    if word(before,TYPED)!=0x44425431 or not 1<=record_index<=word(before,TYPED+1)<=128:raise ValueError('Trace field ownership not established')
    relative=RECORD+(record_index-1)*1040
    if word(before,relative)!=record_index:raise ValueError('Trace record identity differs')
    old_pointer=word(before,POINTER);new_pointer=word(prefix,POINTER)
    if old_pointer!=index*PREFIX+relative or new_pointer!=index*OUTPUT+relative:raise ValueError('Trace address does not match both case bases')
    return dict(case_index=index,word_offset=POINTER,record_index=record_index,old_address=old_pointer,new_address=new_pointer)

def run(reference,candidate,out,*,reference_evidence_sha256,candidate_evidence_sha256):
    reference,candidate,out=map(Path,(reference,candidate,out))
    if out.exists() or out.is_symlink():raise FileExistsError(out)
    old_raw=(reference/'evidence.json').read_bytes();new_raw=(candidate/'evidence.json').read_bytes()
    if sha(old_raw)!=reference_evidence_sha256 or sha(new_raw)!=candidate_evidence_sha256:raise ValueError('Pinned evidence SHA mismatch')
    old,new=map(json.loads,(old_raw,new_raw))
    if json.loads((reference/'result.json').read_text()).get('calculation_verified') is not True:raise ValueError('Verified reference calculation required')
    if new.get('gpu_execution_verified') is not True or new['transport'].get('command_status')!='completed':raise ValueError('Completed candidate GPU transport required')
    count=old['transport']['cases']
    if count!=106 or new['transport']['cases']!=count:raise ValueError('Complete106 inputs required')
    if old['input_sha256']!=new['input_sha256']:raise ValueError('Input fingerprints differ')
    for root,evidence in [(reference,old),(candidate,new)]:
        raw=(root/'input.bin').read_bytes()
        if sha(raw)!=evidence['input_sha256'] or len(raw)!=4+count*INPUT*4 or word(raw,0)!=count:raise ValueError('Input byte verification failed')
    for name in WITNESSES:
        if name not in old['source_sha256'] or old['source_sha256'][name]!=new['source_sha256'].get(name):raise ValueError('Trace writer/binding source changed: '+name)
    before_hash=hashlib.sha256();after_hash=hashlib.sha256();relocations=[]
    with (reference/'readback.bin').open('rb') as before,(candidate/'readback.bin').open('rb') as after:
        for index in range(count):
            a=before.read(PREFIX*4);b=after.read(OUTPUT*4);delta=compare_block(a,b,index)
            before_hash.update(a);after_hash.update(b)
            if delta is not None:relocations.append(delta)
        if before.read(1) or after.read(1):raise ValueError('Unexpected readback suffix')
    if before_hash.hexdigest()!=old['output_sha256'] or after_hash.hexdigest()!=new['output_sha256']:raise ValueError('Complete readback SHA mismatch')
    if (reference/'evidence.json').read_bytes()!=old_raw or (candidate/'evidence.json').read_bytes()!=new_raw:raise ValueError('Evidence changed during retention audit')
    result=dict(schema='resident-arc-retention-v1',passed=True,reference_evidence_sha256=reference_evidence_sha256,candidate_evidence_sha256=candidate_evidence_sha256,reference_output_sha256=before_hash.hexdigest(),candidate_output_sha256=after_hash.hexdigest(),cases=count,old_words=PREFIX,new_words=OUTPUT,verbatim_prefix_equal=not relocations,all_other_prefix_bytes_equal=True,all_tail_bytes_zero=True,relocated_address_words=len(relocations),relocations=relocations,source_witnesses={name:old['source_sha256'][name] for name in WITNESSES},gpu_calls=0,calculation_verified=False,scope='Every byte accounted for; one exact source-defined address field checked against record identity and old/new case bases. Fresh native audit remains required.')
    with out.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    return result
