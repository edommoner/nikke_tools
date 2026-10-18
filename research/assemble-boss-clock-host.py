"""One-shot host ABI migration for the GPU boss scheduler."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def edit(name,changes):
    p=ROOT/name;t=p.read_text(encoding='utf-8')
    for old,new in changes:
        assert old in t,(name,old);t=t.replace(old,new)
    p.write_text(t,encoding='utf-8')
edit('app/detail_world.py',[
 ("parts=read_parts(enemy.pop('parts',[]))\n    if parts:enemy['patterns']=patterns_for(parts)","parts=read_parts(enemy.pop('parts',[]))\n    raw=enemy.pop('patterns',[])\n    from detail_boss import validate_patterns\n    validate_patterns(patterns_for(parts)+raw)\n    if raw or parts:enemy['patterns']=patterns_for(parts)+raw"),
])
edit('app/engine_worker.py',[
 ("'has_parts', 'parts'}","'has_parts', 'parts', 'patterns', 'optimal_range_weapons'}"),
 ("if parts:result['parts_state']=cpu_parts_state(parts,executed)","if parts:result['parts_state']=cpu_parts_state(parts,executed)\n        if body.get('enemy',{}).get('patterns'):\n            result['boss_patterns']=copy.deepcopy(body['enemy']['patterns'])\n            result['boss_timeline']=[dict(time=round(e.t,6),pattern=e.pattern,kind=e.kind,event=e.event,outcome=e.outcome or None) for e in executed.boss_log if e.pattern!='authored-live-parts' and e.event in ('start','end')]"),
])
edit('app/detail_gpu.py',[
 ("from detail_world import EN,read_parts,patterns_for,packed_enemy","from detail_world import EN,read_parts,patterns_for,packed_enemy\nfrom detail_boss import WP,WB,BP,BLOG,WEAPONS,compile_world,validate_world,UnsupportedBoss"),
 ('detail_named_capacity_v30','detail_boss_clock_v31'),('detail_state_bytes_v30','detail_state_bytes_v31'),
 ("return {'effects':rows,'states':states,'chars':chars,'source_rows':source_rows}","return {'effects':rows,'states':states,'chars':chars,'source_rows':source_rows,'mode_weapons':[WEAPONS.index(e.get('weapon_type','SR')) if e.get('type')=='weapon_change' else -1 for e,n in compiled]+[-1]*(len(rows)-len(compiled))}"),
 ("typ=25;arg=int(core>=1)","typ=35;arg=0"),
 ("if enemy.get('patterns',[])!=patterns_for(parts) or enemy.get('coord') is not None:raise UnsupportedDetail('Only authored fixed live parts are implemented; other boss patterns remain unsupported')","if enemy.get('coord') is not None:raise UnsupportedDetail('Coordinate boss geometry is not yet implemented')"),
 ("# Burst-recipient targets are sampled by the GPU and stored in independent", "try:program['world'],patterns=compile_world(enemy,parts,body,program)\n except (UnsupportedBoss,ValueError) as error:raise UnsupportedDetail(str(error)) from error\n # Burst-recipient targets are sampled by the GPU and stored in independent"),
 ("'parts':parts, 'prepared'","'parts':parts,'patterns':patterns, 'prepared'"),
 ("for p in programs:\n  if len(p['chars'])", "for p in programs:\n  validate_world(p.get('world',[0]*WP))\n  if p.get('world',[0])[0] and (not any(r[1]==4 for r in script) or sum(r[1]==5 for r in script)!=1):raise UnsupportedDetail('Live boss patterns require one complete autonomous squad schedule')\n  if len(p['chars'])"),
 ("array.array('d',(v for row in script for v in row))", "array.array('d',(v for p in programs for v in p.get('world',[0]*WP))),array.array('d',(v for row in script for v in row))"),
 ("if any(row[1]==2 and row[2]==113", "if any(row[1]==2 and row[2]==115 and (int(row[4])!=row[4] or not 0<=row[4]<BLOG) for row in script):raise ValueError('Invalid boss log query')\n if any(row[1]==2 and row[2]==113"),
])
edit('app/gpu_service.py',[("'burst_gauge_mode','parts_state'","'burst_gauge_mode','parts_state','boss_patterns','boss_timeline'")])
for name in ['scripts/build-combat.py','scripts/build-detail-native.py']:
    edit(name,[('detail_named_capacity_v30','detail_boss_clock_v31')])
edit('server.mjs',[(".update(readFileSync(path.join(root, 'app/detail_world.py')))",".update(readFileSync(path.join(root, 'app/detail_world.py'))).update(readFileSync(path.join(root, 'app/detail_boss.py')))")])
print('Host boss-clock v31 assembled')
