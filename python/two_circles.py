from runner import run_sample
from sandbox import Scene

from sandbox.property import PointAndCircleProperty

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
A, B, C = triangle.points
circle = scene.circumcircle(triangle)
triangle1 = scene.nondegenerate_triangle(labels=('D', 'E', 'F'))
D, E, F = triangle1.points
circle1 = scene.circumcircle(triangle1)
G = circle.free_point(label='G')
H = circle.free_point(label='H')
I = circle.free_point(label='I')
G.belongs_to(circle1)
H.belongs_to(circle1)
I.belongs_to(circle1)
scene.nondegenerate_triangle_constraint(Scene.Triangle(G, H, I))

props = (
    PointAndCircleProperty(A, D, E, F, 0),
)

run_sample(scene, *props)
