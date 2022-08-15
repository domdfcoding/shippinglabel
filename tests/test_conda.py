# stdlib
from typing import List, Union

# 3rd party
import pytest
from coincidence.regressions import AdvancedFileRegressionFixture
from consolekit.utils import coloured_diff
from domdf_python_tools.paths import PathPlus
from packaging.requirements import InvalidRequirement

# this package
from shippinglabel import conda
from shippinglabel.conda import (
		compile_requirements,
		get_channel_listing,
		make_conda_description,
		prepare_requirements,
		validate_requirements
		)
from shippinglabel.requirements import ComparableRequirement


def test_compile_requirements(tmp_pathplus: PathPlus):
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
			ComparableRequirement("ruamel.yaml>=0.16.12"),  # denormalised elsewhere to solve poerty issue
			ComparableRequirement("tomlkit>=0.7.0"),
			ComparableRequirement("typing-extensions>=3.7.4.3"),
			]


def test_compile_requirements_markers_url_extras(tmp_pathplus: PathPlus):
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


def test_prepare_requirements():
	requirements = [
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
			]

	assert list(prepare_requirements(map(ComparableRequirement, requirements))) == [
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
			ComparableRequirement("ruamel.yaml>=0.16.12"),  # denormalised elsewhere to solve poerty issue
			ComparableRequirement("tomlkit>=0.7.0"),
			ComparableRequirement("typing-extensions>=3.7.4.3"),
			]


def test_prepare_requirements_markers_url_extras():
	requirements = [
			'apeye>=0.3.0; python_version <= "3.9"',
			"pip @ https://github.com/pypa/pip/archive/1.3.1.zip#sha1=da9234ee9982d4bbb3c72346a6de940a148ea686",
			'click==7.1.2; platform_system == "Linux"',
			"requests[security]",
			]

	assert list(prepare_requirements(map(ComparableRequirement, requirements))) == [
			ComparableRequirement("apeye>=0.3.0"),
			ComparableRequirement("click==7.1.2"),
			ComparableRequirement("requests"),
			]


@pytest.mark.flaky(reruns=1, reruns_delay=10)
@pytest.mark.parametrize("clear_cache", [
		False,
		"domdfcoding",
		"conda-forge",
		True,
		])
def test_get_channel_listing(clear_cache: Union[bool, str]):

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


def test_get_channel_listing_error():
	with pytest.raises(ValueError, match="Conda channel 'repo-helper' not found."):
		get_channel_listing("repo-helper")


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
			ComparableRequirement("dom-toml>=0.4.0"),
			ComparableRequirement("dom_toml>=0.4.0"),
			]
	expected = [
			ComparableRequirement("apeye>=0.3.0"),
			ComparableRequirement("attrs>=20.2.0"),
			ComparableRequirement("click==7.1.2"),
			ComparableRequirement("domdf-python-tools>=1.1.0"),  # now in conda-forge
			ComparableRequirement("dulwich>=0.19.16"),
			ComparableRequirement("email-validator==1.1.1"),
			ComparableRequirement("isort>=5.0.0"),
			ComparableRequirement("jinja2>=2.11.2"),
			ComparableRequirement("packaging>=20.4"),
			ComparableRequirement("pre-commit>=2.7.1"),
			ComparableRequirement("ruamel.yaml>=0.16.12"),
			ComparableRequirement("tomlkit>=0.7.0"),
			ComparableRequirement("typing_extensions>=3.7.4.3"),
			ComparableRequirement("dom-toml>=0.4.0"),  # dom-toml is now on conda-forge
			ComparableRequirement("dom_toml>=0.4.0"),
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


def test_validate_requirements_unsatisfied():
	with pytest.raises(
			InvalidRequirement,
			match="Cannot satisfy the requirement 'domdf-python-tools' from any of the channels:",
			):
		validate_requirements(
				[ComparableRequirement("domdf-python-tools>=1.1.0")],
				[],
				)

	with pytest.raises(
			InvalidRequirement,
			match="Cannot satisfy the requirement 'sphinx-pyproject' from any of the channels:",
			):
		validate_requirements(
				[ComparableRequirement("sphinx-pyproject>=1.1.0")],
				["conda-forge"],
				)


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
def test_make_conda_description(
		advanced_file_regression: AdvancedFileRegressionFixture,
		summary: str,
		channels: List[str],
		):
	advanced_file_regression.check(make_conda_description(summary, channels), extension=".md")
