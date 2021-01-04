#!/usr/bin/env python3
#
#  pypi.py
"""
Utilities for working with the Python Package Index (PyPI).

.. versionadded:: 0.2.0
"""
#
#  Copyright © 2020 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
import pathlib
from typing import Any, Callable, Dict, List, Union

# 3rd party
from apeye import URL, RequestsURL
from apeye.slumber_url import HttpNotFoundError, SlumberURL
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from packaging.requirements import InvalidRequirement
from packaging.specifiers import SpecifierSet
from typing_extensions import TypedDict

# this package
from shippinglabel import normalize
from shippinglabel.requirements import operator_symbols, read_requirements

__all__ = [
		"PYPI_API",
		"get_metadata",
		"get_latest",
		"bind_requirements",
		"get_pypi_releases",
		"get_releases_with_digests",
		"get_file_from_pypi",
		"FileURL",
		]

PYPI_API = SlumberURL("https://pypi.org/pypi/", timeout=10)
"""
Instance of :class:`apeye.slumber_url.SlumberURL` which points to the PyPI REST API.

.. versionchanged:: 0.3.0  Now an instance of :class:`apeye.slumber_url.SlumberURL`.
"""


class FileURL(TypedDict):
	"""
	:class:`typing.TypedDict` representing the output of :func:`~.get_releases_with_digests`.

	.. versionadded:: 0.6.1
	"""

	url: str
	digest: str


def get_metadata(pypi_name: str) -> Dict[str, Any]:
	"""
	Returns metadata for the given project on PyPI.

	.. versionadded:: 0.2.0

	:param pypi_name:

	:raises: :exc:`packaging.requirements.InvalidRequirement` if the project cannot be found on PyPI.
	:raises: :exc:`apeye.slumber_url.HttpServerError` if an error occurs in PyPI.
	"""

	query_url: SlumberURL = PYPI_API / pypi_name / "json"

	try:
		return query_url.get()
	except HttpNotFoundError:
		raise InvalidRequirement(f"No such project {pypi_name!r}") from None


def get_latest(pypi_name: str) -> str:
	"""
	Returns the version number of the latest release on PyPI for the given project.

	.. versionadded:: 0.2.0

	:param pypi_name:

	:raises: :exc:`packaging.requirements.InvalidRequirement` if the project cannot be found on PyPI.
	:raises: :exc:`apeye.slumber_url.HttpServerError` if an error occurs in PyPI.
	"""

	return str(get_metadata(pypi_name)["info"]["version"])


def bind_requirements(
		filename: PathLike,
		specifier: str = ">=",
		normalize_func: Callable[[str], str] = normalize,
		) -> int:
	"""
	Bind unbound requirements in the given file to the latest version on PyPI, and any later versions.

	.. versionadded:: 0.2.0

	:param filename: The requirements.txt file to bind requirements in.
	:param specifier: The requirement specifier symbol to use.
	:param normalize_func: Function to use to normalize the names of requirements.

	.. versionchanged:: 0.2.3 Added the ``normalize_func`` keyword-only argument.

	:return: ``1`` if the file was changed; ``0`` otherwise.
	"""

	if specifier not in operator_symbols:
		raise ValueError(f"Invalid specifier {specifier!r}")

	ret = 0
	filename = PathPlus(filename)
	requirements, comments, invalid_lines = read_requirements(
		filename,
		include_invalid=True,
		normalize_func=normalize_func,
		)

	for req in requirements:
		if not req.specifier:
			ret |= 1
			req.specifier = SpecifierSet(f"{specifier}{get_latest(req.name)}")

	sorted_requirements = sorted(requirements)

	buf: List[str] = [*comments, *invalid_lines, *(str(req) for req in sorted_requirements)]

	if buf != list(filter(lambda x: x != '', filename.read_lines())):
		ret |= 1
		filename.write_lines(buf)

	return ret


def get_pypi_releases(pypi_name: str) -> Dict[str, List[str]]:
	"""
	Returns a dictionary mapping PyPI release versions to download URLs.

	.. versionadded:: 0.3.0

	:param pypi_name: The name of the project on PyPI.

	:raises: :exc:`packaging.requirements.InvalidRequirement` if the project cannot be found on PyPI.
	:raises: :exc:`apeye.slumber_url.HttpServerError` if an error occurs in PyPI.
	"""

	pypi_releases = {}

	for release, release_data in get_releases_with_digests(pypi_name).items():
		pypi_releases[release] = [file["url"] for file in release_data]

	return pypi_releases


def get_releases_with_digests(pypi_name: str) -> Dict[str, List[FileURL]]:
	"""
	Returns a dictionary mapping PyPI release versions to download URLs and the sha256sum of the file contents.

	.. versionadded:: 0.6.0

	:param pypi_name: The name of the project on PyPI.

	:raises: :exc:`packaging.requirements.InvalidRequirement` if the project cannot be found on PyPI.
	:raises: :exc:`apeye.slumber_url.HttpServerError` if an error occurs in PyPI.
	"""

	pypi_releases = {}

	for release, release_data in get_metadata(pypi_name)["releases"].items():

		release_urls: List[FileURL] = []

		for file in release_data:
			release_urls.append({"url": file["url"], "digest": file["digests"]["sha256"]})
		pypi_releases[release] = release_urls

	return pypi_releases


def get_file_from_pypi(url: Union[URL, str], tmpdir: PathLike):
	"""
	Download the file with the given URL into the given (temporary) directory.

	.. versionadded:: 0.6.0

	:param url: The URL to download the file from.
	:param tmpdir: The (temporary) directory to store the downloaded file in.
	"""

	if not isinstance(url, RequestsURL):
		url = RequestsURL(url)

	filename = url.name

	r = url.get()
	if r.status_code != 200:  # pragma: no cover
		raise OSError(f"Unable to download '{filename}' from PyPI.")

	(pathlib.Path(tmpdir) / filename).write_bytes(r.content)
