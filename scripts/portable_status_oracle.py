"""Compare pinned status/application/charge/damage behavior after GPU readback."""
from portable_stack_oracle import compare as compare_carriers

def compare(case,gpu,contains):
 cpu=compare_carriers(case,gpu,contains)
 actual={(e['recipient'],e['name']):e['used'] for e in gpu.get('immunity_usage',[])}
 expected={(e['recipient'],e['name']):e['used'] for e in cpu['immunity_usage']}
 assert actual==expected,(case['name'],'immunity usage',actual,expected)
 if case.get('status_damage_reference'):
  from portable_enemy_oracle import observe as damage_reference
  damage=damage_reference(case);contains(gpu['queries'],damage['queries'],case['name']+'.native-damage');contains(gpu['target_scored_damage'],damage['target_scored_damage'],case['name']+'.native-final-scored-damage');cpu['damage_reference']=damage
 return cpu
