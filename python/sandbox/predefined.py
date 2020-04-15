from .core import Constraint, CoreScene
from .property import *
from .util import LazyComment

def enumerate_predefined_properties(scene, max_layer, extra_points=set()):
    layer_set = CoreScene.layers_by(max_layer)
    def is_visible(point):
        return point.layer in layer_set or point in extra_points
    def all_visible(points):
        return all(is_visible(pt) for pt in points)

    for cnstr in scene.constraints(Constraint.Kind.collinear):
        if all_visible(cnstr.params):
            yield (PointsCollinearityProperty(*cnstr.params, True), cnstr.comments)

    for cnstr in scene.constraints(Constraint.Kind.not_collinear):
        if all_visible(cnstr.params):
            yield (PointsCollinearityProperty(*cnstr.params, False), cnstr.comments)
            yield (PointsCoincidenceProperty(*cnstr.params[0:2], False), cnstr.comments)
            yield (PointsCoincidenceProperty(*cnstr.params[1:3], False), cnstr.comments)
            yield (PointsCoincidenceProperty(cnstr.params[0], cnstr.params[2], False), cnstr.comments)

    for cnstr in scene.constraints(Constraint.Kind.not_equal):
        if all_visible(cnstr.params):
            yield (PointsCoincidenceProperty(cnstr.params[0], cnstr.params[1], False), cnstr.comments)

    for cnstr in scene.constraints(Constraint.Kind.length_ratio):
        if all_visible(cnstr.params[0].points + cnstr.params[1].points):
            yield (
                ProportionalLengthsProperty(cnstr.params[0], cnstr.params[1], cnstr.params[2]),
                cnstr.comments
            )

    for cnstr in scene.constraints(Constraint.Kind.same_direction):
        if all_visible(cnstr.params):
            yield (
                AngleValueProperty(cnstr.params[0].angle(*cnstr.params[1:]), 0),
                cnstr.comments
            )

    for cnstr in scene.constraints(Constraint.Kind.perpendicular):
        line0 = cnstr.params[0]
        line1 = cnstr.params[1]
        for pts0 in itertools.combinations(line0.all_points, 2):
            if not all_visible(pts0):
                continue
            for pts1 in itertools.combinations(line1.all_points, 2):
                if not all_visible(pts1):
                    continue
                yield (
                    PerpendicularSegmentsProperty(
                        pts0[0].segment(pts0[1]), pts1[0].segment(pts1[1])
                    ),
                    cnstr.comments
                )

    for cnstr in scene.constraints(Constraint.Kind.acute_angle):
        angle = cnstr.params[0]
        if all_visible(angle.point_set):
            yield (
                AngleKindProperty(angle, AngleKindProperty.Kind.acute),
                cnstr.comments
            )

    for cnstr in scene.constraints(Constraint.Kind.obtuse_angle):
        angle = cnstr.params[0]
        if all_visible(angle.point_set):
            yield (
                AngleKindProperty(angle, AngleKindProperty.Kind.obtuse),
                cnstr.comments
            )

    for cnstr in scene.constraints(Constraint.Kind.parallel_vectors):
        if all(all_visible(param.points) for param in cnstr.params):
            yield (ParallelVectorsProperty(*cnstr.params), cnstr.comments)

    for cnstr in scene.constraints(Constraint.Kind.inside_angle):
        point = cnstr.params[0]
        angle = cnstr.params[1]
        if is_visible(point) and all_visible(angle.point_set):
            yield (
                PointInsideAngleProperty(point, angle),
                cnstr.comments
            )

    for cnstr in scene.constraints(Constraint.Kind.inside_segment):
        if all_visible((cnstr.params[0], *cnstr.params[1].points)):
            yield (
                PointsCoincidenceProperty(*cnstr.params[1].points, False),
                cnstr.comments
            )
            yield (
                AngleValueProperty(cnstr.params[0].angle(*cnstr.params[1].points), 180),
                cnstr.comments
            )

    for cnstr in scene.constraints(Constraint.Kind.equilateral):
        if all_visible(cnstr.params):
            yield (
                EquilateralTriangleProperty(cnstr.params),
                cnstr.comments
            )

    for line in scene.lines(max_layer='auxiliary'):
        for pts in itertools.combinations([p for p in line.all_points], 3):
            if all_visible(pts):
                yield (
                    PointsCollinearityProperty(*pts, True),
                    [LazyComment('Three points on the line %s', line)]
                )

    for circle in scene.circles(max_layer='user'):
        radiuses = [circle.centre.segment(pt) for pt in circle.all_points]
        if circle.centre not in circle.radius.points:
            for rad in radiuses:
                yield (
                    ProportionalLengthsProperty(rad, circle.radius, 1),
                    [LazyComment('Distance between centre %s and point %s on the circle of radius |%s|', circle.centre, rad.points[0], circle.radius)]
                )
        for rad0, rad1 in itertools.combinations(radiuses, 2):
            yield (
                ProportionalLengthsProperty(rad0, rad1, 1),
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
        if all_visible(angle0.point_set) and all_visible(angle1.point_set):
            yield (
                AngleRatioProperty(angle0, angle1, cnstr.params[2]),
                cnstr.comments
            )
