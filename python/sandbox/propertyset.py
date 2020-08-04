import itertools

import networkx as nx
import sympy as sp

from .core import CoreScene
from .figure import Circle
from .property import *
from .reason import Reason
from .rules.abstract import SyntheticPropertyRule
from .stats import Stats
from .util import LazyComment, Comment, common_endpoint, divide, other_point

def _edge_comp(v0, v1, edge):
    return edge['prop'].reason.cost

def _synthetic_property(prop, comment, premises, optimize=True):
    reason = Reason(
        SyntheticPropertyRule.instance(),
        comment,
        premises
    )
    prop.add_reason(reason, optimize=optimize)
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
                    Comment(
                        '$%{line:line0}$ and $%{line:line1}$ are the same line',
                        {'line0': segment0, 'line1': segment1}
                    ),
                    [prop]
                )
            path = nx.algorithms.dijkstra_path(self.premises_graph, segment0, segment1, weight=_edge_comp)
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
                LinesCoincidenceProperty(segment0, segment1, True), comment, premises
            )

        def point_on_line_property(self, segment, point):
            if point in self.points_on:
                on = True
                prop_set = self.points_on[point]
                template = '$%{point:pt}$ lies on line $%{line:line0}$, that coincides with $%{line:line1}$'
            elif point in self.points_not_on:
                on = False
                prop_set = self.points_not_on[point]
                template = '$%{point:pt}$ does not lie on line $%{line:line0}$, that coincides with $%{line:line1}$'
            else:
                return None

            candidates = []

            for seg in self.segments:
                if point in seg.points:
                    prop = PointOnLineProperty(point, segment, on)
                    comment = Comment(template, {'pt': point, 'line0': seg, 'line1': segment})
                    premises = [self.same_line_property(seg, segment)]
                    candidates.append(_synthetic_property(prop, comment, premises))

            for known in prop_set:
                seg = known.segment
                if seg == segment:
                    return known
                prop = PointOnLineProperty(point, segment, on)
                comment = Comment(template, {'pt': point, 'line0': seg, 'line1': segment})
                premises = [known, self.same_line_property(seg, segment)]
                candidates.append(_synthetic_property(prop, comment, premises))

            return LineSet.best_candidate(candidates)

        def non_coincidence_reasons(self, pt_on, pt_not_on):
            for prop_not_on in self.points_not_on.get(pt_not_on):
                seg0 = prop_not_on.segment
                if pt_on in seg0.points:
                    comment = Comment(
                        'two of three non-collinear points $%{point:pt0}$, $%{point:pt1}$, and $%{point:pt2}$',
                        {'pt0': pt_not_on, 'pt1': seg0.points[0], 'pt2': seg0.points[1]}
                    )
                    premises = [prop_not_on]
                    yield (comment, premises)
                for seg1 in [seg for seg in self.segments if seg != seg0 and pt_on in seg.points]:
                    comment = Comment(
                        'point $%{point:pt_on}$ lies on line $%{line:line}$, $%{point:pt_not_on}$ does not',
                        {'pt_on': pt_on, 'line': seg0, 'pt_not_on': pt_not_on}
                    )
                    premises = [self.same_line_property(seg0, seg1), prop_not_on]
                    yield (comment, premises)
                for prop_on in self.points_on.get(pt_on):
                    seg1 = prop_on.segment
                    comment = Comment(
                        'point $%{point:pt_on}$ lies on line $%{line:line}$, $%{point:pt_not_on}$ does not',
                        {'pt_on': pt_on, 'line': seg0, 'pt_not_on': pt_not_on}
                    )
                    if seg0 == seg1:
                        premises = [*prop_on.reason.premises, *prop_not_on.reason.premises]
                    else:
                        premises = [prop_on, self.same_line_property(seg0, seg1), prop_not_on]
                    yield (comment, premises)

    class Circle:
        def __init__(self):
            self.premises_graph = nx.Graph()
            self.points_on = {} # point => set of props
            self.points_inside = {} # point => set of props
            self.points_outside = {} # point => set of props

        @property
        def keys(self):
            return self.premises_graph.nodes

        def add(self, prop):
            self.premises_graph.add_edge(*prop.circle_keys, prop=prop)
            for pt in (*prop.circle_keys[0], *prop.circle_keys[1]):
                if pt not in self.points_on:
                    self.points_on[pt] = set()

        def same_circle_explanation(self, key0, key1):
            edge = self.premises_graph.get_edge_data(key0, key1)
            if edge:
                prop = edge['prop']
                return (
                    LazyComment('%s and %s are the same circle', key0, key1),
                    [prop]
                )
            path = nx.algorithms.dijkstra_path(self.premises_graph, key0, key1, weight=_edge_comp)
            pattern = ' = '.join(['%s'] * len(path))
            return (
                LazyComment(pattern, *path),
                [self.premises_graph[i][j]['prop'] for i, j in zip(path[:-1], path[1:])]
            )

        def same_circle_property(self, key0, key1):
            comment, premises = self.same_circle_explanation(key0, key1)
            if len(premises) == 1:
                return premises[0]
            return _synthetic_property(
                CircleCoincidenceProperty(key0, key1, True), comment, premises
            )

        def point_on_circle_property(self, pt, key):
            for prop in self.points_on[pt]:
                if prop.circle_key == key:
                    return prop
            candidates = []
            for prop in self.points_on[pt]:
                premises = [prop, self.same_circle_property(prop.circle_key, key)]
                candidates.append(_synthetic_property(
                    PointAndCircleProperty(pt, *key, PointAndCircleProperty.Kind.on),
                    LazyComment('%s lies on %s that coincides with %s', pt, prop.circle_key, key),
                    premises
                ))
            return LineSet.best_candidate(candidates)

        def concyclicity_property(self, *pts):
            pt_patterns = ['$%{point:' + str(i) + '}$' for i in range(0, len(pts))]
            pattern = ', '.join(pt_patterns[:-1]) + ', and ' + pt_patterns[-1] + ' lie on $%{circle:circle}$'
            common_params = dict((str(index), pt) for index, pt in enumerate(pts))
            candidates = []
            for key in self.keys:
                premises = []
                for pt in pts:
                    if pt in key:
                        continue
                    premises.append(self.point_on_circle_property(pt, key))
                params = dict(common_params)
                params['circle'] = Circle(*key)
                candidates.append(_synthetic_property(
                    ConcyclicPointsProperty(*pts),
                    Comment(pattern, params),
                    premises
                ))
            return LineSet.best_candidate(candidates)

    def __init__(self):
        self.__segment_to_line = {}
        self.__key_to_circle = {}
        self.__all_lines = []
        self.__all_circles = []
        self.__different_lines = {} # {line, line} => [props]
        self.__coincidence = {}   # {point, point} => prop
        self.__lines_coincidence = {} # {segment, segment} => prop
        self.__collinearity = {}  # {point, point, point} => prop
        self.__concyclicity = {}  # {point, point, point, point} => prop
        self.__point_on_line = {} # (point, segment) => prop
        self.__point_and_circle = {} # (point, set of three points) => prop
        self.__lines_intersection = {} # ({segment, segment}, crossing_point) => prop

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
                for key in list(self.__different_lines.keys()):
                    if line1 in key:
                        new_key = frozenset([next(l for l in key if l != line1), line0])
                        self.__different_lines[new_key] = self.__different_lines.pop(key)

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

    def __add_same_circle_property(self, prop):
        circle0 = self.__key_to_circle.get(prop.circle_keys[0])
        circle1 = self.__key_to_circle.get(prop.circle_keys[1])
        if circle0 and circle1:
            if circle0 != circle1:
                for key in circle1.keys:
                    self.__key_to_circle[key] = circle0
                circle0.premises_graph.add_edges_from(circle1.premises_graph.edges(data=True))
                for pt, data in circle1.points_on.items():
                    known = circle0.points_on.get(pt)
                    if known:
                        known.update(data)
                    else:
                        circle0.points_on[pt] = data
                for pt, data in circle1.points_inside.items():
                    known = circle0.points_inside.get(pt)
                    if known:
                        known.update(data)
                    else:
                        circle0.points_inside[pt] = data
                for pt, data in circle1.points_outside.items():
                    known = circle0.points_outside.get(pt)
                    if known:
                        known.update(data)
                    else:
                        circle0.points_outside[pt] = data
                self.__all_circles.remove(circle1)
            circle0.add(prop)
        elif circle0:
            circle0.add(prop)
            self.__key_to_circle[prop.circle_keys[1]] = circle0
        elif circle1:
            circle1.add(prop)
            self.__key_to_circle[prop.circle_keys[0]] = circle1
        else:
            circle = LineSet.Circle()
            circle.add(prop)
            self.__key_to_circle[prop.circle_keys[0]] = circle
            self.__key_to_circle[prop.circle_keys[1]] = circle
            self.__all_circles.append(circle)

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

    def __circle_by_key(self, key):
        circle = self.__key_to_circle.get(key)
        if circle is None:
            circle = LineSet.Circle()
            circle.premises_graph.add_node(key)
            for pt in key:
                circle.points_on[pt] = set()
            self.__key_to_circle[key] = circle
            self.__all_circles.append(circle)
        return circle

    def __add_different_lines_property(self, prop):
        line0 = self.__line_by_segment(prop.segments[0])
        line1 = self.__line_by_segment(prop.segments[1])
        key = frozenset((line0, line1))
        ar = self.__different_lines.get(key)
        if ar:
            ar.append(prop)
        else:
            self.__different_lines[key] = [prop]

    def __add_point_on_line_property(self, prop):
        self.__point_on_line[(prop.point, prop.segment)] = prop
        line = self.__line_by_segment(prop.segment)
        storage = line.points_on if prop.on_line else line.points_not_on
        prop_set = storage.get(prop.point)
        if prop_set:
            prop_set.add(prop)
        else:
            storage[prop.point] = {prop}

    def __add_point_and_circle_property(self, prop):
        self.__point_and_circle[(prop.point, prop.circle_key)] = prop
        circle = self.__circle_by_key(prop.circle_key)
        if prop.location == PointAndCircleProperty.Kind.on:
            storage = circle.points_on
        elif prop.location == PointAndCircleProperty.Kind.inside:
            storage = circle.points_inside
        elif prop.location == PointAndCircleProperty.Kind.outside:
            storage = circle.points_outside
        prop_set = storage.get(prop.point)
        if prop_set:
            prop_set.add(prop)
        else:
            storage[prop.point] = {prop}

    def __insert_prop__(self, prop):
        if isinstance(prop, LinesCoincidenceProperty):
            self.__lines_coincidence[prop.property_key] = prop
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
        elif isinstance(prop, CircleCoincidenceProperty):
            if prop.coincident:
                self.__add_same_circle_property(prop)
            else:
                #TODO: implement
                pass
        elif isinstance(prop, PointAndCircleProperty):
            self.__add_point_and_circle_property(prop)
        elif isinstance(prop, ConcyclicPointsProperty):
            self.__concyclicity[frozenset(prop.points)] = prop

    def __non_coincidence_property_reasons(self, line, pt_on, pt_not_on):
        for key in [seg for seg in line.segments if pt_on not in seg.points]:
            col = self.collinearity_property(pt_on, *key.points)
            ncol = self.collinearity_property(pt_not_on, *key.points)
            comment = Comment(
                'point $%{point:pt_on}$ lies on line $%{line:line}$, $%{point:pt_not_on}$ does not',
                {'pt_on': pt_on, 'pt_not_on': pt_not_on, 'line': key}
            )
            yield (comment, [col, ncol])

    def coincidence_property(self, pt0, pt1, use_cache=True):
        if use_cache:
            key = frozenset([pt0, pt1])
            cached = self.__coincidence.get(key)
            if cached:
                return cached

        candidates = []
        common_lines = []
        for line in self.__all_lines:
            if pt0 in line.points_on and pt1 in line.points_not_on:
                for reason in line.non_coincidence_reasons(pt0, pt1):
                    candidates.append(reason)
                for reason in self.__non_coincidence_property_reasons(line, pt0, pt1):
                    candidates.append(reason)
            elif pt1 in line.points_on and pt0 in line.points_not_on:
                for reason in line.non_coincidence_reasons(pt1, pt0):
                    candidates.append(reason)
                for reason in self.__non_coincidence_property_reasons(line, pt1, pt0):
                    candidates.append(reason)
            elif pt0 in line.points_on and pt1 in line.points_on:
                common_lines.append(line)

        if candidates:
            prop = PointsCoincidenceProperty(pt0, pt1, False)
            for comment, premises in candidates:
                _synthetic_property(prop, comment, premises, optimize=False)
            prop.optimize()
            if use_cache:
                self.__coincidence[key] = prop
            return prop

        if len(common_lines) > 1:
            prop = None
            colli = {} # (segment, point) => collinearity
            def colli_prop(segment, point):
                key = (segment, point)
                cached = colli.get(key)
                if cached:
                    return cached
                gen = self.collinearity_property(*segment.points, point)
                colli[key] = gen
                return gen

            for line0, line1 in itertools.combinations(common_lines, 2):
                diffs = self.__different_lines.get(frozenset((line0, line1)))
                if diffs is None:
                    continue
                if prop is None:
                    prop = PointsCoincidenceProperty(pt0, pt1, True)
                for diff in diffs:
                    premises = []
                    for seg in diff.segments:
                        if pt0 not in seg.points:
                            premises.append(colli_prop(seg, pt0))
                        if pt1 not in seg.points:
                            premises.append(colli_prop(seg, pt1))
                    premises.append(diff)
                    _synthetic_property(
                        prop,
                        Comment(
                            '$%{point:pt0}$ and $%{point:pt1}$ both lie on different lines $%{line:line0}$ and $%{line:line1}$',
                            {'pt0': pt0, 'pt1': pt1, 'line0': diff.segments[0], 'line1': diff.segments[1]}
                        ),
                        premises
                    )
            return prop

        return None

    def point_on_line_property(self, segment, point, use_cache=True):
        if use_cache:
            key = (point, segment)
            prop = self.__point_on_line.get(key)
            if prop:
                return prop
        line = self.__segment_to_line.get(segment)
        prop = line.point_on_line_property(segment, point) if line else None
        if use_cache and prop:
            self.__point_on_line[key] = prop
        return prop

    def concyclicity_property(self, *pts):
        key = frozenset(pts)
        cached = self.__concyclicity.get(key)
        if cached:
            return cached
        for circle in self.circles:
            if all(pt in circle.points_on for pt in pts):
                return circle.concyclicity_property(*pts)
        return None

    def collinearity(self, pt0, pt1, pt2):
        cached = self.__collinearity.get(frozenset((pt0, pt1, pt2)))
        if cached:
            return cached.collinear

        pts = (pt0, pt1, pt2, pt0, pt1)
        for i in range(0, 3):
            vertex = pts[i]
            side = pts[i + 1].segment(pts[i + 2])
            line = self.__segment_to_line.get(side)
            if line:
                if vertex in line.points_on:
                    return True
                if vertex in line.points_not_on:
                    return False

        for line in self.__all_lines:
            if pt0 in line.points_on and pt1 in line.points_on and pt2 in line.points_on:
                return True

        return None

    def collinearity_property(self, *pts, use_cache=True):
        if use_cache:
            key = frozenset(pts)
            cached = self.__collinearity.get(key)
            if cached:
                return cached

        candidates = []

        pt_patterns = ['$%{point:' + str(i) + '}$' for i in range(0, len(pts))]
        pattern = ', '.join(pt_patterns[:-1]) + ', and ' + pt_patterns[-1] + ' belong to $%{line:line}$'
        common_params = dict((str(index), pt) for index, pt in enumerate(pts))

        for line in self.__all_lines:
            if any(pt not in line.points_on for pt in pts):
                continue
            for seg in line.segments:
                premises = []
                for pt in pts:
                    if pt in seg.points:
                        continue
                    pol = self.__point_on_line.get((pt, seg))
                    if pol is None:
                        pol = line.point_on_line_property(seg, pt)
                    premises.append(pol)
                params = dict(common_params)
                params['line'] = seg
                prop = PointsCollinearityProperty(*pts, True) if len(pts) == 3 else MultiPointsCollinearityProperty(*pts)
                candidates.append(_synthetic_property(
                    prop, Comment(pattern, params), premises
                ))

        if len(pts) > 3:
            prop = LineSet.best_candidate(candidates)
            if use_cache and prop:
                self.__collinearity[key] = prop
            return prop

        triangle = Scene.Triangle(*pts)

        pattern = '$%{point:pt0}$ and $%{point:pt1}$ are on $%{line:line}$, $%{point:pt2}$ is not'
        for vertex, side in zip(triangle.points, triangle.sides):
            line = self.__segment_to_line.get(side)
            if line is None or vertex not in line.points_not_on:
                continue

            common_params = {'pt0': side.points[0], 'pt1': side.points[1], 'pt2': vertex}
            for seg in line.segments:
                premises = []
                premises2 = []
                for pt in [*side.points, vertex]:
                    if pt not in seg.points:
                        premises.append(line.point_on_line_property(seg, pt))
                        premises2.append(self.__collinearity.get(frozenset([*seg.points, pt])))

                prop = PointsCollinearityProperty(*pts, False)
                params = dict(common_params)
                params['line'] = seg
                candidates.append(_synthetic_property(
                    prop, Comment(pattern, params), premises
                ))
                if None not in premises2:
                    prop = PointsCollinearityProperty(*pts, False)
                    candidates.append(_synthetic_property(
                        prop, Comment(pattern, params), premises2
                    ))

        lines = [(triangle.sides[i], self.__segment_to_line.get(triangle.sides[i]), triangle.points[i]) for i in range(0, 3)]
        lines = [lw for lw in lines if lw[1]]
        for (side, line, vertex) in lines:
            pnol_set = line.points_not_on.get(vertex)
            if not pnol_set:
                continue
            for pnol in pnol_set:
                premises = [pnol]
                if pnol.segment != side:
                    premises.append(line.same_line_property(pnol.segment, side))
                candidates.append(_synthetic_property(
                    PointsCollinearityProperty(*pts, False),
                    Comment(
                        '$%{point:pt}$ does not lie on $%{line:line}$',
                        {'pt': vertex, 'line': side}
                    ),
                    premises
                ))

        for (segment0, line0, _), (segment1, line1, _) in itertools.combinations(lines, 2):
            if line0 == line1:
                comment, premises = line0.same_line_explanation(segment0, segment1)
                prop = PointsCollinearityProperty(*pts, True)
                candidates.append(_synthetic_property(prop, comment, premises))
                continue
            different_lines = self.lines_coincidence_property(segment0, segment1)
            if different_lines:
                candidates.append(_synthetic_property(
                    PointsCollinearityProperty(*pts, False),
                    Comment(
                        '$lines %{line:line0}$ and $%{line:line1}$ are different',
                        {'line0': segment0, 'line1': segment1}
                    ),
                    [different_lines]
                ))

        prop = LineSet.best_candidate(candidates)
        if use_cache and prop:
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

    def intersection(self, segment0, segment1):
        if segment0 == segment1 or self.lines_coincidence(segment0, segment1) != False:
            return None
        common = common_endpoint(segment0, segment1)
        if common:
            return common

        line0 = self.__segment_to_line.get(segment0)
        if line0 is None:
            return None
        line1 = self.__segment_to_line.get(segment1)
        if line1 is None:
            return None

        return next((pt for pt in line0.points_on if pt in line1.points_on), None)

    def intersection_property(self, crossing, segment0, segment1):
        key = (frozenset((segment0, segment1)), crossing)
        if key in self.__lines_intersection:
            return self.__lines_intersection.get(key)

        if crossing in segment0.points and crossing in segment1.points:
            comment = Comment(
                '$%{point:common}$ is common point of different lines $%{line:line0}$ and $%{line:line1}$',
                {'common': crossing, 'line0': segment0, 'line1': segment1}
            )
            prop = IntersectionOfLinesProperty(crossing, segment0, segment1)
            colli = self.collinearity_property(*set(segment0.points + segment1.points))
            if colli is None:
                return None
            if colli.collinear:
                self.__lines_intersection[key] = None
                return None
            _synthetic_property(prop, comment, [colli])
            ncl = self.lines_coincidence_property(segment0, segment1)
            _synthetic_property(prop, comment, [ncl])
        else:
            premises = []
            for seg in segment0, segment1:
                if crossing not in seg.points:
                    colli = self.collinearity_property(crossing, *seg.points)
                    if colli is None:
                        return None
                    if not colli.collinear:
                        self.__lines_intersection[key] = None
                        return None
                    premises.append(colli)
            coincidence = self.lines_coincidence_property(segment0, segment1)
            if coincidence is None:
                return None
            if coincidence.coincident:
                self.__lines_intersection[key] = None
                return None
            premises.append(coincidence)

            prop = _synthetic_property(
                IntersectionOfLinesProperty(crossing, segment0, segment1),
                Comment(
                    '$%{point:pt}$ belongs to both $%{line:line0}$ and $%{line:line1}$',
                    {'pt': crossing, 'line0': segment0, 'line1': segment1}
                ),
                premises
            )
        self.__lines_intersection[key] = prop
        return prop

    @property
    def lines(self):
        return list(self.__all_lines)

    def line_for_segment(self, segment):
        return self.__segment_to_line.get(segment)

    @property
    def circles(self):
        return list(self.__all_circles)

    def non_coincident_points(self, point):
        collection = set()
        for key, value in self.__coincidence.items():
            if point in key and not value.coincident:
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

    def lines_coincidence(self, segment0, segment1):
        line0 = self.__segment_to_line.get(segment0)
        if line0 is None:
            return None
        line1 = self.__segment_to_line.get(segment1)
        if line1 is None:
            return None

        if line0 == line1:
            return True
        if self.__different_lines.get(frozenset([line0, line1])):
            return False
        return None

    def lines_coincidence_property(self, segment0, segment1, use_cache=True):
        if use_cache:
            key = frozenset([segment0, segment1])
            cached = self.__lines_coincidence.get(key)
            if cached:
                return cached

        prop = self.__lines_coincidence_property(segment0, segment1)
        if use_cache and prop:
            self.__lines_coincidence[key] = prop
        return prop

    def __lines_coincidence_property(self, segment0, segment1):
        line0 = self.__segment_to_line.get(segment0)
        if line0 is None:
            return None
        line1 = self.__segment_to_line.get(segment1)
        if line1 is None:
            return None

        if line0 == line1:
            return line0.same_line_property(segment0, segment1)

        known = self.__different_lines.get(frozenset([line0, line1]))
        if known is None:
            return None

        for prop in known:
            if segment0 in prop.segments and segment1 in prop.segments:
                return prop

        candidates = []
        for prop in known:
            seg0, seg1 = prop.segments
            if self.__segment_to_line[seg0] == line1:
                seg0, seg1 = seg1, seg0
            premises = [prop]
            params = {'line0': seg0, 'line1': seg1, 'given0': segment0, 'given1': segment1}
            if seg0 == segment0:
                pattern = '$%{line:given0}$ and $%{line:line1}$ are different lines, $%{line:line1}$ is the same as $%{line:given1}$'
                premises.append(line1.same_line_property(seg1, segment1))
            elif seg1 == segment1:
                pattern = '$%{line:given1}$ and $%{line:line0}$ are different lines, $%{line:line0}$ is the same as $%{line:given0}$'
                premises.append(line0.same_line_property(seg0, segment0))
            else:
                pattern = '$%{line:line0}$ and $%{line:line1}$ are different lines, $%{line:line0}$ is the same as $%{line:given0}$, and $%{line:line1}$ is the same as $%{line:given1}$'
                premises.append(line0.same_line_property(seg0, segment0))
                premises.append(line1.same_line_property(seg1, segment1))
            prop = LinesCoincidenceProperty(segment0, segment1, False)
            candidates.append(_synthetic_property(prop, Comment(pattern, params), premises))

        return LineSet.best_candidate(candidates)

class CyclicOrderPropertySet:
    class Family:
        def __init__(self):
            self.cycle_set = set()
            self.premises_graph = nx.Graph()
            self.path_table = None

        def create_path_table(self):
            self.path_table = dict(nx.algorithms.all_pairs_dijkstra_path(self.premises_graph, weight=_edge_comp))

        def same_order_property(self, cycle0, cycle1):
            if self.path_table:
                path = self.path_table[cycle0][cycle1]
            else:
                path = nx.algorithms.shortest_path(self.premises_graph, cycle0, cycle1)
            if len(path) == 1:
                return self.premises_graph.get_edge_data(cycle0, cycle1)['prop']
            pattern = []
            params = {}
            for index, v in enumerate(path):
                pattern.append('%' + ('{cycle:c%d}' % index))
                params['c%d' % index] = v
            comment = Comment('$' + ' =\,\!\! '.join(pattern) + '$', params)
            premises = [self.premises_graph.get_edge_data(i, j)['prop'] for i, j in zip(path[:-1], path[1:])]
            return _synthetic_property(SameCyclicOrderProperty(cycle0, cycle1), comment, premises)

    def __init__(self):
        self.families = []
        self.cache = {} # (cycle, cycle) => prop

    def create_path_table(self):
        for fam in self.families:
            fam.create_path_table()

    def __find_by_cycle(self, cycle):
        for fam in self.families:
            if cycle in fam.cycle_set:
                return fam
        return None

    def add(self, prop):
        if prop.reason and prop.reason.rule == SyntheticPropertyRule.instance():
            return
        self.cache[(prop.cycle0, prop.cycle1)] = prop
        self.cache[(prop.cycle1, prop.cycle0)] = prop
        fam0 = self.__find_by_cycle(prop.cycle0)
        fam1 = self.__find_by_cycle(prop.cycle1)
        if fam0 and fam1:
            if fam0 != fam1:
                fam0.cycle_set.update(fam1.cycle_set)
                fam0.premises_graph.add_edges_from(fam1.premises_graph.edges(data=True))
                self.families.remove(fam1)
            fam = fam0
        elif fam0:
            fam0.cycle_set.add(prop.cycle1)
            fam = fam0
        elif fam1:
            fam1.cycle_set.add(prop.cycle0)
            fam = fam1
        else:
            fam = CyclicOrderPropertySet.Family()
            fam.cycle_set.add(prop.cycle0)
            fam.cycle_set.add(prop.cycle1)
            self.families.append(fam)
        fam.premises_graph.add_edge(prop.cycle0, prop.cycle1, prop=prop)

    def compare(self, cycle0, cycle1):
        fam = self.__find_by_cycle(cycle0)
        if fam is None:
            return None
        if cycle1 in fam.cycle_set:
            return True
        if cycle1.reversed in fam.cycle_set:
            return False
        return None

    def same_order_property(self, cycle0, cycle1, use_cache=True):
        if use_cache:
            key = (cycle0, cycle1)
            cached = self.cache.get(key)
            if cached:
                return cached

        fam = self.__find_by_cycle(cycle0)
        if fam is None or cycle1 not in fam.cycle_set:
            return None
        prop = fam.same_order_property(cycle0, cycle1)
        if use_cache:
            self.cache[key] = prop
            self.cache[(cycle1, cycle0)] = prop
        return prop

class AngleRatioPropertySet:
    class CommentFromPath:
        def __init__(self, path, premises, multiplier, angle_to_ratio):
            self.path = path
            self.premises = [None] + premises
            self.multiplier = multiplier
            self.angle_to_ratio = dict(angle_to_ratio)

        def stringify(self, printer):
            return self.comment().stringify(printer)

        def __str__(self):
            return str(self.comment())

        def comment(self):
            pattern = ['$']
            params = {}
            for index, (vertex, premise) in enumerate(zip(self.path, self.premises)):
                if premise:
                    if isinstance(premise, AngleRatioProperty) and premise.same:
                        pattern.append(' \equiv ')
                    else:
                        pattern.append(' = ')
                if isinstance(vertex, CoreScene.Angle):
                    coef = divide(self.multiplier, self.angle_to_ratio[vertex])
                    if coef != 1:
                        pattern.append('%')
                        pattern.append('{multiplier:coef%d}' % index)
                        params['coef%d' % index] = coef
                    pattern.append('%')
                    pattern.append('{anglemeasure:angle%d}' % index)
                    params['angle%d' % index] = vertex
                else:
                    pattern.append('%')
                    pattern.append('{degree:degree%d}' % index)
                    params['degree%d' % index] = self.multiplier * vertex
            pattern.append('$')
            return Comment(''.join(pattern), params)

    class Family:
        def __init__(self, angle=None):
            self.angle_to_ratio = {}
            self.premises_graph = nx.Graph()
            self.degree = None
            if angle:
                self.angle_to_ratio[angle] = 1
            self.sum_props = set()
            self.path_table = None

        def create_path_table(self):
            self.path_table = dict(nx.algorithms.all_pairs_dijkstra_path(self.premises_graph, weight=_edge_comp))

        def explanation_from_path(self, path, multiplier):
            premises = [self.premises_graph.get_edge_data(i, j)['prop'] for i, j in zip(path[:-1], path[1:])]
            return (AngleRatioPropertySet.CommentFromPath(path, premises, multiplier, self.angle_to_ratio), premises)

        def ratio_property(self, angle0, angle1):
            if self.path_table:
                path = self.path_table[angle0][angle1]
            else:
                path = nx.algorithms.shortest_path(self.premises_graph, angle0, angle1)
            if len(path) == 1:
                return self.premises_graph.get_edge_data(angle0, angle1)['prop']
            coef = self.angle_to_ratio[angle0]
            comment, premises = self.explanation_from_path(path, coef)
            value = divide(coef, self.angle_to_ratio[angle1])
            same = value == 1 and all(isinstance(prop, AngleRatioProperty) and prop.same for prop in [self.premises_graph.get_edge_data(i, j)['prop'] for i, j in zip(path[:-1], path[1:])])
            prop = AngleRatioProperty(angle0, angle1, value, same=same)
            return _synthetic_property(prop, comment, premises)

        def value(self, angle):
            ratio = self.angle_to_ratio.get(angle)
            return ratio * self.degree if ratio else None

        def value_property(self, angle):
            ratio = self.angle_to_ratio.get(angle)
            if ratio is None:
                return None
            if self.path_table:
                path = self.path_table[angle][self.degree]
            else:
                path = nx.algorithms.shortest_path(self.premises_graph, angle, self.degree)
            if len(path) == 1:
                return self.premises_graph.get_edge_data(angle, self.degree)['prop']
            comment, premises = self.explanation_from_path(path, ratio)
            prop = AngleValueProperty(angle, self.degree * ratio)
            return _synthetic_property(prop, comment, premises)

        def values(self):
            pairs = []
            for angle, ratio in self.angle_to_ratio.items():
                pairs.append((angle, self.degree * ratio))
            return pairs

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

        def angles_for_degree(self, degree):
            angles = []
            for angle, ratio in self.angle_to_ratio.items():
                if ratio * self.degree == degree:
                    angles.append(angle)
            return angles

        def value_properties_for_degree(self, degree, condition):
            properties = []
            for angle, ratio in self.angle_to_ratio.items():
                if condition and not condition(angle):
                    continue
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
        self.__sum_of_angles = {} # (angle, angle, ...) => prop
        self.__sum_of_angles_2 = {} # ((fam, ratio), (fam, ratio), ...) => prop

    def create_path_table(self):
        for fam in set(self.angle_to_family.values()):
            fam.create_path_table()

    def value(self, angle):
        fam = self.family_with_degree
        return fam.value(angle) if fam else None

    def value_property(self, angle, use_cache=True):
        if use_cache:
            prop = self.__value_cache.get(angle)
            if prop:
                return prop
        fam = self.family_with_degree
        prop = fam.value_property(angle) if fam else None
        if use_cache and prop:
            self.__value_cache[angle] = prop
        return prop

    def values(self):
        fam = self.family_with_degree
        return fam.values() if fam else []

    def value_properties(self):
        fam = self.family_with_degree
        return fam.value_properties() if fam else []

    def angles_for_degree(self, degree):
        fam = self.family_with_degree
        return fam.angles_for_degree(degree) if fam else []

    def value_properties_for_degree(self, degree, condition):
        fam = self.family_with_degree
        return fam.value_properties_for_degree(degree, condition) if fam else []

    def are_congruent(self, angle0, angle1):
        fam = self.angle_to_family.get(angle0)
        if fam is None:
            return None
        ratio1 = fam.angle_to_ratio.get(angle1)
        if ratio1 is None:
            return None
        return fam.angle_to_ratio[angle0] == ratio1

    def ratio(self, angle0, angle1):
        fam = self.angle_to_family.get(angle0)
        if fam is None:
            return None
        ratio1 = fam.angle_to_ratio.get(angle1)
        if ratio1 is None:
            return None
        return divide(fam.angle_to_ratio[angle0], ratio1)

    def ratio_property(self, angle0, angle1, use_cache=True):
        if use_cache:
            key = (angle0, angle1)
            cached = self.__ratio_cache.get(key)
            if cached:
                return cached
        fam = self.angle_to_family.get(angle0)
        if fam is None or angle1 not in fam.angle_to_ratio:
            return None
        prop = fam.ratio_property(angle0, angle1)
        if use_cache and prop:
            self.__ratio_cache[key] = prop
            self.__ratio_cache[(angle1, angle0)] = prop
        return prop

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
        if prop.reason and prop.reason.rule == SyntheticPropertyRule.instance():
            return
        if isinstance(prop, AngleRatioProperty):
            self.__add_ratio_property(prop)
        elif isinstance(prop, AngleValueProperty):
            self.__add_value_property(prop)
        elif isinstance(prop, SumOfAnglesProperty):
            self.__add_sum_property(prop)

    def __add_sum_property(self, prop):
        for perm in itertools.permutations(prop.angles, len(prop.angles)):
            self.__sum_of_angles[perm] = prop
        def pair(angle):
            fam = self.angle_to_family.get(angle)
            if fam:
                return (fam, fam.angle_to_ratio[angle])
            fam = AngleRatioPropertySet.Family(angle)
            self.angle_to_family[angle] = fam
            return (fam, 1)
        key = [pair(angle) for angle in prop.angles]
        for perm in itertools.permutations(key, len(key)):
            ar = self.__sum_of_angles_2.get(perm)
            if ar:
                if prop not in ar:
                    ar.append(prop)
            else:
                self.__sum_of_angles_2[perm] = [prop]
        for fam, _ in key:
            fam.sum_props.add(prop)

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
                for sum_prop in fam.sum_props:
                    self.__add_sum_property(sum_prop)
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
                for sum_prop in fam1.sum_props:
                    self.__add_sum_property(sum_prop)
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

    def sum_of_angles(self, *angles):
        cached = self.__sum_of_angles.get(angles)
        if cached:
            return cached.degree

        key = []
        for a in angles:
            fam = self.angle_to_family.get(a)
            if fam is None:
                return None
            key.append((fam, fam.angle_to_ratio[a]))
        ar = self.__sum_of_angles_2.get(tuple(key))
        return ar[0].degree if ar else None

    def sum_of_angles_property(self, *angles, use_cache=True):
        if use_cache:
            cached = self.__sum_of_angles.get(angles)
            if cached:
                return cached

        key = []
        for a in angles:
            fam = self.angle_to_family.get(a)
            if fam is None:
                return None
            key.append((fam, fam.angle_to_ratio[a]))
        ar = self.__sum_of_angles_2.get(tuple(key))
        if ar is None:
            return None

        p0 = ['%{angle:a' + str(i) + '}' for i in range(0, len(angles))]
        p1 = ['%{angle:' + str(i) + '}' for i in range(0, len(angles))]
        pattern = '$' + ' + '.join(p0) + ' = ' + ' + '.join(p1) + ' = %{degree:sum}$'
        common_params = {'a' + str(i): angle for i, angle in enumerate(angles)}

        prop = None
        for known in ar:
            if prop is None:
                prop = SumOfAnglesProperty(*angles, degree=known.degree)
            params = dict(common_params)
            premises = [known]
            ka = list(known.angles)
            known_angles = []
            for fam, ratio in key:
                a = next(a for a in ka if fam.angle_to_ratio.get(a) == ratio)
                ka.remove(a)
                known_angles.append(a)
            params.update({str(i): a for i, a in enumerate(known_angles)})
            params['sum'] = known.degree
            comment = Comment(pattern, params)
            for angle, a in zip(angles, known_angles):
                if angle != a:
                    premises.append(self.ratio_property(angle, a))
            _synthetic_property(prop, comment, premises, optimize=False)

        if prop:
            prop.optimize()

        if use_cache and prop:
            for perm in itertools.permutations(angles, len(angles)):
                self.__sum_of_angles[perm] = prop

        return prop

class LengthRatioPropertySet:
    class Family:
        def __init__(self):
            self.ratio_value = None
            self.ratio_set = set()
            self.premises_graph = nx.Graph()
            self.path_table = None

        def add_ratio(self, ratio):
            self.ratio_set.add(ratio)

        def merge(self, other):
            if self.ratio_value is not None:
                # TODO: better way to report contradiction
                assert other.ratio_value is None or sp.N(self.ratio_value) == sp.N(other.ratio_value), 'Contradiction'
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

        def create_path_table(self):
            self.path_table = dict(nx.algorithms.all_pairs_dijkstra_path(self.premises_graph, weight=_edge_comp))

        def explanation(self, ratio0, ratio1):
            if self.path_table:
                path = self.path_table[ratio0][ratio1]
            else:
                path = nx.algorithms.shortest_path(self.premises_graph, ratio0, ratio1)

            pattern = []
            params = {}
            for index, v in enumerate(path):
                if len(v) == 2:
                    pattern.append('|%s{segment:num%d}| / |%s{segment:denom%d}|' % ('%', index, '%', index))
                    params['num%d' % index] = v[0]
                    params['denom%d' % index] = v[1]
                else:
                    pattern.append('%s{number:number%d}' % ('%', index))
                    params['number%d' % index] = v[0]
            premises = [self.premises_graph.get_edge_data(i, j)['prop'] for i, j in zip(path[:-1], path[1:])]
            return (Comment('$' + ' = '.join(pattern) + '$', params), premises)

        def value_explanation(self, ratio):
            return self.explanation(ratio, (self.ratio_value, ))

    def __init__(self):
        self.families = []
        self.ratio_to_family = {}
        self.__cache = {} # (segment, segment) => (prop, value)
        self.__ratio_cache = {} # (ratio, ratio) => EqualLengthRatiosProperty
        self.proportional_lengths = {} # {segment, segment} => ProportionalLengthsProperty

    def create_path_table(self):
        for fam in self.families:
            fam.create_path_table()

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
        self.__ratio_cache[frozenset((ratio0, ratio1))] = prop

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
        if prop.reason.rule == SyntheticPropertyRule.instance():
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

    def equality_property(self, ratio0, ratio1, use_cache=True):
        if use_cache:
            key = frozenset((ratio0, ratio1))
            cached = self.__ratio_cache.get(key)
            if cached:
                return cached
        fam = self.ratio_to_family.get(ratio0)
        if fam is None or ratio1 not in fam.ratio_set:
            return None
        comment, premises = fam.explanation(ratio0, ratio1)
        if len(premises) == 1:
            return premises[0]
        prop = _synthetic_property(
            EqualLengthRatiosProperty(*ratio0, *ratio1),
            comment,
            premises
        )
        if use_cache:
            self.__ratio_cache[key] = prop
        return prop

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

    def congruency_properties(self):
        for fam in set(self.ratio_to_family.values()):
            if fam.ratio_value != 1:
                continue

            unique = set()
            for ratio in fam.ratio_set:
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
        _synthetic_property(prop, comment, premises)
        pair = (prop, value)
        self.__cache[key] = pair
        return pair

class PropertySet(LineSet):
    def __init__(self, points):
        super().__init__()
        self.points = list(points)
        self.__combined = {} # (type, key) => [prop] and type => prop
        self.__full_set = {} # prop => (prop, index)
        self.__angle_kinds = {} # angle => prop
        self.__angle_ratios = AngleRatioPropertySet()
        self.__length_ratios = LengthRatioPropertySet()
        self.__cyclic_orders = CyclicOrderPropertySet()
        self.__similar_triangles = {} # (three points) => {(three points)}
        self.__two_points_relative_to_line = {} # key => SameOrOppositeSideProperty
        self.__points_inside_angle = {} # key => PointInsideAngleProperty
        self.__lengths_inequalities = {} # key => LengthsInequalityProperty
        self.__angles_inequalities = {} # angle => {angle => AnglesInequalityProperty}
        self.__points_inside_triangle = {} # {vertices} => [points]
        self.__perpendicular_feets = {} # (foot, point, segment) => prop

    def __normalize_prop(self, prop):
        for base in prop.bases:
            self.__normalize_prop(base)
        for r in prop.proper_reasons:
            self.__normalize_reason(r)

    def __normalize_reason(self, reason):
        for index, pre in enumerate(reason.premises):
            prop_and_index = self.prop_and_index(pre)
            existing = prop_and_index[0] if prop_and_index else None
            if existing is None:
                self.__normalize_prop(pre)
                self.__insert_prop__(pre)
            elif pre is not existing:
                self.__normalize_prop(pre)
                existing.merge(pre)
                reason.premises[index] = existing

    def insert_prop_and_reason(self, prop, reason):
        existing = self[prop]
        if existing is None:
            prop.reason = reason
            self.__normalize_prop(prop)
            self.__insert_prop__(prop)
        elif existing not in reason.all_premises:
            self.__normalize_reason(reason)
            existing.add_reason(reason)
            was_synthetic = existing.reason.rule == SyntheticPropertyRule.instance()
            if self.prop_and_index(existing) is None or was_synthetic:
                self.__insert_prop__(existing)

    def __insert_prop__(self, prop):
        def put(key):
            lst = self.__combined.get(key)
            if lst:
                lst.append(prop)
            else:
                self.__combined[key] = [prop]

        type_key = type(prop)
        if prop not in self.__full_set:
            put(type_key)
            for key in prop.keys():
                put((type_key, key))
            self.__full_set[prop] = (prop, len(self.__full_set))

        if type_key in (AngleValueProperty, AngleRatioProperty, SumOfAnglesProperty):
            self.__angle_ratios.add(prop)
        elif type_key == AngleKindProperty:
            self.__angle_kinds[prop.angle] = prop
        elif type_key in (EqualLengthRatiosProperty, LengthRatioProperty, ProportionalLengthsProperty):
            self.__length_ratios.add(prop)
        elif type_key == SameCyclicOrderProperty:
            self.__cyclic_orders.add(prop)
        elif type_key in (PointsCoincidenceProperty, LinesCoincidenceProperty, PointOnLineProperty, PointsCollinearityProperty, CircleCoincidenceProperty, PointAndCircleProperty, ConcyclicPointsProperty):
            super().__insert_prop__(prop)
        elif type_key == SameOrOppositeSideProperty:
            self.__two_points_relative_to_line[prop.property_key] = prop
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
        elif type_key == LengthsInequalityProperty:
            self.__lengths_inequalities[prop.property_key] = prop
        elif type_key == AnglesInequalityProperty:
            self.__cache_angles_inequality_property(*prop.angles, prop)
        elif type_key == PointInsideAngleProperty:
            self.__points_inside_angle[prop.property_key] = prop
        elif type_key == PointInsideTriangleProperty:
            key = prop.triangle.symmetric_key
            ar = self.__points_inside_triangle.get(key)
            if ar:
                ar.append(prop.point)
            else:
                self.__points_inside_triangle[key] = [prop.point]

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

    def prop_and_index(self, prop):
        return self.__full_set.get(prop)

    def add_synthetics(self, changeable):
        update_angles = \
            '*' in changeable or AngleRatioProperty in changeable or AngleValueProperty in changeable
        if update_angles:
            self.__angle_ratios.create_path_table()

        update_sums_of_angles = update_angles or SumOfAnglesProperty in changeable

        update_length_ratios = \
            '*' in changeable or EqualLengthRatiosProperty in changeable or LengthRatioProperty in changeable
        if update_length_ratios:
            self.__length_ratios.create_path_table()

        update_cyclic_order = \
            '*' in changeable or SameCyclicOrderProperty in changeable
        if update_cyclic_order:
            self.__cyclic_orders.create_path_table()

        changed = False
        for prop in self.all:
            extra = None
            if isinstance(prop, AngleRatioProperty):
                if update_angles:
                    extra = self.angle_ratio_property(prop.angle0, prop.angle1, use_cache=False)
            elif isinstance(prop, AngleValueProperty):
                if update_angles:
                    extra = self.angle_value_property(prop.angle, use_cache=False)
            elif isinstance(prop, SumOfAnglesProperty):
                if update_sums_of_angles:
                    extra = self.sum_of_angles_property(*prop.angles, use_cache=False)
            elif isinstance(prop, PointsCoincidenceProperty):
                extra = self.coincidence_property(*prop.points, use_cache=False)
            elif isinstance(prop, PointsCollinearityProperty):
                extra = self.collinearity_property(*prop.points, use_cache=False)
            elif isinstance(prop, PointOnLineProperty):
                extra = self.point_on_line_property(prop.segment, prop.point, use_cache=False)
            elif isinstance(prop, LinesCoincidenceProperty):
                extra = self.lines_coincidence_property(*prop.segments, use_cache=False)
            elif isinstance(prop, EqualLengthRatiosProperty):
                if update_length_ratios:
                    extra = self.equal_length_ratios_property(*prop.segments, use_cache=False)
            elif isinstance(prop, SameCyclicOrderProperty):
                if update_cyclic_order:
                    extra = self.same_cyclic_order_property(prop.cycle0, prop.cycle1, use_cache=False)
            elif isinstance(prop, AnglesInequalityProperty):
                extra = self.angles_inequality_property(*prop.angles, use_cache=False)
            else:
                continue

            if extra and extra.reason.cost < prop.reason.cost:
                changed = True
                prop.merge(extra)
        return changed

    def __getitem__(self, prop):
        prop_and_index = self.__full_set.get(prop)
        if prop_and_index:
            existing = prop_and_index[0]
        else:
            if isinstance(prop, AngleRatioProperty):
                existing = self.angle_ratio_property(prop.angle0, prop.angle1)
            elif isinstance(prop, AngleValueProperty):
                existing = self.angle_value_property(prop.angle)
            elif isinstance(prop, SameCyclicOrderProperty):
                existing = self.same_cyclic_order_property(prop.cycle0, prop.cycle1)
            #elif isinstance(prop, PointAndCircleProperty):
            #    existing = self.point_and_circle_property(prop.point, prop.circle_key)
            elif isinstance(prop, PointsCoincidenceProperty):
                existing = self.coincidence_property(*prop.points)
            elif isinstance(prop, PointsCollinearityProperty):
                existing = self.collinearity_property(*prop.points)
            elif isinstance(prop, MultiPointsCollinearityProperty):
                existing = self.collinearity_property(*prop.points)
            elif isinstance(prop, PointOnLineProperty):
                existing = self.point_on_line_property(prop.segment, prop.point)
            elif isinstance(prop, LinesCoincidenceProperty):
                existing = self.lines_coincidence_property(*prop.segments)
            elif isinstance(prop, SumOfAnglesProperty):
                existing = self.sum_of_angles_property(*prop.angles)
            elif isinstance(prop, ConcyclicPointsProperty):
                existing = self.concyclicity_property(*prop.points)
            elif isinstance(prop, AnglesInequalityProperty):
                existing = self.angles_inequality_property(*prop.angles)
            elif isinstance(prop, IntersectionOfLinesProperty):
                existing = self.intersection_property(prop.point, *prop.segments)
            elif isinstance(prop, FootOfPerpendicularProperty):
                existing = self.foot_of_perpendicular_property(prop.foot, prop.point, prop.segment)
            #TODO: LengthRatioProperty
            #TODO: EqualLengthRatiosProperty
            else:
                existing = None
            if existing:
                self.__normalize_prop(existing)
                self.__insert_prop__(existing)

        if existing and not existing.compare_values(prop):
            raise ContradictionError('different values: `%s` vs `%s`' % (prop, existing))
        return existing

    def not_equal_property(self, pt0, pt1):
        prop = self.coincidence_property(pt0, pt1)
        return prop if prop and not prop.coincident else None

    def angle_value(self, angle):
        return self.__angle_ratios.value(angle)

    def angle_value_property(self, angle, use_cache=True):
        return self.__angle_ratios.value_property(angle, use_cache=use_cache)

    def angle_kind_property(self, angle):
        return self.__angle_kinds.get(angle)

    def nondegenerate_angle_values(self):
        return self.__angle_ratios.values()

    def nondegenerate_angle_value_properties(self):
        return self.__angle_ratios.value_properties()

    def angles_for_degree(self, degree):
        if degree == 0:
            return [p.angle for p in self.list(AngleValueProperty) if p.degree == 0]
        return self.__angle_ratios.angles_for_degree(degree)

    def angle_values(self):
        return [(p.angle, 0) for p in self.list(AngleValueProperty) if p.degree == 0] + self.nondegenerate_angle_values()

    def angle_value_properties(self):
        return [p for p in self.list(AngleValueProperty) if p.degree == 0] + self.nondegenerate_angle_value_properties()

    def angle_value_properties_for_degree(self, degree, condition=None):
        if degree == 0:
            if condition:
                return [p for p in self.list(AngleValueProperty) if p.degree == 0 and condition(p.angle)]
            else:
                return [p for p in self.list(AngleValueProperty) if p.degree == 0]
        return self.__angle_ratios.value_properties_for_degree(degree, condition)

    def points_inside_segment(self, segment):
        return [pt for pt in self.collinear_points(segment) if self.__angle_ratios.value(pt.angle(*segment.points)) == 180]

    def points_on_ray(self, vector):
        return [pt for pt in self.collinear_points(vector.as_segment) if self.__angle_ratios.value(vector.start.angle(pt, vector.end)) == 0]

    def points_inside_triangle(self, triangle):
        ar = self.__points_inside_triangle.get(triangle.symmetric_key)
        return ar if ar else []

    def angles_are_congruent(self, angle0, angle1):
        return self.__angle_ratios.are_congruent(angle0, angle1)

    def angle_ratio(self, angle0, angle1):
        return self.__angle_ratios.ratio(angle0, angle1)

    def angle_ratio_property(self, angle0, angle1, use_cache=True):
        return self.__angle_ratios.ratio_property(angle0, angle1, use_cache=use_cache)

    def same_triple_angle_ratio_properties(self):
        return self.__angle_ratios.same_triple_ratio_properties()

    def congruent_angles_with_vertex(self):
        return self.__angle_ratios.congruent_angles_with_vertex()

    def congruent_angles_for(self, angle):
        return self.__angle_ratios.congruent_angles_for(angle)

    def congruent_oriented_angles(self):
        for a0, a1 in self.congruent_angles_with_vertex():
            cycle0 = a0.vertex.cycle(*a0.endpoints)
            cycle1 = a1.vertex.cycle(*a1.endpoints)
            comparison = self.compare_cyclic_order(cycle0, cycle1)
            if comparison == True:
                yield (
                    a0.vertex.oriented_angle(*a0.endpoints),
                    a1.vertex.oriented_angle(*a1.endpoints)
                )
                yield (
                    a0.vertex.oriented_angle(*reversed(a0.endpoints)),
                    a1.vertex.oriented_angle(*reversed(a1.endpoints))
                )
            elif comparison == False:
                yield (
                    a0.vertex.oriented_angle(*reversed(a0.endpoints)),
                    a1.vertex.oriented_angle(*a1.endpoints)
                )
                yield (
                    a0.vertex.oriented_angle(*a0.endpoints),
                    a1.vertex.oriented_angle(*reversed(a1.endpoints))
                )

    def congruent_oriented_angles_property(self, angle0, angle1):
        prop = CongruentOrientedAnglesProperty(angle0, angle1)
        eq = self.angle_ratio_property(angle0.angle, angle1.angle)
        cycle0 = angle0.cycle
        cycle1 = angle1.cycle
        if cycle0 == cycle1:
            return _synthetic_property(
                prop,
                Comment(
                    '$%{orientedangle:angle0}$ and $%{orientedangle:angle1}$ are congruent angles of $%{triangle}$',
                    {'angle0': angle0, 'angle1': angle1, triangle: Scene.Triangle(*angle0.point_set)}
                ),
                [eq]
            )
        else:
            cyc = self.same_cyclic_order_property(cycle0, cycle1)
            return _synthetic_property(
                prop,
                Comment(
                    '$%{anglemeasure:angle0} = %{anglemeasure:angle1}$ and $%{cycle:cycle0}$ has same order as $%{cycle:cycle1}$',
                    {'angle0': angle0.angle, 'angle1': angle1.angle, 'cycle0': cycle0, 'cycle1': cycle1}
                ),
                [eq, cyc]
            )

    def sum_of_angles(self, *angles):
        return self.__angle_ratios.sum_of_angles(*angles)

    def sum_of_angles_property(self, *angles, use_cache=True):
        return self.__angle_ratios.sum_of_angles_property(*angles, use_cache=use_cache)

    def congruent_segments_for(self, segment):
        fam = self.__length_ratios.ratio_to_family.get(1)
        return [n for n, d in fam.ratio_set if d == segment] if fam else []

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

    def congruent_segments_properties(self, allow_zeroes):
        if allow_zeroes:
            collection = []
            for prop in self.__length_ratios.congruency_properties():
                key = frozenset([prop.segment0, prop.segment1])
                if key not in self.__length_ratios.proportional_lengths:
                    collection.append(prop)
            return [p for p in self.__length_ratios.proportional_lengths.values() if p.value == 1] + collection
        else:
            return self.__length_ratios.congruency_properties()

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

    def lengths_inequality_property(self, segment0, segment1):
        return self.__lengths_inequalities.get(LengthsInequalityProperty.unique_key(segment0, segment1))

    def __cache_angles_inequality_property(self, angle0, angle1, prop):
            dct = self.__angles_inequalities.get(angle0)
            if dct:
                dct[angle1] = prop
            else:
                self.__angles_inequalities[angle0] = {angle1: prop}
            dct = self.__angles_inequalities.get(angle1)
            if dct:
                dct[angle0] = prop
            else:
                self.__angles_inequalities[angle1] = {angle0: prop}

    def angles_inequality_property(self, angle0, angle1, use_cache=True):
        assert angle0 != angle1

        def saved_property(a0, a1):
            dct = self.__angles_inequalities.get(a0)
            return dct.get(a1) if dct else None

        prop = saved_property(angle0, angle1)
        if use_cache and prop:
            return prop

        computed = [prop]
        def get_prop(first_is_less):
            if computed[0] is None:
                if first_is_less:
                    computed[0] = AnglesInequalityProperty(angle0, angle1)
                else:
                    computed[0] = AnglesInequalityProperty(angle1, angle0)
            return computed[0]

        arp = self.angle_ratio_property(angle0, angle1)
        if arp:
            if arp.value == 1:
                self.__cache_angles_inequality_property(angle0, angle1, None)
                return None
            _synthetic_property(
                get_prop(angle0 == arp.angle1),
                Comment(
                    '$%{anglemeasure:less} < %{multiplier:coef}%{anglemeasure:less} = %{anglemeasure:greater}$',
                    {'less': arp.angle1, 'greater': angle1, 'coef': arp.value}
                ),
                [arp]
            )

        congruency = {} # angle => congruency property
        def congruency_prop(angle, index):
            cached = congruency.get(angle)
            if cached:
                return cached
            cong = self.angle_ratio_property(angle0 if index == 0 else angle1, angle)
            congruency[angle] = cong
            return cong

        congruents0 = list(self.congruent_angles_for(angle0))
        congruents1 = list(self.congruent_angles_for(angle1))

        for a in congruents0:
            ineq = saved_property(a, angle1)
            if ineq is None:
                continue
            cong = congruency_prop(a, 0)
            params = {'angle': a, 'angle0': angle0, 'angle1': angle1}
            if a == ineq.angles[0]:
                _synthetic_property(
                    get_prop(True),
                    Comment(
                        '$%{anglemeasure:angle0} = %{anglemeasure:angle} < %{anglemeasure:angle1}$',
                        params
                    ),
                    [cong, ineq]
                )
            else:
                _synthetic_property(
                    get_prop(False),
                    Comment(
                        '$%{anglemeasure:angle1} < %{anglemeasure:angle} = %{anglemeasure:angle0}$',
                        params
                    ),
                    [ineq, cong]
                )

        for a in congruents1:
            ineq = saved_property(angle0, a)
            if ineq is None:
                continue
            cong = congruency_prop(a, 1)
            params = {'angle': a, 'angle0': angle0, 'angle1': angle1}
            if a == ineq.angles[1]:
                _synthetic_property(
                    get_prop(True),
                    Comment(
                        '$%{anglemeasure:angle0} < %{anglemeasure:angle} = %{anglemeasure:angle1}$',
                        params
                    ),
                    [cong, ineq]
                )
            else:
                _synthetic_property(
                    get_prop(False),
                    Comment(
                        '$%{anglemeasure:angle1} = %{anglemeasure:angle} < %{anglemeasure:angle0}$',
                        params
                    ),
                    [ineq, cong]
                )

        for a0, a1 in itertools.product(congruents0, congruents1):
            ineq = saved_property(a0, a1)
            if ineq is None:
                continue
            cong0 = congruency_prop(a0, 0)
            cong1 = congruency_prop(a1, 1)
            prop = get_prop(a0 == ineq.angles[0])
            _synthetic_property(
                prop,
                Comment(
                    '$%{anglemeasure:angle0} = %{anglemeasure:known0} < %{anglemeasure:known1} = %{anglemeasure:angle1}$',
                    {'angle0': prop.angles[0], 'angle1': prop.angles[1], 'known0': ineq.angles[0], 'known1': ineq.angles[1]}
                ),
                [cong0, ineq, cong1]
            )

        if use_cache and computed[0]:
            self.__cache_angles_inequality_property(angle0, angle1, computed[0])
        return computed[0]

    def triangles_are_similar(self, points0, points1):
        triples = self.__similar_triangles.get(points0)
        return triples and points1 in triples

    def two_points_relative_to_line_property(self, segment, point0, point1):
        return self.__two_points_relative_to_line.get(SameOrOppositeSideProperty.unique_key(segment, point0, point1))

    def point_inside_angle_property(self, point, angle):
        return self.__points_inside_angle.get(PointInsideAngleProperty.unique_key(point, angle))

    def ratios_in_use(self):
        return list(self.__length_ratios.ratio_to_family)

    def length_ratios_are_equal(self, segment0, segment1, segment2, segment3):
        return self.__length_ratios.contains((segment0, segment1), (segment2, segment3))

    def equal_length_ratios_property(self, segment0, segment1, segment2, segment3, use_cache=True):
        return self.__length_ratios.equality_property((segment0, segment1), (segment2, segment3), use_cache=use_cache)

    def compare_cyclic_order(self, cycle0, cycle1):
        return self.__cyclic_orders.compare(cycle0, cycle1)

    def same_cyclic_order_property(self, cycle0, cycle1, use_cache=True):
        return self.__cyclic_orders.same_order_property(cycle0, cycle1, use_cache=use_cache)

    def foot_of_perpendicular(self, point, segment):
        if point in segment.points or self.collinearity(*segment.points, point):
            return point

        for prop in self.list(PerpendicularSegmentsProperty, [segment]):
            other = prop.segments[1] if segment == prop.segments[0] else prop.segments[0]
            if point not in other.points:
                continue
            candidate = other_point(other.points, point)
            if candidate in segment.points or self.collinearity(*segment.points, candidate):
                return candidate

        return None

    def foot_of_perpendicular_property(self, foot, point, segment):
        assert foot != point

        key = (foot, point, segment)
        if key in self.__perpendicular_feets:
            return self.__perpendicular_feets.get(key)

        perp = point.segment(foot)
        perp_prop = self[PerpendicularSegmentsProperty(segment, perp)]
        if perp_prop is None:
            return None
        premises = [perp_prop]

        if foot in segment.points:
            comment = Comment(
                'segments $%{segment:perp}$ and $%{segment:segment}$ are perpendicular',
                {'perp': perp, 'segment': segment}
            )
        else:
            comment = Comment(
                '$%{segment:perp}$ is perpendicular to $%{line:segment}$ and $%{point:foot}$ lies on $%{line:segment}$',
                {'perp': perp, 'segment': segment, 'foot': foot}
            )
            col = self.collinearity_property(*segment.points, foot)
            if col is None:
                return None
            if not col.collinear:
                self.__perpendicular_feets[key] = None
                return None
            premises.append(col)

        prop = _synthetic_property(
            FootOfPerpendicularProperty(foot, point, segment),
            comment,
            premises
        )
        self.__perpendicular_feets[key] = prop
        return prop

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

    def clone(self, extra_points):
        copy = PropertySet(self.points + extra_points)
        for prop in self.all:
            copy.__insert_prop__(prop)
        return copy
