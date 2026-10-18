"""Observe CPU at the actual frame end, before EOF flush, without gameplay queries."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
for f in ['research/detail-boss-buffs-native-verification.json','research/detail-boss-buffs-native-verification.log','research/detail-boss-buffs-tests.log']:
 p=ROOT/f;dst=p.with_name(p.stem+'-before-observer-alignment'+p.suffix);assert not dst.exists();shutil.copy2(p,dst)
p=ROOT/'scripts/verify-boss-clock-detail.py';s=p.read_text(encoding='utf-8')
s=s.replace('import argparse,copy,hashlib,importlib.util,json,random,sys','import argparse,copy,hashlib,importlib.util,json,random,sys,ast,inspect,textwrap')
old='''        def observed(self,at,enemy):
            events=original(self,at,enemy)
            runs=[self._run_by_id[id] for id in ids]
            frames[at]=dict(time=at,core=enemy['core_px'],distance=-1 if enemy.get('distance') is None else enemy['distance'],weapon_mask=sum(1<<WEAPONS.index(w) for w in set(enemy.get('optimal_range_weapons') or [])),log_count=sum(e.pattern in ids and e.event in ('start','end','dispel') for e in self.log),active_mask=sum(1<<i for i,r in enumerate(runs) if r.active),opens=[r.opens for r in runs],defense=enemy["def"],dispelled_mask=sum(1<<i for i,r in enumerate(runs) if r.dispelled))
            return events
        with patch.object(BossScript,'begin_frame',observed),patch.object(BuffManager,'notify_team_hit',hit):cpu=a.evaluate(body)'''
new='''        from calculator import timeline
        lines,first=inspect.getsourcelines(timeline.simulate)
        tree=ast.parse(textwrap.dedent(''.join(lines)))
        # Bind to the pinned engine's actual time advance, not an approximate
        # callback before shooting or its post-battle projectile flush.
        advances=[n for n in ast.walk(tree) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='t' and isinstance(n.value,ast.Name) and n.value.id=='DT']
        assert len(advances)==1
        end_line=first+advances[0].lineno-1;code=timeline.simulate.__code__
        def observed(frame,event,arg):
            if frame.f_code is not code:return None
            if event=='line' and frame.f_lineno==end_line:
                local=frame.f_locals;boss=local['boss'];at=local['t'];enemy=local['enemy']
                runs=[boss._run_by_id[id] for id in ids]
                frames[at]=dict(time=at,core=enemy['core_px'],distance=-1 if enemy.get('distance') is None else enemy['distance'],weapon_mask=sum(1<<WEAPONS.index(w) for w in set(enemy.get('optimal_range_weapons') or [])),log_count=sum(e.pattern in ids and e.event in ('start','end','dispel') for e in boss.log),active_mask=sum(1<<i for i,r in enumerate(runs) if r.active),opens=[r.opens for r in runs],defense=enemy['def'],dispelled_mask=sum(1<<i for i,r in enumerate(runs) if r.dispelled))
            return observed
        previous_trace=sys.gettrace()
        try:
            with patch.object(BuffManager,'notify_team_hit',hit):
                sys.settrace(observed);cpu=a.evaluate(body)
        finally:sys.settrace(previous_trace)'''
assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
