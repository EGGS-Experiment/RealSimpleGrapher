"""
Test for Linear fits.
"""
from .model_test import ModelTest
from RealSimpleGrapher.analysis.fit_models import Linear

test = ModelTest(Linear, 'Linear')
true_params = [0.3, 4]
test.generate_data(10, 20, 40, 1, true_params)
test.fit()
test.print_results()
test.plot()
