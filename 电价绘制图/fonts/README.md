# 中文字体文件

此目录包含用于图表生成的中文字体文件。

## 文件说明

- `WenQuanYiMicroHei.ttf` - 文泉驿微米黑字体（TrueType Collection 格式）
  - 许可证：GPL v3 with font embedding exception
  - 来源：[WenQuanYi Micro Hei](https://github.com/anthonyfok/fonts-wqy-microhei)
  - 大小：约 5 MB
  - 支持：简体中文、繁体中文、日文、韩文等

## 为什么需要字体文件？

在 Linux 环境下，matplotlib 默认不包含中文字体，导致中文字符显示为方块 (□)。通过在项目中包含字体文件，可以确保在任何环境下都能正确显示中文。

## 字体自动加载

脚本 `电价趋势图绘制.py` 会自动检测并加载此字体文件：
- 如果字体文件存在，自动使用
- 如果字体文件不存在，回退到系统字体

## 许可证信息

文泉驿微米黑字体采用 **GPL v3** 许可证，并带有字体嵌入例外条款，允许将字体嵌入到文档和程序中。

更多信息请参见：https://wenq.org/wqy2/index.cgi?MicroHei
