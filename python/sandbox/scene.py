"""
This module is to be extended in the future to add more construction methods.
"""

import itertools

from .core import CoreScene
from .util import LazyComment

class Triangle:
    def __init__(self, points):
        self.points = tuple(points)
        self.__sides = None
        self.__angles = None
        self.__permutations = None

    @property
    def sides(self):
        if self.__sides is None:
            self.__sides = (
                self.points[1].segment(self.points[2]),
                self.points[0].segment(self.points[2]),
                self.points[0].segment(self.points[1])
            )
        return self.__sides

    @property
    def angles(self):
        if self.__angles is None:
            self.__angles = (
                self.points[0].angle(self.points[1], self.points[2]),
                self.points[1].angle(self.points[0], self.points[2]),
                self.points[2].angle(self.points[0], self.points[1])
            )
        return self.__angles

    @property
    def permutations(self):
        if self.__permutations is None:
            self.__permutations = (
                (self.points[0], self.points[1], self.points[2]),
                (self.points[0], self.points[2], self.points[1]),
                (self.points[1], self.points[0], self.points[2]),
                (self.points[1], self.points[2], self.points[0]),
                (self.points[2], self.points[0], self.points[1]),
                (self.points[2], self.points[1], self.points[0])
            )
        return self.__permutations

    def __str__(self):
        return '△ %s %s %s' % self.points

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
        self.triangle_constraint(triangle)
        altitude0 = self.altitude(triangle, triangle[0], layer='auxiliary')
        altitude1 = self.altitude(triangle, triangle[1], layer='auxiliary')
        altitude2 = self.altitude(triangle, triangle[2], layer='auxiliary')
        centre = altitude0.intersection_point(altitude1, **kwargs)
        centre.belongs_to(altitude2)
        return centre

    def centroid_point(self, triangle, **kwargs):
        """
        Centroid of the triangle (intersection of the medians)
        """
        self.triangle_constraint(triangle)
        median0 = triangle[0].line_through(triangle[1].segment(triangle[2]).middle_point(layer='auxiliary'), layer='auxiliary')
        median1 = triangle[1].line_through(triangle[2].segment(triangle[0]).middle_point(layer='auxiliary'), layer='auxiliary')
        median2 = triangle[2].line_through(triangle[0].segment(triangle[1]).middle_point(layer='auxiliary'), layer='auxiliary')
        centre = median0.intersection_point(median1, **kwargs)
        centre.belongs_to(median2)
        return centre

    def circumcentre_point(self, triangle, **kwargs):
        """
        Circumcentre of the triangle (i.e., centre of the circumcircle)
        """
        self.triangle_constraint(triangle)
        bisector0 = triangle[0].segment(triangle[1]).perpendicular_bisector_line(layer='auxiliary')
        bisector1 = triangle[0].segment(triangle[2]).perpendicular_bisector_line(layer='auxiliary')
        bisector2 = triangle[1].segment(triangle[2]).perpendicular_bisector_line(layer='auxiliary')
        centre = bisector0.intersection_point(bisector1, **kwargs)
        centre.belongs_to(bisector2)
        for seg0, seg1 in itertools.combinations([centre.segment(v) for v in triangle], 2):
            seg0.congruent_constraint(
                seg1,
                comment=LazyComment('%s is circumcentre of △ %s %s %s', centre, *triangle)
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
        self.triangle_constraint(triangle)
        angle0 = triangle[0].angle(triangle[1], triangle[2])
        angle1 = triangle[1].angle(triangle[0], triangle[2])
        angle2 = triangle[2].angle(triangle[0], triangle[1])
        bisector0 = angle0.bisector_line(layer='auxiliary')
        bisector1 = angle1.bisector_line(layer='auxiliary')
        bisector2 = angle2.bisector_line(layer='auxiliary')
        centre = bisector0.intersection_point(bisector1, **kwargs)
        centre.belongs_to(bisector2)
        angle0.point_on_bisector_constraint(centre)
        angle1.point_on_bisector_constraint(centre)
        angle2.point_on_bisector_constraint(centre)
        centre.inside_triangle_constraint(*triangle, comment=LazyComment('%s is incentre of %s %s %s', centre, *triangle))
        return centre

    def incircle(self, triangle, **kwargs):
        """
        Inscribed circle of △ABC
        """
        centre = self.incentre_point(triangle, layer='auxiliary')
        side = triangle[0].line_through(triangle[1], layer='auxiliary')
        foot = self.perpendicular_foot_point(centre, side, layer='auxiliary')
        return centre.circle_through(foot, **kwargs)

    def circumcircle(self, triangle, **kwargs):
        """
        Circumscribed circle of the triangle
        """
        centre = self.circumcentre_point(triangle, layer='auxiliary')
        return centre.circle_through(triangle[0], **kwargs)

    def triangle(self, labels=None):
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

        points = (point(0), point(1), point(2))
        self.triangle_constraint(points)
        return points

    def triangle_constraint(self, triangle, **kwargs):
        """
        Parameter triangle is triple of non-collinear points
        """
        assert len(triangle) == 3
        for pt in triangle:
            self.assert_point(pt)
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = LazyComment('(%s, %s, %s) is a triangle', *triangle)
        triangle[0].not_collinear_constraint(triangle[1], triangle[2], **kwargs)

    def altitude(self, triangle, vertex, **kwargs):
        """
        Height from the vertex in the triangle
        """
        if isinstance(triangle, CoreScene.Point):
            triangle, vertex = vertex, triangle
        self.triangle_constraint(triangle)
        assert vertex in triangle
        points = list(triangle)
        points.remove(vertex)
        base = points[0].line_through(points[1], layer='auxiliary')
        altitude = vertex.perpendicular_line(base, **kwargs)
        altitude.perpendicular_constraint(base, comment=LazyComment('Altitude %s is perpendicular to the base %s', altitude, base), guaranteed=True)
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
