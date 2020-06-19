import itertools
import sympy as sp

from ..property import *
from ..util import Comment

from .abstract import SingleSourceRule

class SideProductsInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return

        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        original = mask
        for i, j in itertools.combinations(range(0, 3), 2):
            bit = 1 << next(k for k in range(0, 3) if k not in (i, j))
            if mask & bit:
                continue
            segments = (sides0[i], sides0[j], sides1[i], sides1[j])
            for inds in [(0, 1, 2, 3), (0, 2, 1, 3), (1, 0, 3, 2), (2, 0, 3, 1)]:
                if not self.context.length_ratios_are_equal(*[segments[n] for n in inds]):
                    break
            else:
                continue
            mask |= bit
            if segments[0] != segments[1] and segments[0] != segments[2] and \
               segments[1] != segments[3] and segments[2] != segments[3]:
                yield (
                    EqualLengthProductsProperty(*segments),
                    Comment(
                        'ratios of sides in similar $%{triangle:tr0}$ and $%{triangle:tr1}$',
                        {'tr0': prop.triangle0, 'tr1': prop.triangle1}
                    ),
                    [prop]
                )

        if original != mask:
            self.processed[prop] = mask

class CorrespondingAnglesInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return

        ne0 = []
        ne1 = []
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i in range(0, 3):
            ne0.append(self.context.not_equal_property(*sides0[i].points))
            ne1.append(self.context.not_equal_property(*sides1[i].points))

        angles0 = prop.triangle0.angles
        angles1 = prop.triangle1.angles
        original = mask
        for i in range(0, 3):
            bit = 1 << i
            if mask & bit:
                continue
            if angles0[i] == angles1[i]:
                mask |= bit
                continue
            ne = []
            for j in range(0, 3):
                if i != j:
                    if ne0[j]:
                        ne.append(ne0[j])
                    if ne1[j]:
                        ne.append(ne1[j])
            if len(ne) < 3:
                continue
            mask |= bit
            yield (
                AngleRatioProperty(angles0[i], angles1[i], 1),
                Comment(
                    'corresponding angles in similar $%{triangle:tr0}$ and $%{triangle:tr1}$',
                    {'tr0': prop.triangle0, 'tr1': prop.triangle1}
                ),
                [prop] + ne
            )

        if original != mask:
            self.processed[prop] = mask

class BaseAnglesOfIsoscelesRule(SingleSourceRule):
    property_type = IsoscelesTriangleProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        neq = self.context.coincidence_property(*prop.base.points)
        if neq is None:
            return
        self.processed.add(prop)
        if neq.coincident:
            return
        yield (
            AngleRatioProperty(
                prop.base.points[0].angle(prop.apex, prop.base.points[1]),
                prop.base.points[1].angle(prop.apex, prop.base.points[0]),
                1
            ),
            Comment('base angles of isosceles $%{triangle:tr}$', {'tr': prop.triangle}),
            [prop, neq]
        )

class BaseAnglesOfIsoscelesWithKnownApexAngleRule(SingleSourceRule):
    property_type = IsoscelesTriangleProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        av = self.context.angle_value_property(prop.apex.angle(*prop.base.points))
        if av is None:
            return
        self.processed.add(prop)
        if av.degree == 0:
            return

        for angle in (
            prop.base.points[0].angle(prop.apex, prop.base.points[1]),
            prop.base.points[1].angle(prop.apex, prop.base.points[0])
        ):
            yield (
                AngleValueProperty(angle, divide(180 - av.degree, 2)),
                Comment(
                    'base angles of isosceles $%{triangle:triangle}$ with apex angle $%{anglemeasure:angle} = %{degree:degree}$',
                    {'triangle': prop.triangle, 'angle': av.angle, 'degree': av.degree}
                ),
                [prop, av]
            )

class LegsOfIsoscelesRule(SingleSourceRule):
    property_type = IsoscelesTriangleProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        yield (
            ProportionalLengthsProperty(
                prop.apex.segment(prop.base.points[0]),
                prop.apex.segment(prop.base.points[1]),
                1
            ),
            Comment('legs of isosceles $%{triangle:triangle}$', {'triangle': prop.triangle}),
            [prop]
        )

class CorrespondingAnglesInCongruentTrianglesRule(SingleSourceRule):
    property_type = CongruentTrianglesProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return

        original = mask
        for triangle, bit in ((prop.triangle0, 1), (prop.triangle1, 2)):
            if mask & bit:
                continue
            ncl = self.context.collinearity_property(*triangle.points)
            if ncl is None:
                continue
            if ncl.collinear:
                mask = 0x3
                break
            mask |= bit
            angles0 = prop.triangle0.angles
            angles1 = prop.triangle1.angles
            for i in range(0, 3):
                if angles0[i] != angles1[i]:
                    yield (
                        AngleRatioProperty(angles0[i], angles1[i], 1),
                        Comment(
                            'corresponding angles in congruent $%{triangle:tr0}$ and $%{triangle:tr1}$',
                            {'tr0': prop.triangle0, 'tr1': prop.triangle1}
                        ),
                        [prop, ncl]
                    )

        if mask != original:
            self.processed[prop] = mask

class CorrespondingSidesInCongruentTrianglesRule(SingleSourceRule):
    property_type = CongruentTrianglesProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i in range(0, 3):
            segment0 = sides0[i]
            segment1 = sides1[i]
            if segment0 != segment1:
                yield (
                    ProportionalLengthsProperty(segment0, segment1, 1),
                    Comment(
                        'corresponding sides in congruent $%{triangle:tr0}$ and $%{triangle:tr1}$',
                        {'tr0': prop.triangle0, 'tr1': prop.triangle1}
                    ),
                    [prop]
                )

class CorrespondingSidesInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        original = mask
        for i in range(0, 3):
            if mask & (1 << i):
                continue
            lr, ratio = self.context.length_ratio_property_and_value(sides0[i], sides1[i], True)
            if lr is None:
                continue
            mask |= (1 << i)
            if ratio == 1:
                mask = 0x7
                break
            for j in [j for j in range(0, 3) if j != i]:
                if sides0[j] == sides1[j]:
                    if ratio != 1:
                        yield (
                            PointsCoincidenceProperty(*sides0[j].points, True),
                            Comment(
                                '$|%{segment:side}| = %{multiplier:ratio} * |%{segment:side}|$ as $%{segment:size}$ is a side in similar but non-congruent $%{triangle:tr0}$ and $%{triangle:tr1}$',
                                {'side': sides0[j], 'ratio': ratio, 'tr0': prop.triangle0, 'tr1': prop.triangle1}
                            ),
                            [prop, lr]
                        )
                else:
                    yield (
                        ProportionalLengthsProperty(sides0[j], sides1[j], ratio),
                        Comment(
                            'ratio of sides in similar $%{triangle:t0}$ and $%{triangle:t1}$',
                            {'t0': prop.triangle0, 't1': prop.triangle1}
                        ),
                        [prop, lr]
                    )

        if original != mask:
            self.processed[prop] = mask

class EquilateralTriangleRule(SingleSourceRule):
    property_type = EquilateralTriangleProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return
        original = mask

        if (mask & 0x1) == 0:
            # properties not depending on degeneracy
            mask |= 0x1
            for side0, side1 in itertools.combinations(prop.triangle.sides, 2):
                yield (
                    ProportionalLengthsProperty(side0, side1, 1),
                    Comment(
                        'sides of equilateral $%{triangle:triangle}$',
                        {'triangle': prop.triangle}
                    ),
                    [prop]
                )

        for side, bit in zip(prop.triangle.sides, (0x2, 0x4, 0x8)):
            if mask & bit:
                continue
            ne = self.context.coincidence_property(*side.points)
            if ne is None:
                continue
            mask |= bit

            if ne.coincident:
                sides_comment_pattern = '$%{point:v0}$ and $%{point:v1}$ are vertices of degenerate equlateral $%{triangle:triangle}$'
            else:
                sides_comment_pattern = '$%{point:v0}$ and $%{point:v1}$ are vertices of non-degenerate equlateral $%{triangle:triangle}$'
                for angle in prop.triangle.angles:
                    yield (
                        AngleValueProperty(angle, 60),
                        Comment(
                            'angle of non-degenerate equilateral $%{triangle:triangle}$',
                            {'triangle': prop.triangle}
                        ),
                        [prop, ne]
                    )

            for other_side in [s for s in prop.triangle.sides if s != side]:
                yield (
                    PointsCoincidenceProperty(*other_side.points, ne.coincident),
                    Comment(
                        sides_comment_pattern,
                        {'v0': other_side.points[0], 'v1': other_side.points[1], 'triangle': prop.triangle}),
                    [prop, ne]
                )

        if mask != original:
            self.processed[prop] = mask

class CentreOfEquilateralTriangleRule(SingleSourceRule):
    property_type = CentreOfEquilateralTriangleProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return

        vertices = prop.triangle.points
        centre = prop.centre
        radiuses = [centre.segment(v) for v in vertices]

        if (mask & 0x1) == 0:
            # properties not depending on degeneracy
            mask |= 0x1
            for rad0, rad1 in itertools.combinations(radiuses, 2):
                comment = Comment(
                    '$%{point:centre}$ is the centre of equilateral $%{triangle:triangle}$',
                    {'centre': centre, 'triangle': prop.triangle}
                )
                yield (ProportionalLengthsProperty(rad0, rad1, 1), comment, [prop])

        original = mask
        for index in range(0, 3):
            bit = 2 << index
            if mask & bit:
                continue
            side = prop.triangle.sides[index]
            ne = self.context.coincidence_property(*side.points)
            if ne is None:
                continue
            mask |= bit

            new_properties = []
            for v in vertices:
                new_properties.append(PointsCoincidenceProperty(centre, v, ne.coincident))

            if ne.coincident:
                pattern = '$%{point:centre}$ is the centre of degenerate equilateral $%{triangle:triangle}$'
            else:
                pattern = '$%{point:centre}$ is the centre of non-degenerate equilateral $%{triangle:triangle}$'
                for v0, v1 in itertools.combinations(vertices, 2):
                    new_properties.append(AngleValueProperty(centre.angle(v0, v1), 120))
                    new_properties.append(AngleValueProperty(v0.angle(centre, v1), 30))
                    new_properties.append(AngleValueProperty(v1.angle(centre, v0), 30))
                for v0, v1, v2 in itertools.permutations(vertices, 3):
                    new_properties.append(AngleValueProperty(centre.vector(v0).angle(v1.vector(v2)), 90))
                for angle in prop.triangle.angles:
                    new_properties.append(PointInsideAngleProperty(centre, angle))
                for radius, side in itertools.product(radiuses, prop.triangle.sides):
                    new_properties.append(ProportionalLengthsProperty(side, radius, sp.sqrt(3)))
                for radius, side in zip(radiuses, prop.triangle.sides):
                    new_properties.append(SameOrOppositeSideProperty(radius, *side.points, False))
                for v, side in zip(vertices, prop.triangle.sides):
                    new_properties.append(SameOrOppositeSideProperty(side, v, centre, True))

            comment = Comment(pattern, {'centre': centre, 'triangle': prop.triangle})
            for p in new_properties:
                yield (p, comment, [prop, ne])

        if mask != original:
            self.processed[prop] = mask
