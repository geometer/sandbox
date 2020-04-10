import itertools
import sympy as sp

from sandbox.property import LengthRatioProperty
from sandbox.util import _comment, angle_of, side_of

from .basic import Rule

class LawOfSinesRule(Rule):
    """
    The law of sines
    """
    def sources(self):
        return [p for p in self.context.nondegenerate_angle_value_properties() if p.angle.vertex]

    def apply(self, av0):
        triangle = (av0.angle.vertex, *av0.angle.endpoints)
        av1 = self.context.angle_value_property(angle_of(triangle, 1))
        if av1 is None or av0.reason.obsolete and av1.reason.obsolete:
            return
        sines = (
            sp.sin(sp.pi * av0.degree / 180),
            sp.sin(sp.pi * av1.degree / 180),
            sp.sin(sp.pi * (180 - av0.degree - av1.degree) / 180)
        )
        sides = [side_of(triangle, i) for i in range(0, 3)]
        for (sine0, side0), (sine1, side1) in itertools.combinations(zip(sines, sides), 2):
            yield (
                LengthRatioProperty(side0, side1, sine0 / sine1),
                _comment('Law of sines for △ %s %s %s', *triangle),
                [av0, av1]
            )
