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
        return 1

class Rule(AbstractRule):
    def __init__(self, context):
        self.context = context

    def generate(self):
        for src in self.sources():
            for reason in self.apply(src):
                yield reason

class SingleSourceRule(Rule):
    def accepts(self, prop):
        return True

    def sources(self):
        return [p for p in self.context.list(type(self).property_type) if self.accepts(p)]
