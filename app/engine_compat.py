"""Narrow integration fixes; pinned upstream source files stay unmodified."""
from functools import wraps


class CharacterLookup(dict):
    """Unknown list targets use the logger's existing caster fallback.

    BuffManager's instant logger probes a raw target against its name mapping.
    Its resolver supports ordered lists, but Python dict membership cannot hash
    them. All string name lookups and the actual target resolver are unchanged.
    """

    def __contains__(self, name):
        if isinstance(name, list):
            return False
        return super().__contains__(name)


def install():
    from effect_overrides import install as install_overrides
    install_overrides()
    from effect_spec import install_reference_layers
    from protection_runtime import install as install_protection
    from calculator.buff_manager import BuffManager as RuntimeManager
    if not getattr(RuntimeManager,'_nikke_lifecycle_runtime',False):install_protection()
    install_reference_layers()
    from reference_count_runtime import install as install_reference_count
    install_reference_count()
    from effect_runtime import install_adapter
    install_adapter()
    from reference_health_runtime import install as install_reference_health
    install_reference_health()
    from calculator.buff_manager import BuffManager
    if getattr(BuffManager.__init__, '_nikke_list_logging_compat', False):
        return
    original = BuffManager.__init__

    @wraps(original)
    def initialize(self, *args, **kwargs):
        original(self, *args, **kwargs)
        self._char = CharacterLookup(self._char)

    initialize._nikke_list_logging_compat = True
    BuffManager.__init__ = initialize
