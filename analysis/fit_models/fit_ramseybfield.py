"""
Fitter class for Ramsey B-field.
"""
from numpy import pi, cos, exp
from RealSimpleGrapher.analysis.model import Model, ParameterInfo


class RamseyBfield(Model):

    def __init__(self):
        self.parameters = {
            'freq': ParameterInfo('freq', 0, lambda x, y: 10000, vary=True),
            'tau': ParameterInfo('tau', 1, lambda x, y: 1000, vary=True),
            'startfrom': ParameterInfo('startfrom', 2, lambda x, y: 1, vary=True),
            'decayto': ParameterInfo('decayto', 3, lambda x, y: 0.5, vary=False),
            'B0': ParameterInfo('B0', 4, lambda x, y: 0.1, vary=True),
            'detuning': ParameterInfo('detuning', 5, lambda x, y: 0, vary=True),
        }

    def model(self, x, p):
        t = 1e-6 * x
        w = 2 * pi * p[0]
        tau = 1e-6 * p[1]
        startfrom = p[2]
        decayto = p[3]
        # detuning due to B field (conversion factor 5e5 needs to be calculated exactly)
        wB = 2 * pi * p[4] * 5e5
        # other detuning
        wd = 2 * pi * p[5]

        return (startfrom - decayto) * exp(-t / tau) * cos(wd * t - (wB / w) * (cos(w * t) - 1)) + decayto
