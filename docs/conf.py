# -- Project information -----------------------------------------------------
project = "RP2040 Temparature Monitor"
author = "Haruki Kiya"
language = "ja"

# -- General configuration ---------------------------------------------------
extensions = [
    "myst_parser",
    "sphinx-needs",
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
]

# ステータスの選択肢（値の表記揺れを防ぐ）
needs_statuses = [
    {"name": "draft", "description": "ドラフト"},
    {"name": "approved", "description": "承認済み"},
    {"name": "obsolute", "description": "廃止"},
]

# 追加フィールド
needs_extra_options = [
    "type_kind",
    "tbd_items",
    "rationale",
]

# トレースリレーション（今日は使わないが設定だけ）
needs_extra_links = [
    {"option": "refines", "incoming": "refined by", "outgoing": "refines"},
    {"option": "verifies", "incoming": "verified by", "outgoing": "verifies"},
]
