# stdlib
import os
from typing import List

# 3rd party
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike

# this package
from shippinglabel import normalize
from shippinglabel.requirements import (
		ComparableRequirement,
		RequirementsManager,
		combine_requirements,
		read_requirements
		)


class DocRequirementsManager(RequirementsManager):
	target_requirements = {
			ComparableRequirement("sphinxcontrib-httpdomain>=1.7.0"),
			ComparableRequirement("sphinxemoji>=0.1.6"),
			ComparableRequirement("sphinx-notfound-page>=0.5"),
			ComparableRequirement("sphinx-tabs>=1.1.13"),
			ComparableRequirement("autodocsumm>=0.2.0"),
			# ComparableRequirement("sphinx-gitstamp"),
			# ComparableRequirement("gitpython"),
			# ComparableRequirement("sphinx_autodoc_typehints>=1.11.0"),
			ComparableRequirement("sphinx-copybutton>=0.2.12"),
			ComparableRequirement("sphinx-prompt>=1.1.0"),
			ComparableRequirement("sphinx>=3.0.3"),
			}

	def __init__(self, repo_path: PathLike):
		self.filename = os.path.join("doc-source", "requirements.txt")
		super().__init__(repo_path)

	def compile_target_requirements(self) -> None:
		# Mapping of pypi_name to version specifier
		theme_versions = {
				"alabaster": ">=0.7.12",
				"sphinx_rtd_theme": "<0.5",
				"domdf_sphinx_theme": ">=0.1.0",
				"repo_helper_sphinx_theme": ">=0.0.2",
				}

		for name, specifier in theme_versions.items():
			if name == "alabaster":
				self.target_requirements.add(ComparableRequirement(f"{name}{specifier}"))
				break
		else:
			self.target_requirements.add(ComparableRequirement("alabaster>=0.7.12"))

		# Mapping of pypi_name to version specifier
		my_sphinx_extensions = {
				"extras_require": ">=0.2.0",
				"seed_intersphinx_mapping": ">=0.1.1",
				"default_values": ">=0.2.0",
				"toctree_plus": ">=0.0.4",
				"sphinx-toolbox": ">=1.7.1",
				}

		for name, specifier in my_sphinx_extensions.items():
			if name != "shippinglabel":
				self.target_requirements.add(ComparableRequirement(f"{name}{specifier}"))

	def merge_requirements(self) -> List[str]:
		current_requirements, comments = read_requirements(self.req_file)

		for req in current_requirements:
			req.name = normalize(req.name)
			if req.name not in self.get_target_requirement_names():
				self.target_requirements.add(req)

		self.target_requirements = set(combine_requirements(self.target_requirements))

		return comments


def test_requirements_manager(tmp_pathplus: PathPlus):

	(tmp_pathplus / "requirements.txt").write_text('')
	(tmp_pathplus / "doc-source").mkdir()
	(tmp_pathplus / "doc-source" / "requirements.txt").write_text('')

	DocRequirementsManager(tmp_pathplus).run()

	assert (tmp_pathplus / "doc-source" / "requirements.txt").read_lines() == [
			"alabaster>=0.7.12",
			"autodocsumm>=0.2.0",
			"default-values>=0.2.0",
			"extras-require>=0.2.0",
			"seed-intersphinx-mapping>=0.1.1",
			"sphinx>=3.0.3",
			"sphinx-copybutton>=0.2.12",
			"sphinx-notfound-page>=0.5",
			"sphinx-prompt>=1.1.0",
			"sphinx-tabs>=1.1.13",
			"sphinx-toolbox>=1.7.1",
			"sphinxcontrib-httpdomain>=1.7.0",
			"sphinxemoji>=0.1.6",
			"toctree-plus>=0.0.4",
			'',
			]

	with (tmp_pathplus / "doc-source" / "requirements.txt").open('a', encoding="UTF-8") as fp:
		fp.write("lorem>=0.1.1")

	DocRequirementsManager(tmp_pathplus).run()

	assert (tmp_pathplus / "doc-source" / "requirements.txt").read_lines() == [
			"alabaster>=0.7.12",
			"autodocsumm>=0.2.0",
			"default-values>=0.2.0",
			"extras-require>=0.2.0",
			"lorem>=0.1.1",
			"seed-intersphinx-mapping>=0.1.1",
			"sphinx>=3.0.3",
			"sphinx-copybutton>=0.2.12",
			"sphinx-notfound-page>=0.5",
			"sphinx-prompt>=1.1.0",
			"sphinx-tabs>=1.1.13",
			"sphinx-toolbox>=1.7.1",
			"sphinxcontrib-httpdomain>=1.7.0",
			"sphinxemoji>=0.1.6",
			"toctree-plus>=0.0.4",
			'',
			]


def test_requirements_manager_extras(tmp_pathplus: PathPlus):

	(tmp_pathplus / "requirements.txt").write_text("domdf_python_tools>=1.5.0")
	(tmp_pathplus / "doc-source").mkdir()
	(tmp_pathplus / "doc-source" / "requirements.txt").write_text("domdf_python_tools[testing]>=1.5.0")

	DocRequirementsManager(tmp_pathplus).run()

	assert (tmp_pathplus / "doc-source" / "requirements.txt").read_lines() == [
			"alabaster>=0.7.12",
			"autodocsumm>=0.2.0",
			"default-values>=0.2.0",
			"domdf-python-tools[testing]>=1.5.0",
			"extras-require>=0.2.0",
			"seed-intersphinx-mapping>=0.1.1",
			"sphinx>=3.0.3",
			"sphinx-copybutton>=0.2.12",
			"sphinx-notfound-page>=0.5",
			"sphinx-prompt>=1.1.0",
			"sphinx-tabs>=1.1.13",
			"sphinx-toolbox>=1.7.1",
			"sphinxcontrib-httpdomain>=1.7.0",
			"sphinxemoji>=0.1.6",
			"toctree-plus>=0.0.4",
			'',
			]
