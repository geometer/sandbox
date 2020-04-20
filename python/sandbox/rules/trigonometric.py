import itertools
import sympy as sp

from sandbox.property import ProportionalLengthsProperty
from sandbox.scene import Scene
from sandbox.util import LazyComment

from .abstract import Rule

class LawOfSinesRule(Rule):
    """
    The law of sines
    """
    def sources(self):
        return [p for p in self.context.nondegenerate_angle_value_properties() if p.angle.vertex]

    def apply(self, av0):
        triangle = Scene.Triangle([av0.angle.vertex, *av0.angle.endpoints])
        av1 = self.context.angle_value_property(triangle.angles[1])
        if av1 is None or av0.reason.obsolete and av1.reason.obsolete:
            return
        sines = (
            sp.sin(sp.pi * av0.degree / 180),
            sp.sin(sp.pi * av1.degree / 180),
            sp.sin(sp.pi * (180 - av0.degree - av1.degree) / 180)
        )
        sides = triangle.sides
        for (sine0, side0), (sine1, side1) in itertools.combinations(zip(sines, sides), 2):
            yield (
                ProportionalLengthsProperty(side0, side1, sine0 / sine1),
                LazyComment('Law of sines for %s', triangle),
                [av0, av1]
            )
