import copy
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('portable_combat_verify',ROOT/'scripts/verify-portable-combat.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from portable_specs import LIMITS as L,check_schema


class CombatBoundaryTests(unittest.TestCase):
    def test_shared_authored_cases_pack_without_mutation(self):
        check_schema()
        for case in v.fixtures():
            before=copy.deepcopy(case);words,meta=v.compile_case(case)
            self.assertEqual(len(words),L['INPUT_WORDS']);self.assertEqual(meta['combat'] is not None,'combat' in case)
            self.assertEqual(case,before)

    def test_unported_mechanics_and_invalid_target_identity_fail_closed(self):
        base=v.fixtures()[0]
        changes=[('weapon',dict(mode='manual')),('weapon',dict(pellets=65)),('weapon',dict(toggle=True)),
                 ('weapon',dict(stage=5)),('weapon',dict(rate=3)),('weapon',dict(rate_max=3)),
                 ('weapon',dict(warmup=0)),('weapon',dict(clip_count=0)),('weapon',dict(clip_count=1.5)),
                 ('weapon',dict(core_diameter=1)),('weapon',dict(min_cycle=float('nan'))),
                 ('weapon',dict(gauge_mult=-1)),('weapon',dict(core_mult=True)),('weapon',dict(full_charge_mult=-1)),
                 ('weapon',dict(full_charge_mult=True)),('weapon',dict(optimal=1)),('weapon',dict(element_match=1)),('weapon',dict(capacity=True)),('weapon',dict(interval=0)),
                 ('weapon',dict(reload=float('nan'))),('weapon',dict(mode='charge',charge=2,interval=1)),
                 ('target',dict(kind=1)),('target',dict(kind=5)),('target',dict(generation=0)),
                 ('target',dict(identity=True)),('target',dict(hp=0)),('target',dict(shield=1))]
        for kind,patch in changes:
            c=copy.deepcopy(base);c['combat']['weapons' if kind=='weapon' else 'targets'][0].update(patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError):v.compile_case(c)
        c=copy.deepcopy(base);c['combat']['weapons'].pop()
        with self.assertRaises(ValueError):v.compile_case(c)
        c=copy.deepcopy(base);c['combat']['targets'] += [dict(kind=5,identity=9,hp=1)]*2
        with self.assertRaises(ValueError):v.compile_case(c)

    def test_unported_mode_mechanics_fail_before_gpu(self):
        base=next(c for c in v.fixtures() if c['name']=='mode-duration-restores-base')
        for patch in (dict(full_charge_mult=float('nan')),dict(fire_rate_max=8),dict(entry_reload=True),
                      dict(max_ammo_buff_applies=True),dict(duration_bullets=2),dict(tick_interval=.1),
                      dict(duration=-1,trigger=dict(timing=['passive'],condition=['during_full_burst']))):
            c=copy.deepcopy(base);c['effects'][1].update(patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError):v.compile_case(c)

    def test_wire_regions_do_not_overlap_or_exceed_transport_capacity(self):
        inputs=[(0,32),(L['DEFINITION_BASE'],L['DEFINITIONS']*L['DEFINITION_WORDS']),
                (L['COMMAND_BASE'],L['COMMANDS']*8),(L['WEAPON_BASE'],5*L['WEAPON_WORDS']),
                (L['TARGET_BASE'],8*L['TARGET_WORDS']),
                (L['WEAPON_EXTRA_BASE'],5*4),(L['MODE_BASE'],L['DEFINITIONS']*L['MODE_WORDS']),
                (L['EVENT_BASE'],L['DEFINITIONS']*L['EVENT_WORDS']),
                (L['CONDITION_BASE'],L['DEFINITIONS']*L['CONDITION_WORDS']),
                (L['ATTACK_CONTEXT_BASE'],5),(L['WEAPON_MECHANICS_BASE'],5*L['WEAPON_MECHANICS_WORDS']),
                (L['MODE_TIMING_BASE'],L['DEFINITIONS']*L['MODE_TIMING_WORDS']),
                (L['DEFINITION_EXTRA_BASE'],L['DEFINITIONS']*L['DEFINITION_EXTRA_WORDS']),
                (L['WEAPON_QUANTITY_BASE'],5*L['WEAPON_QUANTITY_WORDS'])]
        outputs=[(0,16),(L['QUERY_BASE'],L['COMMANDS']*L['QUERY_WORDS']),
                 (L['TRACE_BASE'],L['TRACE']*L['TRACE_WORDS']),(L['STATE_BASE'],L['DEFINITIONS']*10),
                 (L['TIMER_TARGET_BASE'],L['DEFINITIONS']*2),(L['BURST_TRACE_BASE'],64*8),
                 (L['COMBAT_QUERY_BASE'],L['COMMANDS']*L['COMBAT_QUERY_WORDS']),
                 (L['TARGET_STATE_BASE'],8*10),
                 (L['COMBAT_STATE_QUERY_BASE'],L['COMMANDS']*L['COMBAT_STATE_QUERY_WORDS']),
                 (L['WEAPON_STATE_BASE'],5*L['WEAPON_STATE_WORDS']),(L['COUNTER_STATE_BASE'],L['DEFINITIONS']*8),(L['PERIOD_STATE_BASE'],L['DEFINITIONS']*4)]
        for regions,capacity in [(inputs,L['INPUT_WORDS']),(outputs,L['OUTPUT_WORDS'])]:
            end=0
            for start,size in sorted(regions):
                self.assertGreaterEqual(start,end);end=start+size
            self.assertLessEqual(end,capacity);self.assertLessEqual(capacity,16384)

    def test_accuracy_requires_geometry_instead_of_reusing_static_probability(self):
        c=copy.deepcopy(v.fixtures()[0]);c['effects'][0]['stat']='accuracy_pct'
        with self.assertRaises(ValueError):v.compile_case(c)

    def test_frames_accept_no_precomputed_shot_or_state_payload(self):
        for op,arg,payload in [(4,1,0),(4,0,100),(20,8,0),(21,0,0),(22,8,0)]:
            c=copy.deepcopy(v.fixtures()[0]);c['script']=[[0,op,0,0,arg,-1,payload,0]]
            with self.subTest(op=op,arg=arg,payload=payload),self.assertRaises(ValueError):v.compile_case(c)
        for times in ([1],[0,0]):
            c=copy.deepcopy(v.fixtures()[0]);c['script']=[[t,4,0,0,0,-1,0,0] for t in times]
            with self.subTest(times=times),self.assertRaises(ValueError):v.compile_case(c)
        c=copy.deepcopy(v.fixtures()[0]);c['script']=[[0,0,0,0,0,-1,0,0]]
        with self.assertRaises(ValueError):v.compile_case(c)


if __name__=='__main__':unittest.main()
