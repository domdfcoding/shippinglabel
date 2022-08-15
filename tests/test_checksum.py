# stdlib
import os
import pathlib
import tempfile
import urllib.parse
from typing import Iterator

# 3rd party
import pytest
import requests
from domdf_python_tools.paths import PathPlus

# this package
from shippinglabel.checksum import check_sha256_hash, get_md5_hash, get_record_entry, get_sha256_hash
from shippinglabel.pypi import get_file_from_pypi, get_releases_with_digests


@pytest.fixture(scope="session")
def reference_file_a() -> Iterator[PathPlus]:
	with tempfile.TemporaryDirectory() as tmpdir:
		commit_sha = "4f632ed497bffa0cb50d714477de0cf731d34dc6"
		filename = "shippinglabel.svg"
		url = f"https://raw.githubusercontent.com/domdfcoding/shippinglabel/{commit_sha}/{filename}"

		tmpfile = PathPlus(tmpdir) / filename
		tmpfile.write_bytes(requests.get(url).content)

		yield tmpfile


def test_get_sha256_hash(reference_file_a: PathPlus):
	hash_ = get_sha256_hash(reference_file_a)
	assert hash_.hexdigest() == "83065efdedd381da9439b85a270ea9629f1ba46d9c7d7b1858bb70e54d5f664c"
	digest = b"\x83\x06^\xfd\xed\xd3\x81\xda\x949\xb8Z'\x0e\xa9b\x9f\x1b\xa4m\x9c}{\x18X\xbbp\xe5M_fL"
	assert hash_.digest() == digest


def test_get_sha256_hash_fp(reference_file_a: PathPlus):
	with open(reference_file_a, "rb") as fp:
		hash_ = get_sha256_hash(fp)

	assert hash_.hexdigest() == "83065efdedd381da9439b85a270ea9629f1ba46d9c7d7b1858bb70e54d5f664c"
	digest = b"\x83\x06^\xfd\xed\xd3\x81\xda\x949\xb8Z'\x0e\xa9b\x9f\x1b\xa4m\x9c}{\x18X\xbbp\xe5M_fL"
	assert hash_.digest() == digest


def test_get_md5_hash(reference_file_a: PathPlus):
	hash_ = get_md5_hash(reference_file_a)
	assert hash_.hexdigest() == "d7aadf6f1f20826aa227fa1bde281a41"
	assert hash_.digest() == b"\xd7\xaa\xdfo\x1f \x82j\xa2'\xfa\x1b\xde(\x1aA"


def test_get_md5_hash_fp(reference_file_a: PathPlus):
	with open(reference_file_a, "rb") as fp:
		hash_ = get_md5_hash(fp)

	assert hash_.hexdigest() == "d7aadf6f1f20826aa227fa1bde281a41"
	assert hash_.digest() == b"\xd7\xaa\xdfo\x1f \x82j\xa2'\xfa\x1b\xde(\x1aA"


def test_check_sha256_hash(reference_file_a: PathPlus):
	assert check_sha256_hash(
			reference_file_a,
			"83065efdedd381da9439b85a270ea9629f1ba46d9c7d7b1858bb70e54d5f664c",
			)
	assert check_sha256_hash(reference_file_a, get_sha256_hash(reference_file_a))


def test_check_sha256_hash_fp(reference_file_a: PathPlus):
	with open(reference_file_a, "rb") as fp:
		assert check_sha256_hash(
				fp,
				"83065efdedd381da9439b85a270ea9629f1ba46d9c7d7b1858bb70e54d5f664c",
				)

	with open(reference_file_a, "rb") as fp:
		assert check_sha256_hash(fp, get_sha256_hash(reference_file_a))


def test_get_record_entry(reference_file_a: PathPlus):
	entry = get_record_entry(reference_file_a, relative_to=reference_file_a.parent)
	assert entry == f"{os.path.basename(reference_file_a)},sha256=gwZe_e3TgdqUObhaJw6pYp8bpG2cfXsYWLtw5U1fZkw,154911"


def test_checksum_from_pypi(tmp_pathplus: PathPlus):
	for idx, (release, files) in enumerate(get_releases_with_digests("shippinglabel").items()):
		for file in files:
			get_file_from_pypi(file["url"], tmp_pathplus)
			filename = pathlib.PurePosixPath(urllib.parse.urlparse(file["url"]).path).name
			check_sha256_hash(tmp_pathplus / filename, file["digest"])

		if idx == 3:
			return
