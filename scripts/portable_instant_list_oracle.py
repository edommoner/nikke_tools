"""Actual native handlers; comparisons run only after GPU readback."""
import copy
from portable_protection_oracle import observe as protection_observe
from portable_burst_oracle import observe as burst_observe

def observe(case):
 if 'combat' in case:
  selected=copy.deepcopy(case)
  if case.get('instant_list_weapon_observer'):selected['ammo_reference']=True
  return burst_observe(selected)
 return protection_observe(case)
def compare(case,gpu,contains):
 native=observe(case)
 if 'combat' in case:
  contains(gpu['queries'],native['queries'],case['name']+'.native');return native
 assert len(gpu['queries'])==len(native['queries'])
 for i,(actual,expected) in enumerate(zip(gpu['queries'],native['queries'])):
  expected=dict(expected)
  if 'protection' not in actual:
   assert all(not any(row.values()) for row in expected['protection']);expected.pop('protection')
  contains(actual,expected,case['name']+'.native.query'+str(i))
 active=[c for c in gpu['carriers'] if c['active']];assert len(active)==len(native['carriers']),(case['name'],'carrier count')
 for i,(actual,expected) in enumerate(zip(active,native['carriers'])):
  expected=dict(expected)
  if 'protection' not in actual:assert not expected.pop('protection')
  contains(actual,expected,case['name']+'.native.carrier'+str(i))
 if 'protection_hits' in gpu:
  assert len(gpu['protection_hits'])==len(native['hits']);contains(gpu['protection_hits'],native['hits'],case['name']+'.native.hits')
 return native
