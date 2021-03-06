import itertools

from ..property import *
from ..util import Comment, divide

from .abstract import Rule, accepts_auto, processed_cache, source_type

@source_type(SumOfTwoAnglesProperty)
@processed_cache(set())
@accepts_auto
class AngleFromSumOfTwoAnglesRule(Rule):
    def apply(self, prop):
        for a0, a1 in (prop.angles, reversed(prop.angles)):
            av = self.context.angle_value_property(a0)
            if av is None:
                continue
            self.processed.add(prop)
            yield (
                AngleValueProperty(a1, prop.degree - av.degree),
                Comment(
                    '$%{anglemeasure:a1} + %{degree:degree0} = %{anglemeasure:a1} + %{anglemeasure:a0} = %{degree:sum}$',
                    {'a0': a0, 'a1': a1, 'degree0': av.degree, 'sum': prop.degree}
                ),
                [prop, av]
            )
            return

@source_type(SumOfThreeAnglesProperty)
@processed_cache({})
class SumOfTwoAnglesByThreeRule(Rule):
    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return

        original = mask
        for index, angle in enumerate(prop.angles):
            bit = 1 << index
            if mask & bit:
                continue
            av = self.context.angle_value_property(angle)
            if av is None:
                continue
            mask |= bit
            others = [ang for ang in prop.angles if ang != angle]
            yield (
                SumOfTwoAnglesProperty(*others, prop.degree - av.degree),
                Comment(
                    '$%{degree:sum} = %{anglemeasure:a0} + %{anglemeasure:a1} + %{anglemeasure:a2} = %{anglemeasure:a0} + %{anglemeasure:a1} + %{degree:degree2}$',
                    {'a0': others[0], 'a1': others[1], 'a2': angle, 'sum': prop.degree, 'degree2': av.degree}
                ),
                [prop, av]
            )
        if mask != original:
            self.processed[prop] = mask

@source_type(SumOfThreeAnglesProperty)
@processed_cache({})
class AngleBySumOfThreeRule(Rule):
    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return

        avs = []
        miss_count = 0
        for angle in prop.angles:
            av = self.context.angle_value_property(angle)
            if av is None:
                miss_count += 1
                if miss_count == 2:
                    return
            avs.append(av)

        original = mask
        for (av0, av1), bit in zip(itertools.combinations(avs, 2), (1, 2, 4)):
            if mask & bit:
                continue
            if av0 is None or av1 is None:
                continue
            mask |= bit
            third = next(angle for angle in prop.angles if angle not in (av0.angle, av1.angle))
            yield (
                AngleValueProperty(third, prop.degree - av0.degree - av1.degree),
                Comment(
                    '$%{degree:sum} = %{anglemeasure:third} + %{anglemeasure:a0} + %{anglemeasure:a1} = %{anglemeasure:third} + %{degree:d0} + %{degree:d0}$',
                    {
                        'a0': av0.angle,
                        'a1': av1.angle,
                        'third': third,
                        'd0': av0.degree,
                        'd1': av1.degree,
                        'sum': prop.degree
                    }
                ),
                [prop, av0, av1]
            )
        if mask != original:
            self.processed[prop] = mask

@source_type(SumOfTwoAnglesProperty)
@processed_cache(set())
@accepts_auto
class SumAndRatioOfTwoAnglesRule(Rule):
    """
    If the sum and the ratio of two angles are known, we can find the values
    """
    def apply(self, prop):
        ar = self.context.angle_ratio_property(prop.angles[0], prop.angles[1])
        if ar is None:
            return
        self.processed.add(prop)
        value1 = divide(prop.degree, 1 + ar.value)
        value0 = prop.degree - value1
        if ar.value == 1:
            pattern = '$2\,%{anglemeasure:a0} = %{anglemeasure:a0} + %{anglemeasure:a1} = %{degree:sum}$'
            comment0 = Comment(pattern, {'a0': ar.angle0, 'a1': ar.angle1, 'sum': prop.degree})
            comment1 = Comment(pattern, {'a0': ar.angle1, 'a1': ar.angle0, 'sum': prop.degree})
        else:
            comment0 = Comment(
                '$%{anglemeasure:a0} + %{anglemeasure:a0} / %{multiplier:coef} = %{anglemeasure:a0} + %{anglemeasure:a1} = %{degree:sum}$',
                {
                    'a0': ar.angle0,
                    'a1': ar.angle1,
                    'coef': ar.value,
                    'sum': prop.degree
                }
            )
            comment1 = Comment(
                '$%{anglemeasure:a1} + %{multiplier:coef} * %{anglemeasure:a1} = %{anglemeasure:a1} + %{anglemeasure:a0} = %{degree:sum}$',
                {
                    'a0': ar.angle0,
                    'a1': ar.angle1,
                    'coef': ar.value,
                    'sum': prop.degree
                }
            )
        yield (AngleValueProperty(ar.angle0, value0), comment0, [prop, ar])
        yield (AngleValueProperty(ar.angle1, value1), comment1, [prop, ar])

@processed_cache({})
class EqualSumsOfAnglesRule(Rule):
    def sources(self):
        return [(s0, s1) for (s0, s1) in itertools.combinations(self.context.list(SumOfTwoAnglesProperty), 2) if s0.degree == s1.degree]

    def apply(self, src):
        mask = self.processed.get(src, 0)
        if mask == 0xF:
            return

        sum0, sum1 = src
        original = mask
        for index in range(0, 4):
            bit = 1 << index
            if mask & bit:
                continue

            if index // 2:
                other0, eq0 = sum0.angles
            else:
                eq0, other0 = sum0.angles
            if index % 2:
                other1, eq1 = sum1.angles
            else:
                eq1, other1 = sum1.angles

            if other0 == other1:
                mask |= bit
                continue

            if eq0 == eq1:
                mask |= bit
                yield (
                    AngleRatioProperty(other0, other1, 1),
                    Comment(
                        '$%{anglemeasure:other0} + %{anglemeasure:eq0} = %{degree:sum} = %{anglemeasure:other1} + %{anglemeasure:eq1}$',
                        {'other0': other0, 'other1': other1, 'eq0': eq0, 'eq1': eq1, 'sum': sum0.degree}
                    ),
                    [sum0, sum1]
                )
            else:
                ca = self.context.angle_ratio_property(eq0, eq1)
                if ca is None:
                    continue
                mask |= bit
                if ca.value != 1:
                    mask |= 8 // bit # 0x1 <=> 0x8, 0x2 <=> 0x4
                    continue
                sign = '\\equiv' if ca.same else '='
                yield (
                    AngleRatioProperty(other0, other1, 1),
                    Comment(
                        '$%{anglemeasure:other0} + %{anglemeasure:eq0} = %{degree:sum} = %{anglemeasure:other1} + %{anglemeasure:eq1}$ and $%{anglemeasure:eq0} ' + sign + ' %{anglemeasure:eq1}$',
                        {'other0': other0, 'other1': other1, 'eq0': eq0, 'eq1': eq1, 'sum': sum0.degree}
                    ),
                    [sum0, sum1, ca]
                )

        if original != mask:
            self.processed[src] = mask
