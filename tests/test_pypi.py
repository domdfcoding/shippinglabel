# stdlib
import gzip
import re
import tarfile
import zipfile
from typing import Union
from urllib.parse import urlparse

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus
from packaging.requirements import InvalidRequirement
from packaging.version import Version

# this package
from shippinglabel.pypi import (
		bind_requirements,
		get_file_from_pypi,
		get_latest,
		get_metadata,
		get_pypi_releases,
		get_releases_with_digests,
		get_sdist_url,
		get_wheel_tag_mapping,
		get_wheel_url
		)
from shippinglabel.requirements import operator_symbols


@pytest.mark.parametrize(
		"input_s, expected_retval, output",
		[
				pytest.param('', 0, '', id="empty"),
				pytest.param('\n', 0, '\n', id="newline_only"),
				pytest.param('# intentionally empty\n', 0, '# intentionally empty\n', id="intentionally_empty"),
				pytest.param(
						'docutils\n# comment at end\n',
						1,
						'# comment at end\ndocutils>=0.17\n',
						id="comment_at_end",
						),
				pytest.param('docutils\nbar\n', 1, 'bar>=0.2.1\ndocutils>=0.17\n', id="foo_bar"),
				pytest.param('bar\ndocutils\n', 1, 'bar>=0.2.1\ndocutils>=0.17\n', id="bar_foo"),
				pytest.param('a\nc\nb\n', 1, 'a>=1.0\nb>=1.0.0\nc>=0.1.0\n', id="a_c_b"),
				pytest.param('a\nb\nc', 1, 'a>=1.0\nb>=1.0.0\nc>=0.1.0\n', id="a_b_b"),
				pytest.param(
						'#comment1\ndocutils\n#comment2\nbar\n',
						1,
						'#comment1\n#comment2\nbar>=0.2.1\ndocutils>=0.17\n',
						id="comment_foo_comment_bar",
						),
				pytest.param(
						'#comment1\nbar\n#comment2\ndocutils\n',
						1,
						'#comment1\n#comment2\nbar>=0.2.1\ndocutils>=0.17\n',
						id="comment_bar_comment_foo",
						),
				pytest.param(
						'#comment\n\ndocutils\nbar\n',
						1,
						'#comment\nbar>=0.2.1\ndocutils>=0.17\n',
						id="comment_foo_bar",
						),
				pytest.param(
						'#comment\n\nbar\ndocutils\n',
						1,
						'#comment\nbar>=0.2.1\ndocutils>=0.17\n',
						id="comment_barfoo_",
						),
				pytest.param('\ndocutils\nbar\n', 1, 'bar>=0.2.1\ndocutils>=0.17\n', id="foo_bar_2"),
				pytest.param('\nbar\ndocutils\n', 1, 'bar>=0.2.1\ndocutils>=0.17\n', id="bar_foo_2"),
				pytest.
				param('pyramid-foo==1\npyramid>=2\n', 1, 'pyramid>=2\npyramid-foo==1\n', id="pyramid-foo_pyramid"),
				pytest.param(
						'a==1\n'
						'c>=1\n'
						'bbbb!=1\n'
						'c-a>=1;python_version>="3.6"\n'
						'e>=2\n'
						'd>2\n'
						'g<2\n'
						'f<=2\n',
						1,
						'a==1\n'
						'bbbb!=1\n'
						'c>=1\n'
						'c-a>=1; python_version >= "3.6"\n'
						'd>2\n'
						'e>=2\n'
						'f<=2\n'
						'g<2\n',
						id="a-g",
						),
				pytest.param(
						'ocflib\nDjango\nPyMySQL\n',
						1,
						'django>=3.1.5\nocflib>=2020.12.5.10.49\npymysql>=0.10.1\n',
						id="real_requirements"
						),
				pytest.param(
						'bar\npkg-resources==0.0.0\ndocutils\n',
						1,
						'bar>=0.2.1\ndocutils>=0.17\npkg-resources==0.0.0\n',
						id="bar_pkg-resources_foo",
						),
				pytest.param(
						'docutils\npkg-resources==0.0.0\nbar\n',
						1,
						'bar>=0.2.1\ndocutils>=0.17\npkg-resources==0.0.0\n',
						id="foo_pkg-resources_bar",
						),
				pytest.param('foo???1.2.3\nbar\n', 1, 'foo???1.2.3\nbar>=0.2.1\n', id="bad_specifiers"),
				pytest.param(
						'wxpython>=4.0.7; platform_system == "Windows" and python_version < "3.9"\n'
						'wxpython>=4.0.7; platform_system == "Darwin" and python_version < "3.9"\n',
						0,
						'wxpython>=4.0.7; platform_system == "Windows" and python_version < "3.9"\n'
						'wxpython>=4.0.7; platform_system == "Darwin" and python_version < "3.9"\n',
						id="markers",
						),
				pytest.param(
						'pyreadline @ https://github.com/domdfcoding/3.10-Wheels/raw/936f0570b561f3cda0be94d93066a11c6fe782f1/pyreadline-2.0-py3-none-any.whl ; python_version == "3.10" and platform_system == "Windows"',
						1,
						'pyreadline@ https://github.com/domdfcoding/3.10-Wheels/raw/936f0570b561f3cda0be94d93066a11c6fe782f1/pyreadline-2.0-py3-none-any.whl ; python_version == "3.10" and platform_system == "Windows"\n',
						id="url"
						),
				]
		)
@pytest.mark.usefixtures("cassette")
def test_bind_requirements(
		input_s: str,
		expected_retval: int,
		output: str,
		tmp_pathplus: PathPlus,
		):
	path = tmp_pathplus / "requirements.txt"
	path.write_text(input_s)

	assert bind_requirements(path) == expected_retval

	assert path.read_text() == output


def test_bind_requirements_error(tmp_pathplus: PathPlus):
	path = tmp_pathplus / "requirements.txt"
	path.write_text('bar\npkg-resources==0.0.0\ndocutils\n', )

	for specifier in operator_symbols:
		bind_requirements(path, specifier=specifier)

	for specifier in "?*!$&^|":
		with pytest.raises(ValueError, match=re.escape(f"Invalid specifier '{specifier}'")):
			bind_requirements(path, specifier=specifier)


def uri_validator(x) -> bool:  # noqa: MAN001
	# Based on https://stackoverflow.com/a/38020041
	# By https://stackoverflow.com/users/1668293/alemol and https://stackoverflow.com/users/953553/andilabs
	result = urlparse(x)
	return all([result.scheme, result.netloc, result.path])


@pytest.mark.usefixtures("module_cassette")
def test_get_pypi_releases(advanced_data_regression: AdvancedDataRegressionFixture):
	releases = get_pypi_releases("octocheese")
	assert isinstance(releases, dict)

	release_url_list = releases["0.0.2"]
	assert isinstance(release_url_list, list)

	for url in release_url_list:
		print(url)
		assert isinstance(url, str)
		assert uri_validator(url)

	advanced_data_regression.check(release_url_list)


@pytest.mark.usefixtures("module_cassette")
def test_get_releases_with_digests(advanced_data_regression: AdvancedDataRegressionFixture):
	releases = get_releases_with_digests("octocheese")
	assert isinstance(releases, dict)

	release_url_list = releases["0.0.2"]
	assert isinstance(release_url_list, list)

	for url in release_url_list:
		print(url)
		assert isinstance(url, dict)

	advanced_data_regression.check(release_url_list)


def test_get_file_from_pypi(
		advanced_data_regression: AdvancedDataRegressionFixture,
		tmp_pathplus: PathPlus,
		):
	url = (
			"https://files.pythonhosted.org/packages/fa/fb"
			"/d301018af3f22bdbf34b624037e851561914c244a26add8278e4e7273578/octocheese-0.0.2.tar.gz"
			)

	get_file_from_pypi(url, tmp_pathplus)

	the_file = tmp_pathplus / "octocheese-0.0.2.tar.gz"
	assert the_file.is_file()

	# Check it isn't a wheel or Windows-built sdist
	assert not zipfile.is_zipfile(the_file)

	with gzip.open(the_file, 'r'):
		# Check can be opened as gzip file
		assert True

	listing = {
			"octocheese-0.0.2",  # top level directory
			"octocheese-0.0.2/octocheese",  # module
			"octocheese-0.0.2/octocheese/__init__.py",
			"octocheese-0.0.2/octocheese/__main__.py",
			"octocheese-0.0.2/octocheese/action.py",
			"octocheese-0.0.2/octocheese/colours.py",
			"octocheese-0.0.2/octocheese/core.py",
			"octocheese-0.0.2/octocheese.egg-info",  # egg-info
			"octocheese-0.0.2/octocheese.egg-info/dependency_links.txt",
			"octocheese-0.0.2/octocheese.egg-info/entry_points.txt",
			"octocheese-0.0.2/octocheese.egg-info/not-zip-safe",
			"octocheese-0.0.2/octocheese.egg-info/PKG-INFO",
			"octocheese-0.0.2/octocheese.egg-info/requires.txt",
			"octocheese-0.0.2/octocheese.egg-info/SOURCES.txt",
			"octocheese-0.0.2/octocheese.egg-info/top_level.txt",
			"octocheese-0.0.2/__pkginfo__.py",  # metadata
			"octocheese-0.0.2/LICENSE",
			"octocheese-0.0.2/MANIFEST.in",
			"octocheese-0.0.2/PKG-INFO",
			"octocheese-0.0.2/README.rst",
			"octocheese-0.0.2/requirements.txt",
			"octocheese-0.0.2/setup.cfg",
			"octocheese-0.0.2/setup.py",
			}

	with tarfile.open(the_file, "r:gz") as tar:
		assert {f.name for f in tar.getmembers()} == listing
		advanced_data_regression.check(sorted({f.name for f in tar.getmembers()}))


@pytest.mark.usefixtures("module_cassette")
def test_get_latest():
	assert get_latest("octocheese") == "0.2.1"


@pytest.mark.usefixtures("module_cassette")
def test_get_metadata(advanced_data_regression: AdvancedDataRegressionFixture):
	advanced_data_regression.check(get_metadata("octocheese"))


@pytest.mark.usefixtures("cassette")
def test_metadata_nonexistant():
	with pytest.raises(InvalidRequirement, match="No such project 'FizzBuzz'"):
		get_metadata("FizzBuzz")


def _param(name: str, version: Union[str, Version]):  # noqa: MAN002
	return pytest.param(name, version, id=name)


@pytest.mark.parametrize("name, version", [_param("greppy", "0.0.0"), _param("domdf_python_tools", "1.2.3")])
def test_get_sdist_url_no_version(name: str, version: Union[str, Version]):
	with pytest.raises(InvalidRequirement, match="Cannot find version .* on PyPI."):
		get_sdist_url(name, version)


@pytest.mark.parametrize("name, version", [_param("domdf_python_toolsz", "1.2.3")])
def test_get_sdist_url_no_project(name: str, version: Union[str, Version]):
	with pytest.raises(InvalidRequirement, match="No such project .*"):
		get_sdist_url(name, version)


@pytest.mark.parametrize("name, version", [_param("microsoft", "0.0.1")])
def test_get_sdist_url_no_files(name: str, version: Union[str, Version]):
	with pytest.raises(ValueError, match="Version 0.0.1 has no files on PyPI."):
		get_sdist_url(name, version)


@pytest.mark.parametrize("name, version", [_param("protobuf", "3.12.0")])
def test_get_sdist_url_no_sdist(name: str, version: Union[str, Version]):
	with pytest.raises(ValueError, match="Version 3.12.0 has no sdist on PyPI."):
		get_sdist_url(name, version, strict=True)

	assert get_sdist_url(
			name, version
			) == "https://files.pythonhosted.org/packages/1e/80/8470c36703f2fd54882eba1f111c74264b540b1376994a9a87bf81fe931e/protobuf-3.12.0-cp27-cp27m-macosx_10_9_x86_64.whl"


@pytest.mark.parametrize(
		"name, version",
		[
				_param("domdf_python_tools", "1.0.0"),
				_param("mathematical", "0.4.0"),
				_param("shippinglabel", Version("0.12.0")),
				_param("numpy", Version("1.20.3")),
				]
		)
def test_get_sdist_url(
		name: str,
		version: Union[str, Version],
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	advanced_file_regression.check(get_sdist_url(name, version))


@pytest.mark.parametrize(
		"name, version",
		[
				_param("domdf_python_tools", "1.0.0"),
				_param("mathematical", "0.4.0"),
				_param("shippinglabel", Version("0.12.0")),
				]
		)
def test_get_wheel_url(
		name: str,
		version: Union[str, Version],
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	advanced_file_regression.check(get_wheel_url(name, version))


@pytest.mark.parametrize("name, version", [_param("greppy", "0.0.0"), _param("domdf_python_tools", "1.2.3")])
def test_get_wheel_url_no_version(name: str, version: Union[str, Version]):
	with pytest.raises(InvalidRequirement, match="Cannot find version .* on PyPI."):
		get_wheel_url(name, version)


@pytest.mark.parametrize("name, version", [_param("domdf_python_toolsz", "1.2.3")])
def test_get_wheel_url_no_project(name: str, version: Union[str, Version]):
	with pytest.raises(InvalidRequirement, match="No such project .*"):
		get_wheel_url(name, version)


@pytest.mark.parametrize("name, version", [_param("microsoft", "0.0.1")])
def test_get_wheel_url_no_files(name: str, version: Union[str, Version]):
	with pytest.raises(ValueError, match=f"Version {version} has no files on PyPI."):
		get_wheel_url(name, version)


def test_get_wheel_url_no_wheels():
	with pytest.raises(ValueError, match="Version 0.1.3 has no wheels on PyPI."):
		get_wheel_url("greppy", "0.1.3", strict=True)

	with pytest.raises(ValueError, match="Version 0.0.1 has no files on PyPI."):
		get_wheel_url("microsoft", "0.0.1")

	assert get_wheel_url(
			"greppy", "0.1.3"
			) == "https://files.pythonhosted.org/packages/c6/a8/ae563011a12812f8efcbbb9385a6451f4d6674d47055e97f95fae6e883d9/greppy-0.1.3.tar.gz"


@pytest.mark.flaky(reruns=1, reruns_delay=10)
@pytest.mark.parametrize(
		"name, version",
		[
				_param("domdf_python_tools", "1.0.0"),
				_param("mathematical", "0.4.0"),
				_param("shippinglabel", Version("0.12.0")),
				_param("numpy", Version("1.20.3")),
				]
		)
def test_get_wheel_tag_mapping(
		name: str,
		version: Union[Version, str],
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	tag_url_map, non_wheel_urls = get_wheel_tag_mapping(name, version)
	tag_url_map_2 = dict(sorted((str(k), v) for k, v in tag_url_map.items()))
	advanced_data_regression.check((tag_url_map_2, non_wheel_urls))


@pytest.mark.parametrize("name, version", [_param("microsoft", "0.0.1")])
def test_get_wheel_tag_mapping_no_files(name: str, version: Union[str, Version]):
	with pytest.raises(ValueError, match=f"Version {version} has no files on PyPI."):
		get_wheel_tag_mapping(name, version)
