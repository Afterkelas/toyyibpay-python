"""Sphinx configuration for ToyyibPay Python SDK documentation."""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('..'))

# Import version from the package
from toyyibpay import __version__

# -- Project information -----------------------------------------------------

project = 'ToyyibPay Python SDK'
copyright = f'{datetime.now().year}, ToyyibPay SDK Contributors'
author = 'ToyyibPay SDK Contributors'

# The full version, including alpha/beta/rc tags
release = __version__
version = __version__

# -- General configuration ---------------------------------------------------

extensions = [
    # Core extensions
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    
    # Type hints
    'sphinx_autodoc_typehints',
    
    # Markdown support
    'myst_parser',
    
    # Better API docs
    'sphinx_autoapi.extension',
    
    # UI enhancements
    'sphinx_copybutton',
    'sphinx_inline_tabs',
    'sphinx_design',
    'sphinx_togglebutton',
    
    # Diagrams
    'sphinxcontrib.mermaid',
    
    # Search
    'readthedocs_sphinx_search',
    
    # Sitemap
    'sphinx_sitemap',
]

# AutoAPI configuration
autoapi_type = 'python'
autoapi_dirs = ['../toyyibpay']
autoapi_options = [
    'members',
    'undoc-members',
    'show-inheritance',
    'show-module-summary',
    'special-members',
    'imported-members',
]
autoapi_ignore = ['*/migrations/*', '*/tests/*']
autoapi_add_toctree_entry = True
autoapi_keep_files = True

# Autodoc configuration
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}
autodoc_typehints = 'both'
autodoc_typehints_description_target = 'documented'

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

# MyST configuration for Markdown
myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'dollarmath',
    'html_image',
    'linkify',
    'replacements',
    'smartquotes',
    'substitution',
    'tasklist',
]
myst_heading_anchors = 3

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'httpx': ('https://www.python-httpx.org', None),
    'pydantic': ('https://docs.pydantic.dev', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/20/', None),
    'flask': ('https://flask.palletsprojects.com/en/3.0.x/', None),
    'fastapi': ('https://fastapi.tiangolo.com', None),
}

# Add any paths that contain templates here
templates_path = ['_templates']

# List of patterns to exclude
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    '**.ipynb_checkpoints',
    'api/toyyibpay.tests*',
]

# The name of the Pygments (syntax highlighting) style
pygments_style = 'sphinx'
pygments_dark_style = 'monokai'

# -- Options for HTML output -------------------------------------------------

# The theme to use
html_theme = 'sphinx_rtd_theme'
# html_theme = 'sphinx_book_theme'  # Alternative modern theme

# Theme options
html_theme_options = {
    # RTD theme options
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'style_nav_header_background': '#2980B9',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    
    # For sphinx_book_theme (if used)
    # 'repository_url': 'https://github.com/mwaizwafiq/toyyibpay-python',
    # 'use_repository_button': True,
    # 'use_issues_button': True,
    # 'use_edit_page_button': True,
    # 'path_to_docs': 'docs',
    # 'home_page_in_toc': True,
}

# Add any paths that contain custom static files
html_static_path = ['_static']

# Custom CSS
html_css_files = [
    'css/custom.css',
]

# Custom JavaScript
html_js_files = [
    'js/custom.js',
]

# The suffix(es) of source filenames
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# The master toctree document
master_doc = 'index'

# Logo and favicon
html_logo = '_static/logo.png'  # Add your logo
html_favicon = '_static/favicon.ico'  # Add your favicon

# Output file base name for HTML help builder
htmlhelp_basename = 'toyyibpaydoc'

# -- Options for other output formats ----------------------------------------

# LaTeX output
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': r'''
\usepackage{charter}
\usepackage[defaultsans]{lato}
\usepackage{inconsolata}
''',
}

latex_documents = [
    (master_doc, 'toyyibpay.tex', 'ToyyibPay Python SDK Documentation',
     'ToyyibPay SDK Contributors', 'manual'),
]

# EPUB output
epub_title = project
epub_exclude_files = ['search.html']

# -- Extension configuration -------------------------------------------------

# Copy button configuration
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"

# Sitemap configuration
html_baseurl = 'https://toyyibpay-python.readthedocs.io'
sitemap_url_scheme = "{link}"
sitemap_locales = [None]
sitemap_filename = "sitemap.xml"

# Togglebutton configuration
togglebutton_hint = "Click to show"
togglebutton_hint_hide = "Click to hide"

# Search configuration
rtd_sphinx_search_file_type = "minified"

# -- Custom setup ------------------------------------------------------------

def setup(app):
    """Custom Sphinx setup."""
    app.add_css_file('css/custom.css')
    app.add_js_file('js/custom.js')
    
    # Add custom roles
    app.add_role('pypi', lambda name, rawtext, text, lineno, inliner, options={}, content=[]: (
        [inliner.document.reporter.info(f'https://pypi.org/project/{text}/')],
        []
    ))