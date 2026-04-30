# -- Project information -----------------------------------------------------
project = "RP2040 Temperature Monitor"
author = "Haruki"
language = "ja"

# -- General configuration ---------------------------------------------------
extensions = [
    "myst_parser",
    "sphinx_needs",
    "sphinxcontrib.plantuml"
]

source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}

master_doc = "index"
exclude_patterns = ["_build"]

# -- HTML output -------------------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_title = project

# -- PlantUML --------------------------------------------------------------
plantuml = "plantuml"
plantuml_output_format = "svg"

# -- sphinx-needs settings ---------------------------------------------------
# 要件タイプの定義
needs_types = [
    {
        "directive": "sysreq",
        "title": "システム要件",
        "prefix": "SYS_",
        "color": "#BFD8D2",
        "style": "node",
    },
    {
        "directive": "arc",
        "title": "アーキテクチャ要件",
        "prefix": "ARC_",
        "color": "#DF744A",
        "style": "node",
    },
]

# 要件のフィールド定義
needs_fields = {
    "status": {
        "description": "要件のステータス",
        "schema": {
            "enum": ["draft", "approved", "obsolete"],
        },
        "nullable": False,
    },
    "type_kind": {
        "description": "要件の種類(Functional, Timing, Safety等)",
        "schema": {"type": "string"},
        "nullable": True,
    },
    "tbd_items": {
        "description": "未確定項目",
        "schema": {"type": "string"},
        "nullable": True,
    },
    "rationale": {
        "description": "要件の根拠",
        "schema": {"type": "string"},
        "nullable": True,
    },
}

# トレースリレーション
needs_links = {
    "refines": {
        "incoming": "refined by",
        "outgoing": "refines",
    },
    "verifies": {
        "incoming": "verified by",
        "outgoing": "verifies",
    },
}