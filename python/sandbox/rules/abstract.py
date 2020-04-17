class Rule:
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

class RuleWithHints(Rule):
    def sources(self):
        def is_reasoned(prop):
            return prop.reason or any(p.reason for p in prop.variants)
        return [p for p in self.context.hints(type(self).property_type) if not is_reasoned(p)]
