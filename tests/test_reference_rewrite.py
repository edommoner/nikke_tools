import ast,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from reference_rewrite import rewrite_reference

def sample(value=4,*,scale=2):
    return value+scale

class Multiply(ast.NodeTransformer):
    def __init__(self):self.counts={'add':0};self.extra_edits=0
    def visit_Add(self,node):
        self.counts['add']+=1;self.extra_edits+=1
        return ast.copy_location(ast.Mult(),node)

class ReferenceRewriteTests(unittest.TestCase):
    def test_composition_retains_prior_edits_and_new_keyword_defaults(self):
        class Offset(ast.NodeTransformer):
            def __init__(self):self.counts={'function':0,'return':0}
            def visit_FunctionDef(self,node):
                node.args.kwonlyargs.append(ast.arg(arg='offset'))
                node.args.kw_defaults.append(ast.Constant(3));self.counts['function']+=1
                return self.generic_visit(node)
            def visit_Return(self,node):
                node.value=ast.BinOp(left=node.value,op=ast.Add(),right=ast.Name(id='offset',ctx=ast.Load()))
                self.counts['return']+=1;return node
        changed=rewrite_reference(sample,Multiply(),{'add':1})
        combined=rewrite_reference(changed,Offset(),{'function':1,'return':1},compose=True)
        self.assertEqual(combined(),11);self.assertEqual(combined(scale=4,offset=1),17)
        self.assertEqual(changed(),8);self.assertEqual(sample(),6)
        with self.assertRaisesRegex(AssertionError,'retained source tree'):
            rewrite_reference(sample,Offset(),{'function':1,'return':1},compose=True)
        from functools import wraps
        @wraps(changed)
        def wrapper(*args,**kwargs):return changed(*args,**kwargs)
        with self.assertRaisesRegex(AssertionError,'retained source tree'):
            rewrite_reference(wrapper,Offset(),{'function':1,'return':1},compose=True)

    def test_source_defaults_and_original_function_are_preserved(self):
        changed=rewrite_reference(sample,Multiply(),{'add':1},{'extra_edits':1})
        self.assertEqual(changed(),8);self.assertEqual(sample(),6)
        self.assertEqual(changed.__code__.co_filename,sample.__code__.co_filename)
        self.assertEqual(changed.__defaults__,sample.__defaults__)
        self.assertEqual(changed.__kwdefaults__,sample.__kwdefaults__)
    def test_missing_or_extra_edits_are_rejected(self):
        with self.assertRaises(AssertionError):rewrite_reference(sample,Multiply(),{'add':2})
        with self.assertRaises(AssertionError):rewrite_reference(sample,Multiply(),{'add':1},{'extra_edits':0})

if __name__=='__main__':unittest.main()
