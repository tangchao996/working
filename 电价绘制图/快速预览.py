#!/usr/bin/env python3
"""
快速预览脚本 - 使用演示数据快速生成图表
可以不依赖Excel文件，直接查看图表效果
"""
import os
import sys

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入主函数
from 电价趋势图绘制 import plot_daily_price_trend, create_demo_data

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 电价趋势分析图 - 快速预览模式")
    print("=" * 60)
    print()
    print("使用内置演示数据生成图表...")
    print()
    
    # 创建演示数据
    df_demo = create_demo_data()
    
    # 输出路径
    output_path = os.path.join(current_dir, '电价趋势分析图_快速预览.png')
    
    # 生成图表
    fig, axes = plot_daily_price_trend(
        df_demo,
        save_path=output_path,
        show_labels=True,
        figsize=(20, 16)
    )
    
    if fig:
        print()
        print("✅ 图表生成成功！")
        print()
        print(f"📁 保存位置: {output_path}")
        print()
        print("=" * 60)
        print("📊 图表特性说明：")
        print("=" * 60)
        print()
        print("🎯 顶部：4张关键指标卡片")
        print("   - 日前均价、实时均价、平均价差、相关系数")
        print()
        print("📈 中上：主趋势图")
        print("   - 日前与实时均价走势线（带标记点）")
        print("   - 自动标注最高点和最低点（白色空心圆）")
        print("   - 均值参考线 + 标准差置信区间")
        print("   - 价差区间填充（薄荷绿色）")
        print()
        print("📊 中下：价差柱状图")
        print("   - 绿色柱 = 正溢价（实时 > 日前）")
        print("   - 橙色柱 = 负溢价（实时 < 日前）")
        print("   - 标注最大正负溢价点")
        print()
        print("📋 底部：统计信息与智能洞察")
        print("   - 左侧：完整统计表（均值、标准差、极值）")
        print("   - 右侧：自动生成的关键洞察点")
        print()
        print("=" * 60)
        print("💡 提示：")
        print("   - 图表分辨率：300 DPI（适合打印）")
        print("   - 图表尺寸：20×16 英寸")
        print("   - 配色方案：专业 Tailwind CSS 配色")
        print("=" * 60)
        print()
        print("📖 详细说明请查看：设计效果说明.md")
        print()
    else:
        print("❌ 图表生成失败")
        sys.exit(1)
