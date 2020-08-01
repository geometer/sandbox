from copy import copy

class AbstractRule:
    @classmethod
    def priority(clazz):
        return 2

class SyntheticPropertyRule(AbstractRule):
    __instance = None

    @staticmethod
    def instance():
        if SyntheticPropertyRule.__instance is None:
            SyntheticPropertyRule.__instance = SyntheticPropertyRule()
        return SyntheticPropertyRule.__instance

class PredefinedPropertyRule(AbstractRule):
    __instance = None

    @staticmethod
    def instance():
        if PredefinedPropertyRule.__instance is None:
            PredefinedPropertyRule.__instance = PredefinedPropertyRule()
        return PredefinedPropertyRule.__instance

    @classmethod
    def priority(clazz):
        return 0.5

class Rule(AbstractRule):
    def __init__(self, context):
        self.context = context

    def generate(self):
        for src in self.sources():
            if self.accepts(src):
                for reason in self.apply(src):
                    yield reason

class source_type:
    def __init__(self, property_type):
        from ..property import Property
        assert issubclass(property_type, Property), 'Source type must be subclass of Property'
        self.property_type = property_type

    def __call__(self, clazz):
        assert not hasattr(clazz, 'sources'), 'Cannot use @%s on class with sources() method' % type(self).__name__
        return type(
            clazz.__name__,
            (clazz,),
            {'sources': lambda inst: inst.context.list(self.property_type)}
        )

class source_types:
    def __init__(self, *property_types):
        from ..property import Property
        assert all(issubclass(t, Property) for t in property_types), 'Source type must be subclass of Property'
        self.property_types = property_types

    def sources(self, inst):
        full = []
        for t in self.property_types:
            full += inst.context.list(t)
        return full

    def __call__(self, clazz):
        assert not hasattr(clazz, 'sources'), 'Cannot use @%s on class with sources() method' % type(self).__name__
        return type(
            clazz.__name__,
            (clazz,),
            {'sources': lambda inst: self.sources(inst)}
        )

class processed_cache:
    def __init__(self, cache_object):
        self.cache_object = cache_object

    def __call__(self, clazz):
        return type(
            clazz.__name__,
            (clazz,),
            {'processed_proto': self.cache_object}
        )

def accepts_auto(clazz):
    assert not hasattr(clazz, 'accepts'), 'Cannot use @accepts_auto on class with accepts()'
    return type(
        clazz.__name__,
        (clazz,),
        {'accepts': lambda inst, src: src not in inst.processed}
    )

def create_rule(clazz, context):
    if not hasattr(clazz, 'accepts'):
        def generator(rule):
            for src in rule.sources():
                for reason in rule.apply(src):
                    yield reason
        clazz = type(
            clazz.__name__,
            (clazz,),
            {'generate': lambda inst: generator(inst)}
        )
    obj = clazz(context)
    if hasattr(clazz, 'processed_proto'):
        obj.processed = copy(clazz.processed_proto)
    else:
        print('WARNING: Rule %s has no attribute `processed_proto`' % clazz.__name__)
    return obj
