"""Configuracion de Sphinx para la documentacion del proyecto."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
DOCS_DIR = PROJECT_ROOT / "docs"

sys.path.insert(0, str(SRC_DIR))

project = "TPFI - Ingenieria de Software II"
copyright = "2026, Santiago Mout"
author = "Santiago Mout"

with open(PROJECT_ROOT / "VERSION", encoding="utf-8") as f:
    version = f.read().strip()
release = version

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

todo_include_todos = True

html_theme = "alabaster"
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}