"""Stat-keyed process memos retain content guards and never pin source hashes."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import portable_file_identity as facts
import portable_slang_generation as gen
import portable_native as native


class FileIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        facts._values.clear();gen._source_cache.clear()

    def test_digest_hit_and_each_stat_component_invalidates(self):
        p=self.root/'file';p.write_bytes(b'abc')
        original=Path.read_bytes
        with patch.object(Path,'read_bytes',autospec=True,side_effect=original) as read:
            self.assertEqual(facts.file_digest(p),facts.file_digest(p));self.assertEqual(read.call_count,1)
            for index in range(4):
                saved=facts.stamp(p);changed=list(saved);changed[index]+=1
                with patch.object(facts,'stamp',return_value=tuple(changed)):
                    self.assertEqual(facts.file_digest(p),hashlib.sha256(b'abc').hexdigest())
                self.assertEqual(read.call_count,2+index)
        p.write_bytes(b'xyz');self.assertEqual(facts.file_digest(p),hashlib.sha256(b'xyz').hexdigest())
        q=self.root/'replacement';q.write_bytes(b'xyz');q.replace(p)
        self.assertEqual(facts.file_digest(p),hashlib.sha256(b'xyz').hexdigest())

    def test_unstable_read_is_never_cached(self):
        p=self.root/'file';p.write_text('a')
        def mutate(p):p.write_text('longer');return 1
        with self.assertRaisesRegex(RuntimeError,'changed'):facts.file_value(p,'test',mutate)
        self.assertEqual(facts.file_value(p,'test',lambda p:2),2)

    def test_graph_hits_and_transitive_change_and_symlink(self):
        (self.root/'entry').write_text('#include "edge"\n')
        a=self.root/'a';a.write_text('#include "leaf"\n')
        leaf=self.root/'leaf';leaf.write_text('one')
        (self.root/'edge').symlink_to(a)
        first=gen.source_hashes(self.root,'entry')
        first['a']='caller mutation'
        with patch.object(Path,'resolve',side_effect=AssertionError('walk on hit')):
            second=gen.source_hashes(self.root,'entry')
        self.assertNotEqual(first,second)
        leaf.write_text('two');self.assertNotEqual(second,gen.source_hashes(self.root,'entry'))
        b=self.root/'b';b.write_text('new')
        # Atomic replacement of a lexical include edge to another target.
        edge=self.root/'new-edge';edge.symlink_to(b);edge.replace(self.root/'edge')
        self.assertIn('b',gen.source_hashes(self.root,'entry'))

    def test_compiler_identities_hit_and_change(self):
        p=self.root/'compiler';p.write_bytes(b'compiler')
        with patch.object(subprocess,'check_output',return_value=b'version') as call:
            a=gen.cpp_compiler_identity(p);a['sha256']='caller mutation'
            self.assertNotEqual(a,gen.cpp_compiler_identity(p));self.assertEqual(call.call_count,1)
            p.write_bytes(b'changed');gen.cpp_compiler_identity(p);self.assertEqual(call.call_count,2)

    def test_generation_validation_and_hash_hit_then_tamper(self):
        p=self.root/'entry';p.write_text('// source')
        with patch.object(gen,'cpp_compiler_identity',return_value={}),patch.object(gen.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'// good',b'')) as compile,patch.object(gen,'validate_counter_snapshots',wraps=gen.validate_counter_snapshots) as validate:
            output,_=gen.build(self.root,'entry','portableEvents')
            gen.build(self.root,'entry','portableEvents')
            gen.build(self.root,'entry','portableEvents')
            self.assertEqual(compile.call_count,1);self.assertEqual(validate.call_count,2)
            cpp=output['cpp'];cpp.write_text('// tampered')
            gen.build(self.root,'entry','portableEvents')
            self.assertEqual(compile.call_count,2);self.assertEqual(validate.call_count,3)
            p.write_text('// changed source')
            gen.build(self.root,'entry','portableEvents');self.assertEqual(compile.call_count,3)

    def test_clang_version_stat_hit_and_change(self):
        p=self.root/'compiler';p.write_text('one')
        # Fail immediately after obtaining version, avoiding a real compiler.
        with patch.object(native,'clang_compiler',return_value=str(p)),patch.object(subprocess,'check_output',return_value=b'version') as call:
            for _ in range(2):
                with self.assertRaises(FileNotFoundError):native.build_host(self.root,self.root/'missing')
            self.assertEqual(call.call_count,1)
            p.write_text('two')
            with self.assertRaises(FileNotFoundError):native.build_host(self.root,self.root/'missing')
            self.assertEqual(call.call_count,2)

    def test_host_generated_source_and_binary_hashes_hit_and_invalidate(self):
        (self.root/'scripts').mkdir()
        source=self.root/'scripts/native-product-host.cpp';source.write_text('// host')
        cpp=self.root/'kernel.cpp';cpp.write_text('// kernel')
        compiler=self.root/'compiler';compiler.write_text('// compiler')
        def build(command,**kwargs):
            Path(command[-1]).write_bytes(b'binary')
            return subprocess.CompletedProcess(command,0,'','')
        with patch.object(native,'clang_compiler',return_value=str(compiler)),patch.object(subprocess,'check_output',return_value=b'version') as version,patch.object(subprocess,'run',side_effect=build) as compile:
            host,first=native.build_host(self.root,cpp)
            self.assertFalse(first['cache_hit'])
            _,again=native.build_host(self.root,cpp)
            self.assertTrue(again['cache_hit']);self.assertEqual(compile.call_count,1)
            host.write_bytes(b'tampered binary')
            _,again=native.build_host(self.root,cpp)
            self.assertFalse(again['cache_hit']);self.assertEqual(compile.call_count,2)
            cpp.write_text('// changed kernel')
            changed,_=native.build_host(self.root,cpp)
            self.assertNotEqual(host,changed);self.assertEqual(compile.call_count,3)
            source.write_text('// changed host')
            native.build_host(self.root,cpp);self.assertEqual(compile.call_count,4)
            self.assertEqual(version.call_count,1)
