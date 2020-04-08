class Stats:
    def __init__(self, data, header=None):
        self.data = data
        self.header = header

    def dump(self, depth=255, level=0):
        if level > depth:
            return
        if self.header:
            print('\t%s%s:' % ('  ' * level, self.header))
        for pair in self.data:
            if isinstance(pair, Stats):
                pair.dump(depth, level + 1)
            elif isinstance(pair[1], list):
                Stats(*pair).dump(depth, level + 1)
            else:
                print('\t%s%s: %s' % ('  ' * (level + 1), *pair))

def dump_stats(header, stats):
    Stats(header, stats).dump()
