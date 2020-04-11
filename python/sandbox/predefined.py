from .core import Constraint, CoreScene
from .property import *
from .util import LazyComment

def enumerate_predefined_properties(scene):
    for cnstr in scene.constraints(Constraint.Kind.collinear):
        if all(param.layer != 'invisible' for param in cnstr.params):
            yield (PointsCollinearityProperty(*cnstr.params, True), cnstr.comments)

    for cnstr in scene.constraints(Constraint.Kind.not_collinear):
        if all(param.layer != 'invisible' for param in cnstr.params):
            yield (PointsCollinearityProperty(*cnstr.params, False), cnstr.comments)
            yield (PointsCoincidenceProperty(*cnstr.params[0:2], False), cnstr.comments)
            yield (PointsCoincidenceProperty(*cnstr.params[1:3], False), cnstr.comments)
            yield (PointsCoincidenceProperty(cnstr.params[0], cnstr.params[2], False), cnstr.comments)

    for cnstr in scene.constraints(Constraint.Kind.not_equal):
        if all(param.layer != 'invisible' for param in cnstr.params):
            yield (PointsCoincidenceProperty(cnstr.params[0], cnstr.params[1], False), cnstr.comments)

    for cnstr in scene.constraints(Constraint.Kind.length_ratio):
        if all(param.layer != 'invisible' for param in [*cnstr.params[0].points, *cnstr.params[1].points]):
            yield (
                LengthRatioProperty(cnstr.params[0], cnstr.params[1], cnstr.params[2]),
                cnstr.comments
            )

    for cnstr in scene.constraints(Constraint.Kind.same_direction):
        if all(param.layer != 'invisible' for param in cnstr.params):
            yield (
                AngleValueProperty(cnstr.params[0].angle(*cnstr.params[1:]), 0),
                cnstr.comments
            )

    for cnstr in scene.constraints(Constraint.Kind.perpendicular):
        line0 = cnstr.params[0]
        line1 = cnstr.params[1]
        for pts0 in itertools.combinations(line0.all_points, 2):
            if 'invisible' in [p.layer for p in pts0]:
                continue
            for pts1 in itertools.combinations(line1.all_points, 2):
                if 'invisible' in [p.layer for p in pts1]:
                    continue
                yield (
                    PerpendicularSegmentsProperty(
                        pts0[0].segment(pts0[1]), pts1[0].segment(pts1[1])
                    ),
                    cnstr.comments
                )

    for cnstr in scene.constraints(Constraint.Kind.acute_angle):
        angle = cnstr.params[0]
        if 'invisible' in [p.layer for p in angle.points]:
            continue
        yield (
            AcuteAngleProperty(angle),
            cnstr.comments
        )

    for cnstr in scene.constraints(Constraint.Kind.obtuse_angle):
        angle = cnstr.params[0]
        if 'invisible' in [p.layer for p in angle.points]:
            continue
        yield (
            ObtuseAngleProperty(angle),
            cnstr.comments
        )

    for cnstr in scene.constraints(Constraint.Kind.parallel_vectors):
        if all(all(p.layer != 'invisible' for p in param.points) for param in cnstr.params):
            yield (ParallelVectorsProperty(*cnstr.params), cnstr.comments)

    for cnstr in scene.constraints(Constraint.Kind.inside_angle):
        point = cnstr.params[0]
        angle = cnstr.params[1]
        if point.layer != 'invisible' and all(p.layer != 'invisible' for p in angle.points):
            yield (
                PointInsideAngleProperty(point, angle),
                cnstr.comments
            )

    for cnstr in scene.constraints(Constraint.Kind.inside_segment):
        if all(p.layer != 'invisible' for p in (cnstr.params[0], *cnstr.params[1].points)):
            yield (
                PointsCoincidenceProperty(*cnstr.params[1].points, False),
                cnstr.comments
            )
            yield (
                AngleValueProperty(cnstr.params[0].angle(*cnstr.params[1].points), 180),
                cnstr.comments
            )

    for cnstr in scene.constraints(Constraint.Kind.equilateral):
        yield (
            EquilateralTriangleProperty(cnstr.params),
            cnstr.comments
        )

    for line in scene.lines(max_layer='auxiliary'):
        for pts in itertools.combinations([p for p in line.all_points], 3):
            if all(p.layer in CoreScene.layers_by('auxiliary') for p in pts):
                yield (
                    PointsCollinearityProperty(*pts, True),
                    [LazyComment('Three points on the line %s', line)]
                )

    for circle in scene.circles(max_layer='user'):
        radiuses = [circle.centre.segment(pt) for pt in circle.all_points]
        if circle.centre not in circle.radius.points:
            for rad in radiuses:
                yield (
                    LengthRatioProperty(rad, circle.radius, 1),
                    [LazyComment('Distance between centre %s and point %s on the circle of radius |%s|', circle.centre, rad.points[0], circle.radius)]
                )
        for rad0, rad1 in itertools.combinations(radiuses, 2):
            yield (
                LengthRatioProperty(rad0, rad1, 1),
                [LazyComment('Two radiuses of the same circle with centre %s', circle.centre)]
            )

    for cnstr in scene.constraints(Constraint.Kind.opposite_side):
        line = cnstr.params[2]
        yield (
            SameOrOppositeSideProperty(line.point0.segment(line.point1), cnstr.params[0], cnstr.params[1], False),
            cnstr.comments
        )

    for cnstr in scene.constraints(Constraint.Kind.same_side):
        line = cnstr.params[2]
        yield (
            SameOrOppositeSideProperty(line.point0.segment(line.point1), cnstr.params[0], cnstr.params[1], True),
            cnstr.comments
        )

    for cnstr in scene.constraints(Constraint.Kind.angles_ratio):
        angle0 = cnstr.params[0]
        angle1 = cnstr.params[1]
        if any(p.layer == 'invisible' for p in angle0.points):
            continue
        if any(p.layer == 'invisible' for p in angle1.points):
            continue
        yield (
            AngleRatioProperty(angle0, angle1, cnstr.params[2]),
            cnstr.comments
        )
