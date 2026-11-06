"""Synchronize reference/stack-driven maximum HP at outer execution boundaries.
Grants retain native named/stack-child ordering. Crossings observe one actor at
one time; a silent final pass publishes child-mutated rates without edge reentry.
"""
from functools import wraps
HP_STATS=frozenset({'max_hp_pct','max_hp_only_pct','hp_caster_based_pct','hp_only_caster_based_pct'})

def is_reference_health(effect):
    return effect.get('type')=='buff' and effect.get('stat') in HP_STATS and effect.get('scaling')=='stack_count' and bool(effect.get('scaling_ref'))

def enabled(manager):
    result=getattr(manager,'_nikke_reference_health_defined',None)
    if result is None:
        effects=[e for e,_ in manager._effects]
        stack_changes=any(e.get('stat') in ('buff_stack_add','buff_stack_remove','buff_stack_init','buff_max_stack_add','debuff_stack_add','debuff_stack_remove','debuff_cleanse') for e in effects)
        observed_hp=HP_STATS | ({'max_hp_from_max_hp_pct'} if any(e.get('stat')=='debuff_cleanse' for e in effects) else set())
        protection_health=any(e.get('type')=='buff' and e.get('stat') in HP_STATS|{'max_hp_from_max_hp_pct'} and 'during_shield' in e.get('trigger',{}).get('condition',[]) for e in effects)
        # Ordinary finite HP effects also need the existing boundary sync:
        # expiration must not leave stored current HP above the new maximum.
        finite_health=any(e.get('type')=='buff' and e.get('stat') in HP_STATS and e.get('duration',-1) not in (-1,None) for e in effects)
        result=finite_health or protection_health or any(is_reference_health(e) for e in effects) or stack_changes and any(e.get('type')=='buff' and e.get('stat') in observed_hp for e in effects)
        manager._nikke_reference_health_defined=result
    return result

def synchronize(manager,t):
    hp=manager.state.get('hp')
    if not hp or getattr(manager,'_nikke_reference_health_syncing',False):return
    previous_time=manager._cur_t;manager._cur_t=t;manager._nikke_reference_health_syncing=True
    def actor(name):
        if name not in hp:return
        if manager.is_down(name):hp[name]=0;manager.state['hp_pct'][name]=0;return
        maximum=manager.effective_max_hp(name)
        if maximum<=0:return
        hp[name]=max(0.0,min(hp[name],maximum));manager.sync_hp(name)
    try:
        for name in manager.squad_names:actor(name)
        # Native sync_hp suppresses edge recursion while delivering crossings.
        # A callback can mutate another reference; publish the final derived
        # state under the same suppression, after all crossing observers finish.
        guard=manager._in_hp_edge;manager._in_hp_edge=True
        try:
            for name in manager.squad_names:actor(name)
        finally:manager._in_hp_edge=guard
    finally:
        manager._nikke_reference_health_syncing=False;manager._cur_t=previous_time

def execute(manager,t,callback):
    if not enabled(manager):return callback()
    depth=getattr(manager,'_nikke_reference_health_depth',0);previous_time=manager._cur_t
    manager._cur_t=t;manager._nikke_reference_health_depth=depth+1
    try:
        if depth==0:synchronize(manager,t)
        result=callback()
        if depth==0:synchronize(manager,t)
        return result
    finally:
        manager._nikke_reference_health_depth=depth;manager._cur_t=previous_time

def install():
    from calculator.buff_manager import BuffManager
    if getattr(BuffManager,'_nikke_reference_health',False):return
    from protection_runtime import install_health_gate
    install_health_gate()
    original_notify=BuffManager.notify;original_activate=BuffManager._activate
    original_dispatch=BuffManager._dispatch_instant;original_tick=BuffManager.tick
    original_damage=BuffManager.register_damage_handler;original_reset=BuffManager.reset
    original_sync=BuffManager.sync_hp
    original_max_hp=BuffManager.effective_max_hp
    # Retain all installed per-entry semantics (query exclusions, shield gates,
    # and future checked compatibility edits), changing only the loop iterable.
    import ast,copy
    from reference_rewrite import compile_reference_helper
    node=copy.deepcopy(original_max_hp._nikke_reference_tree.body[0])
    loops=[n for n in ast.walk(node) if isinstance(n,ast.For)
           and isinstance(n.iter,ast.Attribute) and n.iter.attr=='_active']
    if len(loops)!=1:raise AssertionError('Unexpected maximum HP loop')
    loop=loops[0]
    # Check every pre-dispatch statement, including installed app gates. For
    # unrelated stats the shield gate short-circuits before any runtime call.
    expected=ast.parse('''if ab.effect.get('stat') in {'max_hp_pct','max_hp_only_pct','hp_caster_based_pct','hp_only_caster_based_pct','max_hp_from_max_hp_pct','hp_copy'} and name in (ab.target_chars or []) and (query_scope is None or not query_scope.excludes(ab)) and ab.has_runtime_conditions and 'during_shield' in ab.effect.get('trigger',{}).get('condition',[]) and not self._runtime_condition_ok(ab.effect['trigger']['condition'],ab.caster,name,name,self._cur_t):
 continue
if query_scope is not None and query_scope.excludes(ab):
 continue
stat=ab.effect.get('stat','')
if name not in (ab.target_chars or []):
 continue
''').body
    if (not isinstance(loop.target,ast.Name) or loop.target.id!='ab' or loop.orelse
            or len(loop.body)!=5 or
            [ast.dump(n) for n in loop.body[:4]]!=[ast.dump(n) for n in expected]):
        raise AssertionError('Unexpected maximum HP loop prelude')
    # Only a chain of stat tests may dispatch work. Derive its complete set;
    # reject any unguarded/default work, rather than silently dropping it.
    hp_stats=set();branch=loop.body[4];branches=0
    while True:
        if not isinstance(branch,ast.If):raise AssertionError('Unexpected maximum HP dispatch')
        branches+=1
        test=branch.test
        if (not isinstance(test,ast.Compare) or not isinstance(test.left,ast.Name)
                or test.left.id!='stat' or len(test.ops)!=1 or len(test.comparators)!=1):
            raise AssertionError('Unexpected maximum HP stat test')
        value=test.comparators[0]
        if isinstance(test.ops[0],ast.Eq):values=[value]
        elif isinstance(test.ops[0],ast.In) and isinstance(value,(ast.Tuple,ast.List,ast.Set)):values=value.elts
        else:raise AssertionError('Unexpected maximum HP stat comparison')
        if not values or any(not isinstance(v,ast.Constant) or not isinstance(v.value,str) for v in values):
            raise AssertionError('Unexpected maximum HP stat literal')
        hp_stats.update(v.value for v in values)
        if not branch.orelse:break
        if len(branch.orelse)!=1:raise AssertionError('Unexpected maximum HP default branch')
        branch=branch.orelse[0]
    # There must be no additional stat comparisons hidden inside contributions.
    comparisons=[n for n in ast.walk(loop) if isinstance(n,ast.Compare)
                 and isinstance(n.left,ast.Name) and n.left.id=='stat']
    if len(comparisons)!=branches:raise AssertionError('Unexpected nested maximum HP stat test')
    hp_stats=frozenset(hp_stats)
    from damage_query_runtime import DamageQueryScope
    # The built-in exclusion is a pure name/caster predicate. Custom scopes
    # may observe visits to unrelated entries, so preserve their original loop.
    import inspect,textwrap
    exclusion=ast.parse(textwrap.dedent(inspect.getsource(DamageQueryScope.excludes))).body[0]
    if ast.dump(exclusion.body[0])!=ast.dump(ast.parse(
            "return carrier.caster == self.owner and carrier.effect.get('name') in self.excluded_names").body[0]) or len(exclusion.body)!=1:
        raise AssertionError('Unexpected maximum HP query exclusion')
    node.name='_indexed_max_hp'
    node.args.kwonlyargs.append(ast.arg(arg='_hp_entries'))
    node.args.kw_defaults.append(ast.Constant(None))
    loop.iter=ast.Name(id='_hp_entries',ctx=ast.Load())
    indexed_max_hp=compile_reference_helper(original_max_hp,node)
    # Share the actual index lifetime: every clear/replacement of _stat_index
    # also discards this list. The private object key cannot alias a stat string.
    hp_entries_key=object()
    @wraps(original_max_hp)
    def effective_max_hp(self,name,*,query_scope=None):
        # Preserve direct unbound calls with minimal reference-test managers.
        if not hasattr(self,'_by_stat') or (query_scope is not None and type(query_scope) is not DamageQueryScope):
            return original_max_hp(self,name,query_scope=query_scope)
        entries=self._stat_index.get(hp_entries_key)
        if entries is None:
            entries=[ab for ab in self._active if ab.effect.get('stat','') in hp_stats]
            self._stat_index[hp_entries_key]=entries
        if not entries:
            base_hp=self.state.get('base_stats',{}).get(name,{}).get('hp',0.0)
            return base_hp * (1.0 + 0.0 / 100.0) + 0.0
        return indexed_max_hp(self,name,query_scope=query_scope,_hp_entries=entries)
    @wraps(original_notify)
    def notify(self,event,t,caster,*args,**kwargs):
        return execute(self,t,lambda:original_notify(self,event,t,caster,*args,**kwargs))
    @wraps(original_activate)
    def activate(self,effect,caster,t,*args,**kwargs):
        if is_reference_health(effect):self._nikke_reference_health_defined=True
        return execute(self,t,lambda:original_activate(self,effect,caster,t,*args,**kwargs))
    @wraps(original_dispatch)
    def dispatch(self,effect,caster,t,*args,**kwargs):
        return execute(self,t,lambda:original_dispatch(self,effect,caster,t,*args,**kwargs))
    @wraps(original_tick)
    def tick(self,t,*args,**kwargs):
        if enabled(self):synchronize(self,t)
        result=original_tick(self,t,*args,**kwargs)
        if enabled(self):synchronize(self,t)
        return result
    @wraps(original_damage)
    def register_damage(self,handler):
        if handler is None:return original_damage(self,None)
        @wraps(handler)
        def damage(effect,caster,t,*args,**kwargs):
            return execute(self,t,lambda:handler(effect,caster,t,*args,**kwargs))
        return original_damage(self,damage)
    @wraps(original_sync)
    def sync_hp(self,name):
        hp=self.state.get('hp',{}).get(name)
        seen=getattr(self,'_nikke_numeric_hp_seen',None)
        if seen is None:seen={};self._nikke_numeric_hp_seen=seen
        if hp is not None and (name not in seen or seen[name]!=hp):
            seen[name]=hp;self._bump_value_version()
        return original_sync(self,name)
    @wraps(original_reset)
    def reset(self,*args,**kwargs):
        self._nikke_reference_health_defined=None;self._nikke_reference_health_depth=0;self._nikke_numeric_hp_seen={}
        return original_reset(self,*args,**kwargs)
    BuffManager.notify=notify;BuffManager._activate=activate;BuffManager._dispatch_instant=dispatch
    BuffManager.tick=tick;BuffManager.register_damage_handler=register_damage;BuffManager.reset=reset
    BuffManager.sync_hp=sync_hp
    BuffManager.effective_max_hp=effective_max_hp
    BuffManager._nikke_reference_health=True
