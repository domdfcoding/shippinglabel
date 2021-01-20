#!/usr/bin/env python3
#
#  sdist.py
"""
Utilities for working with source distributions.

.. versionadded:: 0.9.0
"""
#
#  Copyright © 2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
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
#  Based on wheel-filename
#  https://github.com/jwodder/wheel-filename
#  Copyright (c) 2020 John Thorvald Wodder II
#  MIT Licensed

# stdlib
import os
import re
from typing import NamedTuple

# 3rd party
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from wheel_filename import InvalidFilenameError

__all__ = ["NotAnSdistError", "ParsedSdistFilename", "parse_sdist_filename"]


class NotAnSdistError(ValueError):
	"""
	Raised when something other than a source distribution is passed to :func:`~.parse_sdist_filename`.
	"""

	filename: str

	def __init__(self, filename: PathLike, msg: str = '') -> None:
		#: The invalid filename
		self.filename = str(filename)
		super().__init__(msg)

	def __str__(self) -> str:
		return super().__str__().format(repr(self.filename))


class ParsedSdistFilename(NamedTuple):
	"""
	Represents a parsed sdist filename.

	:param project: The name of the project.
	"""

	#: The name of the project. The case is the same as in the filename.
	project: str

	#: The version number of the project.
	version: str

	#: The file extension of the sdist, e.g. ``.tar.gz``.
	extension: str

	def __str__(self) -> str:
		return f'{self.project}-{self.version}{self.extension}'


SDIST_FILENAME_CRGX = re.compile(
		r'(?P<project>[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?(-stubs)?)'
		r'-(?P<version>[A-Za-z0-9_.!+]+)'
		r'(?P<extension>.tar.gz|.tar.bz2|.zip)'
		)


def parse_sdist_filename(filename: PathLike) -> ParsedSdistFilename:
	"""
	Parse a sdist filename into its components.

	:param filename: An sdist path or filename.

	:raises: :exc:`wheel_filename.InvalidFilenameError` if the filename is invalid.
	:raises: :exc:`shippinglabel.sdist.NotAnSdistError` if the file is not an sdist.
	"""

	filename = PathPlus(filename)

	if filename.suffix == ".whl":
		raise NotAnSdistError(filename, "{} is a wheel.")

	basename = os.path.basename(filename)

	m = SDIST_FILENAME_CRGX.fullmatch(basename)
	if not m:
		raise InvalidFilenameError(basename)

	return ParsedSdistFilename(**m.groupdict())
