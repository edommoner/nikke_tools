"""Keep next-stage requirements concrete without counting pending work as complete."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'research/boss-gpu-integration-notes.json';old=json.loads(p.read_text(encoding='utf-8'))
archive=ROOT/'research/ports/v31/research/boss-gpu-integration-notes.json'
if not archive.exists():archive.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r={'status':'v31 live core/move clock verified; v32 ordered buff/dispel GPU verification in progress','objective':'all characters and all special effects on GPU','objective_complete':False,
 'current_boundary':{'cpu_adapter':'Validated authored enemy.patterns and fixed live parts accepted; coordinates remain rejected for GPU.','gpu_compiler':'core/move/idle/groggy plus ordered boss buff defense and received damage; inactive boss definitions have separate caster identity 5.','gpu_world':'Mutable per-squad EN=68; lifecycle and scalar overlays are computed on device. Enemy cleanse is deferred until the next begin_frame.','verification':'Independent CPU end-of-frame snapshots are collected at the pinned simulate loop time advance, without get_buffs or other gameplay queries. CPU traces are never GPU input.'},
 'next_required_work':[
  {'area':'Rosanna / stealth','source':'calculator/buff_manager.py has_live_stat; timeline.py _boss_targets','requirements':['Port a real live-stat predicate with lifetime, lazy recipients and runtime gates.','Boss target selection must exclude stealth only for random/top-ATK rules, preserve slot/all behavior and taunt priority, and fall back to the remaining pool when all are hidden.','Raw Rosanna is still rejected; implementing enemy_buff_cleanse alone does not count the entire character as supported.']},
  {'area':'Incoming attacks','source':'timeline.py _boss_attack, _boss_targets, _boss_debuff, _boss_dots','requirements':['Separate boss RNG sample stream from skill RNG.','Preserve per-frame scripted shots, taunt, stealth, slot/all/random/rank targets, shields, decoys, cover and pierce.','Implement HP edge notifications, damage split, invincibility/undying, down/revive and all downstream effects; incoming world definitions remain fail-closed until their paths are implemented.']},
  {'area':'Remaining boss worlds','requirements':['interrupt and targets-cleared, moving geometry and aim, shield/vanish block rules, summons, attack/debuff emissions and lifecycle.']},
  {'area':'Full completion','requirements':['Every current character and favorite stage without omitted source definitions.','Replace static-world INERT assumptions with actual behavior as incoming combat is introduced.','Resolve pinned upstream omissions, including unsupported cubes and parsed stats with no CPU implementation; matching two omissions is not evidence of game correctness.','Verify complete squads, event ordering and normal application GPU execution, with honest scope and no silent CPU fallback classified as GPU success.']}]
 }
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
