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
from typing import Iterable, List

__all__ = ["no_dev_versions", "normalize", "normalize_keep_dot"]

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2020 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.5.1"
__email__: str = "dominic@davis-foster.co.uk"


def no_dev_versions(versions: Iterable[str]) -> List[str]:
	"""
	Returns the subset of ``versions`` which does not end with ``-dev``.

	:param versions:
	"""

	return [v for v in versions if not v.endswith("-dev")]


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

	:param name: The project name.

	.. versionadded:: 0.5.1
	"""

	return _normalize_keep_dot_pattern.sub('-', name).lower()
