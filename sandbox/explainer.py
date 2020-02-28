from .core import Constraint
from .hunter import *
from .property import *

class Explainer:
    class Reason:
        def __init__(self, index, prop, comments, roots):
            self.index = index
            self.property = prop
            if isinstance(comments, str):
                self.comments = [comments]
            else:
                self.comments = list(comments)
            self.roots = roots

        def __str__(self):
            if self.roots:
                return '%s (%s)' % (
                    ', '.join(self.comments),
                    ', '.join(['*%d' % rsn.index for rsn in self.roots])
                )
            else:
                return ', '.join(self.comments)

    def __init__(self, scene, properties):
        self.scene = scene
        self.properties = properties
        self.explained = []

    def reason(self, prop, comments, roots=None):
        self.explained.append(Explainer.Reason(len(self.explained), prop, comments, roots))

    def explain(self):
        for prop in self.properties:
            if isinstance(prop, CollinearProperty):
                for line in self.scene.lines():
                    if prop.A in line.all_points and prop.B in line.all_points and prop.C in line.all_points:
                        self.reason(prop, 'Given')
                        break
            if isinstance(prop, RightAngleProperty):
                for cnst in self.scene.constraints(Constraint.Kind.perpendicular):
                    line0 = cnst.params[0]
                    line1 = cnst.params[1]
                    def vector_on_line(vector, line):
                        return vector.start in line.all_points and vector.end in line.all_points

                    if vector_on_line(prop.angle.vector0, line0):
                        if vector_on_line(prop.angle.vector1, line1):
                            self.reason(prop, '%s ⟂ %s' % (line0.label, line1.label))
                    elif vector_on_line(prop.angle.vector0, line1):
                        if vector_on_line(prop.angle.vector1, line0):
                            self.reason(prop, '%s ⟂ %s' % (line0.label, line1.label))

        right_angles = [exp for exp in self.explained if isinstance(exp.property, RightAngleProperty)]
        for prop in self.properties:
            if isinstance(prop, EqualAnglesProperty):
                roots = [exp for exp in right_angles if exp.property.angle in [prop.angle0, prop.angle1]]
                if len(roots) == 2:
                    self.reason(prop, 'both 90º', roots=roots)

    def dump(self):
        print('Explained:')
        for exp in self.explained:
            print('\t%2d: %s [%s]' % (exp.index, exp.property, exp))
        print('\nNot explained:')
        explained = {rsn.property for rsn in self.explained}
        for prop in self.properties:
            if not prop in explained:
                print('\t%s' % prop)
        print('\nTotal properties: %d, explained: %d' % (len(self.properties), len(self.explained)))
