# -*- coding: utf-8 -*-
"""
实验2 数据看板 —— 模拟数据生成与预处理脚本
=====================================================
功能：
  1. 生成「校园消费」业务场景的模拟原始数据（故意注入脏数据，模拟真实采集情况）
  2. 对原始数据做基础预处理：去重、处理缺失值、剔除异常值、类型与维度规范化
  3. 输出三个文件：
       data/校园消费原始数据.xlsx   —— 未清洗的原始数据（用于报告说明清洗前后对比）
       data/校园消费原始数据.csv    —— 同上，CSV 版
       data/校园消费数据.csv        —— 清洗后、可直接用于可视化的分析底表

运行： python generate_data.py
"""

import os
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- 全局配置
SEED = 20250901
RNG = np.random.default_rng(SEED)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 业务维度定义
COLLEGES = ["计算机学院", "机械工程学院", "经济管理学院", "外国语学院", "艺术设计学院"]
COLLEGE_WEIGHT = [0.28, 0.24, 0.20, 0.15, 0.13]

GRADES = ["2022级", "2023级", "2024级", "2025级"]
GRADE_WEIGHT = [0.20, 0.26, 0.28, 0.26]

# 消费类别：名称 -> (金额对数正态 mu, sigma, 权重)
# mu/sigma 用于拟合各类别的真实客单价，权重用于拟合各类别的下单频次
CATEGORIES = {
    "食堂餐饮": (2.60, 0.40, 0.48),   # 客单价 ~14 元，频次最高
    "超市便利店": (2.95, 0.50, 0.20),  # 客单价 ~20 元
    "文具图书": (3.30, 0.55, 0.07),   # 客单价 ~29 元
    "交通出行": (1.70, 0.55, 0.11),   # 客单价 ~6 元，高频小额
    "娱乐休闲": (3.45, 0.60, 0.06),   # 客单价 ~35 元，低频大额
    "快递服务": (1.15, 0.45, 0.08),   # 客单价 ~3 元
}
CAT_NAMES = list(CATEGORIES.keys())
CAT_WEIGHT = [CATEGORIES[c][2] for c in CAT_NAMES]

# 每个类别对应的商户（真实场景里食堂、超市会有多个点位）
MERCHANTS = {
    "食堂餐饮": ["第一食堂", "第二食堂", "第三食堂", "清真餐厅", "教工餐厅"],
    "超市便利店": ["校园教育超市", "西门便利店", "北苑便利店"],
    "文具图书": ["学苑书店", "文具之家", "打印复印中心"],
    "交通出行": ["校园班车", "共享单车", "地铁出行", "网约车"],
    "娱乐休闲": ["校电影院", "大学生活动中心", "体育馆", "桌游社"],
    "快递服务": ["菜鸟驿站", "京东驿站", "顺丰代收点"],
}

PAYMENTS = ["校园卡", "微信", "支付宝", "银行卡"]
PAY_WEIGHT = [0.52, 0.26, 0.18, 0.04]

# 各学院的消费偏好系数：让不同学院在「消费结构」上呈现真实差异，
# 这样雷达图（学院 × 类别占比）才有分析价值
COLLEGE_CAT_BIAS = {
    "计算机学院": {"文具图书": 1.7, "娱乐休闲": 1.3, "食堂餐饮": 0.92, "快递服务": 1.2},
    "机械工程学院": {"食堂餐饮": 1.15, "交通出行": 1.15, "娱乐休闲": 0.75},
    "经济管理学院": {"娱乐休闲": 1.55, "超市便利店": 1.25, "食堂餐饮": 0.88},
    "外国语学院": {"文具图书": 1.35, "快递服务": 1.45, "娱乐休闲": 1.10},
    "艺术设计学院": {"文具图书": 1.9, "快递服务": 1.15, "食堂餐饮": 0.85, "交通出行": 0.7},
}

# 时段定义：名称 -> (起始小时, 结束小时, 权重)
SLOTS = {
    "早餐": (6, 9, 0.12),
    "午餐": (11, 13, 0.30),
    "晚餐": (17, 19, 0.28),
    "夜宵": (21, 23, 0.12),
    "其他": (9, 21, 0.18),
}
SLOT_NAMES = list(SLOTS.keys())
SLOT_WEIGHT = [SLOTS[s][2] for s in SLOT_NAMES]

# 学期区间：2025 秋季学期（19 周）
SEMESTER_START = pd.Timestamp("2025-09-01")
SEMESTER_END = pd.Timestamp("2026-01-11")

# 各月份的整体消费景气系数（模拟开学季低、期末季高的消费节奏）
MONTH_FACTOR = {
    9: 0.85,   # 开学购置高峰后回落
    10: 1.00,  # 国庆后稳定
    11: 1.08,  # 双十一带动超市消费
    12: 1.15,  # 期末季外卖/娱乐/夜宵上升
    1: 1.22,   # 考前冲刺
}


# ---------------------------------------------------------------- 工具函数
def pick(arr, weights, size):
    """按权重抽样"""
    return RNG.choice(arr, size=size, p=np.asarray(weights, dtype=float) / np.sum(weights))


def random_date(size):
    """在学期区间内随机取日期"""
    total_days = (SEMESTER_END - SEMESTER_START).days
    offsets = RNG.integers(0, total_days + 1, size=size)
    return SEMESTER_START + pd.to_timedelta(offsets, unit="D")


def random_time_in_slot(slot):
    """按小时权重生成具体时刻"""
    lo, hi, _ = (6, 9, 1) if slot not in SLOTS else SLOTS[slot]
    hour = int(RNG.integers(lo, hi))
    minute = int(RNG.integers(0, 60))
    return f"{hour:02d}:{minute:02d}"


def build_amount(category, month, dayofweek):
    """生成一条消费金额：类别均值 + 月度景气 + 周末效应 + 随机扰动"""
    mu, sigma, _ = CATEGORIES[category]
    base = float(RNG.lognormal(mean=mu, sigma=sigma))

    factor = MONTH_FACTOR.get(int(month), 1.0)

    # 周末：食堂下降、娱乐上升
    if dayofweek >= 5:
        if category == "食堂餐饮":
            factor *= 0.82
        elif category in ("娱乐休闲", "超市便利店"):
            factor *= 1.30

    amount = base * factor
    return round(max(amount, 1.0), 2)


# ---------------------------------------------------------------- 生成主体数据
def generate_records(n=2000):
    dates = random_date(n)

    df = pd.DataFrame({
        "消费日期": dates,
        "学院": pick(COLLEGES, COLLEGE_WEIGHT, n),
        "年级": pick(GRADES, GRADE_WEIGHT, n),
        "支付方式": pick(PAYMENTS, PAY_WEIGHT, n),
    })

    # 消费类别依赖学院：先定学院，再按该学院的偏好系数抽样类别
    college_arr = df["学院"].to_numpy()
    cats = np.empty(n, dtype=object)
    for college in COLLEGES:
        mask = college_arr == college
        k = int(mask.sum())
        if k == 0:
            continue
        bias = COLLEGE_CAT_BIAS.get(college, {})
        w = np.array([CATEGORIES[c][2] * bias.get(c, 1.0) for c in CAT_NAMES])
        cats[mask] = RNG.choice(CAT_NAMES, size=k, p=w / w.sum())
    df["消费类别"] = cats

    # 时段：早/午/晚餐与餐饮强相关，做一点关联性让数据更"真"
    slots = []
    for cat in df["消费类别"]:
        if cat == "食堂餐饮":
            slots.append(pick(["早餐", "午餐", "晚餐", "其他"], [0.22, 0.38, 0.33, 0.07], 1)[0])
        elif cat == "娱乐休闲":
            slots.append(pick(["晚餐", "夜宵", "其他"], [0.25, 0.35, 0.40], 1)[0])
        else:
            slots.append(pick(SLOT_NAMES, SLOT_WEIGHT, 1)[0])
    df["消费时段"] = slots

    df["消费时刻"] = [random_time_in_slot(s) for s in df["消费时段"]]

    # 商户：从该类别下的商户中抽
    df["商户"] = [RNG.choice(MERCHANTS[c]) for c in df["消费类别"]]

    # 金额
    df["消费金额"] = [
        build_amount(cat, d.month, d.dayofweek)
        for cat, d in zip(df["消费类别"], df["消费日期"])
    ]

    # 满意度评分（1~5，偏高分，餐饮评分波动大一些）
    scores = []
    for cat in df["消费类别"]:
        p = [0.02, 0.05, 0.13, 0.45, 0.35] if cat == "食堂餐饮" else [0.01, 0.03, 0.10, 0.46, 0.40]
        scores.append(pick([1, 2, 3, 4, 5], p, 1)[0])
    df["满意度评分"] = scores

    # 是否退款（真实业务中退款率很低，约 2%）
    refund_mask = RNG.random(n) < 0.02
    df["是否退款"] = np.where(refund_mask, "是", "否")

    # 学生编号：按 学院×年级 建档，每个组合 30 人，使同一学生多次出现（便于做人均分析）
    roster = {}
    sid = 0
    for college in COLLEGES:
        for grade in GRADES:
            ids = []
            for _ in range(30):
                sid += 1
                ids.append(f"S{sid:04d}")
            roster[(college, grade)] = ids

    df["学生编号"] = [
        RNG.choice(roster[(c, g)]) for c, g in zip(df["学院"], df["年级"])
    ]

    # 订单号（时间升序编号更自然，这里先排序）
    df = df.sort_values(["消费日期", "消费时刻"]).reset_index(drop=True)
    df.insert(0, "订单编号", [f"DD{i:05d}" for i in range(1, len(df) + 1)])

    # 列顺序
    df = df[[
        "订单编号", "消费日期", "消费时刻", "消费时段", "学生编号", "学院", "年级",
        "消费类别", "商户", "支付方式", "消费金额", "满意度评分", "是否退款",
    ]]
    return df


# ---------------------------------------------------------------- 注入脏数据
def inject_dirty(df):
    """向干净数据中注入典型脏数据，让预处理环节有真实意义"""
    df = df.copy()
    n = len(df)
    log = {}

    # 1) 金额缺失：模拟刷卡机上传失败
    idx = RNG.choice(n, 1800, replace=False)
    df.loc[idx, "消费金额"] = np.nan
    log["金额为空"] = 1800

    # 2) 类别缺失：模拟人工补录遗漏
    idx = RNG.choice(n, 1080, replace=False)
    df.loc[idx, "消费类别"] = np.nan
    log["类别为空"] = 1080

    # 3) 金额为负：模拟退款冲正记录错记成负数消费
    idx = RNG.choice(n, 840, replace=False)
    df.loc[idx, "消费金额"] = -df.loc[idx, "消费金额"].abs()
    log["金额为负"] = 840

    # 4) 极端异常值：模拟设备故障把 15.8 记成 15800
    idx = RNG.choice(n, 480, replace=False)
    df.loc[idx, "消费金额"] = RNG.choice([8888.0, 15800.0, 9999.0], 480)
    log["金额异常(>5000)"] = 480

    # 5) 重复记录：模拟网络重传导致同一订单被写入两次
    dup = df.sample(1320, random_state=SEED)
    df = pd.concat([df, dup], ignore_index=True)
    log["重复行"] = 1320

    # 6) 日期越界：模拟跨系统时区错误，跑到学期之外
    idx = RNG.choice(len(df), 360, replace=False)
    df.loc[idx, "消费日期"] = pd.Timestamp("2024-03-05")
    log["日期越界"] = 360

    # 7) 满意度评分缺失
    idx = RNG.choice(len(df), 720, replace=False)
    df.loc[idx, "满意度评分"] = np.nan
    log["评分为空"] = 720

    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    return df, log


# ---------------------------------------------------------------- 数据预处理
def clean(df):
    """基础预处理：剔除无效数据、空值、异常值，规范统计维度"""
    steps = []
    start = len(df)

    # Step 1 去重：同一订单编号出现多次，只保留一份
    before = len(df)
    df = df.drop_duplicates(subset=["订单编号"], keep="first").copy()
    steps.append(("按订单编号去重", before - len(df)))

    # Step 2 日期字段规范化 + 剔除学期外记录
    df["消费日期"] = pd.to_datetime(df["消费日期"], errors="coerce")
    before = len(df)
    df = df[df["消费日期"].notna()]
    df = df[(df["消费日期"] >= SEMESTER_START) & (df["消费日期"] <= SEMESTER_END)]
    steps.append(("剔除日期缺失/越界", before - len(df)))

    # Step 3 缺失值处理
    before = len(df)
    df = df.dropna(subset=["消费类别", "消费金额"])          # 关键字段缺失无法修复 → 直接剔除
    steps.append(("剔除关键字段空值", before - len(df)))

    # 满意度评分缺失属于可修复项 → 用中位数填充
    fill_n = int(df["满意度评分"].isna().sum())
    df["满意度评分"] = df["满意度评分"].fillna(df["满意度评分"].median())
    steps.append(("满意度中位数填充", fill_n))

    # Step 4 异常值：消费金额必须为正，且不超过 5000 元（业务上限）
    before = len(df)
    df = df[(df["消费金额"] > 0) & (df["消费金额"] <= 5000)]
    steps.append(("剔除金额异常值", before - len(df)))

    # Step 5 数据类型规范化（维度整理）
    df["消费金额"] = df["消费金额"].astype(float).round(2)
    df["满意度评分"] = df["满意度评分"].astype(int)
    df["消费日期"] = pd.to_datetime(df["消费日期"])

    # 时间维度派生字段
    df["年"] = df["消费日期"].dt.year
    df["月份"] = df["消费日期"].dt.month
    df["月标签"] = df["消费日期"].dt.strftime("%Y-%m")
    df["星期"] = df["消费日期"].dt.dayofweek.map(
        {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
    )
    df["周序"] = ((df["消费日期"] - SEMESTER_START).dt.days // 7 + 1).astype(int)
    df["日期"] = df["消费日期"].dt.strftime("%Y-%m-%d")

    # 数值维度派生字段：单笔金额分档（便于分组分析）
    bins = [0, 10, 30, 60, 100, 5000]
    labels = ["10元以下", "10-30元", "30-60元", "60-100元", "100元以上"]
    df["金额分档"] = pd.cut(df["消费金额"], bins=bins, labels=labels, right=False)

    # 排序与列顺序
    df = df.sort_values(["消费日期", "消费时刻"]).reset_index(drop=True)
    df["序号"] = range(1, len(df) + 1)

    df = df[[
        "序号", "订单编号", "消费日期", "日期", "年", "月份", "月标签", "周序", "星期",
        "消费时刻", "消费时段", "学生编号", "学院", "年级", "消费类别", "商户",
        "支付方式", "消费金额", "金额分档", "满意度评分", "是否退款",
    ]]

    return df, start, steps


# ---------------------------------------------------------------- 主流程
def main():
    print("=" * 62)
    print("实验2 数据看板 —— 模拟数据生成与预处理")
    print("=" * 62)

    print("\n[1/4] 生成主体业务数据 ...")
    base = generate_records(120000)
    print(f"      生成有效业务记录：{len(base)} 条")

    print("\n[2/4] 注入模拟脏数据（贴近真实采集场景）...")
    raw, log = inject_dirty(base)
    for k, v in log.items():
        print(f"      + {k}: {v} 条")
    print(f"      原始数据合计：{len(raw)} 条")

    raw_path_xlsx = os.path.join(DATA_DIR, "校园消费原始数据_前2000条样例.xlsx")
    raw_path_csv = os.path.join(DATA_DIR, "校园消费原始数据.csv")
    # 全量原始数据存 CSV；另存前 2000 条到 Excel，方便直接用 Excel 打开查看字段
    raw.head(2000).to_excel(raw_path_xlsx, index=False, sheet_name="原始数据样例")
    raw.to_csv(raw_path_csv, index=False, encoding="utf-8-sig")
    print(f"      已保存：{raw_path_csv}（全量）")
    print(f"      已保存：{raw_path_xlsx}（前 2000 条样例）")

    print("\n[3/4] 执行数据预处理 ...")
    cleaned, start, steps = clean(raw)
    for name, cnt in steps:
        flag = "" if cnt == 0 else f"  {cnt} 条"
        print(f"      · {name}{flag}")
    print(f"      清洗前 {start} 条 → 清洗后 {len(cleaned)} 条 "
          f"(清洗率 {100 * (1 - len(cleaned) / start):.1f}%)")

    out_path = os.path.join(DATA_DIR, "校园消费数据.csv")
    cleaned.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"      已保存：{out_path}")

    print("\n[4/4] 数据概览 ...")
    print(f"      时间范围：{cleaned['日期'].min()} ~ {cleaned['日期'].max()}")
    print(f"      总消费额：{cleaned['消费金额'].sum():,.2f} 元")
    print(f"      单笔均值：{cleaned['消费金额'].mean():.2f} 元")
    print(f"      覆盖学生：{cleaned['学生编号'].nunique()} 人")
    print(f"      覆盖商户：{cleaned['商户'].nunique()} 家")
    print("\n      各类别消费占比：")
    share = cleaned.groupby("消费类别")["消费金额"].sum().sort_values(ascending=False)
    for cat, amt in share.items():
        print(f"        {cat:<8}{amt:>12,.2f} 元  ({100 * amt / share.sum():5.1f}%)")

    print("\n      各月人均消费（用于设定预算阈值）：")
    mg = cleaned.groupby("月标签").agg(总额=("消费金额", "sum"),
                                       人数=("学生编号", "nunique"))
    mg["月人均"] = (mg["总额"] / mg["人数"]).round(1)
    mg["日均笔数"] = (cleaned.groupby("月标签").size()
                      / cleaned.groupby("月标签")["日期"].nunique()).round(0)
    for idx, row in mg.iterrows():
        print(f"        {idx}  月人均 {row['月人均']:>7.1f} 元   "
              f"日均 {row['日均笔数']:.0f} 笔")
    print("\n完成。运行 python -m streamlit run app.py 启动看板。")
    print("=" * 62)


if __name__ == "__main__":
    main()
