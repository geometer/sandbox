import itertools
import sympy as sp

from ..property import ProportionalLengthsProperty
from ..scene import Scene
from ..util import Comment

from .abstract import Rule

class LawOfSinesRule(Rule):
    """
    The law of sines
    """
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return [p for p in self.context.nondegenerate_angle_value_properties() if p.angle.vertex and p.degree not in (0, 180) and p not in self.processed]

    def apply(self, av0):
        triangle = Scene.Triangle(av0.angle.vertex, *av0.angle.endpoints)
        av1 = self.context.angle_value_property(triangle.angles[1])
        if av1 is None:
            return
        av2 = self.context.angle_value_property(triangle.angles[2])
        if av2 is None:
            return
        avs = [av0, av1, av2]
        self.processed.update(avs)
        sines = [sp.sin(sp.pi * av.degree / 180) for av in avs]
        sides = triangle.sides
        for i, j in itertools.combinations(range(0, 3), 2):
            yield (
                ProportionalLengthsProperty(sides[i], sides[j], sines[i] / sines[j]),
                Comment('law of sines for $%{triangle:triangle}$', {'triangle': triangle}),
                [avs[0], avs[1]]
            )
