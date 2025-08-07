# stdlib
import sys

# 3rd party
import pytest
from coincidence import only_windows
from coincidence.regressions import AdvancedDataRegressionFixture

# this package
from shippinglabel.requirements import list_requirements
from tests.test_requirements import min_311, only_36, only_37, only_38


@only_windows("Output differs on Windows")
@pytest.mark.parametrize(
		"py_version",
		[
				only_36,
				only_37,
				only_38,
				pytest.param(
						"3.9+",
						marks=pytest.mark.skipif(
								not ((3, 9) <= sys.version_info[:2] < (3, 11)),
								reason="Output differs on Python 3.9, 3.10"
								)
						),
				min_311,
				]
		)
@pytest.mark.parametrize("depth", [-1, 0, 1, 2, 3])
def test_list_requirements_pytest(
		advanced_data_regression: AdvancedDataRegressionFixture,
		depth: int,
		py_version: str,
		):
	advanced_data_regression.check(list(list_requirements("pytest", depth=depth)))
