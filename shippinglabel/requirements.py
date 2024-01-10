#!/usr/bin/env python3
#
#  requirements.py
"""
Utilities for working with :pep:`508` requirements.
"""
#
#  Copyright © 2020-2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
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
#  check_dependencies based on https://stackoverflow.com/a/29044693/3092681
#  Copyright © 2015 TehTechGuy
#  Licensed under CC-BY-SA
#

# stdlib
import copy
import warnings
from abc import ABC
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union, cast, overload

# 3rd party
import deprecation_alias
import dist_meta
import dom_toml
from domdf_python_tools.doctools import prettify_docstrings
from domdf_python_tools.iterative import natmax, natmin
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import DelimitedList, StringList
from domdf_python_tools.typing import PathLike
from packaging.markers import default_environment
from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import BaseSpecifier, Specifier, SpecifierSet
from typing_extensions import Literal

# this package
from shippinglabel import __version__, normalize

__all__ = [
		"ComparableRequirement",
		"resolve_specifiers",
		"combine_requirements",
		"read_requirements",
		"RequirementsManager",
		"list_requirements",
		"check_dependencies",
		"parse_requirements",
		"parse_pyproject_dependencies",
		"parse_pyproject_extras",
		]

operator_symbols = ("<=", '<', "!=", "==", ">=", '>', "~=", "===")
_Requirement = Union[str, Requirement]


@prettify_docstrings
class ComparableRequirement(Requirement):
	"""
	Represents a :pep:`508` requirement.

	Can be compared to other requirements.
	A list of :class:`~.ComparableRequirement` objects can be sorted alphabetically.
	"""

	@staticmethod
	def _check_equal_not_none(left: Optional[Any], right: Optional[Any]) -> bool:
		if not left or not right:
			return True
		else:
			return left == right

	@staticmethod
	def _check_marker_equality(left: Optional[Any], right: Optional[Any]) -> bool:
		if left is not None and right is not None:
			for left_mark, right_mark in zip(left._markers, right._markers):
				if str(left_mark) != str(right_mark):
					return False
		return True

	def __eq__(self, other) -> bool:  # noqa: MAN001

		if isinstance(other, str):
			try:
				other = Requirement(other)
			except InvalidRequirement:
				return NotImplemented

			return self == other

		elif isinstance(other, Requirement):
			return all((
					self._check_equal_not_none(self.name, other.name),
					self._check_equal_not_none(self.url, other.url),
					self._check_equal_not_none(self.extras, other.extras),
					self._check_equal_not_none(self.specifier, other.specifier),
					self._check_marker_equality(self.marker, other.marker),
					))
		else:  # pragma: no cover
			return NotImplemented

	def __lt__(self, other) -> bool:  # noqa: MAN001
		if isinstance(other, Requirement):
			if self.name != other.name:
				return self.name < other.name
			else:
				if str(self.specifier or '') != str(other.specifier or ''):
					return str(self.specifier or '') > str(other.specifier or '')
				else:
					return str(self.marker or '') > str(other.marker or '')

		elif isinstance(other, str):
			return self.name < other
		else:  # pragma: no cover
			return NotImplemented

	def __le__(self, other) -> bool:  # noqa: MAN001
		if not isinstance(other, (Requirement, str)):  # pragma: no cover
			return NotImplemented
		if self < other or self == other:
			return True
		return False

	def __ge__(self, other) -> bool:  # noqa: MAN001
		if not isinstance(other, (Requirement, str)):  # pragma: no cover
			return NotImplemented
		if self > other or self == other:
			return True
		return False

	def __gt__(self, other) -> bool:  # noqa: MAN001
		if isinstance(other, Requirement):
			if self.name != other.name:
				return self.name > other.name
			else:
				if str(self.specifier or '') != str(other.specifier or ''):
					return str(self.specifier or '') < str(other.specifier or '')
				else:
					return str(self.marker or '') < str(other.marker or '')

		elif isinstance(other, str):
			return self.name > other
		else:  # pragma: no cover
			return NotImplemented

	def __hash__(self) -> int:
		return hash((
				self.name or '',
				self.url or '',
				str(self.specifier) or '',
				str(self.marker) or '',
				*(self.extras or ()),
				))


class _OperatorLookup(Dict[str, DelimitedList[Specifier]]):

	def __setitem__(self, key: str, value: Any) -> None:
		if key not in operator_symbols:
			raise KeyError(f"Invalid operator symbol {key!r}")

		if isinstance(value, DelimitedList):
			super().__setitem__(key, value)
		else:
			super().__setitem__(key, DelimitedList(value))

	def __getitem__(self, item: str) -> DelimitedList[Specifier]:
		if item not in self and item in operator_symbols:
			self[item] = DelimitedList()

		return super().__getitem__(item)


def resolve_specifiers(specifiers: Iterable[BaseSpecifier]) -> SpecifierSet:
	r"""
	Resolve duplicated and overlapping requirement specifiers.

	:param specifiers:
	:type specifiers: :class:`~typing.Iterable`\[:class:`~.packaging.specifiers.Specifier`]
	"""

	operator_lookup = _OperatorLookup()
	spec: Specifier

	for spec in cast(Iterable[Specifier], specifiers):
		if spec.operator in operator_symbols:
			operator_lookup[spec.operator].append(spec)

	if operator_lookup["<="]:
		operator_lookup["<="] = [Specifier(f"<={natmin(spec.version for spec in operator_lookup['<='])}")]

	if operator_lookup['<']:
		operator_lookup['<'] = [Specifier(f"<{natmin(spec.version for spec in operator_lookup['<'])}")]

	if operator_lookup[">="]:
		operator_lookup[">="] = [Specifier(f">={natmax(spec.version for spec in operator_lookup['>='])}")]

	if operator_lookup['>']:
		operator_lookup['>'] = [Specifier(f">{natmax(spec.version for spec in operator_lookup['>'])}")]

	# merge e.g. >1.2.3 and >=1.2.2 into >1.2.3
	if operator_lookup[">="] and operator_lookup['>']:
		gt_version = operator_lookup['>'][0].version
		ge_version = operator_lookup[">="][0].version

		if gt_version > ge_version:
			del operator_lookup[">="]

	# merge e.g. >=1.2.2 and ==1.2.3 into ==1.2.3
	if operator_lookup[">="] and operator_lookup["=="]:
		ge_version = operator_lookup[">="][0].version

		if any([eq_version.version >= ge_version for eq_version in operator_lookup["=="]]):
			del operator_lookup[">="]

	# merge e.g. <=1.2.3 and <1.2.2 into <1.2.2
	if operator_lookup["<="] and operator_lookup['<']:
		lt_version = operator_lookup['<'][0].version
		le_version = operator_lookup["<="][0].version

		if lt_version < le_version:
			del operator_lookup["<="]

	# merge e.g. <=1.2.3 and ==1.2.2 into ==1.2.2
	if operator_lookup["<="] and operator_lookup["=="]:
		le_version = operator_lookup["<="][0].version

		if any([eq_version.version <= le_version for eq_version in operator_lookup["=="]]):
			del operator_lookup["<="]

	specifier_set = SpecifierSet()

	if operator_lookup["<="]:
		specifier_set &= SpecifierSet(f"{operator_lookup['<=']:,}")

	if operator_lookup['<']:
		specifier_set &= SpecifierSet(f"{operator_lookup['<']:,}")

	for spec in operator_lookup["!="]:
		specifier_set &= SpecifierSet(f"!={spec.version}")

	for spec in operator_lookup["=="]:
		specifier_set &= SpecifierSet(f"=={spec.version}")

	if operator_lookup[">="]:
		specifier_set &= SpecifierSet(f"{operator_lookup['>=']:,}")

	if operator_lookup['>']:
		specifier_set &= SpecifierSet(f"{operator_lookup['>']:,}")

	for spec in operator_lookup["~="]:
		specifier_set &= SpecifierSet(f"~={spec.version}")

	for spec in operator_lookup["==="]:
		specifier_set &= SpecifierSet(f"==={spec.version}")

	return specifier_set


def combine_requirements(
		requirement: Union[_Requirement, Iterable[_Requirement]],
		*requirements: _Requirement,
		normalize_func: Callable[[str], str] = normalize
		) -> List[ComparableRequirement]:
	"""
	Combine duplicated requirements in a list.

	.. versionchanged:: 0.2.1  Added the ``normalize_func`` keyword-only argument.
	.. versionchanged:: 0.3.1  Requirements are no longer combined if their markers differ.

	:param requirement: A single requirement, or an iterable of requirements.
	:param requirements: Additional requirements.
	:param normalize_func: Function to use to normalize the names of requirements.
	"""

	if isinstance(requirement, Iterable):
		all_requirements = [*requirement, *requirements]
	else:
		all_requirements = [requirement, *requirements]

	merged_requirements: List[ComparableRequirement] = []

	for req in all_requirements:
		if not isinstance(req, ComparableRequirement):
			req = ComparableRequirement(str(req))

		req.name = normalize_func(req.name)
		_denormalize_ruamel(req)

		if req.name in merged_requirements:
			possible_other_req = [x for x in merged_requirements if x.name == req.name]
			for other_req in possible_other_req:
				if str(req.marker) == str(other_req.marker):
					other_req.specifier &= req.specifier
					other_req.extras &= req.extras
					other_req.specifier = resolve_specifiers(other_req.specifier)
					break
			else:
				merged_requirements.append(copy.deepcopy(req))
		else:
			merged_requirements.append(copy.deepcopy(req))

	return merged_requirements


_read_requirements_ret_invalid = Tuple[Set[ComparableRequirement], List[str], List[str]]
_read_requirements_ret_valid = Tuple[Set[ComparableRequirement], List[str]]
_read_requirements_ret = Union[_read_requirements_ret_invalid, _read_requirements_ret_valid]


@overload
def read_requirements(
		req_file: PathLike,
		include_invalid: Literal[True],
		*,
		normalize_func: Callable[[str], str] = ...
		) -> _read_requirements_ret_invalid: ...


@overload
def read_requirements(
		req_file: PathLike,
		include_invalid: Literal[False] = ...,
		*,
		normalize_func: Callable[[str], str] = ...
		) -> _read_requirements_ret_valid: ...


def read_requirements(
		req_file: PathLike,
		include_invalid: bool = False,
		*,
		normalize_func: Callable[[str], str] = normalize
		) -> _read_requirements_ret:
	"""
	Reads :pep:`508` requirements from the given file.

	.. versionchanged:: 0.2.0 Added the ``include_invalid`` option.
	.. versionchanged:: 0.2.1 Added the ``normalize_func`` keyword-only argument.

	:param req_file:
	:param include_invalid: If :py:obj:`True`, include invalid lines as the third element of the tuple.
	:param normalize_func: Function to use to normalize the names of requirements.

	:return: The requirements, and a list of commented lines.
	"""

	requirements = PathPlus(req_file).read_lines()

	if include_invalid:
		return parse_requirements(requirements, include_invalid=True, normalize_func=normalize_func)

	else:
		return parse_requirements(requirements, include_invalid=False, normalize_func=normalize_func)


@overload
def parse_requirements(
		requirements: Iterable[str],
		*,
		include_invalid: Literal[True],
		normalize_func: Callable[[str], str] = ...
		) -> _read_requirements_ret_invalid: ...


@overload
def parse_requirements(
		requirements: Iterable[str],
		*,
		include_invalid: Literal[False] = ...,
		normalize_func: Callable[[str], str] = ...
		) -> _read_requirements_ret_valid: ...


def parse_requirements(
		requirements: Iterable[str],
		*,
		include_invalid: bool = False,
		normalize_func: Callable[[str], str] = normalize
		) -> _read_requirements_ret:
	"""
	Parse the given strings as :pep:`508` requirements.

	.. versionadded:: 0.10.0

	:param requirements:
	:param include_invalid: If :py:obj:`True`, include invalid lines as the third element of the tuple.
	:param normalize_func: Function to use to normalize the names of requirements.

	:return: The requirements, and a list of commented lines.

	.. latex:clearpage::
	"""

	comments = []
	invalid_lines: List[str] = []
	parsed_requirements: Set[ComparableRequirement] = set()

	for line in requirements:
		if line.lstrip().startswith('#'):
			comments.append(line)
		elif line:
			try:
				req = ComparableRequirement(line)
				req.name = normalize_func(req.name)
				_denormalize_ruamel(req)
				parsed_requirements.add(req)
			except InvalidRequirement:
				invalid_lines.append(line)

	if include_invalid:
		return parsed_requirements, comments, invalid_lines
	else:
		for line in invalid_lines:
			warnings.warn(f"Ignored invalid requirement {line!r}")

		return parsed_requirements, comments


class RequirementsManager(ABC):
	"""
	Abstract base class for managing requirements files.

	When invoked with run, the methods are called in the following order:

	#. :meth:`~.compile_target_requirements`
	#. :meth:`~.merge_requirements`
	#. :meth:`~.remove_library_requirements`
	#. :meth:`~.write_requirements`

	:param repo_path: Path to the repository root.

	.. autosummary-widths:: 4/10
	"""

	target_requirements: Set[ComparableRequirement]
	"""
	The static target requirements

	.. versionchanged:: 0.4.0  Previously this was a set of :class:`packaging.requirements.Requirement`.
	"""

	#: The path of the requirements file, relative to the repository root.
	filename: PathLike

	def __init__(self, repo_path: PathLike):
		self.repo_path = PathPlus(repo_path)
		self.req_file = self.prep_req_file()
		self.target_requirements = set(self.target_requirements)

	def prep_req_file(self) -> PathPlus:
		"""
		Create the requirements file if necessary, and in any case return its filename.
		"""

		req_file = PathPlus(self.repo_path / self.filename)
		req_file.parent.maybe_make(parents=True)

		if not req_file.is_file():
			req_file.touch()

		return req_file

	def compile_target_requirements(self) -> None:
		"""
		Add and remove requirements depending on the configuration
		by modifying the ``target_requirements`` attribute.

		This method may not return anything.
		"""  # noqa: D400

	def normalize(self, name: str) -> str:
		"""
		Normalize the given name for PyPI et al.

		.. versionadded:: 0.2.1

		:param name: The project name.
		"""

		return normalize(name)

	def get_target_requirement_names(self) -> Set[str]:
		"""
		Returns a list of normalized names for the target requirements,
		including any added by ``compile_target_requirements``.
		"""  # noqa: D400

		names = set()
		for req in self.target_requirements:
			req.name = self.normalize(req.name)
			names.add(req.name)
		return names

	def merge_requirements(self) -> List[str]:
		"""
		Merge requirements already in the file with the target requirements.

		Requirements may be added, changed or removed at this stage
		by modifying the ``target_requirements`` attribute.

		:return: List of commented lines.
		"""

		current_requirements, comments = read_requirements(self.req_file)
		self.target_requirements = set(combine_requirements(*current_requirements, *self.target_requirements))
		return comments

	def remove_library_requirements(self) -> None:
		"""
		Remove requirements given in the library's ``requirements.txt`` file.

		This method may not return anything.
		"""

		lib_requirements, _ = read_requirements(self.repo_path / "requirements.txt")
		lib_requirements_names_extras = {normalize(r.name): r.extras for r in lib_requirements if not r.marker}

		non_library_requirements = set()

		for req in self.target_requirements:
			if req.name in lib_requirements_names_extras:
				if req.extras != lib_requirements_names_extras[req.name]:
					non_library_requirements.add(req)
				if req.marker:
					non_library_requirements.add(req)
			else:
				non_library_requirements.add(req)

		self.target_requirements = non_library_requirements

	def write_requirements(self, comments: List[str]) -> None:
		"""
		Write the list of requirements to the file.

		:param comments: List of commented lines.

		This method may not return anything.
		"""

		buf = StringList(comments)

		for req in sorted(self.target_requirements):
			buf.append(str(req))

		self.req_file.write_lines(buf)

	def run(self) -> PathPlus:
		"""
		Update the list of requirements and return the name of the requirements file.
		"""

		self.compile_target_requirements()
		comments = self.merge_requirements()
		self.remove_library_requirements()
		self.write_requirements(comments)

		return self.req_file


def marker_environment(extra: str) -> Dict[str, str]:
	env: Dict[str, str] = default_environment()
	env["extra"] = extra
	return env


def list_requirements(
		name: str,
		depth: int = 1,
		path: Optional[Iterable[PathLike]] = None,
		) -> Iterator[Union[str, List[str], List[Union[str, List]]]]:
	"""
	Returns an iterator over the requirements of the given library, and the requirements of those requirements.

	The iterator is structured as follows::

		[
			<requirement a>,
			[
				<requirement 1 of requirement a>,
				<requirement 2 of requirement a>,
				[<requirements of requirement 2>, ...],
				<requirement 3 of requirement a>,
			],
			<requirement b>,
		]

	:param name:
	:param depth:
	:param path: The directories entries to search for distributions in.
		This can be used to search in a different (virtual) environment.
	:default path: :py:data:`sys.path`

	.. versionchanged:: 0.8.2  The requirements are now sorted alphabetically.
	.. versionchanged:: 1.7.0  Added the ``path`` argument.
	"""

	req = ComparableRequirement(name)

	try:
		distro = dist_meta.distributions.get_distribution(req.name, path=path)
	except dist_meta.distributions.DistributionNotFoundError:
		return

	raw_deps = distro.get_metadata().get_all("Requires-Dist") or []

	for requirement in [ComparableRequirement(r) for r in sorted(raw_deps)]:
		if requirement.marker:
			if req.extras:
				extras = list(req.extras)[0]
			else:
				extras = ''

			if not requirement.marker.evaluate(marker_environment(extras)):
				continue

		if depth:
			yield str(requirement)

		if depth != 0:
			deps = list(list_requirements(str(requirement), depth=depth - 1, path=path))
			if deps:
				yield deps


@deprecation_alias.deprecated(deprecated_in="1.6.0", removed_in="2.0", current_version=__version__)
def check_dependencies(dependencies: Iterable[str], prt: bool = True) -> List[str]:
	"""
	Check whether one or more dependencies are available to be imported.

	:param dependencies: The list of dependencies to check the availability of.
	:param prt: Whether the status should be printed to the terminal.

	:return: A list of any missing modules.
	"""

	# stdlib
	from pkgutil import iter_modules

	modules = {x[1] for x in iter_modules()}
	missing_modules = []

	for requirement in dependencies:
		if requirement not in modules:
			missing_modules.append(requirement)

	if prt:
		if len(missing_modules) == 0:
			print("All modules installed")
		else:
			print("The following modules are missing:")
			print(missing_modules)
			print("Please check the documentation.")
		print('')

	return missing_modules


def parse_pyproject_dependencies(
		pyproject_file: PathLike,
		flavour: Literal["pep621", "flit", "auto"] = "auto",
		*,
		normalize_func: Callable[[str], str] = normalize
		) -> Set[ComparableRequirement]:
	"""
	Parse the project's dependencies from its ``pyproject.toml`` file.

	.. versionadded:: 0.10.0

	:param pyproject_file:
	:param flavour: Either ``'pep621'`` to parse from the :pep:`621` ``dependencies`` table,
		or ``'flit'`` to parse the ``requires`` key in ``tool.flit.metadata`.
		The string ``'auto`` will use ``'pep621'`` if available, otherwise try ``'flit'``.
	:param normalize_func: Function to use to normalize the names of dependencies.

	If no dependencies are defined an empty set is returned.

	:rtype:

	.. latex:clearpage::
	"""

	config = dom_toml.load(pyproject_file)

	dependencies = []

	if flavour == "auto":
		if "project" in config:
			flavour = "pep621"
		elif "flit" in config.get("tool", {}):
			flavour = "flit"

	if flavour == "pep621":
		dependencies = config.get("project", {}).get("dependencies", [])
	elif flavour == "flit":
		dependencies = config.get("tool", {}).get("flit", {}).get("metadata", {}).get("requires", [])

	return parse_requirements(dependencies, include_invalid=True, normalize_func=normalize_func)[0]


def parse_pyproject_extras(
		pyproject_file: PathLike,
		flavour: Literal["pep621", "flit", "auto"] = "auto",
		*,
		normalize_func: Callable[[str], str] = normalize
		) -> Dict[str, Set[ComparableRequirement]]:
	"""
	Parse the project's extra dependencies from its ``pyproject.toml`` file.

	.. versionadded:: 0.10.0

	:param pyproject_file:
	:param flavour: Either ``'pep621'`` to parse from the :pep:`621` ``dependencies`` table,
		or ``'flit'`` to parse the ``requires-extra`` key in ``tool.flit.metadata`.
		The string ``'auto`` will use ``'pep621'`` if available, otherwise try ``'flit'``.
	:param normalize_func: Function to use to normalize the names of dependencies.

	If no extra dependencies are defined an empty dictionary is returned.
	"""

	config = dom_toml.load(pyproject_file)

	dependencies = {}

	if flavour == "auto":
		if "project" in config:
			flavour = "pep621"
		elif "flit" in config.get("tool", {}):
			flavour = "flit"

	if flavour == "pep621":
		dependencies = config.get("project", {}).get("optional-dependencies", {})
	elif flavour == "flit":
		dependencies = config.get("tool", {}).get("flit", {}).get("metadata", {}).get("requires-extra", {})

	return {
			k: parse_requirements(v, include_invalid=True, normalize_func=normalize_func)[0]
			for k,
			v in dependencies.items()
			}


def _denormalize_ruamel(req: Requirement) -> None:
	if req.name in {"ruamel-yaml", "ruamel_yaml"}:
		# Special case to work around issue with Poetry
		req.name = "ruamel.yaml"
