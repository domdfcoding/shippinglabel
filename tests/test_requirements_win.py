# 3rd party
import pytest
from domdf_python_tools.testing import only_windows
from pytest_regressions.data_regression import DataRegressionFixture

# this package
from shippinglabel.requirements import (
		list_requirements,
		)
from tests.test_requirements import min_38, only_36, only_37


@only_windows("Output differs on Windows")
@pytest.mark.parametrize(
		"py_version",
		[
				only_36,
				only_37,
				min_38,
				]
		)
@pytest.mark.parametrize(
		"library",
		[
				"pytest",
				]
		)
@pytest.mark.parametrize("depth", [-1, 0, 1, 2, 3])
# @pytest.mark.parametrize("depth", [3])
def test_list_requirements(
		data_regression: DataRegressionFixture,
		library,
		depth,
		py_version,
		):
	data_regression.check(list(list_requirements(library, depth=depth)))
