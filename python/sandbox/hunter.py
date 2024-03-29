import time
import itertools
import numpy as np

from . import Scene, iterative_placement
from .placement import Placement
from .property import *
from .stats import Stats
from .util import divide

ERROR = np.float64(5e-6)

class AngleWrapper:
    # arc is always >= 0
    def __init__(self, angle, arc):
        self.angle = angle
        self.arc = arc

    def __str__(self):
        return str(self.angle)

class TriangleWrapper:
    def __init__(self, pts):
        self.triangle = pts if isinstance(pts, Scene.Triangle) else Scene.Triangle(*pts)
        self.__variations = None
        self.ratios = None

    @property
    def variations(self):
        if self.__variations is None:
            pts = self.triangle.points
            self.__variations = ( \
                self, \
                TriangleWrapper((pts[0], pts[2], pts[1])), \
                TriangleWrapper((pts[1], pts[0], pts[2])), \
                TriangleWrapper((pts[1], pts[2], pts[0])), \
                TriangleWrapper((pts[2], pts[0], pts[1])), \
                TriangleWrapper((pts[2], pts[1], pts[0])) \
            )
        return self.__variations

    def __eq__(self, other) -> bool:
        return self.triangle.points == other.triangle.points

    def __str__(self):
        return str(self.triangle)

class LengthFamily:
    def __init__(self, vector: Scene.Vector, placement: Placement):
        self.base = vector
        self.placement = placement
        self.vectors = []

    def __test(self, vector: Scene.Vector) -> str:
        ratio = self.placement.length(vector) / self.placement.length(self.base)
        for i in range(1, 10):
            candidate = ratio * i
            if np.fabs(candidate - round(candidate)) < ERROR:
                return '%d/%d' % (round(candidate), i) if i > 1 else '%d' % round(candidate)
        ratio = ratio * ratio
        for i in range(1, 100):
            candidate = ratio * i
            if np.fabs(candidate - round(candidate)) < ERROR:
                if i == 1:
                    return 'SQRT(%d)' % round(candidate)
                return 'SQRT(%d/%d)' % (round(candidate), i)
        return None

    def add(self, vector: Scene.Vector) -> bool:
        test = self.__test(vector)
        if test is None:
            return False
        self.vectors.append({'vector': vector, 'comment': test})
        return True

class AngleFamily:
    def __init__(self, angle: AngleWrapper):
        self.base = angle
        self.angles = []

    def __test(self, angle: AngleWrapper) -> str:
        for addition0 in (0, 2 * np.pi, -2 * np.pi):
            for addition1 in (0, 2 * np.pi, -2 * np.pi):
                ratio = (angle.arc + addition0) / (self.base.arc + addition1)
                for i in range(1, 10):
                    candidate = ratio * i
                    if np.fabs(candidate - round(candidate)) < ERROR:
                        return '%d/%d' % (round(candidate), i) if i > 1 else '%d' % round(candidate)
        return None

    def add(self, angle: AngleWrapper) -> bool:
        test = self.__test(angle)
        if test is None:
            return False
        self.angles.append({'angle': angle, 'comment': test})
        return True

#def hunt_proportional_angles(angles):
#    families = []
#    zero_count = 0
#    for ngl in angles:
#        if ngl.arc < ERROR:
#            zero_count += 1
#            continue
#        for fam in families:
#            if fam.add(ngl):
#                break
#        else:
#            families.append(AngleFamily(ngl))
#
#    print('%d non-zero angles in %d families' % (len(angles) - zero_count, len([f for f in families if len(f.angles) > 0])))
#    for fam in families:
#        if len(fam.angles) > 0:
#            print('%s: %d angles' % (fam.base, 1 + len(fam.angles)))
#            for pair in fam.angles:
#                print('\t%s (%s)' % (pair['angle'], pair['comment']))

def hunt_coincidences(placement: Placement):
    used_points = set()
    points = placement.scene.points(max_layer='user')
    for index0, pt0 in enumerate(points):
        if pt0 in used_points:
            continue
        loc0 = placement.location(pt0)
        same_points = [pt0]
        for pt1 in points[index0 + 1:]:
            loc1 = placement.location(pt1)
            if loc1.distance_to(loc0) < ERROR:
                same_points.append(pt1)
                used_points.add(pt1)
        if len(same_points) > 1:
            print('same point: %s' % [pt.label for pt in same_points])

class Hunter:
    def __init__(self, scene, max_layer='user'):
        if isinstance(scene, Placement):
            self.placement = scene
        else:
            self.placement = iterative_placement(scene)
        self.properties = []
        self.max_layer = max_layer
        self.__hunting_time = None
        self.__point_location = {} # point -> TwoDCoordinates
        self.__segment_length = {} # segment -> number

    def __vectors(self):
        points = self.placement.scene.points(max_layer=self.max_layer)
        for point0, point1 in itertools.combinations(points, 2):
            vec = point0.vector(point1)
            if self.placement.length(vec) >= ERROR:
                yield vec

    def __triangles(self):
        points = self.placement.scene.points(max_layer=self.max_layer)
        for triple in itertools.combinations(points, 3):
            triangle = Scene.Triangle(*triple)
            sides = triangle.sides
            if all(self.__segment_length[side] > ERROR for side in sides):
                yield TriangleWrapper(triangle)

    def __lines(self):
        lines = []
        used_pairs = set()
        points = self.placement.scene.points(max_layer=self.max_layer)
        for index0, pt0 in enumerate(points):
            loc0 = self.placement.location(pt0)
            for index1, pt1 in enumerate(points[index0 + 1:], start=index0 + 1):
                if (pt0, pt1) in used_pairs:
                    continue
                loc1 = self.placement.location(pt1)
                collinear = [pt0, pt1]
                for pt2 in points[index1 + 1:]:
                    loc2 = self.placement.location(pt2)
                    area = loc0.x * (loc1.y - loc2.y) + loc1.x * (loc2.y - loc0.y) + loc2.x * (loc0.y - loc1.y)
                    if np.fabs(area) < ERROR:
                        for pt in collinear:
                            used_pairs.add((pt, pt2))
                        collinear.append(pt2)
                lines.append(collinear)

        return lines

    def __angles(self, vectors):
        for pair in itertools.combinations(vectors, 2):
            if pair[0].end == pair[1].end:
                angle = pair[0].reversed.angle(pair[1].reversed)
            elif pair[0].start == pair[1].end:
                angle = pair[0].angle(pair[1].reversed)
            elif pair[0].end == pair[1].start:
                angle = pair[0].reversed.angle(pair[1])
            elif pair[0].start == pair[1].start:
                angle = pair[0].angle(pair[1])
            else:
                continue
            arc = self.placement.angle(angle)
            if angle.vertex is None and arc > np.pi / 2:
                angle = angle.vectors[1].angle(angle.vectors[0].reversed)
                arc = np.pi - arc
            yield AngleWrapper(angle, arc)

    def __add(self, prop):
        self.properties.append(prop)

    def __hunt_collinears(self):
        for line in self.__lines():
            for triple in itertools.combinations(line, 3):
                self.__add(PointsCollinearityProperty(*triple, True))

    def __hunt_equal_segments(self):
        vectors = self.__vectors()
        families = []
        for vec in vectors:
            for fam in families:
                if np.fabs(self.placement.length(vec) - self.placement.length(fam[0])) < ERROR:
                    fam.append(vec)
                    break
            else:
                families.append([vec])

        for fam in families:
            for vec0, vec1 in itertools.combinations(fam, 2):
                self.__add(LengthRatioProperty(vec0.as_segment, vec1.as_segment, 1))

    def __hunt_proportional_segments(self, vectors):
        families = []
        for vec in vectors:
            for fam in families:
                if fam.add(vec):
                    break
            else:
                families.append(LengthFamily(vec, self.placement))

        print('%d segments in %d families' % (len(vectors), len([f for f in families if len(f.vectors) > 0])))
        for fam in families:
            if len(fam.vectors) > 0:
                print('%s: %d segments' % (fam.base, 1 + len(fam.vectors)))
                for data in fam.vectors:
                    print('\t%s (%s)' % (data['vector'], data['comment']))

    def __hunt_angle_values(self, angles):
        for ngl in angles:
            arc = ngl.arc
            frac = arc / np.pi * 12
            frac_int = int(np.round(frac))
            if np.fabs(frac - frac_int) < ERROR:
                self.__add(AngleValueProperty(ngl.angle, 15 * frac_int))

    def __hunt_angles_ratio(self, angles):
        families = []

        for ngl in angles:
            if ngl.arc < ERROR or np.fabs(ngl.arc - np.pi) < ERROR:
                continue
            for fam in families:
                ratio = ngl.arc / fam[0][0].arc
                if np.fabs(ratio - np.round(ratio)) < ERROR:
                    fam.append((ngl, int(np.round(ratio))))
                    break
            else:
                families.append([(ngl, 1)])

        for fam in families:
            for pair in itertools.combinations(fam, 2):
                ratio = divide(pair[1][1], pair[0][1])
                self.__add(AngleRatioProperty(pair[1][0].angle, pair[0][0].angle, ratio))

    def __hunt_similar_triangles(self):
        triangles = list(self.__triangles())

        def equilateral(trn):
            sides = trn.triangle.sides
            s0 = self.__segment_length[sides[0]]
            d0 = s0 - self.__segment_length[sides[1]]
            d1 = s0 - self.__segment_length[sides[2]]
            return -ERROR < d0 and d0 < ERROR and -ERROR < d1 and d1 < ERROR

        def isosceles(trn):
            sides = trn.triangle.sides
            s0 = self.__segment_length[sides[0]]
            s1 = self.__segment_length[sides[1]]
            delta = s0 - s1
            if -ERROR < delta and delta < ERROR:
                return TriangleWrapper([trn.triangle.points[i] for i in (2, 0, 1)])
            s2 = self.__segment_length[sides[2]]
            delta = s0 - s2
            if -ERROR < delta and delta < ERROR:
                return TriangleWrapper([trn.triangle.points[i] for i in (1, 0, 2)])
            delta = s1 - s2
            if -ERROR < delta and delta < ERROR:
                return trn

        equilaterals = [trn for trn in triangles if equilateral(trn)]
        for trn in equilaterals:
            equilateral_prop = EquilateralTriangleProperty(trn.triangle)
            equilateral_prop.variants = []
            self.__add(equilateral_prop)
            sides = trn.triangle.sides
            for i in range(0, 3):
                isosceles_prop = IsoscelesTriangleProperty(trn.triangle.points[i], sides[i])
                isosceles_prop.variants = [equilateral_prop]
                self.__add(isosceles_prop)

        triangles = [trn for trn in triangles if trn not in equilaterals]

        isosceles = list(filter(None, [isosceles(trn) for trn in triangles]))
        for trn in isosceles:
            isosceles_prop = IsoscelesTriangleProperty(trn.triangle.points[0], trn.triangle.sides[0])
            isosceles_prop.variants = []
            self.__add(isosceles_prop)

        def similar(trn0, trn1):
            ratios0 = trn0.ratios
            if ratios0 is None:
                sides = trn0.triangle.sides
                ratios0 = (
                    self.__segment_length[sides[0]] / self.__segment_length[sides[1]],
                    self.__segment_length[sides[0]] / self.__segment_length[sides[2]]
                )
                trn0.ratios = ratios0
            ratios1 = trn1.ratios
            if ratios1 is None:
                sides = trn1.triangle.sides
                ratios1 = (
                    self.__segment_length[sides[0]] / self.__segment_length[sides[1]],
                    self.__segment_length[sides[0]] / self.__segment_length[sides[2]]
                )
                trn1.ratios = ratios1

            delta = ratios0[0] - ratios1[0]
            if delta <= -ERROR or delta >= ERROR:
                return False
            delta = ratios0[1] - ratios1[1]
            return -ERROR < delta and delta < ERROR

        families = []
        for trn in triangles:
            found = False
            for fam in families:
                lst = [var for var in trn.variations if similar(fam[0][0], var)]
                if lst:
                    fam.append(lst)
                    break
            else:
                families.append([[trn]])

        for fam in families:
#            print('DEBUG FAM')
#            for trn in fam:
#                print('DEBUG %s' % trn.triangle)
            for lst0, lst1 in itertools.combinations(fam, 2):
                trn0 = lst0[0].triangle
                len0 = self.__segment_length[trn0.sides[0]]
                for wrapper in lst1:
                    prop = SimilarTrianglesProperty(trn0, wrapper.triangle)
                    prop.variants = []
                    self.__add(prop)
                    delta = len0 - self.__segment_length[wrapper.triangle.sides[0]]
                    if -ERROR < delta and delta < ERROR:
                        prop_congruent = CongruentTrianglesProperty(trn0, wrapper.triangle)
                        self.__add(prop_congruent)
                        prop_congruent.variants = []
                        prop.variants.append(prop_congruent)

    def stats(self):
        return Stats([
            ('Hunting time', '%.3f sec' % self.__hunting_time),
            ('Found properties', len(self.properties))
        ], 'Hunter stats')

    def hunt(self, options=('default')):
        start = time.time()
        frozen = self.placement.scene.is_frozen
        if not frozen:
            self.placement.scene.freeze()
        self.__hunt(options)
        if not frozen:
            self.placement.scene.unfreeze()
        self.__hunting_time = time.time() - start

    def __hunt(self, options):
        for pt in self.placement.scene.points(max_layer=self.max_layer):
            self.__point_location[pt] = self.placement.location(pt)
        for pt0, pt1 in itertools.combinations(self.__point_location.keys(), 2):
            loc0 = self.__point_location.get(pt0)
            loc1 = self.__point_location.get(pt1)
            self.__segment_length[pt0.segment(pt1)] = loc0.distance_to(loc1)

        all_vectors = list(self.__vectors())
        all_vectors.sort(key=lambda v: self.placement.length(v))

        all_lines = list(self.__lines())

        all_angles = list(self.__angles(all_vectors))
        all_angles.sort(key=lambda a: a.arc)

        if 'collinears' in options or 'default' in options:
            self.__hunt_collinears()

        if 'coincident_points' in options or 'default' in options:
            points = self.placement.scene.points(max_layer=self.max_layer)
            for point0, point1 in itertools.combinations(points, 2):
                vec = point0.vector(point1)
                if self.placement.length(vec) < ERROR:
                    self.__add(PointsCoincidenceProperty(point0, point1, True))

        if 'equal_segments' in options or 'default' in options:
            self.__hunt_equal_segments()

        if 'angles_ratio' in options or 'default' in options:
            self.__hunt_angles_ratio(all_angles)

        if 'angle_values' in options or 'default' in options:
            self.__hunt_angle_values(all_angles)

        if 'similar_triangles' in options or 'default' in options:
            self.__hunt_similar_triangles()

        if 'proportional_segments' in options or 'all' in options:
            self.__hunt_proportional_segments(all_vectors)

        if 'coincidences' in options or 'all' in options:
            hunt_coincidences(self.placement)

    def guessed(self, obj):
        if isinstance(obj, Scene.Angle):
            for prop in self.properties:
                if isinstance(prop, AngleValueProperty) and obj == prop.angle:
                    return prop.degree
            return None

        raise Exception('Guess not supported for objects of type %s' % type(obj).__name__)

    def dump(self):
        print('Properties:\n')
        for prop in self.properties:
            print('\t%s' % prop)
        print('\nTotal properties: %d' % len(self.properties))
