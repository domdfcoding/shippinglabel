"""
shippinglabel._vendor is for vendoring dependencies to work around boostrapping issues upstream.
Files inside shippinglabel._vendor should be considered immutable and only updated to new versions from upstream.
"""

import importlib

try:
	trove_classifiers = importlib.import_module("trove_classifiers", "trove_classifiers")
except ImportError:
	from . import trove_classifiers as trove_classifiers  # noqa: F401
