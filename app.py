# -*- coding: utf-8 -*-
"""
实验2 数据看板 —— 校园消费数据看板
=====================================================
技术栈：Streamlit + Pandas + Plotly
视觉规范：参考开源项目 VoltAgent/awesome-design-md 中 notion/DESIGN.md
          （见同目录 DESIGN.md，色板 / 字号 / 圆角 / 阴影 / 间距均取自该规范）
运行：  python -m streamlit run app.py
（或直接双击同目录下的 启动看板.bat）

页面结构（对应实验要求的四大模块）：
    模块一  数据概览区   —— 核心指标卡片（含数值滚动动画、预警变色）
    模块二  维度统计区   —— 环形图 / 学院柱状图(可点击联动) / 商户排行榜
    模块三  趋势分析区   —— 消费趋势折线图 / 类别堆叠面积图 / 星期×时段热力图
    模块四  明细数据区   —— 明细表格 / 实时流水 / 数据导出
    多维度分析           —— 雷达图 + 预算执行率仪表盘

进阶与扩展功能：
    进阶1  组件渐入动画、数值滚动动画、hover 提示、自适应栅格布局
    进阶2  多维筛选联动、图表点击下钻联动
    进阶3  排行榜、热力图、雷达图、进度仪表盘
    扩展1  动态数据源 + 秒级自动刷新（实时流水看板）
    扩展2  单笔金额阈值预警、月人均预算预警
    扩展4  数据导出（CSV / Excel）
    扩展5  亮色 / 暗色双主题切换

截图模式（供文档配图使用，正常使用无需关心）：
    ?shot=full          隐藏侧边栏与顶栏，只渲染主内容（便于整页截图）
    ?mod=1..6           只渲染指定模块（1~4 基础模块、5 多维度分析、6 实时流水）
    ?live=1             强制开启实时数据流
"""

import os
import datetime as dt
from string import Template

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================ 页面基础配置
st.set_page_config(
    page_title="校园消费数据看板",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "校园消费数据.csv")

# ============================================================ 设计令牌（Notion DESIGN.md）
# 色值直接取自 awesome-design-md → design-md/notion/DESIGN.md
# 暗色档为该规范的补充（原规范未覆盖暗色值，按同一语义推导）
THEMES = {
    "light": {
        "name": "亮色",
        # 底色 / 表面
        "canvas": "#ffffff",
        "surface": "#f6f5f4",
        "surface_soft": "#fafaf9",
        "panel": "#ffffff",
        "hairline": "#e5e3df",
        "hairline_soft": "#ede9e4",
        "hairline_strong": "#c8c4be",
        # 文字
        "ink": "#1a1a1a",
        "charcoal": "#37352f",
        "slate": "#5d5b54",
        "steel": "#787671",
        "stone": "#a4a097",
        # 品牌色
        "accent": "#5645d4",
        "accent_pressed": "#4534b3",
        "link": "#0075de",
        "navy": "#0a1530",
        "purple": "#7b3ff2",
        "teal": "#2a9d99",
        "green": "#1aae39",
        "orange": "#dd5b00",
        "pink": "#ff64c8",
        "yellow": "#f5d75e",
        # 语义色
        "red": "#e03131",
        "success": "#1aae39",
        "warning": "#dd5b00",
        # 柔和底色（Notion 的 pastel 卡片色）
        "tint_peach": "#ffe8d4",
        "tint_rose": "#fde0ec",
        "tint_mint": "#d9f3e1",
        "tint_lavender": "#e6e0f5",
        "tint_sky": "#dcecfa",
        "tint_yellow": "#fef7d6",
        "tint_cream": "#f8f5e8",
        # 层次
        "hero_accent": "#fef7d6",
        "warn_bg": "#ffe8d4", "warn_border": "rgba(221,91,0,.22)", "warn_text": "#793400",
        "ok_bg": "#d9f3e1", "ok_border": "rgba(26,174,57,.20)", "ok_text": "#14691f",
        "shadow1": "0 1px 2px rgba(15,15,15,.04)",
        "shadow2": "0 4px 12px rgba(15,15,15,.08)",
        "plotly": "plotly_white",
    },
    "dark": {
        "name": "暗色",
        "canvas": "#191919",
        "surface": "#202020",
        "surface_soft": "#1c1c1c",
        "panel": "#202020",
        "hairline": "#2f2f2f",
        "hairline_soft": "#262626",
        "hairline_strong": "#3f3f3f",
        "ink": "#e9e9e7",
        "charcoal": "#d4d4d1",
        "slate": "#b6b5b2",
        "steel": "#9b9a97",
        "stone": "#8a8985",
        "accent": "#8f7ff0",
        "accent_pressed": "#a294f5",
        "link": "#4dabf7",
        "navy": "#0a1530",
        "purple": "#a78bfa",
        "teal": "#3fbfb8",
        "green": "#4ecb71",
        "orange": "#f08a4b",
        "pink": "#ff8ad4",
        "yellow": "#f5d75e",
        "red": "#f06a6a",
        "success": "#4ecb71",
        "warning": "#f08a4b",
        "tint_peach": "#3a2c22",
        "tint_rose": "#3a2530",
        "tint_mint": "#1f3529",
        "tint_lavender": "#2c2740",
        "tint_sky": "#1f2f3a",
        "tint_yellow": "#37331f",
        "tint_cream": "#2b2925",
        "hero_accent": "#f5d75e",
        "warn_bg": "#3a2c22", "warn_border": "rgba(240,138,75,.38)", "warn_text": "#ffc79a",
        "ok_bg": "#1f3529", "ok_border": "rgba(78,203,113,.30)", "ok_text": "#9ce0af",
        "shadow1": "0 1px 2px rgba(0,0,0,.35)",
        "shadow2": "0 4px 12px rgba(0,0,0,.45)",
        "plotly": "plotly_dark",
    },
}

# 消费类别 → Notion 品牌色（对应 DESIGN.md 的 brand spectrum）
CAT_COLOR = {
    "食堂餐饮": "#5645d4",   # Notion Purple（主色）
    "超市便利店": "#2a9d99",  # Teal
    "文具图书": "#dd5b00",   # Orange
    "交通出行": "#0075de",   # Link Blue
    "娱乐休闲": "#ff64c8",   # Pink
    "快递服务": "#a4a097",   # Stone
}

WEEKDAY_ORDER = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
SLOT_ORDER = ["早餐", "午餐", "晚餐", "夜宵", "其他"]
FONT_STACK = ('Inter, -apple-system, "Segoe UI Variable Display", "Segoe UI", '
              '"PingFang SC", "Microsoft YaHei", sans-serif')


def _luminance(color) -> float:
    """估算颜色亮度，用于判断当前主题是深色还是浅色"""
    if not color or not isinstance(color, str):
        return 1.0
    c = color.strip().lstrip("#")
    if len(c) == 6:
        try:
            r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
            return (0.299 * r + 0.587 * g + 0.114 * b) / 255
        except ValueError:
            return 1.0
    return 1.0


def detect_theme() -> dict:
    """
    根据 Streamlit 实际生效的主题（.streamlit/config.toml 中的 [theme]）
    选择看板配色。改 config.toml 的 theme.base 即可切换亮色 / 暗色。
    """
    try:
        base = st.get_option("theme.base") or "light"
        bg = st.get_option("theme.backgroundColor")
    except Exception:
        base, bg = "light", None
    if bg:
        return THEMES["dark" if _luminance(bg) < 0.5 else "light"]
    return THEMES["dark" if base == "dark" else "light"]


def hex_rgba(hex_color: str, alpha: float) -> str:
    """把 #RRGGBB 转成 rgba()，用于半透明填充"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ============================================================ 数据加载
@st.cache_data(show_spinner="正在加载并解析数据 ...")
def load_data(path: str, mtime: float) -> pd.DataFrame:
    """
    读取分析底表。
    mtime 参与缓存键：数据文件一旦重新生成，缓存会自动失效，
    避免看板还在展示旧数据的尴尬。
    """
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["消费日期"] = pd.to_datetime(df["消费日期"])
    return df


# ============================================================ 全局样式（Notion 视觉规范落地）
CSS = Template("""
<style>
/* ---------- 基础排版 ---------- */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: $canvas;
    color: $charcoal;
    font-family: Inter, -apple-system, "Segoe UI Variable Display", "Segoe UI",
                 "PingFang SC", "Microsoft YaHei", sans-serif;
    -webkit-font-smoothing: antialiased;
}
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1360px; }
header[data-testid="stHeader"] { display: none; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stAppDeployButton"], footer { display: none !important; }
#MainMenu { visibility: hidden; }
h1, h2, h3, h4, h5 { color: $ink; letter-spacing: -0.2px; }

/* ---------- 顶部主视觉（Notion 深navy 横幅 + 便签圆点） ---------- */
.hero {
    position: relative; overflow: hidden;
    background: $navy;
    border-radius: 16px;
    padding: 26px 32px 24px 32px;
    margin-bottom: 6px;
    box-shadow: $shadow2;
}
.hero::after {
    content: ""; position: absolute; right: -60px; top: -80px;
    width: 260px; height: 260px; border-radius: 50%;
    background: radial-gradient(circle, rgba(86,69,212,.45) 0%, rgba(10,21,48,0) 70%);
}
.hero-dot { position: absolute; border-radius: 50%; opacity: .92; }
.hero-dot.d1 { width: 13px; height: 13px; background: $tint_yellow; right: 46px;  top: 24px; }
.hero-dot.d2 { width: 8px;  height: 8px;  background: $tint_rose;   right: 74px;  top: 14px; }
.hero-dot.d3 { width: 11px; height: 11px; background: $tint_mint;   right: 104px; top: 42px; }
.hero-dot.d4 { width: 6px;  height: 6px;  background: $tint_sky;    right: 132px; top: 20px; }
.hero-eyebrow {
    font-size: 11px; font-weight: 600; letter-spacing: 1.4px; text-transform: uppercase;
    color: rgba(255,255,255,.55); margin-bottom: 10px;
}
.hero-title {
    font-size: 30px; font-weight: 600; line-height: 1.2; letter-spacing: -0.6px;
    color: #ffffff; margin: 0;
}
.hero-title span { color: $hero_accent; }
.hero-sub { font-size: 13.5px; color: rgba(255,255,255,.66); margin-top: 8px; }
.hero-right { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
.hero-chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 999px;
    background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.16);
    color: rgba(255,255,255,.88); font-size: 11.5px; font-weight: 500;
    white-space: nowrap;
}
.hero-chip b { color: #ffffff; font-weight: 600; }

/* ---------- 模块标题 ---------- */
.sec {
    display: flex; align-items: baseline; gap: 10px;
    margin: 30px 0 12px 0; padding-bottom: 9px;
    border-bottom: 1px solid $hairline_soft;
}
.sec-num {
    font-size: 11px; font-weight: 600; letter-spacing: 1px;
    color: $stone; font-variant-numeric: tabular-nums;
}
.sec-txt { font-size: 19px; font-weight: 600; color: $ink; letter-spacing: -0.25px; }
.sec-tip { margin-left: auto; font-size: 12px; color: $steel; }

/* ---------- 图表卡片 ---------- */
div[data-testid="stPlotlyChart"] {
    background: $panel;
    border: 1px solid $hairline;
    border-radius: 12px;
    padding: 10px 12px 6px 12px;
    box-shadow: $shadow1;
    animation: fadeUp .5s ease-out both;
}

/* ---------- 筛选回显 chip ---------- */
.drill-chip {
    display: inline-block; padding: 3px 9px; margin: 0 6px 6px 0;
    border-radius: 6px; font-size: 12px; font-weight: 600;
    background: $tint_lavender; color: #391c57;
    border: 1px solid rgba(86,69,212,.18);
}

/* ---------- 提示条（Notion callout） ---------- */
.callout {
    display: flex; gap: 10px; align-items: flex-start;
    border-radius: 12px; padding: 13px 16px; margin: 12px 0;
    font-size: 13.5px; line-height: 1.55;
}
.callout .ic { font-size: 15px; line-height: 1.4; }
.callout.warn { background: $warn_bg; border: 1px solid $warn_border; color: $warn_text; }
.callout.ok   { background: $ok_bg;   border: 1px solid $ok_border;   color: $ok_text; }
.callout b { font-weight: 600; }

/* ---------- 侧边栏 ---------- */
section[data-testid="stSidebar"] {
    background: $surface;
    border-right: 1px solid $hairline;
}
section[data-testid="stSidebar"] .block-container,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 1.1rem; }
.sb-brand {
    display: flex; align-items: center; gap: 11px;
    background: $panel; border: 1px solid $hairline; border-radius: 12px;
    padding: 13px 14px; margin-bottom: 14px; box-shadow: $shadow1;
}
.sb-logo {
    width: 32px; height: 32px; border-radius: 8px; flex: 0 0 32px;
    background: $navy; color: #fff; font-size: 15px; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
}
.sb-name { font-size: 14px; font-weight: 600; color: $ink; line-height: 1.3; }
.sb-desc { font-size: 11px; color: $stone; letter-spacing: .3px; margin-top: 2px; }
.sb-label {
    font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;
    color: $stone; margin: 16px 0 6px 0;
}
section[data-testid="stSidebar"] label p { font-size: 12.5px !important; color: $steel !important; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { font-size: 11.5px; }

/* ---------- 控件外观 ---------- */
div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
div[data-testid="stDateInput"] div[data-baseweb="input"],
div[data-testid="stNumberInput"] div[data-baseweb="input"] {
    border-radius: 8px !important;
    border-color: $hairline_strong !important;
    background: $panel !important;
}
.stButton button, .stDownloadButton button {
    border-radius: 8px !important;
    border: 1px solid $hairline_strong !important;
    background: $panel !important;
    color: $ink !important;
    font-size: 13px !important; font-weight: 500 !important;
    padding: 7px 14px !important;
    box-shadow: none !important;
}
.stButton button:hover, .stDownloadButton button:hover {
    border-color: $ink !important; color: $ink !important;
}

/* ---------- 表格 ---------- */
div[data-testid="stDataFrame"] {
    border: 1px solid $hairline; border-radius: 12px; overflow: hidden;
    background: $panel; box-shadow: $shadow1;
}
div[data-testid="stMetric"] {
    background: $panel; border: 1px solid $hairline; border-radius: 12px;
    padding: 12px 16px; box-shadow: $shadow1;
}
div[data-testid="stMetric"] label p { font-size: 11.5px !important; color: $steel !important; }
div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 600; color: $ink; }
hr { border-color: $hairline_soft !important; }

/* ---------- 页脚 ---------- */
.foot {
    margin-top: 30px; padding-top: 14px; border-top: 1px solid $hairline_soft;
    font-size: 11.5px; color: $stone; display: flex; justify-content: space-between;
    flex-wrap: wrap; gap: 8px;
}

/* ---------- 动画 ---------- */
@keyframes fadeUp   { from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: none;} }
@keyframes fadeDown { from {opacity: 0; transform: translateY(-8px);}  to {opacity: 1; transform: none;} }
.hero { animation: fadeDown .45s ease-out both; }

/* ---------- 截图模式：隐藏侧栏、收窄画布 ---------- */
$shot_css
</style>
""")


def inject_css(t: dict, shot_mode: bool = False, zoom: float = 0.0) -> None:
    shot_css = ""
    if shot_mode:
        shot_css = 'section[data-testid="stSidebar"] { display:none !important; }'
        if zoom > 0:
            # 缩放画布：1258 / zoom 得到实际布局宽度，便于一屏截图
            shot_css += (
                f'.block-container {{ max-width: {int(1258 / zoom)}px !important;'
                f' zoom: {zoom}; }}'
            )
        else:
            shot_css += '.block-container { max-width: 1280px; }'
    st.markdown(CSS.substitute(shot_css=shot_css, **t), unsafe_allow_html=True)


def section(num: str, title: str, tip: str = "") -> None:
    st.markdown(
        f'<div class="sec"><span class="sec-num">{num}</span>'
        f'<span class="sec-txt">{title}</span>'
        f'<span class="sec-tip">{tip}</span></div>',
        unsafe_allow_html=True,
    )


def callout(kind: str, icon: str, html: str) -> None:
    st.markdown(
        f'<div class="callout {kind}"><span class="ic">{icon}</span><span>{html}</span></div>',
        unsafe_allow_html=True,
    )


# ============================================================ 图表统一风格
def style_fig(fig: go.Figure, t: dict, height: int = 320, legend: str | None = "top") -> go.Figure:
    """统一图表视觉：Notion 色板、细网格、无外框、hover 卡片化"""
    margin = dict(l=8, r=18, t=58, b=8)
    if legend == "top":
        margin["t"] = 74
    elif legend == "bottom":
        margin["b"] = 52

    fig.update_layout(
        template=t["plotly"],
        height=height,
        margin=margin,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[t["accent"], t["teal"], t["orange"], t["pink"], t["green"], t["link"]],
        font=dict(family=FONT_STACK, size=12, color=t["charcoal"]),
        title=dict(
            text=fig.layout.title.text, x=0, xanchor="left", y=0.97,
            font=dict(family=FONT_STACK, size=15, color=t["ink"]),
        ),
        hoverlabel=dict(
            bgcolor=t["panel"], bordercolor=t["hairline"],
            font=dict(family=FONT_STACK, color=t["ink"], size=12),
        ),
        hovermode="closest",
        showlegend=(legend is not None),
    )
    if legend == "top":
        fig.update_layout(legend=dict(
            orientation="h", yanchor="bottom", y=1.02, x=0,
            font=dict(size=11, color=t["steel"]), bgcolor="rgba(0,0,0,0)",
        ))
    elif legend == "bottom":
        fig.update_layout(legend=dict(
            orientation="h", yanchor="top", y=-0.16, x=0.5, xanchor="center",
            font=dict(size=10.5, color=t["steel"]), bgcolor="rgba(0,0,0,0)",
        ))
    elif legend == "right":
        fig.update_layout(
            legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.015,
                        xanchor="left", font=dict(size=11, color=t["charcoal"]),
                        bgcolor="rgba(0,0,0,0)", itemsizing="constant"),
            margin=dict(l=6, r=104, t=64, b=8),
        )
    else:
        fig.update_layout(showlegend=False)

    fig.update_xaxes(
        showgrid=False, linecolor=t["hairline"], tickfont=dict(color=t["steel"], size=11),
        automargin=True, zeroline=False,
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=t["hairline_soft"], gridwidth=1, zeroline=False,
        automargin=True, linecolor="rgba(0,0,0,0)",
        tickfont=dict(color=t["steel"], size=11),
    )
    # Notion 的图表不靠轴标题表达语义：语义交给卡片标题
    fig.update_xaxes(title_text=None)
    fig.update_yaxes(title_text=None)
    return fig


# ============================================================ 数值滚动卡片
KPI_TEMPLATE = Template("""
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; background: transparent; }
  body { font-family: Inter, -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; }
  .row { display:flex; gap:12px; width:100%; }
  .kpi {
    flex:1 1 0; min-width:0;
    background: $panel;
    border: 1px solid $hairline;
    border-radius: 12px;
    padding: 14px 16px 13px 16px;
    box-shadow: $shadow1;
    animation: fadeUp .55s ease-out both;
  }
  .kpi:nth-child(1) { animation-delay:.02s; }
  .kpi:nth-child(2) { animation-delay:.07s; }
  .kpi:nth-child(3) { animation-delay:.12s; }
  .kpi:nth-child(4) { animation-delay:.17s; }
  .kpi:nth-child(5) { animation-delay:.22s; }
  .kpi:nth-child(6) { animation-delay:.27s; }
  .kpi-top { display:flex; align-items:center; justify-content:space-between; gap:8px; }
  .kpi-icon {
    width: 26px; height: 26px; border-radius: 7px; flex: 0 0 26px;
    display:flex; align-items:center; justify-content:center;
    font-size: 13px; background: var(--tint); color: var(--icon);
  }
  .kpi-label {
    font-size: 10.5px; font-weight: 600; letter-spacing: .9px; text-transform: uppercase;
    color: $stone; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .kpi-value {
    font-size: 27px; font-weight: 600; color: $ink; letter-spacing: -0.7px;
    margin: 9px 0 4px 0; white-space: nowrap; overflow: hidden;
    font-variant-numeric: tabular-nums; line-height: 1.15;
  }
  .kpi-sub { font-size: 11.5px; color: $steel; white-space: nowrap;
             overflow: hidden; text-overflow: ellipsis; }
  @keyframes fadeUp { from {opacity:0; transform:translateY(10px);} to {opacity:1; transform:none;} }
</style></head>
<body>
  <div class="row">$blocks</div>
  <script>
    document.querySelectorAll('.kpi-value').forEach(function (el) {
      var target = parseFloat(el.dataset.target) || 0;
      var dec = parseInt(el.dataset.decimals) || 0;
      var pre = el.dataset.prefix || '';
      var suf = el.dataset.suffix || '';
      var dur = 1000, t0 = performance.now();
      function fmt(v) {
        return v.toLocaleString('zh-CN', { minimumFractionDigits: dec, maximumFractionDigits: dec });
      }
      function step(now) {
        var p = Math.min((now - t0) / dur, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = pre + fmt(target * eased) + suf;
        if (p < 1) { requestAnimationFrame(step); }
        else { el.textContent = pre + fmt(target) + suf; }
      }
      requestAnimationFrame(step);
    });
  </script>
</body></html>
""")


def kpi_cards(cards: list, t: dict, height: int = 128) -> None:
    """
    自绘 KPI 卡片行：st.iframe 内嵌 HTML/CSS/JS
    - 数值滚动动画（count-up）+ 卡片渐入
    - 预警项自动转红（DESIGN.md 的 semantic-error）
    """
    blocks = []
    for c in cards:
        accent = t["red"] if c.get("alert") else c.get("color", t["accent"])
        tint = c.get("tint", t["tint_lavender"])
        blocks.append(f"""
        <div class="kpi" style="--tint:{tint};--icon:{accent}">
          <div class="kpi-top">
            <div class="kpi-label">{c['label']}</div>
            <div class="kpi-icon">{c.get('icon', '•')}</div>
          </div>
          <div class="kpi-value"
               data-target="{c['value']}"
               data-prefix="{c.get('prefix', '')}"
               data-suffix="{c.get('suffix', '')}"
               data-decimals="{c.get('decimals', 0)}"
               style="color:{accent}">--</div>
          <div class="kpi-sub">{c['sub']}</div>
        </div>""")

    html = KPI_TEMPLATE.substitute(
        panel=t["panel"], hairline=t["hairline"], shadow1=t["shadow1"],
        ink=t["ink"], stone=t["stone"], steel=t["steel"],
        blocks="".join(blocks),
    )
    if hasattr(st, "iframe"):                # Streamlit >= 1.66 的新接口
        st.iframe(html, height=height)
    else:                                    # 兼容旧版 Streamlit
        import streamlit.components.v1 as components
        components.html(html, height=height, scrolling=False)


# ============================================================ 筛选（侧边栏 / 截图模式默认值）
def _default_filters(df: pd.DataFrame) -> dict:
    return dict(
        start=df["消费日期"].min().date(),
        end=df["消费日期"].max().date(),
        granularity="按周",
        colleges=sorted(df["学院"].unique()),
        grades=sorted(df["年级"].unique()),
        cats=[c for c in CAT_COLOR if c in df["消费类别"].unique()],
        payments=sorted(df["支付方式"].unique()),
        drop_refund=True,
        amount_threshold=100,
        month_budget=800,
        live_on=False,
        live_interval=3,
    )


def build_sidebar(df: pd.DataFrame) -> dict:
    with st.sidebar:
        st.markdown(
            '<div class="sb-brand"><div class="sb-logo">校</div>'
            '<div><div class="sb-name">看板控制台</div>'
            '<div class="sb-desc">Campus Consumption</div></div></div>',
            unsafe_allow_html=True,
        )
        st.caption("筛选条件同步作用于全部图表")

        st.markdown('<div class="sb-label">时间范围</div>', unsafe_allow_html=True)
        d_min, d_max = df["消费日期"].min().date(), df["消费日期"].max().date()
        start, end = st.date_input(
            "消费日期区间",
            value=(d_min, d_max),
            min_value=d_min,
            max_value=d_max,
            key="date_range",
        )
        if isinstance(start, tuple):          # 兼容只选一天的情况
            start, end = start[0], start[-1]

        granularity = st.segmented_control(
            "趋势粒度", ["按日", "按周", "按月"], default="按周", key="gran"
        ) or "按周"

        st.markdown('<div class="sb-label">维度筛选</div>', unsafe_allow_html=True)

        def _pills(label: str, options: list, default: list, key: str) -> list:
            """多选胶囊：原生支持换行，比下拉多选框更适合侧边栏"""
            val = st.pills(
                label, options, selection_mode="multi", default=default,
                key=key, wrap=True,
            )
            return list(val) if val else []

        colleges = _pills("学院", sorted(df["学院"].unique()),
                          sorted(df["学院"].unique()), "f_college")
        grades = _pills("年级", sorted(df["年级"].unique()),
                        sorted(df["年级"].unique()), "f_grade")
        cats = _pills("消费类别", list(CAT_COLOR.keys()),
                      [c for c in CAT_COLOR if c in df["消费类别"].unique()], "f_cat")
        payments = _pills("支付方式", sorted(df["支付方式"].unique()),
                          sorted(df["支付方式"].unique()), "f_pay")

        drop_refund = st.toggle("排除退款记录", value=True, key="f_refund",
                                help="退款记录不计入消费额统计")

        st.markdown('<div class="sb-label">预警阈值</div>', unsafe_allow_html=True)
        amount_threshold = st.slider(
            "单笔金额预警阈值（元）", 30, 300, 100, step=10, key="th_amount"
        )
        month_budget = st.number_input(
            "月人均消费预算（元）", 300, 3000, 800, step=50, key="th_budget"
        )

        st.markdown('<div class="sb-label">实时数据源</div>', unsafe_allow_html=True)
        live_on = st.toggle("开启实时刷新（模拟接口数据）", value=False, key="live_on")
        live_interval = st.slider("刷新间隔（秒）", 1, 10, 3, key="live_interval")

        st.divider()
        st.caption(f"数据源：data/校园消费数据.csv ｜ 共 {len(df):,} 条记录")
        st.caption("亮 / 暗主题：修改 .streamlit/config.toml 中 [theme] 的 base")

    return dict(
        start=start,
        end=end,
        granularity=granularity,
        colleges=colleges,
        grades=grades,
        cats=cats,
        payments=payments,
        drop_refund=drop_refund,
        amount_threshold=amount_threshold,
        month_budget=month_budget,
        live_on=live_on,
        live_interval=live_interval,
    )


@st.cache_data(show_spinner="正在生成 Excel 汇总 ...")
def build_excel(rows: pd.DataFrame, cat: pd.DataFrame) -> bytes:
    """把明细 + 类别汇总写成多 sheet Excel，结果缓存，避免每次重跑都重写大表"""
    from io import BytesIO
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        rows.to_excel(writer, index=False, sheet_name="明细数据")
        cat.to_excel(writer, index=False, sheet_name="类别汇总")
    return buf.getvalue()


def apply_filters(df: pd.DataFrame, f: dict) -> pd.DataFrame:
    d = df[
        (df["消费日期"].dt.date >= f["start"]) & (df["消费日期"].dt.date <= f["end"])
    ].copy()
    if f["colleges"]:
        d = d[d["学院"].isin(f["colleges"])]
    if f["grades"]:
        d = d[d["年级"].isin(f["grades"])]
    if f["cats"]:
        d = d[d["消费类别"].isin(f["cats"])]
    if f["payments"]:
        d = d[d["支付方式"].isin(f["payments"])]
    if f["drop_refund"]:
        d = d[d["是否退款"] == "否"]
    return d


# ============================================================ 主流程
def main() -> None:
    if not os.path.exists(DATA_PATH):
        st.error(
            "未找到数据文件 `data/校园消费数据.csv`。\n\n"
            "请先在项目目录下运行：`python generate_data.py`"
        )
        st.stop()

    # ---------- 截图模式（文档配图用，正常浏览时可忽略）
    qp = st.query_params
    shot_mode = qp.get("shot", "") == "full"
    only = qp.get("mod", "")
    force_live = qp.get("live", "") == "1"
    try:
        shot_zoom = float(qp.get("zoom", "0") or 0)
    except ValueError:
        shot_zoom = 0.0

    def part(n: str) -> bool:
        return (not only) or only == n

    raw = load_data(DATA_PATH, os.path.getmtime(DATA_PATH))
    if shot_mode:
        # 截图模式：用固定筛选值 + 隐藏侧边栏，保证每次出图一致
        f = _default_filters(raw)
    else:
        f = build_sidebar(raw)
    if force_live:
        f["live_on"] = True

    # 主题跟随 .streamlit/config.toml 的 [theme] 配置（亮色 / 暗色均可）
    t = detect_theme()
    inject_css(t, shot_mode, shot_zoom)

    df = apply_filters(raw, f)

    if df.empty:
        st.warning("当前筛选条件下没有数据，请放宽筛选范围。")
        st.stop()

    # 退款率按「不含退款过滤」的同一筛选条件计算，否则排除退款后永远为 0
    df_with_refund = apply_filters(raw, {**f, "drop_refund": False})

    # -------------------------------------------------- 页头（Notion navy hero）
    st.markdown(
        f"""
        <div class="hero">
          <span class="hero-dot d1"></span><span class="hero-dot d2"></span>
          <span class="hero-dot d3"></span><span class="hero-dot d4"></span>
          <div style="display:flex;gap:24px;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;">
            <div>
              <div class="hero-eyebrow">Experiment 02 · Data Dashboard</div>
              <div class="hero-title">校园<span>消费</span>数据看板</div>
              <div class="hero-sub">Campus Consumption Dashboard ｜ 2025 秋季学期 ｜ 19 周 · 全校 12 个学院</div>
            </div>
            <div class="hero-right">
              <span class="hero-chip">记录 <b>{len(df):,}</b> 条</span>
              <span class="hero-chip">学生 <b>{df['学生编号'].nunique():,}</b> 人</span>
              <span class="hero-chip">更新 <b>{dt.datetime.now().strftime('%m-%d %H:%M')}</b></span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------- 指标计算
    total_amt = df["消费金额"].sum()
    order_cnt = len(df)
    avg_amt = df["消费金额"].mean()
    stu_cnt = df["学生编号"].nunique()
    avg_score = df["满意度评分"].mean()
    refund_rate = (df_with_refund["是否退款"] == "是").mean() * 100
    # 环比：只对比「完整自然月」，避免半月与整月相比造成假跌
    day_cnt = df.groupby("月标签")["日期"].nunique()
    full_months = sorted(day_cnt[day_cnt >= 25].index.tolist())
    month_sum = df.groupby("月标签")["消费金额"].sum()
    full_sum = month_sum[month_sum.index.isin(full_months)].sort_index()
    if len(full_sum) >= 2:
        mom = (full_sum.iloc[-1] / full_sum.iloc[-2] - 1) * 100
        prev_lab = f"{int(full_sum.index[-2][-2:])}月"
        cur_lab = f"{int(full_sum.index[-1][-2:])}月"
        mom_txt = f"环比 {prev_lab}→{cur_lab} {mom:+.1f}%"
    else:
        mom_txt = "完整月不足两个，暂不计算环比"

    # 预警：月人均消费 = 当月消费总额 / 当月活跃学生数
    m_agg = df.groupby("月标签").agg(
        总额=("消费金额", "sum"), 人数=("学生编号", "nunique")
    )
    month_per_capita = m_agg["总额"] / m_agg["人数"]
    over_budget = month_per_capita[month_per_capita > f["month_budget"]]

    # 预警：超过单笔阈值的订单
    over_amount = df[df["消费金额"] > f["amount_threshold"]]
    over_cnt = len(over_amount)
    over_share = over_cnt / order_cnt * 100

    # 类别汇总（模块二环形图 + 导出工作表共用）
    cat_amt = (
        df.groupby("消费类别", as_index=False)["消费金额"].sum()
        .sort_values("消费金额", ascending=False)
    )

    # -------------------------------------------------- 模块一：数据概览区
    if part("1"):
        section("01", "数据概览", "核心指标一屏总览 · 数值滚动入场")
        kpi_cards(
            [
                dict(label="总消费额", value=round(float(total_amt), 2), prefix="¥",
                     decimals=0, sub=mom_txt, color=t["accent"], tint=t["tint_lavender"],
                     icon="¥"),
                dict(label="订单总量", value=order_cnt, suffix=" 笔",
                     decimals=0, sub=f"日均 {order_cnt / max(df['日期'].nunique(), 1):.0f} 笔",
                     color=t["ink"], tint=t["tint_sky"], icon="▦"),
                dict(label="单笔均价", value=round(float(avg_amt), 2), prefix="¥",
                     decimals=1, sub="客单价水平", color=t["ink"], tint=t["tint_mint"],
                     icon="≈"),
                dict(label="覆盖学生", value=stu_cnt, suffix=" 人", decimals=0,
                     sub=f"学期人均 ¥{total_amt / max(stu_cnt, 1):.1f}",
                     color=t["ink"], tint=t["tint_yellow"], icon="◉"),
                dict(label="平均满意度", value=round(float(avg_score), 2), suffix=" 分",
                     decimals=2, sub="满分 5 分", color=t["ink"], tint=t["tint_rose"],
                     icon="★"),
                dict(label=f"超额订单 >¥{f['amount_threshold']}", value=over_cnt,
                     suffix=" 笔", decimals=0,
                     sub=f"占总量 {over_share:.1f}%", color=t["orange"],
                     tint=t["tint_peach"], icon="!", alert=over_cnt > 0),
            ],
            t,
        )

        # 预警横幅（Notion callout 风格）
        if len(over_budget) > 0:
            callout(
                "warn", "⚠",
                "<b>预算预警</b>：" + "、".join(
                    f"{m} 人均 ¥{v:.0f}" for m, v in over_budget.items()
                ) + f" 已超过月人均预算 ¥{f['month_budget']}，建议关注消费结构。",
            )
        else:
            callout(
                "ok", "✓",
                f"全部月份人均消费均控制在预算 ¥{f['month_budget']} 以内"
                f"（最高 {month_per_capita.max():.0f} 元）。",
            )

    # -------------------------------------------------- 模块二：维度统计区
    if part("2"):
        section("02", "维度统计", "看结构 · 看对比 · 看排名（柱状图支持点击联动）")
        c1, c2 = st.columns([1, 1.35], gap="medium")

        with c1:
            fig_pie = px.pie(
                cat_amt, names="消费类别", values="消费金额", hole=0.52,
                color="消费类别", color_discrete_map=CAT_COLOR,
            )
            _share = cat_amt["消费金额"] / cat_amt["消费金额"].sum() * 100
            fig_pie.update_traces(
                text=[f"{v:.1f}%" if v >= 5 else "" for v in _share],
                textposition="inside", textinfo="text",
                insidetextfont=dict(color="#ffffff", size=11.5),
                marker=dict(line=dict(color=t["panel"], width=2)),
                hovertemplate="<b>%{label}</b><br>金额 ¥%{value:,.2f}<br>占比 %{percent}<extra></extra>",
            )
            fig_pie.update_layout(title="消费类别占比结构（环形图）")
            st.plotly_chart(style_fig(fig_pie, t, 310, legend="right"), key="pie_cat",
                            config={"displayModeBar": False})

        with c2:
            col_amt = (
                df.groupby("学院", as_index=False)
                .agg(消费金额=("消费金额", "sum"), 订单数=("订单编号", "count"))
                .sort_values("消费金额", ascending=False)
            )
            col_amt["人均消费"] = col_amt["消费金额"] / col_amt["订单数"]
            fig_bar = px.bar(
                col_amt, x="学院", y="消费金额",
                text=col_amt["消费金额"].map(lambda v: f"{v / 1000:.1f}k"),
                color="消费金额", color_continuous_scale=[t["tint_lavender"], t["accent"]],
            )
            fig_bar.update_traces(
                marker_line_width=0, textposition="outside",
                hovertemplate="<b>%{x}</b><br>消费额 ¥%{y:,.2f}<extra></extra>",
            )
            fig_bar.update_layout(
                title="各学院消费额对比（点击柱子可下钻）", coloraxis_showscale=False
            )
            fig_bar.update_yaxes(range=[0, col_amt["消费金额"].max() * 1.18])
            ev = st.plotly_chart(
                style_fig(fig_bar, t, 310),
                key="bar_college",
                on_select="rerun",
                selection_mode="points",
                config={"displayModeBar": False},
            )
            # --- 图表联动：点击柱子 → 记录被选中的学院
            try:
                pts = ev["selection"]["points"]
                if pts:
                    st.session_state["drill_college"] = pts[0]["x"]
            except (KeyError, IndexError, TypeError):
                pass

        # 下钻状态条
        drill = st.session_state.get("drill_college")
        if drill:
            dc1, dc2 = st.columns([4, 1], vertical_alignment="center")
            with dc1:
                st.markdown(
                    f'<span class="drill-chip">🔎 已下钻学院：{drill}</span>'
                    f'<span class="drill-chip">联动范围：趋势图 + 明细表</span>',
                    unsafe_allow_html=True,
                )
            with dc2:
                if st.button("清除下钻", key="clear_drill"):
                    st.session_state.pop("drill_college", None)
                    st.rerun()

        # 商户排行榜 + 金额分档
        c3, c4 = st.columns([1.35, 1], gap="medium")
        with c3:
            top_merchant = (
                df.groupby("商户", as_index=False)["消费金额"].sum()
                .sort_values("消费金额", ascending=True).tail(10)
            )
            fig_rank = px.bar(
                top_merchant, x="消费金额", y="商户", orientation="h",
                text=top_merchant["消费金额"].map(lambda v: f"¥{v:,.0f}"),
                color="消费金额", color_continuous_scale=[t["tint_lavender"], t["accent"]],
            )
            fig_rank.update_traces(
                textposition="outside", cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>消费额 ¥%{x:,.2f}<extra></extra>",
            )
            fig_rank.update_layout(
                title="商户消费额 TOP 10 排行榜", coloraxis_showscale=False, showlegend=False
            )
            # 右侧留白，避免条末金额文字被裁切
            fig_rank.update_xaxes(range=[0, top_merchant["消费金额"].max() * 1.22])
            st.plotly_chart(style_fig(fig_rank, t, 350), key="rank_merchant",
                            config={"displayModeBar": False})

        with c4:
            band = (
                df["金额分档"].value_counts().reindex(
                    ["10元以下", "10-30元", "30-60元", "60-100元", "100元以上"]
                ).fillna(0).astype(int)
            )
            band_df = pd.DataFrame({"金额分档": band.index, "订单数": band.values})
            fig_band = px.bar(
                band_df, x="金额分档", y="订单数", text="订单数",
                color="订单数", color_continuous_scale=[t["tint_mint"], t["teal"]],
            )
            fig_band.update_traces(textposition="outside", marker_line_width=0)
            fig_band.update_layout(
                title="单笔金额分布（金额分档）", coloraxis_showscale=False
            )
            fig_band.update_yaxes(range=[0, band_df["订单数"].max() * 1.16])
            st.plotly_chart(style_fig(fig_band, t, 350), key="band_dist",
                            config={"displayModeBar": False})

    # 下钻数据的子集（仅作用于趋势 + 明细）；截图/无联动时即全量
    drill = st.session_state.get("drill_college")
    df_drill = df[df["学院"] == drill] if drill else df

    # -------------------------------------------------- 模块三：趋势分析区
    if part("3"):
        section("03", "趋势分析", f"当前粒度：{f['granularity']}（可在左侧切换）")

        gran_col = {"按日": "日期", "按周": "周序", "按月": "月标签"}[f["granularity"]]
        trend = (
            df_drill.groupby(gran_col, as_index=False)
            .agg(消费金额=("消费金额", "sum"), 订单数=("订单编号", "count"))
            .sort_values(gran_col)
        )
        if f["granularity"] == "按周":
            trend["x"] = trend["周序"].map(lambda w: f"第{w}周")
        else:
            trend["x"] = trend[gran_col].astype(str)

        fig_line = px.line(
            trend, x="x", y="消费金额", markers=True,
            color_discrete_sequence=[t["accent"]],
        )
        fig_line.update_traces(
            line=dict(width=2.4, color=t["accent"]),
            marker=dict(size=6.5, line=dict(width=2, color=t["panel"])),
            hovertemplate="%{x}<br>消费额 ¥%{y:,.2f}<extra></extra>",
        )
        fig_line.update_layout(title="消费额变化趋势", hovermode="x unified")
        fig_line.update_xaxes(type="category", title="")   # 避免 "2025-09" 被当成日期轴
        st.plotly_chart(style_fig(fig_line, t, 350, legend=None), key="trend_line",
                        config={"displayModeBar": False})

        c5, c6 = st.columns([1, 1], gap="medium")
        with c5:
            area = (
                df_drill.groupby(["月标签", "消费类别"])["消费金额"].sum().reset_index()
            )
            fig_area = px.area(
                area, x="月标签", y="消费金额", color="消费类别",
                color_discrete_map=CAT_COLOR,
            )
            fig_area.update_layout(title="各类别月度消费构成（堆叠面积图）")
            fig_area.update_xaxes(type="category", title="")
            st.plotly_chart(style_fig(fig_area, t, 340, legend="bottom"), key="trend_area",
                            config={"displayModeBar": False})

        with c6:
            pivot = (
                df.pivot_table(index="消费时段", columns="星期", values="订单编号",
                               aggfunc="count", fill_value=0)
                .reindex(index=SLOT_ORDER, columns=WEEKDAY_ORDER)
            )
            fig_heat = px.imshow(
                pivot, text_auto=True, aspect="auto",
                color_continuous_scale=[
                    t["surface_soft"], t["tint_lavender"], t["accent"],
                ],
                labels=dict(x="星期", y="消费时段", color="订单数"),
            )
            fig_heat.update_traces(
                hovertemplate="%{y} · %{x}<br>订单数 %{z}<extra></extra>"
            )
            fig_heat.update_layout(title="消费时段 × 星期 热力图（订单密度）",
                                   coloraxis_showscale=False)
            fig_heat = style_fig(fig_heat, t, 320)
            fig_heat.update_xaxes(title_text="星期")
            fig_heat.update_yaxes(title_text="消费时段", showgrid=False)
            st.plotly_chart(fig_heat, key="heat", config={"displayModeBar": False})

    # -------------------------------------------------- 05 多维度分析
    if part("4"):
        section("04", "多维度分析", "雷达图看结构差异 · 仪表盘看预算健康度")
        c7, c8 = st.columns([1.3, 1], gap="medium")

        with c7:
            radar = (
                df.pivot_table(index="学院", columns="消费类别", values="消费金额",
                               aggfunc="sum", fill_value=0)
            )
            radar_share = radar.div(radar.sum(axis=1), axis=0) * 100
            palette = [t["accent"], t["teal"], t["orange"], t["pink"], t["link"]]
            fig_radar = go.Figure()
            for i, college in enumerate(radar_share.index):
                vals = radar_share.loc[college]
                color = palette[i % len(palette)]
                fig_radar.add_trace(
                    go.Scatterpolar(
                        r=list(vals.values) + [vals.values[0]],
                        theta=list(vals.index) + [vals.index[0]],
                        name=college, fill="toself",
                        fillcolor=hex_rgba(color, 0.09),     # 淡填充，5 条线叠加也不糊
                        line=dict(width=2, color=color),
                        hovertemplate="<b>%{theta}</b><br>占比 %{r:.1f}%<extra></extra>",
                    )
                )
            fig_radar.update_layout(
                title="各学院消费结构雷达图（类别占比 %）",
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(showline=False, gridcolor=t["hairline_soft"],
                                    showticklabels=False),  # 刻度数字会压住类别名，隐藏
                    angularaxis=dict(gridcolor=t["hairline_soft"], linecolor=t["hairline"],
                                     tickfont=dict(size=11, color=t["charcoal"])),
                ),
            )
            st.plotly_chart(style_fig(fig_radar, t, 400, legend="bottom"), key="radar",
                            config={"displayModeBar": False})

        with c8:
            exec_rate = month_per_capita.max() / f["month_budget"] * 100
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=float(min(exec_rate, 200)),
                    number=dict(suffix="%", valueformat=".1f",
                                font=dict(size=36, color=t["ink"])),
                    title=dict(text="预算执行率（峰值月）",
                               font=dict(size=13, color=t["steel"])),
                    gauge=dict(
                        axis=dict(range=[0, 200], tickvals=[50, 100, 150],
                                  ticksuffix="%", tickfont=dict(color=t["stone"], size=10)),
                        bar=dict(color=t["accent"], thickness=0.34),
                        bgcolor="rgba(0,0,0,0)",
                        borderwidth=0,
                        steps=[
                            dict(range=[0, 80], color=hex_rgba(t["green"], 0.16)),
                            dict(range=[80, 100], color=hex_rgba(t["yellow"], 0.30)),
                            dict(range=[100, 200], color=hex_rgba(t["red"], 0.16)),
                        ],
                        threshold=dict(line=dict(color=t["red"], width=4),
                                       thickness=0.80, value=100),
                    ),
                    domain=dict(x=[0.02, 0.98], y=[0.0, 0.92]),
                )
            )
            st.plotly_chart(style_fig(fig_gauge, t, 400, legend=None), key="gauge",
                            config={"displayModeBar": False})

    # -------------------------------------------------- 06 扩展1：实时流水
    if part("5") and f["live_on"]:
        section("05", "实时数据流", f"每 {f['live_interval']} 秒自动拉取一次（模拟接口数据源）")

        def push_live_row(back_seconds: int = 0) -> dict:
            """模拟一条实时上报的消费记录（back_seconds 用于生成历史时间戳）"""
            cat = np.random.choice(list(CAT_COLOR.keys()))
            mu, sigma = {
                "食堂餐饮": (2.60, 0.40), "超市便利店": (2.95, 0.50),
                "文具图书": (3.30, 0.55), "交通出行": (1.70, 0.55),
                "娱乐休闲": (3.45, 0.60), "快递服务": (1.15, 0.45),
            }[cat]
            ts = dt.datetime.now() - dt.timedelta(seconds=back_seconds)
            return {
                "时间": ts.strftime("%H:%M:%S"),
                "消费类别": cat,
                "学院": np.random.choice(sorted(raw["学院"].unique())),
                "消费金额": round(float(np.random.lognormal(mu, sigma)), 2),
                "支付方式": np.random.choice(["校园卡", "微信", "支付宝", "银行卡"]),
            }

        # 首次进入时先铺满一屏，避免刚打开时表格是空的
        if "live_rows" not in st.session_state:
            st.session_state["live_rows"] = [
                push_live_row(back_seconds=(8 - i) * 12) for i in range(8)
            ]
            st.session_state["live_tick"] = 0

        @st.fragment(run_every=f"{f['live_interval']}s")
        def live_panel() -> None:
            # 每次刷新：新增一条流水，并推进轮播指针
            st.session_state["live_tick"] = st.session_state.get("live_tick", 0) + 1
            st.session_state["live_rows"].insert(0, push_live_row())
            del st.session_state["live_rows"][8:]
            rows = st.session_state["live_rows"]

            lc1, lc2 = st.columns([1.6, 1], gap="medium")
            with lc1:
                st.dataframe(
                    pd.DataFrame(rows),
                    hide_index=True,
                    height=300,
                    column_config={
                        "消费金额": st.column_config.NumberColumn("消费金额", format="¥%.2f"),
                    },
                )
            with lc2:
                # 自动轮播：每刷新一次切换一个展示维度
                tick = st.session_state.get("live_tick", 0)
                cats = list(CAT_COLOR.keys())
                focus = cats[tick % len(cats)]
                sub = df[df["消费类别"] == focus]
                st.markdown(f"#### 轮播关注：{focus}")
                st.caption(f"第 {tick} 次刷新自动切换展示维度")
                st.metric("该类目消费额", f"¥{sub['消费金额'].sum():,.0f}",
                          help="随轮播自动切换类别")
                st.metric("该类目订单数", f"{len(sub):,} 笔")
                st.metric("该类目客单价", f"¥{sub['消费金额'].mean():.2f}" if len(sub) else "—")

        live_panel()

    # -------------------------------------------------- 模块四：明细数据区
    if part("6"):
        section("06", "明细数据", "支持排序、导出；超额订单自动打标")

        detail = df_drill.copy()
        detail["预警"] = np.where(
            detail["消费金额"] > f["amount_threshold"], "超额", ""
        )
        detail = detail.sort_values("消费日期", ascending=False)

        show_cols = [
            "订单编号", "日期", "星期", "消费时刻", "消费时段", "学生编号", "学院",
            "年级", "消费类别", "商户", "支付方式", "消费金额", "满意度评分", "预警",
        ]
        # 数据量大时只渲染最近若干条，保证页面流畅（完整数据走导出）
        DISPLAY_LIMIT = 1200
        detail_show = detail.head(DISPLAY_LIMIT)
        st.dataframe(
            detail_show[show_cols],
            hide_index=True,
            height=380,
            column_config={
                "消费金额": st.column_config.NumberColumn("消费金额", format="¥%.2f"),
                "满意度评分": st.column_config.NumberColumn("满意度评分", format="%d / 5"),
                "预警": st.column_config.TextColumn("预警", width="small"),
            },
        )
        if len(detail) > DISPLAY_LIMIT:
            st.caption(
                f"为保证页面流畅，表格仅渲染最近 {DISPLAY_LIMIT:,} 条；"
                f"当前筛选共 {len(detail):,} 条，完整数据请使用下方导出按钮。"
            )

        # -------------------------------------------------- 扩展4：导出
        e1, e2, e3 = st.columns([1, 1, 2], gap="small")
        csv_bytes = detail[show_cols].to_csv(index=False).encode("utf-8-sig")
        with e1:
            st.download_button(
                "导出明细 CSV", data=csv_bytes,
                file_name=f"校园消费明细_{dt.date.today()}.csv",
                mime="text/csv", key="dl_csv",
            )
        with e2:
            st.download_button(
                "导出汇总 Excel", data=build_excel(detail[show_cols], cat_amt),
                file_name=f"校园消费汇总_{dt.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_xlsx",
            )
        with e3:
            st.caption(
                f"当前筛选：{f['start']} ~ {f['end']} ｜ 学院 {len(f['colleges'])} 个 ｜ "
                f"记录 {len(detail):,} 条 ｜ 合计 ¥{detail['消费金额'].sum():,.2f} ｜ "
                f"退款率 {refund_rate:.1f}%"
            )

    # -------------------------------------------------- 页脚（单模块截图时不渲染）
    if only:
        return
    st.markdown(
        '<div class="foot">'
        '<span>实验2 数据看板的设计与实现 ｜ Streamlit + Pandas + Plotly</span>'
        '<span>视觉规范：awesome-design-md · notion/DESIGN.md ｜ 数据为课程模拟数据</span>'
        '</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
