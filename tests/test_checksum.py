# stdlib
import os
import tempfile

# 3rd party
import pytest
import requests

# this package
from shippinglabel.checksum import check_sha256_hash, get_record_entry, get_sha256_hash


@pytest.fixture(scope="session")
def reference_file_a() -> tempfile.NamedTemporaryFile:
	with tempfile.NamedTemporaryFile() as tmpfile:
		url = "https://raw.githubusercontent.com/domdfcoding/shippinglabel/4f632ed497bffa0cb50d714477de0cf731d34dc6/shippinglabel.svg"
		tmpfile.write(requests.get(url).content)

		yield tmpfile


def test_get_sha256_hash(reference_file_a):
	hash = get_sha256_hash(reference_file_a.name)
	assert hash.hexdigest() == "83065efdedd381da9439b85a270ea9629f1ba46d9c7d7b1858bb70e54d5f664c"
	assert hash.digest(
	) == b"\x83\x06^\xfd\xed\xd3\x81\xda\x949\xb8Z'\x0e\xa9b\x9f\x1b\xa4m\x9c}{\x18X\xbbp\xe5M_fL"


def test_check_sha256_hash(reference_file_a):
	assert check_sha256_hash(
			reference_file_a.name, "83065efdedd381da9439b85a270ea9629f1ba46d9c7d7b1858bb70e54d5f664c"
			)
	assert check_sha256_hash(reference_file_a.name, get_sha256_hash(reference_file_a.name))


def test_get_record_entry(reference_file_a):
	entry = get_record_entry(reference_file_a.name, relative_to=os.path.dirname(reference_file_a.name))
	assert entry == f"{os.path.basename(reference_file_a.name)},sha256=sha256=gwZe_e3TgdqUObhaJw6pYp8bpG2cfXsYWLtw5U1fZkw,154911"
