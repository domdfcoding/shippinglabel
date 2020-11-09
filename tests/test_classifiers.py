# 3rd party
from consolekit.terminal_colours import Fore

# this package
from packing_tape.classifiers import validate_classifiers


class TestValidateClassifiers:

	def test_errors(self, capsys):
		validate_classifiers(["Foo :: Bar", "Foo :: Bar :: Baz", "Fuzzy :: Wuzzy :: Was :: A :: Bear"])
		captured = capsys.readouterr()

		stderr = captured.err.split("\n")
		assert stderr[0].endswith(f"Unknown Classifier 'Foo :: Bar'!{Fore.RESET}")
		assert stderr[1].endswith(f"Unknown Classifier 'Foo :: Bar :: Baz'!{Fore.RESET}")
		assert stderr[2].endswith(f"Unknown Classifier 'Fuzzy :: Wuzzy :: Was :: A :: Bear'!{Fore.RESET}")
		assert not captured.out

	def test_deprecated(self, capsys):
		validate_classifiers(["Natural Language :: Ukranian"])
		captured = capsys.readouterr()

		stderr = captured.err.split("\n")
		assert stderr[0].endswith(f"Classifier 'Natural Language :: Ukranian' is deprecated!{Fore.RESET}")
		assert not captured.out

	def test_valid(self, capsys):
		validate_classifiers(["Natural Language :: Ukrainian", "License :: OSI Approved"])
		captured = capsys.readouterr()
		assert not captured.out
		assert not captured.err
