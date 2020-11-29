# 3rd party
import pytest

# this package
from shippinglabel import no_dev_versions, normalize, normalize_keep_dot


@pytest.mark.parametrize(
		"name, expected",
		[
				("foo", "foo"),
				("bar", "bar"),
				("baz", "baz"),
				("baz-extensions", "baz-extensions"),
				("baz_extensions", "baz-extensions"),
				("baz.extensions", "baz-extensions"),
				]
		)
def test_normalize(name, expected):
	assert normalize(name) == expected


@pytest.mark.parametrize(
		"name, expected",
		[
				("foo", "foo"),
				("bar", "bar"),
				("baz", "baz"),
				("baz-extensions", "baz-extensions"),
				("baz_extensions", "baz-extensions"),
				("baz.extensions", "baz.extensions"),
				]
		)
def test_normalize_keep_dot(name, expected):
	assert normalize_keep_dot(name) == expected


def test_no_dev_versions():
	assert no_dev_versions(["3.6", "3.7", "3.8"]) == ["3.6", "3.7", "3.8"]
	assert no_dev_versions(["3.6", "3.7", "3.8", "3.9-dev"]) == ["3.6", "3.7", "3.8"]
	assert no_dev_versions(["3.6", "3.7", "3.8", "pypy3"]) == ["3.6", "3.7", "3.8", "pypy3"]
