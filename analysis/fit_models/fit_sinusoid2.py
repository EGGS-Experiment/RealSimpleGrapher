"""
Fitter class for Sinusoids.
"""
from numpy import pi, sin
from RealSimpleGrapher.analysis.model import Model, ParameterInfo


class Sinusoid2(Model):

    def __init__(self):
        self.parameters = {
            'contrast': ParameterInfo('contrast', 0, lambda x, y: 0.5, vary=True),
            'phi0': ParameterInfo('phi0', 1, lambda x, y: 0, vary=True),
            'offset': ParameterInfo('offset', 2, lambda x, y: 0, vary=False),
        }

    def model(self, x, p):
        contrast = p[0]
        phi0 = p[1]
        offset = p[2]

        phi_rad = x * pi / 180.0
        phi0_rad = phi0 * pi / 180.0
        return 0.5 + contrast / 2.0 * sin(2 * (phi_rad - phi0_rad)) + offset
