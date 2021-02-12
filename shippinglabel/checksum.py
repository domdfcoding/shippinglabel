#!/usr/bin/env python3
#
#  checksum.py
"""
Utilities for creating and checking file sha256 checksums.

.. versionadded:: 0.6.0
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
from base64 import urlsafe_b64encode
from hashlib import sha256
from typing import TYPE_CHECKING, Optional, Union

# 3rd party
from domdf_python_tools.compat import PYPY
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike

if TYPE_CHECKING:
	# stdlib
	from hashlib import _Hash
elif PYPY:
	# stdlib
	from _hashlib import Hash as _Hash
else:
	# stdlib
	from _hashlib import HASH as _Hash

__all__ = ["check_sha256_hash", "get_record_entry", "get_sha256_hash"]

_HashType = type(sha256())


def get_sha256_hash(filename: PathLike, blocksize: int = 1 << 20) -> "_Hash":
	"""
	Returns the sha256 hash object for the given file.

	.. versionadded:: 0.6.0

	:param filename:
	:param blocksize: The blocksize to read the file with.

	:rtype: :mod:`hashlib.sha256() <hashlib>`
	"""

	sha256_hash = sha256()

	with open(filename, "rb") as f:
		fb = f.read(blocksize)
		while len(fb):
			sha256_hash.update(fb)
			fb = f.read(blocksize)

	return sha256_hash


def check_sha256_hash(
		filename: PathLike,
		hash: Union["_Hash", str],  # noqa: A002  # pylint: disable=redefined-builtin
		blocksize: int = 1 << 20,
		) -> bool:
	r"""
	Returns whether the sha256 hash for the file matches ``hash``.

	.. versionadded:: 0.6.0

	:param filename:
	:param hash:
	:type hash: :py:obj:`Union`\[:mod:`hashlib.sha256() <hashlib>`, :class:`str`\]
	:param blocksize: The blocksize to read the file with.
	"""

	if isinstance(hash, _HashType):
		hash = hash.hexdigest()  # noqa: A001

	return hash == get_sha256_hash(filename, blocksize).hexdigest()


def get_record_entry(filename: PathLike, blocksize: int = 1 << 20, relative_to: Optional[PathLike] = None) -> str:
	"""
	Constructs an entry for the file in a :pep:`376` ``RECORD`` file.

	.. versionadded:: 0.6.0

	:param filename:
	:param blocksize: The blocksize to read the file with.
	:param relative_to:
	"""

	hash = get_sha256_hash(filename, blocksize).digest()  # noqa: A001
	digest = "sha256=" + urlsafe_b64encode(hash).decode("latin1").rstrip('=')

	filename = PathPlus(filename)

	length = filename.stat().st_size

	if relative_to:
		filename = filename.relative_to(relative_to)

	return ','.join([filename.as_posix(), digest, str(length)])
