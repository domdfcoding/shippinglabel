# stdlib
from typing import List

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from consolekit.terminal_colours import Fore

# this package
from shippinglabel.classifiers import classifiers_from_requirements, validate_classifiers
from shippinglabel.requirements import ComparableRequirement


class TestValidateClassifiers:

	def test_errors(self, capsys):
		validate_classifiers(["Foo :: Bar", "Foo :: Bar :: Baz", "Fuzzy :: Wuzzy :: Was :: A :: Bear"])
		captured = capsys.readouterr()

		stderr = captured.err.split('\n')
		assert stderr[0].endswith(f"Unknown Classifier 'Foo :: Bar'!{Fore.RESET}")
		assert stderr[1].endswith(f"Unknown Classifier 'Foo :: Bar :: Baz'!{Fore.RESET}")
		assert stderr[2].endswith(f"Unknown Classifier 'Fuzzy :: Wuzzy :: Was :: A :: Bear'!{Fore.RESET}")
		assert not captured.out

	def test_deprecated(self, capsys):
		validate_classifiers(["Natural Language :: Ukranian"])
		captured = capsys.readouterr()

		stderr = captured.err.split('\n')
		assert stderr[0].endswith(f"Classifier 'Natural Language :: Ukranian' is deprecated!{Fore.RESET}")
		assert not captured.out

	def test_valid(self, capsys):
		validate_classifiers(["Natural Language :: Ukrainian", "License :: OSI Approved"])
		captured = capsys.readouterr()
		assert not captured.out
		assert not captured.err


@pytest.mark.parametrize(
		"requirements",
		[
				pytest.param(["dash"], id="dash_upper"),
				pytest.param(["Dash"], id="dash_lower"),
				pytest.param(["jupyter"], id="jupyter_upper"),
				pytest.param(["Jupyter"], id="jupyter_lower"),
				pytest.param(["matplotlib"], id="matplotlib_upper"),
				pytest.param(["Matplotlib"], id="matplotlib_lower"),
				pytest.param(["pygame"], id="pygame"),
				pytest.param(["arcade"], id="arcade"),
				pytest.param(["flake8"], id="flake8"),
				pytest.param(["flake8-walrus"], id="flake8-walrus"),
				pytest.param(["flask"], id="flask"),
				pytest.param(["werkzeug"], id="werkzeug"),
				pytest.param(["click>=2.0,!=2.0.1"], id="click"),
				pytest.param(["pytest"], id="pytest"),
				pytest.param(["pytest-randomly"], id="pytest-randomly"),
				pytest.param(["tox"], id="tox"),
				pytest.param(["tox-envlist"], id="tox-envlist"),
				pytest.param(["Tox==1.2.3"], id="Tox==1.2.3"),
				pytest.param(["sphinx"], id="sphinx"),
				pytest.param(["sphinx-toolbox"], id="sphinx-toolbox"),
				pytest.param(["Sphinx>=1.3"], id="Sphinx>=1.3"),
				pytest.param(["jupyter", "matplotlib>=3"], id="jupyter_matplotlib"),
				pytest.param(["dash", "flask"], id="dash_flask"),
				pytest.param(["pytest", "flake8"], id="pytest_flake8"),
				pytest.param(["dulwich"], id="dulwich"),
				pytest.param(["gitpython"], id="gitpython"),
				pytest.param(["dulwich", "southwark"], id="dulwich_southwark"),
				]
		)
def test_classifiers_from_requirements(
		requirements: List[str],
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	requirements_list = [ComparableRequirement(req) for req in requirements]
	advanced_data_regression.check(list(classifiers_from_requirements(requirements_list)))
