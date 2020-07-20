from ..property import *

from .abstract import Rule, processed_cache, source_type

@processed_cache(set())
class ZeroAngleWithLengthInequalityRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(0, lambda a: a.vertex and a not in self.processed)

    def apply(self, prop):
        angle = prop.angle
        seg0 = angle.vectors[0].as_segment
        seg1 = angle.vectors[1].as_segment
        ineq = self.context.lengths_inequality_property(seg0, seg1)
        if ineq is None:
            return
        self.processed.add(angle)
        if seg0 == ineq.segments[0]:
            new_angle = angle.endpoints[0].angle(angle.vertex, angle.endpoints[1])
            params = {'long': angle.vectors[1], 'pt': angle.endpoints[0], 'short': angle.vectors[0]}
        else:
            new_angle = angle.endpoints[1].angle(angle.vertex, angle.endpoints[0])
            params = {'long': angle.vectors[0], 'pt': angle.endpoints[1], 'short': angle.vectors[1]}
        yield (
            AngleValueProperty(new_angle, 180),
            Comment(
                '$%{point:pt}$ lies on ray $%{ray:long}$ and $|%{segment:short} < %{segment:long}|$',
                params
            ),
            [prop, ineq]
        )
    
@source_type(LengthsInequalityProperty)
@processed_cache(set())
class LengthsInequalityAndEqualityRule(Rule):
    def apply(self, prop):
        for seg in self.context.congruent_segments_for(prop.segments[0]):
            key = (prop, seg)
            if key in self.processed:
                continue
            self.processed.add(key)
            cong = self.context.congruent_segments_property(prop.segments[0], seg, allow_zeroes=True)
            yield (
                LengthsInequalityProperty(seg, prop.segments[1]),
                Comment(
                    '$|%{segment:seg}| = |%{segment:seg0}| < |%{segment:seg1}|$',
                    {'seg': seg, 'seg0': prop.segments[0], 'seg1': prop.segments[1]}
                ),
                [prop, cong]
            )

        for seg in self.context.congruent_segments_for(prop.segments[1]):
            key = (prop, seg)
            if key in self.processed:
                continue
            self.processed.add(key)
            cong = self.context.congruent_segments_property(seg, prop.segments[1], allow_zeroes=True)
            yield (
                LengthsInequalityProperty(prop.segments[0], seg),
                Comment(
                    '$|%{segment:seg0}| < |%{segment:seg1}| = |%{segment:seg}|$',
                    {'seg': seg, 'seg0': prop.segments[0], 'seg1': prop.segments[1]}
                ),
                [prop, cong]
            )

@source_type(AngleKindProperty)
@processed_cache(set())
class SideOppositeToNonAcuteAngleRule(Rule):
    def accepts(self, prop):
        return prop.kind in (AngleKindProperty.Kind.obtuse, AngleKindProperty.Kind.right) and prop.angle.vertex and prop.angle not in self.processed

    def apply(self, prop):
        self.processed.add(prop.angle)
        long_side = prop.angle.endpoints[0].segment(prop.angle.endpoints[1])
        for vec in prop.angle.vectors:
            yield (
                LengthsInequalityProperty(vec.as_segment, long_side),
                Comment(
                    '$%{segment:side}$ is opposite to the greatest angle of $%{triangle:triangle}$',
                    {'side': long_side, 'triangle': Scene.Triangle(*prop.angle.point_set)}
                ),
                [prop]
            )

@processed_cache(set())
class SideOppositeToNonAcuteAngleRule2(Rule):
    def sources(self):
        return self.context.nondegenerate_angle_value_properties()

    def accepts(self, prop):
        return prop.degree >= 90 and prop.angle.vertex and prop.angle not in self.processed

    def apply(self, prop):
        self.processed.add(prop.angle)
        long_side = prop.angle.endpoints[0].segment(prop.angle.endpoints[1])
        for vec in prop.angle.vectors:
            yield (
                LengthsInequalityProperty(vec.as_segment, long_side),
                Comment(
                    '$%{segment:side}$ is opposite to the greatest angle of $%{triangle:triangle}$',
                    {'side': long_side, 'triangle': Scene.Triangle(*prop.angle.point_set)}
                ),
                [prop]
            )

@processed_cache(set())
class PointInsideSegmentToLengthsInequalityRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(180, lambda a: a.vertex and a not in self.processed)

    def apply(self, prop):
        self.processed.add(prop)
        long_side = prop.angle.endpoints[0].segment(prop.angle.endpoints[1])
        for vec in prop.angle.vectors:
            yield (
                LengthsInequalityProperty(vec.as_segment, long_side),
                Comment(
                    'part $%{segment:part}$ is shorter than whole $%{segment:whole}$',
                    {'part': vec, 'whole': long_side}
                ),
                [prop]
            )

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
