from ..property import *

from .abstract import Rule, processed_cache, source_type

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
