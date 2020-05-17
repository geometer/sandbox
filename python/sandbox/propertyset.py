import itertools
import networkx as nx
import re

from .core import CoreScene
from .property import *
from .reason import Reason
from .stats import Stats
from .util import LazyComment, divide

class ContradictionError(Exception):
    pass

class LineSet:
    class Line:
        def __init__(self):
            self.premises_graph = nx.Graph()

        @property
        def segments(self):
            return self.premises_graph.nodes

        def add(self, prop):
            self.premises_graph.add_edge(*prop.segments, prop=prop)

        def same_line_explanation(self, segment0, segment1):
            edge = self.premises_graph.get_edge_data(segment0, segment1)
            if edge:
                prop = edge['prop']
                return (
                    LazyComment('%s and %s is the same line', segment0.as_line, segment1.as_line),
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
            prop = LineCoincidenceProperty(segment0, segment1, True)
            prop.rule = 'synthetic'
            prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
            prop.reason.obsolete = all(p.reason.obsolete for p in premises)
            return prop

    def __init__(self):
        self.segment_to_line = {}
        self.__all_lines = set()
        self.different_lines_graph = nx.Graph()

    def __add_same_line_property(self, prop):
        line0 = self.segment_to_line.get(prop.segments[0])
        line1 = self.segment_to_line.get(prop.segments[1])
        if line0 and line1:
            if line0 != line1:
                for segment in line1.segments:
                    self.segment_to_line[segment] = line0
                line0.premises_graph.add_edges_from(line1.premises_graph.edges(data=True))
            line0.add(prop)
        elif line0:
            line0.add(prop)
            self.segment_to_line[prop.segments[1]] = line0
        elif line1:
            line1.add(prop)
            self.segment_to_line[prop.segments[0]] = line1
        else:
            line = LineSet.Line()
            line.add(prop)
            self.segment_to_line[prop.segments[0]] = line
            self.segment_to_line[prop.segments[1]] = line
            self.__all_lines.add(line)

    def __add_different_lines_property(self, prop):
        def line_by_segment(segment):
            line = self.segment_to_line.get(segment)
            if line is None:
                line = LineSet.Line()
                line.premises_graph.add_node(segment)
                self.segment_to_line[segment] = line
            return line

        line0 = line_by_segment(prop.segments[0])
        line1 = line_by_segment(prop.segments[1])
        edge = self.different_lines_graph.get_edge_data(line0, line1)
        if edge is None:
            self.different_lines_graph.add_edge(line0, line1, props={prop})
        else:
            edge['props'].add(prop)

    def add(self, prop):
        if prop.coincident:
            self.__add_same_line_property(prop)
        else:
            self.__add_different_lines_property(prop)

    def collinearity_property(self, pt0, pt1, pt2):
        lines = [(side, self.segment_to_line.get(side)) for side in Scene.Triangle(pt0, pt1, pt2).sides]
        lines = [lw for lw in lines if lw[1]]
        if len(lines) < 2:
            return None
        candidates = []
        for (segment0, line0), (segment1, line1) in itertools.combinations(lines, 2):
            if line0 == line1:
                comment, premises = line0.same_line_explanation(segment0, segment1)
                prop = PointsCollinearityProperty(pt0, pt1, pt2, True)
                prop.rule = 'synthetic'
                prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
                prop.reason.obsolete = all(p.reason.obsolete for p in premises)
                candidates.append(prop)
                continue
            data = self.different_lines_graph.get_edge_data(line0, line1)
            if data:
                for prop in data['props']:
                    seg0, seg1 = prop.segments
                    if self.segment_to_line[seg0] == line1:
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
                    prop.rule = 'synthetic'
                    prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
                    prop.reason.obsolete = all(p.reason.obsolete for p in premises)
                    candidates.append(prop)
        if not candidates:
            return None
        best = candidates[0]
        cost = len(best.reason.all_premises)
        for cand in candidates[1:]:
            cand_cost = len(cand.reason.all_premises)
            if cand_cost < cost:
                best = cand
                cost = cand_cost
        return best

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
                    pattern.append('%sº')
                    params.append(self.multiplier * vertex)
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
                    pattern.append('%sº')
                    params.append(self.multiplier * vertex)
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
            prop.rule = 'synthetic'
            prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
            prop.reason.obsolete = all(p.reason.obsolete for p in premises)
            return prop

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
                prop.rule = 'synthetic'
                prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
                prop.reason.obsolete = all(p.reason.obsolete for p in premises)
                properties.append(prop)
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
                prop.rule = 'synthetic'
                prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
                prop.reason.obsolete = all(p.reason.obsolete for p in premises)
                properties.append(prop)
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
                    prop.rule = 'synthetic'
                    prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
                    prop.reason.obsolete = all(p.reason.obsolete for p in premises)
                    yield prop

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
        prop.rule = 'synthetic'
        prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
        prop.reason.obsolete = all(p.reason.obsolete for p in premises)
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
                    prop.rule = 'synthetic'
                    prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
                    prop.reason.obsolete = all(p.reason.obsolete for p in premises)
                    yield prop

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
        prop.rule = 'synthetic'
        prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
        prop.reason.obsolete = all(p.reason.obsolete for p in premises)
        pair = (prop, value)
        self.__cache[key] = pair
        return pair

class PropertySet:
    def __init__(self):
        self.__combined = {} # (type, key) => [prop] and type => prop
        self.__full_set = {} # prop => prop
        self.__indexes = {} # prop => number
        self.__angle_kinds = {} # angle => prop
        self.__line_set = LineSet()
        self.__angle_ratios = AngleRatioPropertySet()
        self.__length_ratios = LengthRatioPropertySet()
        self.__cyclic_orders = CyclicOrderPropertySet()
        self.__coincidence = {} # {point, point} => prop
        self.__collinearity = {} # {point, point, point} => prop
        self.__intersections = {} # {segment, segment} => point, [reasons]
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
        elif type_key == PointsCoincidenceProperty:
            self.__coincidence[prop.property_key] = prop
        elif type_key == PointsCollinearityProperty:
            self.__collinearity[prop.property_key] = prop
        elif type_key == EqualLengthRatiosProperty:
            self.__length_ratios.add(prop)
        elif type_key == SameCyclicOrderProperty:
            self.__cyclic_orders.add(prop)
        elif type_key == LineCoincidenceProperty:
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
            elif isinstance(prop, AngleValueProperty) and prop.degree != 0:
                existing = self.angle_value_property(prop.angle)
            elif isinstance(prop, SameCyclicOrderProperty):
                existing = self.same_cyclic_order_property(prop.cycle0, prop.cycle1)
        #TODO: LengthRatioProperty
        #TODO: EqualLengthRatiosProperty
        if existing and not existing.compare_values(prop):
            raise ContradictionError('different values: `%s` vs `%s`' % (prop, existing))
        return existing

    def collinearity_property(self, pt0, pt1, pt2):
        prop = self.__collinearity.get(frozenset([pt0, pt1, pt2]))
        return prop if prop else self.__line_set.collinearity_property(pt0, pt1, pt2)

    def not_collinear_property(self, pt0, pt1, pt2):
        prop = self.collinearity_property(pt0, pt1, pt2)
        return prop if prop and not prop.collinear else None

    def coincidence_property(self, pt0, pt1):
        return self.__coincidence.get(frozenset([pt0, pt1]))

    def not_equal_property(self, pt0, pt1):
        prop = self.__coincidence.get(frozenset([pt0, pt1]))
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
        prop.rule = 'synthetic'
        prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
        prop.reason.obsolete = all(p.reason.obsolete for p in premises)
        return prop

    def same_cyclic_order_property(self, cycle0, cycle1):
        prop = SameCyclicOrderProperty(cycle0, cycle1)
        existing = self.__full_set.get(prop)
        if existing:
            return existing
        comment, premises = self.__cyclic_orders.explanation(cycle0, cycle1)
        if comment:
            prop.rule = 'synthetic'
            prop.reason = Reason(max(p.reason.generation for p in premises), comment, premises)
            prop.reason.obsolete = all(p.reason.obsolete for p in premises)
            return prop
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
        key = frozenset([segment0, segment1])
        value = self.__intersections.get(key)
        if value is None:
            value = self.__intersection_of_lines(segment0, segment1)
            if value[0]:
                self.__intersections[key] = value
        return value

    def __intersection_of_lines(self, segment0, segment1):
        common = next((pt for pt in segment0.points if pt in segment1.points), None)
        if common:
            return (common, [])

        for index in range(0, 2):
            col = self.collinearity_property(*segment0.points, segment1.points[index])
            if col and col.collinear:
                return (segment1.points[index], [col])
            col = self.collinearity_property(*segment1.points, segment0.points[index])
            if col and col.collinear:
                return (segment0.points[index], [col])

        pts0 = self.collinear_points(segment0)
        if not pts0:
            return (None, [])
        pts1 = self.collinear_points(segment1)
        if not pts1:
            return (None, [])
        common_points = [pt for pt in pts0 if pt in pts1]
        if len(common_points) != 1:
            return (None, [])
        col0 = self.collinearity_property(*segment0.points, common_points[0])
        col1 = self.collinearity_property(*segment1.points, common_points[0])
        return (common_points[0], [col0, col1])

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
