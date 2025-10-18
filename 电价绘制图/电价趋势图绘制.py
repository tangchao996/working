import os
import warnings
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch

# --- 全局配置 ---
# 忽略警告信息
warnings.filterwarnings('ignore')

# 尝试导入adjustText库，用于优化数据标签位置
try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:  # pragma: no cover - 允许无此依赖
    HAS_ADJUST_TEXT = False

# 设置全局字体和样式，确保中文正确显示
plt.rcParams['font.sans-serif'] = [
    'Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'Heiti TC', 'DejaVu Sans'
]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120  # 提高图像分辨率
plt.rcParams['savefig.dpi'] = 300  # 提高保存图像的分辨率

# 使用Seaborn增强图表美观度
sns.set_theme(
    style="whitegrid",
    rc={
        "grid.linewidth": 0.5,
        "grid.alpha": 0.35,
        "axes.edgecolor": "0.85",
        "axes.linewidth": 1.0,
        "figure.facecolor": "white",
        "figure.edgecolor": "white"
    },
)


def _format_percent(value: float) -> str:
    """辅助函数: 以百分比格式展示数值，若无效则返回'--'"""
    if value is None or not np.isfinite(value):
        return "--"
    return f"{value:.2f}%"


def _format_currency(value: float) -> str:
    """辅助函数: 以两位小数的货币格式展示数值，若无效则返回'--'"""
    if value is None or not np.isfinite(value):
        return "--"
    return f"{value:.2f}"


def plot_daily_price_trend(
    df: pd.DataFrame,
    save_path: str | None = None,
    show_labels: bool = True,
    figsize: Tuple[int, int] = (20, 16),
) -> Tuple[plt.Figure | None, Dict[str, plt.Axes] | None]:
    """
    根据给定的数据框，绘制一幅专业、美观的每日电价趋势分析图。

    核心功能:
    1. 绘制日前均价与实时均价的趋势线并突出关键拐点。
    2. 动态计算并展示均值线、标准差范围与价差分布。
    3. 通过顶部信息卡提供关键指标摘要，底部统计面板展示洞察。
    4. 添加精确到两位小数的数据标签，并使用adjustText库（如果可用）避免重叠。
    5. 创建一个独立的价差分析子图，直观展示每日价格波动。
    6. 集成专业的统计信息面板，包含详细的统计数据和关键指标。
    7. 确保所有中文字体都能清晰、正确地显示，整体配色协调。
    8. 格式化X轴，确保显示每一天的日期。

    参数:
    - df (pd.DataFrame): 包含电价数据的数据框，至少三列: 日期、日前均价、实时均价。
    - save_path (str, optional): 图表保存路径。如果提供，将保存为PNG文件。
    - show_labels (bool, optional): 是否在趋势线上展示数据标签。
    - figsize (tuple, optional): 图形的尺寸。

    返回:
    - fig (matplotlib.figure.Figure): 创建的图形对象。
    - axes (dict): 包含所有子图对象的字典，方便进一步定制。
    """

    # --- 1. 数据预处理与计算 ---
    df_clean = df.copy()
    df_clean.columns = ['日期', '日前均价', '实时均价']
    df_clean['日期'] = pd.to_datetime(df_clean['日期'])
    df_clean = df_clean.dropna().sort_values('日期').reset_index(drop=True)

    if df_clean.empty:
        print("错误：数据为空或所有行都包含缺失值，无法生成图表。")
        return None, None

    df_clean['价差'] = df_clean['实时均价'] - df_clean['日前均价']

    # --- 2. 核心统计量计算 ---
    start_date = df_clean['日期'].min()
    end_date = df_clean['日期'].max()

    dayahead_mean = df_clean['日前均价'].mean()
    realtime_mean = df_clean['实时均价'].mean()
    price_diff_mean = df_clean['价差'].mean()

    dayahead_std = df_clean['日前均价'].std()
    realtime_std = df_clean['实时均价'].std()
    spread_std = df_clean['价差'].std()

    price_correlation = df_clean['日前均价'].corr(df_clean['实时均价'])

    premium_rate = (price_diff_mean / dayahead_mean * 100) if dayahead_mean else np.nan
    realtime_volatility = (realtime_std / realtime_mean * 100) if realtime_mean else np.nan
    dayahead_volatility = (dayahead_std / dayahead_mean * 100) if dayahead_mean else np.nan

    dayahead_max_idx = df_clean['日前均价'].idxmax()
    dayahead_min_idx = df_clean['日前均价'].idxmin()
    realtime_max_idx = df_clean['实时均价'].idxmax()
    realtime_min_idx = df_clean['实时均价'].idxmin()
    diff_max_idx = df_clean['价差'].idxmax()
    diff_min_idx = df_clean['价差'].idxmin()

    # --- 3. 创建图形与布局 ---
    fig = plt.figure(figsize=figsize, constrained_layout=True)
    gs = fig.add_gridspec(4, 1, height_ratios=[0.65, 3.1, 1.6, 1.2], hspace=0.18)

    ax_kpi = fig.add_subplot(gs[0, 0])
    ax_main = fig.add_subplot(gs[1, 0])
    ax_diff = fig.add_subplot(gs[2, 0], sharex=ax_main)
    ax_stats = fig.add_subplot(gs[3, 0])

    axes = {
        'kpi': ax_kpi,
        'main': ax_main,
        'diff': ax_diff,
        'stats': ax_stats,
    }

    fig.suptitle(
        f"每日电价趋势洞察 | {start_date:%Y年%m月%d日} - {end_date:%Y年%m月%d日}",
        fontsize=22,
        fontweight='bold',
        color='#0f172a',
        y=0.99,
    )

    # --- 4. 顶部关键指标信息卡 ---
    ax_kpi.axis('off')
    ax_kpi.set_xlim(0, 1)
    ax_kpi.set_ylim(0, 1)

    metric_cards = [
        (
            "日前均价",
            _format_currency(dayahead_mean),
            f"波动率 {_format_percent(dayahead_volatility)}",
        ),
        (
            "实时均价",
            _format_currency(realtime_mean),
            f"波动率 {_format_percent(realtime_volatility)}",
        ),
        (
            "平均价差",
            _format_currency(price_diff_mean),
            f"价差σ {_format_currency(spread_std)}",
        ),
        (
            "相关系数",
            _format_currency(price_correlation),
            f"平均溢价率 {_format_percent(premium_rate)}",
        ),
    ]

    card_width = 0.22
    card_height = 0.78
    start_x = 0.02
    gap = 0.02

    for idx, (title, value, subtitle) in enumerate(metric_cards):
        x = start_x + idx * (card_width + gap)
        y = 0.1
        card = FancyBboxPatch(
            (x, y),
            card_width,
            card_height,
            boxstyle="round,pad=0.02",
            linewidth=1,
            facecolor="#f8fafc",
            edgecolor="#e2e8f0",
            mutation_aspect=0.5,
            transform=ax_kpi.transAxes,
            zorder=1,
        )
        ax_kpi.add_patch(card)

        ax_kpi.text(
            x + 0.02,
            y + card_height - 0.18,
            title,
            transform=ax_kpi.transAxes,
            fontsize=11,
            color='#475569',
            fontweight='semibold',
            ha='left',
        )

        ax_kpi.text(
            x + 0.02,
            y + card_height - 0.45,
            value,
            transform=ax_kpi.transAxes,
            fontsize=20,
            fontweight='bold',
            color='#0f172a',
            ha='left',
        )

        ax_kpi.text(
            x + 0.02,
            y + 0.16,
            subtitle,
            transform=ax_kpi.transAxes,
            fontsize=10.5,
            color='#64748b',
            ha='left',
        )

    # --- 5. 主趋势图绘制 ---
    color_dayahead = '#005f73'
    color_realtime = '#ae2012'

    ax_main.set_facecolor('#f9fbfd')
    ax_main.grid(True, axis='y', linestyle='--', linewidth=0.6, alpha=0.35)

    ax_main.plot(
        df_clean['日期'],
        df_clean['日前均价'],
        linewidth=2.4,
        marker='o',
        markersize=7,
        color=color_dayahead,
        label='日前均价',
        alpha=0.9,
        mec='white',
        mew=1.0,
        zorder=3,
    )

    ax_main.plot(
        df_clean['日期'],
        df_clean['实时均价'],
        linewidth=2.4,
        marker='s',
        markersize=7,
        color=color_realtime,
        label='实时均价',
        alpha=0.9,
        mec='white',
        mew=1.0,
        zorder=3,
    )

    ax_main.fill_between(
        df_clean['日期'],
        df_clean['日前均价'],
        df_clean['实时均价'],
        color='#94d2bd',
        alpha=0.12,
        label='价差区间',
        zorder=1,
    )

    ax_main.axhline(
        y=dayahead_mean,
        color=color_dayahead,
        linestyle='--',
        alpha=0.7,
        linewidth=1.8,
        label=f'日前均价均值: {_format_currency(dayahead_mean)}',
    )

    ax_main.axhline(
        y=realtime_mean,
        color=color_realtime,
        linestyle='--',
        alpha=0.7,
        linewidth=1.8,
        label=f'实时均价均值: {_format_currency(realtime_mean)}',
    )

    ax_main.fill_between(
        df_clean['日期'],
        dayahead_mean - dayahead_std,
        dayahead_mean + dayahead_std,
        color=color_dayahead,
        alpha=0.08,
        zorder=2,
    )

    ax_main.fill_between(
        df_clean['日期'],
        realtime_mean - realtime_std,
        realtime_mean + realtime_std,
        color=color_realtime,
        alpha=0.08,
        zorder=2,
    )

    highlight_style = dict(s=130, linewidths=1.6, facecolors='white', zorder=5)

    ax_main.scatter(
        df_clean.loc[dayahead_max_idx, '日期'],
        df_clean.loc[dayahead_max_idx, '日前均价'],
        edgecolors=color_dayahead,
        **highlight_style,
    )
    ax_main.annotate(
        f"日前峰值\n{df_clean.loc[dayahead_max_idx, '日前均价']:.2f}",
        xy=(df_clean.loc[dayahead_max_idx, '日期'], df_clean.loc[dayahead_max_idx, '日前均价']),
        xytext=(0, 14),
        textcoords='offset points',
        fontsize=9.5,
        color=color_dayahead,
        fontweight='semibold',
        ha='center',
    )

    ax_main.scatter(
        df_clean.loc[realtime_max_idx, '日期'],
        df_clean.loc[realtime_max_idx, '实时均价'],
        edgecolors=color_realtime,
        **highlight_style,
    )
    ax_main.annotate(
        f"实时峰值\n{df_clean.loc[realtime_max_idx, '实时均价']:.2f}",
        xy=(df_clean.loc[realtime_max_idx, '日期'], df_clean.loc[realtime_max_idx, '实时均价']),
        xytext=(0, 14),
        textcoords='offset points',
        fontsize=9.5,
        color=color_realtime,
        fontweight='semibold',
        ha='center',
    )

    ax_main.scatter(
        df_clean.loc[dayahead_min_idx, '日期'],
        df_clean.loc[dayahead_min_idx, '日前均价'],
        edgecolors=color_dayahead,
        **highlight_style,
    )
    ax_main.annotate(
        f"日前低点\n{df_clean.loc[dayahead_min_idx, '日前均价']:.2f}",
        xy=(df_clean.loc[dayahead_min_idx, '日期'], df_clean.loc[dayahead_min_idx, '日前均价']),
        xytext=(0, -32),
        textcoords='offset points',
        fontsize=9.5,
        color=color_dayahead,
        fontweight='semibold',
        ha='center',
        va='top',
    )

    ax_main.scatter(
        df_clean.loc[realtime_min_idx, '日期'],
        df_clean.loc[realtime_min_idx, '实时均价'],
        edgecolors=color_realtime,
        **highlight_style,
    )
    ax_main.annotate(
        f"实时低点\n{df_clean.loc[realtime_min_idx, '实时均价']:.2f}",
        xy=(df_clean.loc[realtime_min_idx, '日期'], df_clean.loc[realtime_min_idx, '实时均价']),
        xytext=(0, -32),
        textcoords='offset points',
        fontsize=9.5,
        color=color_realtime,
        fontweight='semibold',
        ha='center',
        va='top',
    )

    texts = []
    if show_labels:
        label_interval = max(1, len(df_clean) // 18)
        for i, row in df_clean.iterrows():
            if i % label_interval == 0 or i == df_clean.index[-1]:
                texts.append(
                    ax_main.text(
                        row['日期'],
                        row['日前均价'],
                        f" {row['日前均价']:.2f}",
                        fontsize=9,
                        color=color_dayahead,
                        ha='left',
                        va='center',
                        alpha=0.85,
                    )
                )
                texts.append(
                    ax_main.text(
                        row['日期'],
                        row['实时均价'],
                        f" {row['实时均价']:.2f}",
                        fontsize=9,
                        color=color_realtime,
                        ha='left',
                        va='center',
                        alpha=0.85,
                    )
                )

    if HAS_ADJUST_TEXT and texts:
        adjust_text(texts, ax=ax_main, arrowprops=dict(arrowstyle='->', color='#94a3b8', lw=0.5))

    ax_main.set_title(
        '日前与实时均价走势',
        fontsize=18,
        fontweight='bold',
        pad=16,
        color='#0f172a',
    )
    ax_main.set_ylabel('价格 (元/MWh)', fontsize=14, fontweight='bold', color='#1f2937')
    ax_main.tick_params(axis='y', labelsize=12, colors='#334155')
    ax_main.spines[['top', 'right']].set_visible(False)

    legend = ax_main.legend(
        loc='upper left',
        fontsize=11,
        frameon=True,
        ncol=2,
        columnspacing=1.2,
        handlelength=2.2,
    )
    legend.get_frame().set_facecolor('#ffffff')
    legend.get_frame().set_edgecolor('#e2e8f0')
    plt.setp(ax_main.get_xticklabels(), visible=False)

    # --- 6. 价差分析图绘制 ---
    ax_diff.set_facecolor('#fefce8')
    colors = ['#2a9d8f' if x >= 0 else '#e76f51' for x in df_clean['价差']]

    ax_diff.bar(
        df_clean['日期'],
        df_clean['价差'],
        color=colors,
        alpha=0.9,
        width=0.7,
        edgecolor='white',
        linewidth=0.6,
    )

    ax_diff.axhline(y=0, color='#475569', linewidth=0.8, linestyle='-', alpha=0.6)
    ax_diff.axhline(
        y=price_diff_mean,
        color='#1f2937',
        linestyle=':',
        linewidth=1.8,
        alpha=0.85,
        label=f'平均价差: {_format_currency(price_diff_mean)}',
    )

    ax_diff.scatter(
        df_clean.loc[diff_max_idx, '日期'],
        df_clean.loc[diff_max_idx, '价差'],
        s=110,
        color='#2a9d8f',
        edgecolors='white',
        linewidths=1.4,
        zorder=4,
    )
    ax_diff.annotate(
        f"最大正溢价\n{df_clean.loc[diff_max_idx, '价差']:.2f}",
        xy=(df_clean.loc[diff_max_idx, '日期'], df_clean.loc[diff_max_idx, '价差']),
        xytext=(0, 14),
        textcoords='offset points',
        fontsize=9.5,
        color='#2a9d8f',
        fontweight='semibold',
        ha='center',
    )

    ax_diff.scatter(
        df_clean.loc[diff_min_idx, '日期'],
        df_clean.loc[diff_min_idx, '价差'],
        s=110,
        color='#e76f51',
        edgecolors='white',
        linewidths=1.4,
        zorder=4,
    )
    ax_diff.annotate(
        f"最大负溢价\n{df_clean.loc[diff_min_idx, '价差']:.2f}",
        xy=(df_clean.loc[diff_min_idx, '日期'], df_clean.loc[diff_min_idx, '价差']),
        xytext=(0, -28),
        textcoords='offset points',
        fontsize=9.5,
        color='#e76f51',
        fontweight='semibold',
        ha='center',
        va='top',
    )

    ax_diff.set_ylabel('价差 (元/MWh)', fontsize=14, fontweight='bold', color='#1f2937')
    ax_diff.set_xlabel('日期', fontsize=14, fontweight='bold', color='#1f2937', labelpad=10)
    ax_diff.tick_params(axis='x', labelsize=11, colors='#334155')
    ax_diff.tick_params(axis='y', labelsize=12, colors='#334155')
    ax_diff.legend(loc='upper right', fontsize=11, frameon=False)

    ax_diff.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax_diff.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    fig.autofmt_xdate(rotation=40, ha='right')

    # --- 7. 底部统计信息与洞察 ---
    ax_stats.axis('off')

    stats_block = (
        f"—— 核心统计摘要 ——\n"
        f"周期: {len(df_clean)} 天 ({start_date:%Y-%m-%d} → {end_date:%Y-%m-%d})\n\n"
        f"{'指标':<12}{'日前均价':>12}{'实时均价':>12}{'价差':>12}\n"
        f"{'-' * 52}\n"
        f"{'均值':<12}{dayahead_mean:>12.2f}{realtime_mean:>12.2f}{price_diff_mean:>12.2f}\n"
        f"{'标准差':<12}{dayahead_std:>12.2f}{realtime_std:>12.2f}{spread_std:>12.2f}\n"
        f"{'最小值':<12}{df_clean.loc[dayahead_min_idx, '日前均价']:>12.2f}"
        f"{df_clean.loc[realtime_min_idx, '实时均价']:>12.2f}{df_clean.loc[diff_min_idx, '价差']:>12.2f}\n"
        f"{'最大值':<12}{df_clean.loc[dayahead_max_idx, '日前均价']:>12.2f}"
        f"{df_clean.loc[realtime_max_idx, '实时均价']:>12.2f}{df_clean.loc[diff_max_idx, '价差']:>12.2f}\n"
    )

    insight_items = [
        f"实时价格峰值出现在 {df_clean.loc[realtime_max_idx, '日期']:%m月%d日}" \
        f"（{df_clean.loc[realtime_max_idx, '实时均价']:.2f} 元/MWh）",
        f"最大正溢价发生在 {df_clean.loc[diff_max_idx, '日期']:%m月%d日}" \
        f"，价差 {df_clean.loc[diff_max_idx, '价差']:.2f} 元/MWh",
        f"最大负溢价发生在 {df_clean.loc[diff_min_idx, '日期']:%m月%d日}" \
        f"，价差 {df_clean.loc[diff_min_idx, '价差']:.2f} 元/MWh",
        f"实时价格与日前价格的相关性为 {price_correlation:.3f}" \
        f"，平均溢价率 {_format_percent(premium_rate)}",
    ]

    insights_text = '\n'.join(f"• {item}" for item in insight_items)

    ax_stats.text(
        0.02,
        0.95,
        stats_block,
        transform=ax_stats.transAxes,
        fontsize=11,
        fontfamily='monospace',
        verticalalignment='top',
        horizontalalignment='left',
        linespacing=1.65,
        bbox=dict(boxstyle="round,pad=0.55", fc="#f8fafc", ec="#e2e8f0"),
    )

    ax_stats.text(
        0.56,
        0.95,
        insights_text,
        transform=ax_stats.transAxes,
        fontsize=11.5,
        verticalalignment='top',
        horizontalalignment='left',
        linespacing=1.7,
        color='#1f2937',
        bbox=dict(boxstyle="round,pad=0.6", fc="#fff7ed", ec="#fed7aa"),
    )

    # --- 8. 保存与返回 ---
    if save_path:
        try:
            plt.savefig(
                save_path,
                bbox_inches='tight',
                facecolor=fig.get_facecolor(),
                edgecolor='none',
            )
            print(f"图表已成功保存至: {save_path}")
        except Exception as exc:  # pragma: no cover - 捕获文件写入异常
            print(f"保存图表时发生错误: {exc}")

    return fig, axes


def create_demo_data() -> pd.DataFrame:
    """创建一份用于演示的DataFrame"""
    data = {
        '日期': pd.to_datetime([
            '2025/6/29', '2025/6/30', '2025/7/1', '2025/7/2', '2025/7/3',
            '2025/7/4', '2025/7/5', '2025/7/6', '2025/7/7', '2025/7/8',
            '2025/7/9', '2025/7/10', '2025/7/11', '2025/7/12', '2025/7/13',
            '2025/7/14', '2025/7/15', '2025/7/16', '2025/7/17', '2025/7/18',
            '2025/7/19', '2025/7/20', '2025/7/21', '2025/7/22', '2025/7/23',
            '2025/7/24', '2025/7/25', '2025/7/26', '2025/7/27', '2025/7/28',
            '2025/7/29', '2025/7/30', '2025/7/31', '2025/8/1', '2025/8/2'
        ]),
        '日前均价': [
            306.28, 427.16, 298.83, 273.59, 266.34, 312.77, 341.52, 375.37,
            346.33, 310.02, 332.56, 374.76, 421.81, 352.55, 411.63, 365.21,
            381.49, 360.48, 417.15, 454.51, 507.47, 546.51, 275.56, 281.71,
            412.94, 339.47, 374.21, 357.71, 335.31, 327.78, 309.18, 230.01,
            326.55, 320.12, 338.37
        ],
        '实时均价': [
            550.50, 446.52, 370.22, 351.28, 298.34, 365.67, 300.18, 451.16,
            358.45, 361.55, 357.77, 408.07, 424.15, 372.03, 475.77, 468.73,
            427.64, 442.74, 428.10, 427.08, 437.81, 507.91, 340.33, 336.27,
            332.39, 355.34, 280.34, 326.35, 296.43, 279.07, 253.78, 209.47,
            298.27, 345.40, 269.36
        ],
    }

    df_demo = pd.DataFrame(data)
    df_demo.loc[df_demo['日期'] == '2025-08-03', '实时均价'] = np.nan
    return df_demo


if __name__ == '__main__':
    # --- 主执行块 ---
    print("--- 开始生成电价趋势分析图 ---")

    if not HAS_ADJUST_TEXT:
        print("\n[专业建议] 检测到未安装 'adjustText' 库。")
        print("为了获得最佳的数据标签布局效果（自动避免重叠），强烈建议安装此库。")
        print("可通过以下命令安装： pip install adjustText\n")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(script_dir, '每日电价分享.xlsx')
    save_location = os.path.join(script_dir, '电价趋势分析图_专业版.png')

    try:
        print(f"正在尝试从 '{excel_file}' 加载数据...")
        df_from_excel = pd.read_excel(excel_file)
        print("数据加载成功！")

        fig, axes = plot_daily_price_trend(df_from_excel, save_path=save_location)

        if fig:
            plt.show()
            print("\n--- 分析图生成完毕 ---")

    except FileNotFoundError:
        print(f"\n[警告] 未找到Excel文件 '{excel_file}'。")
        print("将使用内置的演示数据生成示例图表。")

        df_demo = create_demo_data()
        fig, axes = plot_daily_price_trend(df_demo, save_path=save_location)

        if fig:
            plt.show()
            print("\n--- 演示分析图生成完毕 ---")

    except Exception as exc:  # pragma: no cover - 输出未知异常
        print(f"\n[严重错误] 处理数据或绘图时发生未知错误: {exc}")
