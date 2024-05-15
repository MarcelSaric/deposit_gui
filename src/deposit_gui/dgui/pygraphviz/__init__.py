"""
PyGraphviz
==========

A Python wrapper for the graphviz Agraph data structure.

See https://pygraphviz.github.io for complete documentation.
See pygraphviz.AGraph for detailed documentation.
"""

import deposit_gui.dgui
import os
import sys

# MODIFIED by Deposit GUI

if sys.platform == "win32":
    path = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(deposit_gui.dgui.__file__), "graphviz")))
    os.add_dll_directory(path)
elif sys.platform == "linux":
    print("Running on Linux")
elif sys.platform == "darwin":
    path = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(deposit_gui.dgui.__file__), "graphviz")))
    print(path)
    os.environ["DYLD_LIBRARY_PATH"] = f"{path}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"
    print("Running on macOS.")
else:
    print("Running on other OS.")


__version__ = "1.9"

from .agraph import AGraph, Node, Edge, Attribute, ItemAttribute, DotError

__all__ = ["AGraph", "Node", "Edge", "Attribute", "ItemAttribute", "DotError"]

# Per contract with Sphinx-Gallery, this method must be available at top level
from .scraper import _get_sg_image_scraper

#del sys
