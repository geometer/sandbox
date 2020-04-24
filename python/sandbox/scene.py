"""
This module is to be extended in the future to add more construction methods.
"""

import itertools

from .core import CoreScene
from .util import LazyComment

class Scene(CoreScene):
    """
    The main class Scene.
    Adds composite construction methods to CoreScene.
    """

    def parallel_line(self, line, point, **kwargs):
        """
        Constructs a line parallel to the given line through the given point.
        """
        fourth = point.translated_point(line.point0.vector(line.point1), layer='auxiliary')
        return point.line_through(fourth, **kwargs)

    def perpendicular_foot_point(self, point, line, **kwargs):
        """
        The foot of the perpendicular from the point to the line
        """
        return line.intersection_point(point.perpendicular_line(line, layer='auxiliary'), **kwargs)

    def orthocentre_point(self, triangle, **kwargs):
        """
        Orthocentre of the triangle (intersection of the altitudes)
        """
        self.nondegenerate_triangle_constraint(triangle)
        altitude0 = self.altitude(triangle, triangle.points[0], layer='auxiliary')
        altitude1 = self.altitude(triangle, triangle.points[1], layer='auxiliary')
        altitude2 = self.altitude(triangle, triangle.points[2], layer='auxiliary')
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = LazyComment('Orthocentre of %s', triangle)
        centre = altitude0.intersection_point(altitude1, **kwargs)
        centre.belongs_to(altitude2)
        return centre

    def centroid_point(self, triangle, **kwargs):
        """
        Centroid of the triangle (intersection of the medians)
        """
        self.nondegenerate_triangle_constraint(triangle)
        medians = [triangle.points[i].line_through(triangle.sides[i].middle_point(layer='auxiliary'), layer='auxiliary') for i in range(0, 3)]
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = LazyComment('Centroid of %s', triangle)
        centre = medians[0].intersection_point(medians[1], **kwargs)
        centre.belongs_to(medians[2])
        return centre

    def circumcentre_point(self, triangle, **kwargs):
        """
        Circumcentre of the triangle (i.e., centre of the circumcircle)
        """
        self.nondegenerate_triangle_constraint(triangle)
        bisectors = [side.perpendicular_bisector_line(layer='auxiliary') for side in triangle.sides]
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = LazyComment('Circumcentre of %s', triangle)
        centre = bisectors[0].intersection_point(bisectors[1], **kwargs)
        centre.belongs_to(bisectors[2])
        for seg0, seg1 in itertools.combinations([centre.segment(v) for v in triangle.points], 2):
            seg0.congruent_constraint(
                seg1,
                comment=LazyComment('%s is circumcentre of %s', centre, triangle)
            )
        return centre

    def free_line_through(self, point, **kwargs):
        """
        A line through the point
        """
        self.assert_point(point)
        extra = self.free_point(layer='auxiliary')
        extra.not_equal_constraint(point)
        return point.line_through(extra, **kwargs)

    def incentre_point(self, triangle, **kwargs):
        """
        Centre of the inscribed circle of the triangle
        """
        self.nondegenerate_triangle_constraint(triangle)
        angles = triangle.angles
        bisector0 = angles[0].bisector_line(layer='auxiliary')
        bisector1 = angles[1].bisector_line(layer='auxiliary')
        bisector2 = angles[2].bisector_line(layer='auxiliary')
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = LazyComment('Incentre of %s', triangle)
        centre = bisector0.intersection_point(bisector1, **kwargs)
        centre.belongs_to(bisector2)
        angles[0].point_on_bisector_constraint(centre)
        angles[1].point_on_bisector_constraint(centre)
        angles[2].point_on_bisector_constraint(centre)
        centre.inside_triangle_constraint(triangle, comment=LazyComment('%s is incentre of %s', centre, triangle))
        return centre

    def incircle(self, triangle, **kwargs):
        """
        Inscribed circle of the triangle
        """
        centre = self.incentre_point(triangle, layer='auxiliary')
        side = triangle.points[0].line_through(triangle.points[1], layer='auxiliary')
        foot = self.perpendicular_foot_point(centre, side, layer='auxiliary')
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = LazyComment('Incircle of %s', triangle)
        return centre.circle_through(foot, **kwargs)

    def circumcircle(self, triangle, **kwargs):
        """
        Circumscribed circle of the triangle
        """
        centre = self.circumcentre_point(triangle, layer='auxiliary')
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = LazyComment('Cicrumcircle of %s', triangle)
        return centre.circle_through(triangle.points[0], **kwargs)

    def nondegenerate_triangle(self, labels=None):
        """
        Free triangle
        Pass array of three strings as 'labels' to use as point labels
        Returns tuple of three points
        """
        assert not labels or len(labels) == 3
        def point(index):
            args = {}
            if labels and labels[index]:
                args['label'] = labels[index]
            return self.free_point(**args)

        triangle = Scene.Triangle(point(0), point(1), point(2))
        self.nondegenerate_triangle_constraint(triangle)
        return triangle

    def nondegenerate_triangle_constraint(self, triangle, **kwargs):
        """
        Parameter triangle is triple of non-collinear points
        """
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = LazyComment('%s is non-degenerate', triangle)
        triangle.points[0].not_collinear_constraint(triangle.points[1], triangle.points[2], **kwargs)

    def altitude(self, triangle, vertex, **kwargs):
        """
        Height from the vertex in the triangle
        """
        if isinstance(triangle, CoreScene.Point):
            triangle, vertex = vertex, triangle
        self.nondegenerate_triangle_constraint(triangle)
        assert vertex in triangle.points
        points = [pt for pt in triangle.points if pt != vertex]
        base = points[0].line_through(points[1], layer='auxiliary')
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = LazyComment('Altitude of %s from vertex %s', triangle, vertex)
        altitude = vertex.perpendicular_line(base, **kwargs)
        altitude.perpendicular_constraint(base, comment=LazyComment('altitude %s is perpendicular to the base %s', altitude, base), guaranteed=True)
        return altitude

    def parallelogram(self, labels=None):
        """
        Free parallelogram
        Pass array of four strings as 'labels' to use as point labels
        Returns tuple of four points, in cyclic order
        """
        assert not labels or len(labels) == 4
        def point(index):
            args = {}
            if labels and labels[index]:
                args['label'] = labels[index]
            return self.free_point(**args)

        pts = [point(0), point(1), point(2)]
        args = {}
        if labels and labels[3]:
            args['label'] = labels[3]
        pts.append(pts[0].translated_point(pts[1].vector(pts[2]), **args))

        comment = LazyComment('%s %s %s %s is a parallelogram', *pts)
        pts[0].vector(pts[1]).parallel_constraint(pts[3].vector(pts[2]), comment=comment)
        pts[0].vector(pts[3]).parallel_constraint(pts[1].vector(pts[2]), comment=comment)
        pts[0].segment(pts[1]).congruent_constraint(pts[2].segment(pts[3]), comment=comment)
        pts[0].segment(pts[3]).congruent_constraint(pts[1].segment(pts[2]), comment=comment)
        for pt0, pt1, pt2 in itertools.combinations(pts, 3):
            pt0.not_collinear_constraint(pt1, pt2, comment=comment)
        return tuple(pts)
