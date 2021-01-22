# 3rd party
import pytest
from coincidence import AdvancedDataRegressionFixture
from domdf_python_tools.paths import PathPlus

# this package
from shippinglabel import no_dev_versions, normalize, normalize_keep_dot, read_pyvenv


@pytest.mark.parametrize(
		"name, expected",
		[
				("foo", "foo"),
				("bar", "bar"),
				("baz", "baz"),
				("baz-extensions", "baz-extensions"),
				("baz_extensions", "baz-extensions"),
				("baz.extensions", "baz-extensions"),
				]
		)
def test_normalize(name, expected):
	assert normalize(name) == expected


@pytest.mark.parametrize(
		"name, expected",
		[
				("foo", "foo"),
				("bar", "bar"),
				("baz", "baz"),
				("baz-extensions", "baz-extensions"),
				("baz_extensions", "baz-extensions"),
				("baz.extensions", "baz.extensions"),
				]
		)
def test_normalize_keep_dot(name, expected):
	assert normalize_keep_dot(name) == expected


def test_no_dev_versions():
	assert no_dev_versions(["3.6", "3.7", "3.8"]) == ["3.6", "3.7", "3.8"]
	assert no_dev_versions(["3.6", "3.7", "3.8", "3.9-dev"]) == ["3.6", "3.7", "3.8"]
	assert no_dev_versions(["3.6", "3.7", "3.8", "pypy3"]) == ["3.6", "3.7", "3.8", "pypy3"]


def test_read_pyvenv(tmp_pathplus: PathPlus, advanced_data_regression: AdvancedDataRegressionFixture):
	(tmp_pathplus / "pyvenv.cfg").write_text(
			'\n'.join([
					"home = /usr",
					"implementation = CPython",
					"version_info = 3.8.5.final.0",
					"virtualenv = 20.2.2",
					"include-system-site-packages = false",
					"base-prefix = /usr",
					"base-exec-prefix = /usr",
					"base-executable = /usr/bin/python3",
					"prompt = (shippinglabel) ",
					"repo_helper_devenv = 0.3.0",
					])
			)

	venv_config = read_pyvenv(tmp_pathplus)
	assert venv_config["prompt"] == "(shippinglabel) "

	advanced_data_regression.check(venv_config)
