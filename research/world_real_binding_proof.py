"""Project immutable compiler binding identities; never change native quantities."""
import copy

def binding_view(prepared,native,metadata):
 indices=metadata['binding_source_indices'];owners=metadata['binding_owners'];names=[c['name'] for c in prepared['chars']]
 if len(indices)!=len(owners):raise ValueError('Compiler binding dimensions differ')
 p=copy.deepcopy(prepared);cpu=copy.deepcopy(native)
 p['effects']=[dict(effect=copy.deepcopy(prepared['effects'][source]['effect']),owner=names[who]) for source,who in zip(indices,owners)]
 for mode in cpu.get('active_weapon_modes',[]):
  choices=[i for i,(source,who) in enumerate(zip(indices,owners)) if source==mode['definition'] and who==mode['owner']]
  if len(choices)!=1:raise ValueError('Native weapon mode has no unique compiler binding')
  mode['definition']=choices[0]
 return p,cpu
