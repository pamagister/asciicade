"""Sphinx configuration for the asciicade documentation."""

# -- Project information ------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "asciicade"
copyright = "2026, pamagister"
author = "pamagister"

# -- General configuration ----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
]

# Enable MyST extensions used by the Markdown sources.
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}

root_doc = "index"

exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

# -- Options for HTML output --------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_title = "Asciicade"
html_static_path = ["_static"]
html_css_files = [
    "css/custom.css",
]
html_logo = "_static/img/logo.png"
html_favicon = "_static/img/favicon.png"
html_show_sourcelink = False

html_theme_options = {
    "repository_url": "https://github.com/pamagister/asciicade",
    "repository_branch": "main",
    "path_to_docs": "docs",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_source_button": False,
    "use_edit_page_button": False,
    "use_download_button": False,
    "use_fullscreen_button": False,
    "home_page_in_toc": True,
    "show_navbar_depth": 2,
    "max_navbar_depth": 4,
    "collapse_navbar": False,
    "toc_title": "On this page",
}

# -- Link checking ------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-the-linkcheck-builder

linkcheck_timeout = 15
linkcheck_retries = 2

# -- MyST heading anchors -----------------------------------------------------
myst_heading_anchors = 3
