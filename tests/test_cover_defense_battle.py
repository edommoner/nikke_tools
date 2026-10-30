"""Declared cover layer boundaries; no new battle clock, HP bank or GPU claim."""
import ast,copy,hashlib,json,math,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from cover_defense_battle_model import CoverDefense,CoverLanding,LAND_PREFIX,cover_defense,normalize

NAMES=['a','b','c','d','e']
def spec():return [dict(name=n,base_defense=100.*(i+1)) for i,n in enumerate(NAMES)]
class Manager:
    squad_names=NAMES
    def __init__(self):self.percent=0.;self.queries=[];self.breaks=[];self.shield=0.;self.shield_percent=0.;self.events=[]
    def _live_sum(self,name,stat,t):self.events.append('cover-query');self.queries.append((name,stat,t));return self.percent
    def is_down(self,name):return False
    def absorb_shield(self,*args,**kw):self.events.append('shield');self.percent=self.shield_percent;return self.shield
    def break_cover(self,name):self.events.append('break');self.breaks.append(name)

class CoverBattle(unittest.TestCase):
    def test_explicit_bases_roster_and_literals(self):
        good=spec();self.assertEqual(normalize(good,NAMES),dict(zip(NAMES,[100.,200.,300.,400.,500.])))
        for names in (NAMES[:4],NAMES[:4]+['a'],NAMES[:4]+[[]]):
            with self.assertRaises(ValueError):normalize(good,names)
        for base in (True,-1.,1e31,math.inf,math.nan,'100'):
            bad=copy.deepcopy(good);bad[0]['base_defense']=base
            with self.assertRaises(ValueError):normalize(bad,NAMES)
        for change in (dict(name=[]),dict(name='missing'),dict(extra=1)):
            bad=copy.deepcopy(good);bad[0].update(change)
            with self.assertRaises(ValueError):normalize(bad,NAMES)

    def test_live_percentage_order_division_and_no_hp_mutation(self):
        m=Manager();r=CoverDefense(spec(),NAMES);m.percent=128.57
        value=r.layer(m,'a',11.,1000.,100.,20.,3,500.)
        q=max((1000.-100.*(1.+128.57/100.))*100./100.*1.2,1.)
        self.assertEqual(value,q/3);self.assertEqual(m.queries,[('a','cover_def_pct',11.)])
        self.assertEqual(r.data['receipts'][0]['hp_after'],500.-value)
        self.assertEqual(m.breaks,[])
        with self.assertRaises(ValueError):r.layer(Manager(),'a',11.,1000.,100.,20.,3,500.)
        for divisor in (True,0,6,1.5):
            with self.assertRaises(ValueError):r.layer(m,'a',11.,1000.,100.,20.,divisor,500.)

    def landing(self,m,*,pierce=False,hp=5000.,covered=True):
        runtime=CoverDefense(spec(),NAMES);state={'cover_hp':dict.fromkeys(NAMES,hp)}
        tree=ast.parse('def _land_squad(name,dmg,hit,t,*,notify_hit):\n    "original phase"\n'+''.join('    '+s+'\n' for s in LAND_PREFIX.splitlines())+'    return shield,cover\n')
        transformer=CoverLanding();tree=transformer.visit(tree);ast.fix_missing_locations(tree)
        self.assertEqual(transformer.counts,dict(bind=0,percent=0,land=0,signature=1,cover=1))
        cs=SimpleNamespace(in_cover=lambda t:covered,cover_blocked=lambda t,bm:False)
        scope=dict(bm=m,state=state,char_states=dict.fromkeys(NAMES,cs),boss=SimpleNamespace(log_squad=lambda *a:m.events.append('log-break')),_nikke_cover_layer=runtime.layer)
        exec(compile(tree,'<checked-cover-phase>','exec'),scope)
        result=scope['_land_squad']('a',321.,SimpleNamespace(spec=SimpleNamespace(pierce=pierce),pattern='hit'),11.,notify_hit=True,cover_attack=1000.,cover_coefficient=100.,cover_received=0.,cover_divisor=1)
        return runtime,state,result

    def test_cover_queries_after_shield_callbacks_and_retains_original_subtraction(self):
        m=Manager();m.shield_percent=100.
        r,state,result=self.landing(m)
        self.assertEqual(m.events,['shield','cover-query']);self.assertEqual(result,(0.,800.))
        self.assertEqual(state['cover_hp']['a'],4200.);self.assertEqual(r.data['receipts'][0]['effective_defense'],200.)

    def test_shield_gate_pierce_broken_and_break_callback_order(self):
        m=Manager();m.shield=123.
        r,state,result=self.landing(m);self.assertEqual(result,(123.,0.));self.assertEqual(r.data['receipts'],[]);self.assertEqual(m.events,['shield'])
        m=Manager();m.shield=123.
        r,state,result=self.landing(m,pierce=True,hp=500.)
        self.assertEqual(result,(123.,500.));self.assertEqual(state['cover_hp']['a'],0.)
        self.assertEqual(m.events,['shield','cover-query','break','log-break'])
        for kw in (dict(hp=0.),dict(covered=False)):
            m=Manager();r,_,_=self.landing(m,**kw);self.assertEqual(r.data['receipts'],[]);self.assertEqual(m.queries,[])

    def test_phase_reorder_and_signature_changes_fail_closed(self):
        prefix=LAND_PREFIX.replace('shield = bm.absorb_shield(name, dmg, t, pierce=spec.pierce)','shield = 0.0')
        for signature,body in [('name,dmg,hit,t,*,notify_hit',prefix),('name,dmg,hit,t,*,notify_hit=False',LAND_PREFIX)]:
            tree=ast.parse('def _land_squad('+signature+'):\n    "phase"\n'+''.join('    '+s+'\n' for s in body.splitlines()))
            with self.assertRaises(ValueError):CoverLanding().visit(tree)

    def test_received_query_once_and_original_divisor_captured(self):
        tree=ast.parse('''def _boss_attack(name,hit,t,group):
    atk=1000.
    spec=hit.spec
    dmg=atk*(1.+bm.incoming_dmg_pct(name,t)/100.)
    if group:
        share=dmg/len(group)
        for member in group:
            _land_squad(member,share,hit,t,notify_hit=member==name)
    else:
        _land_squad(name,dmg,hit,t,notify_hit=True)
''')
        transform=CoverLanding();tree=transform.visit(tree);ast.fix_missing_locations(tree)
        self.assertEqual(transform.counts,dict(bind=1,percent=1,land=2,signature=0,cover=0))
        calls=[];received=[];m=Manager();m.incoming_dmg_pct=lambda *a:received.append(a) or 20.
        scope=dict(bm=m,_nikke_cover_bind=lambda bm:None,_land_squad=lambda *a,**kw:calls.append((a,kw)))
        exec(compile(tree,'<checked-received>','exec'),scope)
        scope['_boss_attack']('a',SimpleNamespace(spec=SimpleNamespace(coeff=75.)),11.,['a','c','e'])
        self.assertEqual(received,[('a',11.)]);self.assertEqual(len(calls),3)
        for args,kw in calls:self.assertEqual(kw['cover_divisor'],3);self.assertEqual(kw['cover_received'],20.);self.assertEqual(args[1],400.)

    def test_real_aliases_and_globals_restore_even_on_exception(self):
        from calculator import timeline
        from runner import sim
        before=timeline.simulate;self.assertIs(before,sim.simulate)
        with self.assertRaisesRegex(RuntimeError,'intentional'):
            with cover_defense(spec(),NAMES):
                self.assertIs(timeline.simulate,sim.simulate);self.assertIsNot(timeline.simulate,before)
                with self.assertRaises(ValueError):
                    with cover_defense(spec(),NAMES):pass
                raise RuntimeError('intentional')
        self.assertIs(timeline.simulate,before);self.assertIs(sim.simulate,before)
        self.assertNotIn('_nikke_cover_layer',before.__globals__);self.assertNotIn('_nikke_cover_bind',before.__globals__)

    def test_saved_full_battle_receipts_and_corruption_detection(self):
        from portable_cover_defense_battle_contracts import verify
        data=json.loads((ROOT/'tests/fixtures/cover-defense-battle-cpu-v1.json').read_text())
        self.assertFalse(data['gpu_verified']);self.assertEqual(len(data['cases']),4)
        for row in data['cases']:
            self.assertEqual(verify(row['case'],row['native']),row['contract'])
            for field in ('effective_defense','quantity','shared_quantity','divisor','applied','hp_after'):
                bad=copy.deepcopy(row['native']);bad['cover_defense']['receipts'][0][field]+=1
                with self.subTest(case=row['case']['name'],field=field),self.assertRaises(AssertionError):verify(row['case'],bad)
        row=data['cases'][2];bad=copy.deepcopy(row['native'])
        bad['battle']['hits']=[h for h in bad['battle']['hits'] if h['pattern']!='phase-7.5-0']
        with self.assertRaisesRegex(AssertionError,'prior death'):verify(row['case'],bad)

    def test_cli_registration_preserves_declared_reference_boundary(self):
        from portable_reference import REFERENCES
        import nikke_gpu
        self.assertEqual(REFERENCES['cover-defense-common'],('portable_cover_defense_battle_cases','world_cover_defense_battle_native','portable_cover_defense_battle_contracts'))
        self.assertNotIn('cover-defense-common',nikke_gpu.SUITES)
        from portable_readiness_semantics import reference_readiness
        result=reference_readiness(dict(phase='effect',kind='buff',stat='cover_def_pct',target='allies_top_atk:3'))
        self.assertEqual(result['lane'],'reference_model_gap');self.assertFalse(result['gpu_supported'])
        proof=result['declared_cover_defense_battle_cpu'];self.assertTrue(proof['private_cpu_reference_verified'])
        self.assertEqual(proof['evidence_sha256'],hashlib.sha256((ROOT/proof['evidence']).read_bytes()).hexdigest())
        for key in ('gpu_wire_connected','metal_battle_verified','cuda_battle_verified','canonical_default_changed','in_game_rules_verified'):self.assertFalse(proof[key])

if __name__=='__main__':unittest.main()
