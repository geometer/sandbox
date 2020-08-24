from .core import Constraint, CoreScene
from .property import *
from .util import Comment, LazyComment

def enumerate_predefined_properties(scene, objects):
    def is_visible(obj):
        return obj in objects
    def all_visible(objs):
        return all(o in objects or o.layer == 'user' for o in objs)

    for cnstr in scene.constraints(Constraint.Kind.collinear):
        if all_visible(cnstr.params):
            yield (PointsCollinearityProperty(*cnstr.params, True), cnstr.comment)

    for cnstr in scene.constraints(Constraint.Kind.not_collinear):
        if all_visible(cnstr.params):
            yield (PointsCollinearityProperty(*cnstr.params, False), cnstr.comment)
            yield (PointsCoincidenceProperty(*cnstr.params[0:2], False), cnstr.comment)
            yield (PointsCoincidenceProperty(*cnstr.params[1:3], False), cnstr.comment)
            yield (PointsCoincidenceProperty(cnstr.params[0], cnstr.params[2], False), cnstr.comment)

    for cnstr in scene.constraints(Constraint.Kind.not_equal):
        if all_visible(cnstr.params):
            yield (PointsCoincidenceProperty(cnstr.params[0], cnstr.params[1], False), cnstr.comment)

    for cnstr in scene.constraints(Constraint.Kind.length_ratio):
        if all_visible(cnstr.params[0].points + cnstr.params[1].points):
            yield (
                ProportionalLengthsProperty(cnstr.params[0], cnstr.params[1], cnstr.params[2]),
                cnstr.comment
            )

    for cnstr in scene.constraints(Constraint.Kind.same_direction):
        if all_visible(cnstr.params):
            yield (
                AngleValueProperty(cnstr.params[0].angle(*cnstr.params[1:]), 0),
                cnstr.comment
            )

    for cnstr in scene.constraints(Constraint.Kind.perpendicular):
        line0 = scene.existing_line(*cnstr.params[0].points)
        line1 = scene.existing_line(*cnstr.params[1].points)
        if line0 is None or line1 is None:
            yield (
                PerpendicularSegmentsProperty(cnstr.params[0], cnstr.params[1]),
                cnstr.comment
            )
            continue

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
                    cnstr.comment
                )

    for cnstr in scene.constraints(Constraint.Kind.acute_angle):
        angle = cnstr.params[0]
        if all_visible(angle.point_set):
            yield (
                AngleKindProperty(angle, AngleKindProperty.Kind.acute),
                cnstr.comment
            )

    for cnstr in scene.constraints(Constraint.Kind.obtuse_angle):
        angle = cnstr.params[0]
        if all_visible(angle.point_set):
            yield (
                AngleKindProperty(angle, AngleKindProperty.Kind.obtuse),
                cnstr.comment
            )

    for cnstr in scene.constraints(Constraint.Kind.angle_value):
        angle = cnstr.params[0]
        if all_visible(angle.point_set):
            yield (
                AngleValueProperty(angle, cnstr.params[1]),
                cnstr.comment
            )

    for cnstr in scene.constraints(Constraint.Kind.parallel_vectors):
        if all(all_visible(param.points) for param in cnstr.params):
            yield (ParallelVectorsProperty(*cnstr.params), cnstr.comment)

    for cnstr in scene.constraints(Constraint.Kind.inside_segment):
        if all_visible((cnstr.params[0], *cnstr.params[1].points)):
            yield (
                PointsCoincidenceProperty(*cnstr.params[1].points, False),
                cnstr.comment
            )
            yield (
                AngleValueProperty(cnstr.params[0].angle(*cnstr.params[1].points), 180),
                cnstr.comment
            )

    for line in scene.lines():
        points = [pt for pt in line.all_points if is_visible(pt)]
        if line.layer == 'user' or len(points) >= 2:
            for pt in points:
                yield (PointOnLineProperty(pt, line, True), None)

    for circle in scene.circles(max_layer='user'):
        radiuses = [circle.centre.segment(pt) for pt in circle.all_points]
        if circle.centre not in circle.radius.points:
            for rad in radiuses:
                yield (
                    ProportionalLengthsProperty(rad, circle.radius, 1),
                    LazyComment('distance between centre %s and point %s on the circle of radius |%s|', circle.centre, rad.points[0], circle.radius)
                )
        for rad0, rad1 in itertools.combinations(radiuses, 2):
            if all_visible(rad0.points + rad1.points):
                yield (
                    ProportionalLengthsProperty(rad0, rad1, 1),
                    LazyComment('two radiuses of the circle with centre %s', circle.centre)
                )

        for four in itertools.combinations([pt for pt in circle.all_points if is_visible(pt)], 4):
            yield (
                ConcyclicPointsProperty(*four),
                LazyComment('points on the same circle')
            )

    for cnstr in scene.constraints(Constraint.Kind.angles_ratio):
        angle0 = cnstr.params[0]
        angle1 = cnstr.params[1]
        if all_visible(angle0.point_set) and all_visible(angle1.point_set):
            yield (
                AngleRatioProperty(angle0, angle1, cnstr.params[2]),
                cnstr.comment
            )

    for prop, comment in scene.properties.items():
        if all_visible(prop.object_set):
            yield (prop, comment if comment else Comment(''))
