"""Static views of the existing compiler's attacker-bound team definitions."""
MAGIC=0x57544831
WORDS=520

def bind_compiled(effects,program,names):
 bound=[];sources=[];owners=[];conditions=[];budgets=[]
 for source,indices in enumerate(program['source_rows']):
  for index in indices:
   if index!=len(bound):raise ValueError('Noncontiguous compiler binding order')
   row=program['effects'][index];who=int(row[0]);origin=int(row[268]);budget=int(row[269])
   if not 0<=who<5 or not 0<=origin<=5 or bool(origin)!=bool(budget):raise ValueError('Invalid compiler team binding')
   bound.append((effects[source][0],names[who]));sources.append(source);owners.append(who);conditions.append(origin);budgets.append(budget)
 return bound,dict(binding_source_indices=sources,binding_owners=owners,team_condition_owners=conditions,team_budget_keys=budgets)

def bound_effects(effects,metadata,names):
 indices=metadata.get('binding_source_indices',list(range(len(effects))))
 owners=metadata.get('binding_owners',[names.index(owner) if isinstance(owner,str) else owner for _,owner in effects])
 return [(effects[index][0],names[owner]) for index,owner in zip(indices,owners)]

def compile_policy(metadata,has_parts):
 if type(has_parts) is not bool:raise ValueError('Static has_parts must be boolean')
 origins=metadata['team_condition_owners'];budgets=metadata['team_budget_keys'];count=len(origins)
 if not 1<=count<=256 or len(budgets)!=count:raise ValueError('Team binding capacity exceeded')
 words=[MAGIC,1,count,int(has_parts),0,0,0,0]+[0]*512
 for row,(origin,budget) in enumerate(zip(origins,budgets)):words[8+row*2:10+row*2]=[origin,budget]
 return words
