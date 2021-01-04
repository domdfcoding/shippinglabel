# stdlib
import os
from pathlib import Path

# 3rd party
import pytest
from _pytest.fixtures import FixtureRequest
from betamax import Betamax
from domdf_python_tools.paths import PathPlus

# this package
from shippinglabel.pypi import PYPI_API

pytest_plugins = ("domdf_python_tools.testing", )

with Betamax.configure() as config:
	config.cassette_library_dir = PathPlus(__file__).parent / "cassettes"


@pytest.fixture()
def original_datadir(request):
	# Work around pycharm confusing datadir with test file.
	return Path(os.path.splitext(request.module.__file__)[0] + '_')


@pytest.fixture()
def cassette(request: FixtureRequest):
	"""
	Provides a Betamax cassette scoped to the test function
	which record and plays back interactions with the PyPI API.
	"""  # noqa: D400

	with Betamax(PYPI_API._store["session"]) as vcr:
		vcr.use_cassette(request.node.name, record="once")

		yield PYPI_API


@pytest.fixture()
def module_cassette(request: FixtureRequest):
	"""
	Provides a Betamax cassette scoped to the test module
	which record and plays back interactions with the PyPI API.
	"""  # noqa: D400

	cassette_name = request.module.__name__.split('.')[-1]

	with Betamax(PYPI_API._store["session"]) as vcr:
		# print(f"Using cassette {cassette_name!r}")
		vcr.use_cassette(cassette_name, record="once")

		yield PYPI_API
