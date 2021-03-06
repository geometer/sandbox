from sandbox import Scene
from sandbox.property import ProportionalLengthsProperty
from sandbox.util import LazyComment

from visualiser import visualise

scene = Scene()

A, D, C, B = scene.square('A', 'D', 'C', 'B')
A.x = 0
A.y = 0
D.x = 1
D.y = 0
I = scene.incentre_point(Scene.Triangle(A, B, C), label='I')
side = A.line_through(C)
foot = scene.perpendicular_foot_point(I, side, layer='auxiliary')
I.circle_through(foot)

prop = ProportionalLengthsProperty(B.segment(C), D.segment(I), 1)

visualise(scene, prop, title='Onestep Problem 1', task=[
    LazyComment('%s is a square', Scene.Polygon(A, B, C, D)),
    LazyComment('%s is the incentre of %s', I, Scene.Triangle(A, B, C)),
    LazyComment('Prove, that |%s| = |%s|', D.segment(I), B.segment(C))
], reference='Problem 1 from <a href="http://www.stanleyrabinowitz.com/download/onestepresults.pdf">onestep results list</a> by <a href="https://www.facebook.com/stanley.rabinowitz">Stanley Rabinowitz</a>');
