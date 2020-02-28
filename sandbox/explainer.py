from .core import Constraint
from .hunter import *
from .property import *

class Explainer:
    def __init__(self, scene, properties):
        self.scene = scene
        self.properties = properties
        self.explanations = {}

    def explain(self):
        for prop in self.properties:
            if isinstance(prop, CollinearProperty):
                for line in self.scene.lines():
                    if prop.A in line.all_points and prop.B in line.all_points and prop.C in line.all_points:
                        self.explanations[prop] = 'Given'
                        break
            if isinstance(prop, RightAngleProperty):
                for cnst in self.scene.constraints(Constraint.Kind.perpendicular):
                    line0 = cnst.params[0]
                    line1 = cnst.params[1]
                    def vector_on_line(vector, line):
                        return vector.start in line.all_points and vector.end in line.all_points

                    if vector_on_line(prop.angle.vector0, line0):
                        if vector_on_line(prop.angle.vector1, line1):
                            self.explanations[prop] = '%s ⟂ %s' % (line0.label, line1.label)
                    elif vector_on_line(prop.angle.vector0, line1):
                        if vector_on_line(prop.angle.vector1, line0):
                            self.explanations[prop] = '%s ⟂ %s' % (line0.label, line1.label)

        right_angles = [p.angle for p in self.explanations if isinstance(p, RightAngleProperty)]
        for prop in self.properties:
            if isinstance(prop, EqualAnglesProperty):
                if prop.angle0 in right_angles and prop.angle1 in right_angles:
                     self.explanations[prop] = 'both 90º'

    def dump(self):
        print('Explained:')
        for prop in self.properties:
            if prop in self.explanations:
                print('\t%s [%s]' % (prop, self.explanations[prop]))
        print('\nNot explained:')
        for prop in self.properties:
            if not prop in self.explanations:
                print('\t%s' % prop)
        print('\nTotal properties: %d, explained: %d' % (len(self.properties), len(self.explanations)))
