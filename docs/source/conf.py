import os
import sys

sys.path.insert(0, os.path.abspath("../../"))

project = "rokujo-scrapy-generic"
copyright = "2026, Tomoyuki Sakurai"
author = "Tomoyuki Sakurai"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxcontrib.mermaid",
]

html_theme = "pydata_sphinx_theme"

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_enable_extensions = [
    "colon_fence",
]

html_theme_options = {
}

html_static_path = ["_static"]
html_css_files = [
    "https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap",  # noqa E501
    "custom.css"
]
html_title = project
