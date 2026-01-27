import os
import sys

sys.path.insert(0, os.path.abspath("../../"))

project = "rokujo-collector-scrapy-generic"
copyright = "2026, Tomoyuki Sakurai"
author = "Tomoyuki Sakurai"

extensions = [
    "sphinxcontrib.mermaid",
    "myst_parser",
    "autodoc2",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_enable_extensions = [
    "colon_fence",
    "substitution",
]

autodoc2_packages = [
    {
        "path": "../../generic",
        "auto_mode": True,
        "exclude_dirs": [
        ]
    },
]
autodoc2_docstring_parser_type = "google"
autodoc2_render_plugin = "rst"

html_theme = "pydata_sphinx_theme"
html_css_files = [
    "https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap",  # noqa E501
    "custom.css"
]
html_static_path = ["_static"]
html_title = project
html_theme_options = {}
