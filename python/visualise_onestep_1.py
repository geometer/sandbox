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

visualise(scene, prop, title='Onestep Problem 1', description=LazyComment('''
<p>%s is a square.</p>
<p>%s is the incentre of %s.</p>
<p>Prove, that |%s| = |%s|.</p>
<p style="font-size:80%%">Problem 1 from <a href="http://www.stanleyrabinowitz.com/download/onestepresults.pdf">onestep results list</a> by <a href="https://www.facebook.com/stanley.rabinowitz">Stanley Rabinowitz</a></p>
''', Scene.Polygon(A, B, C, D), I, Scene.Triangle(A, B, C), D.segment(I), B.segment(C)).html())
