# stdlib
from domdf_python_tools.testing import only_version
from typing import Sequence, Union

# 3rd party
import pytest
from domdf_python_tools.testing import min_version, not_windows, only_windows
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from pytest_regressions.data_regression import DataRegressionFixture
from pytest_regressions.file_regression import FileRegressionFixture

# this package
from shippinglabel.requirements import (
		ComparableRequirement,
		check_dependencies,
		combine_requirements,
		list_requirements,
		read_requirements,
		resolve_specifiers
		)


def check_file_regression(data, file_regression: FileRegressionFixture, extension=".txt"):
	file_regression.check(data, encoding="UTF-8", extension=extension)


class TestComparableRequirement:

	@pytest.fixture(scope="class")
	def req(self):
		return ComparableRequirement('pytest==6.0.0; python_version <= "3.9"')

	@pytest.mark.parametrize(
			"other",
			[
					ComparableRequirement('pytest==6.0.0; python_version <= "3.9"'),
					ComparableRequirement("pytest==6.0.0"),
					ComparableRequirement("pytest"),
					ComparableRequirement("pytest[extra]"),
					Requirement('pytest==6.0.0; python_version <= "3.9"'),
					Requirement("pytest==6.0.0"),
					Requirement("pytest"),
					Requirement("pytest[extra]"),
					"pytest",
					]
			)
	def test_eq(self, req, other):
		assert req == req
		assert req == other

	@pytest.mark.parametrize(
			"other",
			[
					"pytest-rerunfailures",
					ComparableRequirement("pytest-rerunfailures"),
					ComparableRequirement("pytest-rerunfailures==1.2.3"),
					Requirement("pytest-rerunfailures"),
					Requirement("pytest-rerunfailures==1.2.3"),
					ComparableRequirement("pytest"),
					ComparableRequirement("pytest[extra]"),
					Requirement("pytest"),
					Requirement("pytest[extra]"),
					]
			)
	def test_gt(self, req, other):
		assert req < other

	@pytest.mark.parametrize(
			"other",
			[
					"apeye",
					ComparableRequirement("apeye"),
					ComparableRequirement("apeye==1.2.3"),
					Requirement("apeye"),
					Requirement("apeye==1.2.3"),
					]
			)
	def test_lt(self, req, other):
		assert req > other

	@pytest.mark.parametrize(
			"other",
			[
					"pytest-rerunfailures",
					ComparableRequirement("pytest-rerunfailures"),
					ComparableRequirement("pytest-rerunfailures==1.2.3"),
					ComparableRequirement('pytest==6.0.0; python_version <= "3.9"'),
					Requirement("pytest-rerunfailures"),
					Requirement("pytest-rerunfailures==1.2.3"),
					Requirement('pytest==6.0.0; python_version <= "3.9"'),
					ComparableRequirement("pytest==6.0.0"),
					ComparableRequirement("pytest"),
					ComparableRequirement("pytest[extra]"),
					Requirement("pytest==6.0.0"),
					Requirement("pytest"),
					Requirement("pytest[extra]"),
					"pytest",
					]
			)
	def test_ge(self, req, other):
		assert req <= other
		assert req <= req

	@pytest.mark.parametrize(
			"other",
			[
					"apeye",
					ComparableRequirement("apeye"),
					ComparableRequirement("apeye==1.2.3"),
					Requirement("apeye"),
					Requirement("apeye==1.2.3"),
					ComparableRequirement('pytest==6.0.0; python_version <= "3.9"'),
					ComparableRequirement("pytest==6.0.0"),
					ComparableRequirement("pytest"),
					ComparableRequirement("pytest[extra]"),
					Requirement('pytest==6.0.0; python_version <= "3.9"'),
					Requirement("pytest==6.0.0"),
					Requirement("pytest"),
					Requirement("pytest[extra]"),
					"pytest",
					]
			)
	def test_le(self, req, other):
		assert req >= other
		assert req >= req


def test_combine_requirements():
	reqs = [
			ComparableRequirement("foo"),
			ComparableRequirement("foo>2"),
			ComparableRequirement("foo>2.5"),
			ComparableRequirement("foo==3.2.1"),
			ComparableRequirement("foo==3.2.3"),
			ComparableRequirement("foo==3.2.5"),
			]

	assert combine_requirements(reqs) == [Requirement("foo==3.2.1,==3.2.3,==3.2.5,>2.5")]
	assert str(combine_requirements(reqs)[0]) == "foo==3.2.1,==3.2.3,==3.2.5,>2.5"
	assert str(combine_requirements(reqs)[0].specifier) == "==3.2.1,==3.2.3,==3.2.5,>2.5"


def test_combine_requirements_differing_precision():
	reqs = [
			ComparableRequirement("lockfile>=0.9"),
			ComparableRequirement("lockfile>=0.9"),
			ComparableRequirement("lockfile>=0.12.2"),
			]

	assert combine_requirements(reqs) == [Requirement("lockfile>=0.12.2")]


@pytest.mark.parametrize(
		"reqs, combined",
		[
				(
						[
								ComparableRequirement('numpy==1.19.3; platform_system == "Windows"'),
								ComparableRequirement('numpy>=1.19.1; platform_system != "Windows"')
								],
						[
								ComparableRequirement('numpy==1.19.3; platform_system == "Windows"'),
								ComparableRequirement('numpy>=1.19.1; platform_system != "Windows"')
								],
						),
				(
						[
								ComparableRequirement('numpy==1.19.3; platform_system == "Windows"'),
								ComparableRequirement("numpy>=1.19.1"),
								],
						[
								ComparableRequirement('numpy==1.19.3; platform_system == "Windows"'),
								ComparableRequirement("numpy>=1.19.1"),
								],
						),
				(
						[ComparableRequirement("numpy==1.19.3"), ComparableRequirement("numpy>=1.19.1")],
						[ComparableRequirement("numpy==1.19.3")],
						),
				(
						[ComparableRequirement("numpy<=1.19.3"), ComparableRequirement("numpy==1.19.1")],
						[ComparableRequirement("numpy==1.19.1")],
						),
				(
						[ComparableRequirement("numpy<=1.19.3"), ComparableRequirement("numpy<1.19.1")],
						[ComparableRequirement("numpy<1.19.1")],
						),
				(
						[ComparableRequirement("numpy>1.2.3"), ComparableRequirement("numpy>=1.2.2")],
						[ComparableRequirement("numpy>1.2.3")],
						),
				]
		)
def test_combine_requirements_markers(reqs, combined):
	assert combine_requirements(reqs) == combined


@pytest.mark.parametrize(
		"specifiers, resolved",
		[
				([Specifier(">1.2.3"), Specifier(">=1.2.2"), Specifier("<2")], SpecifierSet(">1.2.3,<2")),
				([Specifier(">1.2.3"), Specifier(">=1.2.2")], SpecifierSet(">1.2.3")),
				([Specifier(">=1.2.2"), Specifier("<2")], SpecifierSet(">=1.2.2,<2")),
				([Specifier(">1.2.3"), Specifier("<2")], SpecifierSet(">1.2.3,<2")),
				([Specifier("<1.2.2"), Specifier("<=1.2.3"), Specifier(">2")], SpecifierSet("<1.2.2,>2")),
				([Specifier("<1.2.2"), Specifier("<=1.2.3")], SpecifierSet("<1.2.2")),
				([Specifier("<=1.2.3"), Specifier(">2")], SpecifierSet("<=1.2.3,>2")),
				([Specifier("<1.2.2"), Specifier(">2")], SpecifierSet("<1.2.2,>2")),
				]
		)
def test_resolve_specifiers(specifiers, resolved):
	assert resolve_specifiers(specifiers) == resolved


requirements_a = [
		"autodocsumm>=0.2.0",
		"default-values>=0.2.0",
		"domdf-sphinx-theme>=0.1.0",
		"extras-require>=0.2.0",
		"repo-helper-sphinx-theme>=0.0.2",
		"seed-intersphinx-mapping>=0.1.1",
		"sphinx>=3.0.3",
		"sphinx-click>=2.5.0",
		"sphinx-copybutton>=0.2.12",
		"sphinx-notfound-page>=0.5",
		"sphinx-prompt>=1.1.0",
		"sphinx-tabs>=1.1.13",
		"sphinx-toolbox>=1.7.1",
		"sphinxcontrib-autoprogram>=0.1.5",
		"sphinxcontrib-httpdomain>=1.7.0",
		"sphinxemoji>=0.1.6",
		"toctree-plus>=0.0.4",
		]

requirements_b = [
		"autodocsumm>=0.2.0",
		"default-values>=0.2.0",
		"domdf-sphinx-theme>=0.1.0",
		"domdf-sphinx-theme>=0.1.0",
		"extras-require>=0.2.0",
		"repo-helper-sphinx-theme>=0.0.2",
		"seed-intersphinx-mapping>=0.1.1",
		"sphinx>=3.0.3",
		"sphinx-click>=2.5.0",
		"sphinx-copybutton>=0.2.12",
		"sphinx-copybutton>=0.2.12",
		"sphinx-notfound-page>=0.5",
		"sphinx-prompt>=1.1.0",
		"sphinx-tabs>=1.1.13",
		"sphinx-toolbox>=1.7.1",
		"sphinxcontrib-autoprogram>=0.1.5",
		"sphinxcontrib-autoprogram>=0.1.5",
		"sphinxcontrib-httpdomain>=1.7.0",
		"sphinxemoji>=0.1.6",
		"toctree-plus>=0.0.4",
		"toctree-plus>=0.0.3",
		]

requirements_c = [
		'numpy==1.19.3; platform_system == "Windows"',
		'numpy>=1.19.1; platform_system != "Windows"',
		]


@pytest.mark.parametrize(
		"requirements",
		[
				pytest.param(requirements_a, id='a'),
				pytest.param(requirements_b, id='b'),
				pytest.param(requirements_c, id='c'),
				]
		)
def test_read_requirements(tmp_pathplus, file_regression: FileRegressionFixture, requirements):
	(tmp_pathplus / "requirements.txt").write_lines(requirements)
	requirements, comments = read_requirements(tmp_pathplus / "requirements.txt")
	check_file_regression('\n'.join(str(x) for x in sorted(requirements)), file_regression, extension="._txt")


def test_read_requirements_invalid(tmp_pathplus, file_regression: FileRegressionFixture):
	(tmp_pathplus / "requirements.txt").write_lines([
			"# another comment",
			"autodocsumm>=apples",
			"default-value---0.2.0",
			"domdf-sphinx-theme!!!0.1.0",
			"0.2.0",
			'',
			'',
			"https://bbc.co.uk",
			"toctree-plus>=0.0.4",
			"# a comment",
			])

	with pytest.warns(UserWarning) as record:
		requirements, comments = read_requirements(tmp_pathplus / "requirements.txt")

	# check that only one warning was raised
	assert len(record) == 3
	# check that the message matches

	for idx, warning in enumerate([
		"Creating a LegacyVersion has been deprecated and will be removed in the next major release",
		"Ignored invalid requirement 'domdf-sphinx-theme!!!0.1.0'",
		"Ignored invalid requirement 'https://bbc.co.uk'",
		]):
		assert record[idx].message.args[0] == warning  # type: ignore

	check_file_regression('\n'.join(str(x) for x in sorted(requirements)), file_regression, extension="._txt")
	assert comments == [
			"# another comment",
			"# a comment",
			]


def test_sort_mixed_requirements():

	requirements: Sequence[Union[str, ComparableRequirement]] = [
			"urllib3",
			ComparableRequirement("six==1.15.0"),
			"botocore",
			ComparableRequirement("requests>=2.19.1"),
			"python-dateutil",
			]

	assert sorted(requirements) == [
			"botocore",
			"python-dateutil",
			ComparableRequirement("requests>=2.19.1"),
			ComparableRequirement("six==1.15.0"),
			"urllib3",
			]


def test_check_dependencies(capsys):
	deps = ["pytest", "domdf_python_tools", "madeup_module"]

	missing_deps = check_dependencies(deps, False)
	assert isinstance(missing_deps, list)
	assert len(missing_deps) == 1
	assert missing_deps == ["madeup_module"]

	missing_deps = check_dependencies(deps)
	captured = capsys.readouterr()
	stdout = captured.out.split('\n')
	assert stdout[0] == "The following modules are missing:"
	assert stdout[1] == "['madeup_module']"
	assert stdout[2] == "Please check the documentation."
	assert stdout[3] == ''
	assert isinstance(missing_deps, list)
	assert len(missing_deps) == 1
	assert missing_deps == ["madeup_module"]

	missing_deps = check_dependencies(["pytest"])
	captured = capsys.readouterr()
	stdout = captured.out.split('\n')
	assert stdout[0] == "All modules installed"
	assert stdout[1] == ''
	assert isinstance(missing_deps, list)
	assert len(missing_deps) == 0
	assert missing_deps == []


def test_comparable_requirement():
	assert ComparableRequirement("foo") != ComparableRequirement("bar")
	assert ComparableRequirement("foo") == ComparableRequirement("foo")
	assert ComparableRequirement("foo>=1.2.3") == ComparableRequirement("foo >= 1.2.3")

	def req_with_marker():
		return ComparableRequirement('importlib-metadata>=1.5.0; python_version < "3.8"')

	def req_without_marker():
		return ComparableRequirement("importlib-metadata>=1.5.0")

	assert req_with_marker() == req_with_marker()
	assert req_with_marker() is not req_with_marker()
	assert req_without_marker() is not req_without_marker()

	assert "importlib-metadata" in [req_with_marker()]
	assert req_without_marker() in [req_with_marker()]
	assert req_with_marker() in [req_with_marker()]

	assert "importlib-metadata" in (req_with_marker(), )
	assert req_without_marker() in (req_with_marker(), )
	assert req_with_marker() in (req_with_marker(), )

	assert {req_without_marker(), req_without_marker()} == {req_without_marker()}
	assert {req_with_marker(), req_with_marker()} == {req_with_marker()}

	assert hash(req_with_marker()) == hash(req_with_marker())
	assert hash(req_with_marker()) != hash(req_without_marker())

	assert req_without_marker() not in {req_with_marker()}
	assert req_with_marker() in {req_with_marker()}


only_36 = pytest.param("3.6", marks=only_version((3, 6), reason="Output differs on Python 3.6"))
only_37 = pytest.param("3.7", marks=only_version((3, 7), reason="Output differs on Python 3.7"))
only_38 = pytest.param("3.8", marks=only_version((3, 8), reason="Output differs on Python 3.8"))
min_38 = pytest.param("3.8+", marks=min_version((3, 8), reason="Output differs on Python 3.8+"))
only_39 = pytest.param("3.9", marks=only_version((3, 9), reason="Output differs on Python 3.9"))
only_310 = pytest.param("3.10", marks=only_version((3, 10), reason="Output differs on Python 3.10"))


@not_windows("Output differs on Windows")
@pytest.mark.parametrize(
		"py_version",
		[
				only_36,
				only_37,
				only_38,
				only_39,
				only_310,
				]
		)
@pytest.mark.parametrize(
		"library",
		[
				"shippinglabel",
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


@not_windows("Output differs on Windows")
@pytest.mark.parametrize(
		"py_version",
		[
				only_36,
				only_37,
				min_38,
				]
		)
@pytest.mark.parametrize("depth", [-1, 0, 1, 2, 3])
# @pytest.mark.parametrize("depth", [3])
def test_list_requirements_pytest(
		data_regression: DataRegressionFixture,
		depth,
		py_version,
		):
	data_regression.check(list(list_requirements("pytest", depth=depth)))
