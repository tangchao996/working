import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import seaborn as sns
from datetime import datetime
import warnings

# --- 全局配置 ---
# 忽略警告信息
warnings.filterwarnings('ignore')

# 尝试导入adjustText库，用于优化数据标签位置
try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False

# 设置全局字体和样式，确保中文正确显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'Heiti TC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120  # 提高图像分辨率
plt.rcParams['savefig.dpi'] = 300 # 提高保存图像的分辨率

# 使用Seaborn增强图表美观度
sns.set_theme(style="whitegrid", rc={
    "grid.linewidth": 0.5, 
    "grid.alpha": 0.4,
    "axes.edgecolor": "0.8",
    "axes.linewidth": 1.0,
    "figure.facecolor": "white",
    "figure.edgecolor": "white"
})


def plot_daily_price_trend(df: pd.DataFrame, save_path: str = None, show_labels: bool = True, figsize: tuple = (20, 15)):
    """
    根据给定的数据框，绘制一幅专业、美观的每日电价趋势分析图。

    核心功能:
    1. 绘制日前均价与实时均价的趋势线。
    2. 动态计算并展示两种价格的均值线和标准差范围（置信区间）。
    3. 添加精确到两位小数的数据标签，并使用adjustText库（如果可用）避免重叠。
    4. 创建一个独立的价差分析子图，直观展示每日价格波动。
    5. 集成一个专业的统计信息面板，包含详细的统计数据和关键指标。
    6. 确保所有中文字体都能清晰、正确地显示。
    7. 格式化X轴，确保显示每一天的日期。

    参数:
    - df (pd.DataFrame): 包含电价数据的数据框。
                         必须包含至少三列，按顺序为：日期、日前均价、实时均价。
    - save_path (str, optional): 图表保存路径。如果提供，图表将保存为PNG文件。默认为None。
    - show_labels (bool, optional): 是否在图上显示数据标签。默认为True。
    - figsize (tuple, optional): 图形的尺寸。默认为(20, 15)。

    返回:
    - fig (matplotlib.figure.Figure): 创建的图形对象。
    - axes (dict): 包含所有子图对象的字典，方便进一步定制。
    """
    
    # --- 1. 数据预处理与计算 ---
    df_clean = df.copy()
    
    # 标准化列名
    df_clean.columns = ['日期', '日前均价', '实时均价']
    
    # 转换日期格式，兼容多种输入格式
    df_clean['日期'] = pd.to_datetime(df_clean['日期'])
    
    # 移除包含缺失值的行，确保计算准确性
    df_clean = df_clean.dropna()
    
    if df_clean.empty:
        print("错误：数据为空或所有行都包含缺失值，无法生成图表。")
        return None, None

    # 计算衍生指标
    df_clean['价差'] = df_clean['实时均价'] - df_clean['日前均价']
    
    # --- 2. 核心统计量计算 ---
    start_date = df_clean['日期'].min()
    end_date = df_clean['日期'].max()
    dayahead_mean = df_clean['日前均价'].mean()
    realtime_mean = df_clean['实时均价'].mean()
    price_diff_mean = df_clean['价差'].mean()
    dayahead_std = df_clean['日前均价'].std()
    realtime_std = df_clean['实时均价'].std()
    price_correlation = df_clean['日前均价'].corr(df_clean['实时均价'])
    
    # --- 3. 创建图形与布局 ---
    fig = plt.figure(figsize=figsize, constrained_layout=True)
    
    # 使用GridSpec进行更灵活的布局
    gs = fig.add_gridspec(3, 1, height_ratios=[3, 1.5, 1])
    
    axes = {
        'main': fig.add_subplot(gs[0, 0]),
        'diff': fig.add_subplot(gs[1, 0], sharex=fig.add_subplot(gs[0, 0])), # 共享X轴
        'stats': fig.add_subplot(gs[2, 0])
    }
    
    # --- 4. 主趋势图绘制 ---
    ax_main = axes['main']
    
    # 定义专业配色
    color_dayahead = '#005f73'
    color_realtime = '#ae2012'
    
    # 绘制价格趋势线
    ax_main.plot(df_clean['日期'], df_clean['日前均价'], 
                 linewidth=2.5, marker='o', markersize=7, 
                 color=color_dayahead, label='日前均价', 
                 alpha=0.9, mec='w', mew=1)
    
    ax_main.plot(df_clean['日期'], df_clean['实时均价'], 
                 linewidth=2.5, marker='s', markersize=7, 
                 color=color_realtime, label='实时均价', 
                 alpha=0.9, mec='w', mew=1)
    
    # 绘制均值线和置信区间（标准差）
    ax_main.axhline(y=dayahead_mean, color=color_dayahead, linestyle='--', 
                    alpha=0.7, linewidth=1.8, label=f'日前均价均值: {dayahead_mean:.2f}')
    ax_main.axhline(y=realtime_mean, color=color_realtime, linestyle='--', 
                    alpha=0.7, linewidth=1.8, label=f'实时均价均值: {realtime_mean:.2f}')
    
    ax_main.fill_between(df_clean['日期'], 
                         dayahead_mean - dayahead_std, dayahead_mean + dayahead_std, 
                         color=color_dayahead, alpha=0.1, label='日前价格 ±1σ')
    
    ax_main.fill_between(df_clean['日期'], 
                         realtime_mean - realtime_std, realtime_mean + realtime_std, 
                         color=color_realtime, alpha=0.1, label='实时价格 ±1σ')
    
    # --- 5. 数据标签处理 ---
    texts = []
    if show_labels:
        # 动态调整标签密度，避免大数据集下标示过多
        label_interval = max(1, len(df_clean) // 15)
        
        for i, row in df_clean.iterrows():
            if i % label_interval == 0 or i == df_clean.index[-1]:
                texts.append(ax_main.text(row['日期'], row['日前均价'], f" {row['日前均价']:.2f}", 
                                          fontsize=9, color=color_dayahead, ha='left', va='center'))
                texts.append(ax_main.text(row['日期'], row['实时均价'], f" {row['实时均价']:.2f}", 
                                          fontsize=9, color=color_realtime, ha='left', va='center'))

    # 如果安装了adjust_text库，则使用它来避免标签重叠
    if HAS_ADJUST_TEXT and texts:
        adjust_text(texts, ax=ax_main, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    # --- 6. 主图样式设置 ---
    title = f'每日电价趋势分析报告\n({start_date.strftime("%Y年%m月%d日")} 至 {end_date.strftime("%Y年%m月%d日")})'
    ax_main.set_title(title, fontsize=20, fontweight='bold', pad=20)
    ax_main.set_ylabel('价格 (元/MWh)', fontsize=14, fontweight='bold')
    ax_main.legend(loc='upper left', fontsize=12, ncol=2)
    ax_main.tick_params(axis='y', labelsize=12)
    plt.setp(ax_main.get_xticklabels(), visible=False) # 隐藏共享的X轴标签

    # --- 7. 价差分析图绘制 ---
    ax_diff = axes['diff']
    
    colors = ['#2a9d8f' if x >= 0 else '#e63946' for x in df_clean['价差']]
    ax_diff.bar(df_clean['日期'], df_clean['价差'], color=colors, alpha=0.8, width=0.7,
                edgecolor='white', linewidth=0.5)
    
    ax_diff.axhline(y=price_diff_mean, color='black', linestyle=':', 
                    linewidth=2, alpha=0.8, label=f'平均价差: {price_diff_mean:.2f}')
    
    ax_diff.set_ylabel('价差 (元/MWh)', fontsize=14, fontweight='bold')
    ax_diff.set_xlabel('日期', fontsize=14, fontweight='bold')
    ax_diff.legend(loc='upper right', fontsize=12)
    
    # --- 8. X轴格式化 ---
    # 设置主定位器为天
    ax_diff.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    # 设置主格式化器为 "月/日"
    ax_diff.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    # 自动旋转日期标签以避免重叠
    fig.autofmt_xdate(rotation=45, ha='right')
    ax_diff.tick_params(axis='x', labelsize=10)
    ax_diff.tick_params(axis='y', labelsize=12)
    
    # --- 9. 统计信息面板 ---
    ax_stats = axes['stats']
    ax_stats.axis('off')
    
    # 准备统计文本
    stats_text = (
        f"--- 核心统计摘要 ---\n"
        f"数据周期: {len(df_clean)} 天 ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})\n\n"
        f"{'指标':<12}{'日前均价':>12}{'实时均价':>12}{'价差':>12}\n"
        f"{'-'*52}\n"
        f"{'均值':<12}{dayahead_mean:>12.2f}{realtime_mean:>12.2f}{price_diff_mean:>12.2f}\n"
        f"{'标准差':<12}{dayahead_std:>12.2f}{realtime_std:>12.2f}{df_clean['价差'].std():>12.2f}\n\n"
        f"--- 市场关联性 ---\n"
        f"日前-实时价格相关系数: {price_correlation:.3f}\n"
        f"平均实时溢价率: {(price_diff_mean / dayahead_mean) * 100:.2f}%\n"
    )

    # 在子图中显示文本
    ax_stats.text(0.05, 0.95, stats_text, 
                  transform=ax_stats.transAxes,
                  fontsize=11, 
                  verticalalignment='top', 
                  horizontalalignment='left',
                  fontfamily='monospace',
                  bbox=dict(boxstyle="round,pad=0.5", fc="#f8f9fa", ec="#dee2e6"))
    
    # --- 10. 保存与返回 ---
    if save_path:
        try:
            plt.savefig(save_path, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
            print(f"图表已成功保存至: {save_path}")
        except Exception as e:
            print(f"保存图表时发生错误: {e}")
            
    return fig, axes


def create_demo_data() -> pd.DataFrame:
    """创建一份用于演示的DataFrame"""
    data = {
        '日期': pd.to_datetime(['2025/6/29', '2025/6/30', '2025/7/1', '2025/7/2', '2025/7/3', 
                '2025/7/4', '2025/7/5', '2025/7/6', '2025/7/7', '2025/7/8',
                '2025/7/9', '2025/7/10', '2025/7/11', '2025/7/12', '2025/7/13',
                '2025/7/14', '2025/7/15', '2025/7/16', '2025/7/17', '2025/7/18',
                '2025/7/19', '2025/7/20', '2025/7/21', '2025/7/22', '2025/7/23',
                '2025/7/24', '2025/7/25', '2025/7/26', '2025/7/27', '2025/7/28',
                '2025/7/29', '2025/7/30', '2025/7/31', '2025/8/1', '2025/8/2']),
        '日前均价': [306.28, 427.16, 298.83, 273.59, 266.34, 312.77, 341.52, 375.37,
                   346.33, 310.02, 332.56, 374.76, 421.81, 352.55, 411.63, 365.21,
                   381.49, 360.48, 417.15, 454.51, 507.47, 546.51, 275.56, 281.71,
                   412.94, 339.47, 374.21, 357.71, 335.31, 327.78, 309.18, 230.01,
                   326.55, 320.12, 338.37],
        '实时均价': [550.50, 446.52, 370.22, 351.28, 298.34, 365.67, 300.18, 451.16,
                   358.45, 361.55, 357.77, 408.07, 424.15, 372.03, 475.77, 468.73,
                   427.64, 442.74, 428.10, 427.08, 437.81, 507.91, 340.33, 336.27,
                   332.39, 355.34, 280.34, 326.35, 296.43, 279.07, 253.78, 209.47,
                   298.27, 345.40, 269.36]
    }
    # 增加一个缺失值用于测试
    df = pd.DataFrame(data)
    df.loc[df['日期'] == '2025-08-03', '实时均价'] = np.nan
    return df

if __name__ == '__main__':
    # --- 主执行块 ---
    print("--- 开始生成电价趋势分析图 ---")
    
    # 检查依赖库
    if not HAS_ADJUST_TEXT:
        print("\n[专业建议] 检测到未安装 'adjustText' 库。")
        print("为了获得最佳的数据标签布局效果（自动避免重叠），强烈建议您安装此库。")
        print("您可以通过以下命令安装： pip install adjustText\n")

    # 1. 从Excel文件加载数据
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(script_dir, '每日电价分享.xlsx')
    save_location = os.path.join(script_dir, '电价趋势分析图_专业版.png')
    
    try:
        print(f"正在尝试从 '{excel_file}' 加载数据...")
        df_from_excel = pd.read_excel(excel_file)
        print("数据加载成功！")
        
        # 调用绘图函数
        fig, axes = plot_daily_price_trend(df_from_excel, save_path=save_location)
        
        if fig:
            plt.show()
            print("\n--- 分析图生成完毕 ---")
            
    except FileNotFoundError:
        print(f"\n[警告] 未找到Excel文件 '{excel_file}'。")
        print("将使用内置的演示数据生成示例图表。")
        
        # 2. 如果文件不存在，则使用演示数据
        df_demo = create_demo_data()
        
        # 调用绘图函数
        fig, axes = plot_daily_price_trend(df_demo, save_path=save_location)
        
        if fig:
            plt.show()
            print("\n--- 演示分析图生成完毕 ---")
    
    except Exception as e:
        print(f"\n[严重错误] 处理数据或绘图时发生未知错误: {e}") 