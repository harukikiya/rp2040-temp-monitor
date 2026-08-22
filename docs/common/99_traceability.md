# トレーサビリティ

本ドキュメントは要件群の全体像を俯瞰し、トレース関係を可視化するものである。
要件の追加・更新時には自動的にこのページの内容も更新される。

## ダッシュボード

### 要件のステータス分布

#### システム要件

```{needpie} System Requirements Status
:labels: Draft, Approved, Obsolete
:legend:
type == 'sysreq' and status == 'draft'
type == 'sysreq' and status == 'approved'
type == 'sysreq' and status == 'obsolete'
```

#### ソフトウェア要件

```{needpie} Software Requirements Status
:labels: Draft, Approved, Obsolete
:legend:
type == 'swreq' and status == 'draft'
type == 'swreq' and status == 'approved'
type == 'swreq' and status == 'obsolete'
```

### レイヤ別ソフトウェア要件数

```{needbar} Requirements per Layer
:xlabels: Application, Service, Driver, HAL
:show_sum:
type == 'swreq' and layer == 'application',type == 'swreq' and layer == 'service',type == 'swreq' and layer == 'driver',type == 'swreq' and layer == 'hal'
```

### 品質チェック

#### 承認済みだがTBDが残っている要件

`tbd_items` は構造的 TBD（要件の構造・インタフェースが未定で設計できない項目）のみを保持する。
したがってこの表に要件が現れることは、承認基準の違反を意味する。
値の仮置きは `open_params` に置き、承認を阻まない（ADR-0005）。

```{needtable}
:filter: status == 'approved' and tbd_items is not None and tbd_items != ''
:columns: id, title, type, tbd_items
:style: table
```

#### 実機調整の宿題が残る要件

`open_params` を持つ要件は承認できるが、値は仮置きのままである。
段階4 で閉じるべき宿題の一覧として使う。

```{needtable}
:filter: open_params is not None and open_params != ''
:columns: id, title, status, open_params
:style: table
```

#### 親要件を持たないソフトウェア要件

親要件（refines先）を持たないSWRは孤立した要件であり、システム要件のどこから派生したのかが追跡できない状態である。

```{needtable}
:filter: type == 'swreq' and not refines
:columns: id, title, layer
:style: table
```

#### 派生SWRを持たないシステム要件

派生SWRを持たないシステム要件は、ソフトウェアレベルでの実現方法が未定義の状態である。

```{needtable}
:filter: type == 'sysreq' and not refines_back
:columns: id, title, status
:style: table
```

## システム要件一覧

```{needtable}
:filter: type == 'sysreq'
:columns: id, title, status, type_kind, tbd_items
:style: table
```

## アーキテクチャ要件一覧

```{needtable}
:filter: type == 'arc'
:columns: id, title, status, refines
:style: table
```

## ソフトウェア要件一覧

### Application層

```{needtable}
:filter: type == 'swreq' and layer == 'application'
:columns: id, title, status, refines
:style: table
```

### Service層

```{needtable}
:filter: type == 'swreq' and layer == 'service'
:columns: id, title, status, refines
:style: table
```

### Driver層

```{needtable}
:filter: type == 'swreq' and layer == 'driver'
:columns: id, title, status, refines
:style: table
```

### HAL層

```{needtable}
:filter: type == 'swreq' and layer == 'hal'
:columns: id, title, status, refines
:style: table
```

## SYS → SWR トレースマトリクス

各システム要件が、どのソフトウェア要件によって実現されているかを示す。

```{needtable}
:filter: type == 'sysreq'
:columns: id, title, refines_back as "派生SWR"
:style: table
```

## ARC → SWR トレースマトリクス

各アーキテクチャ要件が、どのソフトウェア要件と関連するかを示す。
（注：現在のSWRはSYS要件にrefinesしている。ARCへのrefinesは将来的に必要に応じて追加する）

```{needtable}
:filter: type == 'arc'
:columns: id, title, refines_back as "関連SWR"
:style: table
```

## 未確定項目を持つ要件

TBD（To Be Determined）が残っている要件の一覧。
これらは実装段階で具体化または調整が必要となる項目を含む。

```{needtable}
:filter: tbd_items is not None and tbd_items != ''
:columns: id, title, type, tbd_items
:style: table
```

## トレースフロー図

### 全体俯瞰(システム要件とアーキテクチャ要件)

システム要件とアーキテクチャ要件の関係を示す。
ソフトウェア要件は数が多いため別図で示す。

```{needflow}
:filter: type in ['sysreq', 'arc']
:link_types: refines
:show_link_names:
```

### SYS_001の派生

```{needflow}
:filter: id == 'SYS_001' or 'SYS_001' in refines
:link_types: refines
:show_link_names:
```

### SYS_002の派生

```{needflow}
:filter: id == 'SYS_002' or 'SYS_002' in refines
:link_types: refines
:show_link_names:
```

### SYS_003の派生

```{needflow}
:filter: id == 'SYS_003' or 'SYS_003' in refines
:link_types: refines
:show_link_names:
```

### SYS_004の派生

```{needflow}
:filter: id == 'SYS_004' or 'SYS_004' in refines
:link_types: refines
:show_link_names:
```

### SYS_005の派生

```{needflow}
:filter: id == 'SYS_005' or 'SYS_005' in refines
:link_types: refines
:show_link_names:
```

### SYS_006の派生

```{needflow}
:filter: id == 'SYS_006' or 'SYS_006' in refines
:link_types: refines
:show_link_names:
```
