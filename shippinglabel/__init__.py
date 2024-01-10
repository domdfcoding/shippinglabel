#!/usr/bin/env python3
#
#  __init__.py
"""
Utilities for handling packages.
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
import re
import warnings
from typing import Dict, Iterable, List, Optional

# 3rd party
import dist_meta.distributions
from dist_meta.metadata_mapping import MetadataMapping
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from packaging.version import InvalidVersion, Version

__all__ = [
		"no_dev_versions",
		"no_pre_versions",
		"normalize",
		"normalize_keep_dot",
		"read_pyvenv",
		"get_project_links",
		]

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2020 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "1.7.1"
__email__: str = "dominic@davis-foster.co.uk"


def no_dev_versions(versions: Iterable[str]) -> List[str]:
	"""
	Returns the subset of ``versions`` which does not end with ``-dev``.

	:param versions:
	"""

	return [v for v in versions if not v.endswith("-dev")]


def no_pre_versions(versions: Iterable[str]) -> List[str]:
	"""
	Returns the subset of ``versions`` which are not prereleases (alpha, beta, dev, rc etc.).

	.. versionadded:: 0.15.0

	:param versions:
	"""

	output = []

	for v in versions:
		try:
			if not Version(v).is_prerelease:
				output.append(v)
		except InvalidVersion:
			output.append(v)

	return output


_normalize_pattern = re.compile(r"[-_.]+")
_normalize_keep_dot_pattern = re.compile(r"[-_]+")


def normalize(name: str) -> str:
	"""
	Normalize the given name for PyPI et al.

	From :pep:`503` (public domain).

	:param name: The project name.
	"""

	return _normalize_pattern.sub('-', name).lower()


def normalize_keep_dot(name: str) -> str:
	"""
	Normalize the given name for PyPI et al., but keep dots in namespace packages.

	.. versionadded:: 0.2.1

	:param name: The project name.
	"""

	return _normalize_keep_dot_pattern.sub('-', name).lower()


def read_pyvenv(venv_dir: PathLike) -> Dict[str, str]:
	"""
	Reads the ``pyvenv.cfg`` for the given virtualenv, and returns a ``key: value`` mapping of its contents.

	.. versionadded:: 0.9.0

	:param venv_dir:
	"""

	pyvenv_config: Dict[str, str] = {}

	for line in (PathPlus(venv_dir) / "pyvenv.cfg").read_lines():
		if line:
			key, value, *_ = line.split(" = ")
			pyvenv_config[key] = value

	return pyvenv_config


class ProjectLinks(MetadataMapping):
	pass


def get_project_links(
		project_name: str,
		path: Optional[Iterable[PathLike]] = None,
		) -> MetadataMapping:
	"""
	Returns the web links for the given project.

	The exact keys vary, but common keys include "Documentation" and "Issue Tracker".

	.. versionadded:: 0.12.0

	:param project_name:
	:param path: The directories entries to search for distributions in.
		This can be used to search in a different (virtual) environment.
	:default path: :py:data:`sys.path`

	:rtype:

	.. versionchanged:: 1.0.0  Now returns a :class:`dist_meta.metadata_mapping.MetadataMapping` object.

	.. versionchanged:: 1.2.0

		The :core-meta:`Home-Page` field from Python core metadata is included under the ``Homepage`` key, if present.
		This matches the output parsed from PyPI for packages which are not installed.

	.. versionchanged:: 1.7.0  Added the ``path`` argument.
	"""

	# this package
	from shippinglabel.pypi import get_metadata

	warnings.warn(
			"shippinglabel.get_project_links is deprecated and will be removed in v2.0.0.\n"
			"Please import from the shippinglabel_pypi package instead.",
			DeprecationWarning,
			)

	# Try a local package first

	urls = ProjectLinks()

	try:
		dist = dist_meta.distributions.get_distribution(project_name, path=path)
		meta = dist.get_metadata()
		raw_urls = meta.get_all("Project-URL", default=())

		for url in raw_urls:
			label, url, *_ = map(str.strip, url.split(','))
			urls[label] = url

		if "Home-Page" in meta:
			urls["Homepage"] = meta["Home-Page"]

	except dist_meta.distributions.DistributionNotFoundError:
		# Fall back to PyPI

		metadata = get_metadata(project_name)["info"]

		if "project_urls" in metadata and metadata["project_urls"]:
			for label, url in metadata["project_urls"].items():
				urls[label] = url

	return urls
