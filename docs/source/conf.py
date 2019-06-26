import sphinx_rtd_theme

project = "aiompesa"
copyright = "2019, Martin Musale <martinmshale@gmail.com>"
author = "Martin Musale <martinmshale@gmail.com>"
extensions = []
templates_path = ["_templates"]
exclude_patterns = []

master_doc = "index"
html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ["_static"]
