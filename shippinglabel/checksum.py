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
import io
from base64 import urlsafe_b64encode
from hashlib import md5, sha256
from typing import IO, TYPE_CHECKING, Callable, Optional, Union, cast

# 3rd party
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike

if TYPE_CHECKING:
	# stdlib
	from hashlib import _Hash
else:
	try:
		# stdlib
		from _hashlib import HASH as _Hash
	except ImportError:  # pragma: no cover
		try:
			# stdlib
			from _hashlib import Hash as _Hash
		except ImportError:
			pass

__all__ = ["get_sha256_hash", "check_sha256_hash", "get_md5_hash", "get_record_entry"]

_HashType = type(sha256())


def _get_hash(fp: IO[bytes], hash_type: Callable, blocksize: int = 1 << 20) -> "_Hash":
	"""
	Returns the SHA256 hash object for the given file object.

	:param fp:
	:param hash_type:
	:param blocksize: The blocksize to read the file with.

	:rtype: :mod:`hashlib.sha256() <hashlib>`
	"""

	hash_obj = hash_type()

	fb = fp.read(blocksize)
	while len(fb):  # pylint: disable=len-as-condition
		hash_obj.update(fb)
		fb = fp.read(blocksize)

	return hash_obj


def get_sha256_hash(
		filename: Union[PathLike, IO[bytes]],
		blocksize: int = 1 << 20,
		) -> "_Hash":
	"""
	Returns the SHA256 hash object for the given file.

	.. versionadded:: 0.6.0

	:param filename:
	:param blocksize: The blocksize to read the file with.

	:rtype: :mod:`hashlib.sha256() <hashlib>`

	.. versionchanged:: 0.16.0  Added support for already open file objects.
	"""

	if isinstance(filename, io.BufferedIOBase):
		return _get_hash(filename, sha256, blocksize)

	with open(cast(PathLike, filename), "rb") as f:
		return _get_hash(f, sha256, blocksize)


def get_md5_hash(
		filename: Union[PathLike, IO[bytes]],
		blocksize: int = 1 << 20,
		) -> "_Hash":
	"""
	Returns the md5 hash object for the given file.

	.. versionadded:: 0.15.0

	:param filename:
	:param blocksize: The blocksize to read the file with.

	:rtype: :mod:`hashlib.md5() <hashlib>`

	.. versionchanged:: 0.16.0  Added support for already open file objects.
	"""

	if isinstance(filename, io.BufferedIOBase):
		return _get_hash(filename, md5, blocksize)

	with open(cast(PathLike, filename), "rb") as f:
		return _get_hash(f, md5, blocksize)


def check_sha256_hash(
		filename: Union[PathLike, IO[bytes]],
		hash: Union["_Hash", str],  # noqa: A002  # pylint: disable=redefined-builtin
		blocksize: int = 1 << 20,
		) -> bool:
	r"""
	Returns whether the SHA256 hash for the file matches ``hash``.

	.. versionadded:: 0.6.0

	:param filename:
	:param hash: If a string, the hexdigest of the hash.
	:type hash: :py:obj:`~typing.Union`\[:mod:`hashlib.sha256() <hashlib>`, :class:`str`\]
	:param blocksize: The blocksize to read the file with.

	:rtype:

	.. versionchanged:: 0.16.0  Added support for already open file objects.
	.. latex:clearpage::
	"""

	if isinstance(hash, _HashType):
		hash = hash.hexdigest()  # noqa: A001  # pylint: disable=redefined-builtin

	return hash == get_sha256_hash(filename, blocksize).hexdigest()


def get_record_entry(filename: PathLike, blocksize: int = 1 << 20, relative_to: Optional[PathLike] = None) -> str:
	"""
	Constructs a :pep:`376` ``RECORD`` entry for the file.

	.. versionadded:: 0.6.0

	:param filename:
	:param blocksize: The blocksize to read the file with.
	:param relative_to:
	"""

	sha256_hash = get_sha256_hash(filename, blocksize).digest()
	digest = "sha256=" + urlsafe_b64encode(sha256_hash).decode("latin1").rstrip('=')

	filename = PathPlus(filename)

	length = filename.stat().st_size

	if relative_to:
		filename = filename.relative_to(relative_to)

	return ','.join([filename.as_posix(), digest, str(length)])
