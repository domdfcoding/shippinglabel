#!/usr/bin/env python3
#
#  conda.py
"""
Functions to aid building of conda packages.

.. versionadded:: 0.7.0
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
import atexit
import difflib
import warnings
from contextlib import suppress
from datetime import datetime, timedelta
from itertools import chain
from typing import Iterable, List

# 3rd party
import apeye.slumber_url.exceptions
import platformdirs
from apeye.slumber_url import SlumberURL
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import DelimitedList
from packaging.requirements import InvalidRequirement

# this package
from shippinglabel import __version__, normalize
from shippinglabel.requirements import ComparableRequirement, combine_requirements, read_requirements

__all__ = [
		"CONDA_API",
		"clear_cache",
		"get_channel_listing",
		"compile_requirements",
		"validate_requirements",
		"make_conda_description",
		"prepare_requirements",
		]

warnings.warn(
		"shippinglabel.conda is deprecated and will be removed in v2.0.0.\n"
		"Please use shippinglabel-conda instead.",
		DeprecationWarning,
		)

CONDA_API = SlumberURL("https://conda.anaconda.org", append_slash=False)
"""
Instance of :class:`apeye.slumber_url.SlumberURL` for accessing the Conda API.

.. versionadded:: 0.7.0
"""

atexit.register(CONDA_API.session.close)

cache_dir = PathPlus(
		platformdirs.user_cache_dir(
				appname="shippinglabel",
				appauthor="domdfcoding",
				version=__version__,
				)
		) / "conda_cache"


def clear_cache(*channel_name: str) -> None:
	r"""
	Clear the cached Conda channel listings.

	.. versionadded:: 0.7.0

	:param \*channel_name: The name(s) of the channels to clear the cache for.

	If no arguments are given the cache is cleared for all channels.

	.. latex:clearpage::
	"""

	filenames: Iterable[PathPlus]

	if channel_name:
		filenames = (cache_dir / f"{channel}.json" for channel in channel_name)
	else:
		filenames = cache_dir.glob("*.json")

	for filename in filenames:
		filename.unlink(missing_ok=True)


def get_channel_listing(channel_name: str) -> List[str]:
	"""
	Obtain the list of packages in the given Conda channel, either from the cache or from the Conda API.

	Responses are cached for 48 hours. The cache can be cleared manually with :func:`~.clear_cache`.

	.. versionadded:: 0.7.0

	:param channel_name:

	:raises ValueError: if the channel can't be found (*New in version 0.15.0*).
	"""

	cache_dir.maybe_make(parents=True)

	filename = cache_dir / f"{channel_name}.json"

	if filename.is_file():
		data = filename.load_json()
		if datetime.fromtimestamp(data["expires"]) > datetime.now():
			return data["packages"]

	conda_packages = set()

	try:
		for package in (CONDA_API / channel_name / "noarch" / "repodata.json").get()["packages"].values():
			conda_packages.add(package["name"])
	except apeye.slumber_url.exceptions.HttpNotFoundError:
		raise ValueError(f"Conda channel {channel_name!r} not found.")

	with suppress(apeye.slumber_url.exceptions.HttpNotFoundError):
		# TODO: other architectures
		for package in (CONDA_API / channel_name / "linux-64" / "repodata.json").get()["packages"].values():
			conda_packages.add(package["name"])

	data = {"expires": (datetime.now() + timedelta(hours=48)).timestamp(), "packages": sorted(conda_packages)}

	filename.dump_json(data, indent=2)

	return data["packages"]


def prepare_requirements(requirements: Iterable[ComparableRequirement]) -> Iterable[ComparableRequirement]:
	"""
	Prepare a list of requirements for use with conda.

	This entails removing any extras and markers from the requirements, and skipping any requirements with URLs,
	as conda does not support these.

	.. versionadded:: 0.13.0

	:param requirements:
	"""

	for requirement in sorted(combine_requirements(requirements)):
		if requirement.url:  # pragma: no cover
			continue

		# TODO: add the extra requirements
		if requirement.extras:
			requirement.extras = set()
		if requirement.marker:
			requirement.marker = None

		yield requirement


def compile_requirements(
		repo_dir: PathPlus,
		extras: Iterable[str] = (),
		) -> List[ComparableRequirement]:
	"""
	Compile a list of requirements for the package from the :file:`requirements.txt` file,
	and any extra dependencies.

	.. versionadded:: 0.7.0

	:param repo_dir:
	:param extras: A list of additional, optional requirements.
		These would be specified in "extras_require" for setuptools.
	"""  # noqa: D400

	requirements = chain(
			read_requirements(repo_dir / "requirements.txt")[0],
			[ComparableRequirement(r) for r in extras],
			)

	return list(prepare_requirements(requirements))


def validate_requirements(
		requirements: Iterable[ComparableRequirement],
		conda_channels: Iterable[str],
		) -> List[ComparableRequirement]:
	"""
	Ensure that all requirements are available from the given Conda channels,
	and normalize the names to those in the Conda channel.

	.. versionadded:: 0.7.0

	:param requirements:
	:param conda_channels:
	"""  # noqa: D400

	validated_requirements = []

	conda_packages = set()
	channels = DelimitedList(conda_channels)

	for channel in channels:
		for package in get_channel_listing(channel):
			conda_packages.add(package)

	for requirement in requirements:

		# Check alias_mapping first
		if requirement.name in alias_mapping:
			requirement.name = alias_mapping[requirement.name]
			validated_requirements.append(requirement)
			continue
		elif requirement.name in conda_packages:
			validated_requirements.append(requirement)
			continue

		matches = difflib.get_close_matches(requirement.name, conda_packages)
		for match in matches:
			if normalize(match) == normalize(requirement.name):
				requirement.name = match
				validated_requirements.append(requirement)
				break
		else:
			raise InvalidRequirement(
					f"Cannot satisfy the requirement {requirement.name!r} "
					f"from any of the channels: '{channels:', '}'."
					)

	return validated_requirements

	#  entry_points:
	#    - {{ import_name }} = {{ import_name }}:main
	#  skip_compile_pyc:
	#    - "*/templates/*.py"          # These should not (and cannot) be compiled


alias_mapping = {"ruamel-yaml": "ruamel.yaml"}
"""
Mapping of normalised names to names on Conda, if they differ for some reason.

.. versionadded:: 0.7.0
"""

# Really just due to https://github.com/conda-forge/ruamel.yaml-feedstock/issues/7
# TODO: might this be solved by the workaround for poetry?


def make_conda_description(summary: str, conda_channels: Iterable[str] = ()) -> str:
	"""
	Create a description for the Conda package from its summary and a list of channels required to install it.

	The description will look like::

		This is my fancy Conda package. Hope you like it 😉.


		Before installing please ensure you have added the following channels: conda-forge, bioconda

	if called as follows:

	.. code-block:: python

		make_conda_description(
			"This is my fancy Conda package. Hope you like it 😉.",
			["conda-forge", "bioconda"],
		)

	.. versionadded:: 0.8.0

	:param summary:
	:param conda_channels:
	"""

	conda_description = summary
	conda_channels = tuple(conda_channels)

	if conda_channels:
		conda_description += "\n\n\n"
		conda_description += "Before installing please ensure you have added the following channels: "
		conda_description += ", ".join(conda_channels)
		conda_description += '\n'

	return conda_description


if __name__ == "__main__":
	clear_cache()
