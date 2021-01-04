# 3rd party
import pytest
from consolekit.utils import coloured_diff
from domdf_python_tools.testing import check_file_regression
from pytest_regressions.file_regression import FileRegressionFixture

# this package
from shippinglabel import conda
from shippinglabel.conda import (
		compile_requirements,
		get_channel_listing,
		make_conda_description,
		validate_requirements
		)
from shippinglabel.requirements import ComparableRequirement


def test_compile_requirements(tmp_pathplus):
	(tmp_pathplus / "requirements.txt").write_lines([
			"apeye>=0.3.0",
			"click==7.1.2",
			"ruamel.yaml>=0.16.12",
			"domdf-python-tools>=1.1.0",
			"dulwich>=0.19.16",
			"email_validator==1.1.1",
			"isort>=5.0.0",
			"typing_extensions>=3.7.4.3",
			"jinja2>=2.11.2",
			"packaging>=20.4",
			"pre-commit>=2.7.1",
			"attrs>=20.2.0",
			"tomlkit>=0.7.0",
			])

	assert compile_requirements(tmp_pathplus) == [
			ComparableRequirement("apeye>=0.3.0"),
			ComparableRequirement("attrs>=20.2.0"),
			ComparableRequirement("click==7.1.2"),
			ComparableRequirement("domdf-python-tools>=1.1.0"),
			ComparableRequirement("dulwich>=0.19.16"),
			ComparableRequirement("email-validator==1.1.1"),
			ComparableRequirement("isort>=5.0.0"),
			ComparableRequirement("jinja2>=2.11.2"),
			ComparableRequirement("packaging>=20.4"),
			ComparableRequirement("pre-commit>=2.7.1"),
			ComparableRequirement("ruamel-yaml>=0.16.12"),
			ComparableRequirement("tomlkit>=0.7.0"),
			ComparableRequirement("typing-extensions>=3.7.4.3"),
			]


def test_compile_requirements_markers_url_extras(tmp_pathplus, conda_cassette):
	(tmp_pathplus / "requirements.txt").write_lines([
			'apeye>=0.3.0; python_version <= "3.9"',
			"pip @ https://github.com/pypa/pip/archive/1.3.1.zip#sha1=da9234ee9982d4bbb3c72346a6de940a148ea686",
			'click==7.1.2; platform_system == "Linux"',
			"requests[security]",
			])

	assert compile_requirements(tmp_pathplus) == [
			ComparableRequirement("apeye>=0.3.0"),
			ComparableRequirement("click==7.1.2"),
			ComparableRequirement("requests"),
			]


@pytest.mark.parametrize("clear_cache", [
		False,
		"domdfcoding",
		"conda-forge",
		True,
		])
def test_get_channel_listing(clear_cache):

	if clear_cache:
		if isinstance(clear_cache, str):
			conda.clear_cache(clear_cache)
		else:
			conda.clear_cache()

	listing = get_channel_listing("domdfcoding")
	assert "attr_utils" in listing
	assert "attr-utils" not in listing
	assert "domdf_python_tools" in listing
	assert "apeye" in listing
	assert "prettyprinter" in listing
	assert "scikit_learn" not in listing

	listing = get_channel_listing("conda-forge")
	assert "typing_extensions" in listing


def test_validate_requirements():
	requirements = [
			ComparableRequirement("apeye>=0.3.0"),
			ComparableRequirement("attrs>=20.2.0"),
			ComparableRequirement("click==7.1.2"),
			ComparableRequirement("domdf-python-tools>=1.1.0"),
			ComparableRequirement("dulwich>=0.19.16"),
			ComparableRequirement("email-validator==1.1.1"),
			ComparableRequirement("isort>=5.0.0"),
			ComparableRequirement("jinja2>=2.11.2"),
			ComparableRequirement("packaging>=20.4"),
			ComparableRequirement("pre-commit>=2.7.1"),
			ComparableRequirement("ruamel-yaml>=0.16.12"),
			ComparableRequirement("tomlkit>=0.7.0"),
			ComparableRequirement("typing_extensions>=3.7.4.3"),
			]
	expected = [
			ComparableRequirement("apeye>=0.3.0"),
			ComparableRequirement("attrs>=20.2.0"),
			ComparableRequirement("click==7.1.2"),
			ComparableRequirement("domdf_python_tools>=1.1.0"),
			ComparableRequirement("dulwich>=0.19.16"),
			ComparableRequirement("email-validator==1.1.1"),
			ComparableRequirement("isort>=5.0.0"),
			ComparableRequirement("jinja2>=2.11.2"),
			ComparableRequirement("packaging>=20.4"),
			ComparableRequirement("pre-commit>=2.7.1"),
			ComparableRequirement("ruamel.yaml>=0.16.12"),
			ComparableRequirement("tomlkit>=0.7.0"),
			ComparableRequirement("typing_extensions>=3.7.4.3"),
			]

	actual = validate_requirements(requirements, ["domdfcoding", "conda-forge"])

	if actual != expected:
		print(
				coloured_diff(
						list(map(str, expected)),
						list(map(str, actual)),
						fromfile="expected",
						tofile="actual",
						lineterm='',
						)
				)
		raise AssertionError(actual)


@pytest.mark.parametrize(
		"summary", [
				pytest.param("A summary.", id="summary-a"),
				pytest.param("Ma awesome package!", id="summary-b"),
				]
		)
@pytest.mark.parametrize(
		"channels",
		[
				pytest.param(["conda-forge"], id="channels-a"),
				pytest.param(["conda-forge", "domdfcoding"], id="channels-b"),
				pytest.param(["conda-forge", "bioconda"], id="channels-c"),
				pytest.param(("conda-forge", "bioconda"), id="channels-d"),
				pytest.param(["conda-forge", "domdfcoding", "bioconda"], id="channels - e"),
				]
		)
def test_make_conda_description(file_regression: FileRegressionFixture, summary, channels):
	check_file_regression(make_conda_description(summary, channels), file_regression, extension=".md")
