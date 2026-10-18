"""Checked source rewriting shared by the existing CPU recovery extensions.

The caller supplies its own semantic transformer. This utility preserves source
locations/defaults and refuses an unexpected number of edits; it does not infer
new gameplay rules or change wrapper installation order.
"""
import ast,copy,inspect,textwrap
from types import CodeType


def referenced_names(fn):
    """Names in a checked executor and its nested code, without executing it."""
    def walk(code):
        names=set(code.co_names)
        for value in code.co_consts:
            if isinstance(value,CodeType):names.update(walk(value))
        return names
    return walk(fn.__code__)


def compile_reference_helper(fn,node):
    """Compile one extracted checked executor once, in its original namespace."""
    first=fn._nikke_reference_first
    tree=ast.Module(body=[copy.deepcopy(node)],type_ignores=[])
    ast.fix_missing_locations(tree);retained=copy.deepcopy(tree)
    ast.increment_lineno(tree,first-1);scope={}
    exec(compile(tree,inspect.getsourcefile(fn),'exec'),fn.__globals__,scope)
    helper=scope[node.name]
    helper._nikke_reference_tree=retained;helper._nikke_reference_first=first;helper._nikke_reference_code=helper.__code__
    return helper

def rewrite_reference(fn,transformer,expected_counts,expected_attributes=None,*,compose=False):
    if compose:
        if getattr(fn,'_nikke_reference_code',None) is not fn.__code__:
            raise AssertionError((fn.__name__,'No matching retained source tree for composition'))
        first=fn._nikke_reference_first
        tree=copy.deepcopy(fn._nikke_reference_tree)
    else:
        lines,first=inspect.getsourcelines(fn)
        tree=ast.parse(textwrap.dedent(''.join(lines)))
    tree=transformer.visit(tree)
    if transformer.counts!=expected_counts:
        raise AssertionError((fn.__name__,transformer.counts,expected_counts))
    for name,value in (expected_attributes or {}).items():
        if getattr(transformer,name)!=value:
            raise AssertionError((fn.__name__,name,getattr(transformer,name),value))
    ast.fix_missing_locations(tree)
    retained=copy.deepcopy(tree)
    ast.increment_lineno(tree,first-1)
    scope={}
    exec(compile(tree,inspect.getsourcefile(fn),'exec'),fn.__globals__,scope)
    result=scope[fn.__name__]
    result.__defaults__=fn.__defaults__
    keyword_defaults=dict(result.__kwdefaults__ or {})
    keyword_defaults.update(fn.__kwdefaults__ or {})
    result.__kwdefaults__=keyword_defaults or None
    result._nikke_reference_tree=retained
    result._nikke_reference_first=first
    result._nikke_reference_code=result.__code__
    return result
