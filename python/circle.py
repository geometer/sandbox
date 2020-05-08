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

props = (
    PointAndCircleProperty(D, *triangle.points, 0),
    PointAndCircleProperty(G, D, E, F, 0),
    PointAndCircleProperty(scene.get('A'), D, E, F, 0),
    PointAndCircleProperty(G, *triangle.points, 0),
)

run_sample(scene, *props)
