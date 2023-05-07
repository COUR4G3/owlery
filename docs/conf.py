# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
import importlib
import inspect
import os
import sys

from importlib.metadata import version as get_version

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "owlery"
copyright = "2023, Michael de Villiers"
author = "Michael de Villiers"

# The full version, including alpha/beta/rc tags
release = get_version("owlery")


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "m2r2",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinx.ext.todo",
    "sphinx_click",
    "sphinx_copybutton",
    "sphinx_issues",
    "sphinx-prompt",
    "sphinxcontrib.spelling",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_title = f"{project} documentation ({release})"
html_theme = "furo"
html_theme_options = {
    "source_repository": "https://github.com/COUR4G3/owlery",
    "source_branch": "master",
    "source_directory": "docs/",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]


autodoc_typehints = "description"

autosectionlabel_prefix_document = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "flask": ("https://flask.palletsprojects.com/", None),
    "imapclient": ("https://imapclient.readthedocs.io/en/master/", None),
}

issues_github_path = "COUR4G3/owlery"

linkcheck_anchors_ignore = ["cron-jobs", "running-the-scheduler"]
linkcheck_ignore = [
    "https://github.com/COUR4G3/owlery",
    "https://pypi.org/project/owlery",
]

suppress_warnings = ["autosectionlabel.*"]

todo_include_todos = True


def linkcode_resolve(domain, info):
    if domain != "py":
        return None
    if not info["module"]:
        return None

    mod = importlib.import_module(info["module"])
    if "." in info["fullname"]:
        objname, attrname = info["fullname"].split(".")
        obj = getattr(mod, objname)
        try:
            # object is a method of a class
            obj = getattr(obj, attrname)
        except AttributeError:
            # object is an attribute of a class
            return None
    else:
        obj = getattr(mod, info["fullname"])

    try:
        file = inspect.getsourcefile(obj)
        lines = inspect.getsourcelines(obj)
    except TypeError:
        # e.g. object is a typing.Union
        return None
    file = os.path.relpath(file, os.path.abspath(".."))
    start, end = lines[1], lines[1] + len(lines[0]) - 1

    return (
        "https://github.com/COUR4G3/owlery/blob/master/"
        f"{file}#L{start}-L{end}"
    )


spelling_lang = "en_GB"

spelling_word_list_filename = [
    "spelling-wordlist.txt",
]

spelling_show_suggestions = True
spelling_ignore_pypi_package_names = True
spelling_ignore_contributor_names = True
