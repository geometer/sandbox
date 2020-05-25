import itertools
import networkx as nx
import re
import sympy as sp

from .core import CoreScene
from .property import *
from .reason import Reason
from .stats import Stats
from .util import LazyComment, divide, degree_to_string

def _synthetic_property(prop, comment, premises):
    prop.rule = 'synthetic'
    prop.reason = Reason(1 + max(p.reason.generation for p in premises), comment, premises)
    prop.reason.obsolete = all(p.reason.obsolete for p in premises)
    return prop

class ContradictionError(Exception):
    pass

class LineSet:
    class Line:
        def __init__(self):
            self.premises_graph = nx.Graph()
            self.points_on = {} # point => set of props
            self.points_not_on = {} # point => set of props

        @property
        def segments(self):
            return self.premises_graph.nodes

        def add(self, prop):
            self.premises_graph.add_edge(*prop.segments, prop=prop)
            for pt in (*prop.segments[0].points, *prop.segments[1].points):
                if pt not in self.points_on:
                    self.points_on[pt] = set()

        def same_line_explanation(self, segment0, segment1):
            edge = self.premises_graph.get_edge_data(segment0, segment1)
            if edge:
                prop = edge['prop']
                return (
                    LazyComment('%s and %s are the same line', segment0.as_line, segment1.as_line),
                    [prop]
                )
            path = nx.algorithms.shortest_path(self.premises_graph, segment0, segment1)
            pattern = ' = '.join(['%s'] * len(path))
            return (
                LazyComment(pattern, *path),
                [self.premises_graph[i][j]['prop'] for i, j in zip(path[:-1], path[1:])]
            )

        def same_line_property(self, segment0, segment1):
            comment, premises = self.same_line_explanation(segment0, segment1)
            if len(premises) == 1:
                return premises[0]
            return _synthetic_property(
                LineCoincidenceProperty(segment0, segment1, True), comment, premises
            )

        def point_on_line_property(self, segment, point):
            if point in self.points_on:
                on = True
                prop_set = self.points_on[point]
                template = '%s lies on line %s, that coincides with %s'
            elif point in self.points_not_on:
                on = False
                prop_set = self.points_not_on[point]
                template = '%s does not lie on line %s, that coincides with %s'
            else:
                return None

            candidates = []

            for seg in self.segments:
                if point in seg.points:
                    prop = PointOnLineProperty(segment, point, on)
                    comment = LazyComment(template, point, seg.as_line, segment.as_line)
                    premises = [self.same_line_property(seg, segment)]
                    candidates.append(_synthetic_property(prop, comment, premises))

            for known in prop_set:
                seg = known.segment
                if seg == segment:
                    return known
                prop = PointOnLineProperty(segment, point, on)
                comment = LazyComment(template, point, seg.as_line, segment.as_line)
                premises = [known, self.same_line_property(seg, segment)]
                candidates.append(_synthetic_property(prop, comment, premises))

            return LineSet.best_candidate(candidates)

        def non_coincidence_property(self, pt_on, pt_not_on):
            candidates = []
            for prop_not_on in self.points_not_on.get(pt_not_on):
                seg0 = prop_not_on.segment
                if pt_on in seg0.points:
                    prop = PointsCoincidenceProperty(pt_on, pt_not_on, False)
                    comment = LazyComment('points %s, %s, and %s are not collinear', pt_not_on, *seg0.points)
                    premises = [prop_not_on]
                    candidates.append(_synthetic_property(prop, comment, premises))
                for seg1 in [seg for seg in self.segments if seg != seg0 and pt_on in seg.points]:
                    prop = PointsCoincidenceProperty(pt_on, pt_not_on, False)
                    comment = LazyComment('point %s lies on line %s, %s does not', pt_on, seg0.as_line, pt_not_on)
                    premises = [self.same_line_property(seg0, seg1), prop_not_on]
                    candidates.append(_synthetic_property(prop, comment, premises))
                for prop_on in self.points_on.get(pt_on):
                    seg1 = prop_on.segment
                    prop = PointsCoincidenceProperty(pt_on, pt_not_on, False)
                    comment = LazyComment('point %s lies on line %s, %s does not', pt_on, seg0.as_line, pt_not_on)
                    if seg0 == seg1:
                        premises = [*prop_on.reason.premises, *prop_not_on.reason.premises]
                    else:
                        premises = [prop_on, self.same_line_property(seg0, seg1), prop_not_on]
                    candidates.append(_synthetic_property(prop, comment, premises))

            return LineSet.best_candidate(candidates)

    def __init__(self):
        self.__segment_to_line = {}
        self.__all_lines = []
        self.__different_lines_graph = nx.Graph()
        self.__coincidence = {}   # {point, point} => prop
        self.__collinearity = {}  # {point, point, point} => prop
        self.__point_on_line = {} # (point, segment) => prop

    def __add_same_line_property(self, prop):
        line0 = self.__segment_to_line.get(prop.segments[0])
        line1 = self.__segment_to_line.get(prop.segments[1])
        if line0 and line1:
            if line0 != line1:
                for segment in line1.segments:
                    self.__segment_to_line[segment] = line0
                line0.premises_graph.add_edges_from(line1.premises_graph.edges(data=True))
                for pt, data in line1.points_on.items():
                    known = line0.points_on.get(pt)
                    if known:
                        known.update(data)
                    else:
                        line0.points_on[pt] = data
                for pt, data in line1.points_not_on.items():
                    known = line0.points_not_on.get(pt)
                    if known:
                        known.update(data)
                    else:
                        line0.points_not_on[pt] = data
                self.__all_lines.remove(line1)
            line0.add(prop)
        elif line0:
            line0.add(prop)
            self.__segment_to_line[prop.segments[1]] = line0
        elif line1:
            line1.add(prop)
            self.__segment_to_line[prop.segments[0]] = line1
        else:
            line = LineSet.Line()
            line.add(prop)
            self.__segment_to_line[prop.segments[0]] = line
            self.__segment_to_line[prop.segments[1]] = line
            self.__all_lines.append(line)

    def __line_by_segment(self, segment):
        line = self.__segment_to_line.get(segment)
        if line is None:
            line = LineSet.Line()
            line.premises_graph.add_node(segment)
            for pt in segment.points:
                line.points_on[pt] = set()
            self.__segment_to_line[segment] = line
            self.__all_lines.append(line)
        return line

    def __add_different_lines_property(self, prop):
        line0 = self.__line_by_segment(prop.segments[0])
        line1 = self.__line_by_segment(prop.segments[1])
        edge = self.__different_lines_graph.get_edge_data(line0, line1)
        if edge is None:
            self.__different_lines_graph.add_edge(line0, line1, props={prop})
        else:
            edge['props'].add(prop)

    def __add_point_on_line_property(self, prop):
        self.__point_on_line[(prop.point, prop.segment)] = prop
        line = self.__line_by_segment(prop.segment)
        storage = line.points_on if prop.on_line else line.points_not_on
        prop_set = storage.get(prop.point)
        if prop_set:
            prop_set.add(prop)
        else:
            storage[prop.point] = {prop}

    def add(self, prop):
        if isinstance(prop, LineCoincidenceProperty):
            if prop.coincident:
                self.__add_same_line_property(prop)
            else:
                self.__add_different_lines_property(prop)
        elif isinstance(prop, PointOnLineProperty):
            self.__add_point_on_line_property(prop)
        elif isinstance(prop, PointsCollinearityProperty):
            self.__collinearity[prop.property_key] = prop
        elif isinstance(prop, PointsCoincidenceProperty):
            self.__coincidence[prop.property_key] = prop

    def coincidence_property(self, pt0, pt1):
        cached = self.__coincidence.get(frozenset([pt0, pt1]))
        if cached:
            return cached
        candidates = []
        for line in self.__all_lines:
            if pt0 in line.points_on and pt1 in line.points_not_on:
                candidates.append(line.non_coincidence_property(pt0, pt1))
            elif pt1 in line.points_on and pt0 in line.points_not_on:
                candidates.append(line.non_coincidence_property(pt1, pt0))
        return LineSet.best_candidate(candidates)

    def point_on_line_property(self, segment, point):
        prop = self.__point_on_line.get((point, segment))
        if prop:
            return prop
        line = self.__segment_to_line.get(segment)
        return line.point_on_line_property(segment, point) if line else None

    def collinearity_property(self, pt0, pt1, pt2):
        pts = (pt0, pt1, pt2)
        key = frozenset(pts)
        cached = self.__collinearity.get(key)
        if cached:
            return cached

        candidates = []
        for line in self.__all_lines:
            pt_not_on = None
            for p in pts:
                if p in line.points_on:
                    continue
                if p in line.points_not_on:
                    if pt_not_on:
                        pt_not_on = False
                        break
                    pt_not_on = p
                else:
                    pt_not_on = False
                    break

            if pt_not_on:
                on = False
                others = [p for p in pts if p != pt_not_on]
                all_pts = [pt_not_on] + others
                def comment(seg):
                    return LazyComment('%s belong to %s, %s and %s do not', pt_not_on, seg.as_line, *others)
            elif pt_not_on is None:
                on = True
                all_pts = pts
                def comment(seg):
                    return LazyComment('%s, %s, and %s belong to %s', *pts, seg.as_line)
            else:
                continue

            for seg in line.segments:
                premises = []
                for pt in all_pts:
                    if pt in seg.points:
                        continue
                    pol = self.__point_on_line.get((pt, seg))
                    if pol is None:
                        pol = line.point_on_line_property(seg, pt)
                    premises.append(pol)
                prop = PointsCollinearityProperty(*all_pts, on)
                candidates.append(_synthetic_property(prop, comment, premises))

        triangle = Scene.Triangle(pt0, pt1, pt2)
        lines = [(side, self.__segment_to_line.get(side)) for side in triangle.sides]
        lines = [lw for lw in lines if lw[1]]

        for (segment0, line0), (segment1, line1) in itertools.combinations(lines, 2):
            if line0 == line1:
                comment, premises = line0.same_line_explanation(segment0, segment1)
                prop = PointsCollinearityProperty(pt0, pt1, pt2, True)
                candidates.append(_synthetic_property(prop, comment, premises))
                continue
            data = self.__different_lines_graph.get_edge_data(line0, line1)
            if data:
                for prop in data['props']:
                    seg0, seg1 = prop.segments
                    if self.__segment_to_line[seg0] == line1:
                        seg0, seg1 = seg1, seg0
                    premises = [prop]
                    if seg0 == segment0 and seg1 == segment1:
                        comment = LazyComment('%s and %s are different lines', segment0, segment1)
                    elif seg0 == segment0:
                        comment = LazyComment('%s and %s are different lines, %s is the same as %s', segment0, segment1, seg1, segment1) 
                        premises.append(line1.same_line_property(seg1, segment1))
                    elif seg1 == segment1:
                        comment = LazyComment('%s and %s are different lines, %s is the same as %s', segment0, segment1, seg0, segment0) 
                        premises.append(line0.same_line_property(seg0, segment0))
                    else:
                        comment = LazyComment('%s and %s are different lines, %s is the same as %s, and %s is the same as %s', segment0, segment1, seg0, segment0, seg1, segment1) 
                        premises.append(line0.same_line_property(seg0, segment0))
                        premises.append(line1.same_line_property(seg1, segment1))
                    prop = PointsCollinearityProperty(pt0, pt1, pt2, False)
                    candidates.append(_synthetic_property(prop, comment, premises))

        prop = LineSet.best_candidate(candidates)
        if prop:
            self.__collinearity[key] = prop
        return prop

    @staticmethod
    def best_candidate(candidates):
        if not candidates:
            return None
        best = candidates[0]
        cost = best.reason.cost
        for cand in candidates[1:]:
            cand_cost = cand.reason.cost
            if cand_cost < cost:
                best = cand
                cost = cand_cost
        return best

    def intersection_of_lines(self, segment0, segment1):
        line0 = self.__segment_to_line.get(segment0)
        if line0 is None:
            return (None, [])
        line1 = self.__segment_to_line.get(segment1)
        #if line1 is None or line1 == line0 or self.__different_lines_graph.get_edge_data(line0, line1) is None:
        if line1 is None or line1 == line0:
            return (None, [])
        pt = next((pt for pt in line0.points_on if pt in line1.points_on), None)
        if pt is None:
            return (None, [])
        premises = []
        if pt not in segment0.points:
            premises.append(self.collinearity_property(pt, *segment0.points))
        if pt not in segment1.points:
            premises.append(self.collinearity_property(pt, *segment1.points))
        return (pt, premises)

    def lines(self):
        return list(self.__all_lines)

    def non_coincident_points(self, point):
        collection = set()
        for key in self.__coincidence:
            if point in key:
                collection.add(next(pt for pt in key if pt != point))
        for line in self.__all_lines:
            if point in line.points_on:
                collection.update(line.points_not_on)
            elif point in line.points_not_on:
                collection.update(line.points_on)
        return list(collection)

    def collinear_points(self, segment):
        line = self.__segment_to_line.get(segment)
        if line is None:
            return []
        return [pt for pt in line.points_on if pt not in segment.points]

    def not_collinear_points(self, segment):
        line = self.__segment_to_line.get(segment)
        return list(line.points_not_on.keys()) if line else []

class CircleSet:
    class Circle:
        def __init__(self, points_key):
            self.main_key = points_key
            self.keys = {points_key}
            self.points_on = set(points_key)
            self.points_inside = set()
            self.points_outside = set()

    def __init__(self, context):
        self.context = context
        self.__circle_by_key = {}
        self.__all_circles = set()

    def add_point_to_circle(self, point, circle):
        if point in circle.points_on:
            return

        old = list(circle.points_on)
        circle.points_on.add(point)
        duplicates = set()
        for pt0, pt1 in itertools.combinations(old, 2):
            dup = self.by_three_points(point, pt0, pt1, False)
            if dup and dup != circle:
                duplicates.add(dup)
        self.__merge(circle, duplicates)

    def __merge(self, circle, duplicates):
        for dup in duplicates:
            circle.keys.update(dup.keys)
            circle.points_on.update(dup.points_on)
            self.__all_circles.remove(dup)
            for key in dup.keys:
                self.__circle_by_key[key] = circle

    def by_three_points(self, pt0, pt1, pt2, create_if_not_exists):
        key = frozenset([pt0, pt1, pt2])
        circle = self.__circle_by_key.get(key)
        if circle or not create_if_not_exists:
            return circle

        existing = [circ for circ in self.__all_circles if key.issubset(circ.points_on)]
        if existing:
            circle = existing[0]
            if len(existing) > 1:
                self.__merge(circle, existing[1:])
            circle.keys.add(key)
        else:
            circle = CircleSet.Circle(key)
            self.__all_circles.add(circle)
        self.__circle_by_key[key] = circle
        return circle

    def add(self, prop):
        if isinstance(prop, PointsCollinearityProperty):
            if not prop.collinear:
                self.by_three_points(*prop.points, True)
        elif isinstance(prop, PointAndCircleProperty):
            circle = self.by_three_points(*prop.circle, True)
            if prop.location == PointAndCircleProperty.Kind.on:
                self.add_point_to_circle(prop.point, circle)
            elif prop.location == PointAndCircleProperty.Kind.inside:
                circle.points_inside.add(prop.point)
            elif prop.location == PointAndCircleProperty.Kind.outside:
                circle.points_outside.add(prop.point)

    def n_concyclic_points(self, n):
        for circle in self.__all_circles:
            for points in itertools.combinations(circle.points_on, n):
                yield (points, circle, [])

    def point_and_circle_property(self, pt, cpoints):
        circle = self.by_three_points(*cpoints, False)
        if not circle:
            return None

        if pt in circle.points_on:
            prop = PointAndCircleProperty(pt, *cpoints, PointAndCircleProperty.Kind.on)
            prop.rule = 'synthetic'
            if pt in cpoints:
                premise = self.context.not_collinear_property(*cpoints)
                prop.reason = Reason(
                    premise.reason.generation,
                    LazyComment('%s, %s, and %s are not collinear', *cpoints),
                    [premise]
                )
                prop.reason.obsolete = premise.reason.obsolete
            else:
                prop.reason = Reason(-2, LazyComment('Temp comment'), [])
                prop.reason.obsolete = False
            return prop
        elif pt in circle.points_inside:
            prop = PointAndCircleProperty(pt, *cpoints, PointAndCircleProperty.Kind.inside)
            prop.rule = 'synthetic'
            prop.reason = Reason(-2, LazyComment('Temp comment'), [])
            prop.reason.obsolete = False
            return prop
        elif pt in circle.points_outside:
            prop = PointAndCircleProperty(pt, *cpoints, PointAndCircleProperty.Kind.outside)
            prop.rule = 'synthetic'
            prop.reason = Reason(-2, LazyComment('Temp comment'), [])
            prop.reason.obsolete = False
            return prop

        return None

    def dump(self):
        for circle in self.__all_circles:
            print('circle ' + ', '.join([str(pt) for pt in circle.points_on]) + ' %d key(s)' % len(circle.keys))
        print('%d circles by %d keys' % (len(self.__all_circles), len(self.__circle_by_key)))

class CyclicOrderPropertySet:
    class Family:
        def __init__(self):
            self.cycle_set = set()
            self.premises_graph = nx.Graph()

        def explanation(self, cycle0, cycle1):
            if cycle0 not in self.cycle_set or cycle1 not in self.cycle_set:
                return (None, None)

            path = nx.algorithms.shortest_path(self.premises_graph, cycle0, cycle1)
            pattern = ' = '.join(['%s'] * len(path))
            comment = LazyComment(pattern, *path)
            premises = [self.premises_graph.get_edge_data(i, j)['prop'] for i, j in zip(path[:-1], path[1:])]
            return (comment, premises)

    def __init__(self):
        self.families = []

    def __find_by_cycle(self, cycle):
        for fam in self.families:
            if cycle in fam.cycle_set:
                return (fam, True)
            if cycle.reversed in fam.cycle_set:
                return (fam, False)
        return (None, None)

    def add(self, prop):
        if hasattr(prop, 'rule') and prop.rule == 'synthetic':
            return
        fam0, order0 = self.__find_by_cycle(prop.cycle0)
        fam1, order1 = self.__find_by_cycle(prop.cycle1)
        if fam0 and fam1:
            if fam0 == fam1:
                # TODO: better way to report contradiction
                assert order0 == order1, 'Contradiction'
            else:
                if order0 == order1:
                    fam0.cycle_set.update(fam1.cycle_set)
                else:
                    for cycle in fam1.cycle_set:
                        fam0.cycle_set.add(cycle.reversed)
                fam0.premises_graph.add_edges_from(fam1.premises_graph.edges(data=True))
                self.families.remove(fam1)
            fam = fam0
        elif fam0:
            fam0.cycle_set.add(prop.cycle1 if order0 else prop.cycle1.reversed)
            fam = fam0
        elif fam1:
            fam1.cycle_set.add(prop.cycle0 if order1 else prop.cycle0.reversed)
            fam = fam1
        else:
            fam = CyclicOrderPropertySet.Family()
            fam.cycle_set.add(prop.cycle0)
            fam.cycle_set.add(prop.cycle1)
            self.families.append(fam)
        fam.premises_graph.add_edge(prop.cycle0, prop.cycle1, prop=prop)
        fam.premises_graph.add_edge(prop.cycle0.reversed, prop.cycle1.reversed, prop=prop)

    def explanation(self, cycle0, cycle1):
        fam, order = self.__find_by_cycle(cycle0)
        if fam is None:
            return (None, None)
        if order:
            return fam.explanation(cycle0, cycle1)
        return fam.explanation(cycle0.reversed, cycle1.reversed)

class LinearAngleSet:
    def __init__(self):
        self.properties = []

    def add(self, prop):
        self.properties.append(prop)

    def dump(self):
        values = {} # angle => num
        equivalents = {} # angle => list(angle)
        others = []
        for prop in self.properties:
            if isinstance(prop, AngleValueProperty):
                values[prop.angle] = prop.degree
            #elif isinstance(prop, AngleRatioProperty) and prop.same:
            elif isinstance(prop, AngleRatioProperty) and prop.value == 1:
                equ0 = equivalents.get(prop.angle0)
                equ1 = equivalents.get(prop.angle1)
                if equ0 and equ1:
                    if equ0 != equ1:
                        equ0 += equ1
                        for angle in equ1:
                            equivalents[angle] = equ0
                elif equ0:
                    equ0.append(prop.angle1)
                elif equ1:
                    equ1.append(prop.angle0)
                else:
                    lst = [prop.angle0, prop.angle1]
                    equivalents[prop.angle0] = lst
                    equivalents[prop.angle1] = lst
            else:
                others.append(prop)

        def angle_to_expression(angle):
            val = values.get(angle)
            if val is not None:
                return val
            equi_set = equivalents.get(angle)
            if equi_set:
                angle = equi_set[0]
            return sp.Symbol(str(angle))

        equations = [prop.equation(angle_to_expression) for prop in others]
        equations = [eq for eq in equations if eq != 0]

        class Group:
            def __init__(self, symbols):
                self.symbols = set(symbols)
                self.equations = []

            def update(self, other):
                self.symbols.update(other.symbols)
                self.equations += other.equations

        symbol_to_group = {}
        for eq in equations:
            groups = list(set(filter(None, [symbol_to_group.get(sym) for sym in eq.free_symbols])))
            if groups:
                the_group = groups[0]
                for gro in groups[1:]:
                    the_group.update(gro)
                    for sym in gro.symbols:
                        symbol_to_group[sym] = the_group
                the_group.symbols.update(eq.free_symbols)
            else:
                the_group = Group(eq.free_symbols)
            for sym in eq.free_symbols:
                symbol_to_group[sym] = the_group
            the_group.equations.append(eq)

#        for eq in subset.equations:
#            print(eq)
        #print('Total: %d symbols' % len(symbols))
        print('Total: %d equations' % len(equations))
        for group in set(symbol_to_group.values()):
            print('Group: %d symbols' % len(group.symbols))
            print('Group: %d equations' % len(group.equations))
            if len(group.equations) < 10:
                for eq in group.equations:
                    print('%s' % eq)
            #solution = sp.solve(group.equations)
            solution = sp.groebner(group.equations, *group.symbols)
            #print(solution)
#        for elt in solution.items():
#            print(elt)
#        print('Total: %d elements' % len(solution))

class AngleRatioPropertySet:
    class CommentFromPath:
        def __init__(self, path, premises, multiplier, angle_to_ratio):
            self.path = path
            self.premises = [None] + premises
            self.multiplier = multiplier
            self.angle_to_ratio = dict(angle_to_ratio)

        def html(self):
            pattern = []
            params = []
            for vertex, premise in zip(self.path, self.premises):
                if premise:
                    if isinstance(premise, AngleRatioProperty) and premise.same:
                        pattern.append(' ≡ ')
                    else:
                        pattern.append(' = ')
                if isinstance(vertex, CoreScene.Angle):
                    coef = divide(self.multiplier, self.angle_to_ratio[vertex])
                    if coef == 1:
                        pattern.append('%s')
                        params.append(vertex)
                    else:
                        pattern.append('%s %s')
                        params.append(coef)
                        params.append(vertex)
                else:
                    pattern.append(degree_to_string(self.multiplier * vertex))
            return LazyComment(''.join(pattern), *params)

        def __str__(self):
            pattern = []
            params = []
            for vertex, premise in zip(self.path, self.premises):
                if premise:
                    if isinstance(premise, AngleRatioProperty) and premise.same:
                        pattern.append(' ≡ ')
                    else:
                        pattern.append(' = ')
                if isinstance(vertex, CoreScene.Angle):
                    coef = divide(self.multiplier, self.angle_to_ratio[vertex])
                    if coef == 1:
                        pattern.append('%s')
                        params.append(vertex)
                    else:
                        pattern.append('%s %s')
                        params.append(coef)
                        params.append(vertex)
                else:
                    pattern.append(degree_to_string(self.multiplier * vertex))
            return str(LazyComment(''.join(pattern), *params))

    class Family:
        def __init__(self):
            self.angle_to_ratio = {}
            self.premises_graph = nx.Graph()
            self.degree = None

        def explanation_from_path(self, path, multiplier):
            premises = [self.premises_graph.get_edge_data(i, j)['prop'] for i, j in zip(path[:-1], path[1:])]
            return (AngleRatioPropertySet.CommentFromPath(path, premises, multiplier, self.angle_to_ratio), premises)

        def value_property(self, angle):
            ratio = self.angle_to_ratio.get(angle)
            if ratio is None:
                return None
            edge = self.premises_graph.get_edge_data(angle, self.degree)
            if edge:
                return edge['prop']
            path = nx.algorithms.shortest_path(self.premises_graph, angle, self.degree)
            comment, premises = self.explanation_from_path(path, ratio)
            prop = AngleValueProperty(angle, self.degree * ratio)
            return _synthetic_property(prop, comment, premises)

        def value_properties(self):
            properties = []
            for angle, ratio in self.angle_to_ratio.items():
                edge = self.premises_graph.get_edge_data(angle, self.degree)
                if edge:
                    properties.append(edge['prop'])
                    continue
                path = nx.algorithms.shortest_path(self.premises_graph, angle, self.degree)
                comment, premises = self.explanation_from_path(path, ratio)
                prop = AngleValueProperty(angle, self.degree * ratio)
                properties.append(_synthetic_property(prop, comment, premises))
            return properties

        def value_properties_for_degree(self, degree):
            properties = []
            for angle, ratio in self.angle_to_ratio.items():
                if self.degree * ratio != degree:
                    continue
                edge = self.premises_graph.get_edge_data(angle, self.degree)
                if edge:
                    properties.append(edge['prop'])
                    continue
                path = nx.algorithms.shortest_path(self.premises_graph, angle, self.degree)
                comment, premises = self.explanation_from_path(path, ratio)
                prop = AngleValueProperty(angle, degree)
                properties.append(_synthetic_property(prop, comment, premises))
            return properties

        def congruent_angles_with_vertex(self):
            reverse_map = {}
            for angle, ratio in self.angle_to_ratio.items():
                if angle.vertex is None:
                    continue
                rs = reverse_map.get(ratio)
                if rs:
                    rs.append(angle)
                else:
                    reverse_map[ratio] = [angle]
            for ar in reverse_map.values():
                for angle0, angle1 in itertools.combinations(ar, 2):
                    yield (angle0, angle1)

        def same_triple_ratio_properties(self):
            angles_map = {}
            for item in self.angle_to_ratio.items():
                if item[0].vertex is None:
                    continue
                key = item[0].point_set
                rs = angles_map.get(key)
                if rs:
                    rs.append(item)
                else:
                    angles_map[key] = [item]
            for ar in angles_map.values():
                for (angle0, ratio0), (angle1, ratio1) in itertools.combinations(ar, 2):
                    edge = self.premises_graph.get_edge_data(angle0, angle1)
                    if edge:
                        yield edge['prop']
                        continue
                    path = nx.algorithms.shortest_path(self.premises_graph, angle0, angle1)
                    comment, premises = self.explanation_from_path(path, ratio0)
                    prop = AngleRatioProperty(angle0, angle1, divide(ratio0, ratio1))
                    yield _synthetic_property(prop, comment, premises)

        def add_value_property(self, prop):
            ratio = self.angle_to_ratio.get(prop.angle)
            if ratio and self.degree:
                # TODO: better way to report contradiction
                assert prop.degree == ratio * self.degree, 'Contradiction'
            elif ratio:
                self.degree = divide(prop.degree, ratio)
            elif self.degree:
                self.angle_to_ratio[prop.angle] = divide(prop.degree, self.degree)
            else:
                self.angle_to_ratio[prop.angle] = 1
                self.degree = prop.degree
            self.premises_graph.add_edge(prop.angle, self.degree, prop=prop)

        def add_ratio_property(self, prop):
            ratio0 = self.angle_to_ratio.get(prop.angle0)
            ratio1 = self.angle_to_ratio.get(prop.angle1)
            if ratio0 and ratio1:
                # TODO: better way to report contradiction
                assert ratio0 == ratio1 * prop.value, 'Contradiction'
            elif ratio0:
                self.angle_to_ratio[prop.angle1] = divide(ratio0, prop.value)
            elif ratio1:
                self.angle_to_ratio[prop.angle0] = ratio1 * prop.value
            else:
                self.angle_to_ratio[prop.angle0] = prop.value
                self.angle_to_ratio[prop.angle1] = 1
            self.premises_graph.add_edge(prop.angle0, prop.angle1, prop=prop)

    def __init__(self):
        self.angle_to_family = {}
        self.family_with_degree = None
        self.__value_cache = {} # angle => prop
        self.__ratio_cache = {} # {angle, angle} => prop

    def value_property(self, angle):
        prop = self.__value_cache.get(angle)
        if prop:
            return prop
        fam = self.family_with_degree
        prop = fam.value_property(angle) if fam else None
        if prop:
            self.__value_cache[angle] = prop
        return prop

    def value_properties(self):
        fam = self.family_with_degree
        return fam.value_properties() if fam else []

    def value_properties_for_degree(self, degree):
        fam = self.family_with_degree
        return fam.value_properties_for_degree(degree) if fam else []

    def ratio_property(self, angle0, angle1):
        key = frozenset((angle0, angle1))
        cached = self.__ratio_cache.get(key)
        if cached:
            return cached
        prop = self.__ratio_property(angle0, angle1)
        if prop:
            self.__ratio_cache[key] = prop
        return prop

    def __ratio_property(self, angle0, angle1):
        fam = self.angle_to_family.get(angle0)
        if fam is None or angle1 not in fam.angle_to_ratio:
            return None
        edge = fam.premises_graph.get_edge_data(angle0, angle1)
        if edge:
            return edge['prop']
        path = nx.algorithms.shortest_path(fam.premises_graph, angle0, angle1)
        coef = fam.angle_to_ratio[angle0]
        comment, premises = fam.explanation_from_path(path, coef)
        value = divide(coef, fam.angle_to_ratio[angle1])
        same = value == 1 and all(isinstance(prop, AngleRatioProperty) and prop.same for prop in [fam.premises_graph.get_edge_data(i, j)['prop'] for i, j in zip(path[:-1], path[1:])])
        prop = AngleRatioProperty(angle0, angle1, value, same=same)
        return _synthetic_property(prop, comment, premises)

    def same_triple_ratio_properties(self):
        for fam in set(self.angle_to_family.values()):
            for prop in fam.same_triple_ratio_properties():
                yield prop

    def congruent_angles_with_vertex(self):
        for fam in set(self.angle_to_family.values()):
            for angle in fam.congruent_angles_with_vertex():
                yield angle

    def congruent_angles_for(self, angle):
        fam = self.angle_to_family.get(angle)
        if fam:
            ratio = fam.angle_to_ratio[angle]
            for a, r in fam.angle_to_ratio.items():
                if r == ratio and a != angle:
                    yield a

    def add(self, prop):
        if hasattr(prop, 'rule') and prop.rule == 'synthetic':
            return
        if isinstance(prop, AngleRatioProperty):
            self.__add_ratio_property(prop)
        elif isinstance(prop, AngleValueProperty):
            self.__add_value_property(prop)

    def __add_value_property(self, prop):
        self.__value_cache[prop.angle] = prop
        if prop.degree == 0:
            # TODO: implement special families
            return
        fam = self.angle_to_family.get(prop.angle)
        if fam and self.family_with_degree:
            if fam != self.family_with_degree:
                coef = divide(prop.degree, self.family_with_degree.degree * fam.angle_to_ratio[prop.angle])
                if coef != 1:
                    for key in fam.angle_to_ratio:
                        fam.angle_to_ratio[key] *= coef
                self.family_with_degree.angle_to_ratio.update(fam.angle_to_ratio)
                for key in self.angle_to_family:
                    if self.angle_to_family[key] == fam:
                        self.angle_to_family[key] = self.family_with_degree
                self.family_with_degree.premises_graph.add_edges_from(fam.premises_graph.edges(data=True))
        elif fam:
            self.family_with_degree = fam
        elif self.family_with_degree:
            self.angle_to_family[prop.angle] = self.family_with_degree
        else:
            self.family_with_degree = AngleRatioPropertySet.Family()
            self.angle_to_family[prop.angle] = self.family_with_degree
        self.family_with_degree.add_value_property(prop)

    def __add_ratio_property(self, prop):
        fam0 = self.angle_to_family.get(prop.angle0)
        fam1 = self.angle_to_family.get(prop.angle1)
        if fam0 and fam1:
            fam0.add_ratio_property(prop)
            if fam0 != fam1:
                if fam1 == self.family_with_degree:
                    fam0, fam1 = fam1, fam0
                    coef = divide(fam0.angle_to_ratio[prop.angle1] * prop.value, fam1.angle_to_ratio[prop.angle0])
                else:
                    coef = divide(fam0.angle_to_ratio[prop.angle0], prop.value * fam1.angle_to_ratio[prop.angle1])
                if coef != 1:
                    for key in fam1.angle_to_ratio:
                        fam1.angle_to_ratio[key] *= coef
                fam0.angle_to_ratio.update(fam1.angle_to_ratio)
                for key in self.angle_to_family:
                    if self.angle_to_family[key] == fam1:
                        self.angle_to_family[key] = fam0
                fam0.premises_graph.add_edges_from(fam1.premises_graph.edges(data=True))
        elif fam0:
            fam0.add_ratio_property(prop)
            self.angle_to_family[prop.angle1] = fam0
        elif fam1:
            fam1.add_ratio_property(prop)
            self.angle_to_family[prop.angle0] = fam1
        else:
            fam = AngleRatioPropertySet.Family()
            fam.add_ratio_property(prop)
            self.angle_to_family[prop.angle0] = fam
            self.angle_to_family[prop.angle1] = fam

class LengthRatioPropertySet:
    class Family:
        def __init__(self):
            self.ratio_value = None
            self.ratio_set = set()
            self.premises_graph = nx.Graph()

        def add_ratio(self, ratio):
            self.ratio_set.add(ratio)

        def merge(self, other):
            if self.ratio_value is not None:
                # TODO: better way to report contradiction
                assert other.ratio_value is None or self.ratio_value == other.ratio_value, 'Contradiction'
            elif other.ratio_value is not None:
                self.ratio_value = other.ratio_value

            self.ratio_set.update(other.ratio_set)
            self.premises_graph.add_edges_from(other.premises_graph.edges(data=True))

        def find_ratio(self, ratio):
            if ratio in self.ratio_set:
                return 1
            if (ratio[1], ratio[0]) in self.ratio_set:
                return -1
            return 0

        def explanation(self, ratio0, ratio1):
            path = nx.algorithms.shortest_path(self.premises_graph, ratio0, ratio1)
            pattern = ' = '.join(['|%s| / |%s|' if len(v) == 2 else '%s' for v in path])
            comment = LazyComment(pattern, *sum(path, ()))
            premises = [self.premises_graph.get_edge_data(i, j)['prop'] for i, j in zip(path[:-1], path[1:])]
            return (comment, premises)

        def value_explanation(self, ratio):
            return self.explanation(ratio, (self.ratio_value, ))

    def __init__(self):
        self.families = []
        self.ratio_to_family = {}
        self.__cache = {} # (segment, segment) => (prop, value)
        self.proportional_lengths = {} # {segment, segment} => ProportionalLengthsProperty

    def __add_lr(self, prop, ratio, value):
        def add_property_to(fam):
            fam.premises_graph.add_edge(ratio, (value, ), prop=prop)

        fam0 = self.ratio_to_family.get(ratio)
        fam1 = self.ratio_to_family.get(value)
        if fam0 and fam1:
            if fam0 != fam1:
                fam0.merge(fam1)
                self.families.remove(fam1)
                for k in list(self.ratio_to_family.keys()):
                    if self.ratio_to_family[k] == fam1:
                        self.ratio_to_family[k] = fam0
            add_property_to(fam0)
        elif fam0:
            #TODO: better way to report contradiction
            assert fam0.ratio_value is None or fam0.ratio_value == value, 'Contradiction'
            fam0.ratio_value = value
            add_property_to(fam0)
            self.ratio_to_family[value] = fam0
        elif fam1:
            fam1.add_ratio(ratio)
            add_property_to(fam1)
            self.ratio_to_family[ratio] = fam1
        else:
            fam = LengthRatioPropertySet.Family()
            fam.ratio_value = value
            fam.add_ratio(ratio)
            add_property_to(fam)
            self.families.append(fam)
            self.ratio_to_family[ratio] = fam
            self.ratio_to_family[value] = fam

    def __add_elr(self, prop):
        ratio0 = (prop.segments[0], prop.segments[1])
        ratio1 = (prop.segments[2], prop.segments[3])

        def add_property_to(fam):
            fam.premises_graph.add_edge(ratio0, ratio1, prop=prop)

        fam0 = self.ratio_to_family.get(ratio0)
        fam1 = self.ratio_to_family.get(ratio1)
        if fam0 and fam1:
            if fam0 != fam1:
                fam0.merge(fam1)
                self.families.remove(fam1)
                for k in list(self.ratio_to_family.keys()):
                    if self.ratio_to_family[k] == fam1:
                        self.ratio_to_family[k] = fam0
            add_property_to(fam0)
        elif fam0:
            fam0.add_ratio(ratio1)
            add_property_to(fam0)
            self.ratio_to_family[ratio1] = fam0
        elif fam1:
            fam1.add_ratio(ratio0)
            add_property_to(fam1)
            self.ratio_to_family[ratio0] = fam1
        else:
            fam = LengthRatioPropertySet.Family()
            fam.add_ratio(ratio0)
            fam.add_ratio(ratio1)
            add_property_to(fam)
            self.families.append(fam)
            self.ratio_to_family[ratio0] = fam
            self.ratio_to_family[ratio1] = fam

    def add(self, prop):
        if hasattr(prop, 'rule') and prop.rule == 'synthetic':
            return
        if isinstance(prop, EqualLengthRatiosProperty):
            self.__add_elr(prop)
        elif isinstance(prop, LengthRatioProperty):
            ratio = (prop.segment0, prop.segment1)
            value = prop.value
            self.__add_lr(prop, ratio, value)
            self.__cache[ratio] = (prop, value)
            ratio = (prop.segment1, prop.segment0)
            value = divide(1, prop.value)
            self.__add_lr(prop, ratio, value)
            self.__cache[ratio] = (prop, value)
        elif isinstance(prop, ProportionalLengthsProperty):
            self.proportional_lengths[prop.property_key] = prop

    def contains(self, ratio0, ratio1):
        fam = self.ratio_to_family.get(ratio0)
        return fam and ratio1 in fam.ratio_set

    def explanation(self, ratio0, ratio1):
        fam = self.ratio_to_family.get(ratio0)
        if fam is None or ratio1 not in fam.ratio_set:
            return (None, None)
        return fam.explanation(ratio0, ratio1)

    def value_explanation(self, ratio):
        fam = self.ratio_to_family.get(ratio)
        if fam is None:
            return (None, None)
        return fam.value_explanation(ratio)

    def values(self):
        for fam in set(self.ratio_to_family.values()):
            if fam.ratio_value is None or fam.ratio_value < 1:
                continue

            unique = set() if fam.ratio_value == 1 else None
            for ratio in fam.ratio_set:
                if unique is not None:
                    key = frozenset(ratio)
                    if key in unique:
                        continue
                    unique.add(key)
                yield (*ratio, fam.ratio_value)

    def value_properties(self):
        for fam in set(self.ratio_to_family.values()):
            if fam.ratio_value is None or fam.ratio_value < 1:
                continue

            unique = set() if fam.ratio_value == 1 else None
            for ratio in fam.ratio_set:
                if unique is not None:
                    key = frozenset(ratio)
                    if key in unique:
                        continue
                    unique.add(key)
                comment, premises = fam.value_explanation(ratio)
                if len(premises) == 1:
                    yield premises[0]
                else:
                    prop = LengthRatioProperty(*ratio, fam.ratio_value)
                    yield _synthetic_property(prop, comment, premises)

    def property_and_value(self, segment0, segment1):
        ratio = (segment0, segment1)
        key = ratio
        cached = self.__cache.get(key)
        if cached:
            return cached

        fam = self.ratio_to_family.get(ratio)
        if fam is None or fam.ratio_value is None:
            return (None, None)
        if ratio in fam.ratio_set:
            value = fam.ratio_value
        else:
            ratio = (segment1, segment0)
            value = divide(1, fam.ratio_value)
        comment, premises = fam.value_explanation(ratio)
        prop = LengthRatioProperty(*ratio, fam.ratio_value)
        prop = _synthetic_property(prop, comment, premises)
        pair = (prop, value)
        self.__cache[key] = pair
        return pair

class PropertySet:
    def __init__(self):
        self.__combined = {} # (type, key) => [prop] and type => prop
        self.__full_set = {} # prop => prop
        self.__indexes = {} # prop => number
        self.__line_set = LineSet()
        self.circles = CircleSet(self)
        self.__angle_kinds = {} # angle => prop
        self.__linear_angles = LinearAngleSet()
        self.__angle_ratios = AngleRatioPropertySet()
        self.__length_ratios = LengthRatioPropertySet()
        self.__cyclic_orders = CyclicOrderPropertySet()
        self.__similar_triangles = {} # (three points) => {(three points)}
        self.__two_points_relatively_to_line = {} # key => SameOrOppositeSideProperty

    def add(self, prop):
        def put(key):
            lst = self.__combined.get(key)
            if lst:
                lst.append(prop)
            else:
                self.__combined[key] = [prop]

        type_key = type(prop)
        put(type_key)
        for key in prop.keys():
            put((type_key, key))
        self.__full_set[prop] = prop
        self.__indexes[prop] = len(self.__indexes)
        if isinstance(prop, LinearAngleProperty):
            self.__linear_angles.add(prop)
        if type_key == AngleValueProperty:
            self.__angle_ratios.add(prop)
        elif type_key == AngleKindProperty:
            self.__angle_kinds[prop.angle] = prop
        elif type_key == AngleRatioProperty:
            self.__angle_ratios.add(prop)
        elif type_key == ProportionalLengthsProperty:
            self.__length_ratios.add(prop)
        elif type_key == LengthRatioProperty:
            self.__length_ratios.add(prop)
        elif type_key == PointsCollinearityProperty:
            self.__line_set.add(prop)
            self.circles.add(prop)
        elif type_key == PointAndCircleProperty:
            self.circles.add(prop)
        elif type_key == EqualLengthRatiosProperty:
            self.__length_ratios.add(prop)
        elif type_key == SameCyclicOrderProperty:
            self.__cyclic_orders.add(prop)
        elif type_key in (PointsCoincidenceProperty, LineCoincidenceProperty, PointOnLineProperty):
            self.__line_set.add(prop)
        elif type_key == SameOrOppositeSideProperty:
            self.__two_points_relatively_to_line[prop.property_key] = prop
        elif type_key in (SimilarTrianglesProperty, CongruentTrianglesProperty):
            for key0, key1 in zip(prop.triangle0.permutations, prop.triangle1.permutations):
                triples = self.__similar_triangles.get(key0)
                if triples:
                    triples.add(key1)
                else:
                    self.__similar_triangles[key0] = {key1}
                triples = self.__similar_triangles.get(key1)
                if triples:
                    triples.add(key0)
                else:
                    self.__similar_triangles[key1] = {key0}

    def equal_length_ratios_with_common_denominator(self):
        pairs = []
        for fam in self.__length_ratios.families:
            pairs_set = set()
            for ratio0, ratio1 in itertools.combinations(fam.ratio_set, 2):
                if ratio0[1] == ratio1[1]:
                    pairs_set.add((ratio0, ratio1))
            pairs += list(pairs_set)
        return pairs

    def list(self, property_type, keys=None):
        if keys:
            assert isinstance(keys, list)
            if len(keys) == 1:
                lst = self.__combined.get((property_type, keys[0]))
                return list(lst) if lst else []
            sublists = [self.__combined.get((property_type, k)) for k in keys]
            return list(set(itertools.chain(*[l for l in sublists if l])))
        else:
            lst = self.__combined.get(property_type)
            return list(lst) if lst else []

    def __len__(self):
        return len(self.__full_set)

    @property
    def all(self):
        return list(self.__full_set)

    def __contains__(self, prop):
        if self[prop] is not None:
            return True
        if isinstance(prop, AngleRatioProperty):
            #TODO: check ratio value for contradiction
            fam = self.__angle_ratios.angle_to_family.get(prop.angle0)
            return fam and prop.angle1 in fam.angle_to_ratio
        if isinstance(prop, AngleValueProperty) and prop.degree != 0:
            #TODO: check degree for contradiction
            fam = self.__angle_ratios.family_with_degree
            return fam and prop.angle in fam.angle_to_ratio
        #TODO: LengthRatioProperty
        #TODO: EqualLengthRatiosProperty
        #TODO: SameCyclicOrderProperty
        return False

    def index_of(self, prop):
        return self.__indexes.get(prop)

    def __getitem__(self, prop):
        existing = self.__full_set.get(prop)
        if not existing:
            if isinstance(prop, AngleRatioProperty):
                existing = self.angle_ratio_property(prop.angle0, prop.angle1)
            elif isinstance(prop, AngleValueProperty):
                existing = self.angle_value_property(prop.angle)
            elif isinstance(prop, SameCyclicOrderProperty):
                existing = self.same_cyclic_order_property(prop.cycle0, prop.cycle1)
            elif isinstance(prop, PointAndCircleProperty):
                existing = self.point_and_circle_property(prop.point, prop.circle)
            elif isinstance(prop, PointsCollinearityProperty):
                existing = self.collinearity_property(*prop.points)
            elif isinstance(prop, PointOnLineProperty):
                existing = self.point_on_line_property(prop.segment, prop.point)
        #TODO: LengthRatioProperty
        #TODO: EqualLengthRatiosProperty
        if existing and not existing.compare_values(prop):
            raise ContradictionError('different values: `%s` vs `%s`' % (prop, existing))
        return existing

    def collinearity_property(self, pt0, pt1, pt2):
        return self.__line_set.collinearity_property(pt0, pt1, pt2)

    def point_on_line_property(self, segment, pt):
        return self.__line_set.point_on_line_property(segment, pt)

    def coincidence_property(self, pt0, pt1):
        return self.__line_set.coincidence_property(pt0, pt1)

    def not_equal_property(self, pt0, pt1):
        prop = self.coincidence_property(pt0, pt1)
        return prop if prop and not prop.coincident else None

    def angle_value_property(self, angle):
        return self.__angle_ratios.value_property(angle)

    def angle_kind_property(self, angle):
        return self.__angle_kinds.get(angle)

    def nondegenerate_angle_value_properties(self):
        return self.__angle_ratios.value_properties()

    def angle_value_properties_for_degree(self, degree):
        if degree == 0:
            return [p for p in self.list(AngleValueProperty) if p.degree == 0]
        return self.__angle_ratios.value_properties_for_degree(degree)

    def angle_value_properties(self):
        return [p for p in self.list(AngleValueProperty) if p.degree == 0] + self.nondegenerate_angle_value_properties()

    def angle_ratio_property(self, angle0, angle1):
        return self.__angle_ratios.ratio_property(angle0, angle1)

    def same_triple_angle_ratio_properties(self):
        return self.__angle_ratios.same_triple_ratio_properties()

    def congruent_angles_with_vertex(self):
        return self.__angle_ratios.congruent_angles_with_vertex()

    def congruent_angles_for(self, angle):
        return self.__angle_ratios.congruent_angles_for(angle)

    def length_ratios(self, allow_zeroes):
        if allow_zeroes:
            collection = []
            for prop in self.__length_ratios.proportional_lengths.values():
                collection.append((prop.segment0, prop.segment1, prop.value))
            for seg0, seg1, value in self.__length_ratios.values():
                key = frozenset([seg0, seg1])
                if key not in self.__length_ratios.proportional_lengths:
                    collection.append((seg0, seg1, value))
            return collection
        else:
            return self.__length_ratios.values()

    def length_ratio_properties(self, allow_zeroes):
        if allow_zeroes:
            collection = []
            for prop in self.__length_ratios.value_properties():
                key = frozenset([prop.segment0, prop.segment1])
                if key not in self.__length_ratios.proportional_lengths:
                    collection.append(prop)
            return list(self.__length_ratios.proportional_lengths.values()) + collection
        else:
            return self.__length_ratios.value_properties()

    def length_ratio_property_and_value(self, segment0, segment1, allow_zeroes):
        if allow_zeroes:
            prop = self.__length_ratios.proportional_lengths.get(frozenset([segment0, segment1]))
            if prop:
                return (prop, prop.value if prop.segment0 == segment0 else divide(1, prop.value))
        return self.__length_ratios.property_and_value(segment0, segment1)

    def congruent_segments_property(self, segment0, segment1, allow_zeroes):
        if allow_zeroes:
            prop = self.__length_ratios.proportional_lengths.get(frozenset([segment0, segment1]))
            if prop:
                return prop if prop.value == 1 else None
        prop, value = self.__length_ratios.property_and_value(segment0, segment1)
        return prop if value == 1 else None

    def triangles_are_similar(self, points0, points1):
        triples = self.__similar_triangles.get(points0)
        return triples and points1 in triples

    def two_points_relatively_to_line_property(self, segment, point0, point1):
        return self.__two_points_relatively_to_line.get(SameOrOppositeSideProperty.unique_key(segment, point0, point1))

    def length_ratios_are_equal(self, segment0, segment1, segment2, segment3):
        return self.__length_ratios.contains((segment0, segment1), (segment2, segment3))

    def equal_length_ratios_property(self, segment0, segment1, segment2, segment3):
        comment, premises = self.__length_ratios.explanation((segment0, segment1), (segment2, segment3))
        if comment is None:
            return None
        if len(premises) == 1:
            return premises[0]
        prop = EqualLengthRatiosProperty(segment0, segment1, segment2, segment3)
        return _synthetic_property(prop, comment, premises)

    def same_cyclic_order_property(self, cycle0, cycle1):
        prop = SameCyclicOrderProperty(cycle0, cycle1)
        existing = self.__full_set.get(prop)
        if existing:
            return existing
        comment, premises = self.__cyclic_orders.explanation(cycle0, cycle1)
        if comment:
            return _synthetic_property(prop, comment, premises)
        return None

    def foot_of_perpendicular(self, point, segment):
        #TODO: cache not-None values (?)
        for prop in self.list(PerpendicularSegmentsProperty, [segment]):
            other = prop.segments[1] if segment == prop.segments[0] else prop.segments[0]
            if not point in other.points:
                continue
            candidate = next(pt for pt in other.points if pt != point)
            if candidate in segment.points:
                return (candidate, [prop])
            col = self.collinearity_property(*segment.points, candidate)
            if col and col.collinear:
                return (candidate, [prop, col])
        return (None, [])

    @property
    def lines(self):
        return self.__line_set.lines()

    def n_concyclic_points(self, n):
        return self.circles.n_concyclic_points(n)

    def point_and_circle_property(self, pt, cpoints):
        prop = self.__full_set.get(PointAndCircleProperty.unique_key(pt, cpoints))
        if prop:
            return prop
        return self.circles.point_and_circle_property(pt, cpoints)

    def collinear_points(self, segment):
        points = []
        for prop in [p for p in self.list(PointsCollinearityProperty, [segment]) if p.collinear]:
            points.append(next(pt for pt in prop.points if pt not in segment.points))
        return points

    def not_collinear_points(self, segment):
        points = []
        for prop in [p for p in self.list(PointsCollinearityProperty, [segment]) if not p.collinear]:
            points.append(next(pt for pt in prop.points if pt not in segment.points))
        return points

    def intersection_of_lines(self, segment0, segment1):
        if segment0 == segment1:
            return (None, [])
        return self.__line_set.intersection_of_lines(segment0, segment1)

    def stats(self):
        def type_presentation(kind):
            return kind.__doc__.strip() if kind.__doc__ else kind.__name__

        by_type = {}
        for prop in self.all:
            key = type(prop)
            by_type[key] = by_type.get(key, 0) + 1
        by_type = [(type_presentation(k), v) for k, v in by_type.items()]
        by_type.sort(key=lambda pair: -pair[1])
        others = []
        return Stats(by_type + others)

    def keys_num(self):
        return len(self.__combined)
