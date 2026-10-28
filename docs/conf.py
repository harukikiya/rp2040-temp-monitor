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
# need の type・フィールド・リンクは docs/ubproject.toml に書き、ここから読む。
# ubCode（VS Code 拡張）も同じファイルを読む（ADR-0007）。
needs_from_toml = "ubproject.toml"

# -- 要件管理の品質チェック ---------------------------------------------------
# これらのフィルタにマッチする要件があるとwarningが出る。
# `make html`の-Wオプションによりwarningはerrorに昇格し、ビルドが失敗する。
needs_warnings = {
    "swr_without_parent": "type == 'swreq' and not refines",
    "sys_without_swr": "type == 'sysreq' and not refines_back",
    "approved_with_tbd": "status == 'approved' and tbd_items is not None and tbd_items != ''",
    "open_params_without_due": (
        "open_params is not None and open_params != '' "
        "and '解決時期:' not in open_params"
    ),
    "swverif_without_target": "type == 'swverif' and not verifies",
    "swverif_without_method": "type == 'swverif' and (method is None or method == '')",
    "approved_swr_without_verification": (
        "type == 'swreq' and status == 'approved' and not verifies_back"
    ),
}

# needs.json を出力（metadata linter・将来のレビュワー/RAG の突合先。ADR-0004）
needs_build_json = True
