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
from typing import Any, Callable, Dict, List

# 3rd party
from apeye.slumber_url import HttpNotFoundError, SlumberURL
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from packaging.requirements import InvalidRequirement
from packaging.specifiers import SpecifierSet

# this package
from shippinglabel import normalize
from shippinglabel.requirements import operator_symbols, read_requirements

__all__ = ["PYPI_API", "get_metadata", "get_latest", "bind_requirements", "get_pypi_releases"]

PYPI_API = SlumberURL("https://pypi.org/pypi/", timeout=10)
"""
Instance of :class:`apeye.slumber_url.SlumberURL` which points to the PyPI REST API.

.. versionchanged:: 0.3.0  Now an instance of :class:`apeye.slumber_url.SlumberURL`.
"""


def get_metadata(pypi_name: str) -> Dict[str, Any]:
	"""
	Returns metadata for the given project on PyPI.

	:param pypi_name:

	:raises: :exc:`packaging.requirements.InvalidRequirement` if the project cannot be found on PyPI.
	:raises: :exc:`apeye.slumber_url.HttpServerError` if an error occurs in PyPI.

	.. versionadded:: 0.2.0
	"""

	query_url: SlumberURL = PYPI_API / pypi_name / "json"

	try:
		response = query_url.get()
	except HttpNotFoundError:
		raise InvalidRequirement(f"No such project {pypi_name!r}")

	return response


def get_latest(pypi_name: str) -> str:
	"""
	Returns the version number of the latest release on PyPI for the given project.

	:param pypi_name:

	:raises: :exc:`packaging.requirements.InvalidRequirement` if the project cannot be found on PyPI.
	:raises: :exc:`apeye.slumber_url.HttpServerError` if an error occurs in PyPI.

	.. versionadded:: 0.2.0
	"""

	return str(get_metadata(pypi_name)["info"]["version"])


def bind_requirements(
		filename: PathLike,
		specifier: str = ">=",
		normalize_func: Callable[[str], str] = normalize,
		) -> int:
	"""
	Bind unbound requirements in the given file to the latest version on PyPI, and any later versions.

	:param filename: The requirements.txt file to bind requirements in.
	:param specifier: The requirement specifier symbol to use.
	:param normalize_func: Function to use to normalize the names of requirements.

	:return: ``1`` if the file was changed; ``0`` otherwise.

	.. versionadded:: 0.2.0

	.. versionchanged:: 0.2.3 Added the ``normalize_func`` keyword-only argument.
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

	:param pypi_name: The name of the project on PyPI.

	:raises: :exc:`packaging.requirements.InvalidRequirement` if the project cannot be found on PyPI.
	:raises: :exc:`apeye.slumber_url.HttpServerError` if an error occurs in PyPI.

	.. versionadded:: 0.3.0
	"""

	pypi_releases = {}

	for release, release_data in get_metadata(pypi_name)["releases"].items():

		release_urls: List[str] = []

		for file in release_data:
			release_urls.append(file["url"])
		pypi_releases[release] = release_urls

	return pypi_releases
