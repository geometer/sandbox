from runner import run_sample
from sandbox import Scene

from sandbox.property import PointAndCircleProperty

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
circle = scene.circumcircle(triangle)
D = circle.free_point(label='D')
E = circle.free_point(label='E')
F = circle.free_point(label='F')
circle2 = scene.circumcircle(Scene.Triangle(D, E, F))
G = circle2.free_point(label='G')
scene.nondegenerate_triangle_constraint(Scene.Triangle(D, F, G))

props = (
    # known
    PointAndCircleProperty(D, *triangle.points, 0),
    # known
    PointAndCircleProperty(G, D, E, F, 0),
    # A in ABC, ABC eq DEF
    PointAndCircleProperty(scene.get('A'), D, E, F, 0),
    # incorrect
    PointAndCircleProperty(scene.get('A'), D, E, G, 0),
    # A in ABC, ABC eq DFG
    PointAndCircleProperty(scene.get('A'), D, F, G, 0),
    # G in DEF, DEF eq ABC
    PointAndCircleProperty(G, *triangle.points, 0),
    # E in DEF, DEF eq DFG
    PointAndCircleProperty(E, D, F, G, 0),
)

# DEF eq DFG: ncl DFG, ncl DEF, G in DEF
# DEF eq ABC: D in ABC, E in ABC, F in ABC, ncl ABC, ncl DEF

run_sample(scene, *props)
