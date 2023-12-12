# stdlib
import sys
from typing import List, Sequence, Union

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from coincidence.selectors import min_version, not_windows, only_version
from deprecation import fail_if_not_removed  # type: ignore[import]
from domdf_python_tools.paths import PathPlus
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from pytest_regressions.data_regression import DataRegressionFixture
from typing_extensions import Literal

# this package
from shippinglabel.requirements import (
		ComparableRequirement,
		check_dependencies,
		combine_requirements,
		list_requirements,
		parse_pyproject_dependencies,
		parse_pyproject_extras,
		parse_requirements,
		read_requirements,
		resolve_specifiers
		)


class TestComparableRequirement:

	@pytest.fixture(scope="class")
	def req(self) -> ComparableRequirement:
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
	def test_eq(self, req: ComparableRequirement, other: Union[str, ComparableRequirement]):
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
	def test_gt(
			self,
			req: ComparableRequirement,
			other: Union[str, ComparableRequirement],
			):
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
	def test_lt(
			self,
			req: ComparableRequirement,
			other: Union[str, ComparableRequirement],
			):
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
	def test_ge(
			self,
			req: ComparableRequirement,
			other: Union[str, ComparableRequirement],
			):
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
	def test_le(
			self,
			req: ComparableRequirement,
			other: Union[str, ComparableRequirement],
			):
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


def test_combine_requirements_no_mutation():
	# Input objects should not be mutated
	reqs = [
			ComparableRequirement("foo>2"),
			ComparableRequirement("foo>2.5"),
			]
	assert combine_requirements(reqs) == [ComparableRequirement("foo>2.5")]

	assert reqs == [
			ComparableRequirement("foo>2"),
			ComparableRequirement("foo>2.5"),
			]


def test_combine_requirements_duplicates():
	reqs = [
			ComparableRequirement('typing-extensions>=3.6.4; python_version < "3.8"'),
			ComparableRequirement("typing-extensions>=3.7.4.3"),
			ComparableRequirement("typing-extensions>=3.7.4.3"),
			ComparableRequirement("typing-extensions>=3.7.4.3"),
			ComparableRequirement("typing-extensions>=3.7.4.3"),
			ComparableRequirement("typing-extensions>=3.7.4.1"),
			ComparableRequirement("typing-extensions>=3.7.4"),
			ComparableRequirement('typing-extensions; python_version < "3.8"'),
			]

	combined_reqs = combine_requirements(reqs)
	assert len(combined_reqs) == 2
	assert combined_reqs[1] == ComparableRequirement("typing-extensions>=3.7.4.3")
	assert combined_reqs[0] == ComparableRequirement('typing-extensions>=3.6.4; python_version < "3.8"')

	reqs.append(reqs.pop(0))

	combined_reqs = combine_requirements(reqs)
	assert len(combined_reqs) == 2
	assert combined_reqs[0] == ComparableRequirement("typing-extensions>=3.7.4.3")
	assert combined_reqs[1] == ComparableRequirement('typing-extensions>=3.6.4; python_version < "3.8"')


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
def test_combine_requirements_markers(
		reqs: List[ComparableRequirement],
		combined: List[ComparableRequirement],
		):
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
def test_resolve_specifiers(specifiers: List[Specifier], resolved: SpecifierSet):
	assert resolve_specifiers(specifiers) == resolved


requirements_a = [
		"autodocsumm>=0.2.0",
		"default-values>=0.2.0",
		"domdf-sphinx-theme>=0.1.0",
		"extras-require>=0.2.0",
		"repo-helper-sphinx-theme>=0.0.2",
		"seed-intersphinx-mapping>=0.1.1",
		"sphinx>=3.0.3",
		"ruamel-yaml>=0.16.12",
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
		"ruamel.yaml>=0.16.12",
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
def test_read_requirements(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		requirements: List[str],
		):
	(tmp_pathplus / "requirements.txt").write_lines(requirements)
	advanced_data_regression.check([
			str(x) for x in sorted(read_requirements(tmp_pathplus / "requirements.txt")[0])
			])


@pytest.mark.parametrize(
		"requirements",
		[
				pytest.param(requirements_a, id='a'),
				pytest.param(requirements_b, id='b'),
				pytest.param(requirements_c, id='c'),
				pytest.param(iter(requirements_a), id="iter(a)"),
				pytest.param(iter(requirements_b), id="iter(b)"),
				pytest.param(iter(requirements_c), id="iter(c)"),
				pytest.param(set(requirements_a), id="set(a)"),
				pytest.param(set(requirements_b), id="set(b)"),
				pytest.param(set(requirements_c), id="set(c)"),
				pytest.param(tuple(requirements_a), id="tuple(a)"),
				pytest.param(tuple(requirements_b), id="tuple(b)"),
				pytest.param(tuple(requirements_c), id="tuple(c)"),
				]
		)
def test_parse_requirements(
		advanced_data_regression: AdvancedDataRegressionFixture,
		requirements: List[str],
		):
	advanced_data_regression.check([str(x) for x in sorted(parse_requirements(requirements)[0])])


@min_version("3.7", reason="Latest packaging is 3.7+")
def test_read_requirements_invalid(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
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
			"   # a comment",
			])

	with pytest.warns(UserWarning) as record:
		requirements, comments = read_requirements(tmp_pathplus / "requirements.txt")

	# check that only one warning was raised
	assert len(record) == 3

	# check that the messages match
	for idx, warning in enumerate([
		"Ignored invalid requirement 'autodocsumm>=apples'",
		"Ignored invalid requirement 'domdf-sphinx-theme!!!0.1.0'",
		"Ignored invalid requirement 'https://bbc.co.uk'",
	]):
		assert record[idx].message.args[0] == warning  # type: ignore[union-attr]

	advanced_data_regression.check([str(x) for x in sorted(requirements)])
	assert comments == ["# another comment", "   # a comment"]


@only_version("3.6", reason="Latest packaging is 3.7+")
def test_read_requirements_invalid_py36(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
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
			"   # a comment",
			])

	with pytest.warns(UserWarning) as record:
		requirements, comments = read_requirements(tmp_pathplus / "requirements.txt")

	# check that only one warning was raised
	assert len(record) == 3

	# check that the messages match
	for idx, warning in enumerate([
		"Creating a LegacyVersion has been deprecated and will be removed in the next major release",
		"Ignored invalid requirement 'domdf-sphinx-theme!!!0.1.0'",
		"Ignored invalid requirement 'https://bbc.co.uk'",
	]):
		assert record[idx].message.args[0] == warning  # type: ignore[union-attr]

	advanced_data_regression.check([str(x) for x in sorted(requirements)])
	assert comments == ["# another comment", "   # a comment"]


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


@fail_if_not_removed
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

	def req_with_marker() -> ComparableRequirement:
		return ComparableRequirement('importlib-metadata>=1.5.0; python_version < "3.8"')

	def req_without_marker() -> ComparableRequirement:
		return ComparableRequirement("importlib-metadata>=1.5.0")

	def req_with_different_marker() -> ComparableRequirement:
		return ComparableRequirement('importlib-metadata>=1.5.0; python_version < "3.10"')

	assert req_with_marker() == req_with_marker()
	assert req_with_marker() is not req_with_marker()
	assert req_without_marker() is not req_without_marker()
	assert req_with_marker() != req_with_different_marker()

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

	assert req_without_marker() != "123foo?"


only_36 = pytest.param("3.6", marks=only_version((3, 6), reason="Output differs on Python 3.6"))
only_37 = pytest.param("3.7", marks=only_version((3, 7), reason="Output differs on Python 3.7"))
only_38 = pytest.param("3.8", marks=only_version((3, 8), reason="Output differs on Python 3.8"))
min_38 = pytest.param("3.8+", marks=min_version((3, 8), reason="Output differs on Python 3.8+"))
min_311 = pytest.param("3.11+", marks=min_version((3, 11), reason="Output differs on Python 3.11+"))
only_39 = pytest.param("3.9", marks=only_version((3, 9), reason="Output differs on Python 3.9"))
only_310 = pytest.param("3.10", marks=only_version((3, 10), reason="Output differs on Python 3.10"))


@not_windows("Output differs on Windows")
@pytest.mark.parametrize("py_version", [
		only_36,
		only_37,
		only_38,
		only_39,
		only_310,
		])
@pytest.mark.parametrize(
		"library", [
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
		advanced_data_regression: AdvancedDataRegressionFixture,
		library: str,
		depth: int,
		py_version: str,
		):
	advanced_data_regression.check(list(list_requirements(library, depth=depth)))


@not_windows("Output differs on Windows")
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
# @pytest.mark.parametrize("depth", [3])
def test_list_requirements_pytest(
		data_regression: DataRegressionFixture,
		depth: int,
		py_version: str,
		):
	data_regression.check(list(list_requirements("pytest", depth=depth)))


@pytest.fixture()
def pyproject_toml(tmp_pathplus: PathPlus) -> PathPlus:

	filename = (tmp_pathplus / "pyproject.toml")
	filename.write_lines([
			"[build-system]",
			'requires = [ "setuptools>=40.6.0", "wheel>=0.34.2",]',
			'build-backend = "setuptools.build_meta"',
			'',
			"[project]",
			"dependencies = [",
			'  "httpx",',
			'  "gidgethub[httpx]>4.0.0",',
			"  \"django>2.1; os_name != 'nt'\",",
			"  \"django>2.0; os_name == 'nt'\"",
			']',
			'',
			"[project.optional-dependencies]",
			"test = [",
			'  "pytest < 5.0.0",',
			'  "pytest-cov[all]"',
			']',
			"[tool.flit.metadata]",
			"requires = [",
			'\t"requests >=2.6",',
			"\t\"configparser; python_version == '2.7'\",",
			']',
			'',
			"[tool.flit.metadata.requires-extra]",
			"test = [",
			'\t"pytest >=2.7.3",',
			'\t"pytest-cov",',
			']',
			])

	return filename


@pytest.mark.parametrize("flavour", ["auto", "pep621", "flit"])
def test_parse_pyproject_dependencies(
		pyproject_toml: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		flavour: Literal["auto", "pep621", "flit"],
		):
	deps = parse_pyproject_dependencies(pyproject_toml, flavour)
	advanced_data_regression.check(sorted(str(x) for x in deps))


@pytest.mark.parametrize("flavour", ["auto", "pep621", "flit"])
def test_parse_pyproject_extras(
		pyproject_toml: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		flavour: Literal["auto", "pep621", "flit"],
		):
	extras = parse_pyproject_extras(pyproject_toml, flavour)
	advanced_data_regression.check({k: sorted(str(x) for x in v) for k, v in extras.items()})
