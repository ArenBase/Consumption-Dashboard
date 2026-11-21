# DESIGN.md · 校园消费数据看板

> 本文件是本看板的**视觉规范落点说明**，写法对齐 Google Stitch 提出的 `DESIGN.md` 约定，
> 设计令牌取自开源项目 [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)
> 中的 `design-md/notion/DESIGN.md`（MIT）。
> `app.py` 里的 `THEMES` / `CSS` / `style_fig()` 就是本文件的代码实现，**改配色先改这里**。

---

## 1. 为什么选 Notion

| 评估项 | Notion 规范的表现 | 对数据看板的意义 |
|---|---|---|
| 底色与层级 | `canvas #ffffff` + `surface #f6f5f4` + 1px `hairline #e5e3df` | 大表格、多图表同屏时靠「发丝线 + 浅表面」分层，不靠阴影堆叠，久看不累 |
| 语义色 | 紫 `#5645d4` 只给主行动，其余用品牌色板（橙 / 青 / 粉 / 蓝） | 6 个指标卡、6 个消费类别正好落在 6 个品牌色上，不会出现「一屏七八种高饱和色」 |
| 字号层级 | 80→11px 共 13 级，600 用于标题、500 用于按钮、400 用于正文 | 指标卡 27px / 模块标题 19px / 正文 13.5px / 说明 11.5px，层级清楚且不用加粗刷屏 |
| 圆角与按钮 | 卡片 12px、按钮 8px（**不用胶囊按钮**）、胶囊只给标签 | 与 Streamlit 默认的「大圆角 + 胶囊」拉开差距，更像产品文档而不是示例页 |
| 暗色 | 规范未覆盖（Known Gaps 已注明） | 本项目按同一语义自行推导了一套暗色令牌，并在文档里注明是补充 |

对比未改造前的默认 Streamlit 外观，主要差异：

| 维度 | 改造前 | 改造后（Notion 规范） |
|---|---|---|
| 底色 | `#F4F6FA` 冷灰蓝 | `#ffffff` + `#f6f5f4` 暖白表面 |
| 主色 | `#2E5BFF` 科技蓝 | `#5645d4` Notion 紫 |
| 卡片 | 左侧 3px 彩色竖条 + 12px 圆角 | 1px 发丝边框 + 12px 圆角 + 4% 阴影 |
| 页头 | 标题 + 下划线 | 深 navy 横幅 `#0a1530` + 便签圆点装饰 |
| 图表 | 白底直角、系统默认色序 | 卡片化、透明背景、品牌色序、无轴标题 |
| 提示条 | Streamlit 原生红/绿 alert | Notion callout：浅桃 / 浅薄荷底 + 深色文字 |

---

## 2. 设计令牌（亮色）

```yaml
colors:
  canvas:        "#ffffff"   # 页面底色
  surface:       "#f6f5f4"   # 侧边栏、次级表面
  panel:         "#ffffff"   # 卡片表面
  hairline:      "#e5e3df"   # 1px 边框 / 分隔线
  hairline_soft: "#ede9e4"   # 更弱的网格线
  ink:           "#1a1a1a"   # 标题
  charcoal:      "#37352f"   # 正文（Notion 标志性暖炭黑）
  steel:         "#787671"   # 次级文字
  stone:         "#a4a097"   # 说明文字 / 标签
  accent:        "#5645d4"   # Notion 紫，只给主指标与主按钮
  navy:          "#0a1530"   # 页头横幅
  teal:          "#2a9d99"
  orange:        "#dd5b00"
  pink:          "#ff64c8"
  link:          "#0075de"
  tint_lavender: "#e6e0f5"   # KPI 图标底、下钻标签底
  tint_peach:    "#ffe8d4"   # 预警 callout
  tint_mint:     "#d9f3e1"   # 正常 callout
  tint_sky:      "#dcecfa"
  tint_yellow:   "#fef7d6"
  red:           "#e03131"   # 语义错误 / 超额预警
```

暗色档为补充推导，语义一一对应：

```yaml
colors_dark:
  canvas: "#191919"   surface: "#202020"   panel: "#202020"
  hairline: "#2f2f2f" hairline_soft: "#262626"
  ink: "#e9e9e7"      charcoal: "#d4d4d1"  steel: "#9b9a97"  stone: "#8a8985"
  accent: "#8f7ff0"   navy: "#0a1530"      red: "#f06a6a"
```

## 3. 排版

| 用途 | 字号 | 字重 | 行高 | 说明 |
|---|---|---|---|---|
| 页头主标题 | 30px | 600 | 1.2 | 字距 -0.6px |
| 模块标题 | 19px | 600 | 1.3 | 前置 `01`~`06` 编号 |
| 模块说明 | 12px | 400 | 1.4 | 右对齐，`steel` |
| KPI 数值 | 27px | 600 | 1.15 | `tabular-nums`，字距 -0.7px |
| KPI 标签 | 10.5px | 600 | 1.4 | 全大写 + 0.9px 字距 |
| 图表标题 | 15px | 600 | 1.2 | 左对齐，位于卡片内 |
| 正文 / 提示 | 13.5px | 400 | 1.55 | — |

字体栈：`Inter, -apple-system, "Segoe UI Variable Display", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif`
（Notion Sans 为商用字体，规范给出的替代方案即 Inter / 系统 UI 字体）

## 4. 组件规范

| 组件 | 规格 |
|---|---|
| 页头横幅 | `navy` 底、16px 圆角、26/32px 内边距、右上角 4 个便签圆点（黄/粉/薄荷/天蓝） |
| KPI 卡 | 白底、1px `hairline`、12px 圆角、14/16px 内边距、26px 浅色系图标块 |
| 图表卡 | 白底、1px `hairline`、12px 圆角、10/12px 内边距、4% 阴影、入场 fadeUp |
| 模块标题 | 编号 + 标题 + 右侧说明，底部 1px `hairline_soft` |
| 下钻标签 | 6px 圆角（非胶囊）、`tint_lavender` 底、深紫字、12px 600 |
| Callout | 12px 圆角、浅色底 + 同色系描边，`warn` 用桃色、`ok` 用薄荷色 |
| 按钮 | 8px 圆角、1px `hairline_strong`、白底黑字（次级按钮语义） |
| 表格 | 12px 圆角描边容器，`st.dataframe` 原生网格 |

## 5. 图表规范

- 背景透明，由卡片提供底色，不使用 Plotly 自带模板底色。
- 色序：`accent → teal → orange → pink → green → link`，与消费类别一一绑定（`CAT_COLOR`）。
- **不画坐标轴标题**：语义交给卡片标题，减少一行小字。
- 网格只保留横向、颜色 `hairline_soft`；纵向网格全关。
- hover 卡片化：白底 + 发丝描边 + 圆角。
- 环形图：环内只标 ≥5% 的占比（3.8% / 1.7% 这类小切片不写字，避免叠字），图例竖排在右。
- 热力图色阶：`surface_soft → tint_lavender → accent`。

## 6. 落地位置

| 令牌 | 代码位置 |
|---|---|
| 亮/暗两套色板 | `app.py` → `THEMES` |
| 类别配色 | `app.py` → `CAT_COLOR` |
| 全局 CSS（布局/卡片/页头/侧栏/callout） | `app.py` → `CSS`（`string.Template`，`$token` 注入） |
| 图表统一样式 | `app.py` → `style_fig()` |
| KPI 卡片（HTML+JS 数值滚动） | `app.py` → `KPI_TEMPLATE` / `kpi_cards()` |
| Streamlit 主题变量 | `.streamlit/config.toml` → `[theme]` |

> 修改流程：先改本文件的令牌表 → 再同步 `THEMES` → 最后同步 `config.toml`。
> 三处保持一致，看板与 Streamlit 原生控件（滑块、日期选择器、表格）才不会「各穿各的衣服」。
