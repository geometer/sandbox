"""
This module is to be extended in the future to add more construction methods.
"""

import itertools
import sympy as sp

from .core import CoreScene, Constraint
from .util import Comment

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
            kwargs['comment'] = Comment('The orthocentre of $%{triangle:tr}$', {'tr': triangle})
        centre = altitude0.intersection_point(altitude1, **kwargs)
        from .property import OrthocentreOfTriangleProperty
        self.add_property(OrthocentreOfTriangleProperty(centre, triangle), None)
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
            kwargs['comment'] = Comment('The centroid of $%{triangle:tr}$', {'tr': triangle})
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
            kwargs['comment'] = Comment('The circumcentre of $%{triangle:tr}$', {'tr': triangle})
        centre = bisectors[0].intersection_point(bisectors[1], **kwargs)
        centre.belongs_to(bisectors[2])
        for seg0, seg1 in itertools.combinations([centre.segment(v) for v in triangle.points], 2):
            seg0.congruent_constraint(
                seg1,
                comment=Comment(
                    '$%{point:centre}$ is the circumcentre of $%{triangle:tr}$',
                    {'centre': centre, 'tr': triangle}
                )
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

    def centre_point(self, triangle, **kwargs):
        """
        Centre of equilateral triangle
        """
        assert triangle.is_equilateral
        aux = triangle.sides[0].middle_point(layer='invisible')
        centre = aux.translated_point(aux.vector(triangle.points[0]), sp.sympify(1) / 3, **kwargs)
        from .property import CentreOfEquilateralTriangleProperty
        self.add_property(CentreOfEquilateralTriangleProperty(centre, triangle), None)
        return centre

    def incentre_point(self, triangle, **kwargs):
        """
        Centre of the inscribed circle of the triangle
        """
        self.nondegenerate_triangle_constraint(triangle)
        bisectors = [a.bisector_line(layer='auxiliary') for a in triangle.angles]
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = Comment('The incentre of $%{triangle:tr}$', {'tr': triangle})
        centre = bisectors[0].intersection_point(bisectors[1], **kwargs)
        centre.belongs_to(bisectors[2])
        for angle in triangle.angles:
            angle.point_on_bisector_constraint(
                centre,
                comment=Comment(
                    'the incentre $%{point:centre}$ of $%{triangle:triangle}$ lies on the bisector of $%{angle:angle}$',
                    {'centre': centre, 'triangle': triangle, 'angle': angle}
                )
            )
        centre.inside_triangle_constraint(
            triangle,
            comment=Comment(
                'the incentre $%{point:centre}$ lies inside $%{triangle:triangle}$',
                {'centre': centre, 'triangle': triangle}
            )
        )
        return centre

    def excentre_point(self, triangle, vertex, **kwargs):
        """
        Centre of the inscribed circle of the triangle
        """
        self.nondegenerate_triangle_constraint(triangle)
        assert vertex in triangle.points
        def correct(angle):
            vec0 = angle.vectors[0]
            if vec0.end == vertex:
                vec0 = vec0.reversed
            vec1 = angle.vectors[1]
            if vec1.end == vertex:
                vec1 = vec1.reversed
            return vec0.angle(vec1)

        angles = [correct(a) for a in triangle.angles]
        bisectors = [a.bisector_line(layer='auxiliary') for a in angles]
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = Comment('The excentre of $%{triangle:tr}$ opposite to $%{point:vertex}$', {'tr': triangle, 'vertex': vertex})
        centre = bisectors[0].intersection_point(bisectors[1], **kwargs)
        centre.belongs_to(bisectors[2])
        for angle in angles:
            angle.point_on_bisector_constraint(
                centre,
                comment=Comment(
                    'the excentre $%{point:centre}$ of $%{triangle:triangle}$ lies on the bisector of $%{angle:angle}$',
                    {'centre': centre, 'triangle': triangle, 'angle': angle}
                )
            )
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
            kwargs['comment'] = Comment('The incircle of $%{triangle:tr}$', {'tr': triangle})
        return centre.circle_through(foot, **kwargs)

    def excircle(self, triangle, vertex, **kwargs):
        """
        Inscribed circle of the triangle
        """
        centre = self.excentre_point(triangle, vertex, layer='auxiliary')
        pts = [pt for pt in triangle.points if pt != vertex]
        side = pts[0].line_through(pts[1], layer='auxiliary')
        foot = self.perpendicular_foot_point(centre, side, layer='auxiliary')
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = Comment('The excircle of $%{triangle:tr}$ opposite to $%{point:vertex}$', {'tr': triangle, 'vertex': vertex})
        return centre.circle_through(foot, **kwargs)

    def circumcircle(self, triangle, **kwargs):
        """
        Circumscribed circle of the triangle
        """
        centre = self.circumcentre_point(triangle, layer='auxiliary')
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = Comment('The circumcircle of $%{triangle:tr}$', {'tr': triangle})
        circle = centre.circle_through(triangle.points[0], **kwargs)
        triangle.points[1].belongs_to(circle)
        triangle.points[2].belongs_to(circle)
        return circle

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
            kwargs['comment'] = Comment('$%{triangle:tr}$ is non-degenerate', {'tr': triangle})
        triangle.points[0].not_collinear_constraint(triangle.points[1], triangle.points[2], **kwargs)

    def altitude(self, triangle, vertex, **kwargs):
        """
        Altitude from the vertex in the triangle
        """
        if isinstance(triangle, CoreScene.Point):
            triangle, vertex = vertex, triangle
        self.nondegenerate_triangle_constraint(triangle)
        assert vertex in triangle.points
        points = [pt for pt in triangle.points if pt != vertex]
        base = points[0].line_through(points[1], layer='auxiliary')
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = Comment(
                'Altitude of $%{triangle:triangle}$ from vertex $%{point:vertex}$',
                {'triangle': triangle, 'vertex': vertex}
            )
        altitude = vertex.perpendicular_line(base, **kwargs)
        altitude.perpendicular_constraint(base, comment=Comment(
            'altitude from vertex $%{point:vertex}$ is perpendicular to the base $%{line:base}$',
            {'vertex': vertex, 'base': points[0].segment(points[1])}
        ), guaranteed=True)
        return altitude

    def equilateral_triangle(self, *points_or_labels, **kwargs):
        assert len(points_or_labels) == 3
        #TODO: check argument types
        def ptargs(index):
            return {'label': points_or_labels[index]}
        pt0 = points_or_labels[0] if isinstance(points_or_labels[0], Scene.Point) \
            else self.free_point(**ptargs(0))
        pt1 = points_or_labels[1] if isinstance(points_or_labels[1], Scene.Point) \
            else self.free_point(**ptargs(1))
        if isinstance(points_or_labels[2], Scene.Point):
            pt2 = points_or_labels[2]
        else:
            circle0 = pt0.circle_through(pt1, layer='invisible')
            circle1 = pt1.circle_through(pt0, layer='invisible')
            pt2 = circle0.intersection_point(circle1, **ptargs(2))
        triangle = Scene.Triangle(pt0, pt1, pt2)
        point_set = set(triangle.points)
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = Comment('$%{triangle:tr}$ is equilateral', {'tr': triangle})
        self.equilateral_constraint(triangle, **kwargs)

        return triangle

    def square(self, *points_or_labels, non_degenerate=False):
        assert len(points_or_labels) == 4
        #TODO: check argument types
        def kwargs(index):
            return {'label': points_or_labels[index]}

        pt0 = points_or_labels[0] if isinstance(points_or_labels[0], Scene.Point) \
            else self.free_point(**kwargs(0))
        pt1 = points_or_labels[1] if isinstance(points_or_labels[1], Scene.Point) \
            else self.free_point(**kwargs(1))
        side = pt0.line_through(pt1, layer='auxiliary')
        perp = pt1.perpendicular_line(side, layer='auxiliary')
        circ = pt1.circle_through(pt0, layer='invisible')
        pt2 = points_or_labels[2] if isinstance(points_or_labels[2], Scene.Point) \
            else perp.intersection_point(circ, **kwargs(2))
        pt3 = points_or_labels[3] if isinstance(points_or_labels[3], Scene.Point) \
            else pt2.translated_point(pt1.vector(pt0), 1, **kwargs(3))

        square = Scene.Polygon(pt0, pt1, pt2, pt3)
        if non_degenerate:
            from .property import NondegenerateSquareProperty
            self.add_property(NondegenerateSquareProperty(square), None)
        else:
            from .property import SquareProperty
            self.add_property(SquareProperty(square), None)
        return square

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

        comment = Comment(
            '$%{polygon:para}$ is a parallelogram',
            {'para': Scene.Polygon(*pts)}
        )
        pts[0].vector(pts[1]).parallel_constraint(pts[3].vector(pts[2]), comment=comment)
        pts[0].vector(pts[3]).parallel_constraint(pts[1].vector(pts[2]), comment=comment)
        pts[0].segment(pts[1]).congruent_constraint(pts[2].segment(pts[3]), comment=comment)
        pts[0].segment(pts[3]).congruent_constraint(pts[1].segment(pts[2]), comment=comment)
        for pt0, pt1, pt2 in itertools.combinations(pts, 3):
            pt0.not_collinear_constraint(pt1, pt2, comment=comment)
        return tuple(pts)
