"""Narrow,explicit native-CPU omission;never alter CPU execution or GPU inputs."""
import math
from unittest.mock import patch
from calculator.buff_manager import BuffManager

HP_STATS={'max_hp_pct','max_hp_only_pct','hp_caster_based_pct','hp_only_caster_based_pct','max_hp_from_max_hp_pct'}


def native_reference(body,prepared,run):
    if body['squad'][0]!='백학':return run(body),None
    # These two fixed simple-boss profiles are the observed gap. Do not turn
    # this into a generic HP-field exclusion for other characters or worlds.
    assert body['duration']==180 and body['burst_gauge_mode']=='accumulate'
    capture={};original=BuffManager.effective_max_hp
    def passthrough(bm,name):
        capture['bm']=bm
        return original(bm,name)
    with patch.object(BuffManager,'effective_max_hp',passthrough):cpu=run(body)
    bm=capture['bm'];names=body['squad'];when=cpu['last_frame']
    active=[ab for ab in bm._active if ab.effect.get('stat') in HP_STATS]
    assert len(active)==1
    ab=active[0];effect=ab.effect
    assert ab.caster==names[0] and effect['stat']=='hp_caster_based_pct'
    assert effect['name']=='회복 독점 서약' and effect['trigger']['condition']==['not_self_state:서약 해지']
    assert ab.has_runtime_conditions and math.isinf(ab.expires_at) and set(ab.target_chars)==set(names)
    enabled=bm._runtime_condition_ok(effect['trigger']['condition'],ab.caster,ab.caster,ab.caster,when)
    assert not enabled
    values=[]
    for i,n in enumerate(names):
        base=prepared['allies'][i]['base_hp'];value=bm._get_value(effect,ab,n)
        assert value is not None
        stale=base+prepared['allies'][0]['base_hp']*value/100.0
        actual=cpu['query']['allies'][i]
        assert actual['hp']==actual['max_hp']==stale and actual['hp_pct']==100
        values.append(dict(owner=i,base_hp=base,value_pct=value,native_hp=stale,contract_hp=base))
    return cpu,dict(kind='Pinned effective_max_hp omits runtime predicate recheck',
        effect_name=effect['name'],caster=ab.caster,conditions=effect['trigger']['condition'],
        runtime_condition_enabled=enabled,observed_time=when,values=values,
        native_battle_modified=False,independent_contract_fixture='tests/fixtures/portable-health-runtime.json',
        scope='Two fixed 180-second simple-boss profiles;not a generic CPU difference waiver')


def verify_difference(differences,evidence):
    if evidence is None:return None
    expected=[]
    for row in evidence['values']:
        for field in ('hp','max_hp'):
            expected.append(dict(path=f".allies[{row['owner']}].{field}",gpu=row['contract_hp'],cpu=row['native_hp']))
    # Exact paths and both numeric values are checked; every other field must
    # still equal the original CPU battle,including damage and burst timing.
    assert differences==expected,(differences,expected)
    return dict(**evidence,original_native_differences=differences,
                contract_all_fields_verified=True,native_exact_match=False)
