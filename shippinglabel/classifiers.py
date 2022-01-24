#!/usr/bin/env python3
#
#  classifiers.py
"""
Utilities for working with trove classifiers.
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

# stdlib
from collections import defaultdict
from typing import Collection, Iterable, Iterator

# 3rd party
from domdf_python_tools.utils import stderr_writer

# this package
from shippinglabel import normalize
from shippinglabel._vendor import trove_classifiers
from shippinglabel.requirements import ComparableRequirement

__all__ = ["validate_classifiers", "classifiers_from_requirements"]


def validate_classifiers(classifiers: Iterable[str]) -> bool:
	"""
	Validate a list of `trove classifiers <https://pypi.org/classifiers/>`_.

	:param classifiers:
	"""

	invalid_classifier = False

	for classifier in classifiers:
		if classifier in trove_classifiers.deprecated_classifiers:
			stderr_writer(f"\x1b[33mClassifier '{classifier}' is deprecated!\x1b[39m")

		elif classifier not in trove_classifiers.classifiers:
			stderr_writer(f"'\x1b[31m'Unknown Classifier '{classifier}'!\x1b[39m")
			invalid_classifier = True

	return invalid_classifier


def classifiers_from_requirements(requirements: Collection[ComparableRequirement]) -> Iterator[str]:
	"""
	Returns an iterator over suggested trove classifiers based on the given requirements.

	.. versionadded:: 0.5.0

	:param requirements:
	"""

	requirement_names = []
	frameworks = defaultdict(bool)

	for _requirement in requirements:
		req = normalize(_requirement.name)
		requirement_names.append(req)

		if req.startswith("flake8"):
			frameworks["flake8"] = True
		elif req.startswith("flask"):
			frameworks["flask"] = True
		elif req.startswith("pytest"):
			frameworks["pytest"] = True
		elif req.startswith("tox"):
			frameworks["tox"] = True
		elif req.startswith("sphinx"):
			frameworks["sphinx"] = True
		elif req in {"click", "typer", "consolekit"}:
			frameworks["console"] = True
		elif req in {"gitpython", "dulwich", "southwark"}:
			frameworks["git"] = True

	if "dash" in requirement_names:
		yield "Framework :: Dash"
	if "jupyter" in requirement_names:
		yield "Framework :: Jupyter"
	if "matplotlib" in requirement_names:
		yield "Framework :: Matplotlib"
	if "pygame" in requirement_names:
		yield "Topic :: Software Development :: Libraries :: pygame"
		yield "Topic :: Games/Entertainment"
	if "arcade" in requirement_names:
		yield "Topic :: Games/Entertainment"
	if "werkzeug" in requirement_names:
		yield "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"

	if frameworks["flake8"]:
		yield "Framework :: Flake8"
		yield "Intended Audience :: Developers"

	if frameworks["flask"]:
		yield "Framework :: Flask"
		yield "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
		yield "Topic :: Internet :: WWW/HTTP :: Dynamic Content"

	if frameworks["console"]:
		yield "Environment :: Console"

	if frameworks["pytest"]:
		yield "Framework :: Pytest"
		yield "Topic :: Software Development :: Quality Assurance"
		yield "Topic :: Software Development :: Testing"
		yield "Topic :: Software Development :: Testing :: Unit"
		yield "Intended Audience :: Developers"

	if frameworks["tox"]:
		yield "Framework :: tox"
		yield "Topic :: Software Development :: Quality Assurance"
		yield "Topic :: Software Development :: Testing"
		yield "Topic :: Software Development :: Testing :: Unit"
		yield "Intended Audience :: Developers"

	if frameworks["sphinx"]:
		yield "Framework :: Sphinx :: Extension"
		# TODO: yield "Framework :: Sphinx :: Theme"
		yield "Topic :: Documentation"
		yield "Topic :: Documentation :: Sphinx"
		yield "Topic :: Software Development :: Documentation"
		yield "Intended Audience :: Developers"

	if frameworks["git"]:
		yield "Topic :: Software Development :: Version Control :: Git"
