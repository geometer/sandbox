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
D_1 = circle.free_point(label='D_1')
E_1 = circle.free_point(label='E_1')
F_1 = circle.free_point(label='F_1')
circle3 = scene.circumcircle(Scene.Triangle(D_1, E_1, F_1))
G_1 = circle3.free_point(label='G_1')
scene.nondegenerate_triangle_constraint(Scene.Triangle(D, F, G))
scene.nondegenerate_triangle_constraint(Scene.Triangle(scene.get('B'), G, G_1))

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
    # E in DEF, DEF eq BGG_1 or E in ABC, ABC eq BGG_1
    PointAndCircleProperty(E, scene.get('B'), G, G_1, 0),
    # G in DEF, DEF eq ABC
    PointAndCircleProperty(G, *triangle.points, 0),
    # E in DEF, DEF eq DFG or E in ABC, ABC eq DFG
    PointAndCircleProperty(E, D, F, G, 0),
)

# DEF eq DFG: ncl DFG, ncl DEF, G in DEF
# DEF eq ABC: D in ABC, E in ABC, F in ABC, ncl ABC, ncl DEF
# BGG_1 eq ABC: B in ABC, G in DEF, G_1 in D_1E_1F_1

run_sample(scene, *props)
