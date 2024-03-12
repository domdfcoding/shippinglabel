# stdlib
import sys
from coincidence.regressions import AdvancedDataRegressionFixture

# 3rd party
import pytest
from coincidence import only_windows

# this package
from shippinglabel.requirements import list_requirements
from tests.test_requirements import min_311, only_36, only_37


@only_windows("Output differs on Windows")
@pytest.mark.parametrize(
		"py_version",
		[
				only_36,
				only_37,
				pytest.param(
						"3.8+",
						marks=pytest.mark.skipif(
								not ((3, 8) <= sys.version_info[:2] < (3, 11)),
								reason="Output differs on Python 3.8, 3.9, 3.10"
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
