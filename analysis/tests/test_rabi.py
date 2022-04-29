"""
Test for Rabi flop fits.
"""
from .model_test import ModelTest
from RealSimpleGrapher.analysis.fit_models import Rabi
from numpy import pi

test = ModelTest(Rabi, 'Rabi')
true_params = [2 * pi / 10, 10, 0.05, 0., 0, 0.6]
test.generate_data(0, 30, 300, 0.02, true_params)
test.fit()
test.print_results()
test.plot(fit=True)
