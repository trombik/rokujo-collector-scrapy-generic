import os
import sys

sys.path.insert(0, os.path.abspath("../../"))

project = "rokujo-collector-scrapy-generic"
copyright = "2026, Tomoyuki Sakurai"
author = "Tomoyuki Sakurai"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxcontrib.mermaid",
]

html_theme = "furo"

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_enable_extensions = [
    "colon_fence",
]

html_theme_options = {
    "light_css_variables": {
        "font-stack": "Arial, sans-serif",
        "font-stack--monospace": "Courier, monospace",
        "font-stack--headings": "Georgia, serif",
    },
    "dark_css_variables": {
        "font-stack": "Arial, sans-serif",
        "font-stack--monospace": "Courier, monospace",
        "font-stack--headings": "Georgia, serif",
    },
}
