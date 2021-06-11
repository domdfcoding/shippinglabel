# stdlib
from typing import Optional

# 3rd party
from domdf_python_tools.paths import PathPlus
from sphinx.application import Sphinx  # nodep
from sphinx.errors import NoUri
from sphinx_toolbox import latex
from docutils import nodes


def replace_emoji(app: Sphinx, exception: Optional[Exception] = None):
	if exception:
		return

	if app.builder.name.lower() != "latex":
		return

	output_file = PathPlus(app.builder.outdir) / f"{app.builder.titles[0][1]}.tex"
	output_content = output_file.read_text()
	output_content = output_content.replace('😉', "\\Smiley")
	output_file.write_clean(output_content)


def handle_missing_xref(app: Sphinx, env, node: nodes.Node, contnode: nodes.Node) -> None:
	# Ignore missing reference warnings for the wheel_filename module
	if node.get("reftarget", '').startswith("wheel_filename."):
		raise NoUri


def setup(app: Sphinx):
	app.connect("build-finished", replace_emoji)
	app.connect("build-finished", latex.replace_unknown_unicode)
	app.connect("missing-reference", handle_missing_xref, priority=950)
