import warnings
warnings.filterwarnings("ignore", message=".*missing from font.*")

# -- Matplotlib 日本語フォント設定 -------------------------------------------
# sphinx-needsの円グラフ・棒グラフでの日本語表示用設定。
# 現状(sphinx-needs 8.0.0)ではrcParams上書きの実装の問題で反映されないため、
# グラフタイトルは英語で書いている。将来sphinx-needs側で改善されれば日本語化可能。
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["font.sans-serif"] = ["Noto Sans CJK JP"]
plt.rcParams["font.serif"] = ["Noto Sans CJK JP"]
plt.rcParams["font.monospace"] = ["Noto Sans CJK JP"]
plt.rcParams["axes.unicode_minus"] = False

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
exclude_patterns = [
    "_build",
    "common/adr/template.md",
]

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
    {
        "directive": "swreq",
        "title": "ソフトウェア要件",
        "prefix": "SWR_",
        "color": "##FEDCD2",
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
    "layer": {
        "description": "要求が属するレイヤ",
        "schema": {
            "type": "string",
            "enum": ["application", "service", "driver", "hal"],
        },
        "nullable": True,
    }
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