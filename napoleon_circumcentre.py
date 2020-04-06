import sys

from sandbox import Scene
from sandbox.explainer import Explainer
from sandbox.property import EquilateralTriangleProperty
from sandbox.propertyset import PropertySet
from sandbox.util import _comment

#scene = Scene(strategy='constraints')
scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])

def napoleonic(A, B, C):
    V = A.scene.free_point(label=C.label + '1')
    A.scene.equilateral_constraint((A, B, V), comment=_comment('Given: △ %s %s %s is an equilateral triangle', V, A, B))
    line = A.line_through(B)
    V.opposite_side_constraint(C, line, comment=_comment('Given: %s is outward of △ %s %s %s', V, A, B, C))
    D = scene.circumcentre_point((A, B, V), label=C.label + '2')
    #D.inside_triangle_constraint(A, B, V)

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

prop = EquilateralTriangleProperty((scene.get('A2'), scene.get('B2'), scene.get('C2')))

if '--use-trigonometry' in sys.argv[1:]:
    explainer = Explainer(scene, options={'trigonometry'})
else:
    explainer = Explainer(scene)

if '--profile' in sys.argv[1:]:
    import cProfile
    cProfile.run('explainer.explain()')
else:
    explainer.explain()
if '--dump' in sys.argv[1:]:
    explainer.dump()
explainer.stats().dump()
print('\tExplained: %s = %s' % (prop, explainer.explained(prop)))

if '--explain' in sys.argv[1:]:
    def dump(prop, level=0):
        print('\t' + '  ' * level + str(prop) + ': ' + ' + '.join([str(com) for com in prop.reason.comments]))
        if prop.reason.premises:
            for premise in prop.reason.premises:
                dump(premise, level + 1)

    def depth(prop):
        if prop.reason.premises:
            return 1 + max(depth(p) for p in prop.reason.premises)
        return 0

    def all_premises(prop):
        premises = PropertySet()
        def collect(p):
            premises.add(p)
            if p.reason.premises:
                for pre in p.reason.premises:
                    collect(pre)
        collect(prop)
        return premises

    explanation = explainer.explanation(prop)
    if explanation:
        dump(explanation)
        print('Depth = %s' % depth(explanation))
        print('Props = %s' % len(all_premises(explanation)))
        all_premises(explanation).stats().dump()
