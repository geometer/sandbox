class ParametrizedString:
    def __init__(self, format_string, *params):
        self.format_string = format_string
        self.params = params

    def __eq__(self, other):
        return isinstance(other, ParametrizedString) and self.format_string == other.format_string and self.params == other.params

    def __str__(self):
        from .core import CoreScene
        return self.format_string % tuple(p.name if isinstance(p, CoreScene.Object) else p for p in self.params)

def _comment(*args):
    return ParametrizedString(*args)
