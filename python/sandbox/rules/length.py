from ..property import *

from .abstract import Rule, processed_cache, source_type

@processed_cache(set())
class LengthEqualityToRatioEqualityRule(Rule):
    def sources(self):
        return [ra for ra in self.context.ratios_in_use() if isinstance(ra, tuple)]

    def apply(self, ratio):
        num, denom = ratio
        num_variants = self.context.congruent_segments_for(num)
        denom_variants = self.context.congruent_segments_for(denom)

        eq_cache = {}
        def eq_prop(seg0, seg1):
            key = frozenset([seg0, seg1])
            cached = eq_cache.get(key)
            if cached:
                return cached
            prop = self.context.congruent_segments_property(seg0, seg1, allow_zeroes=True)
            eq_cache[key] = prop
            return prop

        ne_cache = {}
        def ne_prop(seg):
            cached = ne_cache.get(seg)
            if cached:
                return cached
            prop = self.context.coincidence_property(*seg.points)
            ne_cache[seg] = prop
            return prop

        for n in num_variants:
            if n == denom:
                continue
            key = (denom, frozenset([num, n]))
            if key in self.processed:
                continue
            self.processed.add(key)
            yield (
                EqualLengthRatiosProperty(num, denom, n, denom),
                Comment(
                    '$|%{segment:num}| = |%{segment:n}|$, $%{segment:denom}$ is non-zero',
                    {'num': num, 'n': n, 'denom': denom}
                ),
                [eq_prop(num, n), ne_prop(denom)]
            )
        for d in denom_variants:
            if num == d:
                continue
            key = (num, denom, num, d)
            if key in self.processed:
                continue
            self.processed.add(key)
            yield (
                EqualLengthRatiosProperty(num, denom, num, d),
                Comment(
                    '$|%{segment:denom}| = |%{segment:d}|$, $%{segment:denom}$ is non-zero',
                    {'denom': denom, 'd': d}
                ),
                [eq_prop(denom, d), ne_prop(denom)]
            )
        for n in num_variants:
            for d in denom_variants:
                if n == d:
                    continue
                key = (num, denom, n, d)
                if key in self.processed:
                    continue
                self.processed.add(key)
                yield (
                    EqualLengthRatiosProperty(num, denom, n, d),
                    Comment(
                        '$|%{segment:num}| = |%{segment:n}|$, $|%{segment:denom}| = |%{segment:d}|$, and $%{segment:denom}$ is non-zero',
                        {'num': num, 'n': n, 'denom': denom, 'd': d}
                    ),
                    [eq_prop(num, n), eq_prop(denom, d), ne_prop(denom)]
                )

@source_type(EqualLengthProductsProperty)
@processed_cache({})
class LengthProductEqualityToRatioRule(Rule):
    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return

        ne = [self.context.coincidence_property(*seg.points) for seg in prop.segments]
        original = mask
        for i, j, k, l, bit in [(0, 1, 2, 3, 0x1), (0, 2, 1, 3, 0x2), (3, 1, 2, 0, 0x4), (3, 2, 1, 0, 0x8)]:
            if mask & bit:
                continue
            if ne[j] is None or ne[l] is None:
                continue
            mask |= bit
            if ne[j].coincident or ne[l].coincident:
                continue

            if prop.segments[j] == prop.segments[l]:
                yield (
                    ProportionalLengthsProperty(prop.segments[i], prop.segments[k], 1),
                    prop.reason.comment,
                    prop.reason.premises + [ne[j], ne[l]]
                )
            elif prop.segments[i] == prop.segments[j]:
                yield (
                    ProportionalLengthsProperty(prop.segments[k], prop.segments[l], 1),
                    prop.reason.comment,
                    prop.reason.premises + [ne[j]]
                )
            elif prop.segments[k] == prop.segments[l]:
                yield (
                    ProportionalLengthsProperty(prop.segments[i], prop.segments[j], 1),
                    prop.reason.comment,
                    prop.reason.premises + [ne[l]]
                )
            else:
                yield (
                    EqualLengthRatiosProperty(*[prop.segments[x] for x in (i, j, k, l)]),
                    prop.reason.comment,
                    prop.reason.premises + [ne[j], ne[l]]
                )

        if mask != original:
            self.processed[prop] = mask
