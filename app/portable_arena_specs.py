"""Shared input/output ownership for coordinate and actual-shot profiles.

The combined-v1 entry connects the resident executor and both output arenas.
Coordinate physical routing remains limited to a body-only pool.
"""
from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path

WORLD_INPUT_WORDS = 104400
WORLD_OUTPUT_WORDS = 786432
LEGACY_OUTPUT_WORDS = 1048576
PROFILES = ('coordinate', 'attack-group', 'combined-legacy', 'combined-v1')


@dataclass(frozen=True)
class Region:
    domain: str
    name: str
    base: int
    words: int

    @property
    def end(self):
        return self.base + self.words


def coordinate_layout(base=WORLD_OUTPUT_WORDS):
    from portable_coordinate_scene_specs import LAYOUT as scene
    if type(base) is not int or base < WORLD_OUTPUT_WORDS:
        raise ValueError('Invalid coordinate arena base')
    row = dict(BASE=base, HEADER_WORDS=16, FRAME=base+16,
               FRAME_WORDS=scene['SNAPSHOT'], CAST=base+16+scene['SNAPSHOT'],
               CASTS=32, SNAPSHOT_WORDS=68,
               PACKETS=base+16+scene['SNAPSHOT']+32*68, PACKET_COUNT=2048)
    row['TRACE'] = row['PACKETS'] + row['PACKET_COUNT']*row['SNAPSHOT_WORDS']
    row.update(TRACE_COUNT=4096, TRACE_WORDS=12)
    row['SELECTION'] = row['TRACE'] + row['TRACE_COUNT']*row['TRACE_WORDS']
    row['SELECTION_WORDS'] = 65536
    row['END'] = row['SELECTION'] + row['SELECTION_WORDS']
    return row


def attack_group_layout(landings=2048):
    if type(landings) is not int or landings != 2048:
        raise ValueError('Preserve the actual-shot landing capacity')
    row = dict(HEADER=800000, HEADER_WORDS=32, SLOTS=800032, SLOTS_COUNT=32,
               WORDS=536, LOG=820000, LOG_CAP=64, PACKETS=860000,
               PACKET_COUNT=landings, OUTPUT_WORDS=LEGACY_OUTPUT_WORDS)
    row['COMPACT'] = row['PACKETS'] + landings
    row['COMPACT_WORDS'] = row['OUTPUT_WORDS'] - row['COMPACT']
    return row


def coordinate_shader_schema():
    return ('// Generated from portable_coordinate_packet_specs.\n'
            '#ifdef PORTABLE_COMPOSED_ARENA\n#include "composed_arena_layout.slang"\n#else\n'
            + ''.join(f'static const uint CP_{key}={value};\n' for key,value in coordinate_layout().items())
            + '#endif\n')


def attack_group_shader_declarations():
    row = attack_group_layout()
    return ('static const uint '+','.join(f'AG_{key}={row[key]}' for key in
            ('HEADER', 'SLOTS', 'WORDS', 'LOG', 'LOG_CAP', 'PACKETS'))+';\n'
            '#ifdef PORTABLE_COORDINATE_GROUPS\nstatic const uint AG_COMPACT=1310720,AG_COMPACT_WORDS=186528;\n#else\n'
            f'static const uint AG_COMPACT=AG_PACKETS+P_LANDINGS,AG_COMPACT_WORDS={row["OUTPUT_WORDS"]}-AG_COMPACT;\n#endif\n')


def regions(profile):
    if profile not in PROFILES:
        raise ValueError('Unknown arena profile')
    from portable_coordinate_scene_specs import LAYOUT as scene
    from portable_coordinate_area_specs import LAYOUT as area
    cp = coordinate_layout(LEGACY_OUTPUT_WORDS if profile == 'combined-v1' else WORLD_OUTPUT_WORDS)
    ag = attack_group_layout()
    coordinate = profile != 'attack-group'
    groups = profile != 'coordinate'
    # P_INPUT_WORDS grows by eight with PORTABLE_ATTACK_GROUPS, so the scene
    # reader moves automatically; CA_BASE_INPUT remains literal in legacy IR.
    scene_base = WORLD_INPUT_WORDS + (8 if groups else 0)
    area_base = scene_base+scene['INPUT'] if profile == 'combined-v1' else area['BASE_INPUT']
    input_words = scene_base + scene['INPUT'] + area['INPUT'] if coordinate else WORLD_INPUT_WORDS+8
    output_words = ((cp['END']+65535)//65536)*65536 if profile == 'combined-v1' else LEGACY_OUTPUT_WORDS
    rows = [Region('input', 'world', 0, WORLD_INPUT_WORDS),
            Region('output', 'world-reserved-envelope', 0, WORLD_OUTPUT_WORDS)]
    if groups:
        rows += [Region('input', 'attack-group-policy', WORLD_INPUT_WORDS, 8),
                 Region('output', 'attack-group-header', ag['HEADER'], ag['HEADER_WORDS']),
                 Region('output', 'attack-group-slots', ag['SLOTS'], ag['SLOTS_COUNT']*ag['WORDS']),
                 Region('output', 'attack-group-log', ag['LOG'], ag['LOG_CAP']*ag['WORDS']),
                 Region('output', 'attack-group-packets', ag['PACKETS'], ag['PACKET_COUNT']),
                 Region('output', 'attack-group-compact', ag['COMPACT'], ag['COMPACT_WORDS'])]
    if coordinate:
        rows += [Region('input', 'coordinate-scene', scene_base, scene['INPUT']),
                 Region('input', 'coordinate-area', area_base, area['INPUT']),
                 Region('output', 'coordinate-header', cp['BASE'], cp['HEADER_WORDS']),
                 Region('output', 'coordinate-frame', cp['FRAME'], cp['FRAME_WORDS']),
                 Region('output', 'coordinate-casts', cp['CAST'], cp['CASTS']*cp['SNAPSHOT_WORDS']),
                 Region('output', 'coordinate-packets', cp['PACKETS'], cp['PACKET_COUNT']*cp['SNAPSHOT_WORDS']),
                 Region('output', 'coordinate-trace', cp['TRACE'], cp['TRACE_COUNT']*cp['TRACE_WORDS']),
                 Region('output', 'coordinate-selection', cp['SELECTION'], cp['SELECTION_WORDS']),
                 # The current initializer clears through the output stride.
                 Region('output', 'coordinate-clear-tail', cp['END'], output_words-cp['END'])]
    return rows, input_words, output_words


def audit_regions(rows, input_words, output_words):
    limits = dict(input=input_words, output=output_words)
    for key, value in limits.items():
        if type(value) is not int or value <= 0:
            raise ValueError('Invalid '+key+' stride')
    names = set()
    for row in rows:
        if row.domain not in limits or row.name in names:
            raise ValueError('Unknown domain or duplicate arena owner')
        names.add(row.name)
        if (type(row.base) is not int or type(row.words) is not int
                or row.base < 0 or row.words <= 0 or row.end > limits[row.domain]):
            raise ValueError('Arena region outside stride: '+row.name)
    overlaps = []
    # Check every pair: a large containing region can overlap several shorter ones.
    for index, first in enumerate(rows):
        for second in rows[index+1:]:
            if first.domain != second.domain:
                continue
            start, end = max(first.base, second.base), min(first.end, second.end)
            if start < end:
                overlaps.append(dict(domain=first.domain, first=first.name,
                                     second=second.name, start=start, end=end, words=end-start))
    return dict(address_plan_verified=not overlaps, input_words=input_words,
                output_words=output_words, overlaps=overlaps,
                regions=[dict(asdict(row), end=row.end) for row in rows])


def audit_profile(profile):
    rows, input_words, output_words = regions(profile)
    return dict(profile=profile, runtime_connected=profile != 'combined-legacy',
                composed_physical_scope='body-only' if profile=='combined-v1' else None,
                gpu_execution_verified=False, gpu_calls=0, calculation_verified=False,
                **audit_regions(rows, input_words, output_words))


def audit_live_sources(root):
    """Check generated declarations against the real legacy readers/writers."""
    root = Path(root)
    from portable_specs import shader_schema
    expected = {'gpu/coordinate_packet_layout.slang': coordinate_shader_schema(),
                'gpu/composed_arena_layout.slang': composed_shader_schema(),
                'gpu/portable_schema.slang': shader_schema()}
    hashes = {}
    for name, text in expected.items():
        raw = (root/name).read_bytes()
        if raw != text.encode():
            raise ValueError('Arena schema drift: '+name)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    name = 'gpu/attack_group_runtime.slang'
    raw = (root/name).read_bytes()
    declarations = attack_group_shader_declarations().encode()
    if raw.count(declarations) != 1:
        raise ValueError('Attack-group shader declarations drift')
    hashes[name] = hashlib.sha256(raw).hexdigest()
    consumers = {
        name: ('uint input=s.inputBase+104400,head=agHead(s);',
               'for(uint i=0;i<32+32*AG_WORDS;i++) results[head+i]=0;',
               'for(uint i=0;i<AG_LOG_CAP*AG_WORDS;i++) results[s.resourceOutput+AG_LOG+i]=0;',
               'for(uint i=0;i<P_LANDINGS;i++) results[s.resourceOutput+AG_PACKETS+i]=0;',
               'for(uint i=0;i<AG_COMPACT_WORDS;i++) results[s.resourceOutput+AG_COMPACT+i]=0;'),
        'gpu/world_coordinate_area_entry.slang': (
            'uint input=1+id.x*(P_INPUT_WORDS+C_INPUT+CA_INPUT),output=id.x*P_OUTPUT_WORDS,dst=output+CP_BASE;',
            'CoordinateScene c;c.input=input+P_INPUT_WORDS;',
            'for(uint i=CP_BASE;i<P_OUTPUT_WORDS;i++)results[output+i]=0;',
            'for(uint i=CP_BASE;i<AG_COMPACT;i++)results[output+i]=0;'),
        'gpu/coordinate_skill_runtime.slang': ('CoordinateScene c;c.input=s.inputBase+P_INPUT_WORDS;',),
        'gpu/coordinate_area_runtime.slang': ('uint coordinateAreaInput(inout Runtime s){return s.inputBase+CA_BASE_INPUT;}',),
    }
    for name, snippets in consumers.items():
        raw = (root/name).read_bytes()
        if any(raw.count(snippet.encode()) != 1 for snippet in snippets):
            raise ValueError('Arena consumer address/clear drift: '+name)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    from portable_specs import LIMITS
    from portable_scratch_layout import audit_sources
    resident = audit_sources(root, LIMITS)
    attack_group_layout(LIMITS['LANDINGS'])
    # Area/scene input offsets are separate from the shader's world stride.
    from portable_coordinate_area_specs import LAYOUT as area, check_schema
    from portable_coordinate_scene_specs import LAYOUT as scene, source_matches
    check_schema(root)
    if not source_matches(root) or area['BASE_INPUT'] != WORLD_INPUT_WORDS+scene['INPUT']:
        raise ValueError('Coordinate input schema drift')
    from portable_arena_composed_source_contract import project_sources
    project_sources(root)
    for name in ('gpu/world_coordinate_composed_entry.slang','gpu/coordinate_area_hooks.slang','gpu/world_team_runtime.slang'):
        hashes[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
    return dict(schema=1, scope='Static input/output ownership; no battle or GPU proof',
                legacy_shader_declarations_verified=True, composed_source_contract_verified=True, resident_audit=resident,
                source_sha256=hashes, gpu_calls=0)


def composed_shader_schema():
    """Generated address contract consumed by the composed entry."""
    rows, input_words, output_words = regions('combined-v1')
    offsets = {row.name: row.base for row in rows}
    values = dict(INPUT_WORDS=input_words, OUTPUT_WORDS=output_words,
                  SCENE_INPUT_BASE=offsets['coordinate-scene'],
                  AREA_INPUT_BASE=offsets['coordinate-area'])
    return ('// Generated combined-v1 address contract.\n#ifndef PORTABLE_COMPOSED_ARENA_LAYOUT\n#define PORTABLE_COMPOSED_ARENA_LAYOUT\n'
            + ''.join(f'static const uint COMPOSED_{key}={value};\n' for key, value in values.items())
            + ''.join(f'static const uint CP_{key}={value};\n' for key, value in coordinate_layout(LEGACY_OUTPUT_WORDS).items())
            + attack_group_shader_declarations() + '#endif\n')
