# 3rd party
import pytest
from domdf_python_tools.testing import only_windows
from pytest_regressions.data_regression import DataRegressionFixture

# this package
from shippinglabel.requirements import (
		list_requirements,
		)
from tests.test_requirements import version_specific


@only_windows("Output differs on Windows")
@version_specific
@pytest.mark.parametrize(
		"library",
		[
				"shippinglabel",
				"pytest",
				"apeye",
				"cachecontrol[filecache]",
				"domdf-python-tools",
				"domdf_python_tools",
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
