"""Complete real squads through the proof CLI; reuse preparation and oracle."""
import array
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/p) for p in ('app','research','scripts')]
spec = importlib.util.spec_from_file_location('roster_regression_oracle', ROOT/'research/verify-world-projectile-rosters.py')
real = importlib.util.module_from_spec(spec)
spec.loader.exec_module(real)
spec = importlib.util.spec_from_file_location('roster_regression_digest', ROOT/'research/summarize-portable-cross-gpu.py')
cross = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cross)

# Newly packable stun profiles plus existing burst and live-HP controls. All
# definitions are retained; selection is of complete public character profiles.
PROFILES = [('D',0), *[('프리바티',stage) for stage in range(4)],
            ('마스트 : 로망틱 메이드',0), ('타키나',0), ('목단',3), ('미란다',0),
            ('센티',0), ('센티',1)]
PROFILES += [('센티',2), ('센티',3), ('마르차나',0), ('앵커 : 이노센트 메이드',0), ('소라',0)]
PROFILES += [('스노우 화이트 : 이노센트 데이즈',0), ('홍련 : 흑영',0)]
PROFILES += [('율리아',1), ('율리아',2)]
PROFILES += [('이사벨',0)]
PROFILES += [('에이다',0)]
PROFILES += [('길티',0), ('신',0), ('퀀시',0)]
PROFILES += [('퀸(마코토)',0), ('유키코',0), ('아이기스',0)]
PROFILES += [('브래디',0), ('엠마 : 택티컬 업',0)]
PROFILES += [('브리드 : 사일런트 트랙',0), ('율리아',3), ('미하라 : 본딩 체인',0), ('소다',0),
             ('마르차나 : 마린 스터디',0), ('헬름 : 아쿠아마린',0), ('아인',0), ('신데렐라',0)]
PROFILES += [('이브',0), ('디젤 : 윈터 스위츠',0), ('라푼젤',0), ('마나',0)]
DURATIONS = (3,30)
suite = SimpleNamespace(INPUT=real.INPUT_WORDS, OUTPUT=real.OUTPUT_WORDS,
                        inspect_native=lambda case: real.native_reference(case['body']))


def prepare():
    entries = []
    for character,stage in PROFILES:
        for duration in DURATIONS:
            body = dict(real.body_for(real.policy.roster_for(character),duration), burst_gauge_mode='accumulate')
            profile = body['profile']['chars'][character]
            profile['favorite_stage'] = stage
            if stage: profile['collection_stage'] = 'SR15'
            prepared = real.engine_worker.evaluate(dict(body,_portable_static_inputs=True))
            words,metadata = real.compile_projectile_battle(prepared)
            case = dict(character=character,favorite_stage=stage,duration=duration,body=body)
            entries.append((f'real/{character}/favorite-{stage}/{duration}s',words,
                            (case,prepared,words,metadata)))
    # Exercise the selector with all three real persona characters together,
    # retaining their complete definitions, equipment and support characters.
    for duration in DURATIONS:
        body=dict(real.body_for(['리타','크라운','퀸(마코토)','유키코','아이기스'],duration),burst_gauge_mode='accumulate')
        prepared=real.engine_worker.evaluate(dict(body,_portable_static_inputs=True))
        words,metadata=real.compile_projectile_battle(prepared)
        case=dict(character='persona-triad',favorite_stage=0,duration=duration,body=body)
        entries.append((f'real/persona-triad/favorite-0/{duration}s',words,(case,prepared,words,metadata)))
    packed = array.array('I',[len(entries)])
    for _,words,_ in entries: packed.extend(words)
    if sys.byteorder != 'little': packed.byteswap()
    return entries,packed.tobytes()


def compare(block,domain):
    if block[0] != 0: raise ValueError('Real squad rejected: status '+str(block[0]))
    case,prepared,words,metadata = domain
    native,shots = real.native_reference(case['body'])
    _,_,_,differences = real.compare(block,prepared,(words,metadata),native,shots)
    if differences: raise ValueError(str(dict(difference_count=len(differences),first_differences=differences[:8])))
    return dict(battle=native,skill_trace=shots)
