# 3rd party
import pytest
from packaging.utils import InvalidSdistFilename
from pytest_regressions.data_regression import DataRegressionFixture

# this package
from shippinglabel.sdist import NotAnSdistError, parse_sdist_filename


@pytest.mark.parametrize(
		"filename",
		[
				"wxPython-4.1.0.tar.gz",
				"PyGObject-3.38.0.tar.gz",
				"psutil-5.8.0.tar.gz",
				"tinycss-0.4.tar.gz",
				"cffi-1.14.4.tar.gz",
				"termcolor-1.1.0.tar.gz",
				"autodocsumm-0.2.2.tar.gz",
				"MarkupSafe-1.1.1.tar.gz",
				"astropy-4.2.tar.gz",
				"pyrsistent-0.17.3.tar.gz",
				"memoized-property-1.0.3.tar.gz",
				"PyNaCl-1.4.0.tar.gz",
				"pycairo-1.20.0.tar.gz",
				"strict-rfc3339-0.7.tar.gz",
				"autoflake-1.4.tar.gz",
				"Pillow-8.1.0.tar.gz",
				"cairocffi-1.2.0.tar.gz",
				"quantities-0.12.4.tar.gz",
				"pyerfa-1.7.1.1.tar.gz",
				"matplotlib-3.3.3.tar.gz",
				"fastimport-0.9.8.tar.gz",
				"orderedset-2.0.3.tar.gz",
				"PyYAML-5.3.1.tar.gz",
				"pandas-1.2.0.tar.gz",
				"Cython-0.29.14.tar.gz",
				"PyGObject-stubs-0.0.2.tar.gz",
				"dulwich-0.20.15.tar.gz",
				"tox-pip-version-0.0.7.tar.gz",
				"numpy-1.16.5.zip",
				]
		)
def test_parse_sdist_filename(filename: str, advanced_data_regression: DataRegressionFixture):
	parsed_filename = parse_sdist_filename(filename)
	advanced_data_regression.check(parsed_filename)
	assert str(parsed_filename) == filename


def test_parse_sdist_filename_wheel():
	# Test passing in a wheel
	with pytest.raises(NotAnSdistError, match="'autopep8-1.5.4-py2.py3-none-any.whl' is a wheel."):
		parse_sdist_filename("autopep8-1.5.4-py2.py3-none-any.whl")


def test_parse_sdist_filename_invalid():
	with pytest.raises(InvalidSdistFilename, match="Invalid sdist filename: 'autopep8-.tar.bz2'"):
		parse_sdist_filename("autopep8-.tar.bz2")
