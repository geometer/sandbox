class Rule:
    def __init__(self, context):
        self.context = context

    def generate(self):
        for src in self.sources():
            for reason in self.apply(src):
                yield reason

    @classmethod
    def priority(clazz):
        return 1

class SingleSourceRule(Rule):
    def accepts(self, prop):
        return True

    def sources(self):
        return [p for p in self.context.list(type(self).property_type) if self.accepts(p)]
