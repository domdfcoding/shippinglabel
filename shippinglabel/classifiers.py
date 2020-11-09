#!/usr/bin/env python3
#
#  classifiers.py
"""
Utilities for working with trove classifiers.
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
from typing import Iterable

# 3rd party
import trove_classifiers  # type: ignore
from consolekit.terminal_colours import Fore
from domdf_python_tools.utils import stderr_writer

__all__ = ["validate_classifiers"]


def validate_classifiers(classifiers: Iterable[str]) -> bool:
	"""
	Validate a list of `trove classifiers <https://pypi.org/classifiers/>`_.

	:param classifiers:
	"""

	invalid_classifier = False

	for classifier in classifiers:
		if classifier in trove_classifiers.deprecated_classifiers:
			stderr_writer(Fore.YELLOW(f"Classifier '{classifier}' is deprecated!"))

		elif classifier not in trove_classifiers.classifiers:
			stderr_writer(Fore.RED(f"Unknown Classifier '{classifier}'!"))
			invalid_classifier = True

	return invalid_classifier
