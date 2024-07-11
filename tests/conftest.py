# stdlib
from typing import Callable, Type, TypeVar

# 3rd party
from apeye.url import URL
from betamax import Betamax  # type: ignore
from domdf_python_tools.paths import PathPlus
from packaging.tags import Tag
from pytest_regressions.data_regression import RegressionYamlDumper

pytest_plugins = ("coincidence", )

_C = TypeVar("_C", bound=Callable)

with Betamax.configure() as config:
	config.cassette_library_dir = PathPlus(__file__).parent / "cassettes"


def _representer_for(*data_type: Type):  # noqa: MAN002

	def deco(representer_fn: _C) -> _C:
		for dtype in data_type:
			RegressionYamlDumper.add_custom_yaml_representer(dtype, representer_fn)

		return representer_fn

	return deco


@_representer_for(URL, Tag)
def _represent_sequences(dumper: RegressionYamlDumper, data):  # noqa: MAN001,MAN002
	return dumper.represent_str(str(data))
