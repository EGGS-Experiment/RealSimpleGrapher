"""
Generic fitter class.
FitWrapper is used by TraceListWidget.FitWindowWidget.FitWindow.
"""

__all__ = ["FitWrapper"]

from scipy import optimize
from numpy import linspace, zeros

from .fit_models import *

_MODEL_DICT = {
    'Lorentzian': Lorentzian,
    'Gaussian': Gaussian,
    'Linear': Linear,
    'Rabi': Rabi,
    'RotRabi': RotRabi,
    'RotRamsey': RotRamsey,
    'Bessel': Bessel,
    'Sinusoid': Sinusoid,
    'Sinusoid2': Sinusoid2,
    'ExponentialDecay': ExponentialDecay,
    'GaussianDecay': GaussianDecay,
    'RamseyDecay': RamseyDecay,
    'RamseyBfield': RamseyBfield
}


class FitWrapper(object):

    models = _MODEL_DICT.keys()

    def __init__(self, dataset, index):
        self.dataset = dataset
        self.index = index

    def setModel(self, model):
        self.model = _MODEL_DICT[model]()

    def getParameters(self):
        '''
        Returns a list of params sorted in order of index.
        '''
        params = self.model.parameters.keys()
        return sorted(params, key=lambda p: self.model.parameters[p].index)

    def getVary(self, p):
        return self.model.parameters[p].vary

    def getManualValue(self, p):
        try:
            return self.model.parameters[p].manual_value
        except:  # value doesn't exist. Use automatic guess
            x = self.dataset.data[:, 0]
            y = self.dataset.data[:, self.index + 1]
            guess = self.model.guess_param(p, x, y)
            self.model.parameters[p].manual_value = guess
            return guess

    def getFittedValue(self, p):
        try:
            return self.model.parameters[p].fit_value
        except Exception as e:  # no fitted value exists yet
            return None

    def setManualValue(self, p, value):
        self.model.parameters[p].manual_value = value

    def setVary(self, p, value):
        assert (value is True) or (value is False)
        self.model.parameters[p].vary = value

    def doFit(self):
        x = self.dataset.data[:, 0]
        y = self.dataset.data[:, self.index + 1]

        def residual(p):
            return y - self.model.reduced_model(x, p)

        varied_positions = self.model.varied_positions()
        fixed_positions = self.model.fixed_positions()
        x0 = [self.model.param_from_index(k).manual_value for k in varied_positions]

        result = optimize.leastsq(residual, x0)
        result = result[0]

        # after the fit, assign the fitted values to the parameters
        # For the fixed parameters, set the fit_value = manual_value
        # so that we don't have to deal with it in the GUI display
        for pos, fit_val in zip(varied_positions, result):
            param = self.model.param_from_index(pos)
            param.fit_value = fit_val

        for pos in fixed_positions:
            param = self.model.param_from_index(pos)
            param.fit_value = param.manual_value

    def evaluateFittedParameters(self):
        '''
        Evaluate the model on a fine grid.
        Return 2-d numpy array data where:
            data[:,0] = fine_grid
            data[:,1] = model evaluated on fitted parameters
        '''

        x = self.dataset.data[:, 0]
        n = len(x)
        N = 10 * n
        xmin = x[0];
        xmax = x[-1]
        fine_grid = linspace(xmin, xmax, N)

        p0 = []
        for p in self.getParameters():
            p0.append(self.getFittedValue(p))
        y = self.model.model(fine_grid, p0)

        data = zeros((N, 2))
        data[:, 0] = fine_grid
        data[:, 1] = y
        return data

    def evaluateManualParameters(self):
        '''
        Evaluate the model on a fine grid.
        Return 2-d numpy array data where:
            data[:,0] = fine_grid
            data[:,1] = model evaluated on manual parameters
        '''
        x = self.dataset.data[:, 0]
        n = len(x)
        N = 10 * n
        xmin = x[0];
        xmax = x[-1]
        fine_grid = linspace(xmin, xmax, N)

        p0 = []
        for p in self.getParameters():
            p0.append(self.getManualValue(p))
        y = self.model.model(fine_grid, p0)

        data = zeros((N, 2))
        data[:, 0] = fine_grid
        data[:, 1] = y
        return data
