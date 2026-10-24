"""Geometry uses authored angles and the selected common numeric profile."""
import importlib.util,sys,unittest,math
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_numeric_v1 as n
import coordinate_geometry_reference as ref
from portable_coordinate_geometry_cases import fixtures
s=importlib.util.spec_from_file_location('geometry_adapter',ROOT/'research/verify-coordinate-geometry-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class GeometryTests(unittest.TestCase):
    def test_packing_contains_authored_angle_no_cpu_geometry(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No geometry packing')),patch.object(math,'sin',side_effect=AssertionError('No trig packing')),patch.object(math,'cos',side_effect=AssertionError('No trig packing')):
            entries,raw=a.prepare()
        self.assertEqual(len(entries),1224);self.assertEqual(sum(d is None for _,_,d in entries),15)
        self.assertEqual(len(raw),4+len(entries)*24*4)
        row=next((w,d) for _,w,d in entries if d is not None and d[6]==45. and d[0]==2)
        self.assertEqual(row[0][14:16],a.words64(n.bits(45.)))
    def test_analytic_center_and_external_tangency(self):
        centered=(1,0.,0.,1.,0.,0.,0.,0.,0.,1.,0.)
        e=ref.evaluate(centered);self.assertEqual(e['arcs'],[(0.,n.number(n.TAU))]);self.assertEqual(e['breaks'],[1.,1.])
        tangent=(1,2.,0.,1.,0.,0.,0.,0.,0.,1.,0.)
        self.assertEqual(ref.evaluate(tangent)['arcs'],[])
        rect=(2,0.,0.,0.,2.,2.,90.,0.,0.,.5,0.)
        self.assertEqual(ref.evaluate(rect)['arcs'],[(0.,n.number(n.TAU))])
    def test_circle_acos_split_and_rotation_axes(self):
        e=ref.evaluate((1,1.,0.,1.,0.,0.,0.,0.,0.,1.,0.));half=n.number(n.acos_bits(n.bits(.5)))
        start=n.number(n.TAU)-half
        # Ordered wrap has two additions; algebraically cancelling tau would
        # conceal its three-ULP endpoint rounding in this concrete case.
        self.assertEqual(e['arcs'],[(0.,(start+2.*half)-n.number(n.TAU)),(start,n.number(n.TAU))])
        self.assertEqual(ref.rotation(90.),(0.,1.));self.assertEqual(ref.rotation(450.),ref.rotation(90.))
        self.assertEqual(ref.rotation(-450.),(0.,-1.))
    def test_all_static_cases_finite_sorted_and_rounded_rectangle_breaks(self):
        max_arcs=0
        for name,domain in fixtures():
            e=ref.evaluate(domain);max_arcs=max(max_arcs,len(e['arcs']))
            self.assertEqual(e['arcs'],sorted(e['arcs']),name)
            self.assertTrue(all(0<=start<=end<=n.number(n.TAU) for start,end in e['arcs']),name)
            self.assertTrue(all(e['arcs'][i][1]<e['arcs'][i+1][0] for i in range(len(e['arcs'])-1)),name)
            self.assertEqual(len(e['breaks']),2 if domain[0]==1 else 24 if domain[-1]>0 else 16,name)
        self.assertGreaterEqual(max_arcs,4)
    def test_no_host_transcendentals_or_hypot_in_common_reference(self):
        from contextlib import ExitStack
        ref.evaluate(fixtures()[0][1])
        with ExitStack() as stack:
            for name in ('sin','cos','acos','atan2','hypot','sqrt'):stack.enter_context(patch.object(math,name,side_effect=AssertionError(name)))
            ref.evaluate((2,1.,-2.,0.,6.,2.,45.,0.,0.,2.,.5))
    def test_old_native_distance_and_breaks_preserved_where_policy_does_not_change(self):
        import engine_worker
        from calculator.aim import Shape
        for name,domain in fixtures()[:1080]:
            kind,x,y,r,w,h,rot,ax,ay,rho,grow=domain
            if kind==2 and rot!=0:continue
            shape=Shape(x,y,r,w,h,rot);e=ref.evaluate(domain)
            self.assertEqual(n.bits(e['distance']),n.bits(shape.dist(ax,ay)),name)
            self.assertEqual(e['breaks'],shape.breaks(ax,ay,grow),name)
    def test_intermediate_overflow_and_underflow_explicit_rejection(self):
        entries,_=a.prepare()
        for name,w,d in entries:
            if name.rsplit('/',1)[-1] not in ('overflow-delta','overflow-square','underflow-denominator'):continue
            values=(w[2],*(n.number(w[i]|w[i+1]<<32) for i in range(4,24,2)))
            with self.subTest(name=name),self.assertRaises(ValueError):ref.evaluate(values)
    def test_all_output_lanes_are_compared(self):
        domain=(2,1.,-2.,0.,6.,2.,45.,0.,0.,2.,.5);w,e=a.expected(domain);a.compare(w,domain)
        for at in [0,3,4,6,7,8,10,12,14,16,4112,4159]:
            other=list(w);other[at]^=1
            with self.subTest(at=at),self.assertRaises(AssertionError):a.compare(other,domain)
        a.validate_rejection([64]+[0]*4159,'reject/coordinate-common-geometry/test')
    def test_arc_interiors_and_gaps_against_independent_decimal_geometry(self):
        from decimal import Decimal,localcontext
        from coordinate_decimal_oracle import pi,sincos
        checked=0
        # Independent squared-distance classification; no common hypot,
        # atan2/acos, arc generation, or distance helper is used here.
        for name,domain in fixtures()[1080:]:
            kind,x,y,r,w,h,rot,ax,ay,rho,grow=domain;e=ref.evaluate(domain)
            intervals=e['arcs'];segments=[(s,t,True) for s,t in intervals]
            ends=[0.]+[v for pair in intervals for v in pair]+[n.number(n.TAU)]
            segments += [(ends[i],ends[i+1],False) for i in range(0,len(ends)-1,2)]
            with localcontext() as ctx:
                ctx.prec=90;D=Decimal.from_float
                sr,cr=sincos(D(rot)*pi()/180)
                for start,end,inside in segments:
                    if end-start<1e-10:continue
                    s,c=sincos(D(start+(end-start)/2));px=D(ax)+D(rho)*c-D(x);py=D(ay)+D(rho)*s-D(y)
                    if kind==1:delta=px*px+py*py-(D(r)+D(grow))**2
                    else:
                        lx=px*cr+py*sr;ly=-px*sr+py*cr
                        ex=max(abs(lx)-D(w)/2,Decimal(0));ey=max(abs(ly)-D(h)/2,Decimal(0));delta=ex*ex+ey*ey-D(grow)**2
                    if abs(delta)<Decimal('1e-18'):continue
                    self.assertEqual(delta<0,inside,(name,start,end));checked+=1
        self.assertGreater(checked,200)
if __name__=='__main__':unittest.main()
